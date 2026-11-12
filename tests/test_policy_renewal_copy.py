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
    expected = named - set(NOT_EDITED)
    if mode == "names":
        expected -= {"CHANGELOG.md"}  # step (3): nothing is changed there for the names and claims
    else:
        expected |= {
            "CHANGELOG.md"
        }  # the steps of the kinds change the sentence that gives their days
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


def _printed_row_count(mode: str) -> int:
    """The figure the printed steps give for the rows a renewal of `mode` asks for ('both', 'kinds', 'names')."""
    from tools import policy_page as pp

    text, pattern = {
        "both": (pp.RENEWAL_STEPS, r"both lists asked for about (\d+) rows?"),
        "names": (pp.RENEWAL_STEPS, r"names and claims alone asked for about (\d+) rows?"),
        "kinds": (pp.KINDS_RENEWAL_STEPS, r"kinds alone asked for about (\d+) rows?"),
    }[mode]
    found = re.findall(pattern, text)
    assert len(found) == 1, (
        f"the printed steps give {len(found)} figures for the {mode} renewal: {found}"
    )
    assert int(found[0]) >= 1, f"the printed steps give no rows for the {mode} renewal"
    return int(found[0])


def _assert_the_asked_rows_match_the_printed_figure(mode: str, asked: int) -> None:
    """The printed 'about N rows' is a size that was measured: the count the plant found may be half of it more or
    less (5 more or less when the figure is 10 or less), and then the printed figure is wrong and must be renewed."""
    printed = _printed_row_count(mode)
    _assert_within_the_tolerance(mode, asked, printed)


def _assert_within_the_tolerance(mode: str, asked: int, printed: int) -> None:
    """The count a renewal asked for must be at least 1 (a renewal that asks for no row is not the one the figure was
    measured on) and not more than the tolerance away from the printed figure."""
    tolerance = max(5, printed // 2)
    low = max(1, printed - tolerance)
    assert low <= asked <= printed + tolerance, (
        f"the {mode} renewal asked for {asked} rows, the printed steps say about {printed} "
        f"(allowed {low} to {printed + tolerance}): measure again and rewrite the figure in tools/policy_page.py "
        "and in CHANGELOG.md"
    )


def _fast_renewal(mode: str) -> None:
    """The fast part of a renewal plant: the copy is made and edited by the printed steps of `mode`, and its files
    and days are compared with the steps (no tests run in the copy)."""
    from tests.test_policy_guard import KINDS_DECIDED, pp

    assert _printed_row_count(mode) >= 1, f"no printed row figure for the {mode} renewal"
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
        _assert_the_asked_rows_match_the_printed_figure("both", asked)


def _refusal_of(call, *args) -> str | None:
    """The text of the `AssertionError` that `call` raises, or None when it raises none."""
    try:
        call(*args)
    except AssertionError as exc:
        return str(exc)
    return None


def test_the_printed_row_figure_is_read_once_per_renewal_and_a_missing_or_doubled_one_is_refused(
    monkeypatch,
):
    from tools import policy_page as pp

    figures = [
        _refusal_of(_printed_row_count, m) or _printed_row_count(m)
        for m in ("both", "names", "kinds")
    ]
    assert figures == [36, 1, 35], (
        f"the printed row figures of the three renewals are not 36, 1 and 35: {figures}"
    )
    for text, label in (
        ("", "no"),
        ("both lists asked for about 3 rows; both lists asked for about 4 rows", "two"),
    ):
        monkeypatch.setattr(pp, "RENEWAL_STEPS", text)
        refusal = _refusal_of(_printed_row_count, "both")
        assert refusal is not None, f"{label} printed figure: the figure was read"
        assert "figures for the both renewal" in refusal, refusal
    monkeypatch.setattr(pp, "RENEWAL_STEPS", "both lists asked for about 0 rows")
    refusal = _refusal_of(_printed_row_count, "both")
    assert refusal is not None, "a printed figure of 0 rows: the figure was read"
    assert "no rows" in refusal, refusal


def test_the_asked_row_count_must_be_within_the_tolerance_of_the_printed_figure():
    def rejected(asked, printed):
        try:
            _assert_within_the_tolerance("both", asked, printed)
        except AssertionError:
            return True
        return False

    # a figure of 36: half is 18, so 18 to 54 are allowed and 17 and 55 are not
    assert not rejected(18, 36) and not rejected(54, 36), (
        "the edge of the tolerance of 36 was refused"
    )
    assert rejected(17, 36) and rejected(55, 36), "a count beyond the tolerance of 36 was accepted"
    # a figure of 10 or less: 5 more or less, and never fewer than 1 row
    assert not rejected(6, 10) and not rejected(15, 10), (
        "the edge of the tolerance of 10 was refused"
    )
    assert rejected(16, 10) and rejected(4, 10), "a count beyond the tolerance of 10 was accepted"
    assert not rejected(1, 1) and not rejected(6, 1), "the edge of the tolerance of 1 was refused"
    assert rejected(7, 1), "a count of 7 was accepted for a figure of 1"
    assert rejected(0, 1), "no row at all was accepted for a figure of 1"


def test_the_assertion_helper_reads_the_printed_figure_of_its_own_mode(monkeypatch):
    from tools import policy_page as pp

    monkeypatch.setattr(
        pp,
        "RENEWAL_STEPS",
        "both lists asked for about 36 rows; names and claims alone asked for about 1 row",
    )
    monkeypatch.setattr(pp, "KINDS_RENEWAL_STEPS", "kinds alone asked for about 35 rows")
    _assert_the_asked_rows_match_the_printed_figure("names", 1)
    _assert_the_asked_rows_match_the_printed_figure("kinds", 35)
    accepted = [
        (mode, asked)
        for mode, asked in (("names", 7), ("kinds", 60), ("both", 3))
        if _refusal_of(_assert_the_asked_rows_match_the_printed_figure, mode, asked) is None
    ]
    assert not accepted, f"a count outside the tolerance of its own figure was accepted: {accepted}"
