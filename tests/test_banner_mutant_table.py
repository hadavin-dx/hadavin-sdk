"""The table of banner and guard mutants (`tests/banner_mutants.py`) is checked here. The runner replaces EVERY occurrence
of a row's search text, so a row whose text occurs twice changes two places at once and can be killed for a reason that is
not its own; a text that is not found is an error at run time. `non_unique_rows` finds both, and a planted duplicate proves
that it does."""

from __future__ import annotations

import re
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
            or (e.startswith("AssertionError: ") and len(e) < 24)
            or e.startswith(
                ("AssertionError: (", "assert")
            )  # a printed tuple or comparison, not a message
            or "] ==" in e
            or "== [" in e
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


EXCEPTION_ONLY = re.compile(r"[A-Za-z_.]*(Error|Exception|Exit|Warning)")


def shape_problems(rows=None, same=None) -> list[tuple[str, str]]:
    """Rows whose `expect` is a shape that cannot tell its own killer assert from another failure: a bare exception type,
    pytest's own `DID NOT RAISE` line (it names no input), a fragment that starts with a quote or an operator (it is the
    middle of a comparison, so it also fits any other line holding that value), and two rows that share one killer and one
    expectation unless `same` (label group -> reason) lists the group with a reason."""
    same = bm.SAME_ASSERT if same is None else same
    rows = bm.M if rows is None else rows
    problems: list[tuple[str, str]] = []
    groups: dict[tuple[str, str], list[str]] = {}
    for m in rows:
        label = m.name.split(" ", 1)[0]
        e = m.expect.strip()
        if EXCEPTION_ONLY.fullmatch(e):
            problems.append((label, "expect is a bare exception type"))
        elif e.startswith("DID NOT RAISE"):
            problems.append((label, "expect is pytest's DID NOT RAISE line"))
        elif e[:1] in "'\"" or e.startswith(("==", "!=", "<", ">", "]", ")", "}")):
            problems.append((label, "expect starts mid-comparison"))
        groups.setdefault((m.only_test, m.expect), []).append(label)
    listed = {tuple(k.split()) for k, reason in same.items() if reason.strip()}
    for labels in groups.values():
        if len(labels) > 1 and tuple(labels) not in listed:
            problems.append(
                (
                    " ".join(labels),
                    "rows share one killer and one expect without a same-assert reason",
                )
            )
    return problems


def test_no_row_has_a_bare_type_a_did_not_raise_a_mid_comparison_fragment_or_an_unexplained_shared_assert() -> (
    None
):
    assert shape_problems() == []


def test_every_same_assert_entry_names_a_group_that_exists_and_has_a_reason() -> None:
    labels = {m.name.split(" ", 1)[0] for m in bm.M}
    for group, reason in bm.SAME_ASSERT.items():
        assert reason.strip(), f"the same-assert group {group!r} has no reason"
        missing = [x for x in group.split() if x not in labels]
        assert not missing, (
            f"the same-assert group {group!r} names rows that do not exist: {missing}"
        )


def test_planted_shapes_are_each_reported() -> None:
    def row(label: str, killer: str, expect: str):
        return bm.mutant(f"{label} planted", "x.py", "a", "b", "t.py", killer, expect)

    rows = [
        row("Z1", "t1", "TypeError"),
        row("Z2", "t2", "DID NOT RAISE"),
        row("Z3", "t3", "DID NOT RAISE <class 'ValueError'>"),
        row("Z4", "t4", "'internal-host' not in"),
        row("Z5", "t5", "== [1, 2]"),
        row("Z6", "t6", "own message of the killer"),
        row("Z7", "t7", "shared message"),
        row("Z8", "t7", "shared message"),
        row("Z9", "t9", "shared again"),
        row("Z10", "t9", "shared again"),
    ]
    got = shape_problems(rows=rows, same={"Z9 Z10": "both break the single assert of t9"})
    assert got == [
        ("Z1", "expect is a bare exception type"),
        ("Z2", "expect is pytest's DID NOT RAISE line"),
        ("Z3", "expect is pytest's DID NOT RAISE line"),
        ("Z4", "expect starts mid-comparison"),
        ("Z5", "expect starts mid-comparison"),
        ("Z7 Z8", "rows share one killer and one expect without a same-assert reason"),
    ]
    assert shape_problems(rows=rows[8:], same={"Z9 Z10": " "}) == [
        ("Z9 Z10", "rows share one killer and one expect without a same-assert reason")
    ], "a same-assert entry with a blank reason was accepted"


