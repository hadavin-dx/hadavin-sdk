"""The renewal plants of tests/test_policy_changelog.py, the fast half: the renewed copy is made by the printed
steps and compared with them (which files are edited, which days move), and step (5), the notes check of CI on the
renewed copy, is rehearsed. Kept apart from the slow plants (they run the policy tests, the page and the mutants
inside the copy, about ten minutes each) so that a mutant of the plant helpers can be killed in seconds, and so that
the mutation runner, which runs a whole test file as its baseline, never starts a plant inside a plant. The checks
the plants share (`_assert_the_copy_follows_the_steps`, `_rows_for_the_renewal`) live here, beside the tests that
kill their mutants."""

import os
import re
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

from tests.test_policy_changelog import (
    NOT_EDITED,
    ROOT,
    _commit_the_copy,
    _day_in,
    _make_renewed_copy,
    _renewed_kinds,
    _steps_of,
)


def _assert_the_copy_follows_the_steps(
    copy: Path, mode: str, edited: list[str], new_decided: date
) -> None:
    """The fast checks of a renewed copy (they come before the slow ones): every file the printed steps of `mode`
    name is edited (a step the plant does not do is a step nobody rehearsed), nothing else is, the changelog
    only when the kinds are renewed, and the decision days of the copy are the new day where the steps move them
    and the old day where they do not."""
    from tests.test_policy_guard import KINDS_DECIDED, pp

    named = set(
        re.findall(r"(?<!python )(?:(?:tests|tools)/\w+\.py|CHANGELOG\.md)", _steps_of(mode))
    )
    assert edited, "the renewal has no edit at all: a plant with nothing to apply passes vacuously"
    expected = (named - set(NOT_EDITED)) | ({"CHANGELOG.md"} if mode != "names" else set())
    if mode == "names":
        expected -= {"CHANGELOG.md"}
    assert set(edited) == expected, (
        f"the {mode} renewal edited {edited}, the printed steps name {sorted(expected)}"
    )
    for rel in edited:
        assert (copy / rel).read_bytes() != (ROOT / rel).read_bytes(), f"{rel} is the same file"
    moved_names = mode in ("both", "names")
    moved_kinds = mode in ("both", "kinds")
    if (
        moved_kinds
    ):  # step (1): a later group keeps its day only while it is inside the longest window
        late = max(p.review_by for p in _renewed_kinds(new_decided).values())
        assert (late - new_decided).days <= pp.MAX_PENDING_DAYS, (
            f"after the {mode} renewal a later group of kinds is {(late - new_decided).days} days after "
            f"the new decision day, more than {pp.MAX_PENDING_DAYS}: step (1) must move it too"
        )
    got = _day_in(copy, "tools/policy_page.py", "DECIDED")
    want = new_decided if moved_names else pp.DECIDED
    assert got == want, (
        f"the decision day of the tool in the copy is {got}, expected {want} ({mode})"
    )
    got = _day_in(copy, "tests/test_policy_guard.py", "KINDS_DECIDED")
    want = new_decided if moved_kinds else KINDS_DECIDED
    assert got == want, (
        f"the decision day of the kinds in the copy is {got}, expected {want} ({mode})"
    )


NO_ROW = re.compile(
    r"^(\S+): the (?:test|mutant) (.+) is new or changed and has no row of its own in the notes$"
)


def _rows_for_the_renewal(copy: Path, base: str, env: dict) -> int:
    """Step (5) of the printed steps, done the way a builder does it: the copy (already edited and rewritten) is
    committed on top of `base`, `notes_lines_check.py --auto base` is run as CI runs it, a row is written for each
    line it prints, and the check must then pass. Returns the number of rows it asked for. A line that is not a
    plain 'new or changed and has no row' line cannot be answered with a row and fails here with its text."""
    _commit_the_copy(copy, "the renewal by the printed steps")
    notes = copy / "handover/evidence/Q8c-1/renewal/NOTES.md"
    command = [sys.executable, "tools/notes_lines_check.py", "--auto", base]

    def run() -> subprocess.CompletedProcess:
        return subprocess.run(  # noqa: S603  (argv list of this test, a temporary copy, no shell)
            command, cwd=copy, env=env, capture_output=True, text=True, timeout=900, check=False
        )

    first = run()
    if first.returncode == 0:
        return 0
    lines = [ln for ln in (first.stdout + first.stderr).splitlines() if ln.strip()]
    reason = (
        "plant: the renewal moves a day by the printed steps, see "
        "test_plant_a_full_renewal_done_as_the_overdue_messages_list_it_keeps_the_tests_the_page_and_the_mutants_green"
    )
    rows = []
    for line in lines:
        if line.startswith("the change has no builder notes file"):
            continue  # the file is written below
        found = NO_ROW.match(line)
        assert found, f"step (5): the notes check prints a line a row cannot answer: {line[:300]}"
        file, unit = found.groups()
        rows.append(f"| {file} | `{unit}` | changed | {reason} |")
    notes.parent.mkdir(parents=True, exist_ok=True)
    notes.write_text(
        "| file | unit | what | reason |\n|---|---|---|---|\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _commit_the_copy(copy, "the rows the notes check asked for")
    second = run()
    assert second.returncode == 0, (
        f"step (5): with {len(rows)} generated rows the notes check is still red: "
        f"{(second.stdout + second.stderr)[-800:]}"
    )
    return len(rows)


def _fast_renewal(mode: str) -> None:
    """The fast part of a renewal plant: the copy is made and edited by the printed steps of `mode`, and its files
    and days are compared with the steps (no tests run in the copy)."""
    from tests.test_policy_guard import KINDS_DECIDED, pp

    old = pp.DECIDED
    new = {
        "both": pp.DECIDED + timedelta(days=31),
        "kinds": KINDS_DECIDED + timedelta(days=20),
        "names": pp.DECIDED + timedelta(days=20),
    }[mode]
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "renewed"
        edited, _ = _make_renewed_copy(copy, mode, old, new)
        _assert_the_copy_follows_the_steps(copy, mode, edited, new)


def test_the_copy_of_the_full_renewal_plant_changes_each_file_the_printed_steps_name():
    _fast_renewal("both")


def test_the_copy_of_the_kinds_alone_plant_changes_each_file_the_printed_steps_name():
    _fast_renewal("kinds")


def test_the_copy_of_the_names_and_claims_alone_plant_changes_each_file_the_printed_steps_name():
    _fast_renewal("names")


def test_the_notes_check_of_a_renewed_copy_asks_for_rows_that_can_be_written_and_then_passes():
    """Step (5) of the printed steps, rehearsed: the renewed copy is committed on the base, the notes check of CI
    reads that change, a row is written for each line it prints, and it then passes. The count is printed (it is the
    number a person doing the first renewal should expect)."""
    from tests.test_policy_guard import pp

    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "renewed"
        new = pp.DECIDED + timedelta(days=31)
        _, base = _make_renewed_copy(copy, "both", pp.DECIDED, new, commit_base=True)
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "TMPDIR")}
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
        asked = _rows_for_the_renewal(copy, base, env)
        print(f"the notes check asked for {asked} rows after the full renewal")
        assert asked > 0, (
            "a full renewal changes a day that tests use, so the notes check must ask for rows"
        )
