"""Create a deterministic manifest for the source rootfs skeleton."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def build_manifest(root: Path) -> dict[str, object]:
    files = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": path.relative_to(root).as_posix(), "sha256": digest, "bytes": path.stat().st_size})
    return {"schema": 1, "kind": "rootfs-source-manifest", "files": files}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("core/rootfs"))
    parser.add_argument("--output", type=Path, default=Path("build/out/rootfs-manifest.json"))
    args = parser.parse_args()
    manifest = build_manifest(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({len(manifest['files'])} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
