#!/usr/bin/env python3
"""CLI for host-only firmware package and image forensics."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from firmware_forensics.core import (
    dump_json,
    analyze_dtbo_fdt,
    analyze_kernel,
    analyze_module_metadata,
    inventory_package,
    match_dt_base,
    parse_android_boot,
    parse_dtbo,
    parse_fdt,
    parse_update_payload_file,
    parse_vendor_boot,
    parse_vbmeta,
    scan_fdt_candidates,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    inventory = sub.add_parser("inventory")
    inventory.add_argument("path", type=Path)

    boot = sub.add_parser("boot")
    boot.add_argument("path", type=Path)
    boot.add_argument("--extract-dir", type=Path)

    for name in ("dtbo", "vbmeta", "vendor-boot"):
        command = sub.add_parser(name)
        command.add_argument("path", type=Path)
    for name in ("fdt", "fdt-scan", "kernel", "module-metadata", "payload"):
        command = sub.add_parser(name)
        command.add_argument("path", type=Path)
    dt_match = sub.add_parser("dt-match")
    dt_match.add_argument("dtbo", type=Path)
    dt_match.add_argument("candidates", nargs="+", type=Path)
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
        elif args.command == "fdt":
            result = parse_fdt(args.path.read_bytes(), str(args.path.resolve()))
        elif args.command == "fdt-scan":
            result = scan_fdt_candidates(args.path.read_bytes(), str(args.path.resolve()))
        elif args.command == "kernel":
            result = analyze_kernel(args.path.read_bytes())
        elif args.command == "module-metadata":
            result = analyze_module_metadata(args.path)
        elif args.command == "dt-match":
            dtbo = analyze_dtbo_fdt(args.dtbo.read_bytes(), str(args.dtbo.resolve()))
            candidates = []
            for candidate in args.candidates:
                parsed = parse_fdt(candidate.read_bytes(), str(candidate.resolve()))
                candidates.append(
                    {
                        "name": candidate.name,
                        "source": str(candidate.resolve()),
                        "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                        "parsed": parsed,
                        "compatible": [
                            item["text"]
                            for item in parsed.get("properties", [])
                            if item["path"] == "/" and item["name"] == "compatible" and item["text"]
                        ],
                    }
                )
            result = match_dt_base(dtbo, candidates)
        elif args.command == "payload":
            result = parse_update_payload_file(args.path)
        elif args.command == "vendor-boot":
            result = parse_vendor_boot(args.path)
        else:
            result = parse_vbmeta(args.path)
    except (OSError, ValueError, KeyError) as error:
        print(f"firmware forensics error: {error}", file=sys.stderr)
        return 2
    print(dump_json(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
