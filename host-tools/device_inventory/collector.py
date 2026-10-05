"""Fail-closed inventory orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from .discovery import ToolSelection
from .report import build_observation
from .transport import collect_transport_commands


class DeviceInventory:
    def __init__(self, *, raw_dir: Path | None = None, adb_path: str | None = None, fastboot_path: str | None = None, platform_tools: Path | None = None):
        self.raw_dir = raw_dir
        self.adb_path = adb_path
        self.fastboot_path = fastboot_path
        self.platform_tools = platform_tools

    def collect(self, *, dry_run: bool = False) -> dict:
        results, tools = collect_transport_commands(
            dry_run=dry_run,
            raw_dir=self.raw_dir,
            adb_path=self.adb_path,
            fastboot_path=self.fastboot_path,
            platform_tools=self.platform_tools,
        )
        report = build_observation(results)
        report["tool_discovery"] = {
            name: {"path": selection.path, "source": selection.source, "available": selection.available}
            for name, selection in tools.items()
        }
        report["phone_command_execution_count"] = sum(item.execution_status == "EXECUTED" for item in results)
        return report

    def write_report(self, path: Path, *, dry_run: bool = False) -> dict:
        report = self.collect(dry_run=dry_run)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return report
