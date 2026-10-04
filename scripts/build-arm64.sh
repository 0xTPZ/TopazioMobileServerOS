#!/usr/bin/env bash
set -Eeuo pipefail

# Build a Debian arm64 root filesystem and a bootable QEMU virt ext4 image.
# This script is intended to run as root inside WSL/Linux.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${TOPAZIO_OUT:-$PROJECT_DIR/build/out/arm64}"
WORK_DIR="${TOPAZIO_WORK_DIR:-/tmp/topazio-mobile-server-os-build}"
DISTRO="${TOPAZIO_DEBIAN_RELEASE:-trixie}"
MIRROR="${TOPAZIO_DEBIAN_MIRROR:-https://deb.debian.org/debian}"
IMAGE_SIZE="${TOPAZIO_IMAGE_SIZE:-1G}"
ARCH="arm64"

case "$OUT_DIR" in
  "$PROJECT_DIR/build/out/arm64"|"$PROJECT_DIR/build/out/arm64/"*) ;;
  *) echo "Refusing output outside build/out/arm64: $OUT_DIR" >&2; exit 2 ;;
esac
case "$WORK_DIR" in
  /tmp/topazio-mobile-server-os-build|/tmp/topazio-mobile-server-os-build/*) ;;
  *) echo "Refusing work directory outside /tmp/topazio-mobile-server-os-build: $WORK_DIR" >&2; exit 2 ;;
esac

for command_name in debootstrap qemu-aarch64-static mkfs.ext4 truncate mount umount mountpoint chroot tar gzip; do
  command -v "$command_name" >/dev/null || { echo "missing command: $command_name" >&2; exit 2; }
done
[[ "$(id -u)" == "0" ]] || { echo "run as root inside WSL/Linux" >&2; exit 2; }

ROOTFS="$WORK_DIR/rootfs"
IMAGES="$WORK_DIR/images"
MANIFESTS="$OUT_DIR/manifests"
LOGS="$OUT_DIR/logs"
IMAGE="$IMAGES/topazio-arm64.ext4"
FINAL_IMAGE="$OUT_DIR/images/topazio-arm64.ext4"
BUILD_EPOCH="$(git -C "$PROJECT_DIR" log -1 --format=%ct 2>/dev/null || date +%s)"
COMMIT="$(git -C "$PROJECT_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"

rm -rf "$OUT_DIR" "$WORK_DIR"
mkdir -p "$ROOTFS" "$IMAGES" "$MANIFESTS" "$LOGS"
cleanup_work() { rm -rf "$WORK_DIR"; }

echo "[1/8] debootstrap first stage: $DISTRO/$ARCH"
debootstrap --arch="$ARCH" --foreign --variant=minbase \
  --components=main "$DISTRO" "$ROOTFS" "$MIRROR" \
  >"$LOGS/debootstrap-first-stage.log" 2>&1
cp "$(command -v qemu-aarch64-static)" "$ROOTFS/usr/bin/qemu-aarch64-static"
chroot "$ROOTFS" /debootstrap/debootstrap --second-stage \
  >"$LOGS/debootstrap-second-stage.log" 2>&1

cat >"$ROOTFS/usr/sbin/policy-rc.d" <<'POLICY'
#!/bin/sh
exit 101
POLICY
chmod 0755 "$ROOTFS/usr/sbin/policy-rc.d"

echo "[2/8] installing minimal runtime packages"
cat >"$ROOTFS/etc/apt/sources.list" <<EOF_SOURCES
deb $MIRROR $DISTRO main
deb $MIRROR $DISTRO-updates main
deb http://security.debian.org/debian-security $DISTRO-security main
EOF_SOURCES
cat >"$ROOTFS/etc/apt/apt.conf.d/80topazio" <<'APT'
Acquire::Retries "3";
APT
chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive \
  apt-get update >"$LOGS/apt-update.log" 2>&1
chroot "$ROOTFS" /usr/bin/env DEBIAN_FRONTEND=noninteractive \
  apt-get install -y --no-install-recommends \
  systemd systemd-sysv systemd-resolved linux-image-arm64 \
  openssh-server ca-certificates git python3 nodejs sqlite3 \
  iproute2 iputils-ping procps sudo bash coreutils curl \
  >"$LOGS/apt-install.log" 2>&1

echo "[3/8] configuring identity, network and admin policy"
echo topazio-lab >"$ROOTFS/etc/hostname"
cat >"$ROOTFS/etc/hosts" <<'HOSTS'
127.0.0.1 localhost
127.0.1.1 topazio-lab
::1 localhost ip6-localhost ip6-loopback
HOSTS
cat >"$ROOTFS/etc/fstab" <<'FSTAB'
/dev/vda / ext4 defaults 0 1
FSTAB
mkdir -p "$ROOTFS/etc/systemd/network" "$ROOTFS/etc/ssh/sshd_config.d"
cat >"$ROOTFS/etc/systemd/network/20-topazio.network" <<'NETWORK'
[Match]
Name=en*

[Network]
DHCP=yes
NETWORK
cat >"$ROOTFS/etc/ssh/sshd_config.d/90-topazio.conf" <<'SSHCONF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AllowUsers admin
ListenAddress 0.0.0.0
SSHCONF
rm -f "$ROOTFS/etc/machine-id"
touch "$ROOTFS/etc/machine-id"
chroot "$ROOTFS" useradd --create-home --shell /bin/bash --uid 1000 admin || true
chroot "$ROOTFS" usermod --append --groups sudo admin
chroot "$ROOTFS" passwd --lock admin
if [[ -n "${TOPAZIO_AUTHORIZED_KEY_FILE:-}" ]]; then
  [[ -f "$TOPAZIO_AUTHORIZED_KEY_FILE" ]] || { echo "authorized key file not found" >&2; exit 2; }
  install -d -m 0700 "$ROOTFS/home/admin/.ssh"
  install -m 0600 "$TOPAZIO_AUTHORIZED_KEY_FILE" "$ROOTFS/home/admin/.ssh/authorized_keys"
  chroot "$ROOTFS" chown -R admin:admin /home/admin/.ssh
fi

echo "[4/8] installing Topazio services"
install -d -m 0755 "$ROOTFS/opt/topazio/core" "$ROOTFS/opt/topazio/services/http" \
  "$ROOTFS/opt/topazio/services/status" "$ROOTFS/opt/topazio/services/metrics" \
  "$ROOTFS/opt/topazio/services/console" "$ROOTFS/run/topazio"
install -m 0644 "$PROJECT_DIR/core/__init__.py" "$ROOTFS/opt/topazio/core/__init__.py"
install -m 0644 "$PROJECT_DIR/core/status.py" "$ROOTFS/opt/topazio/core/status.py"
install -m 0644 "$PROJECT_DIR/services/http/topazio_http.py" "$ROOTFS/opt/topazio/services/http/topazio_http.py"
install -m 0644 "$PROJECT_DIR/services/status/topazio_status.py" "$ROOTFS/opt/topazio/services/status/topazio_status.py"
install -m 0644 "$PROJECT_DIR/services/metrics/topazio_metrics.py" "$ROOTFS/opt/topazio/services/metrics/topazio_metrics.py"
install -m 0644 "$PROJECT_DIR/services/console/topazio_console.py" "$ROOTFS/opt/topazio/services/console/topazio_console.py"
install -m 0644 "$PROJECT_DIR/core/rootfs/etc/topazio/feature-contract.json" "$ROOTFS/opt/topazio/feature-contract.json"

for entry in status metrics console; do
  cat >"$ROOTFS/usr/local/bin/topazio-$entry" <<EOF_ENTRY
#!/bin/sh
exec /usr/bin/python3 /opt/topazio/services/$entry/topazio_$entry.py "\$@"
EOF_ENTRY
  chmod 0755 "$ROOTFS/usr/local/bin/topazio-$entry"
done
cat >"$ROOTFS/usr/local/bin/topazio-http" <<'HTTP_ENTRY'
#!/bin/sh
exec /usr/bin/python3 /opt/topazio/services/http/topazio_http.py "$@"
HTTP_ENTRY
chmod 0755 "$ROOTFS/usr/local/bin/topazio-http"
install -m 0644 "$PROJECT_DIR/services/systemd/topazio-status.service" "$ROOTFS/etc/systemd/system/topazio-status.service"
install -m 0644 "$PROJECT_DIR/services/systemd/topazio-metrics.service" "$ROOTFS/etc/systemd/system/topazio-metrics.service"
install -m 0644 "$PROJECT_DIR/services/systemd/topazio-http.service" "$ROOTFS/etc/systemd/system/topazio-http.service"
install -m 0644 "$PROJECT_DIR/services/systemd/topazio-console.service" "$ROOTFS/etc/systemd/system/topazio-console.service"

echo "[5/8] enabling services"
systemctl --root="$ROOTFS" enable systemd-networkd.service systemd-resolved.service \
  ssh.service topazio-status.service topazio-metrics.service topazio-http.service \
  topazio-console.service serial-getty@ttyAMA0.service \
  >"$LOGS/systemd-enable.log" 2>&1
ln -snf /run/systemd/resolve/stub-resolv.conf "$ROOTFS/etc/resolv.conf"

echo "[6/8] cleaning and recording packages"
chroot "$ROOTFS" dpkg-query -W -f='${Package}\t${Version}\n' | sort >"$MANIFESTS/packages.tsv"
chroot "$ROOTFS" apt-get clean >"$LOGS/apt-clean.log" 2>&1
rm -rf "$ROOTFS/var/lib/apt/lists/"*
rm -f "$ROOTFS/usr/bin/qemu-aarch64-static" "$ROOTFS/usr/sbin/policy-rc.d"

echo "[7/8] creating ext4 disk image: $IMAGE_SIZE"
truncate -s "$IMAGE_SIZE" "$IMAGE"
mkfs.ext4 -F -L TOPAZIO "$IMAGE" >"$LOGS/mkfs.ext4.log" 2>&1
MOUNT_DIR="$(mktemp -d)"
cleanup_mount() {
  if mountpoint -q "$MOUNT_DIR"; then umount "$MOUNT_DIR"; fi
  rmdir "$MOUNT_DIR" 2>/dev/null || true
}
trap cleanup_mount EXIT
mount -o loop "$IMAGE" "$MOUNT_DIR"
cp -a "$ROOTFS"/. "$MOUNT_DIR"/
sync
umount "$MOUNT_DIR"
trap - EXIT
rmdir "$MOUNT_DIR"
trap cleanup_work EXIT

KERNEL="$(find "$ROOTFS/boot" -maxdepth 1 -type f -name 'vmlinuz-*' -print | sort | tail -n 1)"
INITRD="$(find "$ROOTFS/boot" -maxdepth 1 -type f -name 'initrd.img-*' -print | sort | tail -n 1)"
[[ -n "$KERNEL" ]] || { echo "no Debian arm64 kernel found" >&2; exit 1; }
[[ -n "$INITRD" ]] || { echo "no Debian arm64 initramfs found" >&2; exit 1; }
mkdir -p "$OUT_DIR/images" "$OUT_DIR/kernel" "$OUT_DIR/rootfs"
cp "$IMAGE" "$FINAL_IMAGE"
cp "$KERNEL" "$OUT_DIR/kernel/vmlinuz"
cp "$INITRD" "$OUT_DIR/kernel/initrd.img"
tar --numeric-owner --sort=name --mtime="@$BUILD_EPOCH" -C "$ROOTFS" -cf - . | gzip -n >"$OUT_DIR/rootfs/topazio-arm64-rootfs.tar.gz"
KERNEL_REL="kernel/vmlinuz"
IMAGE_SHA256="$(sha256sum "$FINAL_IMAGE" | awk '{print $1}')"
ROOTFS_SHA256="$(find "$ROOTFS" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
AUTHORIZED="false"
[[ -n "${TOPAZIO_AUTHORIZED_KEY_FILE:-}" ]] && AUTHORIZED="true"
cat >"$MANIFESTS/topazio-arm64.json" <<EOF_MANIFEST
{
  "schema": 2,
  "project": "Topazio Mobile Server OS",
  "commit": "$COMMIT",
  "built_at_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_date_epoch": $BUILD_EPOCH,
  "distribution": "$DISTRO",
  "architecture": "$ARCH",
  "machine": "qemu virt",
  "mirror": "$MIRROR",
  "kernel": "$KERNEL_REL",
  "initrd": "kernel/initrd.img",
  "image": {
    "path": "images/topazio-arm64.ext4",
    "bytes": $(stat -c '%s' "$FINAL_IMAGE"),
    "sha256": "$IMAGE_SHA256"
  },
  "rootfs_archive": "rootfs/topazio-arm64-rootfs.tar.gz",
  "rootfs_tree_sha256": "$ROOTFS_SHA256",
  "packages_manifest": "manifests/packages.tsv",
  "services": ["topazio-status", "topazio-metrics", "topazio-http", "topazio-console"],
  "ssh": {"port": 22, "admin_password": "disabled", "authorized_key_injected": $AUTHORIZED},
  "network": {"mode": "qemu-user-net", "http_guest_port": 8787},
  "boot_marker": "TOPAZIO_BOOT_OK"
}
EOF_MANIFEST

echo "[8/8] build complete"
echo "rootfs_archive=$OUT_DIR/rootfs/topazio-arm64-rootfs.tar.gz"
echo "image=$FINAL_IMAGE"
echo "manifest=$MANIFESTS/topazio-arm64.json"
echo "kernel=$OUT_DIR/kernel/vmlinuz"
