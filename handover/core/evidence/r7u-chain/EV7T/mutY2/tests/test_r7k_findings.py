"""Round 7K: tests for the mutants of the r7g mutant pass (pass 9) that survived the big set or the selector set, and
the sweeps of their siblings. Made-up data only, loopback only; keys are built from parts; no real model, no real mail.
Header table: finding, mutant, what the test pins, why it matters, result on a copy of r7j (FAILS = new behaviour,
fails before the fix; PIN = pure pin of code that was already right, passes by design).

  finding | mutant   | what is pinned                                                     | on r7j
  ------- | -------- | ------------------------------------------------------------------ | ------
  k1      | M9-32    | a key text is in no exception text, repr, args, attribute, chain    | FAILS for the chain
          | K01-K03  | (cause and context, also a suppressed one), traceback or log line,  | (the raised error kept the
          |          | on every failure path of the live call and of the key file reader   | first error as its context)
          |          | why: the secret is never printed or kept                            |
  k2      | M9-40    | the ledger lock not obtained within tries x wait: reserve, settle   | PIN
          | K04-K06  | and totals refuse, no row is written, no network call is made       |
          |          | why: money, no spend without the ledger                             |
  k3      | M9-33    | the key never reaches a proxy named in the environment (a child     | PIN
          |          | process that starts with the proxy variables set)                   |
  k4      | M9-34    | the reply cap: exactly the cap is read, one byte more is refused    | PIN
          |          | (a reader that hands the bytes in blocks of 4096)                   |
  k5      | M9-64    | a line over the cap is REFUSED, never split; exactly the cap is ok  | PIN
  k6      | M9-65    | a byte-order mark in a key or password file is accepted and dropped  | PIN
  k7      | M9-67    | an error class of a module that only STARTS with the package name   | PIN
          |          | is not ours                                                         |
  k8      | M9-61    | EQUIVALENT (argument in R7K-RESULTS.md): NaN, Infinity, -Infinity,  | PIN
          |          | 1e999 give the one fixed refusal text, at any depth                 |
  k9      | sibling  | a TLS handshake that drips one byte at a time ends inside the total | PIN
          | of M9-08 | budget of the send                                                  |
  k10     | N05, N06 | the cap of running name look-ups is 8: the 8th runs, the 9th is     | PIN
          |          | refused at once with no thread (lead order, EV7H)                   |
  k11     | review M1| `localhost` answers 127.0.0.1 only; when one address times out and  | FAILS
          | N07-N09  | a later one is refused the time-out is raised; all refused: the last| (::1 invented)
  k12     | review m2| a non-OSError (RuntimeError, KeyboardInterrupt) on address 1 is     | PIN
          | N4       | raised at once: the 2nd address is never tried; the socket is closed|
  k13     | review m1| a look-up thread that fails to start, or fails after it began,      | FAILS
          | N10, N11 | gives its place back ONCE (count never below 0, cap stays 8)         | (count -1)
  k14     | review m3| 127.1, 0x7f.1, 2130706433, a form with a leading zero are answered by the system     | FAILS
          | N12      | without a look-up thread, and never refused by the cap              | (127.1 refused)
  k16     | M9-69    | the Start? question of scripts/run_real_check.py: only "y" (after   | PIN
          | N22-N26  | strip and lower case) starts; any other answer, EOF or a failed     | (pass 10)
          |          | read stops at once with EXIT_STOPPED and no call to any fake        |
  k17     | M9-16    | the default port of the mail settings: 587 for starttls, 465 for   | PIN
          | N29, N30 | ssl; a port that is set always wins                                 | (pass 10)
  k15     | review M3| a request that ended in a driver error counts: summary key          | FAILS
          | N13-N15  | driver_errors, exit code 3 and ONE line with the same count         | (exit 0)
"""

from __future__ import annotations

import fcntl
import http.client
import io
import json
import logging
import socket
import ssl
import threading
import time
import traceback
import types
import urllib.error
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest
from support import HOST, REPO, child_env, free_port, run_python, start_serving, stop_serving, text_file, wait_until
from test_live_claude import FAKE_KEY, Model, settings
from test_r7f_findings import _provider

from demo_only.fake_model_server import make_model_server
from lead_desk import constants, crm_hubspot, errcode, netconnect
from lead_desk import live_claude as lc
from lead_desk.adapters import CrmError
from lead_desk.constants import LIVE_LEDGER_LOCK_TRIES, LIVE_REPLY_MAX_BYTES, SECRET_FILE_MAX_BYTES
from lead_desk.contract import SendUnreachable
from lead_desk.crm_hubspot import HubspotCrm, HubspotSettings
from lead_desk.live_claude import LiveBadReply, LiveCapReached, LiveQualifier, LiveRateLimited, LiveTransport
from lead_desk.netconnect import connect_bounded, hung_lookups, resolve_bounded
from lead_desk.regfile import FileRefused, iter_regular_lines, load_json_file, read_secret_line
from lead_desk.smtp_provider import ProviderSettings

OK_REPLY = {
    "content": [{"type": "text", "text": "hot"}],
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 3, "output_tokens": 1},
}
PLAIN = "a@example.test"

_NET1, _NET2 = (f"10.0.0.{n}" for n in (1, 2))  # made-up addresses, built from parts (the hygiene scan)


@pytest.fixture
def model() -> Iterator[Model]:
    srv, state = make_model_server(port=0, mode="ok", key=FAKE_KEY)
    th = start_serving(srv)
    try:
        yield Model(state, f"http://{HOST}:{srv.server_address[1]}")
    finally:
        state.stop.set()
        stop_serving(srv, th)


def _live(tmp_path: Path, url: str, **over: Any) -> LiveQualifier:
    return LiveQualifier(settings(tmp_path, Model(cast(Any, None), url), **over))  # no model state is needed here


def _chain(exc: BaseException | None) -> Iterator[BaseException]:
    """Every exception reachable from `exc` by cause or context, a suppressed context too (a traceback hides it, a
    program reading `__context__` does not)."""
    seen: set[int] = set()
    todo = [exc]
    while todo:
        e = todo.pop()
        if e is None or id(e) in seen:
            continue
        seen.add(id(e))
        yield e
        todo += [e.__cause__, e.__context__]


def _texts(exc: BaseException) -> list[str]:
    out: list[str] = []
    for e in _chain(exc):
        out.append("".join(traceback.format_exception(type(e), e, None)))  # the text a log line prints, no source lines
        out += [str(e), repr(e), repr(e.args), repr(getattr(e, "__dict__", {}))]
        for attr in ("object", "doc", "filename", "filename2", "reason", "url", "msg", "headers", "hdrs"):
            out.append(repr(getattr(e, attr, None)))
    return out


def _assert_no(secret: str, exc: BaseException) -> None:
    for t in _texts(exc):
        assert secret not in t, "the secret is reachable from the exception"
        assert secret.encode() not in t.encode("utf-8", "replace")


