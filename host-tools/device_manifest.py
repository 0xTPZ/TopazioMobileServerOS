"""Small dependency-free validator for Topazio DSP metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_EVIDENCE = {"CONFIRMED", "INFERRED", "UNKNOWN", "BLOCKED"}
ALLOWED_SUPPORT = {"RESEARCH", "SUPPORTED", "STABLE"}


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest must be an object")
    return value


def validate_manifest(manifest: dict[str, Any], root: Path | None = None) -> list[str]:
    errors: list[str] = []
    required = ("schema", "vendor", "model", "codename", "architecture", "support_state", "installable",
                "kernel_source", "required_firmware", "boot_contract", "partition_contract", "capabilities",
                "recovery", "artifact_pipeline")
    for key in required:
        if key not in manifest:
            errors.append(f"manifest missing: {key}")
    if manifest.get("schema") != 2:
        errors.append("manifest schema must be 2")
    if manifest.get("architecture") != "arm64":
        errors.append("manifest architecture must be arm64")
    if manifest.get("support_state") not in ALLOWED_SUPPORT:
        errors.append("manifest support_state is invalid")
    if not isinstance(manifest.get("installable"), bool):
        errors.append("manifest installable must be boolean")
    source = manifest.get("kernel_source", {})
    if not isinstance(source, dict):
        errors.append("kernel_source must be an object")
    else:
        for key in ("repository", "branch", "commit", "defconfig", "dts", "source_status", "build_status"):
            if key not in source:
                errors.append(f"kernel_source missing: {key}")
        if not isinstance(source.get("commit"), str) or len(source.get("commit", "")) != 40:
            errors.append("kernel_source commit must be a full hash")
        for key in ("source_status", "build_status"):
            if source.get(key) not in ALLOWED_EVIDENCE:
                errors.append(f"kernel_source {key} is invalid")
    for section in ("boot_contract", "partition_contract", "recovery", "artifact_pipeline"):
        if not isinstance(manifest.get(section), dict):
            errors.append(f"{section} must be an object")
    if isinstance(manifest.get("boot_contract"), dict) and manifest["boot_contract"].get("status") not in ALLOWED_EVIDENCE:
        errors.append("boot_contract status is invalid")
    if isinstance(manifest.get("partition_contract"), dict) and manifest["partition_contract"].get("status") not in ALLOWED_EVIDENCE:
        errors.append("partition_contract status is invalid")
    if root is not None:
        capabilities = root / "devices" / "xiaomi-sea" / str(manifest.get("capabilities", ""))
        if not capabilities.is_file():
            errors.append(f"capabilities file missing: {capabilities}")
    return errors
