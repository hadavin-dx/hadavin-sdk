"""The one place where the helper scripts open a web address: only http and https are allowed, never file:, ftp: or
any other scheme (urllib would open those too). Used by feed.py, n8n_api.py, run_real_check.py, demo_only/burst.py and
load_tools/load_driver.py.

Two layers, so that a new caller cannot reopen the hole: the scheme is checked BEFORE the opener is used, and the opener
itself is built from the http and https handlers only (urllib's default opener also carries a file: handler, which reads
a named pipe for ever, and an ftp: handler)."""

from __future__ import annotations

import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

try:  # started as a script from another folder: the src folder is added (the one place for the reply limit)
    from lead_desk.constants import (
        FAKE_BODY_DEADLINE_SECONDS,
        FAKE_BODY_MAX_BYTES,
        FAKE_HEAD_DEADLINE_SECONDS,
        FAKE_SOCKET_TIMEOUT_SECONDS,
        SCRIPT_REPLY_MAX_BYTES,
    )
    from lead_desk.jsonread import loads_bounded as loads_bounded  # re-exported: the ONE parse call of the fakes
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from lead_desk.constants import (
        FAKE_BODY_DEADLINE_SECONDS,
        FAKE_BODY_MAX_BYTES,
        FAKE_HEAD_DEADLINE_SECONDS,
        FAKE_SOCKET_TIMEOUT_SECONDS,
        SCRIPT_REPLY_MAX_BYTES,
    )
    from lead_desk.jsonread import loads_bounded as loads_bounded  # re-exported: the ONE parse call of the fakes

ALLOWED_SCHEMES = ("http", "https")
ONLY_HTTP_TEXT = "only http and https addresses are opened"
REPLY_TOO_BIG_TEXT = "the reply is too big to read (it is more than the allowed size)"


class ReplyTooBig(ValueError):
    """A web reply is longer than SCRIPT_REPLY_MAX_BYTES. The text is fixed (no address, no body)."""


def read_reply(reply: Any, max_bytes: int = SCRIPT_REPLY_MAX_BYTES) -> bytes:
    """The body of a web reply (an open response or an HTTPError), at most `max_bytes` of it: one byte more is read to
    tell "exactly the limit" from "longer", and a longer body is a ReplyTooBig. Why: `reply.read()` with no limit takes
    whatever a stand-in, a proxy or a broken service sends, until memory is full. Every helper script reads replies
    through this function; the guard test names the bare `.read()` calls it refuses."""
    data: bytes = reply.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ReplyTooBig(REPLY_TOO_BIG_TEXT)
    return data


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuses to follow a redirect: the 3xx answer is raised as urllib.error.HTTPError instead."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def http_only_opener(follow_redirects: bool = True, use_proxy: bool = True) -> urllib.request.OpenerDirector:
    """An opener that knows the http and https schemes and nothing else (no file:, ftp: or data: handler).
    `use_proxy=False`: the proxy settings of the environment are ignored (an empty proxy map). `follow_redirects=False`:
    the 3xx answer is raised as urllib.error.HTTPError."""
    opener = urllib.request.OpenerDirector()
    for handler in (
        urllib.request.ProxyHandler({}) if not use_proxy else urllib.request.ProxyHandler(),
        urllib.request.UnknownHandler(),  # a redirect to another scheme ends as URLError, never as a file read
        urllib.request.HTTPHandler(),
        urllib.request.HTTPSHandler(),
        urllib.request.HTTPDefaultErrorHandler(),
        _NoRedirect() if not follow_redirects else urllib.request.HTTPRedirectHandler(),
        urllib.request.HTTPErrorProcessor(),
    ):
        opener.add_handler(handler)
    return opener


def check_scheme(url: str) -> None:
    """ValueError unless `url` can be split and is an http or https address."""
    try:
        scheme = urlsplit(url).scheme.lower()
    except ValueError:  # `http://[::1`: an unclosed bracket
        raise ValueError(ONLY_HTTP_TEXT) from None
    if scheme not in ALLOWED_SCHEMES:
        raise ValueError(ONLY_HTTP_TEXT)


def open_http(
    req: urllib.request.Request | str, timeout: float, follow_redirects: bool = True, use_proxy: bool = True
) -> Any:
    """Open `req` after a scheme check; raises ValueError for any scheme but http and https (and for text that cannot
    be split into an address). The opener holds the http and https handlers only (see http_only_opener).
    With follow_redirects=False a redirect is not followed (urllib would send every request header, an API key
    included, to the new address): the 3xx answer is raised as urllib.error.HTTPError.
    With use_proxy=False the proxy settings of the environment (HTTP_PROXY, HTTPS_PROXY, no_proxy) are ignored and the
    request goes straight to the address (for a request to this computer that carries a key in a header)."""
    check_scheme(req if isinstance(req, str) else req.full_url)
    return http_only_opener(follow_redirects, use_proxy).open(req, timeout=timeout)  # noqa: S310  # nosec B310


