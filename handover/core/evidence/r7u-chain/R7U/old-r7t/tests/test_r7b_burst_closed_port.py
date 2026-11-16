"""Round 7B (hostile-driver result 3): `burst --url http://127.0.0.1:<closed port>` ran 30 s with 32 connect attempts
and no output. Now it looks for a listener for at most BURST_START_LOOK_SECONDS, then ends with ONE line on the error
output and exit code 3 (the thing it talks to cannot be reached); a listener that appears within that time is used."""

from __future__ import annotations

import socket
import threading
import time

import pytest
from support import HOST, free_port

from lead_desk.constants import BURST_START_LOOK_SECONDS, EXIT_UNREACHABLE

burst = pytest.importorskip("demo_only.burst")


def test_a_closed_port_ends_fast_with_one_line_and_exit_3(capsys: pytest.CaptureFixture[str]) -> None:
    port = free_port()  # nothing listens on it
    t0 = time.monotonic()
    code = burst.main(
        [
            "--url",
            f"http://{HOST}:{port}/x",
            "--n",
            "5",
            "--email",
            "a@example.com",
            "--ref-prefix",
            "p",
            "--source",
            "form",
        ]
    )
    took = time.monotonic() - t0
    out = capsys.readouterr()
    assert code == EXIT_UNREACHABLE, (code, out)
    assert took < BURST_START_LOOK_SECONDS + 3, f"took {took:.1f} s"
    assert out.out == "" and out.err.strip().splitlines() == [
        "ERROR: nothing answers at that address: no request was sent"
    ]


def test_a_listener_that_starts_late_is_waited_for() -> None:
    port = free_port()
    srv = socket.socket()

    def later() -> None:
        time.sleep(1.0)
        srv.bind((HOST, port))
        srv.listen(1)

    th = threading.Thread(target=later, daemon=True)
    th.start()
    try:
        assert burst.listener_answers(f"http://{HOST}:{port}/", BURST_START_LOOK_SECONDS)
    finally:
        th.join(5)
        srv.close()


def test_the_look_gives_up_when_nothing_ever_listens() -> None:
    assert burst.listener_answers(f"http://{HOST}:{free_port()}/", 0.5) is False
