"""The service: three listeners, routing, the one response writer, limits and ``serve`` (brief-v3 4.6, 5, 7, 12; portal plan-v6 W-21). The security-critical
core of the work app: strict request parsing, sessions and sign-in dispatch, headers on every response, role dispatch (default deny), the closed
code-to-status map, the decide and export handoffs, and the start sequence. Later owners (the dashboards, performance, send-back) only ADD entries to
``HANDLERS`` and a branch to ``csp_for``; they never change the request pipeline.

Markup comes only from ``ui`` (called as ``ui.render_*``); this module never builds a tag. Every response goes through ``send``."""

from __future__ import annotations

import hmac
import ipaddress
import json
import re
import signal
import socket
import sqlite3
import sys
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import MappingProxyType
from typing import Any
from urllib.parse import parse_qs

from . import access, budget, codes, exporter, inbox, lockfile, model, review_page, routes, secret_store, ui, workqueue
from . import decisions as decisions_mod
from .codes import ConfigError, Refused, SecretError
from .inbox import InboxUnavailable as _InboxUnavailable  # 6b raises it for a missing, unreadable or linked inbox folder (erratum 101a)
from .settings import Settings

HOST_TOKEN, HOST_WORK, HOST_DASH = "127.0.0.1", "127.0.0.11", "127.0.0.12"  # plan-v5 B3.1
PRODUCT_HOSTS = MappingProxyType({"token": HOST_TOKEN, "work": HOST_WORK, "dash": HOST_DASH})
LIMIT_CONN_WORK, LIMIT_CONN_DASH, LIMIT_CONN_TOKEN = 16, 12, 4  # W-12
LIMIT_READ_S = 15
LIMIT_HANDLE_S = 30
LIMIT_SOCKET_S = 10  # reading (request line, headers, body) vs processing; per-receive timeout (spec 11)
LIMIT_REQUEST_LINE = 2048
LIMIT_HEADERS = 40
LIMIT_HEADER_LINE = 4096  # W-10
LIMIT_BODY_WORK = 8192
LIMIT_BODY_TOKEN = 4096
LIMIT_DRAIN = 65536  # bytes read and dropped after a 413 before closing
WORK_LOCK_WAIT_S = (
    5  # how long an approval waits for a running Write (and the other way round); a waiter holds one of the 16 work connections meanwhile
)
STOP_GRACE_S = 5  # how long a stop waits for requests in progress
SPEND_REFRESH_S = 2  # m8: one SpendReading per server, refreshed at most this often


@dataclass(frozen=True)
class Limits:
    """Tests shrink every field."""

    conn_work: int
    conn_dash: int
    conn_token: int
    read_s: float  # from accept until the body is fully read
    handle_s: float  # processing of every route except ``scan``
    scan_s: float | None  # processing of ``scan``; None = ``inbox.scan_deadline_s(s)`` at serve start
    socket_s: float


PRODUCT_LIMITS = Limits(LIMIT_CONN_WORK, LIMIT_CONN_DASH, LIMIT_CONN_TOKEN, LIMIT_READ_S, LIMIT_HANDLE_S, None, LIMIT_SOCKET_S)

# The closed code-to-status map (brief-v3 13). Any code that is not listed here answers 500 ``internal``.
STATUS: Mapping[str, int] = MappingProxyType(
    {
        **dict.fromkeys(("bad_request", "bad_decision"), 400),
        **dict.fromkeys(("unauthorized", "login_failed"), 401),
        **dict.fromkeys(("bad_origin", "csrf_failed", "role_denied", "token_not_allowed"), 403),
        "not_found": 404,
        "method_not_allowed": 405,
        **dict.fromkeys(
            (
                "stale_content",
                "already_decided",
                "reject_only",
                "invalid_reason",
                "not_approvable",
                "state_conflict",
                "stored_data_bad",
                "export_changed",
            ),
            409,
        ),
        "length_required": 411,
        "body_too_large": 413,
        "bad_host": 421,
        "bad_query": 422,
        "too_many_attempts": 429,
        "internal": 500,
        **dict.fromkeys(
            ("not_configured", "settle_failed", "db_busy", "ledger_missing", "budget_halted"), 503
        ),  # budget_halted: page code ``halted``
    }
)
# Codes a handler can meet that DELIBERATELY answer 500 ``internal``: the program or its files are broken, ask the lead.
INTERNAL_OK: frozenset[str] = frozenset(
    {
        "bad_config",
        "local_unset",
        "bad_backend",
        "ledger_inconsistent",
        "prices_missing",
        "owner_sentence_missing",
        "provider_limit_missing",
        "cap_too_small_for_worst_case",
        "budget_total",
        "real_file_refused",
        "fake_on_real_folder",
        "id_collision",  # outside a scan
        "purge_refused",  # no route purges
        "bad_name",  # outside a scan
        "serve_running",  # start-up only (exit 3), never a request
        "port_in_use",  # start-up only (exit 3), never a request
    }
)
# The exporter's result and file codes shown on a 200 result page with the exporter's own texts, never through ``STATUS`` (they are RETURNED).
OUTCOME_CODES: frozenset[str] = frozenset(
    {
        "exported",
        "already_exported",
        "not_approved",
        "not_approvable",
        "approval_mismatch",
        "row_id_conflict",
        "state_conflict",
        "db_busy",
        "db_error",
        "kill_switch",
        "written",
        "sink_locked",
        "sink_error",
    }
)
CSP_JSON = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
# The work-page policy has the style hash of ``ui`` in it (brief-v3 7.2, 10.0 item 6): 6d fills ``{style_hash}`` with ``ui.STYLE_SHA256``.
CSP_WORK_FORMAT = (
    "default-src 'none'; style-src '{style_hash}'; style-src-attr 'none'; form-action 'self'; frame-ancestors 'none'; "
    "base-uri 'none'; require-trusted-types-for 'script'; trusted-types 'none'"
)
SEND_COEP = True  # P0-9 decides; the browser smoke test checks the page still styles and posts
HDR_NO_STORE = "no-store"
_PERMISSIONS = "camera=(), microphone=(), geolocation=(), usb=(), serial=(), hid=(), bluetooth=(), payment=(), clipboard-read=(), display-capture=(), fullscreen=()"
JSON_ROUTES: frozenset[str] = (
    frozenset()
)  # route names that answer JSON and never refresh the idle time (W-7); release 2 adds its API rows here
_KNOWN_OTHER_METHODS = frozenset({"HEAD", "PUT", "DELETE", "TRACE", "OPTIONS", "CONNECT", "PATCH"})
_HEADING = {
    400: "Bad request",
    401: "Sign in needed",
    403: "Not allowed",
    404: "Not found",
    405: "Not allowed",
    409: "Conflict",
    411: "Length needed",
    413: "Too large",
    414: "Address too long",
    421: "Wrong address",
    422: "Not accepted",
    429: "Too many attempts",
    431: "Headers too large",
    500: "Something went wrong",
    501: "Not supported",
    503: "Unavailable",
    505: "Version not supported",
}
_STDLIB_TEXT = {414: "Request line too long", 505: "HTTP version not supported"}
_REASON = {
    200: "OK",
    303: "See Other",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    411: "Length Required",
    413: "Content Too Large",
    414: "URI Too Long",
    421: "Misdirected Request",
    422: "Unprocessable Content",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    500: "Internal Server Error",
    501: "Not Implemented",
    503: "Service Unavailable",
    505: "HTTP Version Not Supported",
}
_TOKEN_CHARS = re.compile(r"[A-Za-z0-9!#$%&'*+.^_`|~-]+")
_TARGET_RE = re.compile(r"/[\x21-\x7e]*")
_CL_RE = re.compile(r"[0-9]{1,5}")
_FORM_CT_RE = re.compile(r"application/x-www-form-urlencoded([ \t]*;[ \t]*charset=utf-8)?", re.IGNORECASE)
_SINGLE_VALUED = (
    "origin",
    "sec-fetch-site",
    "sec-fetch-mode",
    "sec-fetch-dest",
    "content-type",
)  # a repeated X-Request-Id is not refused: only its first value is used, and only in the log
_VERSION_RE = re.compile(r"[0-9]{1,9}")
_PREVIEW_RE = re.compile(r"[0-9a-f]{64}")
_BIND_FAILED = "a listener address is taken or cannot be used" + (
    " (macOS answers only on 127.0.0.1 until the aliases are added, for example: sudo ifconfig lo0 alias 127.0.0.11)"
    if sys.platform == "darwin"
    else ""
)
_OPTIONAL_FIELDS = frozenset({"preview"})  # a Write without the page's token is refused with 409 after the step-up, not 400 (erratum 102)
_CONTENT_CODE_RE = re.compile(r"[0-9a-f]{64}")
_RID_RE = re.compile(r"[A-Za-z0-9_-]{1,32}")
_PAGE = "text/html; charset=utf-8"
_JSON = "application/json; charset=utf-8"


