"""Reproducible, host-only package acquisition with hash verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


def download(url: str, destination: Path, chunk_size: int = 1024 * 1024) -> dict[str, object]:
    if not url.startswith(("https://", "http://")):
        raise ValueError("only HTTP(S) package URLs are accepted")
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "TopazioFirmwareForensics/0.1"})
    with urllib.request.urlopen(request) as response, destination.open("wb") as output:
        digest = hashlib.sha256()
        total = 0
        while block := response.read(chunk_size):
            output.write(block)
            digest.update(block)
            total += len(block)
    return {"url": url, "path": str(destination.resolve()), "size_bytes": total, "sha256": digest.hexdigest()}


def validate(result: dict[str, object], expected_size: int | None, expected_md5: str | None, expected_sha256: str | None) -> None:
    if expected_size is not None and result["size_bytes"] != expected_size:
        raise ValueError(f"size mismatch: expected {expected_size}, got {result['size_bytes']}")
    if expected_sha256 and result["sha256"].lower() != expected_sha256.lower():
        raise ValueError("SHA-256 mismatch")
    if expected_md5:
        import hashlib

        digest = hashlib.md5()
        with Path(str(result["path"])).open("rb") as stream:
            while block := stream.read(1024 * 1024):
                digest.update(block)
        if digest.hexdigest().lower() != expected_md5.lower():
            raise ValueError("MD5 mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--expected-size", type=int)
    parser.add_argument("--expected-md5")
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    result = download(args.url, args.destination)
    validate(result, args.expected_size, args.expected_md5, args.expected_sha256)
    result["validation"] = {
        "expected_size": args.expected_size,
        "expected_md5": args.expected_md5,
        "expected_sha256": args.expected_sha256,
        "passed": True,
    }
    if args.provenance:
        args.provenance.parent.mkdir(parents=True, exist_ok=True)
        args.provenance.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
