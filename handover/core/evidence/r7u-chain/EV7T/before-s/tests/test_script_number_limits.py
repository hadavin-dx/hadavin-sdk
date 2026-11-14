"""Class: a number typed on a command line (a port, a count, a scenario) must end in ONE fixed refusal line (exit 2)
when it is not a usable whole number or is out of range, never in a Python traceback (OverflowError from a port of
99999, ValueError from `Barrier(0)`, `int(nan)`, `int(inf)`) and never with the typed text printed back. The limits
come from lead_desk/constants.py. One shared type, `tools.refusing_args.bounded_int`, is used by every script; one case
per script. Each script runs in its own process with a 10 second limit; made-up data only; no network."""

from __future__ import annotations

import os
import subprocess  # noqa: S404
import sys
from pathlib import Path
from typing import Any

import pytest
from support import run_program

from lead_desk import constants, regfile
from load_tools import load_driver
from tools.refusing_args import BOUNDED_INT_TEXT, bounded_int

REPO = Path(__file__).resolve().parents[1]
BAD_PORTS = ["99999", "65536", "-5", "abc", "1e3", "", "٣" * 10, "9" * 5000]
PORT_TEXT = f"refused: --port: must be a whole number from 0 to {constants.PORT_MAX}"


def _run(args: list[str], *, cwd: Path = REPO, with_pythonpath: bool = True) -> tuple[int, str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("DESK_", "N8N_", "PYTHON"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if with_pythonpath:
        env["PYTHONPATH"] = str(REPO / "src") + os.pathsep + str(REPO)
    try:
        done = run_program(
            [sys.executable, *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("the script did not end: it started to serve or to wait instead of refusing")
    return done.returncode, done.stdout, done.stderr


def _assert_one_refusal(code: int, out: str, err: str, line: str, typed: str) -> None:
    assert code == constants.EXIT_REFUSED, (code, out, err)
    assert out.splitlines() == [line], (out, err)
    assert "Traceback" not in out + err and "Error" not in out + err, (out, err)
    if typed and len(typed) < 100 and not typed.lstrip("-").isdigit():  # a short number may be part of a limit
        assert typed not in out + err, "the typed text was printed back"


def test_the_constants_hold_the_limits_and_the_exit_codes_once() -> None:
    assert constants.EXIT_REFUSED == 2 and constants.EXIT_UNREACHABLE == 3 and constants.EXIT_STOPPED == 6
    assert constants.EXIT_CHECK_FAILED == 1 and constants.EXIT_BAD_SETTING_OR_PATH == 4
    assert constants.PORT_MAX == 65535 and constants.FAKE_MODEL_DEFAULT_PORT == 48767
    for name in ("LOAD_TOTAL_MAX", "LOAD_RATE_MAX", "LOAD_SECONDS_MAX", "LOAD_WORKERS_MAX", "LOAD_THREADS_MAX"):
        assert getattr(constants, name) > 0, name


# -- the shared type ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad", ["", " ", "abc", "1.5", "1e3", "nan", "inf", "-1", "0", "11", "9" * 5000, "٣٣٣٣٣٣٣٣", " 5 ", "1_0"]
)
def test_bounded_int_refuses_everything_outside_the_range_with_the_fixed_text(bad: str) -> None:
    import argparse

    parse = bounded_int(1, 10)
    with pytest.raises(argparse.ArgumentTypeError) as seen:
        parse(bad)
    assert str(seen.value) == "must be a whole number from 1 to 10" and BOUNDED_INT_TEXT.fullmatch(str(seen.value))


@pytest.mark.parametrize("good", ["1", "10", "+3", "007"])
def test_bounded_int_accepts_the_edges(good: str) -> None:
    assert 1 <= bounded_int(1, 10)(good) <= 10


# -- one case per script ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("bad", BAD_PORTS)
@pytest.mark.parametrize(
    "script",
    [
        ["load_tools/catcher.py", "--out", "{out}"],
        ["-m", "demo_only.fakes_server", "--outbox", "keyed"],
        ["-m", "demo_only.fake_model_server"],
    ],
    ids=["catcher", "fakes_server", "fake_model_server"],
)
def test_a_bad_port_is_one_refusal_line_in_every_server_script(tmp_path: Path, script: list[str], bad: str) -> None:
    args = [a.replace("{out}", str(tmp_path / "mail.jsonl")) for a in script]
    code, out, err = _run([*args, f"--port={bad}"])
    _assert_one_refusal(code, out, err, PORT_TEXT, bad)


@pytest.mark.parametrize("bad", ["0", "-1", "abc", "1.5", str(constants.BURST_N_MAX + 1), "9" * 5000])
def test_a_bad_burst_count_is_one_refusal_line_and_never_barrier_zero(bad: str) -> None:
    code, out, err = _run(
        ["-m", "demo_only.burst", "--url", "http://127.0.0.1:1/", "--email", "a@example.com", "--ref-prefix", "p"]
        + ["--source", "form", f"--n={bad}"]
    )
    _assert_one_refusal(code, out, err, f"refused: --n: must be a whole number from 1 to {constants.BURST_N_MAX}", bad)


@pytest.mark.parametrize(
    ("option", "bad", "high"),
    [
        ("--workers", "0", constants.LOAD_WORKERS_MAX),
        ("--workers", "-3", constants.LOAD_WORKERS_MAX),
        ("--workers", str(constants.LOAD_WORKERS_MAX + 1), constants.LOAD_WORKERS_MAX),
        ("--threads", "0", constants.LOAD_THREADS_MAX),
        ("--threads", "-1", constants.LOAD_THREADS_MAX),
        ("--threads", str(constants.LOAD_THREADS_MAX + 1), constants.LOAD_THREADS_MAX),
        ("--threads", "many", constants.LOAD_THREADS_MAX),
    ],
)
def test_a_bad_worker_or_thread_count_is_one_refusal_line(tmp_path: Path, option: str, bad: str, high: int) -> None:
    code, out, err = _run(
        ["-m", "load_tools.load_driver", "--base-url", "http://127.0.0.1:1", "--scenario", "burst:3"]
        + ["--log", str(tmp_path / "l.jsonl"), f"{option}={bad}"]
    )
    _assert_one_refusal(code, out, err, f"refused: {option}: must be a whole number from 1 to {high}", bad)
    assert not list(tmp_path.iterdir()), "something was written before the refusal"


# -- the scenario words ------------------------------------------------------------------------------------------------

NOT_FINITE = ["burst:nan", "burst:inf", "burst:-inf", "burst:infinity", "rate:nan:1", "rate:5:inf", "rate:inf:inf"]
NOT_FINITE += ["dupmix:nan:0.5", "dupmix:10:nan", "dupmix:inf:0.5", "dupmix:10:0.5:nan", "dupmix:10:0.5:inf"]
TOO_BIG = [
    f"burst:{constants.LOAD_TOTAL_MAX + 1}",
    "burst:1e999",
    "burst:1e300",
    f"rate:{constants.LOAD_RATE_MAX * 2}:1",
    f"rate:1:{constants.LOAD_SECONDS_MAX * 2}",
    "rate:1e200:1e200",
    "rate:100000:100000",
    f"dupmix:{constants.LOAD_TOTAL_MAX + 1}:0.5",
    "dupmix:1e300:0.5",
    "dupmix:10:0.5:1e300",
    "dupmix:100000:0.5:0.0001",
]
EMPTY = ["burst:0.5", "rate:0.1:1", "rate:1e-300:1", "dupmix:0.5:0.5"]


@pytest.mark.parametrize("scenario", NOT_FINITE + TOO_BIG + EMPTY)
def test_a_scenario_with_a_number_that_cannot_be_used_is_a_value_error_with_a_fixed_text(scenario: str) -> None:
    with pytest.raises(ValueError) as seen:  # not OverflowError, not a traceback of int(nan) / int(inf)
        load_driver.parse_scenario(scenario)
    assert type(seen.value) is ValueError and scenario not in str(seen.value)
    with pytest.raises(ValueError):
        load_driver.build_schedule(scenario, 0.0, "p", 1)


@pytest.mark.parametrize("scenario", NOT_FINITE + TOO_BIG + EMPTY)
def test_the_load_driver_ends_a_bad_scenario_with_one_line_and_exit_2(tmp_path: Path, scenario: str) -> None:
    code, out, err = _run(
        ["-m", "load_tools.load_driver", "--base-url", "http://127.0.0.1:1", f"--scenario={scenario}"]
        + ["--log", str(tmp_path / "l.jsonl")]
    )
    assert code == constants.EXIT_REFUSED and out == "", (code, out, err)
    assert len(err.splitlines()) == 1 and err.startswith("ERROR: bad scenario"), err
    assert "Traceback" not in err and scenario not in err
    assert not list(tmp_path.iterdir())


def test_the_edges_of_the_limits_are_accepted() -> None:
    assert load_driver.parse_scenario(f"burst:{constants.LOAD_TOTAL_MAX}")[0] == "burst"
    assert load_driver.parse_scenario("burst:1")[1] == [1.0]
    assert load_driver.parse_scenario(f"rate:{constants.LOAD_RATE_MAX}:1")[0] == "rate"
    assert load_driver.parse_scenario(f"rate:1:{constants.LOAD_SECONDS_MAX}")[0] == "rate"
    assert load_driver.parse_scenario(":".join(("dupmix", "10", "0", "1")))[0] == "dupmix"
    assert len(load_driver.build_schedule("burst:7", 0.0, "p", 1)) == 7
    assert len(load_driver.build_schedule(":".join(("rate", "10", "2")), 0.0, "p", 1)) == 20


# -- the model stand-in: starts without PYTHONPATH, reads a key file with a cap --------------------------------------


def test_the_model_stand_in_starts_without_pythonpath_like_the_catcher(tmp_path: Path) -> None:
    """`python -m demo_only.fake_model_server` from the repository folder, with no PYTHONPATH at all, must reach its own
    argument check (the one-line refusal), not die with ModuleNotFoundError on `lead_desk`."""
    code, out, err = _run(["-m", "demo_only.fake_model_server", "--port=99999"], with_pythonpath=False)
    assert "ModuleNotFoundError" not in err and "Traceback" not in err, err
    assert code == constants.EXIT_REFUSED and out.splitlines() == [PORT_TEXT], (out, err)
    code, out, err = _run(
        ["load_tools/catcher.py", "--out", str(tmp_path / "m"), "--port=99999"], with_pythonpath=False
    )
    assert code == constants.EXIT_REFUSED and out.splitlines() == [PORT_TEXT], (out, err)


class _Started(Exception):
    """Raised by a stand-in for make_model_server: the key file was accepted and the server would start."""


def _main_with_key(monkeypatch: pytest.MonkeyPatch, key_file: Path) -> str | None:
    from demo_only import fake_model_server as fms

    seen: list[str | None] = []

    def start(**kw: object) -> None:
        seen.append(kw["key"])  # type: ignore[arg-type]
        raise _Started

    monkeypatch.setattr(fms, "make_model_server", start)
    monkeypatch.setattr(sys, "argv", ["fake_model_server", "--port", "0", "--key-file", str(key_file)])
    with pytest.raises(_Started):
        fms.main()
    return seen[0]


def test_the_model_stand_in_reads_at_most_the_key_file_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from demo_only import fake_model_server as fms

    monkeypatch.chdir(tmp_path)
    cap = constants.SECRET_FILE_MAX_BYTES
    ok = tmp_path / "ok.key"
    ok.write_bytes(b"k" * cap)  # exactly the cap: accepted
    assert _main_with_key(monkeypatch, ok) == "k" * cap
    big = tmp_path / "big.key"
    big.write_bytes(b"k" * (3 * 1024 * 1024))  # three megabytes: refused, and never read whole
    reads: list[int] = []
    real: Any = regfile.open_regular

    class Counting:
        """The opened key file; every read size is noted (the one secret reader asks for the cap plus one byte)."""

        def __init__(self, path: object) -> None:
            self.f = real(path)

        def __enter__(self) -> Counting:
            return self

        def __exit__(self, *a: object) -> None:
            self.f.close()

        def read(self, n: int) -> bytes:
            reads.append(n)
            return self.f.read(n)

    monkeypatch.setattr(regfile, "open_regular", Counting)
    monkeypatch.setattr(fms, "make_model_server", lambda **kw: pytest.fail("a key file over the cap was accepted"))
    monkeypatch.setattr(sys, "argv", ["fake_model_server", "--port", "0", "--key-file", str(big)])
    with pytest.raises(SystemExit) as seen:
        fms.main()
    assert seen.value.code == constants.EXIT_BAD_SETTING_OR_PATH and reads == [cap + 1]
    assert (
        capsys.readouterr().out.strip() == "refused: --key-file: the key file is too large: it must hold only the key"
    )


def _desk_setting(word: str, env: dict[str, str]) -> tuple[int, str]:
    import sys

    base = {k: v for k, v in os.environ.items() if not k.startswith("DESK_")}
    r = run_program(
        [sys.executable, str(REPO / "scripts" / "desk_setting.py"), word],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env={**base, "PYTHONPATH": str(REPO / "src"), **env},
    )
    return r.returncode, r.stdout + r.stderr


def test_the_book_path_is_never_printed_when_it_is_a_folder_or_a_pipe(tmp_path: Path) -> None:
    for word in ("db-path", "data-dir"):
        code, out = _desk_setting(word, {"DESK_DB_PATH": str(tmp_path)})
        assert code == 4 and out.startswith("the desk refuses to start:") and str(tmp_path) not in out, (word, out)
    code, out = _desk_setting("db-path", {"DESK_DB_PATH": str(tmp_path / "new.sqlite3")})
    assert code == 0 and out.strip() == str(tmp_path / "new.sqlite3")


def test_a_port_and_an_effort_with_spaces_around_them_are_treated_alike(tmp_path: Path) -> None:
    code, out = _desk_setting("port", {"DESK_PORT": " 5 "})
    assert (code, out.strip()) == (0, "5")  # spaces around a value are harmless, for every setting
    from lead_desk.config import _live_from_env

    env = {
        "DESK_LIVE_MODEL": "m",
        "DESK_LIVE_KEY_FILE": str(tmp_path / "k"),
        "DESK_LIVE_LEDGER_PATH": str(tmp_path / "l"),
        "DESK_LIVE_PRICE_DATE": "2026-01-01",
        "DESK_LIVE_RUN_ID": "r",
        "DESK_LIVE_PRICE_IN_PER_MTOK": "1",
        "DESK_LIVE_PRICE_OUT_PER_MTOK": "1",
        "DESK_LIVE_CAP_RUN_USD": "1",
        "DESK_LIVE_CAP_TOTAL_USD": "1",
        "DESK_LIVE_EFFORT": " low ",
    }
    try:
        assert _live_from_env(env).effort == "low"
    except KeyError as e:  # a name this made-up set lacks: the test needs the real list
        raise AssertionError(f"test setup lacks {e}") from None
