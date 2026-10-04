import json
import threading
import unittest
from http.client import HTTPConnection

from services.console.topazio_console import render_banner
from services.http.topazio_http import Handler
from services.metrics.topazio_metrics import render_metrics
from services.status.topazio_status import main as status_main
from http.server import ThreadingHTTPServer
from unittest.mock import patch


class ServiceContractTests(unittest.TestCase):
    def test_console_has_machine_readable_boot_marker(self):
        self.assertIn("TOPAZIO_BOOT_OK", render_banner())

    def test_metrics_expose_core_and_architecture(self):
        metrics = render_metrics()
        self.assertIn("topazio_up 1", metrics)
        self.assertIn("topazio_build_info", metrics)

    def test_status_json_entrypoint(self):
        with patch("sys.argv", ["topazio-status", "--json"]), patch("builtins.print") as printer:
            self.assertEqual(status_main(), 0)
        payload = json.loads(printer.call_args.args[0])
        self.assertEqual(payload["service"], "topazio-core-prototype")

    def test_http_health_and_missing_routes(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/healthz")
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())["status"], "ok")
            connection.close()

            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/missing")
            response = connection.getresponse()
            self.assertEqual(response.status, 404)
            self.assertEqual(json.loads(response.read())["error"], "not-found")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