# ---- k1: M9-32 (the key is in no exception text, chain, traceback or log line) ----


class _Echo(BaseHTTPRequestHandler):
    """Answers every POST with a configured status, header and body; `{KEY}` in them is replaced by the key it was
    sent, so a program that copied any part of the answer into an error text would carry the key."""

    status = 200
    header: tuple[str, str] | None = None
    body = b"{}"

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("content-length") or 0))
        key = (self.headers.get("x-api-key") or "").encode()
        self.send_response(self.status)
        if self.header:
            self.send_header(self.header[0], self.header[1].replace("{KEY}", key.decode()))
        body = self.body.replace(b"{KEY}", key)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_a: Any) -> None:
        pass


@contextmanager
def _echo_server(status: int, body: bytes, header: tuple[str, str] | None = None) -> Iterator[str]:
    handler = type("H", (_Echo,), {"status": status, "body": body, "header": header})
    srv = ThreadingHTTPServer((HOST, 0), handler)
    th = start_serving(srv)
    try:
        yield f"http://{HOST}:{srv.server_address[1]}"
    finally:
        stop_serving(srv, th)


ECHO_CASES: dict[str, tuple[int, bytes, tuple[str, str] | None, type[Exception]]] = {
    "500 json whose message is the key": (
        500,
        b'{"type":"error","error":{"type":"api_error","message":"{KEY}"}}',
        None,
        LiveTransport,
    ),
    "500 plain text is the key": (500, b"{KEY}", ("x-request-id", "{KEY}"), LiveTransport),
    "401 echoes the key": (401, b'{"error":"{KEY}"}', ("www-authenticate", "Bearer {KEY}"), LiveTransport),
    "429 retry-after is the key": (429, b"{KEY}", ("retry-after", "{KEY}"), LiveRateLimited),
    "200 not json, holds the key": (200, b"not json {KEY}", None, LiveBadReply),
    "200 json list holding the key": (200, b'["{KEY}"]', None, LiveBadReply),
    "200 not utf-8, key before the bad byte": (200, b"{KEY} \xff\xfe", None, LiveBadReply),
    "200 too long, starts with the key": (200, b"{KEY}" + b" " * (LIVE_REPLY_MAX_BYTES + 10), None, LiveBadReply),
    "200 json object, label is the key": (
        200,
        b'{"content":[{"type":"text","text":"{KEY}"}],"stop_reason":"end_turn"}',
        None,
        LiveBadReply,
    ),
}


@pytest.mark.parametrize("name", sorted(ECHO_CASES))
def test_k1_a_server_that_echoes_the_key_never_puts_it_in_an_error(
    tmp_path: Path, name: str, caplog: pytest.LogCaptureFixture
) -> None:
    status, body, header, exc_class = ECHO_CASES[name]
    caplog.set_level(logging.DEBUG)
    with _echo_server(status, body, header) as url:
        q = _live(tmp_path, url, timeout_seconds=3.0)
        with pytest.raises(exc_class) as info:
            q.qualify("L1", PLAIN)
    _assert_no(FAKE_KEY, info.value)
    assert FAKE_KEY not in caplog.text


def test_k1_an_unreachable_server_never_puts_the_key_in_an_error(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    q = _live(tmp_path, f"http://{HOST}:{free_port()}", timeout_seconds=2.0)  # nothing listens: the connect is refused
    with pytest.raises(LiveTransport, match="could not be reached") as info:
        q.qualify("L1", PLAIN)
    _assert_no(FAKE_KEY, info.value)
    assert FAKE_KEY not in caplog.text


def test_k1_a_call_that_is_not_answered_in_time_never_puts_the_key_in_an_error(
    tmp_path: Path, model: Model, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    model.state.mode = "timeout"
    q = LiveQualifier(settings(tmp_path, model, timeout_seconds=0.5))
    with pytest.raises(LiveTransport, match="in time") as info:
        q.qualify("L1", PLAIN)
    _assert_no(FAKE_KEY, info.value)
    assert FAKE_KEY not in caplog.text


class _Resp:
    """What the opener returns for a call: a context manager whose reads answer with `chunks` or fail."""

    status = 200

    def __init__(self, chunks: list[bytes], fail: BaseException | None = None) -> None:
        self.chunks, self.fail = list(chunks), fail

    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *_a: object) -> None:
        return None

    def read1(self, _n: int = -1) -> bytes:
        if self.fail:
            raise self.fail
        return self.chunks.pop(0) if self.chunks else b""


class _Opener:
    def __init__(self, act: Any) -> None:
        self.act = act

    def open(self, *_a: Any, **_k: Any) -> Any:
        return self.act()


def _inject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, act: Any) -> LiveQualifier:
    monkeypatch.setattr(lc, "_OPENER", _Opener(act))
    return _live(tmp_path, f"http://{HOST}:1", timeout_seconds=3.0)


def _http_error(code: int, body: bytes) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://example.test/", code, FAKE_KEY, http.client.HTTPMessage(), io.BytesIO(body))


def _raiser(e: Any) -> Any:
    """A call that raises `e`, or what `e()` returns when it is a function (a new error for every call)."""

    def go() -> Any:
        raise e() if callable(e) else e

    return go


INJECTED: dict[str, Any] = {
    "urlerror": lambda: _raiser(urllib.error.URLError(FAKE_KEY)),
    "oserror": lambda: _raiser(OSError(FAKE_KEY)),
    "timeout": lambda: _raiser(TimeoutError(FAKE_KEY)),
    "valueerror": lambda: _raiser(ValueError("bad header " + repr(FAKE_KEY))),
    "httpexception": lambda: _raiser(http.client.HTTPException(FAKE_KEY)),
    "http 500 error holding the key": lambda: _raiser(lambda: _http_error(500, FAKE_KEY.encode())),
    "http 429 error holding the key": lambda: _raiser(lambda: _http_error(429, FAKE_KEY.encode())),
    "read fails with the key": lambda: lambda: _Resp([], fail=OSError(FAKE_KEY)),
    "reply holds the key, not json": lambda: lambda: _Resp([FAKE_KEY.encode() + b" tail"]),
    "reply is not utf-8": lambda: lambda: _Resp([FAKE_KEY.encode() + b"\xff"]),
}


@pytest.mark.parametrize("name", sorted(INJECTED))
def test_k1_what_an_error_inside_the_call_holds_is_not_reachable_from_the_error_raised(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, name: str
) -> None:
    """FAILS on r7j: the raised error kept the first error (the one that held the key text) as its context."""
    caplog.set_level(logging.DEBUG)
    q = _inject(tmp_path, monkeypatch, INJECTED[name]())
    with pytest.raises(lc.LiveError) as info:
        q.qualify("L1", PLAIN)
    _assert_no(FAKE_KEY, info.value)
    assert FAKE_KEY not in caplog.text


