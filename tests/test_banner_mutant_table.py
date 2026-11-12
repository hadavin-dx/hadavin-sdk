"""The table of banner and guard mutants (`tests/banner_mutants.py`) is checked here. The runner replaces EVERY occurrence
of a row's search text, so a row whose text occurs twice changes two places at once and can be killed for a reason that is
not its own; a text that is not found is an error at run time. `non_unique_rows` finds both, and a planted duplicate proves
that it does."""

from __future__ import annotations

from pathlib import Path

from tests import banner_mutants as bm


def test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once() -> None:
    assert bm.non_unique_rows() == []


def test_the_table_has_no_loose_expectation_left() -> None:
    loose = [m.name for m in bm.M if m.expect in ("assert", "ZZZZ") or len(m.expect) < 4]
    assert loose == []


def test_a_planted_duplicate_or_missing_search_text_or_repeated_label_is_reported(
    tmp_path: Path,
) -> None:
    (tmp_path / "x.py").write_text("a = 1\nb = 1\nc = 2\n", encoding="utf-8")
    rows = [
        bm.mutant("Z1 once", "x.py", "c = 2", "c = 3", "t.py", "test_k", "wrong value"),
        bm.mutant("Z2 twice", "x.py", "= 1", "= 5", "t.py", "test_k", "wrong value"),
        bm.mutant("Z3 never", "x.py", "d = 9", "d = 8", "t.py", "test_k", "wrong value"),
        bm.mutant("Z1 again", "x.py", "c = 2", "c = 4", "t.py", "test_k", "wrong value"),
    ]
    assert bm.non_unique_rows(root=tmp_path, rows=rows) == [
        ("Z2 twice", "search text found 2 times"),
        ("Z3 never", "search text found 0 times"),
        ("Z1", "label used twice"),
    ]
