#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${TOPAZIO_OUT:-$PROJECT_DIR/build/out/arm64}"
IMAGE="$OUT_DIR/images/topazio-arm64.ext4"
KERNEL="$OUT_DIR/kernel/vmlinuz"
INITRD="$OUT_DIR/kernel/initrd.img"
LOG_DIR="$OUT_DIR/logs"
SERIAL_LOG="$LOG_DIR/qemu-serial.log"

[[ -f "$IMAGE" ]] || { echo "image missing; run build-arm64.sh first" >&2; exit 2; }
[[ -f "$KERNEL" ]] || { echo "kernel missing; run build-arm64.sh first" >&2; exit 2; }
[[ -f "$INITRD" ]] || { echo "initramfs missing; rebuild with build-arm64.sh" >&2; exit 2; }
mkdir -p "$LOG_DIR"

exec qemu-system-aarch64 \
  -machine virt \
  -cpu cortex-a57 \
  -m 1024 \
  -smp 2 \
  -accel tcg \
  -kernel "$KERNEL" \
  -initrd "$INITRD" \
  -append "root=/dev/vda rw console=ttyAMA0 systemd.show_status=false" \
  -drive "if=none,file=$IMAGE,format=raw,id=drive0" \
  -device virtio-blk-device,drive=drive0 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22,hostfwd=tcp:127.0.0.1:8787-:8787 \
  -device virtio-net-device,netdev=net0 \
  -nographic \
  -serial "file:$SERIAL_LOG"
