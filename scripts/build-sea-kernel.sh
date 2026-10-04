#!/usr/bin/env bash
set -u
set -o pipefail

# PC-only research build. This script never invokes adb, fastboot, flashing,
# partition tools, or a phone transport. It does not modify the source tree.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${TOPAZIO_SEA_KERNEL_SOURCE:-/root/topazio-sea-source}"
output_dir="${TOPAZIO_SEA_KERNEL_OUTPUT:-${repo_root}/build/out/sea-kernel}"
build_dir="${TOPAZIO_SEA_KERNEL_BUILD:-/root/topazio-sea-build}"
toolchain_bin="${TOPAZIO_SEA_CLANG_BIN:-/root/android-clang/clang-r433403b/bin}"
toolchain_checkout="${TOPAZIO_SEA_CLANG_CHECKOUT:-/root/android-clang}"
expected_toolchain_commit="0625305092d0cfa7e28b0e1b268aff1d3d751eca"
expected_clang_sha256="ea2fd6ab23df6601d88d0198fd3444e608b08341a2da5c0d219f708ac93c944e"
expected_lld_sha256="a2abf2aca9ff6e7545676cac2cbd2759dd11d98572c84c13e5709d192a430b74"
log_file="${output_dir}/build.log"
manifest_file="${output_dir}/manifest.json"

mkdir -p "$output_dir"
status="BLOCKED"
reason="source or build prerequisites were not validated"
make_rc=127
source_commit="UNKNOWN"
toolchain_status="NOT_CHECKED"
compiler="clang-r433403b"

if [[ "${1:-}" == "--help" ]]; then
    echo "PC-only sea kernel research build"
    echo "Environment: TOPAZIO_SEA_KERNEL_SOURCE, TOPAZIO_SEA_KERNEL_OUTPUT,"
    echo "TOPAZIO_SEA_KERNEL_BUILD, TOPAZIO_SEA_CLANG_BIN"
    exit 0
fi

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
elif [[ -n "$(git -C "$source_dir" status --porcelain 2>/dev/null)" ]]; then
    reason="official source checkout is dirty; refusing to build"
elif [[ ! -x "$toolchain_bin/clang" || ! -x "$toolchain_bin/ld.lld" ]]; then
    reason="recorded clang-r433403b toolchain is missing"
elif [[ "$(git -C "$toolchain_checkout" rev-parse HEAD 2>/dev/null || echo UNKNOWN)" != "$expected_toolchain_commit" ]]; then
    reason="clang-r433403b checkout is not the recorded Android tag commit"
elif [[ "$(sha256sum "$toolchain_bin/clang" 2>/dev/null | awk '{print $1}')" != "$expected_clang_sha256" ]]; then
    reason="clang binary SHA-256 does not match provenance"
elif [[ "$(sha256sum "$toolchain_bin/ld.lld" 2>/dev/null | awk '{print $1}')" != "$expected_lld_sha256" ]]; then
    reason="ld.lld binary SHA-256 does not match provenance"
elif [[ ! -f "$source_dir/firmware/Makefile" ]]; then
    reason="kernel source checkout is incomplete: firmware/Makefile is missing"
else
    mkdir -p "$build_dir"
    : > "$log_file"
    export PATH="$toolchain_bin:$PATH"
    make -C "$source_dir" O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LLVM=1 LLVM_IAS=1 CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump READELF=llvm-readelf STRIP=llvm-strip sea_defconfig >>"$log_file" 2>&1
    make_rc=$?
    if [[ "$make_rc" -eq 0 ]]; then
        toolchain_status="VERIFIED"
        make -C "$source_dir" O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LLVM=1 LLVM_IAS=1 CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump READELF=llvm-readelf STRIP=llvm-strip CFLAGS_KERNEL=-Wno-unused-but-set-variable -j2 Image.gz dtbs >>"$log_file" 2>&1
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

python3 - "$manifest_file" "$source_commit" "$status" "$reason" "$make_rc" "$toolchain_status" <<'PY'
import json
import sys
from pathlib import Path

path, commit, status, reason, make_rc, toolchain_status = sys.argv[1:]
Path(path).write_text(json.dumps({
    "schema": 2,
    "device": "xiaomi-sea",
    "status": status,
    "source_commit": commit,
    "toolchain": {
        "name": "clang-r433403b",
        "profile": "build.config.mtk.aarch64.tiramisu",
        "llvm": True,
        "llvm_ias": True,
        "compiler": "clang",
        "linker": "ld.lld",
        "cflags_kernel": "-Wno-unused-but-set-variable",
        "status": toolchain_status,
    },
    "make_exit_code": int(make_rc),
    "reason": reason,
    "source_tree_modified": False,
    "artifacts": [],
    "writes_to_device": False,
    "artifacts_copied": False,
}, indent=2) + "\n", encoding="utf-8")
PY

cat "$manifest_file"
[[ "$status" == "BUILDABLE" ]]
