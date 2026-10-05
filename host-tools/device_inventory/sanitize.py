"""Minimize and sanitize device command output before persistence."""

from __future__ import annotations

import hashlib
import re


_KEY_VALUE_SECRET = re.compile(
    r"(?im)^(\s*(?:ro\.(?:serialno|boot\.serialno)|serial(?:number)?|imei|meid|android_id|account|user(?:name)?|token|password|ssid|ip(?:v4)?|mac(?:_address)?)[^:=]*[:=]\s*)\S+"
)
_IMEI_MEID = re.compile(r"(?i)\b(?:imei|meid)\s*[:=]?\s*[0-9a-f-]{8,32}\b")
_MAC = re.compile(r"(?i)\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b")
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_ANDROID_ID = re.compile(r"(?i)\b(?:android[_ ]?id|device[_ ]?id)\s*[:=]\s*\S+")
_BEARER = re.compile(r"(?i)\b(?:token|password|passwd|secret|authorization)\s*[:=]\s*\S+")
_SERIAL_LABEL = re.compile(r"(?i)\b(?:serial(?:number)?|ro\.serialno|ro\.boot\.serialno)\s*[:=]\s*\S+")
_GETPROP_SECRET = re.compile(
    r"(?im)^(\[(?:ro\.serialno|ro\.boot\.serialno|ro\.vendor\.serialno|(?:imei|meid|android_id|account|user(?:name)?|token|password|ssid))\]:\s*)\[[^\]]*\]"
)
_TRANSPORT_SERIAL = re.compile(r"(?im)^\s*[^\s]+(\s+(?:device|unauthorized|offline|fastboot)\b)")


def sanitize_text(text: str) -> str:
    """Redact identifiers and network/user secrets while retaining structure."""

    result = _KEY_VALUE_SECRET.sub(r"\1<REDACTED>", text)
    result = _GETPROP_SECRET.sub(r"\1[<REDACTED>]", result)
    result = _TRANSPORT_SERIAL.sub(r"<REDACTED_SERIAL>\1", result)
    result = _IMEI_MEID.sub("<REDACTED_IMEI_MEID>", result)
    result = _MAC.sub("<REDACTED_MAC>", result)
    result = _ANDROID_ID.sub("<REDACTED_ANDROID_ID>", result)
    result = _BEARER.sub("<REDACTED_SECRET>", result)
    result = _SERIAL_LABEL.sub("<REDACTED_SERIAL>", result)
    return result


def sanitized_result_hash(stdout: str, stderr: str) -> str:
    sanitized = sanitize_text(stdout) + "\n" + sanitize_text(stderr)
    return hashlib.sha256(sanitized.encode("utf-8", "replace")).hexdigest()


def sanitize_mapping(value):
    """Recursively sanitize strings in a JSON-compatible value."""

    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize_mapping(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_mapping(item) for key, item in value.items()}
    return value
