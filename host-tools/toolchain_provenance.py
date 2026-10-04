"""Validate the small, text-only toolchain provenance record for sea."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(record: dict[str, Any], toolchain_dir: Path | None = None) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != 1:
        errors.append("provenance schema must be 1")
    if record.get("device") != "xiaomi-sea":
        errors.append("provenance device must be xiaomi-sea")
    toolchains = record.get("toolchains")
    if toolchains is None:
        toolchains = [
            item for item in record.get("sources", [])
            if isinstance(item, dict) and item.get("name") in {
                "Android Clang prebuilt",
                "GNU AArch64 cross compiler",
            }
        ]
    if not isinstance(toolchains, list) or not toolchains:
        return errors + ["provenance must contain toolchains"]
    for item in toolchains:
        if not isinstance(item, dict):
            errors.append("toolchain entry must be an object")
            continue
        for field in ("name", "origin", "license", "redistribution"):
            if not item.get(field):
                errors.append(f"toolchain missing: {field}")
        if not item.get("version") and not item.get("ref"):
            errors.append(f"toolchain missing: version/ref ({item.get('name')})")
        if not item.get("purpose") and not item.get("use"):
            errors.append(f"toolchain missing: purpose/use ({item.get('name')})")
        if item.get("redistribution") not in {"source-only", "public-prebuilt"}:
            errors.append(f"unsupported redistribution policy: {item.get('redistribution')}")
        hashes = item.get("sha256", {})
        if not isinstance(hashes, dict):
            errors.append(f"toolchain hashes must be an object: {item.get('name')}")
        elif item.get("redistribution") == "public-prebuilt":
            for binary in ("clang", "ld.lld"):
                if not isinstance(hashes.get(binary), str) or len(hashes[binary]) != 64:
                    errors.append(f"toolchain hash missing: {item.get('name')} {binary}")
    if toolchain_dir is not None:
        clang = toolchain_dir / "bin/clang"
        lld = toolchain_dir / "bin/ld.lld"
        clang_item = next((item for item in toolchains if item.get("name") in {
            "clang-r433403b", "Android Clang prebuilt"
        }), None)
        if clang_item is None:
            errors.append("clang-r433403b provenance entry is missing")
        else:
            for name, path in (("clang", clang), ("ld.lld", lld)):
                if not path.is_file():
                    errors.append(f"toolchain binary missing: {path}")
                elif sha256(path) != clang_item["sha256"].get(name):
                    errors.append(f"toolchain hash mismatch: {path}")
    return errors


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provenance must be an object")
    return value


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--toolchain-dir", type=Path)
    args = parser.parse_args()
    problems = validate(load(args.path), args.toolchain_dir)
    for problem in problems:
        print(f"ERROR: {problem}")
    raise SystemExit(1 if problems else 0)
