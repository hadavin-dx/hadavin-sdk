"""d-fix18: door review 1, the code fixes.

M1 a cap on request line and headers together (431), M4 the memory store only at stage demo, M6 the tests that
kill the mutants of `hmac_v0.py`, of the single write of `send_error` and of the two halves of the no-version guard."""

from __future__ import annotations

import contextlib
import socket
from email.message import Message
from types import SimpleNamespace

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.triggers import endpoint, server, worker
from hadavin_sdk.triggers.server import QuietRequestHandler
from tests.triggers.test_d_fix13_single_write import (
    CLIENT_TIMEOUT_S,
    _post,
    _serving,
    _wsgi,
)

PAD = b"a" * 190


def _with_headers(count: int) -> bytes:
    data = _post()
    head, sep, body = data.partition(b"\r\n\r\n")
    extra = b"".join(b"\r\nX-Pad-%d: %s" % (i, PAD) for i in range(count))
    return head + extra + sep + body


def _exchange(data: bytes):
    log: list[list[bytes]] = []
    with _serving(_wsgi(), log) as srv:
        sock = socket.create_connection(
            (worker.LOOPBACK, srv.server_address[1]), timeout=CLIENT_TIMEOUT_S
        )
        try:
            sock.sendall(data)
            raw = b""
            with contextlib.suppress(ConnectionResetError, TimeoutError):
                while part := sock.recv(65536):
                    raw += part
        finally:
            sock.close()
    return raw, log


def test_m1_many_small_headers_over_16_kb_are_431_in_one_write():
    raw, log = _exchange(
        _with_headers(90)
    )  # 90 x ~200 bytes, far under 100 headers and 64 KB a line
    assert raw == (
        b"HTTP/1.0 431 Request Header Fields Too Large\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
    )
    assert len(log) == 1 and len(log[0]) == 1, [w[:30] for w in log[0]]


def test_m1_headers_under_the_cap_are_still_taken():
    raw, log = _exchange(_with_headers(50))  # about 10 KB
    assert raw.startswith(b"HTTP/1.0 202 "), raw[:60]
    assert server.MAX_HEADER_BYTES == 16384


# --- M4: the memory store is for demo only --------------------------------------------------------------------


@pytest.mark.parametrize("stage", ["pilot", "prod", "other"])
def test_m4_the_memory_store_is_refused_unless_the_stage_is_demo(stage):
    with pytest.raises(worker.ConfigError, match="memory store is for the demo stage only"):
        worker.check_store_stage(MemoryStore(), SimpleNamespace(environment=stage))


def test_m4_demo_and_other_stores_pass():
    worker.check_store_stage(MemoryStore(), SimpleNamespace(environment="demo"))
    worker.check_store_stage(SimpleNamespace(), SimpleNamespace(environment="prod"))


def test_m4_make_app_refuses_a_memory_store_at_pilot(rt_pilot_app):
    with pytest.raises(worker.ConfigError, match="demo stage only"):
        worker.make_app(rt_pilot_app)


@pytest.fixture
def rt_pilot_app(monkeypatch):
    seen = []
    monkeypatch.setattr(worker, "trigger_settings", lambda c: seen.append(c) or object())
    monkeypatch.setattr(worker, "secret_reader", lambda a: None)
    monkeypatch.setattr(worker, "sender_list", lambda s: [])
    monkeypatch.setattr(worker, "check_senders", lambda *a: None)
    monkeypatch.setattr(worker, "read_secrets", lambda *a: {})
    monkeypatch.setattr(worker, "_field", lambda o, n, w: getattr(o, n))
    monkeypatch.setattr(worker, "check_secrets", lambda s: None)
    monkeypatch.setattr(worker, "Runner", lambda *a, **k: SimpleNamespace(close=lambda *_: None))
    return SimpleNamespace(
        config=SimpleNamespace(environment="pilot"),
        runtime=SimpleNamespace(agents=[]),
        registry=SimpleNamespace(principals={}),
        store=MemoryStore(),
    )


# --- M6: hmac_v0 ---------------------------------------------------------------------------------------------


def test_m6_the_signature_is_compared_with_compare_digest(monkeypatch):
    calls = []
    real = hmac_v0.hmac.compare_digest
    monkeypatch.setattr(
        hmac_v0.hmac, "compare_digest", lambda a, b: calls.append((a, b)) or real(a, b)
    )
    headers = hmac_v0.sign(b"body", 1000, "s" * 40, "X-T")
    assert hmac_v0.verify(headers, b"body", 1000, "s" * 40, "X-T") is True
    assert len(calls) == 1 and calls[0][0] == calls[0][1]


@pytest.mark.parametrize(
    ("now", "ok"), [(1300, True), (1301, False), (700, True), (699, False), (1000, True)]
)
def test_m6_the_five_minute_window(now, ok):
    headers = hmac_v0.sign(b"body", 1000, "s" * 40, "X-T")
    assert hmac_v0.verify(headers, b"body", now, "s" * 40, "X-T") is ok, now


# --- M6: the answer of send_error is one write; the no-version guard has two halves --------------------------


def test_m6_send_error_is_exactly_one_write():
    writes: list[bytes] = []
    h = QuietRequestHandler.__new__(QuietRequestHandler)
    h.request_version = "HTTP/1.1"
    h.wfile = SimpleNamespace(write=writes.append)  # type: ignore[assignment]
    h.send_error(431)
    assert len(writes) == 1, writes


def _handler(version, headers):
    h = QuietRequestHandler.__new__(QuietRequestHandler)
    h.rfile = SimpleNamespace(
        readline=lambda n=-1: b"GET /x HTTP/1.1\r\n",
        count_head=lambda n: None,
        stop_count=lambda: None,
    )
    h.parse_request = lambda: (
        setattr(h, "request_version", version)
        or setattr(  # type: ignore[method-assign]
            h, "headers", headers
        )
        or True
    )
    sent: list[bytes] = []
    h.wfile = SimpleNamespace(write=sent.append)  # type: ignore[assignment]

    def get_app():
        raise AssertionError("the application was reached")

    h.server = SimpleNamespace(get_app=get_app)  # type: ignore[assignment]
    return h, sent


def test_m6_version_0_9_with_a_header_block_is_closed_with_no_answer():
    h, sent = _handler("HTTP/0.9", Message())
    h._serve()
    assert sent == []


def test_m6_a_header_block_that_is_not_a_message_is_closed_with_no_answer():
    h, sent = _handler("HTTP/1.1", object())
    h._serve()
    assert sent == []


def test_m6_the_dead_constants_are_gone():
    from tests import endpoint_mutants

    assert not hasattr(endpoint_mutants, "EMPTY_REFUSAL")
    assert not hasattr(endpoint_mutants, "NO_VERSION")
    assert endpoint is not None
