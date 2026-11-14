"""Command-line refusals of the check scripts (class: text typed by the person is echoed back, or an exception name is
shown, instead of a fixed refusal line).

* a fake key typed in the wrong place (the value of a whole-number option, a stray word, an unknown option name, an
  abbreviated option, a value on a flag, a wrong choice) is never printed by scripts/run_real_check.py,
  scripts/run_live_check.py, scripts/feed.py or scripts/hubspot_probe.py (all four share scripts/refusing_args.py);
* the exact refusal line of each bad port, behaviour word, price date, effort word and repeated model id;
* every refusal comes before the start question.
Each script runs as its own program, with no network (`unshare -n` when the machine allows it); made-up data only."""

from __future__ import annotations

import argparse
import os
import re
import subprocess  # noqa: S404
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_real_check as rrc
from support import run_program

from lead_desk.constants import LIVE_EFFORTS, PORT_MAX

REPO = Path(__file__).resolve().parents[1]

FAKE_KEY = "sk-" + "ant-" + "FAKE" + "0123456789"  # a made-up key, built from parts
ONE_LINE = re.compile(r"refused: [^\n]+\n")
NO_NETWORK = ["unshare", "-n"]


def _prefix() -> list[str]:
    try:
        ok = run_program([*NO_NETWORK, "true"], capture_output=True, timeout=30, check=False).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        ok = False
    return NO_NETWORK if ok else []  # the refusals come before any network use either way


PREFIX = _prefix()


def run_script(name: str, *args: str) -> tuple[int, str, str]:
    """Run scripts/<name> as its own program with no standard input (not a terminal): (exit code, stdout, stderr)."""
    return _run_command([f"scripts/{name}"], *args)


