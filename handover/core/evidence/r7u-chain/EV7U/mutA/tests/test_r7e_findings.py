"""Round 7E: the r7d review findings. Real loopback sockets, made-up data only.

M1-new  a desk that answered once is never called unreachable: the load driver marks the desk as answering after
        EVERY try (any code), not only after a 503.
m1      exit code 2 for a refused setting of run_real_check: docs and the constants comment say the same number.
m3      the portal asks the CRM for `limit=200` (a test asserts what the stand-in saw).
N6      the docs say that a secret file is checked first and read again by the program that uses it.
Every test says in its docstring whether it FAILS on the r7d tree (a fix test) or is a CONTROL."""

from __future__ import annotations

import json
import re
import socket
import threading
import time
from pathlib import Path

from support import REPO
from test_r7d_findings import _run_driver


class _DropsSomeRequests:
    """A stand-in desk on 127.0.0.1: answers 202 to every request except requests number DROP_FROM to DROP_TO
    (counted from 0 over requests that sent bytes; a probe that only connects is not counted), which are closed
    without any answer."""

    DROP_FROM = 20
    DROP_TO = 39

    def __init__(self) -> None:
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(128)
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.count = 0
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._accept, daemon=True)
        self.thread.start()

    def _accept(self) -> None:
        while not self.stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except OSError:
                continue
            threading.Thread(target=self._one, args=(conn,), daemon=True).start()

    def _one(self, conn: socket.socket) -> None:
        with conn:
            conn.settimeout(5)
            try:
                data = b""
                while b"\r\n\r\n" not in data:
                    piece = conn.recv(65536)
                    if not piece:
                        return  # the probe: connected and left, nothing sent
                    data += piece
                head, _, body = data.partition(b"\r\n\r\n")
                need = 0
                for header in head.split(b"\r\n")[1:]:
                    name, _, value = header.partition(b":")
                    if name.strip().lower() == b"content-length":
                        need = int(value.strip())
                while len(body) < need:
                    body += conn.recv(65536)
                with self.lock:
                    n = self.count
                    self.count += 1
                if self.DROP_FROM <= n <= self.DROP_TO:
                    return  # closed without an answer
                raw = b'{"receipt_id": "r", "verdict": "accepted"}'
                head_out = b"HTTP/1.1 202 Accepted\r\nContent-Length: " + str(len(raw)).encode()
                conn.sendall(head_out + b"\r\nConnection: close\r\n\r\n" + raw)
            except OSError:
                return

    def close(self) -> None:
        self.stop.set()
        self.thread.join(5)
        self.sock.close()


def test_m1_new_a_desk_that_answered_and_then_drops_some_connections_is_not_called_unreachable(tmp_path: Path) -> None:
    """FAILS on r7d: the answered flag was set only by a 503, so after 2 x threads connection errors the run was
    stopped (79 requests `driver:stopped`, never sent) and the false line 'every request ended in a connection error'
    was printed (rc 3). Here the desk answers 202, drops requests 20 to 39 and answers again: all 100 requests are
    sent and logged, none is `driver:stopped`, no 'cannot be reached' line."""
    srv = _DropsSomeRequests()
    try:
        log = tmp_path / "req.jsonl"
        t0 = time.monotonic()
        done = _run_driver(
            f"http://127.0.0.1:{srv.port}", "burst:100", log, "--workers", "1", "--threads", "2", timeout=120
        )
        took = time.monotonic() - t0
    finally:
        srv.close()
    err = done.stderr.decode()
    assert "cannot be reached" not in err, (done.returncode, err[-400:])
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 100, len(lines)
    assert not [d for d in lines if d["final_status"] == "driver:stopped"], "requests were never sent"
    assert not [d for d in lines if d["gave_up"] == "stopped"]
    assert all(d["accepted"] for d in lines), [d["final_status"] for d in lines if not d["accepted"]][:5]
    assert done.returncode == 0, (done.returncode, err[-400:])
    assert took < 100, f"took {took:.1f} s"


# -- m1: one number, one meaning (exit code 2 of run_real_check) -----------------------------------------------------


def test_m1_the_exit_code_2_of_run_real_check_is_the_same_in_the_script_the_constants_and_the_docs() -> None:
    """FAILS on r7d: docs/settings.md and the script said 2 for a refused setting while the comment in constants.py
    said 4 for a bad setting, and docs/limits.md said no number has two meanings, with no exception named. Now the
    script refuses with EXIT_REFUSED (2) only, and the three texts name run_real_check as the one exception."""
    constants = (REPO / "src" / "lead_desk" / "constants.py").read_text(encoding="utf-8")
    limits = (REPO / "docs" / "limits.md").read_text(encoding="utf-8")
    settings = (REPO / "docs" / "settings.md").read_text(encoding="utf-8")
    script = (REPO / "scripts" / "run_real_check.py").read_text(encoding="utf-8")
    assert "EXIT_REFUSED: Final = 2" in constants and "EXIT_BAD_SETTING_OR_PATH: Final = (\n    4" in constants
    assert "scripts/run_real_check.py ends EVERY refusal at its start with 2, a refused setting" in constants.replace(
        "\n# ", " "
    )
    assert re.search(r"one exception is\s+`scripts/run_real_check.py`,\s+which ends every refusal", limits)
    assert "this script uses 2 for a bad setting where the other scripts use 4" in settings.replace("\n  ", " ")
    assert "refused at the start (a missing or bad setting" in settings.replace("\n  ", " ")
    # the script itself: no refusal path uses the code 4 constant as a return value
    assert not re.search(r"return\s+EXIT_BAD_SETTING_OR_PATH", script)
    assert len(re.findall(r"return\s+EXIT_REFUSED", script)) >= 8
