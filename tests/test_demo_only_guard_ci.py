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


def _step_block(job: str, run_line: str) -> str:
    """The text of the one step whose `run:` line is `run_line` (from its `- name:` line to the next step)."""
    blocks = re.split(r"(?m)^      - name: ", job)
    found = [b for b in blocks if f"run: {run_line}" in b]
    assert len(found) == 1, f"expected exactly one step running {run_line!r}, found {len(found)}"
    return found[0]


def test_ci_runs_the_copy_run_the_banner_mutants_and_checks_node_is_there() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    check_job = ci.split("\n  check:\n", 1)[1].split("\n  tests-py312:\n", 1)[0]
    runs = _steps(check_job)
    copy_run = (
        'python tools/demo_only_guard.py --without-folder-if-present -- -m "not live and not perf"'
    )
    assert copy_run in runs  # the copy run takes the same test selection as the main tests step
    assert "python tests/banner_mutants.py" in runs
    assert "node --version" in runs
    # the node check comes before the tests that need node (checked on the parsed workflow below)
    assert runs.index("node --version") < runs.index('pytest -q -m "not live and not perf" -rs')
    assert 'HADAVIN_REQUIRE_NODE: "1"' in _step_block(
        check_job, 'pytest -q -m "not live and not perf" -rs'
    )
    # the copy run's own step sets it as well, or its banner tests would skip without node
    assert 'HADAVIN_REQUIRE_NODE: "1"' in _step_block(check_job, copy_run)


def test_ci_requires_node_in_the_python_312_test_job_too() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    job = ci.split("\n  tests-py312:\n", 1)[1].split("\n  security:\n", 1)[0]
    assert "node --version" in _steps(job)
    assert 'HADAVIN_REQUIRE_NODE: "1"' in job


def test_the_changelog_does_not_claim_the_banner_reads_urls_exactly_like_the_tool_client() -> None:
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "modelled on the tool client and at least as strict" in log
    assert "read the way the tool client reads it" not in log


def test_the_changelog_lists_the_refused_endings_the_guard_refuses() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_guard_for_changelog", ROOT / "tools" / "demo_only_guard.py"
    )
    assert spec is not None and spec.loader is not None
    guard = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[spec.name] = guard
    try:
        spec.loader.exec_module(guard)
    finally:
        sys.modules.pop(spec.name, None)
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    entry = log.split("**Demo-only folder guard (promoted from a public demo).**", 1)[1].split(
        "\n- **", 1
    )[0]
    listed = set(
        re.findall(
            r"`(\.[a-z0-9]+)`",
            entry.split("These files are refused:", 1)[1].split(" by ending", 1)[0],
        )
    )
    assert listed == set(guard.REFUSED_SUFFIXES), sorted(listed ^ set(guard.REFUSED_SUFFIXES))


def test_the_parsed_workflow_has_node_before_both_node_test_steps_and_requires_it_in_their_env() -> (
    None
):
    import yaml

    doc = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    steps = doc["jobs"]["check"]["steps"]
    runs = [str(st.get("run", "")) for st in steps]
    node_at = runs.index("node --version")
    copy_at = next(
        i for i, r in enumerate(runs) if "demo_only_guard.py --without-folder-if-present" in r
    )
    tests_at = next(
        i for i, r in enumerate(runs) if r.startswith('pytest -q -m "not live and not perf"')
    )
    assert node_at < copy_at, "the node check comes after the copy run, whose tests need node"
    assert node_at < tests_at, "the node check comes after the main tests step"
    for at, what in ((copy_at, "the copy run"), (tests_at, "the main tests step")):
        env = steps[at].get("env") or {}
        assert str(env.get("HADAVIN_REQUIRE_NODE")) == "1", (
            f"{what} does not set HADAVIN_REQUIRE_NODE to 1"
        )


def test_the_changelog_names_exactly_the_first_byte_kinds_the_guard_lists_and_states_the_banner_limits() -> (
    None
):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_guard_kinds", ROOT / "tools" / "demo_only_guard.py"
    )
    assert spec is not None and spec.loader is not None
    guard = importlib.util.module_from_spec(spec)
    import sys

    sys.modules["_guard_kinds"] = guard  # a dataclass in the module looks its module up by name
    try:
        spec.loader.exec_module(guard)
    finally:
        sys.modules.pop("_guard_kinds", None)
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    found = re.search(r"first bytes are those of: ([^.]*?) \(whatever its ending\)", log)
    assert found, (
        "the CHANGELOG has no sentence 'first bytes are those of: ... (whatever its ending)'"
    )
    named = re.split(r", | or ", found.group(1))
    assert sorted(named) == sorted(guard.MAGIC_KINDS), (
        f"the CHANGELOG names {sorted(named)} but the guard lists {sorted(guard.MAGIC_KINDS)}"
    )
    for phrase in (
        "a loopback address can still be a port forward",
        "`localhost` is trusted to resolve to the loopback address and that is not checked",
        "the objects handed to `app.build` are invisible to the banner except by name",
        "`App.overridden`",
        "the tone `unconfirmed`",
    ):
        assert phrase in log, f"the CHANGELOG no longer says: {phrase}"
