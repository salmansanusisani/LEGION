"""The HTTP server.

Standard library only: a threading ``HTTPServer`` over ``BaseHTTPRequestHandler``.
The spec's load profile is 50 in-flight requests against 2 vCPU, which a thread
per connection absorbs comfortably because every request is a short SQLite
transaction.

Two details matter for conformance rather than speed:

* every response carries an accurate ``Content-Length``, so HTTP/1.1 keep-alive
  works and a client never has to guess where a body ends;
* section 3.4's media type is sent on every JSON response, including errors.
"""
from __future__ import annotations

import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import config, errors, jsonutil
from .transport import Application, Request

SERVER_TOKEN = "tablekeeper"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = SERVER_TOKEN
    sys_version = ""

    application: Application  # injected by serve()

    # -- body ----------------------------------------------------------

    def _read_body(self) -> bytes:
        encoding = (self.headers.get("Transfer-Encoding") or "").strip().lower()
        if encoding == "chunked":
            return self._read_chunked()
        raw_length = self.headers.get("Content-Length")
        if not raw_length:
            return b""
        try:
            length = int(raw_length)
        except ValueError:
            return b""
        if length <= 0:
            return b""
        if length > config.MAX_BODY_BYTES:
            raise errors.malformed_request("the request body is too large")
        return self.rfile.read(length)

    def _read_chunked(self) -> bytes:
        chunks = bytearray()
        while True:
            line = self.rfile.readline(64).strip()
            if not line:
                break
            try:
                size = int(line.split(b";")[0], 16)
            except ValueError:
                raise errors.malformed_request("malformed chunked body") from None
            if size == 0:
                self.rfile.readline(4)
                break
            if len(chunks) + size > config.MAX_BODY_BYTES:
                raise errors.malformed_request("the request body is too large")
            chunks += self.rfile.read(size)
            self.rfile.readline(4)
        return bytes(chunks)

    # -- responses -----------------------------------------------------

    def _respond(self, status: int, payload) -> None:
        body = b"" if payload is None else jsonutil.encode(payload)
        self.send_response(status)
        if status != 204:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if status != 204 and self.command != "HEAD" and body:
            self.wfile.write(body)

    def _serve(self, method: str) -> None:
        try:
            body = self._read_body()
        except errors.ApiError as exc:
            self._respond(exc.status, exc.body())
            return
        except (socket.timeout, ConnectionError):
            return
        request = Request(method, self.path, self.headers, body)
        response = self.application.handle(request)
        try:
            self._respond(response.status, response.body)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    # -- verbs ---------------------------------------------------------

    def do_GET(self) -> None:
        self._serve("GET")

    def do_POST(self) -> None:
        self._serve("POST")

    def do_PATCH(self) -> None:
        self._serve("PATCH")

    def do_PUT(self) -> None:
        self._serve("PUT")

    def do_DELETE(self) -> None:
        self._serve("DELETE")

    def do_HEAD(self) -> None:
        self._serve("HEAD")

    def log_message(self, fmt, *args) -> None:  # pragma: no cover - quiet by design
        pass

    def log_error(self, fmt, *args) -> None:  # pragma: no cover - quiet by design
        pass


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 256

    def __init__(self, address, application) -> None:
        handler = type("BoundHandler", (Handler,), {"application": application})
        super().__init__(address, handler)

    def handle_error(self, request, client_address) -> None:
        # A dropped client connection is not a service fault; never spam stderr.
        exc = sys.exc_info()[0]
        if exc in (BrokenPipeError, ConnectionResetError, socket.timeout):
            return
        super().handle_error(request, client_address)


def serve(store, host: str, port: int) -> Server:
    application = Application(store)
    return Server((host, port), application)
