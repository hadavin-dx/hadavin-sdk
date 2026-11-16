"""Class F6b: the start and reset scripts (reset.sh, start_all.sh, reset.ps1, start_all.ps1) read the desk's settings
through ONE helper, scripts/desk_setting.py. A bad DESK_* value ends with the one refusal line the desk itself prints
and exit code 4: no Python traceback, and never the value that was typed. Made-up values only, built from parts.

Run here: the two shell scripts (bash) and the helper. NOT run here: the two .ps1 scripts (no PowerShell on this
machine); they are pinned by a text check only, and on a Windows machine the same tests run them for real."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from test_reset_scripts import WINDOWS, _run

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
WRAPPERS = ("reset.sh", "start_all.sh", "reset.ps1", "start_all.ps1")
FAKE_SECRET = "sk-" + "test-" + "not-a-real-key-" + "0123456789"  # made up, built from parts
REFUSED_LINE = "the desk refuses a setting: "


def _helper() -> Any:
    sys.path.insert(0, str(SCRIPTS))
    try:
        import desk_setting

        return desk_setting
    finally:
        sys.path.remove(str(SCRIPTS))


@pytest.mark.parametrize(
    "wrapper", ["reset.ps1" if WINDOWS else "reset.sh", "start_all.ps1" if WINDOWS else "start_all.sh"]
)
@pytest.mark.parametrize(
    "bad",
    [
        {"DESK_BIND": "a b"},
        {"DESK_PORT": FAKE_SECRET},
        {"DESK_BIND": "a b", "DESK_PORT": FAKE_SECRET, "DESK_NOTE": FAKE_SECRET},
    ],
)
def test_a_wrapper_shows_the_refusal_line_and_exits_4_for_a_bad_setting(
    tmp_path: Path, wrapper: str, bad: dict[str, str]
) -> None:
    book = tmp_path / "data" / "desk.sqlite3"
    book.parent.mkdir()
    book.write_text("keep me", encoding="utf-8")
    pid = book.parent / "desk.pid"
    pid.write_text("1\n", encoding="utf-8")  # a wrapper that went on would stop or delete things around here
    done = _run(wrapper, book, **bad)
    text = done.stdout + done.stderr
    assert done.returncode == 4, (done.returncode, text)
    assert "Traceback" not in text and 'File "' not in text, text
    assert FAKE_SECRET not in text and "a b" not in text, text
    assert text.strip().splitlines()[0].startswith(REFUSED_LINE), text
    assert len(text.strip().splitlines()) == 1, text
    assert book.read_text(encoding="utf-8") == "keep me" and pid.exists()
    assert sorted(p.name for p in book.parent.iterdir()) == [
        "desk.pid",
        "desk.sqlite3",
    ]  # nothing made, nothing deleted


@pytest.mark.parametrize("wrapper", WRAPPERS)
def test_no_wrapper_builds_a_config_inside_python_dash_c_any_more(wrapper: str) -> None:
    """All four wrappers go through scripts/desk_setting.py; the .ps1 pair (not run here) is pinned by its text: the
    helper is called, its exit code is checked, and the script ends with that code."""
    text = (SCRIPTS / wrapper).read_text(encoding="utf-8")
    assert "Config.from_env" not in text and "lead_desk.config" not in text
    assert "desk_setting.py" in text
    if wrapper.endswith(".ps1"):
        assert "$LASTEXITCODE -ne 0" in text and "exit $LASTEXITCODE" in text and "Write-Host $text" in text
    else:
        assert "|| rc=$?" in text and 'exit "$rc"' in text


def test_the_helper_prints_each_value_and_refuses_a_bad_one_in_one_line(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    helper = _helper()
    book = tmp_path / "d" / "x.sqlite3"
    for k in [k for k in os.environ if k.startswith("DESK_")]:
        monkeypatch.delenv(k)
    monkeypatch.setenv("DESK_DB_PATH", str(book))
    monkeypatch.setenv("DESK_PORT", "8123")
    monkeypatch.setenv("DESK_FAKES_PORT", "8124")
    for name, want in (
        ("db-path", str(book)),
        ("data-dir", str(book.parent)),
        ("fakes-port", "8124"),
        ("port", "8123"),
    ):
        assert helper.main(["desk_setting.py", name]) == 0
        assert capsys.readouterr().out.strip() == want
    monkeypatch.setenv("DESK_BIND", "a b")
    monkeypatch.setenv("DESK_NOTE", FAKE_SECRET)
    assert helper.main(["desk_setting.py", "port"]) == 4
    out = capsys.readouterr()
    assert out.out.startswith(REFUSED_LINE) and len(out.out.strip().splitlines()) == 1 and out.err == ""
    assert "a b" not in out.out


@pytest.mark.parametrize("argv", [[], ["port", "extra"], ["nope"], [FAKE_SECRET]])
def test_the_helper_answers_a_wrong_command_line_with_usage_and_exit_2(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    assert _helper().main(["desk_setting.py", *argv]) == 2
    out = capsys.readouterr().out
    assert out.startswith("usage: ") and FAKE_SECRET not in out
