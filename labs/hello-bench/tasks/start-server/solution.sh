#!/bin/bash
cat > /workspace/server.py <<'PY'
from http.server import BaseHTTPRequestHandler, HTTPServer


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"hello")

    def log_message(self, *a):
        pass


HTTPServer(("127.0.0.1", 8080), H).serve_forever()
PY
