"""
Legal-Bridge AI Local Server
Zero-dependency Python server that serves Legal-Bridge AI and proxies requests to Ollama
with streaming support and CORS handling.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import os
import webbrowser

PORT = 8000
OLLAMA_HOST = "http://127.0.0.1:11434"
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class LegalBridgeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for local interactions
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        # Route default root to legal_bridge_ai.html
        if self.path == '/' or self.path == '':
            self.path = '/legal_bridge_ai.html'
            return super().do_GET()

        # Reverse proxy for Ollama GET endpoints (e.g. /api/tags, /api/version)
        if self.path.startswith('/api/ollama/'):
            target_path = self.path[len('/api/ollama'):]
            target_url = urllib.parse.urljoin(OLLAMA_HOST, target_path)
            try:
                req = urllib.request.Request(target_url, headers={'User-Agent': 'LegalBridgeAI'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    self.send_response(response.status)
                    for key, val in response.getheaders():
                        if key.lower() not in ['transfer-encoding', 'content-length', 'access-control-allow-origin']:
                            self.send_header(key, val)
                    self.end_headers()
                    self.wfile.write(response.read())
            except Exception as e:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'Failed to connect to Ollama: {str(e)}'}).encode())
            return

        return super().do_GET()

    def do_POST(self):
        # Reverse proxy for Ollama POST endpoints (e.g. /api/chat, /api/generate)
        if self.path.startswith('/api/ollama/'):
            target_path = self.path[len('/api/ollama'):]
            target_url = urllib.parse.urljoin(OLLAMA_HOST, target_path)
            content_length = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_length)

            try:
                req = urllib.request.Request(
                    target_url,
                    data=post_body,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'LegalBridgeAI'
                    },
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=300) as response:
                    self.send_response(response.status)
                    self.send_header('Content-Type', response.headers.get('Content-Type', 'application/x-ndjson'))
                    self.send_header('Transfer-Encoding', 'chunked')
                    self.end_headers()

                    # Stream chunks back to client
                    while True:
                        chunk = response.read(1024)
                        if not chunk:
                            break
                        self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
                        self.wfile.flush()
                    self.wfile.write(b"0\r\n\r\n")
                    self.wfile.flush()
            except Exception as e:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'Ollama request failed: {str(e)}'}).encode())
            return

        self.send_response(404)
        self.end_headers()

def run():
    global PORT
    while PORT < 8020:
        try:
            with socketserver.ThreadingTCPServer(("", PORT), LegalBridgeHandler) as httpd:
                print(f"======================================================")
                print(f" Legal-Bridge AI is running at: http://localhost:{PORT}")
                print(f" Connected to Ollama at: {OLLAMA_HOST}")
                print(f" Press Ctrl+C to stop.")
                print(f"======================================================")
                # Open browser
                webbrowser.open(f"http://localhost:{PORT}")
                httpd.serve_forever()
                break
        except OSError as e:
            if e.errno == 10048 or "Address already in use" in str(e):
                PORT += 1
            else:
                raise e

if __name__ == '__main__':
    run()
