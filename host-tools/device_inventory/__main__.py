#!/usr/bin/env python3
"""Sanitized, read-only SEA physical inventory CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .collector import DeviceInventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show safe commands without touching a device")
    parser.add_argument("--report", type=Path, help="write sanitized report to this path")
    parser.add_argument("--raw-dir", type=Path, help="temporary local raw-output directory; never use the repository")
    args = parser.parse_args(argv)
    if args.raw_dir and str(Path.cwd()).lower().startswith(str(args.raw_dir.resolve()).lower()):
        parser.error("raw output directory must not be the repository working directory")
    inventory = DeviceInventory(raw_dir=args.raw_dir)
    report = inventory.collect(dry_run=args.dry_run)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
