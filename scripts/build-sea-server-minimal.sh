#!/usr/bin/env bash
set -u
set -o pipefail

# PC/WSL-only research build. It never addresses a phone or creates boot.img.
# The official source checkout is never patched in place: a detached temporary
# worktree receives the explicit SERVER_MINIMAL layer.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${TOPAZIO_SEA_KERNEL_SOURCE:-/root/topazio-sea-source}"
output_dir="${TOPAZIO_SEA_SERVER_OUTPUT:-${repo_root}/build/out/sea-server-minimal}"
build_dir="${TOPAZIO_SEA_SERVER_BUILD:-/root/topazio-sea-server-build}"
toolchain_bin="${TOPAZIO_SEA_CLANG_BIN:-/root/android-clang/clang-r433403b/bin}"
toolchain_checkout="${TOPAZIO_SEA_CLANG_CHECKOUT:-/root/android-clang}"
expected_source_commit="6f6b84e0e2fa8d474db66798a051ec1835257729"
expected_toolchain_commit="0625305092d0cfa7e28b0e1b268aff1d3d751eca"
expected_clang_sha256="ea2fd6ab23df6601d88d0198fd3444e608b08341a2da5c0d219f708ac93c944e"
expected_lld_sha256="a2abf2aca9ff6e7545676cac2cbd2759dd11d98572c84c13e5709d192a430b74"
fragment="$repo_root/devices/xiaomi-sea/server-minimal/config/topazio_sea_server_defconfig"
patch_file="$repo_root/devices/xiaomi-sea/server-minimal/patches/0001-focaltech-no-auto-upgrade.patch"
log_file="$output_dir/build.log"
manifest_file="$output_dir/manifest.json"

mkdir -p "$output_dir"
status="BLOCKED"
reason="prerequisites were not validated"
make_rc=127
source_commit="UNKNOWN"
toolchain_status="NOT_CHECKED"
compiler="clang-r433403b"
start_epoch="$(date +%s)"
worktree_parent=""
patched_source=""

if [[ "${1:-}" == "--help" ]]; then
    echo "PC-only SERVER_MINIMAL sea research build"
    echo "Environment: TOPAZIO_SEA_KERNEL_SOURCE, TOPAZIO_SEA_SERVER_OUTPUT,"
    echo "TOPAZIO_SEA_SERVER_BUILD, TOPAZIO_SEA_CLANG_BIN, TOPAZIO_SEA_CLANG_CHECKOUT"
    exit 0
fi

cleanup_worktree() {
    if [[ -n "$patched_source" && -d "$patched_source" ]]; then
        git -C "$source_dir" worktree remove --force "$patched_source" >/dev/null 2>&1 || true
    fi
    if [[ -n "$worktree_parent" && -d "$worktree_parent" ]]; then
        rmdir "$worktree_parent" >/dev/null 2>&1 || true
    fi
}
trap cleanup_worktree EXIT

if [[ -d "$source_dir/.git" ]]; then
    source_commit="$(git -C "$source_dir" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
fi

if [[ "$source_commit" != "$expected_source_commit" ]]; then
    reason="official sea-t-oss source checkout is missing or not at the recorded commit"
elif [[ -n "$(git -C "$source_dir" status --porcelain 2>/dev/null)" ]]; then
    reason="official source checkout is dirty; refusing to build"
elif [[ ! -f "$source_dir/arch/arm64/configs/sea_defconfig" || ! -f "$source_dir/firmware/Makefile" ]]; then
    reason="official source checkout is incomplete"
elif [[ ! -x "$toolchain_bin/clang" || ! -x "$toolchain_bin/ld.lld" ]]; then
    reason="recorded clang-r433403b toolchain is missing"
elif [[ "$(git -C "$toolchain_checkout" rev-parse HEAD 2>/dev/null || echo UNKNOWN)" != "$expected_toolchain_commit" ]]; then
    reason="clang-r433403b checkout is not the recorded Android tag commit"
elif [[ "$(sha256sum "$toolchain_bin/clang" 2>/dev/null | awk '{print $1}')" != "$expected_clang_sha256" ]]; then
    reason="clang binary SHA-256 does not match provenance"
elif [[ "$(sha256sum "$toolchain_bin/ld.lld" 2>/dev/null | awk '{print $1}')" != "$expected_lld_sha256" ]]; then
    reason="ld.lld binary SHA-256 does not match provenance"
elif [[ ! -f "$fragment" || ! -f "$patch_file" ]]; then
    reason="SERVER_MINIMAL config or patch layer is missing"
