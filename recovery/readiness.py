"""Evaluate recovery prerequisites without touching a device."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Readiness:
    decision: str
    missing: tuple[str, ...]


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