# ---- the seams later owners fill (W-21) --------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Request:
    app: str
    route: routes.Route
    params: Mapping[str, str]
    query: Mapping[str, str]
    form: Mapping[str, str] = field(repr=False)  # a passphrase or a CSRF token can be in here
    headers: Mapping[str, str] = field(repr=False)  # the Cookie header is in here
    session: access.Session | None = field(repr=False)
    settings: Settings
    server: IntakeServer | None = (
        None  # additive: the handlers read the shared stores (sessions, throttle, scanner, spend reading) through it
    )
    raw_query: str = ""


@dataclass(frozen=True)
class Reply:
    status: int
    body: bytes
    content_type: str
    headers: tuple[tuple[str, str], ...] = ()
    code: str | None = None  # additive: the code to put in the log line when the reply is a page that explains a refusal


def csp_for(app: str, route: routes.Route | None) -> str:
    """The ``Content-Security-Policy`` value for this app and route. The one place a policy string is chosen; every response still goes through ``send``."""
    if app == "token":
        return CSP_JSON
    return CSP_WORK_FORMAT.format(
        style_hash="sha256-" + ui.STYLE_SHA256
    )  # dash (no rows yet) and work share the work string until release 2 adds a branch


# ---- responses ------------------------------------------------------------------------------------------------------------------------------
def _check_header(name: str, value: str) -> None:
    for part in (name, value):
        if not isinstance(part, str) or any(c in part for c in ("\r", "\n", "\x00")):
            raise ValueError("header with CR, LF or NUL refused")


def log_line(app: str, route: str | None, status: int, item_id: str | None, request_id: str | None, code: str | None) -> None:
    """One line per request on stderr; every field is checked against its grammar, else ``-``. Never a path, body, header value or cookie."""
    r = route if route in {x.name for x in routes.ROUTE_TABLE} else "-"
    i = item_id if isinstance(item_id, str) and re.fullmatch(routes.ITEM_ID_RE, item_id) else "-"
    c = code if code in codes.CODES else "-"
    rid = request_id if isinstance(request_id, str) and _RID_RE.fullmatch(request_id) else "-"
    a = app if app in routes.APPS else "-"
    sys.stderr.write(f"intake {workqueue.now_utc()} app={a} route={r} status={int(status)} item={i} rid={rid} code={c}\n")
    sys.stderr.flush()


def send(handler: Any, status: int, body: bytes | str, content_type: str, headers: tuple[tuple[str, str], ...] = ()) -> None:
    """THE response writer. A ``str`` body is encoded UTF-8 with ``errors="replace"``; CR, LF and NUL in any header name or value are refused. Adds the
    full header set of brief-v3 7.2 for the listener (so redirects, errors and the stdlib's own error paths carry it too) and logs one line."""
    srv = handler.server
    app = srv.app
    data = body.encode("utf-8", "replace") if isinstance(body, str) else body
    length = len(data)
    if getattr(handler, "method", "") == "HEAD":
        data = b""  # a reply to HEAD carries the headers only
    token_app = app == "token"
    std: list[tuple[str, str]] = [
        ("Content-Type", content_type),
        ("Content-Length", str(length)),
        ("Content-Security-Policy", csp_for(app, getattr(handler, "route", None))),
        ("Referrer-Policy", "no-referrer" if token_app else "same-origin"),
        ("X-Content-Type-Options", "nosniff"),
        ("Cache-Control", HDR_NO_STORE),
        ("Cross-Origin-Resource-Policy", "same-origin"),
        ("Server", "intake"),
        ("Connection", "close"),
    ]
    if not token_app:
        std += [("Cross-Origin-Opener-Policy", "same-origin"), ("Permissions-Policy", _PERMISSIONS), ("X-Frame-Options", "DENY")]
        if SEND_COEP:
            std.append(("Cross-Origin-Embedder-Policy", "require-corp"))
    allh = std + list(headers)
    for k, v in allh:
        _check_header(k, v)
    head = f"HTTP/1.0 {int(status)} {_REASON.get(int(status), 'Status')}\r\n" + "".join(f"{k}: {v}\r\n" for k, v in allh) + "\r\n"
    ctx = getattr(handler, "ctx", {})
    try:
        handler.wfile.write(head.encode("latin-1") + data)
        handler.wfile.flush()
    except OSError:
        pass  # the client went away (or the watchdog shut the socket); nothing to tell it
    finally:
        log_line(app, ctx.get("route"), status, ctx.get("item"), ctx.get("rid"), ctx.get("code"))


