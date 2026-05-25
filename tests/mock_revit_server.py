"""
Mock pyRevit Routes server for testing.
Runs a lightweight HTTP server that mimics the pyRevit Routes API responses
without requiring Revit to be installed.

Usage:
    python tests/mock_revit_server.py
    # or in pytest:
    from tests.mock_revit_server import MockRevitServer
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse

# ------------------------------------------------------------------
# Mock data
# ------------------------------------------------------------------

MOCK_PROJECT_INFO = {
    "project_name": "Test Project",
    "project_number": "2026-001",
    "client_name": "ACME Corp",
    "building_name": "Test Building",
    "address": "123 Main St",
    "issue_date": "2026-01-01",
    "status": "Design Development",
    "author": "Test User",
    "file_path": "C:\\Projects\\test.rvt",
    "revit_version": "2025",
    "is_workshared": False,
    "is_detached": False,
}

MOCK_LEVELS = [
    {"element_id": 1001, "name": "Level 1", "elevation": 0.0},
    {"element_id": 1002, "name": "Level 2", "elevation": 13.123359580052493},  # ~4000mm
    {"element_id": 1003, "name": "Level 3", "elevation": 26.246719160104987},  # ~8000mm
]

MOCK_ELEMENTS = [
    {"element_id": 2001, "category": "Walls", "name": "Basic Wall : Generic - 200mm", "level": "Level 1"},
    {"element_id": 2002, "category": "Doors", "name": "Single-Flush : 36\" x 84\"", "level": "Level 1"},
    {"element_id": 2003, "category": "Windows", "name": "Fixed : 24\" x 48\"", "level": "Level 1"},
]

MOCK_ROOMS = [
    {"element_id": 3001, "number": "101", "name": "Office", "level": "Level 1",
     "area": 215.278, "perimeter": 59.055},
    {"element_id": 3002, "number": "102", "name": "Conference", "level": "Level 1",
     "area": 537.0, "perimeter": 94.0},
]

MOCK_SHEETS = [
    {"element_id": 4001, "sheet_number": "A-101", "sheet_name": "LEVEL 1 FLOOR PLAN", "views": []},
    {"element_id": 4002, "sheet_number": "A-102", "sheet_name": "LEVEL 2 FLOOR PLAN", "views": []},
]


# ------------------------------------------------------------------
# Request handler
# ------------------------------------------------------------------

class MockRevitHandler(BaseHTTPRequestHandler):

    ROUTES: dict[str, Any] = {
        "GET /revit/ping": {"status": "ok", "revit_version": "2025", "document_open": True},
        "GET /revit/project/info": MOCK_PROJECT_INFO,
        "GET /revit/project/stats": {"total_elements": 500, "category_counts": {"Walls": 50}},
        "GET /revit/project/warnings": [],
        "GET /revit/project/links": [],
        "GET /revit/levels": MOCK_LEVELS,
        "GET /revit/rooms": MOCK_ROOMS,
        "GET /revit/sheets": MOCK_SHEETS,
        "GET /revit/elements/by_category": MOCK_ELEMENTS,
        "GET /revit/families/categories": [{"category": "Doors", "family_count": 5}],
        "GET /revit/worksets/status": {"workshared": False},
        "GET /revit/materials": [{"element_id": 5001, "name": "Concrete", "material_class": "Concrete"}],
    }

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress default access logs in tests

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        key = f"GET {path}"
        if key in self.ROUTES:
            self._send_json(self.ROUTES[key])
        elif path.startswith("/revit/elements/") and path.endswith("/parameters"):
            self._send_json([{"name": "Mark", "value": "1", "storage_type": "String", "read_only": False}])
        else:
            self._send_json({"error": f"Mock route not found: {path}"}, 404)

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}
        path = urlparse(self.path).path
        if path == "/revit/sheets/create":
            self._send_json({"element_id": 9001, "sheet_number": body.get("sheet_number"), "sheet_name": body.get("sheet_name")})
        elif path == "/revit/levels/create":
            self._send_json({"element_id": 9002, "name": body.get("level_name", "New Level"), "elevation": body.get("elevation", 0)})
        elif path == "/revit/families/place":
            self._send_json({"element_id": 9003, "family": body.get("family_name"), "type": body.get("type_name")})
        else:
            self._send_json({"status": "ok", "message": f"POST to {path} accepted"})

    def do_DELETE(self) -> None:
        self._send_json({"status": "ok", "deleted_count": 1})


# ------------------------------------------------------------------
# Server class
# ------------------------------------------------------------------

class MockRevitServer:
    """Context manager that runs a mock pyRevit Routes server in a thread."""

    def __init__(self, host: str = "localhost", port: int = 48884):
        self.host = host
        self.port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "MockRevitServer":
        self._server = HTTPServer((self.host, self.port), MockRevitHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_: Any) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None


if __name__ == "__main__":
    print(f"Starting mock Revit server on http://localhost:48884")
    print("Press Ctrl+C to stop.")
    server = HTTPServer(("localhost", 48884), MockRevitHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
