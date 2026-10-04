"""Portable status collection for the first Core prototype.

The collector is deliberately best-effort: a PC test run and an Android/Linux
target expose different metrics. Missing platform metrics are represented as
``unknown`` instead of becoming false claims.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import socket
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


UNKNOWN = "unknown"


@dataclass(frozen=True)
class SystemStatus:
    service: str
    hostname: str
    architecture: str
    cpu_percent: str
    memory: str
    storage: str
    temperature: str
    uptime: str
    ssh: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _linux_memory() -> str:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return UNKNOWN
    values: dict[str, int] = {}
    for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].rstrip(":") in {"MemTotal", "MemAvailable"}:
            values[parts[0].rstrip(":")] = int(parts[1])
    if "MemTotal" not in values or "MemAvailable" not in values:
        return UNKNOWN
    used = values["MemTotal"] - values["MemAvailable"]
    return f"{used / 1024 / 1024:.1f} GB / {values['MemTotal'] / 1024 / 1024:.1f} GB"


def _linux_uptime() -> str:
    uptime = Path("/proc/uptime")
    if not uptime.exists():
        return UNKNOWN
    seconds = int(float(uptime.read_text(encoding="utf-8").split()[0]))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days}d {hours:02d}h {minutes:02d}m"


def collect_status(root: str | os.PathLike[str] = "/") -> SystemStatus:
    """Collect non-invasive metrics, returning ``unknown`` when unavailable."""

    try:
        hostname = socket.gethostname()
    except OSError:
        hostname = UNKNOWN
    usage = shutil.disk_usage(root)
    storage = f"{(usage.total - usage.free) / 1024**3:.1f} GB / {usage.total / 1024**3:.1f} GB"
    load = UNKNOWN
    loadavg = getattr(os, "getloadavg", None)
    if loadavg:
        try:
            load = f"{loadavg()[0]:.2f} load"
        except OSError:
            pass
    return SystemStatus(
        service="topazio-core-prototype",
        hostname=os.environ.get("TOPAZIO_HOSTNAME", hostname),
        architecture=platform.machine() or UNKNOWN,
        cpu_percent=load,
        memory=_linux_memory(),
        storage=storage,
        temperature=UNKNOWN,
        uptime=_linux_uptime(),
        ssh=os.environ.get("TOPAZIO_SSH_STATUS", UNKNOWN),
    )


def render_text(status: SystemStatus) -> str:
    """Render the stable, human-readable emergency-console summary."""

    return "\n".join(
        [
            "TOPAZIO MOBILE SERVER OS",
            "",
            f"Hostname: {status.hostname}",
            f"Arch:     {status.architecture}",
            f"SSH:      {status.ssh}",
            f"CPU:      {status.cpu_percent}",
            f"RAM:      {status.memory}",
            f"Storage:  {status.storage}",
            f"Temp:     {status.temperature}",
            f"Uptime:   {status.uptime}",
        ]
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Show Topazio status")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--root", default="/", help="filesystem root to measure")
    args = parser.parse_args()
    status = collect_status(args.root)
    if args.json:
        print(json.dumps(status.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_text(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