def _json_reply(status: int, obj: object, headers: tuple[tuple[str, str], ...] = ()) -> Reply:
    return Reply(status, json.dumps(obj, ensure_ascii=True, sort_keys=True).encode("ascii"), _JSON, headers)


def _text_for(s: Settings, code: str) -> str:
    text = review_page.ERROR_TEXT.get("halted" if code == "budget_halted" else code, review_page.ERROR_TEXT["internal"])
    try:
        return text.format(reason_min_chars=s.review.reason_min_chars, reason_max_chars=s.review.reason_max_chars)
    except (KeyError, IndexError, ValueError):
        return text


def status_and_code(exc: BaseException) -> tuple[int, str]:
    """Map anything a handler can raise to (HTTP status, public code). ``Refused.text`` and exception messages never reach a client."""
    code = "internal"
    if isinstance(exc, access.Throttled):
        code = "too_many_attempts"
    elif isinstance(exc, access.NotConfigured):
        code = "not_configured"
    elif isinstance(exc, access.Denied):
        code = exc.code
    elif isinstance(exc, SecretError):
        code = "not_configured"  # every secrets-file problem code
    elif isinstance(exc, (Refused, ConfigError)):
        code = exc.code
    elif isinstance(exc, sqlite3.OperationalError):
        msg = str(exc).lower()
        code = "db_busy" if "locked" in msg or "busy" in msg else "internal"
    if code not in STATUS:
        code = "internal"
    return STATUS[code], code


# ---- the handler ----------------------------------------------------------------------------------------------------------------------------
# What a handler may raise. Deliberately NOT a bare ``except Exception`` (the broad-catch pin of errata 74 counts those): anything else reaches the
# standard library's ``process_request_thread``, which calls ``IntakeServer.handle_error`` (one fixed log line, the connection closes).
_HANDLER_ERRORS = (Refused, ConfigError, access.Denied, access.NotConfigured, access.Throttled, sqlite3.Error, ArithmeticError, LookupError, TypeError, ValueError, AttributeError, RuntimeError, OSError)  # fmt: skip


class _Fail(Exception):  # noqa: N818 (an internal control-flow carrier, not an error type)
    def __init__(self, code: str, *, status: int | None = None, headers: tuple[tuple[str, str], ...] = (), text: str | None = None) -> None:
        super().__init__(code)
        self.code, self.status, self.headers, self.text = code, status, headers, text


