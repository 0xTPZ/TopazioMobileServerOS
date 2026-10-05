"""Static safety classification for a future SEA inventory session.

This module deliberately does not execute ADB or fastboot. It only classifies
the narrow read-only command set documented for a future, separately
authorized session.
"""

from __future__ import annotations


READ_ONLY_SAFE_PREFIXES = (
    "adb devices",
    "adb get-state",
    "adb shell getprop",
    "adb shell uname",
    "adb shell cat /proc/",
    "adb shell cat /sys/",
    "adb shell ls -l /dev/block/by-name",
    "adb shell cat /proc/partitions",
    "adb shell cat /proc/mounts",
    "fastboot getvar ",
)

STATE_CHANGING_PREFIXES = (
    "adb reboot",
    "fastboot reboot",
    "fastboot boot",
)

WRITE_PREFIXES = (
    "adb push",
    "adb shell dd ",
    "fastboot flash ",
    "fastboot erase ",
    "fastboot format ",
    "fastboot flashing unlock",
    "fastboot oem unlock",
)


def classify_command(command: str) -> str:
    normalized = " ".join(command.strip().split()).lower()
    if any(normalized.startswith(prefix) for prefix in WRITE_PREFIXES):
        return "WRITE"
    if any(normalized.startswith(prefix) for prefix in STATE_CHANGING_PREFIXES):
        return "STATE_CHANGING"
    if any(normalized.startswith(prefix) for prefix in READ_ONLY_SAFE_PREFIXES):
        return "READ_ONLY_SAFE"
    return "UNKNOWN"


def planned_commands() -> list[dict[str, str]]:
    return [
        {"command": "adb devices", "classification": "READ_ONLY_SAFE", "purpose": "transport presence"},
        {"command": "adb get-state", "classification": "READ_ONLY_SAFE", "purpose": "ADB state"},
        {"command": "adb shell getprop", "classification": "READ_ONLY_SAFE", "purpose": "Android identity and boot properties"},
        {"command": "adb shell uname -a", "classification": "READ_ONLY_SAFE", "purpose": "running kernel release"},
        {"command": "adb shell cat /proc/meminfo", "classification": "READ_ONLY_SAFE", "purpose": "RAM inventory"},
        {"command": "adb shell cat /proc/partitions", "classification": "READ_ONLY_SAFE", "purpose": "logical block inventory"},
        {"command": "adb shell cat /proc/mounts", "classification": "READ_ONLY_SAFE", "purpose": "filesystem and module locations"},
        {"command": "adb shell ls -l /dev/block/by-name", "classification": "READ_ONLY_SAFE", "purpose": "published partition names"},
        {"command": "fastboot getvar product", "classification": "READ_ONLY_SAFE", "purpose": "bootloader product identity"},
        {"command": "fastboot getvar current-slot", "classification": "READ_ONLY_SAFE", "purpose": "active slot"},
        {"command": "fastboot getvar slot-count", "classification": "READ_ONLY_SAFE", "purpose": "slot count"},
        {"command": "fastboot getvar unlocked", "classification": "READ_ONLY_SAFE", "purpose": "bootloader state"},
        {"command": "fastboot getvar all", "classification": "READ_ONLY_SAFE", "purpose": "standard bootloader metadata"},
    ]


if __name__ == "__main__":
    import json

    print(json.dumps(planned_commands(), indent=2))
