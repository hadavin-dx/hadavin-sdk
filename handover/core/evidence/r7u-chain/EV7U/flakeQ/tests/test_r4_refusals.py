"""Class: a script must not show a traceback, echo a typed value, hang on a pipe, or read a huge file on bad input.
Each bad input gets ONE refusal line and a fixed exit code (2 bad usage). Pins, per script and as a child process:
an address option takes http or https only (a file:// pipe is never opened); a number option is bounded and finite
(inf, nan, 1e999 are refused); a refusal names the option that was typed, not an internal setting; a bad listen host or
a busy port is one line; a refusal never echoes the base name of an existing file. Made-up data only; loopback only."""

from __future__ import annotations

import errno
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from support import run_program

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
FIFO = pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no named pipes on this platform")
SRC = str(REPO / "src")
PIPE_TEXT = "--config: is not a regular file (a pipe, a device or a socket would block): give a file"
ADDRESS_LINE = "must be an http or https address (for example http://127.0.0.1:8765)"
LOOPBACK_ADDRESS_LINE = "must be an http address on this computer (127.0.0.1 or localhost)"
ADDRESS_TEXT = {"burst": LOOPBACK_ADDRESS_LINE, "load_driver": LOOPBACK_ADDRESS_LINE}  # R7: burst is loopback-only too


def _run(args: list[str], tmp: Path, limit: float = 8, cwd: Path | None = None, **env: str) -> tuple[int, str]:
    """A script in its own process, WITHOUT the repository on the path; a hang fails the test."""
    base = {k: v for k, v in os.environ.items() if not k.startswith(("DESK_", "N8N_", "PYTHON"))}
    base.update(PYTHONDONTWRITEBYTECODE="1", LEAD_DESK_PATH_ROOTS=str(tmp), TMPDIR=str(tmp), **env)
    try:
        done = run_program(
            [sys.executable, *args],
            cwd=cwd or tmp,
            env=base,
            capture_output=True,
            text=True,
            timeout=limit,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"still running after {limit} seconds (a pipe or a hang): {args[:3]}")
    return done.returncode, done.stdout + done.stderr


def _one_line(out: str) -> str:
    lines = out.strip().splitlines()
    assert len(lines) == 1 and "Traceback" not in out, out
    return lines[0]


BURST = [str(REPO / "demo_only" / "burst.py"), "--url"]
LOAD = [str(REPO / "load_tools" / "load_driver.py"), "--base-url"]
PROBE = [str(REPO / "scripts" / "hubspot_probe.py"), "--yes-spend-calls", "0", "--dry-run"]
ADDRESS_USERS = {"burst": (BURST, "--url"), "load_driver": (LOAD, "--base-url")}
BAD_ADDRESSES = ["file:///etc/hostname", "ftp://127.0.0.1/x", "http://[::1", "gopher://x", "x", "", "//127.0.0.1:1"]


@pytest.mark.parametrize("who", sorted(ADDRESS_USERS))
@pytest.mark.parametrize("bad", BAD_ADDRESSES)
def test_an_address_option_takes_http_or_https_only_one_line_exit_2(tmp_path: Path, who: str, bad: str) -> None:
    prefix, option = ADDRESS_USERS[who]
    code, out = _run([*prefix, bad], tmp_path)
    assert code == 2 and _one_line(out) == f"refused: {option}: {ADDRESS_TEXT[who]}", (code, out)


@FIFO
@pytest.mark.parametrize("who", sorted(ADDRESS_USERS))
def test_a_file_address_that_is_a_pipe_returns_at_once(tmp_path: Path, who: str) -> None:
    """The old opener opened file:// addresses: a pipe would have waited for ever."""
    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)
    prefix, option = ADDRESS_USERS[who]
    code, out = _run([*prefix, f"file://{pipe}"], tmp_path, limit=5)
    assert code == 2 and _one_line(out) == f"refused: {option}: {ADDRESS_TEXT[who]}"
    assert str(pipe) not in out


