"""Evaluate recovery readiness from local metadata only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from device_manifest import load_manifest


CHECKS = (
    "exact_unit_identity",
    "stock_firmware_hashed",
    "backup_verified",
    "permitted_partitions_enumerated",
    "recovery_procedure_verified",
    "compatible_artifacts_hashed",
)


def evaluate(manifest: dict, evidence: dict | None = None) -> dict:
    evidence = evidence or {}
    missing = [name for name in CHECKS if evidence.get(name) is not True]
    dsp_blocked = manifest.get("support_state") == "RESEARCH" or manifest.get("installable") is not True
    if dsp_blocked:
        missing.append("DSP_not_installable")
    if dsp_blocked or not evidence:
        decision = "BLOCKED"
    elif missing:
        decision = "NOT_READY"
    else:
        decision = "READY"
    return {
        "decision": decision,
        "missing": sorted(set(missing)),
        "writes_performed": False,
        "device_access": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DSP recovery prerequisites without device I/O")
    parser.add_argument("--device", default="xiaomi-sea")
    parser.add_argument("--evidence", type=Path, help="optional JSON evidence fixture")
    args = parser.parse_args()
    manifest_path = Path("devices") / args.device / "device.json"
    manifest = load_manifest(manifest_path)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8")) if args.evidence else {}
    result = evaluate(manifest, evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
