"""CI runs the demo-only folder guard. Kept apart from tests/test_demo_only_guard.py because it reads .github, which the
mutation runner's copy of the repository does not hold."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_runs_the_scan_in_the_main_check_job_with_read_only_permissions() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "run: python tools/demo_only_guard.py" in ci
    head = ci.split("\njobs:\n", 1)[0]
    assert re.search(r"^permissions:\n  contents: read\n", head, re.MULTILINE)  # no new rights
    check_job = ci.split("\n  check:\n", 1)[1].split("\n  tests-py312:\n", 1)[0]
    assert "run: python tools/demo_only_guard.py" in check_job