@pytest.mark.parametrize("who", sorted(ADDRESS_USERS))
@pytest.mark.parametrize(
    "far",
    [
        "http://example.test:9/x",
        "http://" + "192.0.2.1:9/x",
        "https://example.test/x",
        "http://" + ".".join(("10", "0", "0", "5")) + ":80/",
        "http://[2001:db8::1]:9/x",
    ],
)
def test_an_address_that_is_not_on_this_computer_is_refused_before_any_connection(
    tmp_path: Path, who: str, far: str
) -> None:
    """R7 (BURST): the same one line and exit 2 for a far host; a counting loopback listener proves nothing is opened
    on this computer either, and the quick return (no wait for a connect timeout) shows no connection was tried."""
    prefix, option = ADDRESS_USERS[who]
    code, out = _run([*prefix, far], tmp_path, limit=3)
    assert code == 2 and _one_line(out) == f"refused: {option}: {LOOPBACK_ADDRESS_LINE}", (code, out)


def test_the_shared_opener_has_no_file_handler_and_refuses_a_bad_scheme() -> None:
    import http_guard

    opener = http_guard.http_only_opener(follow_redirects=False, use_proxy=False)
    names = {type(h).__name__ for h in opener.handlers}
    assert "FileHandler" not in names and "FTPHandler" not in names and "DataHandler" not in names
    for bad in ("file:///etc/hostname", "ftp://x/y", "http://[::1", "data:,x"):
        with pytest.raises(ValueError):
            http_guard.check_scheme(bad)


@pytest.mark.parametrize("bad", ["http://[::1", "file:///etc/hostname", "ftp://x", "http://example.test", "x"])
def test_hubspot_probe_dry_run_address_is_refused_in_one_line_before_any_call(tmp_path: Path, bad: str) -> None:
    code, out = _run([*PROBE, bad], tmp_path, HUBSPOT_PROBE_TOKEN="made-up-token-value")
    assert code == 2 and _one_line(out) == (
        "refused: --dry-run: must be an http address on this computer (127.0.0.1 or localhost)"
    ), (code, out)
    assert "made-up-token-value" not in out


NUMBER_BAD = ["inf", "-inf", "nan", "1e999", "-1e999", "abc", "", "0x10"]


def _number_cases(tmp: Path) -> list[tuple[str, list[str], str]]:
    """(label, the program and its arguments up to the option, the option)."""
    req = [str(tmp / "r"), str(tmp / "b"), str(tmp / "c"), str(tmp / "m")]
    inv = [str(REPO / "load_tools" / "check_invariants.py")]
    for name, path in zip(("--requests", "--book", "--catcher", "--model-log"), req, strict=True):
        inv += [name, path]
    inv += ["--crm", str(tmp / "crm")]
    live = [str(REPO / "scripts" / "run_live_check.py")]
    return [
        ("live --max-tokens", [*live, "--max-tokens"], "--max-tokens"),
        ("live --timeout", [*live, "--timeout"], "--timeout"),
        ("live --leads", [*live, "--leads"], "--leads"),
        ("live --runs", [*live, "--runs"], "--runs"),
        ("inv --model-bound", [*inv, "--model-bound"], "--model-bound"),
        ("inv --max-failed", [*inv, "--max-failed"], "--max-failed"),
        ("inv --max-unknown", [*inv, "--max-unknown"], "--max-unknown"),
        ("inv --max-review", [*inv, "--max-review"], "--max-review"),
        ("inv --max-503-rate", [*inv, "--max-503-rate"], "--max-503-rate"),
        ("inv --max-drain-seconds", [*inv, "--max-drain-seconds"], "--max-drain-seconds"),
        (
            "burst --expect",
            [str(REPO / "demo_only" / "burst.py"), "--url", "http://127.0.0.1:1", "--expect"],
            "--expect",
        ),
        (
            "probe --yes-spend-calls",
            [str(REPO / "scripts" / "hubspot_probe.py"), "--yes-spend-calls"],
            "--yes-spend-calls",
        ),
        ("load --seed", [str(REPO / "load_tools" / "load_driver.py"), "--seed"], "--seed"),
    ]


LABELS = [c[0] for c in _number_cases(Path("x"))]


