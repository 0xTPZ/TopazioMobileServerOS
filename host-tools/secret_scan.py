"""Basic secret and forbidden-artifact scanner for local/CI use."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 5 * 1024 * 1024
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".img", ".bin", ".elf", ".dtb", ".dtbo", ".zip", ".7z"}
PATTERNS = [
    ("private-key", re.compile(rb"-----BEGIN [A-Z0-9 ]+PRIVATE KEY-----")),
    ("github-token", re.compile(rb"(?:ghp_|gho_|github_pat_)[A-Za-z0-9_]{20,}")),
    ("aws-access-key", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("generic-secret-assignment", re.compile(rb"(?i)(?:password|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[\"'][^\"']{12,}[\"']")),
]


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return [ROOT / line.strip() for line in result.stdout.splitlines() if line.strip()]


def _working_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "build" in path.parts and "out" in path.parts:
            continue
        paths.append(path)
    return paths


def scan(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in sorted(set(paths)):
        if not path.exists() or not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append(f"forbidden artifact suffix: {relative}")
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            findings.append(f"file too large (>5 MiB): {relative}")
            continue
        data = path.read_bytes()
        for name, pattern in PATTERNS:
            if pattern.search(data):
                findings.append(f"{name}: {relative}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--working-tree", action="store_true")
    group.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    findings = scan(_working_files() if args.working_tree else _tracked_files())
    if findings:
        for finding in findings:
            print(f"ERROR: {finding}")
        return 1
    print("secret/artifact scan clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
