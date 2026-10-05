"""Reproducible, host-only package acquisition with hash verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path


def download(
    url: str,
    destination: Path,
    chunk_size: int = 1024 * 1024,
    resume: bool = False,
    range_start: int | None = None,
    range_end: int | None = None,
) -> dict[str, object]:
    if not url.startswith(("https://", "http://")):
        raise ValueError("only HTTP(S) package URLs are accepted")
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "TopazioFirmwareForensics/0.2"}
    append = False
    if range_start is not None:
        if range_start < 0 or (range_end is not None and range_end < range_start):
            raise ValueError("invalid HTTP range")
        suffix = "" if range_end is None else str(range_end)
        headers["Range"] = f"bytes={range_start}-{suffix}"
    elif resume and destination.exists():
        existing_size = destination.stat().st_size
        if existing_size:
            headers["Range"] = f"bytes={existing_size}-"
            append = True
    request = urllib.request.Request(url, headers=headers)
    try:
        response_context = urllib.request.urlopen(request)
    except urllib.error.HTTPError as error:
        if error.code == 416 and append:
            return {
                "url": url,
                "path": str(destination.resolve()),
                "size_bytes": destination.stat().st_size,
                "sha256": sha256_path(destination),
                "resumed": True,
                "range": None,
                "complete_by_server": True,
            }
        raise
    with response_context as response:
        if append and getattr(response, "status", 200) != 206:
            append = False
        mode = "ab" if append else "wb"
        with destination.open(mode) as output:
            digest = hashlib.sha256()
            if append:
                with destination.open("rb") as existing:
                    while block := existing.read(chunk_size):
                        digest.update(block)
            total = destination.stat().st_size if append else 0
            while block := response.read(chunk_size):
                output.write(block)
                digest.update(block)
                total += len(block)
    return {
        "url": url,
        "path": str(destination.resolve()),
        "size_bytes": total,
        "sha256": digest.hexdigest(),
        "resumed": append,
        "range": {"start": range_start, "end": range_end} if range_start is not None else None,
    }


def sha256_path(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


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
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--range-start", type=int)
    parser.add_argument("--range-end", type=int)
    args = parser.parse_args()
    result = download(
        args.url,
        args.destination,
        resume=args.resume,
        range_start=args.range_start,
        range_end=args.range_end,
    )
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