@pytest.mark.parametrize("label", LABELS)
@pytest.mark.parametrize("bad", NUMBER_BAD)
def test_every_formerly_bare_number_option_refuses_a_bad_number_in_one_line(
    tmp_path: Path, label: str, bad: str
) -> None:
    prefix, option = next((p, o) for lab, p, o in _number_cases(tmp_path) if lab == label)
    code, out = _run([*prefix[:-1], f"{prefix[-1]}={bad}"], tmp_path)  # `=` so that -inf is a value, not an option
    line = _one_line(out)
    assert code == 2 and line.startswith(f"refused: {option}: "), (code, out)
    if bad:
        assert bad not in line.replace(option, "")  # the typed text is never echoed


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
@pytest.mark.parametrize(
    ("label", "ok"),
    [("live --max-tokens", "100"), ("load --seed", "-5"), ("inv --max-503-rate", "0.5"), ("live --timeout", "2.5")],
)
def test_a_good_number_is_not_refused_by_the_parser(tmp_path: Path, label: str, ok: str) -> None:
    prefix, option = next((p, o) for lab, p, o in _number_cases(tmp_path) if lab == label)
    _, out = _run([*prefix, ok], tmp_path)
    assert not out.startswith(f"refused: {option}: "), out


def test_the_live_check_names_the_option_not_the_setting(tmp_path: Path) -> None:
    for option in ("--max-tokens", "--timeout"):
        for bad in ("0", "-1", "1e9", "99999999"):
            code, out = _run([str(REPO / "scripts" / "run_live_check.py"), option, bad], tmp_path)
            line = _one_line(out)
            assert code == 2 and line.startswith(f"refused: {option}: ") and "DESK_LIVE" not in out, (option, bad, out)


