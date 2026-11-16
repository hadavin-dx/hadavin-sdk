"""Round 7B (lead N1, N2), at the one place every fake server's handler passes through.

N1: a request body that nests about 100,000 levels deep made json.loads raise RecursionError in the fakes: a
traceback on the error output and NO answer. Now `scripts.http_guard.loads_bounded` turns it into the same ValueError
as any text that is not JSON, and `AnswersBadRequests` also shields RecursionError: one fixed 400 and no traceback,
per fake.
N2: the request line and the headers had no total time limit (the socket timeout restarts with every byte): a sender of
one byte every few seconds held a handler thread for about 80 seconds. Now ONE timer per request
(FAKE_HEAD_DEADLINE_SECONDS, shortened here) ends the connection. Each case is a raw request over a loopback socket."""

from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

import pytest
import test_r7_fake_slow_senders as slow
from test_r7_fake_bad_requests import KEY
from test_r7_fake_slow_senders import _head, _status

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import http_guard

import scripts.http_guard as scripts_http_guard

DEPTH = 100_000
target = slow.target  # the same fixture (one fake per case), reused here


def _post(port: int, line: str, auth: bool, body: bytes, extra: str = "") -> bytes:
    head = _head(line, auth, f"Content-Length: {len(body)}\r\n{extra}")
    with socket.create_connection(("127.0.0.1", port), timeout=20) as s:
        s.sendall(head + body)
        out = b""
        while chunk := s.recv(4096):
            out += chunk
    return out


@pytest.mark.parametrize("body", [b"[" * DEPTH, b'{"a":' * DEPTH, b"[" * DEPTH + b"]" * DEPTH])
def test_a_body_nested_100000_deep_is_one_400_and_no_traceback(
    target: tuple[int, str, bool], capfd: pytest.CaptureFixture[str], body: bytes
) -> None:
    port, line, auth = target
    out = _post(port, line, auth, body)
    assert _status(out) == 400, out[:80]
    assert "Traceback" not in capfd.readouterr().err


def test_the_model_fake_answers_a_deep_message_body_too(
    target: tuple[int, str, bool], capfd: pytest.CaptureFixture[str]
) -> None:
    port, line, _ = target
    if line != "POST /control":
        pytest.skip("only the model fake has /v1/messages")
    out = _post(port, "POST /v1/messages", False, b"[" * DEPTH, extra=f"x-api-key: {KEY}\r\n")
    assert 200 <= _status(out) < 500, out[:80]
    assert "Traceback" not in capfd.readouterr().err


def test_loads_bounded_refuses_deep_text_like_any_other_bad_json() -> None:
    for module in (http_guard, scripts_http_guard):
        with pytest.raises(ValueError):
            module.loads_bounded(b"[" * DEPTH)
        assert module.loads_bounded(b'{"a": [1, 2]}') == {"a": [1, 2]}


@pytest.mark.parametrize("pause", [1.0, 0.3])  # one byte per second (the lead's case), and a faster drip
def test_a_header_drip_is_cut_off_at_the_head_deadline(
    target: tuple[int, str, bool], monkeypatch: pytest.MonkeyPatch, pause: float
) -> None:
    for module in (http_guard, scripts_http_guard):
        monkeypatch.setattr(module, "FAKE_HEAD_DEADLINE_SECONDS", 2.0)
    port, line, auth = target
    head = _head(line, auth, "Content-Length: 2\r\n")[:-2] + b"X-Slow: "  # an unfinished header line, then a drip
    t0 = time.monotonic()
    closed_after: list[float] = []

    def drip(s: socket.socket) -> None:
        try:
            for ch in head + b"a" * 200:  # one byte per `pause` seconds, each well inside the socket timeout
                s.sendall(bytes([ch]))
                time.sleep(pause)
        except OSError:
            pass

    with socket.create_connection(("127.0.0.1", port), timeout=15) as s:
        th = threading.Thread(target=drip, args=(s,), daemon=True)
        th.start()
        try:
            while True:
                data = s.recv(4096)
                if not data:
                    break
        except OSError:
            pass
        closed_after.append(time.monotonic() - t0)
    assert closed_after[0] < 5.0, f"the server held the connection for {closed_after[0]:.1f} s"


def test_a_normal_request_after_the_head_is_read_is_not_cut(
    target: tuple[int, str, bool], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The timer ends when the headers are read: a slow ANSWER or a body inside its own deadline is not cut."""
    for module in (http_guard, scripts_http_guard):
        monkeypatch.setattr(module, "FAKE_HEAD_DEADLINE_SECONDS", 1.0)
    port, line, auth = target
    head = _head(line, auth, "Content-Length: 2\r\n")
    with socket.create_connection(("127.0.0.1", port), timeout=15) as s:
        s.sendall(head)
        time.sleep(1.8)  # longer than the head deadline: the head is complete, the body is on its own deadline
        s.sendall(b"{}")
        out = b""
        while chunk := s.recv(4096):
            out += chunk
    assert 200 <= _status(out) < 500, out[:80]
