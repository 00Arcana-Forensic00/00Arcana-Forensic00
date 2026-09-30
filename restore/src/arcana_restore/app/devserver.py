"""Serve the UI in an ordinary browser for development and automated UI tests.

    python -m arcana_restore.app.devserver [--port 8765]

Binds 127.0.0.1 only and requires a per-run token in the URL. The shipped app does
not use this: it talks to the back end through pywebview's in-process bridge.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .api import Api, call

WEB = os.path.join(os.path.dirname(__file__), "web")
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript"}


def make_server(api: Api, port: int = 0, token: str | None = None):
    token = token or secrets.token_urlsafe(16)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _ok_cookie(self):
            return f"arcalume_dev={token}" in (self.headers.get("Cookie") or "")

        def do_GET(self):
            u = urlparse(self.path)
            name = os.path.basename(u.path) or "index.html"
            if name == "index.html":
                if parse_qs(u.query).get("t", [""])[0] != token and not self._ok_cookie():
                    return self.send_error(403)
            elif not self._ok_cookie():
                return self.send_error(403)
            path = os.path.join(WEB, name)
            if not os.path.isfile(path):
                return self.send_error(404)
            body = open(path, "rb").read()
            if name == "index.html":
                body = body.replace(b"<script src=\"app.js\">", b"<script>window.__ARCALUME_TEST_BRIDGE__=1</script><script src=\"app.js\">")
            self.send_response(200)
            self.send_header("Content-Type", TYPES.get(os.path.splitext(name)[1], "application/octet-stream"))
            self.send_header("Set-Cookie", f"arcalume_dev={token}; SameSite=Strict; HttpOnly; Path=/")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            u = urlparse(self.path)
            if not u.path.startswith("/__api/") or not self._ok_cookie():
                return self.send_error(403)
            n = int(self.headers.get("Content-Length") or 0)
            args = json.loads(self.rfile.read(n) or b"[]")
            body = json.dumps(call(api, u.path[len("/__api/"):], args)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html?t={token}"
    return srv, url


def serve_in_thread(api: Api):
    srv, url = make_server(api)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, url


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    srv, url = make_server(Api(), a.port)
    print(f"open {url}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
