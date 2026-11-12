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


def _steps(ci: str) -> list[str]:
    return re.findall(r"^\s+run: (.+)$", ci, re.MULTILINE)


def test_ci_runs_the_copy_run_the_banner_mutants_and_checks_node_is_there() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    check_job = ci.split("\n  check:\n", 1)[1].split("\n  tests-py312:\n", 1)[0]
    runs = _steps(check_job)
    assert "python tools/demo_only_guard.py --without-folder-if-present" in runs
    assert "python tests/banner_mutants.py" in runs
    assert "node --version" in runs
    # the node check comes before the tests that need node, and HADAVIN_REQUIRE_NODE is set for them
    assert runs.index("node --version") < runs.index('pytest -q -m "not live and not perf" -rs')
    assert 'HADAVIN_REQUIRE_NODE: "1"' in check_job


def test_ci_requires_node_in_the_python_312_test_job_too() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    job = ci.split("\n  tests-py312:\n", 1)[1].split("\n  security:\n", 1)[0]
    assert "node --version" in _steps(job)
    assert 'HADAVIN_REQUIRE_NODE: "1"' in job


def test_the_changelog_does_not_claim_the_banner_reads_urls_exactly_like_the_tool_client() -> None:
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "modelled on the tool client and at least as strict" in log
    assert "read the way the tool client reads it" not in log
