"""Validate a generated Topazio ARM64 artifact bundle."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_SERVICES = {
    "topazio-status",
    "topazio-metrics",
    "topazio-http",
    "topazio-console",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_path(root: Path, relative: str, errors: list[str]) -> Path | None:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        errors.append(f"artifact path escapes bundle: {relative}")
        return None
    if not path.is_file():
        errors.append(f"missing artifact file: {relative}")
        return None
    return path


def validate(root: Path) -> list[str]:
    """Return validation errors for ``build/out/arm64``."""

    errors: list[str] = []
    manifest_path = root / "manifests/topazio-arm64.json"
    if not manifest_path.is_file():
        return [f"missing artifact manifest: {manifest_path}"]
    try:
        manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid artifact manifest: {exc}"]

    if manifest.get("architecture") != "arm64":
        errors.append("artifact architecture must be arm64")
    if manifest.get("machine") != "qemu virt":
        errors.append("artifact machine must be qemu virt")
    if manifest.get("boot_marker") != "TOPAZIO_BOOT_OK":
        errors.append("artifact boot marker is missing")
    if set(manifest.get("services", [])) != REQUIRED_SERVICES:
        errors.append("artifact service contract is incomplete")

    image_info = manifest.get("image", {})
    image_relative = image_info.get("path")
    image = _artifact_path(root, image_relative, errors) if isinstance(image_relative, str) else None
    if image is None and not isinstance(image_relative, str):
        errors.append("artifact image path is missing")
    if image is not None:
        expected_bytes = image_info.get("bytes")
        if expected_bytes != image.stat().st_size:
            errors.append("artifact image byte count does not match manifest")
        expected_sha = image_info.get("sha256")
        if not isinstance(expected_sha, str) or _sha256(image) != expected_sha:
            errors.append("artifact image SHA-256 does not match manifest")

    for field in ("kernel", "initrd", "rootfs_archive", "packages_manifest"):
        relative = manifest.get(field)
        if not isinstance(relative, str):
            errors.append(f"artifact manifest field is missing: {field}")
        else:
            _artifact_path(root, relative, errors)

    ssh = manifest.get("ssh", {})
    if ssh.get("admin_password") != "disabled":
        errors.append("artifact must disable the admin password")
    if manifest.get("network", {}).get("http_guest_port") != 8787:
        errors.append("artifact HTTP guest port must be 8787")
    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/out/arm64")
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"ARM64 artifact valid: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
