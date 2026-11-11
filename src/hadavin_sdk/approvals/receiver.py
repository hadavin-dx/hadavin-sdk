"""Inbound approval callbacks. Framework-free: ``handle_action`` maps (headers, body) to (status, body).

It verifies the request, records the decision (``record_only``) and answers well inside the reply deadline of an
interactive channel (the tightest one known is 3 seconds). It never executes: ``tick`` reconcile runs approved
plans, so a repeated delivery can never cause double work. Production hosting is decided at S11; ``serve`` is a
stdlib server for the demo stage and local runs. Any other host must route by ``callback_path(approvals)``.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hadavin_sdk.approvals.channel import CALLBACK_PATH
from hadavin_sdk.approvals.requests import Approvals
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.protocol import NotFound

MAX_BODY = 64 * 1024  # interactive callback payloads are a few KB
MAX_PATH_CHARS = 64
_LOG = logging.getLogger("hadavin_sdk.receiver")


def callback_path(approvals: Approvals) -> str:
    """The URL path the configured channel kind's callbacks are posted to, checked: there is no fallback path."""
    channel = approvals.channel
    # `getattr` only so that a missing attribute gives this message; it never supplies a path.
    path = getattr(channel, "callback_path", None)
    if not isinstance(path, str) or len(path) > MAX_PATH_CHARS or not CALLBACK_PATH.fullmatch(path):
        name = getattr(channel, "name", None)
        name = name if isinstance(name, str) else type(channel).__name__
        raise ConfigError(f"channel {name}: callback_path must be a path such as /channel/actions")
    return path


def handle_action(
    approvals: Approvals, headers: Mapping[str, str], body: bytes
) -> tuple[int, bytes]:
    """401 for a bad or stale signature, 413 for an oversize body, else 200 (the outcome is audited and the
    channel message updated; a refused click is not an HTTP error)."""
    if len(body) > MAX_BODY:
        return 413, b""
    try:
        _, reason = approvals.receive(headers, body, record_only=True)
    except NotFound:  # signed, but for an approval this deployment does not have
        _LOG.warning("channel action for an unknown approval")
        return 200, b""
    if reason == "bad_signature":
        return 401, b""
    _LOG.info("channel action: %s", reason)
    return 200, b""


def serve(approvals: Approvals, host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """A stdlib server for ``POST`` to the configured channel's ``callback_path`` (every other path: 404); call
    ``serve_forever()`` on the result. Raises ``ConfigError`` when the channel names no valid path."""
    path = callback_path(approvals)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            raw = self.headers.get("Content-Length") or "0"
            length = int(raw) if raw.isascii() and raw.isdigit() else -1
            if self.path != path:
                status, out = 404, b""
            elif length < 0:
                status, out = 400, b""
            elif length > MAX_BODY:
                status, out = 413, b""
            else:
                status, out = handle_action(approvals, dict(self.headers), self.rfile.read(length))
            self.send_response(status)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, format: str, *args: object) -> None:
            _LOG.debug(format, *args)

    return ThreadingHTTPServer((host, port), Handler)
