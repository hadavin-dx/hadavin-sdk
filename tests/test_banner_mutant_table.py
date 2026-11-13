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


GENERIC_EXPECTATIONS = ("AssertionError", "did not match", "boom", "assert", "Exception", "Error")


def weak_expectations(rows=None) -> list[tuple[str, str]]:
    """Rows whose `expect` would also fit an unrelated failure: a bare exception word, pytest's own "did not match"
    line, a bare tuple repr, or a short bare comparison of two values. Every row names a fragment of its own message
    instead (the message of the assert, or the name of the rule it expects)."""
    weak: list[tuple[str, str]] = []
    for m in bm.M if rows is None else rows:
        e = m.expect.strip()
        generic = (
            e in GENERIC_EXPECTATIONS
            or "did not match" in e
            or e.startswith("AssertionError: (")
            or (e.startswith("assert ") and len(e) < 30)  # a bare comparison of two short values
            or (e.startswith("AssertionError: ") and len(e) < 24)
            or "..." in e  # pytest shortened the line: what hides behind the dots is not checked
        )
        if generic:
            weak.append((m.name, e))
    return weak


def test_no_row_has_a_generic_or_shortened_expectation() -> None:
    assert weak_expectations() == []


def test_no_row_changes_nothing() -> None:
    assert [m.name for m in bm.M if m.old == m.new] == []


def test_a_planted_generic_expectation_or_a_row_that_changes_nothing_is_reported() -> None:
    good = bm.mutant("Z1 ok", "x.py", "a", "b", "t.py", "test_k", "wrong value written")
    rows = [
        good,
        bm.mutant("Z2 bare", "x.py", "a", "b", "t.py", "test_k", "AssertionError"),
        bm.mutant("Z3 nomatch", "x.py", "a", "b", "t.py", "test_k", "Regex pattern did not match"),
        bm.mutant("Z4 boom", "x.py", "a", "b", "t.py", "test_k", "boom"),
        bm.mutant("Z5 cut", "x.py", "a", "b", "t.py", "test_k", "assert 0 == 2"),
        bm.mutant("Z6 tuple", "x.py", "a", "b", "t.py", "test_k", "AssertionError: ('x',)"),
        bm.mutant(
            "Z8 dots",
            "x.py",
            "a",
            "b",
            "t.py",
            "test_k",
            "wrong value in ['src/pkg/a.p...-only-folder']",
        ),
    ]
    assert [name for name, _ in weak_expectations(rows)] == [
        "Z2 bare",
        "Z3 nomatch",
        "Z4 boom",
        "Z5 cut",
        "Z6 tuple",
        "Z8 dots",
    ]
    same = bm.mutant("Z7 same", "x.py", "a", "a", "t.py", "test_k", "wrong value written")
    assert [m.name for m in [good, same] if m.old == m.new] == ["Z7 same"]