elif [[ -e "$build_dir" && -n "$(find "$build_dir" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
    reason="build directory is not empty; refusing to overwrite an existing build"
else
    worktree_parent="$(mktemp -d -p /tmp topazio-sea-server-source.XXXXXX)"
    patched_source="$worktree_parent/source"
    mkdir -p "$build_dir"
    : > "$log_file"
    if ! git -C "$source_dir" -c core.autocrlf=false -c core.eol=lf worktree add --detach "$patched_source" "$expected_source_commit" >>"$log_file" 2>&1; then
        reason="unable to create detached source worktree"
    elif ! sed -i 's/\r$//' "$patched_source/drivers/input/touchscreen/mediatek/ft3418_i2c/focaltech_config.h" "$patched_source/drivers/input/touchscreen/mediatek/ft3418_i2c/focaltech_flash.c"; then
        reason="unable to normalize temporary Focaltech source line endings"
    elif ! git -C "$patched_source" apply --check --unidiff-zero "$patch_file" >>"$log_file" 2>&1; then
        reason="SERVER_MINIMAL patch does not apply cleanly to the pinned source"
    elif ! git -C "$patched_source" apply --unidiff-zero "$patch_file" >>"$log_file" 2>&1; then
        reason="SERVER_MINIMAL patch application failed"
    else
        mkdir -p "$build_dir"
        python3 "$repo_root/host-tools/server_minimal_config.py" \
            --base "$patched_source/arch/arm64/configs/sea_defconfig" \
            --fragment "$fragment" \
            --output "$build_dir/.config" \
            --report "$output_dir/config-diff.json" >>"$log_file" 2>&1
        config_rc=$?
        if [[ "$config_rc" -ne 0 ]]; then
            make_rc="$config_rc"
            reason="SERVER_MINIMAL critical-config validation failed"
        else
            export PATH="$toolchain_bin:$PATH"
            build_command="make -C $patched_source O=$build_dir ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LLVM=1 LLVM_IAS=1 CC=clang LD=ld.lld KCONFIG_CONFIG=$build_dir/.config CFLAGS_KERNEL=-Wno-unused-but-set-variable -j2 olddefconfig Image.gz modules dtbs"
            make -C "$patched_source" O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LLVM=1 LLVM_IAS=1 CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump READELF=llvm-readelf STRIP=llvm-strip LLVM=1 LLVM_IAS=1 KCONFIG_CONFIG="$build_dir/.config" olddefconfig >>"$log_file" 2>&1
            make_rc=$?
            if [[ "$make_rc" -eq 0 ]]; then
                make -C "$patched_source" O="$build_dir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LLVM=1 LLVM_IAS=1 CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump READELF=llvm-readelf STRIP=llvm-strip KCONFIG_CONFIG="$build_dir/.config" CFLAGS_KERNEL=-Wno-unused-but-set-variable -j2 Image.gz modules dtbs >>"$log_file" 2>&1
                make_rc=$?
            fi
            if [[ "$make_rc" -eq 0 && -s "$build_dir/arch/arm64/boot/Image.gz" ]]; then
                status="BUILT_UNTESTED"
                reason="Image.gz was produced out-of-tree; DTB and hardware remain independently unverified"
            elif [[ "$make_rc" -eq 0 ]]; then
                reason="make returned success but no Image.gz was produced"
            else
                reason="kernel make failed; inspect build.log"
            fi
            toolchain_status="VERIFIED"
        fi
    fi
fi

duration_seconds="$(( $(date +%s) - start_epoch ))"
python3 - "$manifest_file" "$source_commit" "$status" "$reason" "$make_rc" "$toolchain_status" "$duration_seconds" "${build_command:-}" "$build_dir" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

path, commit, status, reason, make_rc, toolchain_status, duration, command, build_dir = sys.argv[1:]
root = Path(path).parent
log_path = root / "build.log"
log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
outputs = []
for candidate in [
    Path(build_dir) / "arch/arm64/boot/Image.gz",
    Path(build_dir) / "arch/arm64/boot/Image",
]:
    if candidate.is_file() and candidate.stat().st_size:
        outputs.append({"path": str(candidate), "size": candidate.stat().st_size, "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()})
manifest = {
    "schema": 1,
    "device": "xiaomi-sea",
    "profile": "SERVER_MINIMAL",
    "status": status,
    "source_commit": commit,
    "toolchain": {
        "name": "clang-r433403b",
        "commit": "0625305092d0cfa7e28b0e1b268aff1d3d751eca",
        "compiler": "clang",
        "linker": "ld.lld",
        "status": toolchain_status,
    },
    "config": "config-diff.json",
    "patch": "devices/xiaomi-sea/server-minimal/patches/0001-focaltech-no-auto-upgrade.patch",
    "command": command,
    "duration_seconds": int(duration),
    "make_exit_code": int(make_rc),
    "log": "build.log",
    "outputs": outputs,
    "dtb": "BLOCKED unless independently evidenced",
    "warnings_and_errors": "see build.log",
    "warning_count": log_text.count("warning:"),
    "error_count": log_text.count("error:"),
    "writes_to_device": False,
    "boot_image_created": False,
    "reason": reason,
}
(root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

cat "$manifest_file"
[[ "$status" == "BUILT_UNTESTED" ]]