class Handler(BaseHTTPRequestHandler):
    server_version = "intake"
    sys_version = ""
    protocol_version = "HTTP/1.0"

    def setup(self) -> None:
        self.timeout = self.server.limits.socket_s
        super().setup()
        self.ctx: dict[str, Any] = {"route": None, "item": None, "rid": None, "code": None}
        self.route: routes.Route | None = None
        self._declared = 0
        self._body_read = False
        self.method = ""

    def _code_of(self, e: BaseException) -> str:
        """The public code of an error; a ``settle_failed`` from ANY handler also stops the service (money path: it can never be swallowed here)."""
        if isinstance(e, ConfigError) and e.code == "settle_failed":
            self.server.fail_fatal()
        return status_and_code(e)[1]

    def handle(self) -> None:
        self.handle_one_request()

    # every stdlib hook that writes is replaced so nothing bypasses ``send``
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass

    def log_request(self, code: object = "-", size: object = "-") -> None:
        pass

    def log_error(self, format: str, *args: object) -> None:  # noqa: A002
        pass

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        self._respond_error(_Fail("bad_request", status=int(code)), None)

    def handle_one_request(self) -> None:
        self.close_connection = True
        try:
            self._run()
        except _Fail as f:
            self._respond_error(f, self._session_for_error())
        except OSError:
            return  # timeout, reset, or the watchdog's shutdown: no response is possible
        except _HANDLER_ERRORS as e:  # a bug in a handler is a 500 with a fixed text, never a traceback
            self._respond_error(_Fail(self._code_of(e)), self._session_for_error())

    # -- parsing ------------------------------------------------------------------------------------------------------------------------------
    def _readline(self, limit: int) -> bytes:
        return self.rfile.readline(limit + 3)

    def _read_request_line(self) -> tuple[str, str, str] | None:
        line = self._readline(LIMIT_REQUEST_LINE)
        if not line:
            return None
        first_word = line.split(b" ", 1)[0]
        if re.fullmatch(rb"[A-Z]{1,16}", first_word):
            self.method = first_word.decode("ascii")  # known before any refusal, so HEAD gets no body on a 414 either
        if not line.endswith(b"\n"):
            if len(line) >= LIMIT_REQUEST_LINE + 3:
                raise _Fail("bad_request", status=414)
            return None  # the client hung up in the middle of the line
        if not line.endswith(b"\r\n"):
            raise _Fail("bad_request")
        line = line[:-2]
        if len(line) > LIMIT_REQUEST_LINE:
            raise _Fail("bad_request", status=414)
        parts = line.decode("latin-1").split(" ")
        if len(parts) != 3 or not all(parts) or not re.fullmatch(r"[A-Z]{1,16}", parts[0]):
            raise _Fail("bad_request")
        method, target, version = parts
        if not re.fullmatch(r"HTTP/[0-9]\.[0-9]", version):
            raise _Fail("bad_request")
        if version not in ("HTTP/1.0", "HTTP/1.1"):
            raise _Fail("bad_request", status=505)
        if not _TARGET_RE.fullmatch(target) or target.startswith("//"):
            raise _Fail("bad_request")  # absolute form, authority form, "*", "//host", spaces, control characters
        return method, target, version

    def _read_headers(self) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        while True:
            h = self._readline(LIMIT_HEADER_LINE)
            if not h:
                raise OSError("closed")
            if not h.endswith(b"\n"):
                if len(h) >= LIMIT_HEADER_LINE + 3:
                    raise _Fail("bad_request", status=431)
                raise OSError("closed")
            if not h.endswith(b"\r\n"):
                raise _Fail("bad_request")
            h = h[:-2]
            if not h:
                return out
            if len(h) > LIMIT_HEADER_LINE or len(out) >= LIMIT_HEADERS:
                raise _Fail("bad_request", status=431)
            name, sep, value = h.decode("latin-1").partition(":")
            if not sep or not _TOKEN_CHARS.fullmatch(name):
                raise _Fail("bad_request")  # also: a continuation line or a name with a space
            value = value.strip(" \t")
            if any((ord(c) < 32 and c != "\t") or ord(c) == 127 for c in value):
                raise _Fail("bad_request")
            out.append((name.lower(), value))

    def _drain(self) -> None:
        """After an early error on a POST: read and drop at most ``LIMIT_DRAIN`` bytes of the body so closing does not reset the connection (m6)."""
        if self._body_read or self._declared <= 0:
            return
        left = min(self._declared, LIMIT_DRAIN)
        try:
            while left > 0:
                chunk = self.rfile.read(min(left, 8192))
                if not chunk:
                    break
                left -= len(chunk)
        except OSError:
            pass
        self._body_read = True

    # -- the pipeline (brief-v3 7.1) ----------------------------------------------------------------------------------------------------------
    def _session_for_error(self) -> access.Session | None:
        return getattr(self, "_session", None)

    def _run(self) -> None:
        srv: IntakeServer = self.server
        s = srv.settings
        app = srv.app
        first = self._read_request_line()
        if first is None:
            return
        method, target, _version = first
        headers = self._read_headers()
        by: dict[str, list[str]] = {}
        for k, v in headers:
            by.setdefault(k, []).append(v)
        rid = by.get("x-request-id", [""])[0][:32]
        self.ctx["rid"] = rid if _RID_RE.fullmatch(rid or "") else None
        cl = by.get("content-length", [])
        if len(cl) == 1 and _CL_RE.fullmatch(cl[0]):
            self._declared = int(cl[0])
        if srv.fatal.is_set():
            raise _Fail("settle_failed")
        if not access.host_ok(app, by.get("host", []), srv.port, srv.hosts):
            raise _Fail("bad_host")
        if "upgrade" in by or any(len(by.get(h, [])) > 1 for h in _SINGLE_VALUED):
            raise _Fail("bad_request")  # a repeated security header is refused, not read as its first value
        self.method = method
        path, _, raw_query = target.partition("?")
        if method not in ("GET", "POST"):
            if method not in _KNOWN_OTHER_METHODS:
                raise _Fail("method_not_allowed", status=501, text=review_page.ERROR_TEXT["method_not_allowed"])
            allow = [m for m in ("GET", "POST") if isinstance(routes.match(app, m, path), tuple)]
            if not allow:
                raise _Fail("not_found")
            raise _Fail("method_not_allowed", headers=(("Allow", ", ".join(allow)),))
        hit = routes.match(app, method, path)
        if hit is None:
            raise _Fail("not_found")
        if hit == "method":
            other = "POST" if method == "GET" else "GET"
            raise _Fail("method_not_allowed", headers=(("Allow", other),))
        route, params = hit
        self.route = route
        self.ctx["route"] = route.name
        self.ctx["item"] = params.get("id")
        query = self._parse_query(raw_query, route)
        # token / session
        session: access.Session | None = None
        sid: str | None = None
        if route.family == "token":
            try:
                expected = secret_store.get(secret_store.WEBHOOK_SECRET, local=s.local)
            except SecretError:
                raise _Fail("not_configured") from None
            sent = by.get("x-hadavin-token", [])
            if len(sent) != 1 or not access.equal_secret(sent[0], expected):
                raise _Fail("unauthorized")
        else:
            if "x-hadavin-token" in by:
                raise _Fail("token_not_allowed")
            if route.family == "session":
                sid = access.cookie_value("; ".join(by["cookie"]) if "cookie" in by else None, access.COOKIE_SESSION)
                session = srv.sessions.get(sid, touch=False)  # a refused request is not activity: touched below, after every check passed
                self._session = session
                if session is None:
                    if method == "GET":
                        raise _Fail("unauthorized", status=303, headers=(("Location", "/login"),))
                    raise _Fail("unauthorized")
        if method == "POST" and app == "work":
            if not access.origin_ok(by.get("origin", []), by.get("sec-fetch-site", []), srv.port, srv.hosts["work"]):
                raise _Fail("bad_origin")
        if "transfer-encoding" in by:
            raise _Fail("bad_request")
        if len(cl) > 1 or (cl and not _CL_RE.fullmatch(cl[0])):
            raise _Fail("bad_request")
        n = int(cl[0]) if cl else 0
        if method == "GET" and n:
            raise _Fail("bad_request")
        if method == "POST":
            if not cl and app == "work":
                raise _Fail("length_required")
            if n > (LIMIT_BODY_WORK if app == "work" else LIMIT_BODY_TOKEN):
                raise _Fail("body_too_large")
        body = b""
        if n:
            body = self.rfile.read(n)
            if len(body) < n:
                return  # the client hung up before the body was complete
        self._body_read = True
        srv.begin_processing(self.request, scan=route.name == "scan")
        form: dict[str, str] = {}
        if method == "POST" and app == "work":
            form = self._parse_form(route, by.get("content-type", []), body)
            if route.family == "session" and not access.csrf_ok(session, form.get("csrf")):
                raise _Fail("csrf_failed")
        if route.family == "session" and not access.allowed(route, session):
            raise _Fail("role_denied")
        fn = HANDLERS.get(route.name)
        if fn is None:
            raise _Fail("not_found")
        if session is not None and route.name not in JSON_ROUTES:
            srv.sessions.get(sid, touch=True)  # work HTML pages and POSTs that passed Origin, CSRF and role refresh the idle time (W-7)
        req = Request(app, route, MappingProxyType(params), MappingProxyType(query), MappingProxyType(form),
                      MappingProxyType({k: ("; ".join(v) if k == "cookie" else v[0]) for k, v in by.items()}), session, s, srv, raw_query)  # fmt: skip
        try:
            reply = fn(req)
        except _Fail:
            raise
        except _HANDLER_ERRORS as e:
            raise _Fail(self._code_of(e)) from None
        if reply.code is not None:
            self.ctx["code"] = reply.code
        send(self, reply.status, reply.body, reply.content_type, reply.headers)

    def _parse_query(self, raw: str, route: routes.Route) -> dict[str, str]:
        if not raw:
            return {}
        try:
            q = parse_qs(raw, keep_blank_values=True, strict_parsing=True, errors="strict", max_num_fields=len(route.query) + 1)
        except ValueError:
            raise _Fail("bad_query") from None
        if any(k not in route.query or len(v) != 1 for k, v in q.items()):
            raise _Fail("bad_query")
        return {k: v[0] for k, v in q.items()}

    def _parse_form(self, route: routes.Route, ct: list[str], body: bytes) -> dict[str, str]:
        if len(ct) != 1 or not _FORM_CT_RE.fullmatch(ct[0]):
            raise _Fail("bad_request")
        try:
            q = parse_qs(
                body.decode("utf-8", "strict"),
                keep_blank_values=True,
                strict_parsing=True,
                errors="strict",
                max_num_fields=len(route.fields) + 1,
            )
        except ValueError:
            raise _Fail("bad_request") from None
        if set(q) - set(route.fields) or set(route.fields) - set(q) - _OPTIONAL_FIELDS or any(len(v) != 1 for v in q.values()):
            raise _Fail("bad_request")  # an unknown, repeated or missing field (identity comes from the session only)
        return {k: v[0] for k, v in q.items()}

    # -- errors -------------------------------------------------------------------------------------------------------------------------------
    def _respond_error(self, f: _Fail, session: access.Session | None) -> None:
        srv: IntakeServer = self.server
        status, code = (f.status, f.code) if f.status is not None else (STATUS.get(f.code, 500), f.code if f.code in STATUS else "internal")
        self.ctx["code"] = code
        text = f.text or _STDLIB_TEXT.get(status) or _text_for(srv.settings, code)
        send(self, status, *self._error_body(status, code, text, session), f.headers)
        self._drain()

    def _error_body(self, status: int, code: str, text: str, session: access.Session | None) -> tuple[bytes | str, str]:
        if self.server.app == "token":
            return json.dumps({"error": "halted" if code == "budget_halted" else code}, sort_keys=True), _JSON
        if status == 303:
            return b"", _PAGE
        try:
            sv = review_page.session_view(session) if session is not None else None
            return str(ui.render_error(status, _HEADING.get(status, "Error"), text, sv).html), _PAGE
        except _HANDLER_ERRORS:  # the error page itself failed: a fixed plain text, never a traceback
            return text, "text/plain; charset=utf-8"


