"""Round 7C nits: the burst's listener probe sends NOTHING (the text "no request was sent" is true), and the address
rule: `localhost` and the loopback addresses are accepted; look-alike names are refused before any connection."""

from __future__ import annotations

import socket
import threading

import pytest
from support import HOST

burst = pytest.importorskip("demo_only.burst")


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the probe sends a byte, or a look-alike name is accepted.
def test_the_probe_connects_and_sends_no_byte() -> None:
    srv = socket.socket()
    srv.bind((HOST, 0))
    srv.listen(1)
    got: list[bytes] = []

    def accept() -> None:
        conn, _ = srv.accept()
        conn.settimeout(2.0)
        try:
            while chunk := conn.recv(100):
                got.append(chunk)
        except OSError:
            pass
        conn.close()

    th = threading.Thread(target=accept, daemon=True)
    th.start()
    try:
        assert burst.listener_answers(f"http://{HOST}:{srv.getsockname()[1]}/x", 2.0)
    finally:
        th.join(5)
        srv.close()
    assert got == []


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the probe sends a byte, or a look-alike name is accepted.
@pytest.mark.parametrize("good", ["http://localhost:1/x", "http://127.0.0.1:1/x", "http://[::1]:1/x"])
def test_the_names_this_computer_has_are_accepted(good: str, capsys: pytest.CaptureFixture[str]) -> None:
    argv = ["--n", "1", "--email", "a@example.com", "--ref-prefix", "p", "--source", "form"]
    assert burst.main(["--url", good, *argv]) == 3  # parsed; nothing listens on port 1: the one unreachable line
    assert capsys.readouterr().err.strip() == "ERROR: nothing answers at that address: no request was sent"


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# the probe sends a byte, or a look-alike name is accepted.
@pytest.mark.parametrize(
    "bad",
    [
        "http://" + "localhost.example.test:1/x",
        "http://" + "127.0.0.1.example.test:1/x",
        "http://" + "localhostx:1/x",
        "http://" + "0:1/x",
    ],
)
def test_look_alike_names_are_refused_before_any_connection(bad: str, capsys: pytest.CaptureFixture[str]) -> None:
    argv = ["--n", "1", "--email", "a@example.com", "--ref-prefix", "p", "--source", "form"]
    with pytest.raises(SystemExit) as info:
        burst.main(["--url", bad, *argv])
    assert info.value.code == 2
    assert "nothing answers" not in capsys.readouterr().err
