"""Round 7: input files and replies that are read with a size rule, tested where the rule is applied.
F5: the invariant checker (byte-order mark, line rule, row caps, exit codes). F7: the portal demo reads a reply
of 6,200 rows whole and refuses one over the cap. F8: Content-Length text (leading zeros, two lines) and the
body read of a fake server on a REAL socket (a slow sender gets 408, chunked 411, Expect: 100-continue). F14:
reset_check refuses a book path that is not a plain file with exit 4. Exit codes: scripts return the shared
constants, never a bare number. F1: a mailbox user that cannot be used ends run_real_check with one fixed line
and exit 2."""

from __future__ import annotations

import ast
import email.message
import json
import os
import socket
import sys
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from support import run_python
from test_path_confinement import _ci_args

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import http_guard

from demo_only import portal_demo
from lead_desk import constants
from load_tools import check_invariants as ci
from tools import pathconfine as pc

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def jail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pc.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(pc, "REPO_ROOT", tmp_path)
    monkeypatch.delenv(pc.ROOTS_ENV, raising=False)
    return tmp_path


# -- F5: the invariant checker -------------------------------------------------------------------------------------


def test_a_byte_order_mark_in_front_of_the_first_row_is_dropped(jail: Path) -> None:
    (jail / "a.jsonl").write_bytes(b'\xef\xbb\xbf{"a": 1}\n{"a": 2}\n')
    assert ci.read_jsonl(Path("a.jsonl")) == [{"a": 1}, {"a": 2}]


def test_a_byte_order_mark_in_the_middle_is_not_json(jail: Path) -> None:
    (jail / "a.jsonl").write_bytes(b'{"a": 1}\n\xef\xbb\xbf{"a": 2}\n')
    with pytest.raises(ci.InputError, match="line 2: not JSON"):
        ci.read_jsonl(Path("a.jsonl"), "--x")


def test_a_row_ends_at_a_line_feed_a_carriage_return_before_it_is_white_space_a_lone_one_is_no_line_break(
    jail: Path,
) -> None:
    (jail / "ok.jsonl").write_bytes(b'{"a": 1}\r\n{"a": 2}\r\n')
    assert len(ci.read_jsonl(Path("ok.jsonl"))) == 2
    (jail / "lone.jsonl").write_bytes(b'{"a": 1}\r{"a": 2}\n')  # two objects on one "line": not one JSON value
    with pytest.raises(ci.InputError, match="line 1: not JSON"):
        ci.read_jsonl(Path("lone.jsonl"), "--x")


def test_more_rows_than_the_cap_raise_the_log_too_long_error(jail: Path) -> None:
    (jail / "a.jsonl").write_text('{"a": 1}\n' * 4, encoding="utf-8")
    assert len(ci.read_jsonl(Path("a.jsonl"), row_cap=4)) == 4
    with pytest.raises(ci.TooManyRowsError, match="more than 3 rows"):
        ci.read_jsonl(Path("a.jsonl"), "--model-log", row_cap=3)


def test_the_model_log_has_its_own_cap_and_main_passes_it() -> None:
    assert constants.MODEL_LOG_ROWS_MAX > constants.LOAD_TOTAL_MAX  # several model calls per lead
    tree = ast.parse((REPO / "load_tools" / "check_invariants.py").read_text(encoding="utf-8"))
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "read_jsonl"
        and any(isinstance(a, ast.Constant) and a.value == "--model-log" for a in n.args)
    ]
    assert len(calls) == 1
    assert any(isinstance(a, ast.Name) and a.id == "MODEL_LOG_ROWS_MAX" for a in calls[0].args)