# ---- handlers --------------------------------------------------------------------------------------------------------------------------------
def _page(status: int, page: Any, headers: tuple[tuple[str, str], ...] = ()) -> Reply:
    return Reply(status, str(page.html).encode("utf-8", "replace"), _PAGE, headers)


def _redirect(location: str, headers: tuple[tuple[str, str], ...] = ()) -> Reply:
    return Reply(303, b"", _PAGE, (("Location", location), *headers))


def _login_page(req: Request, status: int, code: str | None) -> Reply:
    """Every response that shows the sign-in form issues a fresh pre-session (M-A)."""
    pre_id, token = req.server.pre.issue()
    text = None if code is None else _text_for(req.settings, code)
    page = ui.render_login(text, csrf=token)
    h: tuple[tuple[str, str], ...] = (("Set-Cookie", access.set_cookie(access.COOKIE_PRE, pre_id, max_age=access.LIMIT_PRE_SESSION_S)),)
    if status == 429:
        h += (("Retry-After", "1"),)
    return replace(_page(status, page, h), code=code)


def h_login(req: Request) -> Reply:
    sf = [req.headers.get("sec-fetch-mode"), req.headers.get("sec-fetch-dest")]
    if sf != ["navigate", "document"] or req.headers.get("sec-fetch-site") not in ("none", "same-origin"):
        # a fetch, image or script request, or a navigation started by another site (a popup flood would evict the real pre-session): no pre-session
        raise _Fail("bad_origin")
    return _login_page(req, 200, None)


def h_login_post(req: Request) -> Reply:
    srv = req.server
    form = req.form
    try:
        srv.throttle.admit()
    except access.Throttled:
        return _login_page(req, 429, "too_many_attempts")
    guessed_wrong = False
    try:
        if not srv.pre.redeem(access.cookie_value(req.headers.get("cookie"), access.COOKIE_PRE), form["csrf"]):
            return _login_page(req, 403, "csrf_failed")
        try:
            login = access.match_login(req.settings, form["login"], form["passphrase"])
        except access.NotConfigured:
            return _login_page(req, 503, "not_configured")
        if login is None:
            guessed_wrong = True
            return _login_page(req, 401, "login_failed")
        sess = srv.sessions.create(login, replacing=access.cookie_value(req.headers.get("cookie"), access.COOKIE_SESSION))
        return _redirect(
            "/",
            (("Set-Cookie", access.set_cookie(access.COOKIE_SESSION, sess.sid)), ("Set-Cookie", access.clear_cookie(access.COOKIE_PRE))),
        )
    finally:
        srv.throttle.failed() if guessed_wrong else srv.throttle.passed()  # the slot reserved by admit() is always given back


def h_logout(req: Request) -> Reply:
    req.server.sessions.end_all(req.session.login_name)
    return _redirect("/login", (("Set-Cookie", access.clear_cookie(access.COOKIE_SESSION)),))


def _sv(req: Request) -> Any:
    return review_page.session_view(req.session)


def h_home(req: Request) -> Reply:
    try:
        q = ui.parse_list_query(req.raw_query)
    except ui.QueryRefused:
        return _page(422, ui.render_query_refused(_sv(req)))
    view = review_page.queue_view(
        req.settings,
        req.session,
        q,
        req.server.scanner.last_refused(),
        req.server.spend(),
        scan_running=scan_running(req.server),
        refused_total=req.server.shared.refused_total,
    )
    return _page(200, ui.render_list(view, _sv(req)))