@pytest.mark.parametrize("name", sorted(INJECTED))
def test_k1_the_crm_key_is_not_reachable_from_the_error_either(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, name: str
) -> None:
    """Sibling: the HubSpot adapter sends its key the same way. FAILS on r7j for the errors that carry the key text."""
    caplog.set_level(logging.DEBUG)
    key_file = tmp_path / "hub-key.txt"
    key_file.write_text(FAKE_KEY + "\n", encoding="utf-8")
    crm = HubspotCrm(
        HubspotSettings(
            key_file=key_file,
            max_calls=50,
            base_url=f"http://{HOST}:1",
            timeout_seconds=2.0,
            allow_any_base_url=True,
        )
    )
    monkeypatch.setattr(crm_hubspot, "_OPENER", _Opener(INJECTED[name]()))
    with pytest.raises(CrmError) as info:
        crm.put("L1", {"name": "Ada", "email": "ada@example.test", "company": "X", "source": "form", "ai_label": "hot"})
    _assert_no(FAKE_KEY, info.value)
    assert FAKE_KEY not in caplog.text


# the key file reader: every refusal is one fixed text with no earlier error behind it
BAD_SECRET_FILES = {
    "not utf-8": b"made-up-key-\xff\xfe\xfd-more\n",
    "two lines": b"made-up-key-one\nmade-up-key-two\n",
    "holds a tab": b"made-up\tkey-text-here\n",
    "too short": b"short\n",
}


@pytest.mark.parametrize("shape", sorted(BAD_SECRET_FILES))
def test_k1_a_refused_key_file_leaves_no_path_and_no_bytes_behind(tmp_path: Path, shape: str) -> None:
    """FAILS on r7j for `not utf-8` (the decode error, which holds the bytes of the file, stayed as context)."""
    f = tmp_path / "secret-file-name.txt"
    f.write_bytes(BAD_SECRET_FILES[shape])
    with pytest.raises(FileRefused) as info:
        read_secret_line(f, "key", "key")
    assert info.value.__context__ is None and info.value.__cause__ is None
    _assert_no("made-up-key", info.value)
    _assert_no("secret-file-name", info.value)


def test_k1_a_missing_key_file_leaves_no_path_behind(tmp_path: Path) -> None:
    with pytest.raises(FileRefused) as info:
        read_secret_line(tmp_path / "no-such-key-file.txt", "key", "key")
    assert info.value.__context__ is None
    _assert_no("no-such-key-file", info.value)


def test_k1_the_live_call_with_a_bad_key_file_holds_no_bytes_of_the_file(tmp_path: Path, model: Model) -> None:
    f = tmp_path / "bad-key.txt"
    f.write_bytes(BAD_SECRET_FILES["not utf-8"])
    q = LiveQualifier(settings(tmp_path, model, key_file=f))
    with pytest.raises(LiveTransport) as info:
        q.qualify("L1", PLAIN)
    _assert_no("made-up-key", info.value)
    assert info.value.__cause__ is None and model.state.calls == 0


# ---- k2: M9-40 (the ledger lock is not obtained: no spend) ----


@pytest.fixture
def short_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lc, "LIVE_LEDGER_LOCK_TRIES", 4)
    monkeypatch.setattr(lc, "LIVE_LEDGER_LOCK_WAIT", 0.05)


@contextmanager
def _hold(path: Path) -> Iterator[None]:
    """Hold the lock from another open handle (flock conflicts between handles, also inside one process)."""
    with open(path, "a+b") as h:
        fcntl.flock(h.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def test_k2_a_lock_held_longer_than_tries_times_wait_stops_the_call_before_any_spend(
    tmp_path: Path, model: Model, short_lock: None
) -> None:
    s = settings(tmp_path, model, timeout_seconds=5.0)
    with _hold(Path(f"{s.ledger_path}.lock")):
        q = LiveQualifier(s)
        t0 = time.monotonic()
        with pytest.raises(LiveCapReached, match="locked by another process"):
            q.qualify("L1", PLAIN)
        waited = time.monotonic() - t0
        assert 0.18 <= waited < 3.0  # it tried 4 times and waited 0.05 s after each: about 0.2 s, never the 5 s limit
        assert model.state.calls == 0 and q.calls == 0  # no network call
        assert not s.ledger_path.exists() or s.ledger_path.read_text(encoding="utf-8") == ""  # no reserve row
    assert LiveQualifier(s).qualify("L2", PLAIN) in {"hot", "warm", "cold"}  # free again: it works
    rows = [json.loads(x) for x in s.ledger_path.read_text(encoding="utf-8").splitlines()]
    assert [r["op"] for r in rows] == ["reserve", "settle"]  # one call, one pair of rows


def test_k2_the_same_refusal_on_settle_totals_and_reserve_and_nothing_is_written(
    tmp_path: Path, model: Model, short_lock: None
) -> None:
    s = settings(tmp_path, model)
    ledger = lc.SpendLedger(s.ledger_path)
    rid = ledger.reserve(s, Decimal("0.01"))
    before = s.ledger_path.read_bytes()
    with _hold(Path(f"{s.ledger_path}.lock")):
        with pytest.raises(LiveCapReached, match="locked by another process"):
            ledger.settle(rid, Decimal("0.005"))
        with pytest.raises(LiveCapReached, match="locked by another process"):
            ledger.totals("run-a")
        with pytest.raises(LiveCapReached, match="locked by another process"):
            ledger.reserve(s, Decimal("0.01"))
        assert s.ledger_path.read_bytes() == before  # no row was added by any of the three


def test_k2_the_file_lock_refuses_holds_nothing_and_the_lock_is_free_after(tmp_path: Path, short_lock: None) -> None:
    path = tmp_path / "x.lock"
    lock = lc._FileLock(path)
    with _hold(path):
        with pytest.raises(LiveCapReached):
            lock.__enter__()
        assert lock._f is None  # nothing is held
    with lc._FileLock(path):  # and the lock is free now
        pass


def test_k2_the_ledger_tries_and_wait_are_the_documented_numbers() -> None:
    assert LIVE_LEDGER_LOCK_TRIES * lc.LIVE_LEDGER_LOCK_WAIT == pytest.approx(5.0)


# ---- k3: M9-33 (the key never goes to a proxy named in the environment) ----

PROBE = """
import sys, types, urllib.request
from lead_desk import adapters, live_claude as lc
if sys.argv[3] == "live":
    q = lc.LiveQualifier.__new__(lc.LiveQualifier)
    q.s = types.SimpleNamespace(base_url=sys.argv[1], api_version="2023-06-01", timeout_seconds=3.0)
    call = lambda: q._post_once(b"{}", sys.argv[2], 3.0)
else:
    req = urllib.request.Request(sys.argv[1] + "/x", headers={"Authorization": "Bearer " + sys.argv[2]})
    call = lambda: adapters._OPENER.open(req, timeout=3.0).read()
try:
    call()
    print("OK")
except Exception as e:
    print(type(e).__name__)
"""


class _Listener:
    def __init__(self, answer: bytes) -> None:
        self.srv = socket.socket()
        self.srv.bind((HOST, 0))
        self.srv.listen(4)
        self.srv.settimeout(0.2)
        self.port = self.srv.getsockname()[1]
        self.data: list[bytes] = []
        self.answer = answer
        self.stop = threading.Event()
        self.th = threading.Thread(target=self._run, daemon=True)
        self.th.start()

    def _run(self) -> None:
        while not self.stop.is_set():
            try:
                c, _ = self.srv.accept()
            except OSError:
                continue
            c.settimeout(1.0)
            buf = b""
            try:
                while b"\r\n\r\n" not in buf:
                    chunk = c.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                self.data.append(buf)
                c.sendall(self.answer)
            except OSError:
                self.data.append(buf)
            finally:
                c.close()

    def close(self) -> None:
        self.stop.set()
        self.th.join(2)
        self.srv.close()


@pytest.mark.parametrize("opener", ["live", "adapters"])
def test_k3_the_key_is_not_sent_to_a_proxy_named_in_the_environment(opener: str) -> None:
    """The opener is built when the module is imported, so the proxy variables must be set when the program starts:
    a child process. Without `ProxyHandler({})` the request goes to the proxy, with the key in its header. The
    second opener is the one the HubSpot adapter and the plain CRM adapter send their key through."""
    ok = b"HTTP/1.1 200 OK\r\ncontent-length: 2\r\ncontent-type: application/json\r\n\r\n{}"
    target, proxy = _Listener(ok), _Listener(b"HTTP/1.1 502 Bad Gateway\r\ncontent-length: 0\r\n\r\n")
    try:
        env = {k: v for k, v in child_env().items() if k.lower() not in {"no_proxy", "http_proxy", "all_proxy"}}
        for name in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy"):
            env[name] = f"http://{HOST}:{proxy.port}"
        done = run_python([text_file(PROBE), f"http://{HOST}:{target.port}", FAKE_KEY, opener], env, cwd=REPO)
        assert done.stdout.strip() == "OK", done.stderr[-300:]
        assert target.data and FAKE_KEY.encode() in target.data[0]  # it went straight to the target's host
        assert proxy.data == [], "something reached the proxy"
    finally:
        target.close()
        proxy.close()


# ---- k4: M9-34 (the reply cap: exactly the cap is read, one byte more is refused) ----


def _blocks(body: bytes) -> list[bytes]:
    return [body[i : i + 4096] for i in range(0, len(body), 4096)]


def _padded(n: int) -> bytes:
    raw = json.dumps(OK_REPLY).encode()
    return raw + b" " * (n - len(raw))  # trailing white space is still one JSON object


@pytest.mark.parametrize("size", [LIVE_REPLY_MAX_BYTES - 1, LIVE_REPLY_MAX_BYTES])
def test_k4_a_reply_of_at_most_the_cap_is_read_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, size: int
) -> None:
    q = _inject(tmp_path, monkeypatch, lambda: _Resp(_blocks(_padded(size))))
    assert q.qualify("L1", PLAIN) == "hot"


