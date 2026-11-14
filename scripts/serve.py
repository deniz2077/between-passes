"""Local dev server for app/ with caching disabled. Usage: python3 scripts/serve.py [port]"""
import functools
import http.server
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")


class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
handler = functools.partial(NoCache, directory=os.path.abspath(ROOT))
print(f"Serving {os.path.abspath(ROOT)} on http://localhost:{port}")
http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
