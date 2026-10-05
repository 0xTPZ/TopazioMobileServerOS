#!/usr/bin/env python3
"""CLI for host-only firmware package and image forensics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from firmware_forensics.core import (
    dump_json,
    inventory_package,
    parse_android_boot,
    parse_dtbo,
    parse_vbmeta,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    inventory = sub.add_parser("inventory")
    inventory.add_argument("path", type=Path)

    boot = sub.add_parser("boot")
    boot.add_argument("path", type=Path)
    boot.add_argument("--extract-dir", type=Path)

    for name in ("dtbo", "vbmeta"):
        command = sub.add_parser(name)
        command.add_argument("path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inventory":
            result = inventory_package(args.path)
        elif args.command == "boot":
            result = parse_android_boot(args.path, args.extract_dir)
        elif args.command == "dtbo":
            result = parse_dtbo(args.path)
        else:
            result = parse_vbmeta(args.path)
    except (OSError, ValueError, KeyError) as error:
        print(f"firmware forensics error: {error}", file=sys.stderr)
        return 2
    print(dump_json(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
