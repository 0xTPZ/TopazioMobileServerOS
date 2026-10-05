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


def build_graph(
    entry: Path,
    include_dirs: list[Path],
    *,
    source_id: str = "unknown",
    repository: str | None = None,
    commit: str | None = None,
    source_root: Path | None = None,
    confidence: str = "unknown",
) -> dict[str, Any]:
    entry = entry.resolve()
    if source_root is not None:
        source_root = source_root.resolve()
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    visiting: set[Path] = set()

    def provenance(path: Path) -> dict[str, Any]:
        record: dict[str, Any] = {
            "source_id": source_id,
            "repository": repository,
            "commit": commit,
        }
        if source_root is not None:
            try:
                record["relative_path"] = path.relative_to(source_root).as_posix()
            except ValueError:
                record["relative_path"] = None
        return record

    def node_metadata(path: Path, *, available: bool, node_confidence: str) -> dict[str, Any]:
        return {
            "source": source_id,
            "provenance": provenance(path),
            "confidence": node_confidence,
            "required": True,
            "available": available,
        }

    def visit(path: Path) -> None:
        path = path.resolve()
        key = str(path)
        if key in nodes or path in visiting:
            return
        visiting.add(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            nodes[key] = {
                "path": key,
                "exists": False,
                "error": str(exc),
                "includes": [],
                "sha256": None,
                **node_metadata(path, available=False, node_confidence="low"),
            }
            visiting.discard(path)
            return
        includes: list[str] = []
        node = {
            "path": key,
            "exists": True,
            "sha256": sha256(path),
            "includes": includes,
            **node_metadata(path, available=True, node_confidence=confidence),
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
                missing_key = f"<missing:{name}>"
                nodes.setdefault(
                    missing_key,
                    {
                        "path": missing_key,
                        "exists": False,
                        "sha256": None,
                        "includes": [],
                        "include": name,
                        **node_metadata(
                            Path(name), available=False, node_confidence="low"
                        ),
                    },
                )
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
        "provenance": {
            "source_id": source_id,
            "repository": repository,
            "commit": commit,
            "source_root": str(source_root) if source_root else None,
        },
        "status": "COMPLETE" if entry.is_file() and not missing else "BLOCKED",
        "nodes": sorted(nodes.values(), key=lambda item: item["path"]),
        "edges": sorted(edges, key=lambda item: (item["from"], item["to"])),
        "missing": sorted(missing, key=lambda item: (item["from"], item["include"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", type=Path, required=True)
    parser.add_argument("--include-dir", action="append", type=Path, default=[])
    parser.add_argument("--source-id", default="unknown")
    parser.add_argument("--repository")
    parser.add_argument("--commit")
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--confidence", default="unknown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_graph(
        args.entry,
        args.include_dir,
        source_id=args.source_id,
        repository=args.repository,
        commit=args.commit,
        source_root=args.source_root,
        confidence=args.confidence,
    )
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
