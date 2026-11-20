"""The strict switch on a tree without core-b's trigger config: FAILED at test time, never an error at collection.

`tests/triggers/test_t5_main_start.py` needs core-b's config. With `HADAVIN_REQUIRE_PG=1` its tests must be listed
as FAILED and the rest of the run must go on (an ImportError at collection stopped the whole run once). Without
the switch the module is skipped. Both are run here in a child pytest, on that one module. On a tree that has
core-b's config the module runs for real and there is nothing to show here: this test skips.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.triggers.conftest import STRICT_VARIABLE, core_b_trigger_config

MODULE = "tests/triggers/test_t5_main_start.py"
ROOT = Path(__file__).resolve().parents[2]


def _child(strict: bool) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != STRICT_VARIABLE}
    if strict:
        env[STRICT_VARIABLE] = "1"
    return subprocess.run(  # noqa: S603 - this interpreter, pytest, no shell
        [sys.executable, "-m", "pytest", MODULE, "-q", "-p", "no:cacheprovider", "-rfs"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


pytestmark = pytest.mark.skipif(
    core_b_trigger_config(),
    reason="this tree has core-b's trigger config: the module runs for real",
)


def test_strict_a_missing_core_b_config_is_failed_at_test_time_not_a_collection_error():
    done = _child(strict=True)
    out = done.stdout + done.stderr
    assert done.returncode == 1, out[-2000:]
    assert "FAILED tests/triggers/test_t5_main_start.py::test_1_" in out, out[-2000:]
    assert "Interrupted" not in out and "FAILED" in out, out[
        -2000:
    ]  # rc 1 = tests failed; 2 would be an abort
    assert "core-b trigger config" in out


def test_without_the_switch_a_missing_core_b_config_is_a_skip():
    done = _child(strict=False)
    out = done.stdout + done.stderr
    assert done.returncode in (0, 5), out[-2000:]  # 5: pytest's code for a run in which nothing ran
    assert "skipped" in out and "FAILED" not in out and " failed" not in out, out[-2000:]
