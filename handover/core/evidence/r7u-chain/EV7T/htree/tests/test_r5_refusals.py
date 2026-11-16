"""Class (round 5): a script or a reader must not show a traceback, echo a typed value, hang on a pipe, read a huge
file, or listen or send somewhere unintended on a bad input. The answer is ONE refusal line and a fixed exit code (2 bad
usage, 3 desk unreachable, 4 bad setting). Made-up data only; loopback only; no real service."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import popen_program, run_program

from lead_desk.constants import LOAD_FILE_MAX_BYTES, LOOPBACK_HOSTS
from lead_desk.envnum import SettingRefused

REPO = Path(__file__).resolve().parents[1]

HTTP = "http" + "://"
PRIVATE_ADDRESS = ".".join(["10", "1", "2", "3"])  # an address of another computer
ALL_INTERFACES = ".".join(["0"] * 4)  # built from parts: the address that listens on every interface
FIFO = pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no named pipes on this platform")


def _run(args: list[str], tmp: Path, limit: float = 20, **env: str) -> tuple[int, str, str]:
    """A script in its own process; a hang fails the test. (code, stdout, stderr)."""
    base = {k: v for k, v in os.environ.items() if not k.startswith(("DESK_", "N8N_", "PYTHON"))}
    base.update(PYTHONDONTWRITEBYTECODE="1", LEAD_DESK_PATH_ROOTS=str(tmp), TMPDIR=str(tmp), **env)
    try:
        done = run_program(
            [sys.executable, *args],
            cwd=tmp,
            env=base,
            capture_output=True,
            text=True,
            timeout=limit,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"still running after {limit} seconds (a pipe or a hang): {args[:2]}")
    return done.returncode, done.stdout, done.stderr


def _one_line(out: str, err: str = "") -> str:
    text = (out + err).strip()
    lines = text.splitlines()
    assert len(lines) == 1 and "Traceback" not in text, text
    return lines[0]


# -- R4-01: a log of the largest run is read; one byte over the cap is refused --


def _log_row(i: int) -> str:
    row = {
        "request_id": f"ld-{i}",
        "intended_ts": 1_700_000_000.0 + i,
        "sent_ts": 1_700_000_000.5 + i,
        "done_ts": 1_700_000_001.0 + i,
        "door": "form",
        "scenario": ":".join(("rate", "100", "1000")),
        "attempts": [{"code": 200, "ts": 1_700_000_000.9 + i, "ms": 12.5}],
        "pad": "x" * 330,
    }
    return json.dumps(row)


def test_a_log_of_a_hundred_thousand_real_shaped_rows_is_read_and_one_byte_over_the_cap_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lead_desk.constants import MAX_JSON_BYTES
    from load_tools import check_invariants as ci

    monkeypatch.setenv("LEAD_DESK_PATH_ROOTS", str(tmp_path))
    log = tmp_path / "requests.jsonl"
    with log.open("w", encoding="utf-8") as f:
        for i in range(100_000):
            f.write(_log_row(i) + "\n")
    size = log.stat().st_size
    assert MAX_JSON_BYTES < size < LOAD_FILE_MAX_BYTES, size  # bigger than the small-file cap, inside the load cap
    assert len(ci.read_jsonl(log, "--requests")) == 100_000
    log.unlink()
    big = tmp_path / "big.jsonl"
    with big.open("wb") as f:
        f.truncate(LOAD_FILE_MAX_BYTES + 1)  # a sparse file: no disk is used
    with pytest.raises(ci.InputError, match="cannot read --requests"):
        ci.read_jsonl(big, "--requests")


# -- R4-02 / R4-03: every wrong shape of a field is one refusal line, never a traceback with exit 1 --

BAD_TIME_TEXT = [
    '"x"',
    "[1]",
    '{"a": 1}',
    "null",
    "-1",
    "true",
    "false",
    "1e13",
    "NaN",
    "Infinity",
    "-Infinity",
    "1e999",
]


@pytest.mark.parametrize("field", ["intended_ts", "sent_ts", "done_ts", "drained_ts"])
@pytest.mark.parametrize("text", BAD_TIME_TEXT)
def test_a_row_with_a_time_of_the_wrong_kind_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, text: str
) -> None:
    from load_tools import check_invariants as ci

    monkeypatch.setenv("LEAD_DESK_PATH_ROOTS", str(tmp_path))
    for reader, where in ((ci.read_jsonl, "log"), (ci.read_crm, "crm")):
        f = tmp_path / f"{where}.json"
        row = '{"request_id": "a", "lead_id": "a", "%s": %s}' % (field, text)
        f.write_text(row + "\n" if where == "log" else "[" + row + "]", encoding="utf-8")
        with pytest.raises(ci.InputError) as e:
            reader(f)
        message = str(e.value)
    # a number that is not finite never gets as far as the field check: the JSON reader refuses it first
    assert (field in message or "not JSON" in message) and text not in message


@pytest.mark.parametrize(
    "line",
    [
        '{"request_id": 5}',
        '{"request_id": null}',
        '{"request_id": ["a"]}',
        '{"attempts": "x"}',
        '{"attempts": [1]}',
        '{"attempts": null}',
        '{"attempts": {"a": 1}}',
        '{"intended_requests": 1.5}',
        '{"intended_requests": true}',
        '{"intended_requests": -1}',
        '{"intended_requests": 1000000000000}',
        '{"intended_requests": "5"}',
        '{"intended_requests": null}',
    ],
)
def test_every_other_field_of_the_wrong_kind_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, line: str
) -> None:
    from load_tools import check_invariants as ci

    monkeypatch.setenv("LEAD_DESK_PATH_ROOTS", str(tmp_path))
    f = tmp_path / "x.jsonl"
    f.write_text(line + "\n", encoding="utf-8")
    with pytest.raises(ci.InputError):
        ci.read_jsonl(f, "--requests")
    if "intended_requests" in line:
        facts = tmp_path / "facts.json"
        facts.write_text(line, encoding="utf-8")
        with pytest.raises(ci.InputError):
            ci._intended(facts)


@pytest.mark.parametrize("text", BAD_TIME_TEXT)
def test_a_drain_marker_with_a_bad_time_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    from load_tools import check_invariants as ci

    monkeypatch.setenv("LEAD_DESK_PATH_ROOTS", str(tmp_path))
    f = tmp_path / "drain.json"
    f.write_text('{"drained_ts": %s}' % text, encoding="utf-8")
    with pytest.raises(ci.InputError) as e:
        ci._drain_marker(f)
    assert text not in str(e.value) or text == "null"


def test_check_invariants_on_the_command_line_ends_with_exit_2_and_one_line_for_a_bad_row(tmp_path: Path) -> None:
    (tmp_path / "r.jsonl").write_text('{"request_id": "a", "intended_ts": 1e999}\n', encoding="utf-8")
    (tmp_path / "r.jsonl.facts.json").write_text('{"intended_requests": 1}', encoding="utf-8")
    names = {"--book": "b.sqlite3", "--catcher": "c.jsonl", "--crm": "m.json", "--model-log": "l.jsonl"}
    args = [str(REPO / "load_tools" / "check_invariants.py"), "--requests", str(tmp_path / "r.jsonl")]
    for option, name in names.items():
        (tmp_path / name).write_text("", encoding="utf-8")  # each input file must exist; the first one read is refused
        args += [option, str(tmp_path / name)]
    code, out, err = _run(args, tmp_path)
    assert code == 2, (code, out, err)
    assert (
        _one_line(out, err) == "INPUT ERROR: --requests line 1: intended_ts must be a time in seconds (a number from 0)"
    )


def test_an_unexpected_failure_inside_check_invariants_is_exit_2_with_the_fixed_line_never_exit_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from load_tools import check_invariants as ci

    def boom(_argv: object) -> int:
        raise RuntimeError("typed-secret-value")

    monkeypatch.setattr(ci, "_main", boom)
    assert ci.main([]) == 2
    seen = capsys.readouterr()
    assert seen.err.strip() == ci.UNEXPECTED_TEXT and "typed-secret-value" not in seen.out + seen.err


# -- R4-04 / R4-05: a listener is on this computer only --

BAD_HOSTS = [
    "",
    ALL_INTERFACES,
    "::",
    "example.com",
    "bad_label.test",
    "a" * 64 + ".test",
    "café",
    "127.0.0.1:80",
    ".".join(("1", "2", "3", "4")),
]


@pytest.mark.parametrize("host", BAD_HOSTS)
def test_the_catcher_refuses_a_host_that_is_not_this_computer_in_one_line(tmp_path: Path, host: str) -> None:
    code, out, err = _run(
        [str(REPO / "load_tools" / "catcher.py"), "--out", str(tmp_path / "o.jsonl"), "--host", host], tmp_path
    )
    assert code == 2 and _one_line(out, err) == "refused: --host: must be this computer: localhost or 127.0.0.1", (
        code,
        out,
        err,
    )
    assert not (tmp_path / "o.jsonl").exists()


def test_the_catcher_says_its_port_only_when_it_listens(tmp_path: Path) -> None:
    proc = popen_program(
        [sys.executable, str(REPO / "load_tools" / "catcher.py"), "--out", str(tmp_path / "o.jsonl"), "--port", "0"],
        cwd=tmp_path,
        env={**os.environ, "LEAD_DESK_PATH_ROOTS": str(tmp_path), "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    first: list[str] = []
    out = proc.stdout
    assert out is not None
    reader = threading.Thread(target=lambda: first.append(out.readline()), daemon=True)
    reader.start()
    reader.join(15)
    try:
        assert first and re.fullmatch(r"LISTENING \d+\n", first[0]), first
    finally:
        proc.terminate()
        proc.wait(10)
        out.close()


def test_the_stand_in_server_factories_refuse_a_host_that_is_not_this_computer() -> None:
    from demo_only.fake_model_server import make_model_server
    from demo_only.fakes_server import make_fakes_server

    for host in (ALL_INTERFACES, "", "::", "example.com", PRIVATE_ADDRESS):
        with pytest.raises(ValueError):
            make_model_server(host=host, port=0)
        with pytest.raises(ValueError):
            make_fakes_server("keyed", 0, "keyed", host=host or ALL_INTERFACES)
    srv = make_fakes_server("keyed", 0, "keyed", host="127.0.0.1")  # a loopback host still works
    srv.server_close()


# -- R4-06: the one address parser --

BAD_ADDRESSES = [
    "http://127.0.0.1:1@evil",
    HTTP + "user:pw@127.0.0.1:1",
    HTTP + "１２７.0.0.1:1",
    "http://127.0.0.1:0",
    "http://127.0.0.1:65536",
    "http://127.0.0.1:99999",
    "http://127.0.0.1:1 ",
    " http://127.0.0.1:1",
    HTTP + "127.0.0.1\n:1",
    HTTP + "127.0.0.1\x00:1",
    HTTP + "127.0.0.1\t:1",
    "http://" + "a" * 64 + ".test:1",
    HTTP + ":1",
    "http://[::1",
    "http://[::1]x:1",
    "http://127.0.0.1:1/\x7f",
    HTTP + "café.test:1",
    "http://127.0.0.1:abc",
    "file:///etc/hostname",
    "ftp://127.0.0.1/x",
    "127.0.0.1:1",
    "",
]


@pytest.mark.parametrize("bad", BAD_ADDRESSES)
def test_the_address_parser_refuses_each_bad_shape_with_a_fixed_text_that_never_repeats_it(bad: str) -> None:
    from tools.refusing_args import http_address

    for parse in (http_address(), http_address(LOOPBACK_HOSTS)):
        with pytest.raises(argparse.ArgumentTypeError) as e:
            parse(bad)
        text = str(e.value)
        for piece in ("evil", "pw", "caf", "abc", "etc/hostname"):
            assert piece not in text, text
        assert "\n" not in text


@pytest.mark.parametrize(
    "bad", ["http://" + ALL_INTERFACES + ":1", "http://[::]:1", HTTP + PRIVATE_ADDRESS + ":1", "http://example.test:1"]
)
def test_the_loopback_address_parser_refuses_an_address_of_another_computer(bad: str) -> None:
    from tools.refusing_args import http_address

    with pytest.raises(argparse.ArgumentTypeError):
        http_address(LOOPBACK_HOSTS)(bad)


@pytest.mark.parametrize("good", ["http://127.0.0.1:8765", "http://localhost:1", "http://[::1]:5", "http://127.0.0.1"])
def test_the_address_parser_accepts_loopback_addresses(good: str) -> None:
    from tools.refusing_args import http_address

    assert http_address(LOOPBACK_HOSTS)(good)


def test_the_address_parser_without_a_list_takes_a_named_host_but_a_list_refuses_it() -> None:
    from tools.refusing_args import http_address

    assert http_address()("https://example.test:8443/x")
    with pytest.raises(argparse.ArgumentTypeError):
        http_address(LOOPBACK_HOSTS)("https://example.test:8443/x")


# -- R4-09: one number reader, ASCII only --

BAD_NUMBERS = ["1_0", "٣٣", "１０", " 5", "5 ", "5\n", "nan", "inf", "-inf", "", "0x10", "1,5", "+-1"]


@pytest.mark.parametrize("text", BAD_NUMBERS)
def test_the_number_reader_refuses_what_python_would_accept(text: str) -> None:
    from lead_desk.envnum import read_number

    for cast in (int, float, Decimal):
        with pytest.raises(ValueError):
            read_number(text, cast)


@pytest.mark.parametrize("text", ["5", "+5", "-5", "007"])
def test_the_number_reader_takes_plain_ascii_integers(text: str) -> None:
    from lead_desk.envnum import read_number

    assert read_number(text, int) == int(text)
    assert read_number("1.5e2", float) == 150.0 and read_number("0.25", Decimal) == Decimal("0.25")


@pytest.mark.parametrize("text", BAD_NUMBERS)
def test_every_option_that_takes_a_number_uses_that_reader(text: str) -> None:
    import run_live_check as rlc

    from tools.refusing_args import bounded_float, bounded_int

    with pytest.raises(argparse.ArgumentTypeError):
        bounded_int(0, 100)(text)
    with pytest.raises(argparse.ArgumentTypeError):
        bounded_float(0.0, 100.0)(text)
    with pytest.raises(argparse.ArgumentTypeError):
        rlc._usd_arg(text)
    with pytest.raises(argparse.ArgumentTypeError):
        rlc._model_arg(f"m-a={text},2")


@pytest.mark.parametrize(
    "scenario",
    [
        "burst:1_0",
        "burst:٣",
        "rate:1_0:5",
        ":".join(("rate", "5", "1_0")),
        "burst: 5",
        "dupmix:1_0:0.5",
        "burst:nan",
        "rate:inf:1",
    ],
)
def test_a_scenario_with_an_odd_number_is_refused(scenario: str) -> None:
    from load_tools.load_driver import parse_scenario

    with pytest.raises(ValueError):
        parse_scenario(scenario)


@pytest.mark.parametrize("url", ["http://127.0.0.1:0", "http://127.0.0.1:99999", "http://127.0.0.1:abc"])
def test_a_setting_address_with_a_bad_port_is_a_setting_refusal(url: str) -> None:
    from urllib.parse import urlsplit

    from lead_desk.envnum import check_url_port

    with pytest.raises(SettingRefused):
        check_url_port("DESK_LIVE_BASE_URL", urlsplit(url))


# -- R4-10: every typed value is judged before "no terminal" and before the cost line --


def _live(tmp: Path, *extra: str) -> list[str]:
    (tmp / "k").write_text("made-up-key-" + "x" * 12 + "\n", encoding="utf-8")
    return [
        str(REPO / "scripts" / "run_live_check.py"),
        *("--key-file", str(tmp / "k")),
        *("--ledger", str(tmp / "ledger.jsonl")),
        *("--base-url", "http://127.0.0.1:1"),
        *("--cap-total", "3", "--price-date", "2026-01-01", "--model", "m-a=1,2", "--effort", "low"),
        *extra,
    ]


@pytest.mark.parametrize("cap", ["abc", "1_0", "nan", "-1", "0", ""])
def test_a_bad_cap_is_refused_in_one_line_before_the_no_terminal_line(tmp_path: Path, cap: str) -> None:
    code, out, err = _run(_live(tmp_path, "--cap-run", cap), tmp_path)
    assert code == 2 and _one_line(out, err).startswith("refused: --cap-run: "), (code, out, err)
    assert "terminal" not in out + err


@pytest.mark.parametrize("port", ["0", "99999", "65536"])
def test_a_base_url_with_a_bad_port_is_refused_before_the_cost_line(tmp_path: Path, port: str) -> None:
    args = _live(tmp_path, "--cap-run", "1")
    args[args.index("--base-url") + 1] = f"http://127.0.0.1:{port}"
    code, out, err = _run(args, tmp_path)
    assert code == 2 and _one_line(out, err).startswith("refused: --base-url: "), (code, out, err)


@FIFO
@pytest.mark.parametrize("which", ["key", "ledger"])
def test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line(tmp_path: Path, which: str) -> None:
    args = _live(tmp_path, "--cap-run", "1")
    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)
    args[args.index("--key-file" if which == "key" else "--ledger") + 1] = str(pipe)
    code, out, err = _run(args, tmp_path, limit=10)
    assert code == 2, (code, out, err)
    line = _one_line(out, err)
    assert line.startswith("refused: --key-file: " if which == "key" else "refused: --ledger: "), line
    assert "expected MAXIMUM" not in out and str(pipe) not in line


# -- R4-12: no Python class name in a refusal line --


def test_the_real_check_refusal_line_has_no_class_name(tmp_path: Path) -> None:
    code, out, err = _run(
        [str(REPO / "scripts" / "run_real_check.py"), "--config", str(tmp_path / "nope.env")], tmp_path
    )
    line = _one_line(out, err)
    assert code != 0 and line.startswith("refused: ")
    assert not re.search(r"\b[A-Z][A-Za-z]+(Refused|Error|Exception)\b", line), line


# -- R4-13: the n8n helper judges its command line first; every reply read has a limit --


@pytest.mark.parametrize("words", [[], ["bogus"], ["import"], ["activate"], ["deactivate"], ["frobnicate", "x"]])
def test_n8n_api_with_a_bad_command_line_is_usage_and_exit_2_without_a_key_file(
    tmp_path: Path, words: list[str]
) -> None:
    code, out, err = _run([str(REPO / "scripts" / "n8n_api.py"), *words], tmp_path)
    assert code == 2 and _one_line(out, err).startswith("usage: python scripts/n8n_api.py"), (code, out, err)


def test_a_reply_is_read_up_to_the_limit_and_one_byte_more_is_refused() -> None:
    import io

    from http_guard import ReplyTooBig, read_reply

    from lead_desk.constants import SCRIPT_REPLY_MAX_BYTES

    assert read_reply(io.BytesIO(b"x" * SCRIPT_REPLY_MAX_BYTES)) == b"x" * SCRIPT_REPLY_MAX_BYTES
    with pytest.raises(ReplyTooBig):
        read_reply(io.BytesIO(b"x" * (SCRIPT_REPLY_MAX_BYTES + 1)))
    assert read_reply(io.BytesIO(b"abc"), 3) == b"abc"
    with pytest.raises(ReplyTooBig):
        read_reply(io.BytesIO(b"abcd"), 3)


def test_no_script_reads_a_reply_without_a_limit() -> None:
    """Every helper that talks to a service reads the answer through read_reply (a bare `.read()` is a hit)."""
    for name in ("feed.py", "n8n_api.py", "run_real_check.py"):
        text = (REPO / "scripts" / name).read_text(encoding="utf-8")
        assert "read_reply(" in text, name
        assert not re.search(r"\b(r|reply|resp|response|e)\.read\(\)", text), name


# -- R4-14: the id prefix and the unreachable desk --


@pytest.mark.parametrize("bad", ["", "-a", "a-", "a b", "a/b", "a\n", "café", "a" * 41, ".x", "x.", "a:b"])
def test_an_id_prefix_that_the_desk_would_refuse_is_refused_up_front(bad: str) -> None:
    from load_tools.load_driver import build_schedule, id_prefix

    with pytest.raises(argparse.ArgumentTypeError):
        id_prefix(bad)
    with pytest.raises(ValueError):
        build_schedule("burst:2", 0.0, bad, 1)


@pytest.mark.parametrize("good", ["ld", "run-7", "a.b_c", "x" * 40])
def test_an_id_prefix_of_the_allowed_form_is_accepted(good: str) -> None:
    from load_tools.load_driver import id_prefix

    assert id_prefix(good) == good


def test_a_run_in_which_every_try_was_a_connection_error_is_unreachable() -> None:
    from load_tools.load_driver import desk_unreachable

    refused = {"attempts": [{"code": None}, {"code": None}]}
    answered = {"attempts": [{"code": None}, {"code": 200}]}
    assert desk_unreachable([refused, refused]) is True
    assert desk_unreachable([refused, answered]) is False
    assert desk_unreachable([]) is False
    assert desk_unreachable([{"attempts": []}]) is False


def test_the_load_driver_ends_with_exit_3_and_one_line_when_the_desk_is_not_there(tmp_path: Path) -> None:
    """A real run: nothing listens on the port; since r7d the driver looks once before it starts any worker and ends
    at once (the mid-run case, a desk that hangs up, is tested in test_r7d_findings.py)."""
    holder = socket.socket()
    holder.bind(("127.0.0.1", 0))
    port = holder.getsockname()[1]
    holder.close()  # the port is free now: a connect is refused
    code, out, err = _run(
        [
            str(REPO / "load_tools" / "load_driver.py"),
            "--base-url",
            f"http://127.0.0.1:{port}",
            "--scenario",
            "burst:1",
            "--log",
            str(tmp_path / "l.jsonl"),
        ],
        tmp_path,
        limit=170,
    )
    assert code == 3, (code, out, err)
    assert (
        _one_line(out, err)
        == "ERROR: the desk cannot be reached: nothing answers at that address (is it running?); no request was sent"
    )


# -- R4-15: start_all.sh with a bad mode is exit 2 (the test is in test_reset_scripts.py) --

# -- F5: a TLS context that does not verify is refused --


def _unverified(kind: str) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if kind == "none":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    elif kind == "no-name":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


@pytest.mark.parametrize("kind", ["none", "no-name"])
def test_require_verifying_refuses_a_context_that_does_not_check_the_server(kind: str) -> None:
    from lead_desk.tls_trust import CaFileRefused, require_verifying

    with pytest.raises(CaFileRefused):
        require_verifying(_unverified(kind), "DESK_SMTPP_CA_FILE")
    good = _unverified("good")
    assert require_verifying(good, "DESK_SMTPP_CA_FILE") is good


@pytest.mark.parametrize("kind", ["none", "no-name"])
def test_the_mail_sender_refuses_a_context_that_does_not_check_the_server(tmp_path: Path, kind: str) -> None:
    from lead_desk.smtp_provider import ProviderSettings, SmtpProviderOutbox

    pw = tmp_path / "pw"
    pw.write_text("made-up-password-value\n", encoding="utf-8")
    settings = ProviderSettings(
        "localhost", 1, "u", pw, "sender@example.test", ("a@example.test",), 5, timeout_seconds=1.0
    )
    with pytest.raises(SettingRefused):
        SmtpProviderOutbox(settings, ssl_context=_unverified(kind))


@pytest.mark.parametrize("kind", ["none", "no-name"])
def test_the_mailbox_counter_refuses_a_context_that_does_not_check_the_server_before_it_connects(
    tmp_path: Path, kind: str
) -> None:
    from lead_desk.imap_count import ImapCountError, ImapSettings, counts_by_key

    pw = tmp_path / "pw"
    pw.write_text("made-up-password-value\n", encoding="utf-8")
    settings = ImapSettings("localhost", "u", pw, port=1, ssl_context=_unverified(kind))
    with pytest.raises(ImapCountError) as e:
        counts_by_key(settings, "p")
    assert "ssl_context" in str(e.value)


# -- F1 / F2: the key and password readers --


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\n",
        b"short\n",
        b"two\nlines-of-text\n",
        b"has a space in it\n",
        b"ctrl\x01char-in-key\n",
        "utf16-text-key".encode("utf-16"),
        b"\xff\xfe-bad",
    ],
)
def test_the_secret_reader_refuses_each_bad_shape_with_a_fixed_text_that_never_repeats_the_content(
    tmp_path: Path, raw: bytes
) -> None:
    from lead_desk.regfile import FileRefused, read_secret_line

    f = tmp_path / "secret-name.txt"
    f.write_bytes(raw)
    with pytest.raises(FileRefused) as e:
        read_secret_line(f, "key", "key")
    assert "secret-name" not in str(e.value) and "line" not in str(e.value).replace("one line", "").replace(
        "more than one line", ""
    )


def test_the_secret_reader_accepts_one_line_with_a_byte_order_mark_and_a_spaced_password_when_asked(
    tmp_path: Path,
) -> None:
    from lead_desk.regfile import read_secret_line

    f = tmp_path / "k"
    f.write_bytes(b"\xef\xbb\xbfmade-up-key-value\r\n")
    assert read_secret_line(f, "key", "key") == "made-up-key-value"
    g = tmp_path / "p"
    g.write_text("made up pass word\n", encoding="utf-8")
    assert read_secret_line(g, "password", "password", spaced=True) == "madeuppassword"


@FIFO
def test_the_secret_reader_does_not_wait_on_a_pipe(tmp_path: Path) -> None:
    from lead_desk.regfile import FileRefused, read_secret_line

    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)
    with pytest.raises(FileRefused):
        read_secret_line(pipe, "key", "key")


def test_the_settings_text_says_the_named_authority_file_is_the_only_trusted_source() -> None:
    text = (REPO / "docs" / "settings.md").read_text(encoding="utf-8")
    assert "extra trusted certificate authorities" not in text
    assert "are the ONLY ones trusted" in text and "is NOT used" in text
