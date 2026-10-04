"""Validate required project structure and metadata."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "AGENTS.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "DECISOES.md",
    "docs/ARCHITECTURE.md",
    "docs/VISION.md",
    "docs/ROADMAP.md",
    "docs/BUILD.md",
    "docs/RECOVERY.md",
    "docs/INSTALLER.md",
    "docs/DEVICE-SUPPORT.md",
    "docs/SECURITY-MODEL.md",
    "docs/UI-CONSOLE.md",
    "docs/RESEARCH.md",
    "docs/HANDOFF.md",
    "devices/xiaomi-sea/README.md",
    "devices/xiaomi-sea/HARDWARE.md",
    "devices/xiaomi-sea/BOOT.md",
    "devices/xiaomi-sea/STATUS.md",
    "devices/xiaomi-sea/device.json",
]


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    for marker in (".env", "*.pem", "*.img", "**/firmware/**", "dumps/"):
        if marker not in gitignore:
            errors.append(f".gitignore missing guard: {marker}")
    try:
        device = json.loads((root / "devices/xiaomi-sea/device.json").read_text(encoding="utf-8"))
        if device.get("support_state") != "RESEARCH":
            errors.append("sea DSP must remain RESEARCH until evidence changes")
        if device.get("installable") is not False:
            errors.append("sea DSP must not be installable in mission 001")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid sea DSP metadata: {exc}")
    if "Apache License" not in (root / "LICENSE").read_text(encoding="utf-8"):
        errors.append("LICENSE is not Apache-2.0 text")
    if "RESEARCH" not in (root / "README.md").read_text(encoding="utf-8"):
        errors.append("README must state research status")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"repository structure valid: {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
