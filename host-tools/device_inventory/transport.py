"""ADB and fastboot read-only transport collectors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import subprocess
from pathlib import Path

from device_command_safety import classify_command

from .discovery import ToolSelection, discover_tools
from .sanitize import sanitized_result_hash, sanitize_text


@dataclass
class CommandResult:
    command_id: str
    transport: str
    command: str
    safety_class: str
    executable_present: bool
    exit_code: int | None
    stdout: str
    stderr: str
    sanitized_stdout: str
    sanitized_stderr: str
    result_hash: str | None
    timestamp: str
    execution_status: str = "EXECUTED"

    def as_dict(self) -> dict:
        return {
            "command_id": self.command_id,
            "transport": self.transport,
            "command": self.command,
            "safety_class": self.safety_class,
            "executable_present": self.executable_present,
            "exit_code": self.exit_code,
            "stdout": self.sanitized_stdout,
            "stderr": self.sanitized_stderr,
            "sanitized_result_hash": self.result_hash,
            "timestamp": self.timestamp,
            "execution_status": self.execution_status,
        }


def command_result(
    command_id: str,
    transport: str,
    command: str,
    *,
    dry_run: bool,
    tool: ToolSelection | None = None,
    skipped_reason: str | None = None,
) -> CommandResult:
    safety = classify_command(command)
    if safety != "READ_ONLY_SAFE":
        raise ValueError(f"refusing non-read-only command: {command} ({safety})")
    executable = tool.path if tool else None
    present = bool(executable)
    if dry_run or not present or skipped_reason:
        if dry_run:
            stderr = "DRY_RUN"
            execution_status = "DRY_RUN"
        elif skipped_reason:
            stderr = skipped_reason
            execution_status = "NOT_EXECUTED_FAIL_CLOSED"
        else:
            stderr = "COMMAND_NOT_FOUND"
            execution_status = "NOT_EXECUTED_TOOL_ABSENT"
        return CommandResult(
            command_id,
            transport,
            command,
            safety,
            present,
            None,
            "",
            stderr,
            "",
            sanitize_text(stderr),
            sanitized_result_hash("", stderr),
            datetime.now(timezone.utc).isoformat(),
            execution_status,
        )
    tokens = command.split()
    completed = subprocess.run(
        [executable, *tokens[1:]],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return CommandResult(
        command_id,
        transport,
        command,
        safety,
        True,
        completed.returncode,
        stdout,
        stderr,
        sanitize_text(stdout),
        sanitize_text(stderr),
        sanitized_result_hash(stdout, stderr),
        datetime.now(timezone.utc).isoformat(),
        "EXECUTED",
    )


ADB_COMMANDS = (
    ("adb_devices", "adb devices"),
    ("adb_get_state", "adb get-state"),
    ("adb_getprop", "adb shell getprop"),
    ("adb_uname", "adb shell uname -a"),
    ("adb_meminfo", "adb shell cat /proc/meminfo"),
    ("adb_partitions", "adb shell cat /proc/partitions"),
    ("adb_mounts", "adb shell cat /proc/mounts"),
    ("adb_modules", "adb shell cat /proc/modules"),
    ("adb_by_name", "adb shell ls -l /dev/block/by-name"),
    ("adb_thermal_type", "adb shell cat /sys/class/thermal/thermal_zone0/type"),
    ("adb_thermal_temp", "adb shell cat /sys/class/thermal/thermal_zone0/temp"),
    ("adb_battery_status", "adb shell cat /sys/class/power_supply/battery/status"),
    ("adb_battery_technology", "adb shell cat /sys/class/power_supply/battery/technology"),
    ("adb_battery_capacity", "adb shell cat /sys/class/power_supply/battery/capacity"),
    ("adb_storage_size", "adb shell cat /sys/block/sda/size"),
    ("adb_storage_block_size", "adb shell cat /sys/block/sda/queue/logical_block_size"),
    ("adb_ufs_vendor", "adb shell cat /sys/block/sda/device/vendor"),
    ("adb_ufs_model", "adb shell cat /sys/block/sda/device/model"),
    ("adb_ufs_revision", "adb shell cat /sys/block/sda/device/rev"),
    ("adb_wifi_uevent", "adb shell cat /sys/class/net/wlan0/device/uevent"),
    ("adb_usb_uevent", "adb shell cat /sys/class/net/usb0/device/uevent"),
    ("adb_display_uevent", "adb shell cat /sys/class/drm/card0/device/uevent"),
)

FASTBOOT_COMMANDS = (
    ("fastboot_devices", "fastboot devices"),
    ("fastboot_product", "fastboot getvar product"),
    ("fastboot_variant", "fastboot getvar variant"),
    ("fastboot_current_slot", "fastboot getvar current-slot"),
    ("fastboot_slot_count", "fastboot getvar slot-count"),
    ("fastboot_unlocked", "fastboot getvar unlocked"),
    ("fastboot_secure", "fastboot getvar secure"),
)


def _adb_state(result: CommandResult) -> str:
    if not result.executable_present or result.execution_status != "EXECUTED":
        return "ABSENT"
    lines = [line.strip().lower() for line in result.sanitized_stdout.splitlines() if line.strip()]
    if any("unauthorized" in line for line in lines):
        return "UNAUTHORIZED"
    if any("offline" in line for line in lines):
        return "OFFLINE"
    if any(line.endswith("\tdevice") or line.endswith(" device") for line in lines):
        return "AUTHORIZED"
    return "ABSENT"


def _record(
    results: list[CommandResult],
    command_id: str,
    command: str,
    transport: str,
    *,
    dry_run: bool,
    tools: dict[str, ToolSelection],
    raw_dir: Path | None,
    skipped_reason: str | None = None,
) -> CommandResult:
    result = command_result(
        command_id,
        transport,
        command,
        dry_run=dry_run,
        tool=tools[transport],
        skipped_reason=skipped_reason,
    )
    if raw_dir and result.execution_status == "EXECUTED":
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{command_id}.stdout.txt").write_text(result.stdout, encoding="utf-8")
        (raw_dir / f"{command_id}.stderr.txt").write_text(result.stderr, encoding="utf-8")
    results.append(result)
    return result


def collect_transport_commands(
    *,
    dry_run: bool,
    raw_dir: Path | None = None,
    adb_path: str | None = None,
    fastboot_path: str | None = None,
    platform_tools: Path | None = None,
) -> tuple[list[CommandResult], dict[str, ToolSelection]]:
    tools = discover_tools(adb=adb_path, fastboot=fastboot_path, platform_tools=platform_tools)
    results: list[CommandResult] = []
    adb_probe = _record(results, "adb_devices", "adb devices", "adb", dry_run=dry_run, tools=tools, raw_dir=raw_dir)
    adb_state = "DRY_RUN" if dry_run else _adb_state(adb_probe)
    for command_id, command in ADB_COMMANDS[1:]:
        reason = None if dry_run or adb_state == "AUTHORIZED" else f"ADB_{adb_state}_NO_SHELL"
        _record(results, command_id, command, "adb", dry_run=dry_run, tools=tools, raw_dir=raw_dir, skipped_reason=reason)

    _record(results, "fastboot_devices", "fastboot devices", "fastboot", dry_run=dry_run, tools=tools, raw_dir=raw_dir)
    for command_id, command in FASTBOOT_COMMANDS[1:]:
        _record(results, command_id, command, "fastboot", dry_run=dry_run, tools=tools, raw_dir=raw_dir, skipped_reason="FASTBOOT_METADATA_NOT_REQUESTED_IN_012B")
    return results, tools
