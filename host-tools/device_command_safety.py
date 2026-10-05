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
    "fastboot devices",
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

READ_ONLY_FASTBOOT_COMMANDS = frozenset(
    {
        "fastboot getvar product",
        "fastboot getvar variant",
        "fastboot getvar current-slot",
        "fastboot getvar slot-count",
        "fastboot getvar unlocked",
        "fastboot getvar secure",
    }
)


def classify_command(command: str) -> str:
    normalized = " ".join(command.strip().split()).lower()
    if any(normalized.startswith(prefix) for prefix in WRITE_PREFIXES):
        return "WRITE"
    if any(normalized.startswith(prefix) for prefix in STATE_CHANGING_PREFIXES):
        return "STATE_CHANGING"
    if normalized in READ_ONLY_FASTBOOT_COMMANDS:
        return "READ_ONLY_SAFE"
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
        {"command": "adb shell cat /proc/modules", "classification": "READ_ONLY_SAFE", "purpose": "currently loaded module names"},
        {"command": "adb shell ls -l /dev/block/by-name", "classification": "READ_ONLY_SAFE", "purpose": "published partition names"},
        {"command": "adb shell cat /sys/class/thermal/thermal_zone0/type", "classification": "READ_ONLY_SAFE", "purpose": "public thermal zone identity"},
        {"command": "adb shell cat /sys/class/thermal/thermal_zone0/temp", "classification": "READ_ONLY_SAFE", "purpose": "public thermal sensor value"},
        {"command": "adb shell cat /sys/class/power_supply/battery/status", "classification": "READ_ONLY_SAFE", "purpose": "battery charging state"},
        {"command": "adb shell cat /sys/class/power_supply/battery/technology", "classification": "READ_ONLY_SAFE", "purpose": "battery technology"},
        {"command": "adb shell cat /sys/class/power_supply/battery/capacity", "classification": "READ_ONLY_SAFE", "purpose": "battery capacity percentage"},
        {"command": "adb shell cat /sys/block/sda/size", "classification": "READ_ONLY_SAFE", "purpose": "public storage sector count"},
        {"command": "adb shell cat /sys/block/sda/queue/logical_block_size", "classification": "READ_ONLY_SAFE", "purpose": "public logical block size"},
        {"command": "adb shell cat /sys/block/sda/device/vendor", "classification": "READ_ONLY_SAFE", "purpose": "public UFS vendor string"},
        {"command": "adb shell cat /sys/block/sda/device/model", "classification": "READ_ONLY_SAFE", "purpose": "public UFS model string"},
        {"command": "adb shell cat /sys/block/sda/device/rev", "classification": "READ_ONLY_SAFE", "purpose": "public UFS revision"},
        {"command": "adb shell cat /sys/class/net/wlan0/device/uevent", "classification": "READ_ONLY_SAFE", "purpose": "public Wi-Fi driver metadata"},
        {"command": "adb shell cat /sys/class/net/usb0/device/uevent", "classification": "READ_ONLY_SAFE", "purpose": "public USB network driver metadata"},
        {"command": "adb shell cat /sys/class/drm/card0/device/uevent", "classification": "READ_ONLY_SAFE", "purpose": "public display driver metadata"},
        {"command": "fastboot devices", "classification": "READ_ONLY_SAFE", "purpose": "fastboot transport presence without reboot"},
        {"command": "fastboot getvar product", "classification": "READ_ONLY_SAFE", "purpose": "bootloader product identity"},
        {"command": "fastboot getvar variant", "classification": "READ_ONLY_SAFE", "purpose": "bootloader variant"},
        {"command": "fastboot getvar current-slot", "classification": "READ_ONLY_SAFE", "purpose": "active slot"},
        {"command": "fastboot getvar slot-count", "classification": "READ_ONLY_SAFE", "purpose": "slot count"},
        {"command": "fastboot getvar unlocked", "classification": "READ_ONLY_SAFE", "purpose": "bootloader state"},
        {"command": "fastboot getvar secure", "classification": "READ_ONLY_SAFE", "purpose": "verified boot security state"},
    ]


if __name__ == "__main__":
    import json

    print(json.dumps(planned_commands(), indent=2))
