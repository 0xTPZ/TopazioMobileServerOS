"""Fail-closed inventory orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from .report import build_observation
from .transport import collect_transport_commands


class DeviceInventory:
    def __init__(self, *, raw_dir: Path | None = None):
        self.raw_dir = raw_dir

    def collect(self, *, dry_run: bool = False) -> dict:
        results = collect_transport_commands(dry_run=dry_run, raw_dir=self.raw_dir)
        return build_observation(results)

    def write_report(self, path: Path, *, dry_run: bool = False) -> dict:
        report = self.collect(dry_run=dry_run)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return report