INTERPRETER_TEXT = re.compile(
    r"(AttributeError|TypeError|KeyError|NameError|IndexError)\b|has no attribute|object of type|is not subscriptable|"
    r"unexpected keyword|validation errors? for|object is not"
)


def interpreter_text_problems(rows=None, pinned=None) -> list[tuple[str, str]]:
    """Rows whose `expect` is the interpreter's or a library's own error text, unless the row is on the pinned crash list:
    only a row that crashes on purpose may be expected to show that text; any other row must show a message of its test."""
    pinned = bm.CRASH_ROWS if pinned is None else pinned
    problems = []
    for m in bm.M if rows is None else rows:
        label = m.name.split(" ", 1)[0]
        if INTERPRETER_TEXT.search(m.expect) and label not in pinned:
            problems.append(
                (label, "expect is an interpreter message and the row is not a pinned crash row")
            )
    return problems


def test_pin_the_crash_rows_are_exactly_the_pinned_set_and_only_they_expect_an_interpreter_message() -> (
    None
):
    declared = {m.name.split(" ", 1)[0] for m in bm.M if m.allow_crash}
    assert declared == set(bm.CRASH_ROWS), (
        f"crash rows not pinned: {sorted(declared - set(bm.CRASH_ROWS))}; pinned but not crash rows: "
        f"{sorted(set(bm.CRASH_ROWS) - declared)}"
    )
    assert interpreter_text_problems() == []


def test_pin_a_planted_interpreter_message_outside_the_pinned_set_is_reported() -> None:
    rows = [
        bm.mutant(
            "Z1 on",
            "x.py",
            "a",
            "b",
            "t.py",
            "k",
            "AttributeError: 'list' has no x",
            crash="AttributeError",
        ),
        bm.mutant("Z2 off", "x.py", "a", "b", "t.py", "k", "'list' object has no attribute 'get'"),
        bm.mutant("Z3 fine", "x.py", "a", "b", "t.py", "k", "the names were not shown once"),
    ]
    assert interpreter_text_problems(rows=rows, pinned={"Z1"}) == [
        ("Z2", "expect is an interpreter message and the row is not a pinned crash row")
    ]


# PIN: this test also passes on dd827d79 (the fail-before run of batch 10 shows it); it keeps a behaviour from breaking and is not proof of a fix


def test_pin_rows_killed_by_the_same_first_failing_line_of_one_killer_are_reported() -> None:
    from collections import Counter

    kill = Counter(m.only_test for m in bm.M).most_common(1)[0][0]
    names = [m.name for m in bm.M if m.only_test == kill][:2]
    assert len(names) == 2
    same = {names[0]: "assert 1 == 2", names[1]: "assert 1 == 2"}
    assert bm.shared_first_lines(same) == [[n.split(" ", 1)[0] for n in names]]
    assert bm.shared_first_lines({names[0]: "assert 1 == 2", names[1]: "assert 3 == 4"}) == []
    assert bm.shared_first_lines({}) == []


# PIN: this test also passes on dd827d79 (the fail-before run of batch 10 shows it); it keeps a behaviour from breaking and is not proof of a fix


def test_pin_every_killer_named_in_the_table_is_a_test_that_exists_in_its_file() -> None:
    """A renamed or removed killer left its row naming a test that is not there (R9A4 did, found by running it); the run
    then reports an error for the row only when someone runs that row. Checked here for every row, with no run."""
    root = Path(bm.ROOT)
    missing = []
    for m in bm.M:
        text = (root / m.test_file).read_text(encoding="utf-8")
        if f"def {m.only_test}(" not in text:
            missing.append((m.name.split(" ", 1)[0], m.only_test))
    assert missing == []


# PIN: this test also passes on dd827d79 (the fail-before run of batch 10 shows it); it keeps a behaviour from breaking and is not proof of a fix


def test_pin_the_row_count_is_the_number_of_distinct_labels_in_the_table() -> None:
    labels = [m.name.split(" ", 1)[0] for m in bm.M]
    assert len(labels) == len(set(labels)) == len(bm.M) and len(labels) >= 300
