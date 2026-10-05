"""Sanitized unit-observation report generation."""

from __future__ import annotations

from datetime import datetime, timezone
import re

from .sanitize import sanitize_text


EXPECTED_BUILD = "OS2.0.209.0.VHZMIXM"
EXPECTED_KERNEL = "6.6.58-android15"


def _field(value, source: str, confidence: str, timestamp: str, safety: str) -> dict:
    return {"value": value, "source": source, "confidence": confidence, "timestamp": timestamp, "safety_class": safety}


def _result(results, command_id: str):
    return next((item for item in results if item.command_id == command_id), None)


def _has_data(result) -> bool:
    return bool(result and result.executable_present and result.exit_code == 0 and result.sanitized_stdout.strip())


def _prop_text(result) -> dict[str, str]:
    if not result:
        return {}
    props = {}
    for line in result.sanitized_stdout.splitlines():
        match = re.match(r"^\[([^]]+)\]: \[([^]]*)\]$", line.strip())
        if match:
            props[match.group(1)] = match.group(2)
    return props


def _transport_state(results, command_id: str, *, fastboot: bool = False) -> str:
    result = _result(results, command_id)
    if result is None or not result.executable_present:
        return "ABSENT"
    if result.exit_code not in (None, 0):
        return "DRIVER_BLOCKED"
    lines = [
        line.strip()
        for line in result.sanitized_stdout.splitlines()
        if line.strip() and line.strip().lower() != "list of devices attached"
    ]
    if not lines:
        return "ABSENT"
    if fastboot:
        return "PRESENT_FASTBOOT"
    if any("unauthorized" in line.lower() for line in lines):
        return "PRESENT_UNAUTHORIZED"
    if any(re.search(r"\bdevice\b", line, re.I) for line in lines):
        return "PRESENT_AUTHORIZED"
    return "UNKNOWN"


def _mem_total(result):
    if not result:
        return None
    match = re.search(r"(?im)^MemTotal:\s+(\d+)\s+kB", result.sanitized_stdout)
    return int(match.group(1)) * 1024 if match else None


def _mem_value(result, label: str):
    if not result:
        return None
    match = re.search(rf"(?im)^{re.escape(label)}:\s+(\d+)\s+kB", result.sanitized_stdout)
    return int(match.group(1)) * 1024 if match else None


def _text_value(results, command_id: str):
    result = _result(results, command_id)
    return result.sanitized_stdout.strip() if _has_data(result) else None


def _driver_from_uevent(results, command_id: str):
    value = _text_value(results, command_id)
    if not value:
        return None
    match = re.search(r"(?im)^DRIVER=(\S+)", value)
    return match.group(1) if match else value


def _build_match(props: dict[str, str]) -> str:
    fingerprint = props.get("ro.build.fingerprint") or props.get("ro.system.build.fingerprint")
    device = props.get("ro.product.device") or props.get("ro.build.product")
    incremental = props.get("ro.build.version.incremental", "")
    if not fingerprint and not device and not incremental:
        return "UNKNOWN"
    if EXPECTED_BUILD in (fingerprint or "") or EXPECTED_BUILD == incremental:
        return "EXACT_MATCH"
    if device == "sea":
        return "COMPATIBLE_FAMILY"
    return "DIFFERENT_BUILD"


def _kernel_match(result) -> str:
    if not result or not result.sanitized_stdout.strip():
        return "UNKNOWN"
    return "YES" if EXPECTED_KERNEL in result.sanitized_stdout else "NO"


def _partition_names(result) -> list[str]:
    if not result:
        return []
    names = []
    for line in result.sanitized_stdout.splitlines():
        match = re.search(r"->\s*[^/]+/([^\s]+)$", line.strip())
        if match:
            names.append(match.group(1))
    return sorted(set(names))


def _loaded_modules(result) -> list[str]:
    if not result:
        return []
    modules = []
    for line in result.sanitized_stdout.splitlines():
        fields = line.split()
        if fields:
            modules.append(fields[0])
    return modules


