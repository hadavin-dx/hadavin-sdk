"""Round 7C, finding D: the quiet drop of an error answer to a sender that has gone (`HeadDeadline.send_error`).

The r7b review changed `except OSError` to `except KeyError` (mutant M7) and all 84 tests still passed, while a real
header drip then printed BrokenPipeError traces. Two tests: the mix-in alone (a parent whose send_error fails like a
closed connection), and a real drip against each fake with the error output captured."""

from __future__ import annotations

import socket
import threading
import time
from typing import Any

import pytest
import test_r7_fake_slow_senders as slow
from test_r7_fake_slow_senders import _head

import scripts.http_guard as guard

target = slow.target  # the same fixture (one fake per case), reused here


class _ParentThatFails:
    error: BaseException = BrokenPipeError()

    def send_error(self, *_a: Any, **_k: Any) -> None:
        raise self.error


class _Handler(guard.HeadDeadline, _ParentThatFails):
    close_connection = False


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# a trace is printed for a gone sender, or a real bug is hidden.
@pytest.mark.parametrize("error", [BrokenPipeError(), ConnectionResetError(), OSError("gone"), TimeoutError()])
def test_an_error_answer_to_a_gone_sender_is_dropped_quietly(error: OSError) -> None:
    h = _Handler.__new__(_Handler)
    h.error = error
    h.send_error(408, "x")  # no exception
    assert h.close_connection is True


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# a trace is printed for a gone sender, or a real bug is hidden.
def test_only_connection_errors_are_dropped_a_real_bug_is_not_hidden() -> None:
    h = _Handler.__new__(_Handler)
    h.error = KeyError("bug")
    with pytest.raises(KeyError):
        h.send_error(408, "x")


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# a trace is printed for a gone sender, or a real bug is hidden.
def test_a_real_header_drip_prints_no_trace(
    target: tuple[int, str, bool], monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(guard, "FAKE_HEAD_DEADLINE_SECONDS", 1.0)
    port, line, auth = target
    head = _head(line, auth, "Content-Length: 2\r\n")[:-2] + b"X-Slow: "
    stop = threading.Event()

    def drip(s: socket.socket) -> None:
        try:
            for ch in head + b"a" * 100:
                if stop.is_set():
                    return
                s.sendall(bytes([ch]))
                time.sleep(0.1)
        except OSError:
            pass

    with socket.create_connection(("127.0.0.1", port), timeout=15) as s:
        th = threading.Thread(target=drip, args=(s,), daemon=True)
        th.start()
        try:
            while s.recv(4096):
                pass
        except OSError:
            pass
        stop.set()
        th.join(5)
    time.sleep(0.5)  # the server thread prints (if it prints) after the connection closed
    err = capfd.readouterr().err
    assert "Traceback" not in err and "BrokenPipeError" not in err, err[-300:]
