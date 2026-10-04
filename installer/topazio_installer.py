"""Read-only planning logic for Topazio Mobile Installer.

This module intentionally has no USB, ADB, fastboot, partition or subprocess
writer. Future transport adapters must feed observations into this policy layer.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DeviceObservation:
    transport: str | None = None
    vendor: str | None = None
    model: str | None = None
    codename: str | None = None
    bootloader_state: str = "UNKNOWN"
    recovery_ready: str = "UNKNOWN"
    read_only: bool = True


@dataclass(frozen=True)
class InstallPlan:
    decision: str
    reason: str
    actions: tuple[str, ...]
    observation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["actions"] = list(self.actions)
        return result


def build_plan(observation: DeviceObservation, registry: dict[str, dict[str, Any]]) -> InstallPlan:
    """Return a fail-closed plan; never perform device I/O."""

    observed = asdict(observation)
    if not observation.transport:
        return InstallPlan("NO_DEVICE", "nenhum transporte detectado", ("collect-read-only",), observed)
    if not all((observation.vendor, observation.model, observation.codename)):
        return InstallPlan("AMBIGUOUS_IDENTITY", "identidade incompleta", (), observed)
    key = f"{observation.vendor}-{observation.codename}"
    dsp = registry.get(key)
    if not dsp or dsp.get("model") != observation.model:
        return InstallPlan("UNSUPPORTED", "nenhum DSP exato para a identidade", (), observed)
    if dsp.get("support_state") not in {"SUPPORTED", "STABLE"}:
        return InstallPlan("UNSUPPORTED", "DSP ainda não atingiu suporte instalável", (), observed)
    if observation.recovery_ready != "CONFIRMED":
        return InstallPlan("BLOCKED_RECOVERY", "recovery-readiness não confirmada", (), observed)
    if observation.bootloader_state != "AUTHORIZED":
        return InstallPlan("BLOCKED_SECURITY", "bootloader exige estado autorizado explícito", (), observed)
    if not observation.read_only:
        return InstallPlan("ABORTED", "observação não está em modo somente leitura", (), observed)
    return InstallPlan(
        "READY_FOR_EXPLICIT_CONFIRMATION",
        "pré-condições de política satisfeitas; nenhuma gravação é executada",
        ("show-plan", "request-explicit-confirmation", "verify-artifact-hashes"),
        observed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only Topazio install plan")
    parser.add_argument("--observation", help="JSON observation; omitted means no device")
    args = parser.parse_args()
    raw = json.loads(args.observation) if args.observation else {}
    observation = DeviceObservation(**raw)
    registry = {
        "xiaomi-sea": {
            "model": "Redmi Note 12S",
            "support_state": "RESEARCH",
        }
    }
    print(json.dumps(build_plan(observation, registry).to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
