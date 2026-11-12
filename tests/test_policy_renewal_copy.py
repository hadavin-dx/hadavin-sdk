"""The renewal plants of tests/test_policy_changelog.py, the fast half: the renewed copy is made by the printed
steps and compared with them (which files are edited, which days move), and step (5), the notes check of CI on the
renewed copy, is rehearsed. Kept apart from the slow plants (they run the policy tests, the page and the mutants
inside the copy, about ten minutes each) so that a mutant of the plant helpers can be killed in seconds."""

import os
import tempfile
from datetime import timedelta
from pathlib import Path

from tests.test_policy_changelog import (
    _assert_the_copy_follows_the_steps,
    _make_renewed_copy,
    _rows_for_the_renewal,
)


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
