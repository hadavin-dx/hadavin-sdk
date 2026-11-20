"""R4-1 and R4-2: the strict switch itself (tests/triggers/conftest.py), not only the core-b case.

R4-1: a test that skips with a reason naming the DSN variable is FAILED under HADAVIN_REQUIRE_PG=1 and stays
skipped without it. It is shown in a child pytest on a tiny temp test file whose conftest takes the hooks of
tests/triggers/conftest.py. R4-2: one function reads the variable: 1, true, yes (any case) are strict; unset,
empty, 0, false, no are not; any other value stops the session with a clear message.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from tests.triggers import conftest as switch
from tests.triggers.conftest import DSN_VARIABLE, STRICT_VARIABLE

ROOT = Path(__file__).resolve().parents[2]

CONFTEST = "from tests.triggers.conftest import pytest_configure, pytest_runtest_makereport  # noqa: F401\n"
TESTS = f'''
import pytest

def test_skips_for_the_dsn():
    pytest.skip("{DSN_VARIABLE} is not set")

def test_skips_for_the_driver():
    pytest.importorskip("psycopg_that_is_not_installed_here")  # reason names the module, not psycopg alone

def test_skips_for_another_reason():
    pytest.skip("Windows only")

def test_passes():
    pass
'''


def _child(tmp_path: Path, value: str | None) -> subprocess.CompletedProcess[str]:
    (tmp_path / "conftest.py").write_text(CONFTEST, encoding="utf-8")
    (tmp_path / "test_child.py").write_text(TESTS, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in (STRICT_VARIABLE, DSN_VARIABLE)}
    env["PYTHONPATH"] = str(ROOT)
    if value is not None:
        env[STRICT_VARIABLE] = value
    return subprocess.run(  # noqa: S603 - this interpreter, pytest, no shell
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfs", "-n", "0", "test_child.py"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def test_r41_a_skip_that_names_the_dsn_variable_is_failed_under_the_switch(tmp_path):
    done = _child(tmp_path, "1")
    out = done.stdout + done.stderr
    assert done.returncode == 1, out[-2000:]
    assert "FAILED test_child.py::test_skips_for_the_dsn" in out, out[-2000:]
    assert "FAILED test_child.py::test_skips_for_another_reason" not in out, out[-2000:]
    assert "FAILED test_child.py::test_passes" not in out, out[-2000:]
    assert "1 passed" in out and "1 skipped" in out and "2 failed" in out, out[-2000:]


def test_r41_without_the_switch_the_same_skips_stay_skips(tmp_path):
    done = _child(tmp_path, None)
    out = done.stdout + done.stderr
    assert done.returncode == 0, out[-2000:]
    assert "FAILED" not in out and "1 passed" in out and "3 skipped" in out, out[-2000:]


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "Yes", " yes ", "True"])
def test_r42_strict_words_are_strict(monkeypatch, value):
    monkeypatch.setenv(STRICT_VARIABLE, value)
    assert switch.strict() is True


@pytest.mark.parametrize("value", ["", "0", "false", "False", "NO", " no "])
def test_r42_not_strict_words_and_empty_are_not_strict(monkeypatch, value):
    monkeypatch.setenv(STRICT_VARIABLE, value)
    assert switch.strict() is False


def test_r42_unset_is_not_strict(monkeypatch):
    monkeypatch.delenv(STRICT_VARIABLE, raising=False)
    assert switch.strict() is False


@pytest.mark.parametrize("value", ["2", "on", "tru", "y", "enable"])
def test_r42_any_other_value_is_an_error_naming_the_variable(value):
    # not monkeypatch: that would keep the bad value set while this session's own makereport hook reads it
    with mock.patch.dict(os.environ, {STRICT_VARIABLE: value}):
        with pytest.raises(pytest.UsageError, match=STRICT_VARIABLE):
            switch.strict()


def test_r42_an_unknown_value_stops_the_session_at_start(tmp_path):
    done = _child(tmp_path, "maybe")
    out = done.stdout + done.stderr
    assert done.returncode != 0, out[-2000:]
    assert f"{STRICT_VARIABLE}='maybe' is not understood" in out, out[-2000:]
    assert "passed" not in out and "skipped" not in out, out[-2000:]


def test_r42_test_worker_and_conftest_use_the_one_function():
    text = (ROOT / "tests" / "triggers" / "test_worker.py").read_text(encoding="utf-8")
    assert "os.environ.get(\"HADAVIN_REQUIRE_PG\")" not in text and "strict()" in text
