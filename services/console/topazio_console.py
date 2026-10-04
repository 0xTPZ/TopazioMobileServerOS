"""Serial-friendly local console banner for the ARM64 lab image."""

from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.status import collect_status  # noqa: E402


def _ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("198.51.100.1", 80))
        address = sock.getsockname()[0]
        sock.close()
        return address
    except OSError:
        return "unknown"


def render_banner() -> str:
    status = collect_status()
    return "\n".join(
        [
            "========================================",
            "TOPAZIO MOBILE SERVER OS",
            "",
            f"Hostname: {status.hostname}",
            f"IP:       {_ip()}",
            f"SSH:      {status.ssh if status.ssh != 'unknown' else 'ONLINE (service)'}",
            f"CPU:      {status.cpu_percent}",
            f"RAM:      {status.memory}",
            f"Disk:     {status.storage}",
            f"Temp:     {status.temperature}",
            f"Uptime:   {status.uptime}",
            "",
            "Connect from another machine:",
            "ssh admin@<IP>",
            "",
            "----------------------------------------",
            "TOPAZIO_BOOT_OK",
            "========================================",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Topazio serial console")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=30.0)
    args = parser.parse_args()
    while True:
        print(render_banner(), flush=True)
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
