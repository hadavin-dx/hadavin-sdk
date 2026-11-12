"""The check that a builder's notes hold one line for every new or changed test (tools/notes_lines_check.py)."""

from tools import notes_lines_check as nlc

OLD = "def test_a():\n    assert 1\n\n\ndef test_b():\n    assert 2\n"
NEW = "def test_a():\n    assert 1\n\n\ndef test_b():\n    assert 3\n\n\ndef test_c():\n    assert 4\n"
REASON = "killing mutant: B10 the clock function reads the real day"


def test_a_changed_and_a_new_test_are_found_and_an_unchanged_one_is_not():
    changed, gone = nlc.changed_tests(OLD, NEW)
    assert changed == ["test_b", "test_c"], f"the changed or new tests found are {changed}"
    assert gone == [], f"a test is reported gone that is not: {gone}"


def test_a_test_that_is_gone_is_a_problem_even_with_a_line():
    changed, gone = nlc.changed_tests(NEW, "def test_a():\n    assert 1\n")
    assert gone == ["test_b", "test_c"], f"the tests that are gone were reported as {gone}"
    found = nlc.problems(changed, gone, "", "f.py")
    assert len(found) == 2 and all("never delete a test" in p for p in found), (
        f"a deleted test is not reported as a problem: {found}"
    )


def test_a_test_with_no_row_or_a_row_with_no_reason_is_a_problem_and_a_full_row_is_not():
    notes = f"| f.py | `test_b` | changed | {REASON} |\n| f.py | `test_c` | new | ok |\n"
    found = nlc.problems(["test_b", "test_c"], [], notes, "f.py")
    assert len(found) == 1 and "test_c" in found[0], f"a row with a one-word reason passed: {found}"
    assert nlc.problems(["test_d"], [], notes, "f.py"), "a test with no row at all passed"
    assert nlc.problems(["test_b"], [], notes, "f.py") == [], "a full row was refused"


def test_a_row_is_read_only_from_a_table_line():
    prose = f"The test `test_b` is covered: {REASON}\n"
    assert nlc.problems(["test_b"], [], prose, "f.py"), (
        "a sentence outside a table counted as a row"
    )