def test_k4_a_reply_one_byte_over_the_cap_is_refused_not_cut(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A reader that stops at exactly the cap would cut this reply back to a valid one and accept it."""
    body = _padded(LIVE_REPLY_MAX_BYTES + 1)
    assert len(_blocks(body)) == 17 and len(_blocks(body)[-1]) == 1
    q = _inject(tmp_path, monkeypatch, lambda: _Resp(_blocks(body)))
    with pytest.raises(LiveBadReply, match="too long"):
        q.qualify("L1", PLAIN)


def test_k4_the_same_on_a_real_connection(tmp_path: Path) -> None:
    (tmp_path / "e0").mkdir()
    (tmp_path / "e1").mkdir()
    with _echo_server(200, _padded(LIVE_REPLY_MAX_BYTES)) as url:
        assert _live(tmp_path / "e0", url, timeout_seconds=5.0).qualify("L1", PLAIN) == "hot"
    with _echo_server(200, _padded(LIVE_REPLY_MAX_BYTES + 1)) as url:
        with pytest.raises(LiveBadReply, match="too long"):
            _live(tmp_path / "e1", url, timeout_seconds=5.0).qualify("L1", PLAIN)


# ---- k5: M9-64 (a line over the cap is refused, not split) ----


def test_k5_a_line_of_exactly_the_cap_is_read_and_one_more_byte_is_refused(tmp_path: Path) -> None:
    cap = 16
    exact = tmp_path / "exact.txt"
    exact.write_bytes(b"x" * (cap - 1) + b"\n" + b"y" * cap)  # a line of 16 bytes with its line feed, then 16 without
    assert list(iter_regular_lines(exact, 1000, cap)) == ["x" * (cap - 1) + "\n", "y" * cap]
    over = tmp_path / "over.txt"
    over.write_bytes(b"x" * cap + b"\n")  # 17 bytes with the line feed
    seen: list[str] = []
    with pytest.raises(FileRefused, match="too big"):
        for ln in iter_regular_lines(over, 1000, cap):
            seen.append(ln)
    assert seen == []  # not one piece of the long line was handed out
    over_end = tmp_path / "over-end.txt"
    over_end.write_bytes(b"a\n" + b"z" * (cap + 1))  # the long line has no line feed at the end of the file
    with pytest.raises(FileRefused):
        list(iter_regular_lines(over_end, 1000, cap))


def test_k5_the_whole_file_and_the_row_count_are_refused_one_past_the_limit_and_read_at_it(tmp_path: Path) -> None:
    f = tmp_path / "rows.txt"
    f.write_bytes(b"1234567\n" * 2)  # 16 bytes, two rows
    assert len(list(iter_regular_lines(f, 16, 8))) == 2  # exactly max_bytes: read
    with pytest.raises(FileRefused, match="too big"):
        list(iter_regular_lines(f, 15, 8))  # one byte over
    assert len(list(iter_regular_lines(f, 16, 8, max_rows=2))) == 2  # exactly max_rows: read
    with pytest.raises(FileRefused, match="too big"):
        list(iter_regular_lines(f, 16, 8, max_rows=1))  # one row over


# ---- k6: M9-65 (a byte-order mark in a key or password file) ----


@pytest.mark.parametrize("spaced", [False, True])
@pytest.mark.parametrize("tail", [b"\n", b"\r\n", b""])
def test_k6_a_utf8_byte_order_mark_is_accepted_and_dropped(tmp_path: Path, spaced: bool, tail: bytes) -> None:
    f = tmp_path / "bom.txt"
    f.write_bytes(b"\xef\xbb\xbf" + FAKE_KEY.encode() + tail)
    assert read_secret_line(f, "key", "key", spaced=spaced) == FAKE_KEY


def test_k6_a_bom_alone_a_second_bom_and_utf16_are_still_refused(tmp_path: Path) -> None:
    for name, raw in (
        ("only", b"\xef\xbb\xbf\n"),
        ("twice", b"\xef\xbb\xbf\xef\xbb\xbf" + FAKE_KEY.encode()),
        ("inside", FAKE_KEY.encode() + b"\xef\xbb\xbf"),
        ("utf16", b"\xff\xfe" + FAKE_KEY.encode("utf-16-le")),
    ):
        f = tmp_path / f"{name}.txt"
        f.write_bytes(raw)
        with pytest.raises(FileRefused):
            read_secret_line(f, "key", "key")


def test_k6_the_docs_say_what_the_code_does() -> None:
    assert "byte-order mark is accepted" in (read_secret_line.__doc__ or "")
    assert SECRET_FILE_MAX_BYTES == 4096


# ---- k7: M9-67 (an error class of a module whose name only starts with the package name) ----


def _cls(name: str, module: str, base: type = Exception) -> type[BaseException]:
    return type(name, (base,), {"__module__": module})


def test_k7_only_a_class_of_this_package_gives_its_name() -> None:
    pkg = errcode.PACKAGE
    assert errcode.error_code(_cls("Mine", pkg)()) == "Mine"
    assert errcode.error_code(_cls("Mine", pkg + ".sub.mod")()) == "Mine"
    for module in (pkg + "_other", pkg + "x.mod", pkg + "2", pkg[:-1], "x." + pkg):
        assert errcode.error_code(_cls("Foreign", module)()) == "error", module
        assert errcode.error_code(_cls("Foreign", module, ValueError)()) == "error", module  # a subclass is not data
    assert errcode.error_code(lc.LiveTransport("x")) == "LiveTransport"
    assert errcode.error_code(ValueError("x")) == "data" and errcode.error_code(OSError("x")) == "error"


# ---- k8: M9-61 (NaN and Infinity give the one refusal text, at any depth) ----

NON_FINITE = ("NaN", "Infinity", "-Infinity", "[NaN]", '{"a":[1,{"b":-Infinity}]}', "1e999", "[1e999]", '{"a":-1e999}')


@pytest.mark.parametrize("text", NON_FINITE)
def test_k8_a_number_that_is_not_finite_is_refused_with_the_one_fixed_text(tmp_path: Path, text: str) -> None:
    f = tmp_path / "n.json"
    f.write_text(text, encoding="utf-8")
    with pytest.raises(FileRefused) as info:
        load_json_file(f)
    assert str(info.value) == "the file is not JSON that can be read"


def test_k8_finite_numbers_still_read(tmp_path: Path) -> None:
    f = tmp_path / "n.json"
    f.write_text('{"a":[1,2.5,-3e2]}', encoding="utf-8")
    assert load_json_file(f) == {"a": [1, 2.5, -300.0]}


# ---- k9: sibling of M9-08 (a handshake that drips one byte at a time ends inside the send budget) ----


def _dripper(c: socket.socket, stop: threading.Event) -> None:
    record = b"\x16\x03\x03\x00\x40" + b"\x02" * 64  # the start of a handshake record, never finished
    try:
        for b in record * 400:
            if stop.is_set():
                return
            c.sendall(bytes([b]))
            time.sleep(0.05)
    except OSError:
        return


def test_k9_a_tls_handshake_dripped_byte_by_byte_ends_inside_the_budget(tmp_path: Path) -> None:
    """The server answers the TLS handshake with one byte every 0.05 s for ever. Python counts the socket time-out for
    the handshake as a whole, so the send must end near its 1 s budget, not when the server stops."""
    srv = socket.socket()
    srv.bind((HOST, 0))
    srv.listen(2)
    srv.settimeout(0.2)
    stop = threading.Event()
    held: list[socket.socket] = []

    def accept_and_drip() -> None:
        while not stop.is_set():
            try:
                c, _ = srv.accept()
            except OSError:
                continue
            held.append(c)
            threading.Thread(target=_dripper, args=(c, stop), daemon=True).start()

    th = threading.Thread(target=accept_and_drip, daemon=True)
    th.start()
    try:
        box = _provider(
            tmp_path, srv.getsockname()[1], ssl.create_default_context(), security="ssl", timeout_seconds=1.0
        )
        t0 = time.monotonic()
        with pytest.raises(SendUnreachable):
            box.send("RUN1-L-001", "lead@example.test", "Hi", "Hi", 30.0)
        assert time.monotonic() - t0 < 2.5
        assert box.sent == 0
    finally:
        stop.set()
        th.join(2)
        for c in held:
            c.close()
        srv.close()


# ---- k10: N05, N06 (the cap of running name look-ups is exactly 8: not 7, not 9) ----


def test_k10_the_cap_of_running_look_ups_is_eight_and_the_ninth_is_refused_without_a_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kills N05 (8 -> 9: a ninth thread starts) and N06 (8 -> 7: the eighth is refused). The value is the one in
    docs/limits.md. The look-up blocks until released, each caller gives up after 0.05 s, so the threads stay."""
    assert constants.LOOKUP_HUNG_MAX == 8 and netconnect.LOOKUP_HUNG_MAX == 8
    wait_until(lambda: hung_lookups() == 0, what="look-ups of earlier tests ended")
    release = threading.Event()
    started: list[str] = []

    def blocking(host: str, *_a: Any, **_k: Any) -> list[Any]:
        started.append(host)
        release.wait(20)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (HOST, 9))]

    monkeypatch.setattr(
        netconnect,
        "socket",
        types.SimpleNamespace(getaddrinfo=blocking, SOCK_STREAM=socket.SOCK_STREAM, AF_INET=socket.AF_INET),
    )
    try:
        for i in range(8):  # eight are allowed: each waits its 0.05 s, gives up, and leaves its thread running
            with pytest.raises(TimeoutError):
                resolve_bounded(f"name{i}.example.test", 9, 0.05)
        wait_until(lambda: len(started) == 8, what="eight look-up threads running")
        assert hung_lookups() == 8
        t0 = time.monotonic()
        with pytest.raises(TimeoutError):
            resolve_bounded("name9.example.test", 9, 5.0)  # the ninth: refused at once, not after 5 s
        assert time.monotonic() - t0 < 1.0
        assert len(started) == 8 and hung_lookups() == 8  # no ninth thread, nothing counted for it
    finally:
        release.set()
        wait_until(lambda: hung_lookups() == 0, what="stuck look-ups ended")


