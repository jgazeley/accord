"""accord-upload/1 offset, append and durable completion, plus health.

Supports the cd64ce5 client: stable U_<id>.CSV identities, acknowledged byte
prefixes and explicit completion. Per-file locks serialize append and complete;
HTTP success waits for durability, but never for trip building. Early failure
closes HTTP/1.1 connections so an unread body cannot become a new request.
"""
import json
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from storage import MAX_CHUNK, FILE_RE, UNIT_RE, Store


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "accord-upload/1"

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    # ---- plumbing ------------------------------------------------------
    def log_message(self, fmt, *args):
        # Never the Authorization header, never the body (PROTOCOL §4), and
        # never /health -- a probe every minute is 1440 lines a day in a file
        # nobody rotates, which is the lesson tripingest.py records.
        if "/health" in (self.path or ""):
            return
        sys.stderr.write(f"upload {self.address_string()} {fmt % args}\n")

    def reply(self, code, payload):
        body = json.dumps(payload).encode()
        if code != 200:
            # See the module docstring: an unread request body would be read as
            # the start of the next request on a kept-alive connection.
            self.close_connection = True
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorised(self):
        if not self.server.token:
            return True
        # Compared in full rather than with a prefix check, so a missing or
        # malformed header cannot accidentally match.
        if self.headers.get("Authorization", "") == f"Bearer {self.server.token}":
            return True
        self.reply(401, {"error": "unauthorised"})
        return False

    def params(self, query, need_from):
        q = parse_qs(query)
        unit = (q.get("unit") or [""])[0]
        name = (q.get("file") or [""])[0]
        # Both are used to build a path, so both are validated rather than
        # trusted: the receiver may be talking to anything at all.
        if not UNIT_RE.fullmatch(unit):
            self.reply(400, {"error": "unit must be 16 hex digits"})
            return None
        if not FILE_RE.fullmatch(name) or name in (".", ".."):
            self.reply(400, {"error": "file name rejected"})
            return None
        if not need_from:
            return unit, name, None
        raw = (q.get("from") or [""])[0]
        if not raw.isdigit():
            self.reply(400, {"error": "from must be a non-negative integer"})
            return None
        return unit, name, int(raw)

    # ---- the two endpoints, plus health --------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        if url.path.rstrip("/") in ("/health", ""):
            return self.reply(200, self.server.health())
        if url.path != "/v1/offset":
            return self.reply(404, {"error": "no such endpoint"})
        if not self.authorised():
            return
        got = self.params(url.query, need_from=False)
        if not got:
            return
        unit, name, _ = got
        try:
            held, complete = self.server.store.status(unit, name)
        except (OSError, ValueError):
            return self.reply(500, {"error": "storage failure"})
        self.log_message("offset %s/%s -> %d", unit, name, held)
        self.reply(200, {"file": name, "bytes": held, "complete": complete})

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/v1/complete":
            return self.do_complete(url)
        if url.path != "/v1/append":
            return self.reply(404, {"error": "no such endpoint"})
        if not self.authorised():
            return
        got = self.params(url.query, need_from=True)
        if not got:
            return
        unit, name, start = got
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.reply(400, {"error": "bad Content-Length"})
        if length < 0 or length > MAX_CHUNK:
            return self.reply(413, {"error": f"chunk larger than {MAX_CHUNK}"})
        if self.headers.get("Transfer-Encoding"):
            return self.reply(400, {"error": "transfer encoding unsupported"})
        try:
            body = self.rfile.read(length) if length else b""
        except (TimeoutError, socket.timeout):
            return self.reply(408, {"error": "body timeout"})
        if len(body) != length:
            return self.reply(400, {"error": "short body"})
        try:
            total, held = self.server.store.append(unit, name, start, body)
            if total is None:
                held, complete = self.server.store.status(unit, name)
        except (OSError, ValueError):
            return self.reply(500, {"error": "storage failure"})
        if total is None:
            # The ONE interesting response. Nothing was written; the client is
            # told where we actually are and retries from there.
            self.log_message("append %s/%s from=%d REJECTED, hold %d",
                             unit, name, start, held)
            return self.reply(409, {"file": name, "bytes": held, "complete": complete})
        self.log_message("append %s/%s from=%d +%d -> %d",
                         unit, name, start, len(body), total)
        self.reply(200, {"file": name, "bytes": total})
        # After the client has its answer, never before: ingestion must not
        # wait on trip building, and a POST must cost the Pico one chunk of
        # core-0 time whatever the pipeline is doing.
        self.server.touched()

    def do_complete(self, url):
        if not self.authorised():
            return
        got = self.params(url.query, need_from=False)
        if not got:
            return
        unit, name, _ = got
        values = parse_qs(url.query).get("bytes", [])
        if len(values) != 1 or not values[0].isascii() or not values[0].isdigit():
            return self.reply(400, {"error": "bytes must be a non-negative integer"})
        if self.headers.get("Content-Length", "0") != "0" or self.headers.get("Transfer-Encoding"):
            return self.reply(400, {"error": "completion has no body"})
        try:
            complete, held = self.server.store.complete(unit, name, int(values[0]))
        except (OSError, ValueError):
            return self.reply(500, {"error": "storage failure"})
        self.reply(200 if complete else 409,
                   {"file": name, "bytes": held, "complete": complete})
        if complete:
            self.server.touched()


class Server(ThreadingHTTPServer):
    """Threaded so one slow client cannot hold the port.

    Concurrency is safe because `Store.append` serialises on a per-file lock,
    which is the one thing the reference receiver says it is missing.
    """
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, store, token, on_append=None, health=None):
        super().__init__(address, Handler)
        self.store = store
        self.token = token
        self._on_append = on_append or (lambda: None)
        self._health = health or (lambda: {"ok": True})

    def touched(self):
        self._on_append()

    def health(self):
        return self._health()


def serve(root, token, port, host="0.0.0.0", on_append=None, health=None):
    """Signature-compatible with the reference receiver's `serve`.

    `tests/check_protocol.py` substitutes this module for the reference and
    runs its suite unchanged, so this signature is load-bearing.
    """
    return Server((host, port), Store(root), token, on_append, health)
