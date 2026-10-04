"""Small dependency-free HTTP diagnostic service."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.status import collect_status  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    server_version = "TopazioHTTP/0.1"

    def _send(self, status: int, body: str, content_type: str = "application/json") -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        status = collect_status()
        if self.path == "/healthz":
            self._send(200, json.dumps({"status": "ok", "service": status.service}))
        elif self.path == "/status":
            self._send(200, json.dumps(status.to_dict(), sort_keys=True))
        elif self.path == "/metrics":
            lines = [
                "# TYPE topazio_info gauge",
                "topazio_info 1",
                f"topazio_storage_bytes {__import__('shutil').disk_usage('/').used}",
            ]
            self._send(200, "\n".join(lines) + "\n", "text/plain; version=0.0.4")
        else:
            self._send(404, json.dumps({"error": "not-found"}))

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write((fmt % args) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Topazio diagnostic HTTP service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--once", action="store_true", help="print a status response and exit")
    args = parser.parse_args()
    if args.once:
        print(json.dumps({"status": "ok", "service": "topazio-http", "port": args.port}))
        return 0
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Topazio HTTP listening on {args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