# ---- k11: review M1 (localhost is IPv4 only; the time-out wins over a later refusal) ----


class _FakeSock:
    """A socket stand-in: `outcomes` is consumed one per socket made; an Exception instance is raised on connect."""

    def __init__(self, outcomes: list[Any], log: list[str]) -> None:
        self.outcomes, self.log = outcomes, log
        self.closed = False

    def settimeout(self, _t: float) -> None:
        return None

    def connect(self, address: Any) -> None:
        self.log.append(address[0])
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome

    def close(self) -> None:
        self.closed = True


def _fake_net(
    monkeypatch: pytest.MonkeyPatch, addresses: list[str], outcomes: list[Any]
) -> tuple[list[str], list[Any]]:
    log: list[str] = []
    made: list[Any] = []

    def make(*_a: Any) -> _FakeSock:
        sock = _FakeSock(outcomes, log)
        made.append(sock)
        return sock

    def lookup(_host: str, port: int, *_a: Any, **_k: Any) -> list[Any]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, port)) for a in addresses]

    monkeypatch.setattr(
        netconnect,
        "socket",
        types.SimpleNamespace(getaddrinfo=lookup, SOCK_STREAM=socket.SOCK_STREAM, AF_INET=socket.AF_INET, socket=make),
    )
    return log, made


