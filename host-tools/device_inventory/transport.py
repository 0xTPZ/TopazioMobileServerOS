"""ADB and fastboot read-only transport collectors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import shutil
import subprocess
from pathlib import Path

from device_command_safety import classify_command

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
        }


def command_result(command_id: str, transport: str, command: str, *, dry_run: bool) -> CommandResult:
    safety = classify_command(command)
    if safety != "READ_ONLY_SAFE":
        raise ValueError(f"refusing non-read-only command: {command} ({safety})")
    executable = command.split()[0]
    present = shutil.which(executable) is not None
    if dry_run or not present:
        stderr = "DRY_RUN" if dry_run else "COMMAND_NOT_FOUND"
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
        )
    completed = subprocess.run(
        command.split(),
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


def collect_transport_commands(*, dry_run: bool, raw_dir: Path | None = None) -> list[CommandResult]:
    results: list[CommandResult] = []
    for command_id, command in (*ADB_COMMANDS, *FASTBOOT_COMMANDS):
        transport = "adb" if command.startswith("adb ") else "fastboot"
        result = command_result(command_id, transport, command, dry_run=dry_run)
        if raw_dir and not dry_run and result.executable_present:
            raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / f"{command_id}.stdout.txt").write_text(result.stdout, encoding="utf-8")
            (raw_dir / f"{command_id}.stderr.txt").write_text(result.stderr, encoding="utf-8")
        results.append(result)
    return results
