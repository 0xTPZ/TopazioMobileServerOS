"""Validate fail-closed reconstruction profiles and patch ordering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ARTIFACT_STATES = {
    "SOURCE_ONLY",
    "BUILDABLE",
    "BUILT_UNTESTED",
    "HARDWARE_TEST_REQUIRED",
    "WORKING",
    "BLOCKED",
    "DESIGN_ONLY",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("reconstruction manifest must be an object")
    return value


def validate(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != 1:
        errors.append("reconstruction schema must be 1")
    profiles = record.get("profiles")
    if not isinstance(profiles, dict):
        return errors + ["profiles must be an object"]
    for name in ("VENDOR_REFERENCE", "SERVER_MINIMAL"):
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            errors.append(f"missing profile: {name}")
            continue
        if profile.get("status") not in ARTIFACT_STATES:
            errors.append(f"invalid profile state: {name}")
        for output, state in profile.get("outputs", {}).items():
            if state not in ARTIFACT_STATES:
                errors.append(f"invalid artifact state {output}: {name}")
        patches = profile.get("patches")
        if not isinstance(patches, list):
            errors.append(f"patch list must be a list: {name}")
        elif patches:
            numbers = [item.get("order") for item in patches if isinstance(item, dict)]
            if numbers != list(range(1, len(numbers) + 1)):
                errors.append(f"patch order is not contiguous: {name}")
    if profiles.get("VENDOR_REFERENCE", {}).get("status") == "WORKING":
        errors.append("VENDOR_REFERENCE cannot be WORKING in mission 005")
    if profiles.get("SERVER_MINIMAL", {}).get("status") != "DESIGN_ONLY":
        errors.append("SERVER_MINIMAL must remain DESIGN_ONLY")
    top_order = record.get("patch_order")
    if not isinstance(top_order, list):
        errors.append("patch_order must be a list")
    elif top_order and top_order != list(range(1, len(top_order) + 1)):
        errors.append("top-level patch_order is not contiguous")
    return errors


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "devices/xiaomi-sea/reconstruction/manifest.json"
    errors = validate(load(path))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"reconstruction manifest valid: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
