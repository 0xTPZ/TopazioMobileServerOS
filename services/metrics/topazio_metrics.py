"""Dependency-free metrics writer for the Topazio lab image."""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.status import collect_status  # noqa: E402


RUNNING = True


def _stop(*_: object) -> None:
    global RUNNING
    RUNNING = False


def _number(value: str) -> float:
    try:
        return float(value.split()[0])
    except (ValueError, IndexError):
        return 0.0


def render_metrics() -> str:
    status = collect_status()
    return "\n".join(
        [
            "# HELP topazio_up Topazio Core process is collecting metrics",
            "# TYPE topazio_up gauge",
            "topazio_up 1",
            "# TYPE topazio_storage_used_gib gauge",
            f"topazio_storage_used_gib {_number(status.storage):.3f}",
            "# TYPE topazio_build_info gauge",
            f'topazio_build_info{{architecture="{status.architecture}"}} 1',
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Topazio metrics")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    while RUNNING:
        payload = render_metrics()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="", flush=True)
        if args.once:
            break
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
