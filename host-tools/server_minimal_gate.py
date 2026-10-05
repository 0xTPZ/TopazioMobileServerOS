"""Validate the Mission 007 SERVER_MINIMAL build gate report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


CATEGORIES = {
    "A_COMPILER_COMPATIBILITY",
    "B_MISSING_VENDOR_CONTEXT",
    "C_ACTUAL_SOURCE_BUG",
    "D_OPTIONAL_SUBSYSTEM",
    "E_CRITICAL_SUBSYSTEM",
    "F_UNKNOWN",
}
DECISIONS = {"SEA_CONTINUE", "SEA_HOLD", "SEA_FREEZE"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _check_hash(item: dict[str, Any], label: str, errors: list[str]) -> None:
    value = item.get("sha256")
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        errors.append(f"{label} does not have a lowercase SHA-256")


def validate_gate(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("schema") != 1 or report.get("mission") != 7:
        errors.append("schema or mission is not 1/7")
    reproduction = report.get("reproduction", {})
    original_errors = reproduction.get("errors", [])
    if len(original_errors) != 7:
        errors.append(f"expected 7 original errors, found {len(original_errors)}")
    if reproduction.get("error_count") != 7 or reproduction.get("make_exit_code") != 2:
        errors.append("reproduction does not record the seven-error failure")
    for item in original_errors:
        if item.get("category") not in CATEGORIES:
            errors.append(f"invalid original-error category: {item.get('category')!r}")
        if item.get("root_cause") not in CATEGORIES:
            errors.append(f"invalid original-error root cause: {item.get('root_cause')!r}")
    if report.get("new_blocker_count", 0) > 25:
        errors.append("new blocker count exceeds the Mission 007 limit")

    final = next((item for item in report.get("iterations", []) if item.get("id") == "M007-FINAL"), None)
    if final is None or final.get("make_exit_code") != 0 or final.get("error_count") != 0:
        errors.append("final iteration is not a green build")
    if report.get("artifacts", {}).get("state") != "BUILT_UNTESTED":
        errors.append("artifact state must be BUILT_UNTESTED")
    artifacts = report.get("artifacts", {})
    for key in ("image", "image_gz"):
        item = artifacts.get(key, {})
        if not isinstance(item.get("size_bytes"), int) or item["size_bytes"] <= 0:
            errors.append(f"{key} has no positive size")
        _check_hash(item, key, errors)
    if artifacts.get("module_count", 0) < 1:
        errors.append("module audit is empty")
    if artifacts.get("dtb_status") != "BLOCKED":
        errors.append("DTB status must remain BLOCKED")

    configuration = report.get("configuration", {})
    if configuration.get("charging_preserved") != ["CONFIG_MTK_CHARGER=y", "CONFIG_CHARGER_BQ2589X=y"]:
        errors.append("charging preservation evidence is incomplete")
    if configuration.get("global_werror_disabled") is not False:
        errors.append("global Werror policy was not preserved")
    command = " ".join(str(item.get("command", "")) for item in report.get("iterations", []))
    if "-Wno-error" in command or "-Wno-werror" in command:
        errors.append("global warning-to-error policy was disabled")

    for patch in report.get("patches", []):
        required = {"id", "file", "problem", "category", "justification", "source_evidence", "impact", "risk", "subsystem", "reversibility", "sha256"}
        missing = sorted(required - patch.keys())
        if missing:
            errors.append(f"patch {patch.get('id')} is missing metadata: {', '.join(missing)}")
        if patch.get("category") not in CATEGORIES:
            errors.append(f"patch {patch.get('id')} has an invalid category")
        _check_hash(patch, f"patch {patch.get('id')}", errors)

    contract = report.get("rootfs_contract", {})
    if set(contract) != {"KERNEL", "DEVICE_TREE", "FIRMWARE", "BOOT_ARTIFACT", "ROOTFS"}:
        errors.append("rootfs contract must contain exactly five stages")
    decision = report.get("decision", {})
    if decision.get("sea") not in DECISIONS:
        errors.append("invalid SEA decision")
    if decision.get("recovery_readiness") != "BLOCKED" or decision.get("write_phone_authorized") is not False:
        errors.append("recovery/write safety state is invalid")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    errors = validate_gate(report)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Mission 007 build gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
