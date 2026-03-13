#!/usr/bin/env python3
"""Simple HTTP server to serve datapulse-ui.html"""
import http.server
import os
import socketserver

PORT = 3001


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve index.html for root path
        if self.path == "/" or self.path == "":
            self.path = "/datapulse-ui.html"
        return super().do_GET()

    def end_headers(self):
        # Add CORS and Private Network Access headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()


os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print("✓ DataPulse UI Server running!")
    print(f"📱 UI URL: http://[your-ip]:{PORT}")
    print("📊 Backend API: http://[your-ip]:8000")
    print("📈 Analytics Dashboard: http://[your-ip]:8501")
    print("\n⚠️  IMPORTANT: When accessing remotely, ensure your firewall allows ports 3001, 8000, and 8501.")
    print("\nPress Ctrl+C to stop the server\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
