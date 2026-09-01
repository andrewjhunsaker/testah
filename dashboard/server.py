"""Loopback HTTP interface for the Current Snapshot."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from dashboard.snapshot import build_snapshot, snapshot_version


def make_server(root: Path, port: int = 0) -> ThreadingHTTPServer:
    """Create a loopback-only server scoped to one repository root."""
    repository_root = root.resolve()
    ui_root = Path(__file__).parent / "ui"

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/snapshot":
                self._send_json(build_snapshot(repository_root))
            elif path == "/api/version":
                self._send_json({"version": snapshot_version(repository_root)})
            elif path == "/":
                self._send_file(ui_root / "index.html", "text/html; charset=utf-8")
            elif path == "/styles.css":
                self._send_file(ui_root / "styles.css", "text/css; charset=utf-8")
            elif path == "/dist/app.js":
                self._send_file(ui_root / "dist" / "app.js", "text/javascript; charset=utf-8")
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            self._method_not_allowed()

        def do_PUT(self) -> None:
            self._method_not_allowed()

        def do_PATCH(self) -> None:
            self._method_not_allowed()

        def do_DELETE(self) -> None:
            self._method_not_allowed()

        def _send_json(self, body: dict[str, object]) -> None:
            encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_file(self, path: Path, content_type: str) -> None:
            try:
                encoded = path.read_bytes()
            except OSError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _method_not_allowed(self) -> None:
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_header("Allow", "GET")
            self.end_headers()

    return ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
