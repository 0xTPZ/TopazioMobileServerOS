"""Derive and validate a reproducible SERVER_MINIMAL Kconfig delta."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


CONFIG_ASSIGN_LINE = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$")
CONFIG_NOT_SET_LINE = re.compile(r"^# (CONFIG_[A-Za-z0-9_]+) is not set$")

CRITICAL_SYMBOLS = {
    "CONFIG_SCSI_UFSHCD",
    "CONFIG_SCSI_UFSHCD_PLATFORM",
    "CONFIG_SCSI_UFS_MEDIATEK",
    "CONFIG_USB_MTK_HDRC",
    "CONFIG_USB_MTK_OTG",
    "CONFIG_USB_USBNET",
    "CONFIG_CFG80211",
    "CONFIG_MTK_COMBO",
    "CONFIG_MTK_COMBO_WIFI",
    "CONFIG_INPUT_TOUCHSCREEN",
    "CONFIG_TOUCHSCREEN_FTS",
    "CONFIG_DRM",
    "CONFIG_DRM_MEDIATEK",
    "CONFIG_MTK_CHARGER",
    "CONFIG_CHARGER_BQ2589X",
    "CONFIG_THERMAL",
    "CONFIG_CPU_THERMAL",
    "CONFIG_WATCHDOG",
    "CONFIG_SERIAL_8250_CONSOLE",
}

MODEM_SYMBOLS = {
    "CONFIG_MTK_CCCI_DEVICES",
    "CONFIG_MTK_ECCCI_DRIVER",
    "CONFIG_MTK_ECCCI_C2K",
    "CONFIG_MTK_MD1_SUPPORT",
}


def parse_config(text: str) -> dict[str, str]:
    """Return the last value for each Kconfig symbol in a defconfig text."""

    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = CONFIG_ASSIGN_LINE.match(line)
        if match:
            symbol, value = match.groups()
            values[symbol] = value
            continue
        match = CONFIG_NOT_SET_LINE.match(line)
        if match:
            values[match.group(1)] = "n"
    return values


def render_symbol(symbol: str, value: str) -> str:
    if value in {"n", ""}:
        return f"# {symbol} is not set"
    return f"{symbol}={value}"


def derive(base_text: str, fragment_text: str) -> str:
    """Apply an explicit fragment while preserving the base file's ordering."""

    fragment = parse_config(fragment_text)
    lines = base_text.splitlines()
    seen: set[str] = set()
    rendered: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        match = CONFIG_ASSIGN_LINE.match(line) or CONFIG_NOT_SET_LINE.match(line)
        if match:
            symbol = match.group(1)
            if symbol in fragment:
                rendered.append(render_symbol(symbol, fragment[symbol]))
                seen.add(symbol)
                continue
        rendered.append(raw_line)
    absent = [symbol for symbol in fragment if symbol not in seen]
    if absent:
        if rendered and rendered[-1] != "":
            rendered.append("")
        rendered.extend(render_symbol(symbol, fragment[symbol]) for symbol in absent)
    return "\n".join(rendered).rstrip() + "\n"


def diff_config(base_text: str, derived_text: str) -> list[dict[str, str | None]]:
    base = parse_config(base_text)
    derived = parse_config(derived_text)
    changes: list[dict[str, str | None]] = []
    for symbol in sorted(set(base) | set(derived)):
        old = base.get(symbol)
        new = derived.get(symbol)
        if old != new:
            changes.append({"symbol": symbol, "old": old, "new": new})
    return changes


def validate_critical(config_text: str, required: Iterable[str] = CRITICAL_SYMBOLS) -> list[str]:
    values = parse_config(config_text)
    errors: list[str] = []
    for symbol in sorted(required):
        if values.get(symbol) != "y":
            errors.append(f"critical symbol is not enabled: {symbol}={values.get(symbol)!r}")
    for symbol in sorted(MODEM_SYMBOLS):
        if values.get(symbol) not in {None, "n", "0"}:
            errors.append(f"modem symbol remains enabled: {symbol}={values[symbol]}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    base_text = args.base.read_text(encoding="utf-8")
    fragment_text = args.fragment.read_text(encoding="utf-8")
    derived_text = derive(base_text, fragment_text)
    errors = validate_critical(derived_text)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(derived_text, encoding="utf-8")
    report = {
        "base": str(args.base),
        "fragment": str(args.fragment),
        "output": str(args.output),
        "changes": diff_config(base_text, derived_text),
        "critical_validation": "PASS",
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
