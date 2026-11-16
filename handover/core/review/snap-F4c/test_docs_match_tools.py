"""Places where a page says what a command prints or needs, checked against the command itself.

Class of bug: a sentence in the documentation that nobody checked against the tool (a test count that grew, a command
that prints a different shape, a start line that leaves out a needed folder). Each test below reads the sentence from
the page and runs the real command, so the page and the tool cannot drift apart without a red test.
Made-up data only."""

from __future__ import annotations

import ntpath
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


# set to any non-empty value: a skipped count check is then a failure (docs/settings.md)
REQUIRE_COUNT_ENV = "DPLD_REQUIRE_COUNT"


def _plain_total_or_skip(last: str) -> re.Match[str]:
    """The match of the plain total line, or (no switch set) a skip, or (switch set) a failure: a skip must not hide
    a stale number in docs/tests.md in the run that is meant to catch it."""
    match = TOTAL_LINE.match(last)
    if match is None:
        message = f"the last line is not the plain total on this computer: {last!r}"
        if os.environ.get(REQUIRE_COUNT_ENV):
            pytest.fail(f"{message} (and {REQUIRE_COUNT_ENV} is set, so this is not a skip)")
        pytest.skip(message)
    return match


@pytest.fixture(scope="module")
def collected_q() -> list[str]:
    return _collect("-q")


@pytest.fixture(scope="module")
def collected_qq() -> list[str]:
    return _collect("-qq")


def test_the_q_form_prints_one_line_per_test_and_a_total_as_its_last_line(collected_q: list[str]) -> None:
    match = _plain_total_or_skip(collected_q[-1])  # an unusable module (no browser tools) can change this line
    assert len(collected_q) - 1 == int(match.group(1))  # one line per test, then the total
    assert all("::" in line for line in collected_q[:-1])
    assert "one line for each test" in TESTS_PAGE and "`N tests collected in S seconds`" in TESTS_PAGE


def test_the_qq_form_prints_one_line_per_file_whose_numbers_add_up_and_no_total(
    collected_q: list[str], collected_qq: list[str]
) -> None:
    files = [FILE_LINE.match(line) for line in collected_qq]
    assert all(files), [line for line, m in zip(collected_qq, files, strict=True) if m is None][:3]
    assert not any("collected" in line for line in collected_qq)  # no total line in this form
    match = _plain_total_or_skip(collected_q[-1])
    assert sum(int(m.group(2)) for m in files if m) == int(match.group(1))
    # the page says what this form prints, in the words the reader will look for
    assert "`-qq` it prints one line for each test file instead" in TESTS_PAGE
    assert "with no total line" in TESTS_PAGE


def test_the_page_states_the_number_of_tests_and_files_that_the_collector_counts(
    collected_q: list[str], collected_qq: list[str]
) -> None:
    said = COUNT_SENTENCE.search(TESTS_PAGE)
    assert said is not None, "docs/tests.md must say 'This tree holds N tests in M test files'"
    match = _plain_total_or_skip(collected_q[-1])
    assert (int(said.group(1)), int(said.group(2))) == (int(match.group(1)), len(collected_qq)), (
        f"docs/tests.md is out of date: it says {said.group(1)} tests in {said.group(2)} test files, the collector"
        f" counts {match.group(1)} tests in {len(collected_qq)} test files; change the sentence to"
        f" 'This tree holds {match.group(1)} tests in {len(collected_qq)} test files'"
    )


def _documented_python_path(text: str) -> str:
    found = {m.group(1) for m in re.finditer(r"PYTHONPATH=(\S+?)`? python scripts/crash_desk\.py", text)}
    assert len(found) == 1, f"the text must name one PYTHONPATH for scripts/crash_desk.py, found {found}"
    return found.pop()


def test_the_two_texts_that_start_the_crash_script_name_the_same_path() -> None:
    assert _documented_python_path(TESTS_PAGE) == _documented_python_path(CRASH_SCRIPT)


def test_the_windows_form_is_the_linux_form_with_semicolons_and_is_said_to_be_unrun() -> None:
    """The Windows form is not run here: the test pins only that its text is the Linux entries joined by `;` (the
    separator of ntpath, which is what Windows uses) and that both texts say only the Linux form was run."""
    entries = _documented_python_path(TESTS_PAGE).split(":")
    windows = ";".join(entries)
    assert ntpath.pathsep == ";" and windows == "src;."
    assert f"(`{windows}`)" in TESTS_PAGE and f"set PYTHONPATH={windows} first" in CRASH_SCRIPT
    assert "was not run on Windows, only the Linux form was" in TESTS_PAGE
    assert "only the Linux form was run" in CRASH_SCRIPT


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
    bad = "qzx9 not-a-name 7kv"
    assert hp.main(["--plan", "--token-env", bad]) == hp.EXIT_OK
    assert hp.main(["--token-env", bad]) == hp.EXIT_REFUSED  # refused earlier, for the missing confirmation
    assert hp.main(["--yes-spend-calls", str(hp.PLANNED_CALLS), "--token-env", bad]) == hp.EXIT_REFUSED
    out = capsys.readouterr().out
    assert "must be the NAME of an environment variable" in out and bad not in out
    assert "`--plan` does not look at the name" in PROBE_PAGE