def test_k11_localhost_has_one_address_127_0_0_1(monkeypatch: pytest.MonkeyPatch) -> None:
    """FAILS on r7j (it also answered ::1). Kills N07 (the ::1 answer back) and N20 (the name compared with case: it
    would need a look-up thread, which the cap of 0 refuses)."""
    wait_until(lambda: hung_lookups() == 0, what="look-ups of earlier tests ended")
    monkeypatch.setattr(netconnect, "LOOKUP_HUNG_MAX", 0, raising=False)
    found = resolve_bounded("LocalHost", 7, 1.0)
    assert [(a[0], a[4]) for a in found] == [(socket.AF_INET, ("127.0.0.1", 7))]


def test_k11_a_refused_localhost_ends_with_the_refusal_after_one_try() -> None:
    port = free_port()  # nothing listens here
    with pytest.raises(ConnectionRefusedError):
        connect_bounded("localhost", port, 2.0)


@pytest.mark.parametrize(
    ("outcomes", "expected"),
    [
        ([TimeoutError("first"), ConnectionRefusedError("second")], TimeoutError),  # the time-out first, then refused
        ([ConnectionRefusedError("first"), TimeoutError("second")], TimeoutError),
        ([ConnectionRefusedError("first"), ConnectionResetError("second")], ConnectionResetError),  # no time-out
    ],
)
def test_k11_a_time_out_wins_over_a_later_refusal_and_without_one_the_last_error_is_raised(
    monkeypatch: pytest.MonkeyPatch, outcomes: list[Any], expected: type[OSError]
) -> None:
    """Kills N08 (`last` raised even when an address timed out) and N09 (the FIRST error raised)."""
    log, made = _fake_net(monkeypatch, [_NET1, _NET2], list(outcomes))
    with pytest.raises(OSError) as e:
        connect_bounded("two.example.test", 9, 5.0)
    assert type(e.value) is expected and len(log) == 2 and all(m.closed for m in made)


# ---- k12: review m2 (kills N4: the guard that a non-OSError is raised at once) ----


@pytest.mark.parametrize("first", [RuntimeError("boom"), KeyboardInterrupt()])
def test_k12_an_error_that_is_not_an_oserror_is_raised_and_the_second_address_is_never_tried(
    monkeypatch: pytest.MonkeyPatch, first: BaseException
) -> None:
    log, made = _fake_net(monkeypatch, [_NET1, _NET2], [first, None])  # the 2nd would connect
    with pytest.raises(type(first)):
        connect_bounded("two.example.test", 9, 5.0)
    assert log == [_NET1] and len(made) == 1 and made[0].closed


# ---- k13: review m1 (the look-up place goes back once) ----


class _StartsThenFails(threading.Thread):
    """Starts for real, runs to its end, and THEN start() raises (a failure after the thread began)."""

    def start(self) -> None:
        super().start()
        self.join(5)
        raise RuntimeError("after start")


class _FailsToStart(threading.Thread):
    def start(self) -> None:
        raise RuntimeError("no thread")


@pytest.mark.parametrize("thread_class", [_StartsThenFails, _FailsToStart])
def test_k13_the_place_goes_back_once_whatever_happens_when_the_thread_starts(
    monkeypatch: pytest.MonkeyPatch, thread_class: type[threading.Thread]
) -> None:
    """FAILS on r7j for _StartsThenFails (the count went to -1). Kills N10 (no release in the except) and N11 (the
    release without the once-only flag)."""
    wait_until(lambda: hung_lookups() == 0, what="look-ups of earlier tests ended")
    monkeypatch.setattr(
        netconnect, "threading", types.SimpleNamespace(Thread=thread_class, Event=threading.Event, Lock=threading.Lock)
    )
    monkeypatch.setattr(
        netconnect,
        "socket",
        types.SimpleNamespace(
            getaddrinfo=lambda *_a, **_k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (HOST, 9))],
            SOCK_STREAM=socket.SOCK_STREAM,
        ),
    )
    for _ in range(constants.LOOKUP_HUNG_MAX + 3):  # more tries than places: a leak or a double release shows
        with pytest.raises(RuntimeError):
            resolve_bounded("name.example.test", 9, 1.0)
        assert hung_lookups() == 0


# ---- k14: review m3 (digit addresses in every form the system accepts) ----


@pytest.mark.parametrize(
    ("literal", "address"),
    [
        ("127.1", "127.0.0.1"),
        ("0x7f.1", "127.0.0.1"),
        ("2130706433", "127.0.0.1"),
        (f"0{17}.0.0.{1}", f"{15}.0.0.{1}"),  # a leading 0 is OCTAL for the system: its answer is used as it is
        ("127.0.0.1", "127.0.0.1"),
    ],
)
def test_k14_every_digit_form_of_an_address_is_answered_without_a_thread_and_never_refused_by_the_cap(
    monkeypatch: pytest.MonkeyPatch, literal: str, address: str
) -> None:
    """FAILS on r7j for the four short forms (they went to a look-up thread and were refused at a full cap). Kills
    N12 (the numeric-only flag dropped: the look-up thread is used)."""
    wait_until(lambda: hung_lookups() == 0, what="look-ups of earlier tests ended")
    monkeypatch.setattr(netconnect, "LOOKUP_HUNG_MAX", 0, raising=False)  # every real look-up is refused at once
    before = sum(1 for t in threading.enumerate() if t.name == "name-lookup")
    found = resolve_bounded(literal, 9, 1.0)
    assert [(a[0], a[4]) for a in found] == [(socket.AF_INET, (address, 9))]
    expected = socket.getaddrinfo(literal, 9, type=socket.SOCK_STREAM, flags=socket.AI_NUMERICHOST)
    assert [a[4] for a in found] == [a[4] for a in expected]  # the system's own answer
    assert sum(1 for t in threading.enumerate() if t.name == "name-lookup") == before
    with pytest.raises(TimeoutError):  # CONTROL: a real name is refused at this cap
        resolve_bounded("name.example.test", 9, 1.0)


