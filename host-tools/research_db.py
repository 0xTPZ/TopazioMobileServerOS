"""Validate the reusable public-source research database for a DSP."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CLASSIFICATIONS = {
    "OFFICIAL",
    "COMMUNITY_VERIFIED",
    "STRONG_CANDIDATE",
    "WEAK_CANDIDATE",
    "UNRELATED",
    "PROPRIETARY",
    "UNKNOWN",
}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("research database must be an object")
    return value


def validate(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != 1:
        errors.append("research schema must be 1")
    if record.get("device") != "xiaomi-sea":
        errors.append("research device must be xiaomi-sea")
    sources = record.get("sources")
    components = record.get("components")
    if not isinstance(sources, list) or not isinstance(components, list):
        return errors + ["sources and components must be lists"]

    source_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            errors.append("source entry must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            errors.append("source id must be non-empty")
        elif source_id in source_ids:
            errors.append(f"duplicate source id: {source_id}")
        else:
            source_ids.add(source_id)
        if source.get("classification") not in CLASSIFICATIONS:
            errors.append(f"invalid source classification: {source_id}")
        url = source.get("repository")
        if not isinstance(url, str) or not url.startswith("https://"):
            errors.append(f"source URL must be HTTPS: {source_id}")
        commit = source.get("commit")
        if commit is not None and (not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit)):
            errors.append(f"source commit must be a full hash or null: {source_id}")
        if not isinstance(source.get("license"), str) or not source.get("license"):
            errors.append(f"source license missing: {source_id}")

    component_ids: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            errors.append("component entry must be an object")
            continue
        component_id = component.get("id")
        if not isinstance(component_id, str) or not component_id:
            errors.append("component id must be non-empty")
        elif component_id in component_ids:
            errors.append(f"duplicate component id: {component_id}")
        else:
            component_ids.add(component_id)
        if component.get("classification") not in CLASSIFICATIONS:
            errors.append(f"invalid component classification: {component_id}")
        refs = component.get("source_ids")
        if not isinstance(refs, list) or not refs:
            errors.append(f"component has no source_ids: {component_id}")
        else:
            for ref in refs:
                if ref not in source_ids:
                    errors.append(f"component references unknown source {ref}: {component_id}")
        hashes = component.get("hashes", {})
        if not isinstance(hashes, dict):
            errors.append(f"component hashes must be an object: {component_id}")
        else:
            for algorithm, digest in hashes.items():
                if algorithm != "sha256" or not isinstance(digest, str) or not HASH_RE.fullmatch(digest):
                    errors.append(f"invalid component hash {algorithm}: {component_id}")
        if not isinstance(component.get("license"), str) or not component.get("license"):
            errors.append(f"component license missing: {component_id}")
        if component.get("redistributable") is None:
            errors.append(f"component redistribution policy missing: {component_id}")

    for relationship in record.get("relationships", []):
        if not isinstance(relationship, dict):
            errors.append("relationship entry must be an object")
            continue
        if relationship.get("from") not in source_ids | component_ids:
            errors.append(f"relationship from is unknown: {relationship.get('from')}")
        if relationship.get("to") not in source_ids | component_ids:
            errors.append(f"relationship to is unknown: {relationship.get('to')}")

    measurements = record.get("measurements", {})
    convergence = measurements.get("cust_dtsi_independent_convergence", {})
    if convergence.get("sea") != 1 or convergence.get("k6781v1_64_k419") != 0:
        errors.append("cust.dtsi convergence measurement changed unexpectedly")
    policies = record.get("policies", {})
    if policies.get("community_replaces_official_silently") is not False:
        errors.append("community replacement policy must be fail-closed")
    if policies.get("empty_firmware_accepted") is not False:
        errors.append("empty firmware must never be accepted")
    return errors


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "devices/xiaomi-sea/sources.json"
    errors = validate(load(path))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"research database valid: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
