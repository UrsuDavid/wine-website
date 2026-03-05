#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PORT="${1:-8765}"

python3 - "$PORT" <<'PY'
import http.server
import socketserver
import sys

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
handler = http.server.SimpleHTTPRequestHandler

try:
  httpd = socketserver.TCPServer(("", port), handler)
except OSError:
  httpd = socketserver.TCPServer(("", 0), handler)

host, actual_port = httpd.server_address
print(f"Serving on http://localhost:{actual_port}", flush=True)

try:
  httpd.serve_forever()
finally:
  httpd.server_close()
PY

