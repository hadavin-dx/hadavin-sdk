"""Class: every limit and vendor fact lives once, in lead_desk/constants.py. The file reader takes its caps and the file
mode from there; the effort words are one list used by the desk setting and by the live check script; the flags of the
opening calls keep a terminal from becoming the controlling terminal. Made-up data only."""

from __future__ import annotations

import ast
import importlib
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from lead_desk import constants, regfile
from lead_desk.config import LiveSettings
from lead_desk.envnum import SettingRefused

REPO = Path(__file__).resolve().parents[1]


def test_regfile_defines_no_limit_of_its_own() -> None:
    tree = ast.parse((REPO / "src" / "lead_desk" / "regfile.py").read_text(encoding="utf-8"))
    own = {t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    assert not own & {"MAX_JSON_BYTES", "MAX_TEXT_BYTES", "NEW_FILE_MODE", "_NEW_FILE_MODE"}, own
    assert regfile.MAX_JSON_BYTES is constants.MAX_JSON_BYTES  # the same object: imported, not copied
    assert regfile.MAX_TEXT_BYTES is constants.MAX_TEXT_BYTES


def test_the_live_script_takes_its_date_floor_and_effort_list_from_constants() -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import run_live_check as rlc

    assert rlc.PRICE_DATE_FLOOR == date(*constants.LIVE_PRICE_DATE_FLOOR)
    assert rlc.LIVE_EFFORTS is constants.LIVE_EFFORTS
    text = (REPO / "scripts" / "run_live_check.py").read_text(encoding="utf-8")
    assert "date(2023" not in text and '"xhigh"' not in text


def _settings(effort: str) -> LiveSettings:
    return LiveSettings(
        model="fake-model-1",
        key_file=Path("k"),
        price_in_per_mtok=Decimal("1"),
        price_out_per_mtok=Decimal("1"),
        price_date="2026-01-01",
        cap_run_usd=Decimal("1"),
        cap_total_usd=Decimal("3"),
        ledger_path=Path("l"),
        run_id="run-a",
        base_url=constants.LIVE_DEFAULT_BASE_URL,
        effort=effort,
    )


@pytest.mark.parametrize("effort", constants.LIVE_EFFORTS)
def test_the_desk_setting_accepts_every_listed_effort_word(effort: str) -> None:
    assert _settings(effort).effort == effort


@pytest.mark.parametrize("effort", ["LOW", "turbo", "low ", "extreme"])
def test_the_desk_setting_refuses_any_other_effort_word_like_the_script_does(effort: str) -> None:
    with pytest.raises(SettingRefused, match="DESK_LIVE_EFFORT must be one of: " + ", ".join(constants.LIVE_EFFORTS)):
        _settings(effort)


@pytest.mark.skipif(not hasattr(os, "O_NOCTTY"), reason="no O_NOCTTY on this platform")
def test_the_opening_flags_keep_a_terminal_from_becoming_the_controlling_one(tmp_path: Path) -> None:
    assert regfile._FLAGS & os.O_NOCTTY and regfile._COMMON & os.O_NOCTTY
    f = regfile.open_output(tmp_path / "out", "a+b")  # the flags still open a normal file
    f.close()


# -- the limits and exit codes of the helper scripts: defined once, in constants.py ----------------------------------

GUARDED_FOLDERS = ("src/lead_desk", "load_tools", "demo_only", "scripts", "tools")
ONLY_IN_CONSTANTS = {
    "EXIT_REFUSED",
    "EXIT_UNREACHABLE",
    "EXIT_STOPPED",
    "DRY_PORT_COUNT",
    "FAKE_MODEL_DEFAULT_PORT",
    "ARMED_READ_MAX",
    "MAX_PATH_CHARS",
    "MAX_KEY",
    "MAX_PORT",
    "PORT_MAX",
    "SECRET_FILE_MAX_BYTES",
    "LOAD_TOTAL_MAX",
    "LOAD_RATE_MAX",
    "LOAD_SECONDS_MAX",
    "LOAD_WORKERS_MAX",
    "LOAD_THREADS_MAX",
    "BURST_N_MAX",
}


def _code_files() -> list[Path]:
    return [
        p
        for folder in GUARDED_FOLDERS
        for p in sorted((REPO / folder).rglob("*.py"))
        if p.relative_to(REPO).as_posix() != "src/lead_desk/constants.py"
    ]


def test_no_script_or_module_defines_one_of_the_shared_limits_or_exit_codes_itself() -> None:
    """Class: the same number defined in several files (EXIT_REFUSED four times, the key-file cap twice, the default
    port of the model stand-in in code and in a doc line) drifts apart. They are assigned in constants.py only."""
    bad = []
    for py in _code_files():
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    targets += t.elts if isinstance(t, ast.Tuple) else [t]
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            bad += [
                f"{py.relative_to(REPO).as_posix()}:{node.lineno}: {t.id}"
                for t in targets
                if isinstance(t, ast.Name) and t.id in ONLY_IN_CONSTANTS
            ]
    assert not bad, bad


def test_the_port_of_the_model_stand_in_is_a_number_in_constants_only() -> None:
    found = [
        f"{py.relative_to(REPO).as_posix()}:{n.lineno}"
        for py in _code_files()
        for n in ast.walk(ast.parse(py.read_text(encoding="utf-8")))
        if isinstance(n, ast.Constant) and n.value == constants.FAKE_MODEL_DEFAULT_PORT
    ]
    assert not found, found
    assert constants.FAKE_MODEL_DEFAULT_PORT == 48767


def test_every_script_sees_the_same_objects_as_constants() -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import hubspot_probe
    import refusals
    import run_live_check
    import run_real_check

    from demo_only import portal_demo
    from tools import pathconfine, refusing_args

    assert refusing_args.EXIT_REFUSED is constants.EXIT_REFUSED is refusals.EXIT_REFUSED
    assert hubspot_probe.EXIT_REFUSED is constants.EXIT_REFUSED is run_live_check.EXIT_REFUSED
    assert run_real_check.EXIT_REFUSED is constants.EXIT_REFUSED
    assert run_real_check.EXIT_STOPPED is constants.EXIT_STOPPED
    assert refusals.EXIT_UNREACHABLE is constants.EXIT_UNREACHABLE
    assert run_real_check.DRY_PORT_COUNT is constants.DRY_PORT_COUNT
    assert pathconfine.MAX_PATH_CHARS is constants.MAX_PATH_CHARS
    assert portal_demo.ARMED_READ_MAX is constants.ARMED_READ_MAX


def test_the_n8n_key_file_has_the_cap_of_the_other_key_readers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key = tmp_path / "key"
    key.write_text("k" * constants.SECRET_FILE_MAX_BYTES, encoding="ascii")
    monkeypatch.setenv("N8N_API_KEY_FILE", str(key))  # the module reads the key when it is imported
    monkeypatch.delenv("N8N_URL", raising=False)
    monkeypatch.syspath_prepend(str(REPO / "scripts"))
    sys.modules.pop("n8n_api", None)
    n8n_api = importlib.import_module("n8n_api")
    try:
        assert not hasattr(n8n_api, "MAX_KEY") and not hasattr(n8n_api, "MAX_PORT")
        assert n8n_api._read_key() == "k" * constants.SECRET_FILE_MAX_BYTES
        key.write_text("k" * (constants.SECRET_FILE_MAX_BYTES + 1), encoding="ascii")
        with pytest.raises(SystemExit, match="the n8n API key file is too large"):
            n8n_api._read_key()
    finally:
        sys.modules.pop("n8n_api", None)
