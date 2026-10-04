"""Read-only host observation probe.

This tool consumes a fixture or inventory file. It never invokes adb, fastboot,
USB driver installers, or any command that can write to a phone.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from device_manifest import load_manifest


def evaluate(observation: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    expected = {"vendor": manifest.get("vendor"), "model": manifest.get("model"), "codename": manifest.get("codename")}
    supplied = {key: observation.get(key) for key in expected}
    mismatches = [key for key in expected if supplied[key] is not None and supplied[key] != expected[key]]
    if mismatches:
        decision = "ABORTED_IDENTITY_MISMATCH"
        reason = "observed identity does not match the exact DSP"
    elif not observation.get("adb_seen") and not observation.get("fastboot_seen"):
        decision = "BLOCKED_NO_READ_ONLY_TRANSPORT"
        reason = "no ADB or fastboot observation was supplied"
    else:
        decision = "BLOCKED_RESEARCH_ONLY"
        reason = "transport observation is not permission to install"
    return {
        "decision": decision,
        "reason": reason,
        "installation_enabled": False,
        "read_only": True,
        "expected": expected,
        "observed": observation,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a sanitized, read-only host observation")
    parser.add_argument("--fixture", type=Path, required=True, help="JSON fixture; no USB command is executed")
    parser.add_argument("--manifest", type=Path, default=Path("devices/xiaomi-sea/device.json"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    observation = json.loads(args.fixture.read_text(encoding="utf-8"))
    manifest = load_manifest(args.manifest)
    result = evaluate(observation, manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "BLOCKED_RESEARCH_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
