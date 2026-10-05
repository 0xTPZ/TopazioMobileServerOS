"""Validate the immutable Mission 007 SERVER_MINIMAL kernel baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _compare(actual: Any, expected: Any, label: str, errors: list[str]) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected!r}, got {actual!r}")


def validate_baseline(
    baseline: dict[str, Any],
    gate: dict[str, Any],
    repo_root: Path,
    *,
    require_files: bool = False,
) -> list[str]:
    errors: list[str] = []
    if baseline.get("baseline_id") != "SEA_SERVER_MINIMAL_KERNEL_001":
        errors.append("unexpected baseline id")

    _compare(gate.get("source"), baseline.get("source"), "source", errors)
    for field in ("name", "commit", "compiler", "linker"):
        _compare(
            gate.get("toolchain", {}).get(field),
            baseline.get("toolchain", {}).get(field),
            f"toolchain.{field}",
            errors,
        )
    gate_config = gate.get("configuration", {})
    expected_config = baseline.get("configuration", {})
    _compare(
        gate_config.get("fragment"),
        expected_config.get("fragment"),
        "configuration.fragment",
        errors,
    )
    _compare(
        gate_config.get("fragment_sha256"),
        expected_config.get("fragment_sha256"),
        "configuration.fragment_sha256",
        errors,
    )

    gate_patches = {
        item.get("file"): item.get("sha256") for item in gate.get("patches", [])
    }
    for patch in baseline.get("patches", []):
        path = patch.get("path")
        _compare(gate_patches.get(path), patch.get("sha256"), f"patch {path}", errors)
        local = repo_root / path
        if not local.is_file():
            errors.append(f"patch missing: {path}")
        elif _sha256(local) != patch.get("sha256"):
            errors.append(f"patch hash changed: {path}")

    gate_artifacts = gate.get("artifacts", {})
    expected_artifacts = baseline.get("artifacts", {})
    for key in ("image", "image_gz", "system_map", "config"):
        artifact = expected_artifacts.get(key, {})
        if not isinstance(artifact, dict) or "path" not in artifact:
            continue
        path = artifact["path"]
        gate_entry = gate_artifacts.get(key)
        if gate_entry is not None:
            if "size_bytes" in gate_entry:
                _compare(gate_entry.get("size_bytes"), artifact.get("size_bytes"), f"artifact {path} size", errors)
            if "sha256" in gate_entry:
                _compare(gate_entry.get("sha256"), artifact.get("sha256"), f"artifact {path} hash", errors)
        local = repo_root / path
        if not local.is_file():
            if require_files:
                errors.append(f"artifact missing: {path}")
            continue
        _compare(local.stat().st_size, artifact.get("size_bytes"), f"artifact {path} local size", errors)
        _compare(_sha256(local), artifact.get("sha256"), f"artifact {path} local hash", errors)

    for artifact in expected_artifacts.get("modules", []):
        path = artifact["path"]
        local = repo_root / path
        if not local.is_file():
            if require_files:
                errors.append(f"artifact missing: {path}")
            continue
        _compare(local.stat().st_size, artifact.get("size_bytes"), f"artifact {path} local size", errors)
        _compare(_sha256(local), artifact.get("sha256"), f"artifact {path} local hash", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-files", action="store_true")
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    gate = json.loads(args.gate.read_text(encoding="utf-8"))
    errors = validate_baseline(
        baseline,
        gate,
        args.repo_root.resolve(),
        require_files=args.require_files,
    )
    if errors:
        print("\n".join(errors))
        return 1
    print("kernel baseline verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