def _run_command(command: list[str], *args: str) -> tuple[int, str, str]:
    """Run a program of this repository (a file path or `-m module`), the same way."""
    r = run_program(
        [*PREFIX, sys.executable, *command, *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO,
        env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(REPO / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    return r.returncode, r.stdout, r.stderr


LIVE_BASE = [
    *("--key-file", "k"),
    *("--ledger", "l"),
    *("--base-url", "http://127.0.0.1:1"),
    *("--cap-run", "1", "--cap-total", "3"),
    *("--price-date", "2026-01-01", "--model", "m-a=1,2", "--effort", "low"),
]


def _live(**over: str) -> list[str]:
    """A good live-check command line (nothing is read: every case here is refused first) with options replaced."""
    args = list(LIVE_BASE)
    for key, value in over.items():
        option = "--" + key.replace("_", "-")
        args[args.index(option) + 1] = value
    return args


# every program with a command line: (how to start it, arguments that are good on their own, a whole-number option or
# a number option of it, a flag of it, the unique start of that option's name). Each case below puts the fake key where
# it does not belong, so every refusal is read for the key.
PROGRAMS: dict[str, tuple[list[str], list[str], str, str | None]] = {
    "real": (["scripts/run_real_check.py"], [], "--dry-port-base", "--dry-fakes"),
    "live": (["scripts/run_live_check.py"], LIVE_BASE, "--max-tokens", "--assume-yes"),
    "feed": (["scripts/feed.py"], ["--source", "form"], "--index", "--all"),
    "probe": (["scripts/hubspot_probe.py"], [], "--yes-spend-calls", "--plan"),
    "catcher": (["load_tools/catcher.py"], ["--out", "o"], "--port", None),
    "invariants": (
        ["load_tools/check_invariants.py"],
        [*("--requests", "a", "--book", "b", "--catcher", "c", "--crm", "d", "--model-log", "e")],
        "--max-failed",
        "--no-require-comparable",
    ),
    "driver": (
        ["load_tools/load_driver.py"],
        [*("--base-url", "http://127.0.0.1:1", "--scenario", "burst:1", "--log", "l")],
        "--workers",
        None,
    ),
    "fakes": (["-m", "demo_only.fakes_server"], ["--outbox", "keyed"], "--port", None),
    "model": (["-m", "demo_only.fake_model_server"], [], "--port", None),
    "burst": (
        ["-m", "demo_only.burst"],
        [*("--url", "http://127.0.0.1:1", "--email", "e", "--ref-prefix", "p", "--source", "form", "--n", "1")],
        "--expect",
        "--wrap-n8n",
    ),
}


# per program: the start of the number option's name that only it has, and a start that two or more options share
# (None when no start is shared)
ABBREVIATIONS: dict[str, tuple[str, str | None]] = {
    "real": ("--dry-po", "--dry"),
    "live": ("--max-tok", "--c"),
    "feed": ("--ind", None),
    "probe": ("--yes-s", None),
    "catcher": ("--po", None),
    "invariants": ("--max-fa", "--max"),
    "driver": ("--work", "--s"),
    "fakes": ("--po", None),
    "model": ("--po", "--c"),
    "burst": ("--exp", "--e"),
}


def _typed_wrong(name: str) -> dict[str, list[str]]:
    """The argument lists that put the fake key in the wrong place, for one program."""
    _, good, number, flag = PROGRAMS[name]
    own, shared = ABBREVIATIONS[name]
    cases = {
        "value of a number option": [*good, number, FAKE_KEY],
        "value joined with =": [*good, number + "=" + FAKE_KEY],
        "stray word": [*good, FAKE_KEY],
        "stray word first (the slot of a subcommand)": [FAKE_KEY, *good],
        "unknown option name": [*good, "--" + FAKE_KEY],
        "unknown option with a value": [*good, "--unknown-option=" + FAKE_KEY],
        "abbreviated option": [*good, own + "=" + FAKE_KEY],
        "option name missing its value": [*good, number, "--" + FAKE_KEY],
    }
    if shared is not None:
        cases["ambiguous abbreviation"] = [*good, shared + "=" + FAKE_KEY]
    if flag is not None:
        cases["value on a flag"] = [*good, flag + "=" + FAKE_KEY]
    return cases


ALL_CASES = [(name, case) for name in PROGRAMS for case in _typed_wrong(name)]


@pytest.mark.parametrize(("name", "case"), ALL_CASES, ids=[f"{n}: {c}" for n, c in ALL_CASES])
def test_what_was_typed_is_never_printed_back(name: str, case: str) -> None:
    command = PROGRAMS[name][0]
    code, out, err = _run_command(command, *_typed_wrong(name)[case])
    assert code == 2, (out, err)
    assert FAKE_KEY not in out + err and "FAKE0123" not in out + err and "ant-" not in out + err, (out, err)
    assert ONE_LINE.fullmatch(out) and err == "" and "Traceback" not in out, (out, err)


def test_the_real_script_no_longer_echoes_like_stock_argparse() -> None:
    """The reproduced defect, exact: `invalid int value: '<key>'` and `unrecognized arguments: <x>` are gone."""
    assert run_script("run_real_check.py", "--dry-fakes", "--dry-port-base", FAKE_KEY)[1] == (
        "refused: --dry-port-base: must be a whole number\n"
    )
    assert run_script("run_real_check.py", FAKE_KEY)[1] == (
        "refused: the arguments: an option is unknown, ambiguous or has a stray value (see --help)\n"
    )


@pytest.mark.parametrize("base", ["99999", "65536", "65532", "0", "-5", "1000000000000000000000"])
def test_a_port_base_without_room_for_the_self_test_ports_is_refused_in_plain_words(base: str) -> None:
    code, out, err = run_script("run_real_check.py", "--dry-fakes", "--assume-yes", "--dry-port-base", base)
    last = PORT_MAX - (rrc.DRY_PORT_COUNT - 1)
    assert code == 2 and err == ""
    assert out == (
        f"refused: --dry-port-base: must be between 1 and {last} "
        f"(the self-test uses {rrc.DRY_PORT_COUNT} ports in a row from it)\n"
    )
    assert "Error" not in out  # no exception name


def _real_args(**given: object) -> argparse.Namespace:
    values: dict[str, object] = {"dry_fakes": True, "dry_port_base": None, "dry_smtp_script": None}
    return argparse.Namespace(**{**values, **given})


def test_the_edges_of_the_port_range() -> None:
    last = PORT_MAX - (rrc.DRY_PORT_COUNT - 1)
    assert rrc.option_problem(_real_args(dry_port_base=1)) is None
    assert rrc.option_problem(_real_args(dry_port_base=last)) is None  # the last base: its 5th port is 65535
    assert rrc.option_problem(_real_args(dry_port_base=last + 1)) is not None
    assert rrc.option_problem(_real_args(dry_port_base=0)) is not None
    assert rrc.option_problem(_real_args()) is None


def test_a_bad_smtp_behaviour_word_is_refused_before_the_start_question() -> None:
    """No terminal and no --assume-yes: the start question (and its "no terminal" refusal) would come next, so the
    behaviour word is refused first. The words offered are the fake mail server's own list."""
    from demo_only.fake_smtp_tls import SCRIPTS

    code, out, _ = run_script("run_real_check.py", "--dry-fakes", "--dry-smtp-script", "bogus")
    assert code == 2
    assert out == "refused: --dry-smtp-script: is not a known behaviour; use one of: " + ", ".join(SCRIPTS) + "\n"
    assert "bogus" not in out
    assert rrc.option_problem(_real_args(dry_smtp_script="final_452")) is None


@pytest.mark.parametrize(
    ("extra", "option"),
    [(["--dry-port-base", "9000"], "--dry-port-base"), (["--dry-smtp-script", "ok"], "--dry-smtp-script")],
)
def test_the_self_test_options_are_refused_without_the_self_test(extra: list[str], option: str) -> None:
    code, out, _ = run_script("run_real_check.py", *extra)
    assert code == 2 and out == f"refused: {option}: only for the self-test (--dry-fakes)\n"


@pytest.mark.parametrize(
    ("over", "line"),
    [
        (
            {"price_date": "04-11-2026"},
            "refused: --price-date: must be a day written YYYY-MM-DD (for example 2026-01-31)",
        ),
        (
            {"price_date": "20260131"},
            "refused: --price-date: must be a day written YYYY-MM-DD (for example 2026-01-31)",
        ),
        (
            {"price_date": "2026-W05-1"},
            "refused: --price-date: must be a day written YYYY-MM-DD (for example 2026-01-31)",
        ),
        ({"price_date": "2026-02-30"}, "refused: --price-date: is not a real calendar day (written YYYY-MM-DD)"),
        ({"price_date": "2020-01-01"}, "refused: --price-date: is too old (not before 2023-01-01)"),
        (
            {"price_date": "2030-01-01"},
            "refused: --price-date: is in the future: give the day the prices were read from the provider's page",
        ),
        ({"effort": "bogus"}, "refused: --effort: must be one of: " + ", ".join(LIVE_EFFORTS)),
        ({"effort": "LOW"}, "refused: --effort: must be one of: " + ", ".join(LIVE_EFFORTS)),
        ({"effort": " low"}, "refused: --effort: must be one of: " + ", ".join(LIVE_EFFORTS)),
    ],
)
def test_the_live_script_refuses_a_bad_price_date_and_effort_with_the_exact_line(
    over: dict[str, str], line: str
) -> None:
    code, out, err = run_script("run_live_check.py", *_live(**over))
    assert code == 2 and err == "", (out, err)
    assert out == line + "\n"


def test_the_same_model_twice_is_refused_even_with_different_prices() -> None:
    args = [*_live(), "--model", "m-a=3,4"]
    code, out, _ = run_script("run_live_check.py", *args)
    assert code == 2 and out == "refused: --model: the same model id is given twice: give each model once\n"
    code, out, _ = run_script("run_live_check.py", *_live(), "--model", " M-A =3,4")
    assert code == 2 and out == "refused: --model: the same model id is given twice: give each model once\n"


def test_no_program_builds_a_stock_argparse_parser() -> None:
    """The class check: the only `ArgumentParser(` of the repository is the shared refusing parser's own base class."""
    found = []
    for folder in ("scripts", "load_tools", "demo_only", "tools", "src"):
        for path in sorted((REPO / folder).rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            if re.search(r"(?<!Refusing)ArgumentParser\(", text) or re.search(r"class \w+\(.*ArgumentParser\)", text):
                found.append(str(path.relative_to(REPO)))
    assert found == ["tools/refusing_args.py"]


@pytest.mark.parametrize("scenario", ["burst:" + FAKE_KEY, "rate:1:" + FAKE_KEY, "dupmix:" + FAKE_KEY, FAKE_KEY])
def test_a_bad_scenario_names_the_form_without_the_words_typed(scenario: str) -> None:
    from load_tools import load_driver

    with pytest.raises(ValueError) as stop:
        load_driver.parse_scenario(scenario)
    assert str(stop.value) == load_driver.SCENARIO_FORM and FAKE_KEY not in str(stop.value)
    code, out, err = _run_command(
        ["load_tools/load_driver.py"], *PROGRAMS["driver"][1][:2], "--scenario", scenario, "--log", "l"
    )
    assert code == 2 and out == "" and err == f"ERROR: {load_driver.SCENARIO_FORM}\n", (out, err)


def test_a_scenario_with_a_bad_number_has_its_own_fixed_text() -> None:
    from load_tools import load_driver

    with pytest.raises(ValueError) as stop:
        load_driver.parse_scenario("burst:-3")
    assert str(stop.value) == load_driver.SCENARIO_NUMBERS


def test_n8n_api_messages_do_not_repeat_the_name_or_the_file_that_was_typed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import importlib

    key = tmp_path / "key.txt"
    key.write_text("made-up-key-for-the-test\n", encoding="utf-8")
    monkeypatch.setenv("N8N_API_KEY_FILE", str(key))
    monkeypatch.setenv("N8N_URL", "http" + "://127.0.0.1:1")
    sys.modules.pop("n8n_api", None)
    n8n_api = importlib.import_module("n8n_api")
    monkeypatch.setattr(n8n_api, "workflows", lambda: [{"id": "1", "name": "other", "active": False}])
    with pytest.raises(SystemExit) as stop:
        n8n_api.main(["n8n_api.py", "activate", FAKE_KEY])
    assert str(stop.value) == "0 workflows have the NAME given (exactly one is needed)"
    bad = tmp_path / (FAKE_KEY + ".json")
    bad.write_text("not json", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as stop:
        n8n_api.main(["n8n_api.py", "import", bad.name])
    assert str(stop.value) == "cannot read a workflow from the FILE given (the file is not JSON that can be read)"
    with pytest.raises(SystemExit) as stop:
        n8n_api.main(["n8n_api.py", "import", FAKE_KEY + "-missing.json"])
    assert FAKE_KEY not in str(stop.value)


# -- the points found by the hostile-input run: checks after the start question, one key-size limit, a class name --


def test_a_folder_that_cannot_be_written_or_holds_a_nul_character_is_seen_before_the_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert rrc.folder_cannot_be_made(tmp_path / "new" / "run" / "desk.db") is False  # a folder that can be made
    assert rrc.folder_cannot_be_made(str(tmp_path / "a\0b" / "desk.db")) is True
    monkeypatch.setattr("os.access", lambda *_a, **_k: False)  # a read-only mount answers "no write access"
    assert rrc.folder_cannot_be_made(tmp_path / "new" / "run" / "desk.db") is True
    assert rrc.folder_cannot_be_made(None) is True  # type: ignore[arg-type]


def test_a_run_folder_that_cannot_be_made_after_the_question_is_a_fixed_refusal_not_a_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The self-test skips the question (--assume-yes), so the folder step after it is reached without any answer."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    real_mkdir = Path.mkdir

    def mkdir(self: Path, *args: object, **kwargs: object) -> None:
        if self.name == "run":  # the run folder of the self-test: as if the mount had turned read-only
            raise OSError(30, "Read-only file system")
        real_mkdir(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "mkdir", mkdir)
    code = rrc.main(["--dry-fakes", "--assume-yes"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_REFUSED
    assert out.splitlines()[-1] == (
        "refused: DESK_DB_PATH: the run folder cannot be made (no write access or no space); nothing was started"
    )
    assert "Errno" not in out and "Read-only" not in out


def test_a_nul_character_in_the_database_path_is_refused_before_the_question(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from test_real_check_dry import _valid_config

    monkeypatch.setattr("builtins.input", lambda *_a: pytest.fail("the start question was asked"))
    cfg = _valid_config(tmp_path, DESK_DB_PATH=str(tmp_path / "a\0b" / "desk.db"))
    code = rrc.main(["--config", str(cfg)])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_REFUSED and out.startswith("refused: DESK_DB_PATH: "), out
    assert "Traceback" not in out


def test_the_live_key_file_has_the_same_size_limit_as_the_other_key_readers(tmp_path: Path) -> None:
    from lead_desk.config import LiveSettings
    from lead_desk.constants import SECRET_FILE_MAX_BYTES
    from lead_desk.live_claude import LiveError, LiveQualifier

    def reader(size: int) -> LiveQualifier:
        key = tmp_path / f"k{size}"
        key.write_text("k" * size, encoding="utf-8")
        s = LiveSettings(
            model="m",
            key_file=key,
            price_in_per_mtok=Decimal(1),
            price_out_per_mtok=Decimal(2),
            price_date="2026-01-01",
            cap_run_usd=Decimal(1),
            cap_total_usd=Decimal(2),
            ledger_path=tmp_path / "l",
            run_id="r",
            base_url="http" + "://127.0.0.1:1",
        )
        return LiveQualifier(s)

    assert reader(SECRET_FILE_MAX_BYTES)._read_key() == "k" * SECRET_FILE_MAX_BYTES  # the limit itself is allowed
    with pytest.raises(LiveError, match="too large"):
        reader(SECRET_FILE_MAX_BYTES + 1)._read_key()
    with pytest.raises(LiveError, match="too large"):
        reader(1_000_000)._read_key()  # the size the hostile-input run used


def test_a_ledger_that_cannot_be_written_says_so_without_a_class_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import run_live_check as rlc

    from lead_desk.live_claude import LiveCapReached

    def refuse(*_a: object, **_k: object) -> None:
        raise LiveCapReached("the spend ledger cannot be written: check the disk and the ledger file")

    monkeypatch.setattr(rlc, "run_model", refuse)
    monkeypatch.setattr("builtins.input", lambda *_a: "y")  # a person answers the start question
    key = tmp_path / "k"
    key.write_text("made-up-" + "key-0003", encoding="utf-8")
    args = _live()
    args[args.index("--key-file") + 1] = str(key)
    args[args.index("--ledger") + 1] = str(tmp_path / "ledger")
    assert rlc.main(args) == rlc.EXIT_REFUSED
    out = capsys.readouterr().out
    assert out.splitlines()[-1] == "stopped: the spend ledger could not be read or written; nothing more was called"
    assert "LiveCapReached" not in out
