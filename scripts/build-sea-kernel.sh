#!/usr/bin/env bash
set -u

# PC-only research build. This script never invokes adb, fastboot, flashing,
# partition tools, or a phone transport. It does not modify the source tree.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${TOPAZIO_SEA_KERNEL_SOURCE:-/root/topazio-sea-source}"
output_dir="${TOPAZIO_SEA_KERNEL_OUTPUT:-${repo_root}/build/out/sea-kernel}"
build_dir="${TOPAZIO_SEA_KERNEL_BUILD:-/root/topazio-sea-build}"
log_file="${output_dir}/build.log"
manifest_file="${output_dir}/manifest.json"

mkdir -p "$output_dir"
status="BLOCKED"
reason="source or build prerequisites were not validated"
make_rc=127
source_commit="UNKNOWN"

if [[ -d "$source_dir/.git" ]]; then
    source_commit="$(git -C "$source_dir" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
else
    reason="official sea-t-oss source checkout is missing"
fi

if [[ "$source_commit" != "6f6b84e0e2fa8d474db66798a051ec1835257729" ]]; then
    reason="source checkout is not the recorded official sea-t-oss commit"
elif [[ ! -f "$source_dir/arch/arm64/configs/sea_defconfig" ]]; then
    reason="sea_defconfig is missing from source checkout"
elif [[ ! -f "$source_dir/arch/arm64/boot/dts/mediatek/sea.dts" ]]; then
    reason="sea.dts is missing from source checkout"
else
    mkdir -p "$build_dir"
    : > "$log_file"
    make -C "$source_dir" O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- sea_defconfig >>"$log_file" 2>&1
    make_rc=$?
    if [[ "$make_rc" -eq 0 ]]; then
        make -C "$source_dir" O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j2 Image.gz dtbs >>"$log_file" 2>&1
        make_rc=$?
    fi
    if [[ "$make_rc" -eq 0 && -s "$build_dir/arch/arm64/boot/Image.gz" ]]; then
        if [[ -s "$build_dir/arch/arm64/boot/dts/mediatek/sea.dtb" ]]; then
            status="BUILDABLE"
            reason="Image.gz and sea.dtb were produced out-of-tree"
        else
            reason="Image.gz built but the public Makefile produced no sea.dtb"
        fi
    elif [[ "$make_rc" -eq 0 ]]; then
        reason="make returned success but no Image.gz was produced"
    else
        reason="kernel make failed; inspect build.log"
    fi
fi

python3 - "$manifest_file" "$source_commit" "$status" "$reason" "$make_rc" <<'PY'
import json
import sys
from pathlib import Path

path, commit, status, reason, make_rc = sys.argv[1:]
Path(path).write_text(json.dumps({
    "schema": 1,
    "device": "xiaomi-sea",
    "status": status,
    "source_commit": commit,
    "make_exit_code": int(make_rc),
    "reason": reason,
    "writes_to_device": False,
    "artifacts_copied": False,
}, indent=2) + "\n", encoding="utf-8")
PY

cat "$manifest_file"
[[ "$status" == "BUILDABLE" ]]