def test_k14_the_system_is_asked_for_a_digit_address_with_the_numeric_only_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The flag is what makes the question unable to reach a name server (it cannot hang). Kills N12b (flags=0)."""
    seen: list[int] = []
    real = socket.getaddrinfo

    def spy(host: str, port: int, *a: Any, **k: Any) -> list[Any]:
        seen.append(k.get("flags", 0))
        return real(host, port, *a, **k)

    monkeypatch.setattr(netconnect, "_getaddrinfo", spy)
    resolve_bounded("127.1", 9, 1.0)
    with pytest.raises(OSError):
        resolve_bounded("", 9, 1.0)
    assert seen and all(f & socket.AI_NUMERICHOST for f in seen), seen


_ODD_NAMES = ["", "a\x00b", ".".join("12345"), ".".join(("999", "1", "1", "1")), "１２７.0.0.1", "fe80::1%lo"]


@pytest.mark.parametrize("name", _ODD_NAMES)
def test_k14_a_name_that_is_not_a_digit_address_still_gets_the_one_fixed_refusal_or_the_normal_look_up(
    name: str,
) -> None:
    try:
        resolve_bounded(name, 9, 2.0)
    except OSError as e:  # a refusal text without the name; a time-out is also an OSError
        assert name not in str(e) or name == ""
        assert str(e) in (netconnect.LOOKUP_REFUSED_TEXT, netconnect.LOOKUP_TEXT)


# ---- k15: review M3 (a driver error counts: exit 3, one line, the same count) ----


def _fake_pool_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """Runs the workers in this process (the real run uses a spawned pool, which cannot see a patched function)."""
    from load_tools import load_driver

    class Pool:
        def __init__(self, _workers: int, initializer: Any, initargs: tuple[Any, ...]) -> None:
            self.init = (initializer, initargs)

        def __enter__(self) -> Pool:
            self.init[0](*self.init[1])
            return self

        def __exit__(self, *_a: Any) -> None:
            return None

        def map(self, fn: Any, jobs: list[Any], chunksize: int = 1) -> None:
            for job in jobs:
                fn(job)

    class _Counter:
        """A process-pool Value in this process: `.value` and `.get_lock()`, as the real one has."""

        def __init__(self, value: int) -> None:
            self.value = value
            self._lock = threading.Lock()

        def get_lock(self) -> threading.Lock:
            return self._lock

    # the pool initializer stores its shared flags in module globals; restore them when the test ends, or the next
    # test that calls the driver in this process finds this test's fakes there
    for name in ("_STOP", "_ANSWERED", "_ERRORS", "_STOP_LIMIT"):
        monkeypatch.setattr(load_driver, name, getattr(load_driver, name))
    ctx = types.SimpleNamespace(Event=threading.Event, Value=lambda _t, v: _Counter(v), Pool=Pool)
    monkeypatch.setattr(load_driver.multiprocessing, "get_context", lambda _name: ctx)
    monkeypatch.setattr(load_driver, "START_LEAD_SECONDS", 0.0)


def _run_main_with_sender(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str], fails: Any, total: int
) -> tuple[int, dict[str, Any], str, list[dict[str, Any]]]:
    from load_tools import load_driver

    _fake_pool_context(monkeypatch)

    def sender(_url: str, item: dict[str, Any]) -> dict[str, Any]:
        if fails(item["request_id"]):
            raise RuntimeError("the sender broke")
        line = load_driver._driver_error_line(item, RuntimeError("x"))
        line.update(final_status=202, accepted=True, gave_up=None, attempts=[{"code": 202}], attempt_count=1)
        return line

    monkeypatch.setattr(load_driver, "send_with_retries", sender)
    srv = socket.socket()
    srv.bind((HOST, 0))
    srv.listen(8)
    try:
        log = tmp_path / "l.jsonl"
        rc = load_driver.main(
            ["--base-url", f"http://{HOST}:{srv.getsockname()[1]}", "--scenario", f"burst:{total}", "--log", str(log)]
        )
    finally:
        srv.close()
    cap = capsys.readouterr()
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
    return rc, json.loads(cap.out.strip().splitlines()[-1]), cap.err, lines


@pytest.mark.parametrize(("total", "bad"), [(4, 4), (6, 2), (5, 1)])
def test_k15_requests_that_ended_in_a_driver_error_end_the_run_with_exit_3_one_line_and_the_same_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    total: int,
    bad: int,
) -> None:
    """FAILS on r7j (exit 0 and no line: a request the driver could not finish passed). Kills N13 (the count left out
    of the exit decision), N14 (left out of the line's number) and N15 (the summary key missing)."""
    seen = {"n": 0}
    guard = threading.Lock()

    def fails(_request_id: str) -> bool:  # the first `bad` requests to reach the sender fail
        with guard:
            seen["n"] += 1
            return seen["n"] <= bad

    rc, summary, err, lines = _run_main_with_sender(monkeypatch, tmp_path, capsys, fails, total)
    errors = sum(1 for d in lines if d["gave_up"] == "driver_error")
    assert errors == bad and len(lines) == total
    assert summary["driver_errors"] == bad and summary["given_up"] == 0 and summary["stopped"] == 0
    assert rc == 3
    assert err.count("\n") == 1 and err.startswith(f"ERROR: {bad} of {total} requests were not accepted")
    assert f"{bad} because the driver itself failed" in err


def test_k15_no_driver_error_means_exit_0_and_no_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc, summary, err, _lines = _run_main_with_sender(monkeypatch, tmp_path, capsys, lambda _r: False, 3)
    assert rc == 0 and err == "" and summary["driver_errors"] == 0


@pytest.mark.parametrize(
    ("given_up", "stopped", "errors", "count"),
    [(0, 0, 3, 3), (1, 0, 2, 3), (0, 2, 1, 3), (2, 1, 1, 4), (0, 2, 0, 2), (1, 1, 0, 2)],
)
def test_k15_the_count_in_the_line_is_the_count_of_all_three_kinds(
    capsys: pytest.CaptureFixture[str], given_up: int, stopped: int, errors: int, count: int
) -> None:
    from load_tools import load_driver

    summary = {"given_up": given_up, "stopped": stopped, "driver_errors": errors, "intended": 9}
    assert load_driver.exit_code_and_line(summary) == 3
    err = capsys.readouterr().err
    assert err.count("\n") == 1 and f"{count} of 9 requests" in err


def test_k15_driver_error_count_counts_only_driver_errors() -> None:
    from load_tools import load_driver

    lines = [{"gave_up": "driver_error"}, {"gave_up": "deadline"}, {"gave_up": "stopped"}, {"gave_up": None}]
    assert load_driver.driver_error_count(lines) == 1 and load_driver.driver_error_count([]) == 0


@pytest.mark.parametrize(("given_up", "lines_missing"), [(0, True), (2, True), (2, False), (0, False)])
def test_k15_a_run_prints_at_most_one_line_on_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    given_up: int,
    lines_missing: bool,
) -> None:
    """Review nit n2: the ERROR line (exit 3) and the WARNING (exit 0, lines missing) never both appear."""
    from load_tools import load_driver

    summary = {
        "unreachable": False,
        "intended": 7,
        "logged": 5 if lines_missing else 7,
        "final_status": {},
        "given_up": given_up,
        "stopped": 0,
        "driver_errors": 0,
    }
    monkeypatch.setattr(load_driver, "run", lambda *_a, **_k: summary)
    rc = load_driver.main(
        ["--base-url", f"http://{HOST}:9", "--scenario", "burst:7", "--log", str(tmp_path / "l.jsonl")]
    )
    err = capsys.readouterr().err
    assert rc == (3 if given_up else 0)
    if given_up:
        assert err.count("\n") == 1 and err.startswith("ERROR: ")
    elif lines_missing:
        assert err == "WARNING: 7 requests intended, 5 logged\n"
    else:
        assert err == ""