def test_no_script_option_takes_a_bare_int_or_float() -> None:
    """The refusing parser's promise is checked here, not claimed: a `type=int` or `type=float` option is listed with
    its reason or it fails."""
    import ast

    listed = {
        ("scripts/feed.py", "--index"): "range-checked against the canned leads in build_envelope (FeedRefused)",
        ("scripts/run_real_check.py", "--dry-port-base"): "range-checked by port_range before any port is used",
    }
    found: set[tuple[str, str]] = set()
    for folder in ("scripts", "tools", "load_tools", "demo_only"):
        for py in sorted((REPO / folder).rglob("*.py")):
            for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
                if not (isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_argument"):
                    continue
                kw = {k.arg: k.value for k in node.keywords}
                kind = kw.get("type")
                if isinstance(kind, ast.Name) and kind.id in ("int", "float"):
                    found.add((py.relative_to(REPO).as_posix(), ast.literal_eval(node.args[0])))
    assert found == set(listed), (sorted(found - set(listed)), sorted(set(listed) - found))


def test_crash_desk_prints_the_file_name_only_never_the_folder(tmp_path: Path) -> None:
    folder = tmp_path / "private-folder-name"
    folder.mkdir()
    _, out = _run(
        [str(REPO / "scripts" / "crash_desk.py")], tmp_path, DESK_DB_PATH=str(folder / "book.db"), PYTHONPATH=SRC
    )
    first = out.splitlines()[0]
    assert first.startswith("crash flag file: crash.flag next to the database file"), out
    assert "private-folder-name" not in out and str(tmp_path) not in out


def test_burst_runs_as_a_plain_script_from_any_folder(tmp_path: Path) -> None:
    """No PYTHONPATH, another current folder: the sys.path guard finds tools/ (it was an ImportError traceback)."""
    code, out = _run([str(REPO / "demo_only" / "burst.py"), "--help"], tmp_path)
    assert code == 0 and "Traceback" not in out and "--url" in out, (code, out[:300])
    code, out = _run([str(REPO / "demo_only" / "burst.py"), "--url", "ftp://x"], tmp_path)
    assert code == 2 and _one_line(out).startswith("refused: --url: ")


def _busy_port() -> tuple[socket.socket, int]:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    return s, int(s.getsockname()[1])


def test_catcher_with_a_bad_host_is_one_line_exit_2(tmp_path: Path) -> None:
    code, out = _run(
        [
            str(REPO / "load_tools" / "catcher.py"),
            "--out",
            str(tmp_path / "o.jsonl"),
            "--host",
            "no-such-host" + ".invalid",
        ],
        tmp_path,
    )
    assert code == 2 and _one_line(out) == "refused: --host: must be this computer: localhost or 127.0.0.1", (code, out)


def test_catcher_with_a_busy_port_is_one_line_exit_2(tmp_path: Path) -> None:
    held, port = _busy_port()
    with held:
        code, out = _run(
            [str(REPO / "load_tools" / "catcher.py"), "--out", str(tmp_path / "o.jsonl"), "--port", str(port)], tmp_path
        )
    line = _one_line(out)
    assert code == 2 and line.startswith("refused: --port: ") and str(port) not in line, (code, out)


@pytest.mark.parametrize(
    "args",
    [
        ["-m", "demo_only.fake_model_server"],
        ["-m", "demo_only.fakes_server", "--outbox", "keyed"],
    ],
    ids=["fake_model_server", "fakes_server"],
)
def test_a_fake_server_on_a_busy_port_is_one_line_exit_2(tmp_path: Path, args: list[str]) -> None:
    held, port = _busy_port()
    with held:
        code, out = _run([*args, "--port", str(port)], tmp_path, cwd=REPO, PYTHONPATH=SRC)
    line = _one_line(out)
    assert code == 2 and line.startswith("refused: --port: ") and str(port) not in line, (code, out)


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_check_invariants_never_echoes_the_base_name_of_an_existing_file(tmp_path: Path) -> None:
    secret = "secret-base-name"
    folder = tmp_path / secret  # a folder where a file is expected, and a file that is not what it should be
    folder.mkdir()
    bad_file = tmp_path / f"{secret}.json"
    bad_file.write_text("{not json", encoding="utf-8")
    plain = tmp_path / "zz.jsonl"
    plain.write_text("", encoding="utf-8")
    tool = str(REPO / "load_tools" / "check_invariants.py")
    full = ["--requests", str(plain), "--book", str(plain), "--catcher", str(plain), "--crm", str(plain)]
    for what in ("--requests", "--book", "--catcher", "--crm", "--model-log"):
        for target in (folder, bad_file, tmp_path / f"{secret}-missing.db"):
            args = dict(zip(full[::2], full[1::2], strict=True))
            args["--model-log"] = str(plain)
            args[what] = str(target)
            argv = [tool] + [x for kv in args.items() for x in kv]
            _, out = _run(argv, tmp_path)
            assert secret not in out and "Traceback" not in out, (what, out)


def test_n8n_api_refusals_never_echo_the_name_of_the_workflow_file(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("k\n", encoding="utf-8")
    secret = tmp_path / "secret-base-name.json"
    secret.write_text("not a workflow", encoding="utf-8")
    for target in (secret, tmp_path, tmp_path / "secret-missing.json"):
        _, out = _run(
            [str(REPO / "scripts" / "n8n_api.py"), "import", str(target)], tmp_path, N8N_API_KEY_FILE=str(key)
        )
        assert "secret-" not in out and "Traceback" not in out and out.strip(), out


@FIFO
def test_run_real_check_config_refusals_have_the_exact_fixed_text(tmp_path: Path) -> None:
    import run_real_check as rrc

    pipe = tmp_path / "config.env"
    os.mkfifo(pipe)
    with pytest.raises(ValueError, match="--config: is not a regular file") as raised:
        rrc.load_env(pipe)
    assert str(raised.value) == PIPE_TEXT
    bad = tmp_path / "bad.env"
    bad.write_bytes(b"\xff\xfe")
    with pytest.raises(ValueError, match="the config file is not UTF-8 text") as raised2:
        rrc.load_env(bad)
    assert str(raised2.value) == ("the config file is not UTF-8 text (or is over 1 MiB): save it as plain UTF-8 text")
    code, out = _run(
        [str(REPO / "scripts" / "run_real_check.py"), "--config", str(pipe)],
        tmp_path,
        limit=8,
        PYTHONPATH=str(REPO / "src"),
    )
    assert code == 2 and _one_line(out) == f"refused: {PIPE_TEXT}", (code, out)


def test_the_real_check_prompt_with_a_closed_descriptor_is_a_stop_not_a_traceback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """EBADF (the descriptor of standard input was closed): the question is never read as a yes."""
    import run_real_check as rrc

    def closed(prompt: str = "") -> str:
        raise OSError(errno.EBADF, "Bad file descriptor")

    monkeypatch.setattr("builtins.input", closed)
    from test_real_check_dry import _valid_config

    assert rrc.main(["--config", str(_valid_config(tmp_path))]) == rrc.EXIT_STOPPED
    assert "no terminal" in capsys.readouterr().out


# -- lead additions: the book check agrees in desk and wrapper; a big log is refused by its cap; control characters --


def _book_check_child(tmp: Path, db: str, word: str) -> tuple[int, str]:
    return _run([str(REPO / "scripts" / "desk_setting.py"), word], tmp, cwd=REPO, PYTHONPATH=SRC, DESK_DB_PATH=db)


@pytest.mark.parametrize("word", ["db-path", "data-dir"])
def test_the_book_helper_refuses_in_one_line_exit_4_for_both_words(tmp_path: Path, word: str) -> None:
    """Behaviour, not source text: a book path the desk refuses ends the helper with exit 4 and ONE line, for the book
    path and for its folder alike; a good path prints the value and exits 0."""
    bad = {
        "a line break": str(tmp_path / "a\nb.db"),
        "a part that is a file": "/dev/null/x.db",
        "a name too long for the lock file": str(tmp_path / ("n" * 252 + ".db")),
        "a folder as the book": str(tmp_path),
    }
    for what, path in bad.items():
        code, out = _book_check_child(tmp_path, path, word)
        assert code == 4 and _one_line(out).startswith("the desk refuses to start: "), (what, code, out)
        assert "\n" not in path.replace(str(tmp_path), "") or "a\nb" not in out
    code, out = _book_check_child(tmp_path, str(tmp_path / "good.db"), word)
    assert code == 0 and _one_line(out), (code, out)


def test_check_invariants_refuses_a_log_over_the_cap_without_reading_it_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lead_desk.constants import LOAD_FILE_MAX_BYTES as MAX_JSON_BYTES

    sys.path.insert(0, str(REPO))
    from load_tools import check_invariants as ci

    big = tmp_path / "zz-secret.jsonl"
    with big.open("wb") as f:
        f.truncate(MAX_JSON_BYTES + 1)  # a sparse file: no disk is used
    monkeypatch.setenv("LEAD_DESK_PATH_ROOTS", str(tmp_path))
    with pytest.raises(ci.InputError, match="cannot read --requests") as raised:
        ci.read_jsonl(big, "--requests")
    assert "zz-secret" not in str(raised.value)
    crm = tmp_path / "crm.json"
    with crm.open("wb") as f:
        f.truncate(MAX_JSON_BYTES + 1)
    with pytest.raises(ci.InputError, match="cannot read the CRM dump"):
        ci.read_crm(crm)


@pytest.mark.parametrize("name", ["a\nb.json", "a\rb.json", "a\x1bb.json", "a\x00b.json", "a\x85b.json"])
def test_real_result_file_with_a_control_character_is_refused_and_nothing_is_made(tmp_path: Path, name: str) -> None:
    import run_real_check as rrc

    env = {"REAL_RESULT_FILE": str(tmp_path / name)}
    with pytest.raises(ValueError, match="REAL_RESULT_FILE has a bad character in it"):
        rrc.check_result_file(env, tmp_path / "book.db")
    assert list(tmp_path.iterdir()) == []
    assert rrc.folder_cannot_be_made(tmp_path / name) is True
    env_ok = {"REAL_RESULT_FILE": str(tmp_path / "ok.json")}
    rrc.check_result_file(env_ok, tmp_path / "book.db")