def _page_lines() -> list[tuple[str, str]]:
    names = ["README.md", "versions.md", "load_tools/README.md"]
    pages = [REPO / n for n in names] + sorted((REPO / "docs").glob("*.md"))
    return [(p.name, line) for p in pages for line in p.read_text(encoding="utf-8").splitlines()]


def test_no_page_says_that_sending_a_request_again_changes_nothing() -> None:
    """The desk gives the stored answer, but it also uses up one receipt number and adds one to that request's count
    of arrivals (`receipts.attempts`), so "changes nothing" on a line about a repeated request is wrong (the README
    said it in four places and docs/tests.md in one)."""
    about_repeat = re.compile(r"replay|sent again|same request|comes again|came again|again gets", re.IGNORECASE)
    claim = re.compile(r"changes? nothing|nothing changes", re.IGNORECASE)
    bad = [(n, line[:80]) for n, line in _page_lines() if about_repeat.search(line) and claim.search(line)]
    assert not bad, bad
    assert "It only uses one receipt number and adds one to that request's count of arrivals" in README
    assert "it only uses one receipt number and adds one to that request's count of arrivals" in TESTS_PAGE


def test_every_page_about_a_repeated_request_says_it_can_start_a_follow_up_that_is_due() -> None:
    """desk.py `_verdict_reply` / `_pending_and_due` (and contract.md, "Follow-up"): a repeat of a request whose verdict
    is `new` starts the lead's follow-up only when that is due (no automatic try yet, or the waiting time after the last
    try is over), so repeats cannot use up the tries. Every page that describes a repeat says the same thing."""
    import inspect

    from lead_desk import desk, gate

    assert "elif self._pending_and_due(rec" in inspect.getsource(desk.Desk._verdict_reply)
    assert gate.SEND_MAX_ATTEMPTS == 5  # the number the pages give
    said = (
        "a repeat of a request whose verdict is `new` starts it; a repeat that comes earlier does not, "
        "so repeats cannot use up the 5 automatic tries"
    )
    contract = (REPO / "contract.md").read_text(encoding="utf-8")
    for name, text in (("README.md", README), ("docs/tests.md", TESTS_PAGE), ("contract.md", contract)):
        assert said in text, name
    assert README.count(said) == 3  # the example, the word list and the list of claims
    assert "no automatic try yet, or its backoff is over. Replays cannot use up the 5 tries" in contract


def test_every_old_test_count_is_named_as_from_an_earlier_commit() -> None:
    """The count of this tree comes from the collector (the test above); a figure from an older run must say so on the
    same line, or a reader takes it for the number of tests today."""
    old = re.compile(r"\b(2516|2465|2464)\b")
    marked = re.compile(r"earlier (commit|full run|full runs)", re.IGNORECASE)
    bad = [(n, line[:80]) for n, line in _page_lines() if old.search(line) and not marked.search(line)]
    assert not bad, bad
    for name in ("versions.md", "docs/limits.md"):  # dated pass counts name what they were run on
        text = (REPO / name).read_text(encoding="utf-8")
        assert "on an earlier commit, not named here" in text, name


def test_the_load_tools_recipe_has_its_own_book_and_ports_and_waits_for_each_server() -> None:
    """load_tools/README.md "A whole run": it must not touch the desk book or the ports of the README's "Try it"
    run (a book with other leads fails the checks), and it must wait for each server before the next step."""
    text = (REPO / "load_tools" / "README.md").read_text(encoding="utf-8")
    assert "rm -rf data/load && mkdir -p data/load" in text
    assert "DESK_DB_PATH=data/load/desk.sqlite3" in text and "--book data/load/desk.sqlite3" in text
    assert "DESK_PORT=18765" in text and "wait_for http://127.0.0.1:18765/counts" in text
    assert "wait_for http://127.0.0.1:18766/fake/crm" in text
    assert "data/desk.sqlite3" not in text and "8765/" not in text.replace("18765/", "")
    assert "It was run once as written on 2026-11-13" in text and "is not repeated by any test" in text


def test_the_load_tools_recipe_prose_wait_equals_the_wait_loop_of_the_recipe() -> None:
    """load_tools/README.md: "Each server is waited for (up to N seconds)" must equal the loop in the recipe's
    `wait_for` (a count of tries times the pause between them), and the recipe must call it for each server."""
    text = (REPO / "load_tools" / "README.md").read_text(encoding="utf-8")
    prose = re.search(r"Each server is waited for \(up to (\d+) seconds\) before the next step", text)
    loop = re.search(r"wait_for\(\) \{ for i in \$\(seq 1 (\d+)\); do .*?; sleep (\d+); done;", text)
    assert prose and loop, "the sentence or the wait loop is missing or was reworded"
    assert int(prose.group(1)) == int(loop.group(1)) * int(loop.group(2))
    assert len(re.findall(r"^\s*wait_for http://", text, re.MULTILINE)) == 2  # the demo CRM and the desk