def test_a_path_that_cannot_be_used_ends_the_checker_with_4_and_a_bad_file_with_2(
    jail: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = _ci_args(jail)
    (jail / "r.jsonl").write_text("not json\n", encoding="utf-8")
    assert ci.main([w for pair in args.items() for w in pair]) == constants.EXIT_REFUSED == 2
    capsys.readouterr()
    args["--catcher"] = "gone.jsonl"
    assert ci.main([w for pair in args.items() for w in pair]) == constants.EXIT_BAD_SETTING_OR_PATH == 4
    assert "no such file" in capsys.readouterr().err


# -- F7: the portal demo reads a reply whole up to the cap ----------------------------------------------------------


class _Reply(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body: bytes = self.server.body
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def reply_server() -> Iterator[ThreadingHTTPServer]:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Reply)
    srv.daemon_threads = True
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield srv
    srv.shutdown()
    srv.server_close()
    th.join(5)


def _url(srv: ThreadingHTTPServer) -> str:
    return f"http://127.0.0.1:{srv.server_address[1]}/x"


def test_a_reply_of_3000_rows_is_read_whole(reply_server: ThreadingHTTPServer) -> None:
    rows = [{"lead": f"L{n:06d}", "state": "sent", "note": "x" * 380} for n in range(3000)]
    reply_server.body = json.dumps({"rows": rows}).encode()
    assert 1_000_000 < len(reply_server.body) < constants.PORTAL_VIEW_REPLY_MAX_BYTES
    got = portal_demo._fetch_json(_url(reply_server), 10.0)
    assert got is not None and len(got["rows"]) == 3000 and got["rows"][-1]["lead"] == "L002999"


def test_a_reply_over_the_cap_is_refused_whole_not_cut(reply_server: ThreadingHTTPServer) -> None:
    pad = "x" * (constants.PORTAL_VIEW_REPLY_MAX_BYTES + 10)  # the portal's view cap (round 7B), not the script cap
    reply_server.body = json.dumps({"pad": pad}).encode()
    assert portal_demo._fetch_json(_url(reply_server), 10.0) is None


def test_a_reply_of_exactly_the_cap_is_accepted_and_one_byte_more_is_not() -> None:
    cap = constants.SCRIPT_REPLY_MAX_BYTES

    class R:
        def __init__(self, n: int) -> None:
            self.n = n

        def read(self, size: int) -> bytes:
            return b"x" * min(size, self.n)

    assert len(portal_demo._read_capped(R(cap))) == cap
    with pytest.raises(portal_demo.ReplyTooBig):
        portal_demo._read_capped(R(cap + 1))


# -- F8: Content-Length text and the body read on a real socket -------------------------------------------------------


def _headers(*lines: str) -> email.message.Message:
    msg = email.message.Message()
    for line in lines:
        k, v = line.split(":", 1)
        msg[k] = v.strip()
    return msg


@pytest.mark.parametrize(
    ("lines", "want"),
    [
        (("Content-Length: 5",), (5, 0)),
        (("Content-Length: 0000000000000000005",), (5, 0)),  # leading zeros are not a length problem
        (("Content-Length: " + "0" * 5000 + "7",), (7, 0)),  # long, but only zeros in front
        (("Content-Length: 00",), (0, 0)),
        (("Content-Length: 5", "Content-Length: 5"), (5, 0)),  # the same twice is one
        (("Content-Length: 5", "Content-Length: 6"), (0, http_guard.BODY_BAD)),  # two readers would size it differently
        (("Content-Length: 5", "Content-Length: 05"), (0, http_guard.BODY_BAD)),
        (("Content-Length: -1",), (0, http_guard.BODY_BAD)),
        (("Content-Length: +5",), (0, http_guard.BODY_BAD)),
        (("Content-Length: 5x",), (0, http_guard.BODY_BAD)),
        (("Content-Length: " + "9" * 5000,), (0, http_guard.BODY_TOO_BIG)),
        (("Transfer-Encoding: chunked",), (0, http_guard.BODY_NEEDS_LENGTH)),
        ((), (0, 0)),
    ],
)
def test_announced_length_text(lines: tuple[str, ...], want: tuple[int, int]) -> None:
    assert http_guard.announced_length(_headers(*lines)) == want


class _Body(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 0.6  # the socket timeout of the handler: a sender that stops sending is cut off

    def do_POST(self) -> None:
        body, status = http_guard.read_request_body(self)
        out = json.dumps({"n": len(body)}).encode() if not status else b"{}"
        self.send_response(status or 200)
        self.send_header("Content-Length", str(len(out)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(out)
        self.close_connection = True

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def body_server() -> Iterator[int]:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Body)
    srv.daemon_threads = True
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield int(srv.server_address[1])
    srv.shutdown()
    srv.server_close()
    th.join(5)


def _raw(port: int, head: bytes, then: bytes = b"", wait: float = 0.0) -> bytes:
    with socket.create_connection(("127.0.0.1", port), timeout=10) as s:
        s.sendall(head)
        if wait:
            threading.Event().wait(wait)
        if then:
            s.sendall(then)
        out = b""
        while chunk := s.recv(4096):
            out += chunk
    return out


def test_a_slow_sender_that_stops_midway_is_answered_408(body_server: int) -> None:
    head = b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 10\r\n\r\nabc"  # 3 of 10 bytes, then silence
    assert _raw(body_server, head, wait=1.5).startswith(b"HTTP/1.0 408") or b" 408 " in _raw(
        body_server, head, wait=1.5
    )


def test_the_full_body_is_read_and_a_short_one_is_408(body_server: int) -> None:
    ok = _raw(body_server, b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 4\r\n\r\nabcd")
    assert b" 200 " in ok.split(b"\r\n", 1)[0] + b" " and b'"n": 4' in ok
    short = _raw(body_server, b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 4\r\n\r\nab", wait=1.2)
    assert b" 408 " in short.split(b"\r\n", 1)[0] + b" "


def test_a_chunked_body_is_411_and_the_body_is_not_read(body_server: int) -> None:
    head = b"POST / HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    assert b" 411 " in _raw(body_server, head).split(b"\r\n", 1)[0] + b" "


def test_expect_100_continue_with_a_good_length_reads_the_body_and_with_two_lengths_is_400(body_server: int) -> None:
    good = b"POST / HTTP/1.1\r\nHost: x\r\nExpect: 100-continue\r\nContent-Length: 3\r\n\r\nabc"
    got = _raw(body_server, good)
    assert b"100 Continue" in got and b" 200 " in got and b'"n": 3' in got
    two = b"POST / HTTP/1.1\r\nHost: x\r\nExpect: 100-continue\r\nContent-Length: 3\r\nContent-Length: 4\r\n\r\nabc"
    assert b" 400 " in _raw(body_server, two)


# -- F14: reset_check refuses a book path that is not a plain file --------------------------------------------------


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs named pipes")
def test_reset_check_refuses_a_book_that_is_a_named_pipe_with_exit_4(tmp_path: Path) -> None:
    fifo = tmp_path / "book.sqlite3"
    os.mkfifo(fifo)
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(REPO / "src"), "DESK_DB_PATH": str(fifo)}
    done = run_python([str(REPO / "scripts" / "reset_check.py")], env, timeout=20)
    assert done.returncode == constants.EXIT_RESET_PORT_OR_BOOK == 4, (done.stdout, done.stderr)
    assert done.stdout.startswith("refused: the lead book path cannot be used") and "nothing was deleted" in done.stdout
    assert len(done.stdout.strip().splitlines()) == 1 and "Traceback" not in done.stderr


# -- exit codes: scripts use the shared constants ------------------------------------------------------------------


def _bare_exit_numbers(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        value: ast.AST | None = None
        if isinstance(node, ast.Return):
            value = node.value
        elif isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name)):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            if name in {"exit", "_exit"} and node.args:
                value = node.args[0]
        if isinstance(value, ast.Constant) and isinstance(value.value, int) and not isinstance(value.value, bool):
            if value.value != 0:
                found.append((node.lineno, f"bare {value.value}"))
    return found


def test_no_script_ends_with_a_bare_exit_number_other_than_zero() -> None:
    """A `return 4` or `sys.exit(3)` hides what the number means; every non-zero code is a named constant.
    Zero is the one number that needs no name."""
    bad: dict[str, list[tuple[int, str]]] = {}
    for folder in ("scripts", "tools", "load_tools", "demo_only"):
        for p in sorted((REPO / folder).rglob("*.py")):
            hits = _bare_exit_numbers(p)
            if hits:
                bad[p.relative_to(REPO).as_posix()] = hits
    assert not bad, bad


def test_the_exit_constants_have_one_meaning_each_and_the_documented_values() -> None:
    c = constants
    pairs = {
        "EXIT_CHECK_FAILED": 1,
        "EXIT_REFUSED": 2,
        "EXIT_UNREACHABLE": 3,
        "EXIT_BAD_SETTING_OR_PATH": 4,
        "EXIT_STOPPED": 6,
        "EXIT_ADAPTERS_UNREACHABLE": 7,
        "EXIT_RESET_DESK_RUNNING": 3,  # the reset family: its own numbers, pinned by tests/test_reset_scripts.py
        "EXIT_RESET_PORT_OR_BOOK": 4,
    }
    for name, value in pairs.items():
        assert getattr(c, name) == value, name


# -- F1: a mailbox user that cannot be used, end to end through the real main -------------------------------------


def test_f1_run_real_check_with_a_bad_mailbox_user_ends_with_one_fixed_line_and_exit_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import run_real_check as rrc

    canary = "CANARY-" + "mailbox-user"
    real = rrc.DryFakes

    class BadUser(real):
        def __init__(self, *a: Any, **k: Any) -> None:
            super().__init__(*a, **k)
            self.env = {**self.env, "REAL_IMAP_1_USER": canary + "\nbad"}

    monkeypatch.setattr(rrc, "DryFakes", BadUser)
    rc = rrc.main(["--dry-fakes", "--assume-yes"])
    out = capsys.readouterr()
    text = out.out + out.err
    assert rc == constants.EXIT_REFUSED == 2
    assert len(text.strip().splitlines()) == 1 and text.startswith("refused: ")
    assert "ImapSettingRefused" not in text and "ImapCountError" not in text and "Traceback" not in text
    assert canary not in text
