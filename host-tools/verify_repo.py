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
    "docs/QEMU-LAB.md",
    "host-tools/validate_arm64_artifact.py",
    "scripts/build-arm64.sh",
    "scripts/run-qemu.sh",
    "scripts/smoke-qemu.sh",
    "scripts/build.ps1",
    "scripts/run-qemu.ps1",
    "scripts/test.ps1",
    "services/status/topazio_status.py",
    "services/metrics/topazio_metrics.py",
    "services/console/topazio_console.py",
    "services/systemd/topazio-status.service",
    "services/systemd/topazio-metrics.service",
    "services/systemd/topazio-http.service",
    "services/systemd/topazio-console.service",
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
    feature_path = root / "core/rootfs/etc/topazio/feature-contract.json"
    try:
        feature = json.loads(feature_path.read_text(encoding="utf-8"))
        if feature.get("validation_scope") != "qemu-virt-only":
            errors.append("feature contract must scope boot validation to qemu-virt-only")
        if feature.get("phone_support") is not False:
            errors.append("feature contract must not claim phone support")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid feature contract: {exc}")
    artifact_manifest = root / "build/out/arm64/manifests/topazio-arm64.json"
    if artifact_manifest.is_file():
        try:
            from importlib.util import module_from_spec, spec_from_file_location

            validator_path = root / "host-tools/validate_arm64_artifact.py"
            spec = spec_from_file_location("topazio_artifact_validator", validator_path)
            if spec is None or spec.loader is None:
                errors.append("unable to load ARM64 artifact validator")
            else:
                validator = module_from_spec(spec)
                spec.loader.exec_module(validator)
                errors.extend(validator.validate(root / "build/out/arm64"))
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"unable to validate ARM64 artifact: {exc}")
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
