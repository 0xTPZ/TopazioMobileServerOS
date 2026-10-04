"""Validate static sea kernel/device-tree artifacts without packaging them."""

from __future__ import annotations

import hashlib
from pathlib import Path


FDT_MAGIC = b"\xd0\x0d\xfe\xed"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(path: Path, kind: str, expected_sha256: str | None = None) -> list[str]:
    errors: list[str] = []
    if path.name in {"boot.img", "vendor_boot.img", "init_boot.img", "vbmeta.img"}:
        return [f"Android boot packaging is prohibited in this mission: {path.name}"]
    if not path.is_file() or path.stat().st_size == 0:
        return [f"artifact is missing or empty: {path}"]
    if kind in {"dtb", "dtbo"} and path.read_bytes()[:4] != FDT_MAGIC:
        errors.append(f"{kind} does not start with the FDT magic")
    if kind == "Image.gz" and path.read_bytes()[:2] != b"\x1f\x8b":
        errors.append("Image.gz does not start with the gzip magic")
    if expected_sha256 is not None and sha256(path) != expected_sha256:
        errors.append("artifact SHA-256 does not match the expected value")
    return errors


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("kind", choices=("Image.gz", "dtb", "dtbo"))
    parser.add_argument("--sha256")
    args = parser.parse_args()
    problems = validate(args.path, args.kind, args.sha256)
    for problem in problems:
        print(f"ERROR: {problem}")
    raise SystemExit(1 if problems else 0)
