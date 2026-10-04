#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${TOPAZIO_OUT:-$PROJECT_DIR/build/out/arm64}"
LOG_DIR="$OUT_DIR/logs"
SERIAL_LOG="$LOG_DIR/qemu-smoke-serial.log"
KEY_DIR="$OUT_DIR/smoke-key"
SMOKE_IMAGE="$OUT_DIR/images/topazio-arm64-smoke.ext4"

# Keep the private key on a native Linux filesystem.  OpenSSH rejects private
# keys stored on a default Windows-mounted path because drvfs reports mode 0777.
KEY_DIR="$(mktemp -d /tmp/topazio-mobile-server-os-smoke-key.XXXXXX)"

mkdir -p "$LOG_DIR" "$KEY_DIR"
rm -f "$SERIAL_LOG"
ssh-keygen -q -t ed25519 -N '' -f "$KEY_DIR/id_ed25519"
if [[ ! -f "$OUT_DIR/images/topazio-arm64.ext4" || ! -f "$OUT_DIR/kernel/initrd.img" ]]; then
  "$PROJECT_DIR/scripts/build-arm64.sh"
fi
cp "$OUT_DIR/images/topazio-arm64.ext4" "$SMOKE_IMAGE"
SMOKE_MOUNT="$(mktemp -d)"
cleanup_mount() {
  if mountpoint -q "$SMOKE_MOUNT"; then umount "$SMOKE_MOUNT"; fi
  rmdir "$SMOKE_MOUNT" 2>/dev/null || true
}
trap cleanup_mount EXIT
mount -o loop "$SMOKE_IMAGE" "$SMOKE_MOUNT"
install -d -m 0700 "$SMOKE_MOUNT/home/admin/.ssh"
install -m 0600 "$KEY_DIR/id_ed25519.pub" "$SMOKE_MOUNT/home/admin/.ssh/authorized_keys"
chown 1000:1000 "$SMOKE_MOUNT/home/admin/.ssh" "$SMOKE_MOUNT/home/admin/.ssh/authorized_keys"
if [[ "${TOPAZIO_SMOKE_DEBUG:-0}" == "1" ]]; then
  install -d -m 0755 "$SMOKE_MOUNT/etc/systemd/system/multi-user.target.wants"
  cat >"$SMOKE_MOUNT/etc/systemd/system/topazio-smoke-debug.service" <<'DEBUG_UNIT'
[Unit]
Description=Topazio QEMU smoke diagnostics
After=network-online.target ssh.service topazio-http.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'mkdir -p /run/sshd; systemctl --no-pager --full status ssh.service; ss -lnt; /usr/sbin/sshd -t'
StandardOutput=journal+console
StandardError=journal+console

[Install]
WantedBy=multi-user.target
DEBUG_UNIT
  ln -sfn ../topazio-smoke-debug.service \
    "$SMOKE_MOUNT/etc/systemd/system/multi-user.target.wants/topazio-smoke-debug.service"
fi
sync
umount "$SMOKE_MOUNT"
trap - EXIT
rmdir "$SMOKE_MOUNT"

SHOW_STATUS=false
if [[ "${TOPAZIO_SMOKE_DEBUG:-0}" == "1" ]]; then
  SHOW_STATUS=true
fi
qemu-system-aarch64 \
  -machine virt -cpu cortex-a57 -m 1024 -smp 2 -accel tcg \
  -kernel "$OUT_DIR/kernel/vmlinuz" \
  -initrd "$OUT_DIR/kernel/initrd.img" \
  -append "root=/dev/vda rw console=ttyAMA0 systemd.show_status=$SHOW_STATUS" \
  -drive "if=none,file=$SMOKE_IMAGE,format=raw,id=drive0" \
  -device virtio-blk-device,drive=drive0 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22,hostfwd=tcp:127.0.0.1:8787-:8787 \
  -device virtio-net-device,netdev=net0 \
  -nographic -serial "file:$SERIAL_LOG" >/dev/null 2>&1 &
QEMU_PID=$!
cleanup() {
  kill "$QEMU_PID" 2>/dev/null || true
  wait "$QEMU_PID" 2>/dev/null || true
  rm -rf "$KEY_DIR"
}
trap cleanup EXIT

deadline=$((SECONDS + 180))
boot_ok=0
http_ok=0
ssh_ok=0
services_ok=0
guest_arch=""
while (( SECONDS < deadline )); do
  if grep -q 'TOPAZIO_BOOT_OK' "$SERIAL_LOG" 2>/dev/null; then boot_ok=1; fi
  if curl --silent --show-error --max-time 2 http://127.0.0.1:8787/healthz >/tmp/topazio-health.json 2>/dev/null; then http_ok=1; fi
  guest_arch="$(ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o ConnectTimeout=2 -i "$KEY_DIR/id_ed25519" -p 2222 admin@127.0.0.1 uname -m \
      2>/dev/null || true)"
  if [[ "$guest_arch" == "aarch64" ]]; then ssh_ok=1; fi
  if ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o ConnectTimeout=2 -i "$KEY_DIR/id_ed25519" -p 2222 admin@127.0.0.1 \
      systemctl is-active --quiet topazio-status.service topazio-metrics.service \
      topazio-http.service topazio-console.service >/dev/null 2>&1; then
    services_ok=1
  fi
  if (( boot_ok == 1 && http_ok == 1 && ssh_ok == 1 && services_ok == 1 )); then
    echo "TOPAZIO_QEMU_SMOKE_OK"
    echo "boot_marker=ok"
    echo "http=ok"
    echo "ssh=ok"
    echo "guest_arch=$guest_arch"
    echo "services=ok"
    cat /tmp/topazio-health.json
    exit 0
  fi
  sleep 2
done

echo "TOPAZIO_QEMU_SMOKE_FAILED" >&2
echo "boot_marker=$boot_ok http=$http_ok ssh=$ssh_ok services=$services_ok guest_arch=$guest_arch" >&2
tail -n 120 "$SERIAL_LOG" >&2 || true
exit 1