def h_item(req: Request) -> Reply:
    view = review_page.invoice_view(
        req.settings, req.session, req.params["id"], spend=req.server.spend(), scan_running=scan_running(req.server)
    )
    return _page(200, ui.render_item(view, _sv(req)))


def _item_page(req: Request, status: int, *, refusal_code: str | None = None, outcome_code: str | None = None) -> Reply:
    view = review_page.invoice_view(
        req.settings,
        req.session,
        req.params["id"],
        refusal_code=refusal_code,
        outcome_code=outcome_code,
        spend=req.server.spend(),
        scan_running=scan_running(req.server),
    )
    return _page(status, ui.render_item(view, _sv(req)))


def h_decide(req: Request) -> Reply:
    f = req.form
    if f["decision"] not in ("approve", "reject"):
        raise _Fail("bad_decision")
    if not _VERSION_RE.fullmatch(f["version"]) or not _CONTENT_CODE_RE.fullmatch(f["content_code"]):
        raise _Fail("bad_request")
    lock = req.server.shared.work_lock
    if not lock.acquire(timeout=WORK_LOCK_WAIT_S):  # a Write is running (it holds the lock from the list comparison to the last byte)
        raise _Fail("db_busy")
    try:
        decisions_mod.decide(
            req.settings, req.params["id"], f["decision"], req.session.login_name, f["reason"], f["content_code"], int(f["version"])
        )
    except Refused as e:
        status, code = status_and_code(e)
        if status != 409:
            raise
        return replace(_item_page(req, 409, refusal_code=code), code=code)
    finally:
        lock.release()
    return _item_page(req, 200, outcome_code="approved" if f["decision"] == "approve" else "rejected")


def h_export(req: Request) -> Reply:
    return _page(
        200,
        ui.render_export(
            review_page.export_view(req.settings, req.session, spend=req.server.spend(), scan_running=scan_running(req.server)), _sv(req)
        ),
    )


def h_export_run(req: Request) -> Reply:
    srv = req.server
    shown = req.form.get("preview")  # the page's own hidden field; judged AFTER the passphrase, below

    def page(status: int, **kw: Any) -> Reply:
        hdr = (("Retry-After", "1"),) if status == 429 else ()
        return replace(
            _page(
                status,
                ui.render_export(
                    review_page.export_view(req.settings, req.session, spend=srv.spend(), scan_running=scan_running(srv), **kw), _sv(req)
                ),
                hdr,
            ),
            code=kw.get("refusal_code"),
        )

    try:
        srv.throttle.admit()
    except access.Throttled:
        return page(429, refusal_code="too_many_attempts")
    guessed_wrong = False
    try:
        try:
            ok = access.check_step_up(req.settings, req.session, req.form["passphrase"])
        except access.NotConfigured:
            return page(503, refusal_code="not_configured")
        if not ok:
            guessed_wrong = True
            return page(401, refusal_code="login_failed")
    finally:
        srv.throttle.failed() if guessed_wrong else srv.throttle.passed()
    lock = srv.shared.work_lock
    if not lock.acquire(timeout=WORK_LOCK_WAIT_S):  # an approval is running: the person presses Write again
        return page(503, refusal_code="db_busy")  # page() puts the code in the log line
    refused = False
    run = None
    try:
        try:
            current = review_page.export_token(req.settings)
        except (Refused, sqlite3.Error, OSError):
            # the list could not be read (a busy or damaged database): nothing is written. A coding error is NOT caught here: it is a 500
            current = None
        if current is None or shown is None or not _PREVIEW_RE.fullmatch(shown) or not hmac.compare_digest(current, shown):
            refused = True  # missing, malformed, different or unreadable: nothing is written (errata 102, 103c); the page is built below, outside the lock
        else:
            run = exporter.export_pending(req.settings)  # still under the lock: no approval can slip in between the comparison and the read
    finally:
        lock.release()
    if refused:
        return page(409, refusal_code="export_changed")
    return page(200, run=run)


def h_healthz(req: Request) -> Reply:
    return _json_reply(200, {"ok": True})


def h_scan(req: Request) -> Reply:
    srv = req.server
    try:
        result = srv.scanner.try_scan()
    except ConfigError as e:
        if e.code == "settle_failed":
            srv.fail_fatal()
            return _json_reply(503, {"error": "settle_failed"})
        # the inbox folder is missing, unreadable or a link (errata 93, 101a): a fixed 503, no path or text
        if isinstance(e, _InboxUnavailable):
            return _json_reply(503, {"error": "not_configured"})
        raise  # every other ConfigError (a damaged queue is bad_config too) is an internal error, 500
    except Refused as e:
        if e.code in ("budget_halted", "ledger_missing"):
            return _json_reply(503, {"error": "halted" if e.code == "budget_halted" else "ledger_missing"})
        raise
    if result is None:
        return _json_reply(200, {"busy": True})
    srv.shared.refused_total = result.refused_total
    return _json_reply(200, result.as_json())


# route name -> handler; read-only, built once from one dict literal. Later owners add entries; ``overview`` has none until P2a (404).
HANDLERS: Mapping[str, Callable[[Request], Reply]] = MappingProxyType(
    {
        "login": h_login,
        "login_post": h_login_post,
        "home": h_home,
        "item": h_item,
        "decide": h_decide,
        "export": h_export,
        "export_run": h_export_run,
        "logout": h_logout,
        "healthz": h_healthz,
        "scan": h_scan,
    }
)


# ---- the servers ----------------------------------------------------------------------------------------------------------------------------
class _Shared:
    """State shared by the three listeners of one ``serve`` (instance state, not module state)."""

    def __init__(self, s: Settings, scanner: Any, limits: Limits, hosts: Mapping[str, str]) -> None:
        self.settings, self.scanner, self.limits, self.hosts = s, scanner, limits, hosts
        self.sessions, self.pre, self.throttle = access.SessionStore(), access.PreSessions(), access.Throttle()
        self.fatal = threading.Event()
        self.stop = threading.Event()
        self.work_lock = (
            threading.Lock()
        )  # a decision and a Write never run at the same time: the Write writes exactly the list it compared
        self.servers: list[IntakeServer] = []
        self._spend_lock = threading.Lock()
        self._spend_at = -1e9
        self._spend: review_page.SpendReading | None = None
        self.refused_total: int | None = (
            None  # all refusals of the last scan (the list shows the first MAX_REFUSED); passed to the list page
        )


