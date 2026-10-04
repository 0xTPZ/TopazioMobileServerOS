"""Build a static, fail-closed include graph for a device-tree entry point.

This tool never edits a kernel tree and never treats a missing include as an
empty file.  It is intentionally independent of dtc so it can be used before
the vendor build context is complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


INCLUDE_RE = re.compile(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(name: str, including: Path, include_dirs: list[Path], angle: bool) -> Path | None:
    candidates: list[Path] = []
    if not angle:
        candidates.append(including.parent / name)
    candidates.extend(directory / name for directory in include_dirs)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def build_graph(entry: Path, include_dirs: list[Path]) -> dict[str, Any]:
    entry = entry.resolve()
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    visiting: set[Path] = set()

    def visit(path: Path) -> None:
        path = path.resolve()
        key = str(path)
        if key in nodes or path in visiting:
            return
        visiting.add(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            nodes[key] = {"path": key, "exists": False, "error": str(exc), "includes": []}
            visiting.discard(path)
            return
        includes: list[str] = []
        node = {
            "path": key,
            "exists": True,
            "sha256": sha256(path),
            "includes": includes,
        }
        nodes[key] = node
        for line in text.splitlines():
            match = INCLUDE_RE.match(line)
            if not match:
                continue
            name = match.group(1)
            includes.append(name)
            angle = "<" in line[line.find("include") :]
            resolved = _resolve(name, path, include_dirs, angle)
            if resolved is None:
                missing.append({"from": key, "include": name})
                continue
            edges.append({"from": key, "to": str(resolved), "include": name})
            visit(resolved)
        visiting.discard(path)

    if entry.is_file():
        visit(entry)
    else:
        missing.append({"from": str(entry), "include": "<entry>"})

    return {
        "schema": 1,
        "entry": str(entry),
        "include_dirs": [str(path.resolve()) for path in include_dirs],
        "status": "COMPLETE" if entry.is_file() and not missing else "BLOCKED",
        "nodes": sorted(nodes.values(), key=lambda item: item["path"]),
        "edges": sorted(edges, key=lambda item: (item["from"], item["to"])),
        "missing": sorted(missing, key=lambda item: (item["from"], item["include"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", type=Path, required=True)
    parser.add_argument("--include-dir", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_graph(args.entry, args.include_dir)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
