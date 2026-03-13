#!/usr/bin/env python3
"""Simple HTTP server for the canonical frontend UI."""

import http.server
import os
import socketserver
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
PORT = int(os.getenv("PORT", "3001"))


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve the canonical frontend UI file at root.
        if self.path in {"/", ""}:
            self.path = "/datapulse-ui.html"
        return super().do_GET()

    def end_headers(self):
        # Add CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()


if not FRONTEND_ROOT.exists():
    raise FileNotFoundError(f"Frontend directory not found: {FRONTEND_ROOT}")

# Use frontend/ as the source of truth for local UI serving.
os.chdir(FRONTEND_ROOT)

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print("DataPulse UI server running")
    print(f"UI URL: http://localhost:{PORT}")
    print("Backend API: http://localhost:8000")
    print("Source of truth: frontend/datapulse-ui.html")
    print("\nPress Ctrl+C to stop the server\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
