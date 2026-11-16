"""Round 7 (EV6): a request with NO Content-Length, and a sender that trickles its body (one byte at a time, each
byte inside the socket timeout) are both answered and let go by every fake server: no traceback, no handler held for
ever. The body has ONE total deadline (FAKE_BODY_DEADLINE_SECONDS, shortened here); a socket timeout alone restarts
with every byte. Each case is a raw request over a loopback socket to the real handler class."""

from __future__ import annotations

import socket
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from test_r7_fake_bad_requests import KEY, fh, make_fakes_server, make_model_server, serve

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import http_guard

import scripts.http_guard as scripts_http_guard

CASES = {
    "hubspot": ("POST /crm/v3/objects/contacts", True),
    "fakes": ("POST /fake/outbox", False),
    "model": ("POST /control", False),
}


@pytest.fixture(params=sorted(CASES))
def target(request: pytest.FixtureRequest) -> Iterator[tuple[int, str, bool]]:
    which = request.param
    if which == "hubspot":
        state = fh.HubspotState(KEY, "ok")
        srv: Any = fh.FakeHubspot(("127.0.0.1", 0), type("H", (fh._Handler,), {"state": state}))
    elif which == "fakes":
        srv = make_fakes_server("keyed", 0, "keyed", "127.0.0.1")
    else:
        srv, _ = make_model_server("127.0.0.1", 0, "ok")
    gen = serve(srv)
    port = next(gen)
    yield port, CASES[which][0], CASES[which][1]
    next(gen, None)


def _head(line: str, auth: bool, extra: str) -> bytes:
    a = f"Authorization: Bearer {KEY}\r\n" if auth else ""
    return f"{line} HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n{a}{extra}\r\n".encode()


def _status(raw: bytes) -> int:
    return int(raw.split(b" ", 2)[1]) if raw.startswith(b"HTTP/") else 0


def test_a_post_with_no_content_length_is_answered_without_a_traceback(
    target: tuple[int, str, bool], capfd: pytest.CaptureFixture[str]
) -> None:
    port, line, auth = target
    with socket.create_connection(("127.0.0.1", port), timeout=10) as s:
        s.sendall(_head(line, auth, ""))
        out = b""
        while chunk := s.recv(4096):
            out += chunk
    assert 200 <= _status(out) < 500, out[:80]
    assert "Traceback" not in capfd.readouterr().err


def test_a_sender_of_one_byte_at_a_time_is_cut_off_at_the_body_deadline(
    target: tuple[int, str, bool], capfd: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    for module in (http_guard, scripts_http_guard):  # the fakes import it as scripts.http_guard
        monkeypatch.setattr(module, "FAKE_BODY_DEADLINE_SECONDS", 1.0)
    port, line, auth = target
    t0 = time.monotonic()
    out = b""
    with socket.create_connection(("127.0.0.1", port), timeout=15) as s:
        s.sendall(_head(line, auth, "Content-Length: 60\r\n"))
        stop = threading.Event()

        def trickle() -> None:
            for _ in range(60):
                if stop.wait(0.3):
                    return
                try:
                    s.sendall(b" ")
                except OSError:
                    return

        th = threading.Thread(target=trickle, daemon=True)
        th.start()
        while chunk := s.recv(4096):
            out += chunk
        stop.set()
        th.join(5)
    took = time.monotonic() - t0
    assert _status(out) == (400 if line.startswith("POST /crm") else 408), out[
        :80
    ]  # 408 from the shared reader, or the one fixed 400 of the hubspot fake
    assert took < 8, took  # the whole body is allowed 1 s here; 60 bytes at 0.3 s would have held it for 18 s
    assert "Traceback" not in capfd.readouterr().err


def test_a_deadline_does_not_cut_off_a_body_that_arrives_in_time(monkeypatch: pytest.MonkeyPatch) -> None:
    class H:
        pass

    class R:
        def __init__(self) -> None:
            self.data = b"abcdef"

        def read1(self, n: int) -> bytes:
            out, self.data = self.data[: min(n, 2)], self.data[min(n, 2) :]
            return out

    class C:
        def settimeout(self, _t: float) -> None:
            pass

    h = H()
    h.headers = {"Content-Length": "6"}
    h.rfile, h.connection = R(), C()
    read: Callable[..., tuple[bytes, int]] = http_guard.read_request_body
    assert read(h) == (b"abcdef", 0)
