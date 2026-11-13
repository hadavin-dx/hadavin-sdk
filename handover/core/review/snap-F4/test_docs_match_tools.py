"""Places where a page says what a command prints or needs, checked against the command itself.

Class of bug: a sentence in the documentation that nobody checked against the tool (a test count that grew, a command
that prints a different shape, a start line that leaves out a needed folder). Each test below reads the sentence from
the page and runs the real command, so the page and the tool cannot drift apart without a red test.
Made-up data only."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from support import HOST, REPO, call, child_env, free_port, lead, post_lead, stop_proc
from test_http import launch

from lead_desk.constants import EXIT_SIMULATED_KILL

sys.path.insert(0, str(REPO / "scripts"))
import hubspot_probe as hp  # noqa: E402

README = (REPO / "README.md").read_text(encoding="utf-8")
PROBE_PAGE = (REPO / "docs" / "hubspot-probe.md").read_text(encoding="utf-8")
TESTS_PAGE = (REPO / "docs" / "tests.md").read_text(encoding="utf-8")
CRASH_SCRIPT = (REPO / "scripts" / "crash_desk.py").read_text(encoding="utf-8")
COUNT_SENTENCE = re.compile(r"This tree holds (\d+) tests in (\d+) test files")
TOTAL_LINE = re.compile(r"^(\d+) tests collected in [0-9.]+s$")
FILE_LINE = re.compile(r"^(tests/\S+\.py): (\d+)$")


def _collect(flag: str) -> list[str]:
    """The lines `python -m pytest --collect-only <flag>` prints for the tests folder (nothing is run)."""
    env = child_env()
    env.pop("PYTEST_ADDOPTS", None)
    done = subprocess.run(  # noqa: S603 (this interpreter, a fixed argument list)
        [sys.executable, "-m", "pytest", "--collect-only", flag, "-p", "no:cacheprovider", "tests"],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert done.returncode == 0, done.stdout[-400:] + done.stderr[-400:]
    return [line for line in done.stdout.splitlines() if line.strip()]


@pytest.fixture(scope="module")
def collected_q() -> list[str]:
    return _collect("-q")


@pytest.fixture(scope="module")
def collected_qq() -> list[str]:
    return _collect("-qq")


def test_the_q_form_prints_one_line_per_test_and_a_total_as_its_last_line(collected_q: list[str]) -> None:
    last = collected_q[-1]
    match = TOTAL_LINE.match(last)
    if match is None:  # a module that cannot be imported here (no browser tools) changes the wording of this line
        pytest.skip(f"the last line is not the plain total on this computer: {last!r}")
    assert len(collected_q) - 1 == int(match.group(1))  # one line per test, then the total
    assert all("::" in line for line in collected_q[:-1])
    assert "one line for each test" in TESTS_PAGE and "`N tests collected in S seconds`" in TESTS_PAGE


def test_the_qq_form_prints_one_line_per_file_whose_numbers_add_up_and_no_total(
    collected_q: list[str], collected_qq: list[str]
) -> None:
    files = [FILE_LINE.match(line) for line in collected_qq]
    assert all(files), [line for line, m in zip(collected_qq, files, strict=True) if m is None][:3]
    assert not any("collected" in line for line in collected_qq)  # no total line in this form
    match = TOTAL_LINE.match(collected_q[-1])
    if match is None:
        pytest.skip("the plain total is not printed on this computer")
    assert sum(int(m.group(2)) for m in files if m) == int(match.group(1))


def test_the_page_states_the_number_of_tests_and_files_that_the_collector_counts(
    collected_q: list[str], collected_qq: list[str]
) -> None:
    said = COUNT_SENTENCE.search(TESTS_PAGE)
    assert said is not None, "docs/tests.md must say 'This tree holds N tests in M test files'"
    match = TOTAL_LINE.match(collected_q[-1])
    if match is None:
        pytest.skip(f"the last line is not the plain total on this computer: {collected_q[-1]!r}")
    assert int(said.group(1)) == int(match.group(1)), "docs/tests.md: the test count is out of date"
    assert int(said.group(2)) == len(collected_qq), "docs/tests.md: the test file count is out of date"


def _documented_python_path(text: str) -> str:
    found = {m.group(1) for m in re.finditer(r"PYTHONPATH=(\S+?)`? python scripts/crash_desk\.py", text)}
    assert len(found) == 1, f"the text must name one PYTHONPATH for scripts/crash_desk.py, found {found}"
    return found.pop()


def test_the_two_texts_that_start_the_crash_script_name_the_same_path() -> None:
    assert _documented_python_path(TESTS_PAGE) == _documented_python_path(CRASH_SCRIPT)


def test_the_crash_script_starts_with_the_path_the_page_gives(env, tmp_path: Path) -> None:
    """Start it as the page says (relative path entries, the repository as the working folder), arm the flag file and
    see the real stop at point D2. The old text said `PYTHONPATH=src`; then the desk stops with `the folder demo_only
    is missing`, because a script started by its path does not see the repository folder."""
    entries = _documented_python_path(TESTS_PAGE).split(":")
    _, fakes_url = env.fakes("keyed")
    replies = tmp_path / "replies.json"
    replies.write_text("{}", encoding="utf-8")
    port = free_port()
    base = f"http://{HOST}:{port}"
    env_vars = child_env(
        DESK_DB_PATH=str(tmp_path / "desk.sqlite3"),
        DESK_BIND=HOST,
        DESK_PORT=str(port),
        DESK_FAKES_URL=fakes_url,
        DESK_REPLIES_PATH=str(replies),
    )
    env_vars["PYTHONPATH"] = os.pathsep.join(entries)  # exactly the entries the page names, nothing added
    (tmp_path / "crash.flag").write_text("D2", encoding="utf-8")
    p = launch([str(REPO / "scripts" / "crash_desk.py")], env_vars, base)
    try:
        status, _ = post_lead(base, "form", "sub-1", lead())
        assert status == 201
        p.wait(timeout=20)
        out = stop_proc(p)
        assert p.returncode == EXIT_SIMULATED_KILL, out.decode(errors="replace")[-400:]
        assert b"simulate crash" in out
        assert call(fakes_url, "GET", "/fake/outbox")[1]["count"] == 1
    finally:
        stop_proc(p)


def test_a_repeated_request_uses_up_a_receipt_number_as_the_readme_says(env) -> None:
    """README, "Try it": the repeated request makes no lead and no mail, but the next new receipt is number 3."""
    base = env.serve(env.rig())
    first = post_lead(base, "form", "sub-1", lead())[1]
    again = post_lead(base, "form", "sub-1", lead())[1]
    other_door = post_lead(base, "webhook", "sub-1", lead())[1]
    assert (first["receipt_id"], first["verdict"]) == (1, "new")
    assert again["replayed"] is True and again["receipt_id"] == 1
    assert (other_door["receipt_id"], other_door["verdict"]) == (3, "duplicate")  # number 2 was used up
    assert call(base, "GET", "/counts")[1]["received"] == 2  # the count of receipts does not show the skip
    assert '"receipt_id": 3' in README and "can skip but are never reused" in README


def test_the_probe_checks_the_token_variable_name_only_when_calls_are_confirmed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """docs/hubspot-probe.md: `--plan` does not look at the name; with `--yes-spend-calls` a bad name is refused and
    never printed. No call is made in any of the three runs."""
    bad = "not a name"
    assert hp.main(["--plan", "--token-env", bad]) == hp.EXIT_OK
    assert hp.main(["--token-env", bad]) == hp.EXIT_REFUSED  # refused earlier, for the missing confirmation
    assert hp.main(["--yes-spend-calls", str(hp.PLANNED_CALLS), "--token-env", bad]) == hp.EXIT_REFUSED
    out = capsys.readouterr().out
    assert "must be the NAME of an environment variable" in out and bad not in out
    assert "`--plan` does not look at the name" in PROBE_PAGE
