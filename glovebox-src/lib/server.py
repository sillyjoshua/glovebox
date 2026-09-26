"""Tiny local web server. Binds to 127.0.0.1 only, standard library only."""

import json
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import toolkit

WEB = toolkit.ROOT / "web"
_lock = threading.Lock()
_progress = {"current": None, "done": 0, "total": 0, "log": []}


def _json(handler, code, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the console quiet

    def _origin_ok(self):
        """Reject requests that did not come from this page (blocks other sites
        from poking the local server through the browser)."""
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        host = self.headers.get("Host", "")
        return origin in (f"http://{host}",)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/tools":
            plat = toolkit.current_platform()
            state = toolkit.load_state()
            tools = []
            for t in toolkit.load_catalog():
                t = dict(t)
                t["status"] = state.get(t["id"], {}).get("status", "empty")
                t["supported"] = plat in t["platforms"]
                tools.append(t)
            return _json(self, 200, {
                "platform": plat,
                "free_mb": toolkit.disk_free_mb(),
                "tools": tools,
            })

        if path == "/api/progress":
            with _lock:
                return _json(self, 200, dict(_progress))

        if path == "/api/bundle.zip":
            state = toolkit.load_state()
            ids = [k for k, v in state.items() if v.get("status") in ("installed", "queued")]
            tmp = Path(tempfile.gettempdir()) / "glovebox-bundle.zip"
            toolkit.build_zip(ids, tmp)
            data = tmp.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="glovebox.zip"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # static files
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        target = (WEB / rel).resolve()
        if WEB.resolve() not in target.parents and target != WEB.resolve():
            self.send_error(403)
            return
        if not target.is_file():
            self.send_error(404)
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
        }.get(target.suffix, "application/octet-stream")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if not self._origin_ok():
            self.send_error(403, "Cross-origin request blocked")
            return
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return _json(self, 400, {"error": "Bad JSON"})

        if path == "/api/install":
            ids = body.get("ids") or []
            known = {t["id"] for t in toolkit.load_catalog()}
            ids = [i for i in ids if i in known]
            if not ids:
                return _json(self, 400, {"error": "No valid tools selected"})

            def work():
                with _lock:
                    _progress.update(current=None, done=0, total=len(ids), log=[])
                for n, tid in enumerate(ids, 1):
                    with _lock:
                        _progress["current"] = tid
                    ok, msg = toolkit.install_tool(tid)
                    with _lock:
                        _progress["done"] = n
                        _progress["log"].append({"id": tid, "ok": ok, "message": msg})
                with _lock:
                    _progress["current"] = None

            threading.Thread(target=work, daemon=True).start()
            return _json(self, 202, {"started": len(ids)})

        if path == "/api/mark-done":
            tid = body.get("id")
            if toolkit.find_tool(tid):
                toolkit.mark_done(tid)
                return _json(self, 200, {"ok": True})
            return _json(self, 400, {"error": "Unknown tool"})

        self.send_error(404)


def run(port=8765, open_browser=True):
    server = None
    for p in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit("Could not find a free port.")

    url = f"http://127.0.0.1:{port}/"
    print(f"\n  Glovebox is running at {url}")
    print("  Press Ctrl+C to stop.\n")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        server.server_close()