class IntakeServer(ThreadingHTTPServer):
    """One per listener; attributes: app, settings, sessions, pre, throttle, scanner, fatal (an event shared by the three), limits, gate."""

    daemon_threads = True
    allow_reuse_address = sys.platform != "win32"
    request_queue_size = 16

    def __init__(self, address: tuple[str, int], shared: _Shared, app: str) -> None:
        self.app, self.shared = app, shared
        self.settings, self.sessions, self.pre, self.throttle = shared.settings, shared.sessions, shared.pre, shared.throttle
        self.scanner, self.fatal, self.limits, self.hosts = shared.scanner, shared.fatal, shared.limits, shared.hosts
        n = {"work": self.limits.conn_work, "dash": self.limits.conn_dash, "token": self.limits.conn_token}[app]
        self.gate = threading.BoundedSemaphore(n)
        self._watch: dict[int, list] = {}  # id(socket) -> [socket, deadline, shut]
        self._watch_lock = threading.Lock()
        self._wd_stop = threading.Event()
        self._active = 0  # handler threads running now: ``Running.stop`` waits for them before the serve lock is given back
        self._active_lock = threading.Lock()
        super().__init__(address, Handler)
        self.port = self.server_address[1]
        threading.Thread(target=self._watchdog, daemon=True, name=f"watchdog-{app}").start()

    def server_bind(self) -> None:
        if sys.platform == "win32":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        elif self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()
        self.server_name, self.server_port = self.server_address[0], self.server_address[1]  # never socket.getfqdn

    # -- deadlines: the watchdog only shuts a socket down; the handler thread closes it ----------------------------------------------------------
    def _watchdog(self) -> None:
        while not self._wd_stop.wait(0.05):
            now = time.monotonic()
            with self._watch_lock:
                due = [e for e in self._watch.values() if not e[2] and now > e[1]]
                for e in due:
                    e[2] = True
            for e in due:
                try:
                    e[0].shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    def watch_start(self, sock: Any, seconds: float) -> None:
        with self._watch_lock:
            self._watch[id(sock)] = [sock, time.monotonic() + seconds, False]

    def begin_processing(self, sock: Any, *, scan: bool) -> None:
        """Reading is over: the processing deadline starts now (a slow upload never earns the scan bound)."""
        lim = self.limits
        secs = (lim.scan_s if lim.scan_s is not None else lim.handle_s) if scan else lim.handle_s
        with self._watch_lock:
            e = self._watch.get(id(sock))
            if e is not None and not e[2]:
                e[1] = time.monotonic() + secs

    def watch_end(self, sock: Any) -> None:
        with self._watch_lock:
            self._watch.pop(id(sock), None)

    def process_request(self, request, client_address) -> None:  # noqa: ANN001
        if not self.gate.acquire(blocking=False):
            self.shutdown_request(request)  # full: close at once
            return
        self.watch_start(request, self.limits.read_s)
        with self._active_lock:
            self._active += 1
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.watch_end(request)
            self.gate.release()
            with self._active_lock:
                self._active -= 1
            raise

    def process_request_thread(self, request, client_address) -> None:  # noqa: ANN001
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.watch_end(request)
            self.gate.release()
            with self._active_lock:
                self._active -= 1

    def wait_idle(self, grace_s: float) -> bool:
        """True when no handler thread is running (waits at most ``grace_s``)."""
        end = time.monotonic() + grace_s
        while time.monotonic() < end:
            with self._active_lock:
                if self._active == 0:
                    return True
            time.sleep(0.02)
        with self._active_lock:
            return self._active == 0

    def handle_error(self, request, client_address) -> None:  # noqa: ANN001
        log_line(self.app, None, 500, None, None, "internal")  # one fixed line, no traceback

    def server_close(self) -> None:
        self._wd_stop.set()
        super().server_close()

    # -- shared helpers for handlers --------------------------------------------------------------------------------------------------------------
    def fail_fatal(self) -> None:
        """settle_failed: every later request on any listener answers 503; the shutdown starts from a NEW thread (never from a handler thread)."""
        self.fatal.set()
        threading.Thread(target=self.shared.stop.set, daemon=True).start()

    def spend(self) -> review_page.SpendReading | None:
        sh = self.shared
        with sh._spend_lock:
            if time.monotonic() - sh._spend_at >= SPEND_REFRESH_S:
                sh._spend = review_page.SpendReading(
                    budget.total_settled_readonly(self.settings), budget.halt_state_readonly(self.settings)
                )
                sh._spend_at = time.monotonic()
            return sh._spend


def scan_running(server: IntakeServer) -> bool:
    return bool(server.scanner.running())


# ---- start, stop, serve ----------------------------------------------------------------------------------------------------------------------
class Running:
    def __init__(self, shared: _Shared, servers: dict[str, IntakeServer], lock: Any) -> None:
        self.shared, self.servers, self._lock = shared, servers, lock
        self.threads = [threading.Thread(target=sv.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True) for sv in servers.values()]

    @property
    def ports(self) -> dict[str, int]:
        return {a: sv.port for a, sv in self.servers.items()}

    def begin(self) -> None:
        for t in self.threads:
            t.start()

    def stop(self, grace_s: float = STOP_GRACE_S) -> None:
        """Stop accepting, let the requests in progress finish (at most ``grace_s``: a reply such as the 503 of ``settle_failed`` is written), close the
        sockets, then give the serve lock back."""
        for sv, th in zip(self.servers.values(), self.threads, strict=True):
            if th.is_alive():  # shutdown() waits for serve_forever: only a server whose thread started may be asked
                sv.shutdown()
        end = time.monotonic() + grace_s
        for sv in self.servers.values():
            sv.wait_idle(max(0.0, end - time.monotonic()))
        for sv in self.servers.values():
            sv.server_close()
        for th in self.threads:
            if th.is_alive():
                th.join(timeout=5)
        lock, self._lock = (
            self._lock,
            None,
        )  # cleared first: a second press that lands here and retries stop() must not release a closed handle
        if lock is not None:
            lockfile.release(lock)


def _secret_line(s: Settings, name: str) -> str:
    st = secret_store.status(name, s.local)
    return f"key {name}: ok" if st == "ok" else f"key {name}: fail {st}"