def build_observation(results, *, timestamp: str | None = None) -> dict:
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    adb_state = _transport_state(results, "adb_devices")
    fastboot_state = _transport_state(results, "fastboot_devices", fastboot=True)
    props_result = _result(results, "adb_getprop")
    props = _prop_text(props_result)
    safe = "READ_ONLY_SAFE"
    identity = {
        "manufacturer": _field(props.get("ro.product.manufacturer"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "brand": _field(props.get("ro.product.brand"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "model": _field(props.get("ro.product.model"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "device": _field(props.get("ro.product.device"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "product": _field(props.get("ro.product.name"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "hardware": _field(props.get("ro.hardware"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "board": _field(props.get("ro.product.board"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "codename_assessment": _field("sea" if props.get("ro.product.device") == "sea" else None, "adb_getprop", "HIGH" if props else "UNKNOWN", timestamp, safe),
    }
    software = {
        "build_fingerprint": _field(props.get("ro.build.fingerprint") or props.get("ro.system.build.fingerprint"), "adb_getprop", "HIGH" if props else "UNKNOWN", timestamp, safe),
        "build_id": _field(props.get("ro.build.id"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "android_version": _field(props.get("ro.build.version.release"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "security_patch": _field(props.get("ro.build.version.security_patch"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "ota_comparison": _field(_build_match(props), "adb_getprop", "HIGH" if props else "UNKNOWN", timestamp, safe),
    }
    kernel_result = _result(results, "adb_uname")
    mem_result = _result(results, "adb_meminfo")
    return {
        "schema": 1,
        "mission": 12,
        "device": "xiaomi-sea",
        "report_type": "SANITIZED_UNIT_OBSERVATION",
        "timestamp": timestamp,
        "transport": {
            "adb": _field(adb_state, "adb devices", "HIGH", timestamp, safe),
            "fastboot": _field(fastboot_state, "fastboot devices", "HIGH", timestamp, safe),
        },
        "identity": identity,
        "software": software,
        "kernel": {
            "release": _field(kernel_result.sanitized_stdout.strip() if kernel_result else None, "adb shell uname -a", "HIGH" if kernel_result and kernel_result.sanitized_stdout else "UNKNOWN", timestamp, safe),
            "unit_matches_stock_kernel": _field(_kernel_match(kernel_result), "adb shell uname -a", "HIGH" if kernel_result and kernel_result.sanitized_stdout else "UNKNOWN", timestamp, safe),
            "architecture": _field(props.get("ro.product.cpu.abilist64") or props.get("ro.product.cpu.abi"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        },
        "ram": {
            "unit_ram_total_bytes": _field(_mem_total(mem_result), "adb shell cat /proc/meminfo", "HIGH" if mem_result and mem_result.sanitized_stdout else "UNKNOWN", timestamp, safe),
            "available_bytes": _field(_mem_value(mem_result, "MemAvailable"), "adb shell cat /proc/meminfo", "HIGH" if mem_result and mem_result.sanitized_stdout else "UNKNOWN", timestamp, safe),
        },
        "storage": {
            "capacity_bytes": _field((int(_text_value(results, "adb_storage_size")) * 512) if (_text_value(results, "adb_storage_size") or "").isdigit() else None, "adb shell cat /sys/block/sda/size", "HIGH" if _text_value(results, "adb_storage_size") else "UNKNOWN", timestamp, safe),
            "logical_block_size": _field(int(_text_value(results, "adb_storage_block_size")) if (_text_value(results, "adb_storage_block_size") or "").isdigit() else None, "adb shell cat /sys/block/sda/queue/logical_block_size", "HIGH" if _text_value(results, "adb_storage_block_size") else "UNKNOWN", timestamp, safe),
            "mounts": _field(_result(results, "adb_mounts").sanitized_stdout if _result(results, "adb_mounts") else None, "adb shell cat /proc/mounts", "MEDIUM" if _result(results, "adb_mounts") and _result(results, "adb_mounts").sanitized_stdout else "UNKNOWN", timestamp, safe),
        },
        "ufs": {
            "vendor": _field(_text_value(results, "adb_ufs_vendor"), "public UFS sysfs", "HIGH" if _text_value(results, "adb_ufs_vendor") else "UNKNOWN", timestamp, safe),
            "model": _field(_text_value(results, "adb_ufs_model"), "public UFS sysfs", "HIGH" if _text_value(results, "adb_ufs_model") else "UNKNOWN", timestamp, safe),
            "revision": _field(_text_value(results, "adb_ufs_revision"), "public UFS sysfs", "HIGH" if _text_value(results, "adb_ufs_revision") else "UNKNOWN", timestamp, safe),
        },
        "slot": _field(props.get("ro.boot.slot_suffix"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "partition_names": _field(_partition_names(_result(results, "adb_by_name")), "adb shell ls -l /dev/block/by-name", "MEDIUM" if _has_data(_result(results, "adb_by_name")) else "UNKNOWN", timestamp, safe),
        "boot_state": {
            "bootloader": _field(props.get("ro.boot.flash.locked"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
            "device_state": _field(props.get("ro.boot.verifiedbootstate"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
            "verity_mode": _field(props.get("ro.boot.veritymode"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        },
        "avb_state": _field(props.get("ro.boot.verifiedbootstate"), "adb_getprop", "MEDIUM" if props else "UNKNOWN", timestamp, safe),
        "dt_metadata": {"value": None, "source": "not exposed or not collected", "confidence": "UNKNOWN", "timestamp": timestamp, "safety_class": safe},
        "modules": _field(_loaded_modules(_result(results, "adb_modules")), "adb shell cat /proc/modules", "MEDIUM" if _has_data(_result(results, "adb_modules")) else "UNKNOWN", timestamp, safe),
        "thermal": {
            "zone0_type": _field(_result(results, "adb_thermal_type").sanitized_stdout.strip() if _result(results, "adb_thermal_type") else None, "sysfs thermal zone 0", "MEDIUM" if _has_data(_result(results, "adb_thermal_type")) else "UNKNOWN", timestamp, safe),
            "zone0_temp": _field(_result(results, "adb_thermal_temp").sanitized_stdout.strip() if _result(results, "adb_thermal_temp") else None, "sysfs thermal zone 0", "MEDIUM" if _has_data(_result(results, "adb_thermal_temp")) else "UNKNOWN", timestamp, safe),
        },
        "power": {
            "battery_status": _field(_result(results, "adb_battery_status").sanitized_stdout.strip() if _result(results, "adb_battery_status") else None, "battery sysfs", "MEDIUM" if _has_data(_result(results, "adb_battery_status")) else "UNKNOWN", timestamp, safe),
            "battery_technology": _field(_result(results, "adb_battery_technology").sanitized_stdout.strip() if _result(results, "adb_battery_technology") else None, "battery sysfs", "MEDIUM" if _has_data(_result(results, "adb_battery_technology")) else "UNKNOWN", timestamp, safe),
        },
        "wifi": {"driver": _field(_driver_from_uevent(results, "adb_wifi_uevent"), "public network sysfs", "MEDIUM" if _text_value(results, "adb_wifi_uevent") else "UNKNOWN", timestamp, safe)},
        "usb": {"driver": _field(_driver_from_uevent(results, "adb_usb_uevent"), "public network sysfs", "MEDIUM" if _text_value(results, "adb_usb_uevent") else "UNKNOWN", timestamp, safe)},
        "display": {"driver": _field(_driver_from_uevent(results, "adb_display_uevent"), "public DRM sysfs", "MEDIUM" if _text_value(results, "adb_display_uevent") else "UNKNOWN", timestamp, safe)},
        "touch": {"value": None, "source": "not exposed or not collected", "confidence": "UNKNOWN", "timestamp": timestamp, "safety_class": safe},
        "audit_log": [item.as_dict() for item in results],
        "sanitization": {"status": "APPLIED", "raw_device_output_versioned": False, "pii_persisted": False},
        "ota_reference": EXPECTED_BUILD,
        "recovery_readiness": "BLOCKED" if adb_state in {"ABSENT", "PRESENT_UNAUTHORIZED"} else "NOT_READY",
        "stock_dtb_origin": "UNKNOWN",
        "next_hardware_gate": "PHYSICAL_TRANSPORT_BLOCKED" if adb_state == "ABSENT" and fastboot_state == "ABSENT" else "PHYSICAL_IDENTITY_PARTIAL",
        "phone_writes_performed": False,
        "phone_state_changed": False,
    }