# ---- k16: M9-69 (the Start? question: only "y" starts) ----


class _Started(Exception):
    """Raised by the stand-in for `make_plan`, the first thing the script does after the question was answered yes."""


@pytest.fixture
def real_check(monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    import run_real_check as rrc

    made: list[Any] = []
    real_fakes = rrc.DryFakes

    def recording(*a: Any, **k: Any) -> Any:
        fakes = real_fakes(*a, **k)
        made.append(fakes)
        return fakes

    def stop_here(*_a: Any, **_k: Any) -> None:
        raise _Started

    monkeypatch.setattr(rrc, "DryFakes", recording)
    monkeypatch.setattr(rrc, "make_plan", stop_here)
    return types.SimpleNamespace(rrc=rrc, made=made)


def _no_call_was_made(fakes: Any) -> None:
    assert fakes.state.calls == [] and fakes.smtp.commands == [] and fakes.smtp.messages == []
    assert all(im.logins == [] for im in fakes.imaps)
    assert not Path(fakes.env["DESK_DB_PATH"]).exists()  # no desk was started: no book, no outbox, no ledger


def _answer(monkeypatch: pytest.MonkeyPatch, reply: Any) -> list[str]:
    asked: list[str] = []

    def fake_input(prompt: str = "") -> str:
        asked.append(prompt)
        if isinstance(reply, BaseException):
            raise reply
        return str(reply)

    monkeypatch.setattr("builtins.input", fake_input)
    return asked


@pytest.mark.parametrize(
    "reply",
    [
        "",
        " ",
        "n",
        "N",
        "no",
        "yes",
        "Yes",
        "maybe",
        "yes please",
        "yy",
        "y y",
        "ye",
        "1",
        "true",
        "\uff59",
        "ok",
        "n y",
    ],
)
def test_k16_every_answer_but_y_stops_and_nothing_is_called(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], real_check: Any, reply: str
) -> None:
    """Kills M9-69 (anything but n counts as yes) and N22 (`== "n"`). `yes` is NOT a yes."""
    asked = _answer(monkeypatch, reply)
    rrc = real_check.rrc
    assert rrc.main(["--dry-fakes"]) == rrc.EXIT_STOPPED == constants.EXIT_STOPPED
    out = capsys.readouterr().out
    assert asked == ["Start? [y/N] "] and out.endswith("stopped, nothing was called\n")
    assert "no terminal" not in out
    _no_call_was_made(real_check.made[0])


@pytest.mark.parametrize("reply", ["y", "Y", " y ", "y ", "\ty\n", "  Y  "])
def test_k16_y_after_strip_and_lower_case_starts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], real_check: Any, reply: str
) -> None:
    """Pins the exact rule: strip() and lower() are applied, so `Y` and ` y ` ARE yes (`y ` too). Kills N23 (no
    strip) and N24 (no lower)."""
    _answer(monkeypatch, reply)
    with pytest.raises(_Started):
        real_check.rrc.main(["--dry-fakes"])
    assert "stopped" not in capsys.readouterr().out


@pytest.mark.parametrize("failure", [EOFError(), OSError("no input"), BrokenPipeError("closed")])
def test_k16_no_terminal_stops_with_the_no_terminal_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], real_check: Any, failure: BaseException
) -> None:
    """Kills N26 (the stop turned into exit code 0)."""
    _answer(monkeypatch, failure)
    rrc = real_check.rrc
    assert rrc.main(["--dry-fakes"]) == rrc.EXIT_STOPPED
    assert capsys.readouterr().out.endswith(
        "stopped, nothing was called: there is no terminal to answer the question on\n"
    )
    _no_call_was_made(real_check.made[0])


def test_k16_the_self_test_alone_still_asks_and_assume_yes_alone_is_refused(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], real_check: Any
) -> None:
    """Each flag alone: `--dry-fakes` asks; `--assume-yes` without it is refused before anything (no fakes, no
    question). Both together skip the question. Kills N25 (`and` -> `or`: the self-test alone would skip it)."""
    rrc = real_check.rrc
    asked = _answer(monkeypatch, "n")
    assert rrc.main(["--dry-fakes"]) == rrc.EXIT_STOPPED and len(asked) == 1
    capsys.readouterr()
    assert rrc.main(["--assume-yes"]) == rrc.EXIT_REFUSED
    out = capsys.readouterr().out
    assert out.startswith("refused: --assume-yes is only for the self-test") and len(asked) == 1
    assert len(real_check.made) == 1  # the refusal came before any fake was started
    with pytest.raises(_Started):  # both: no question, the run goes on
        rrc.main(["--dry-fakes", "--assume-yes"])
    assert len(asked) == 1


# ---- k17: M9-16 (the default mail port follows the security mode) ----


def _smtp_env(tmp_path: Path, **extra: str) -> dict[str, str]:
    return {
        "DESK_SMTPP_HOST": "localhost",
        "DESK_SMTPP_USER": "sender-user",
        "DESK_SMTPP_PASSWORD_FILE": str(tmp_path / "pw.txt"),
        "DESK_SMTPP_FROM": "sender@example.test",
        "DESK_SMTPP_RECIPIENTS": "inbox-a@example.test",
        "DESK_SMTPP_MAX_SENDS": "5",
        **extra,
    }


@pytest.mark.parametrize(
    ("security", "port", "expected"),
    [
        ("starttls", None, 587),
        ("ssl", None, 465),
        (None, None, 587),  # no mode named: the default mode is starttls
        ("starttls", "2525", 2525),
        ("ssl", "2525", 2525),
        ("ssl", "587", 587),
        ("starttls", "465", 465),
    ],
)
def test_k17_the_default_mail_port_follows_the_security_mode_and_a_set_port_wins(
    tmp_path: Path, security: str | None, port: str | None, expected: int
) -> None:
    """Kills M9-16 (the two defaults swapped) and N29 (the default always 587)."""
    extra: dict[str, str] = {}
    if security:
        extra["DESK_SMTPP_SECURITY"] = security
    if port:
        extra["DESK_SMTPP_PORT"] = port
    got = ProviderSettings.from_env(_smtp_env(tmp_path, **extra))
    assert got.port == expected
    assert got.security == (security or "starttls")