def reason_word(error: BaseException | object) -> str:
    """ONE fixed word for a request that got no HTTP status ("refused", "no_answer" or "error"): what a status line or a
    log shows instead of the name of a Python error class. `error` is an exception, or the `.reason` of a URLError."""
    if isinstance(error, ConnectionRefusedError):
        return "refused"
    if isinstance(error, TimeoutError):
        return "no_answer"
    return "error"


BODY_BAD, BODY_NEEDS_LENGTH, BODY_TOO_BIG, BODY_TOO_SLOW = 400, 411, 413, 408


_READ_PIECE_BYTES = 65536  # one read of a body: a deadline is looked at between pieces


def announced_length(headers: Any, cap: int = FAKE_BODY_MAX_BYTES) -> tuple[int, int]:
    """(length, 0) for a usable Content-Length (a missing one is 0), else (0, status): 400 for text that is not a plain
    count (negative, a sign, non-ASCII digits, a digit string so long that int() would fail), 411 when the body is sent
    in chunks (no length), 413 above `cap`. The length of the text is compared first: Python refuses int() of a digit
    string of more than 4300 characters. Leading zeros are dropped before that comparison ("0000000000000005" is 5, not
    too long). Two Content-Length lines that differ are 400 (a request that two readers would size differently is
    never answered); two that are the same are one."""
    if headers.get("Transfer-Encoding"):
        return 0, BODY_NEEDS_LENGTH
    values = headers.get_all("Content-Length") if hasattr(headers, "get_all") else None
    if values is None:
        one = headers.get("Content-Length")
        values = [] if one is None else [one]
    if len({v.strip() for v in values}) > 1:
        return 0, BODY_BAD
    text = values[0] if values else None
    if text is None or text == "":
        return 0, 0
    if not (text.isascii() and text.isdigit()):
        return 0, BODY_BAD
    text = text.lstrip("0") or "0"
    if len(text) > len(str(cap)) or int(text) > cap:
        return 0, BODY_TOO_BIG
    return int(text), 0


def read_request_body(handler: Any, cap: int = FAKE_BODY_MAX_BYTES) -> tuple[bytes, int]:
    """(body, 0), or (b"", status) when the request must be refused (see announced_length; 408 when the sender stops
    sending: the handler's socket timeout, and when fewer bytes arrive than were announced). At most `cap` bytes are
    ever read. The caller answers with the status; nothing of the body is kept or shown."""
    n, status = announced_length(handler.headers, cap)
    if status or n == 0:
        return b"", status
    deadline = time.monotonic() + FAKE_BODY_DEADLINE_SECONDS  # for the WHOLE body: a socket timeout restarts per byte
    parts: list[bytes] = []
    got = 0
    try:
        while got < n:
            left = deadline - time.monotonic()
            if left <= 0:
                return b"", BODY_TOO_SLOW
            handler.connection.settimeout(min(left, FAKE_SOCKET_TIMEOUT_SECONDS))
            piece: bytes = handler.rfile.read1(min(n - got, _READ_PIECE_BYTES))
            if not piece:  # the sender closed early
                return b"", BODY_TOO_SLOW
            parts.append(piece)
            got += len(piece)
    except OSError:  # TimeoutError is an OSError; a reset too
        return b"", BODY_TOO_SLOW
    return b"".join(parts), 0


class HeadDeadline:
    """Mix-in for a BaseHTTPRequestHandler: the request line and the header lines have ONE total time limit
    (FAKE_HEAD_DEADLINE_SECONDS). The socket timeout of the handler restarts with every received byte, so a sender
    of one byte every few seconds held a handler thread for about 80 seconds. A timer started when the request begins
    shuts the connection down at the deadline (the blocked read then ends); it is cancelled as soon as the headers are
    read, so the body has its own deadline (read_request_body) and a slow answer is never cut. An error answer to a
    sender that has already gone (or was cut off here) is dropped quietly: there is nobody to read it."""

    _head_timer: threading.Timer | None = None

    def _head_too_slow(self) -> None:
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def send_error(self, *args: Any, **kwargs: Any) -> None:
        try:
            parent: Any = super()
            parent.send_error(*args, **kwargs)
        except OSError:  # BrokenPipeError, ConnectionResetError: the sender is gone
            self.close_connection = True

    def handle_one_request(self) -> None:
        timer = threading.Timer(FAKE_HEAD_DEADLINE_SECONDS, self._head_too_slow)
        timer.daemon = True
        self._head_timer = timer
        timer.start()
        try:
            parent: Any = super()
            parent.handle_one_request()
        finally:
            timer.cancel()

    def parse_request(self) -> bool:
        try:
            parent: Any = super()
            return bool(parent.parse_request())
        finally:
            if self._head_timer is not None:
                self._head_timer.cancel()
