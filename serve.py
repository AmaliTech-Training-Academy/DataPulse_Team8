#!/usr/bin/env python3
"""Simple HTTP server to serve datapulse-ui.html"""
import http.server
import socketserver
import os
from http import HTTPStatus

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/' or self.path == '':
            self.path = '/datapulse-ui.html'
        return super().do_GET()
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"✓ DataPulse UI Server running!")
    print(f"📱 Open your browser to: http://localhost:{PORT}")
    print(f"📊 Backend API: http://localhost:8000")
    print(f"\nDefault credentials: qa_user@datapulse.com / qapassword123")
    print(f"\nPress Ctrl+C to stop the server\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