def start(s: Settings, *, hosts: Mapping[str, str] = PRODUCT_HOSTS, limits: Limits = PRODUCT_LIMITS) -> Running:
    """The start sequence of brief-v3 12.1 (steps 1b to 10) without waiting: returns the running listeners. Errors: ``ConfigError`` (exit 3) or ``Refused``
    (exit 2). The serve lock is released again on any failure."""
    if s.service.name_regex != "^" + routes.STEM_RE + "$":
        raise ConfigError("bad_config", "item id pattern does not match the configured name rule")
    for name, host in hosts.items():
        try:
            # the listeners are IPv4 sockets: an IPv6 address would only fail later, as a bind error
            loopback = ipaddress.IPv4Address(host).is_loopback
        except ValueError:
            loopback = False
        if not loopback:
            # a listener is never reachable from outside
            raise ConfigError("bad_config", f"the {name} listener must be an IPv4 loopback address (127.x.x.x), not {host}")
    log_level = s_log_level()  # INTAKE_LOG is read once, before anything is bound (a bad value is exit 3)
    for sub in (s.intake_home / "inbox", s.intake_home / "out", s.run_dir):
        sub.mkdir(parents=True, exist_ok=True)
    try:
        lock = lockfile.acquire(s.intake_home / "serve.lock")
    except lockfile.LockHeld:
        raise ConfigError("serve_running", "another intake serve is running") from None
    servers: dict[str, IntakeServer] = {}
    run: Running | None = None
    try:
        if budget.files_state(s) != "ok":
            raise ConfigError("ledger_missing", "run intake init first")
        workqueue.connect(s).close()
        recovered = workqueue.recover_received(s, serve_lock_held=lambda: True)
        guarded = model.build_guarded(s)
        if guarded.deferred is not None:
            raise Refused(guarded.deferred, "the spend guard is not ready")
        lim = limits if limits.scan_s is not None else replace(limits, scan_s=float(inbox.scan_deadline_s(s)))
        shared = _Shared(s, inbox.Scanner(s, guarded), lim, hosts)
        port = s.service.port
        try:
            for app in ("token", "work", "dash"):
                servers[app] = IntakeServer((hosts[app], port), shared, app)
        except OSError:
            raise ConfigError("port_in_use", _BIND_FAILED) from None
        shared.servers = list(servers.values())
        run = Running(shared, servers, lock)
        p = run.ports
        for line in (
            "config: ok",
            f"queue: ok (recovered {len(recovered)})",
            _secret_line(s, secret_store.WEBHOOK_SECRET),
            _secret_line(s, secret_store.APPROVER_PASSPHRASE),
            f"serving: token http://{hosts['token']}:{p['token']}/ work http://{hosts['work']}:{p['work']}/ dashboards http://{hosts['dash']}:{p['dash']}/",
            f"backend: {s.backend}",
            f"log: {log_level}",
        ):
            # flushed: a redirected stdout is block-buffered. Inside the guard: a closed pipe must not leave the lock held
            print(line, flush=True)
        run.begin()
    except BaseException:  # anything, a second Ctrl+C included: close what was opened and give the lock back
        if run is not None:
            run.stop(grace_s=0.0)
        else:
            for sv in servers.values():
                sv.server_close()
            lockfile.release(lock)
        raise
    return run


def s_log_level() -> str:
    from . import settings as settings_mod

    return settings_mod.read_log_level()


def serve(s: Settings, *, hosts: Mapping[str, str] = PRODUCT_HOSTS, limits: Limits = PRODUCT_LIMITS) -> int:
    """W-13. Only tests and the attack harness pass ``hosts=`` or ``limits=``. Returns the exit code (0 normal stop, 3 after settle_failed).

    The stop signals are installed BEFORE the start lines are printed, so a signal right after "serving:" is already a normal stop. The FIRST press (Ctrl+C,
    SIGTERM, Ctrl+Break) only asks for a stop: a start that is stuck goes on until it finishes. A SECOND press raises KeyboardInterrupt in the main thread: a
    stuck start is abandoned (start() stops what it opened and gives the lock back; exit 3), a slow stop is cut short (grace 0). Stopping on a signal
    (or Ctrl+C) equals crash recovery for work in progress: requests get ``STOP_GRACE_S`` seconds, then the sockets close; a scan or export that was cut
    off leaves received items and open reservations that the NEXT start repairs (errata 101b). ``serve`` called from a thread that is not the main thread
    installs no signal handlers and cannot be stopped from outside: use ``start`` and ``Running.stop`` there."""
    flag = _StopFlag()
    restore = _stop_on_signals(flag)
    try:
        try:
            run = start(s, hosts=hosts, limits=limits)
        except KeyboardInterrupt:  # a second press during a stuck start: start() has closed what it opened and given the lock back
            print("interrupted during start", flush=True)
            return 3
        try:
            while not (run.shared.stop.wait(0.25) or flag.requested):
                pass
        except KeyboardInterrupt:
            pass
        finally:
            try:
                print(
                    "stopping: requests in progress get a few seconds; a scan or export cut off is repaired at the next start", flush=True
                )
                run.stop()
            except KeyboardInterrupt:
                # the second press, wherever it lands (the message, the stop): stop at once; later presses are ignored
                run.stop(grace_s=0.0)
    finally:
        for signum, old in restore:
            signal.signal(signum, old)
    return 3 if run.shared.fatal.is_set() else 0


class _StopFlag:
    """Set by the signal handler. A plain attribute and nothing else: no lock, no Event (``Event.set`` takes a lock the interrupted code may hold)."""

    requested = False
    presses = 0


def _stop_on_signals(flag: _StopFlag) -> list:
    """A process stop (SIGTERM; on Windows also Ctrl+Break) and Ctrl+C set ``flag``; ``serve`` then stops normally (exit 0). Only the main thread may
    install handlers; anywhere else nothing is installed. Returns what to put back."""
    if threading.current_thread() is not threading.main_thread():
        return []
    wanted = [signal.SIGTERM, signal.SIGINT] + ([signal.SIGBREAK] if sys.platform == "win32" else [])
    saved = []

    def on_signal(_signum, _frame) -> None:
        flag.presses += 1
        flag.requested = True
        if flag.presses == 2:
            raise KeyboardInterrupt  # the second press: stop waiting for a stuck start or a slow stop. Later presses only count

    for signum in wanted:
        saved.append((signum, signal.signal(signum, on_signal)))
    return saved
