"""Evaluate recovery prerequisites without touching a device."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Readiness:
    decision: str
    missing: tuple[str, ...]


def evaluate_manifest(manifest: dict, evidence: dict | None = None) -> Readiness:
    """Evaluate a DSP manifest without opening a transport or writing a device."""

    evidence = evidence or {}
    checks = {
        "identity": evidence.get("exact_unit_identity") is True,
        "exact-dsp": manifest.get("codename") == "sea" and manifest.get("model") == "Redmi Note 12S",
        "backup": evidence.get("backup_verified") is True,
        "recovery-procedure": evidence.get("recovery_procedure_verified") is True,
        "artifact-hashes": evidence.get("compatible_artifacts_hashed") is True,
        "permitted-partitions": evidence.get("permitted_partitions_enumerated") is True,
        "stock-firmware": evidence.get("stock_firmware_hashed") is True,
    }
    missing = tuple(name for name, passed in checks.items() if not passed)
    if manifest.get("support_state") == "RESEARCH" or manifest.get("installable") is not True:
        missing += ("dsp-installable",)
    return Readiness("READY" if not missing else "BLOCKED", missing)


def evaluate(
    *,
    identity_confirmed: bool,
    exact_dsp: bool,
    backup_verified: bool,
    recovery_procedure_verified: bool,
    artifacts_hashed: bool,
    permitted_partitions_enumerated: bool,
) -> Readiness:
    checks = {
        "identity": identity_confirmed,
        "exact-dsp": exact_dsp,
        "backup": backup_verified,
        "recovery-procedure": recovery_procedure_verified,
        "artifact-hashes": artifacts_hashed,
        "permitted-partitions": permitted_partitions_enumerated,
    }
    missing = tuple(name for name, passed in checks.items() if not passed)
    return Readiness("READY" if not missing else "BLOCKED", missing)
