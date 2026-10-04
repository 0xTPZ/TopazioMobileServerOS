"""Topazio status service entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.status import collect_status, render_text  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Topazio status")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", default="/")
    args = parser.parse_args()
    status = collect_status(args.root)
    print(json.dumps(status.to_dict(), sort_keys=True) if args.json else render_text(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
