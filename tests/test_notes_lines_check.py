"""The check that a builder's notes hold one line for each new or changed test (tools/notes_lines_check.py).

The tests that need git make their own throwaway repository in a temporary folder."""

import shutil
import subprocess

from tools import notes_lines_check as nlc

OLD = "def test_a():\n    assert 1\n\n\ndef test_b():\n    assert 2\n"
NEW = "def test_a():\n    assert 1\n\n\ndef test_b():\n    assert 3\n\n\ndef test_c():\n    assert 4\n"
REASON = "killing mutant: B10 the clock function reads the real day"


def row(file: str, test: str, reason: str = REASON) -> str:
    return f"| {file} | `{test}` | changed | {reason} |\n"


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


def test_a_name_in_another_rows_reason_cell_or_another_cell_is_no_row_of_its_own():
    notes = (
        row("f.py", "test_a", f"{REASON}; also covers `test_b` and `test_c`")
        + "| `test_c` | `test_a` | changed | killing mutant: B1 something real |\n"
    )
    found = nlc.problems(["test_b", "test_c"], [], notes, "f.py")
    assert len(found) == 2 and all("has no row of its own" in p for p in found), (
        f"an id found in another cell counted as a row: {found}"
    )


def test_the_same_test_name_in_two_files_needs_a_row_for_each_file():
    notes = row("a/test_one.py", "test_x")
    assert nlc.problems(["test_x"], [], notes, "tests/a/test_one.py") == [], (
        "the row of the file, named by the end of its path, was refused"
    )
    found = nlc.problems(["test_x"], [], notes, "tests/b/test_two.py")
    assert found and "has no row of its own" in found[0], (
        f"a row of another file covered a test of this file: {found}"
    )
    assert nlc.problems(["test_x"], [], notes, "tests/xa/test_one.py"), (
        "a file name that only ends alike (not at a path part) matched"
    )


def test_an_async_test_and_a_class_method_are_read_and_named_by_their_class():
    before = "async def test_a():\n    assert 1\n\n\nclass TestK:\n    def test_m(self):\n        assert 1\n"
    after = "async def test_a():\n    assert 2\n\n\nclass TestK:\n    def test_m(self):\n        assert 2\n"
    changed, gone = nlc.changed_tests(before, after)
    assert changed == ["TestK::test_m", "test_a"], f"async or method tests not read: {changed}"
    assert gone == [], gone
    _, gone = nlc.changed_tests(before, "")
    assert gone == ["TestK::test_m", "test_a"], f"deleted async or method tests not read: {gone}"
    assert nlc.problems(["TestK::test_m"], [], row("f.py", "TestK::test_m"), "f.py") == [], (
        "a method row written `Class::test_x` was refused"
    )
    assert nlc.problems(["TestK::test_m"], [], row("f.py", "test_m"), "f.py"), (
        "a method row written without its class counted"
    )


def test_a_changed_helper_constant_or_fixture_lists_each_test_that_uses_it_and_only_those():
    base = (
        "LIMIT = 1\n\n\ndef inner():\n    return 1\n\n\ndef helper():\n    return inner()\n\n\n"
        "def fixture_x():\n    return 1\n\n\n"
        "def test_direct():\n    assert LIMIT\n\n\n"
        "def test_deep():\n    assert helper()\n\n\n"
        "def test_param(fixture_x):\n    assert True\n\n\n"
        "def test_free():\n    assert True\n"
    )
    constant = base.replace("LIMIT = 1", "LIMIT = 2")
    far = base.replace("return 1\n\n\ndef helper", "return 2\n\n\ndef helper")
    fixture = base.replace("def fixture_x():\n    return 1", "def fixture_x():\n    return 3")
    near = base.replace("return inner()", "return inner() + 0")
    got = nlc.changed_tests(base, constant)
    assert got == (["test_direct"], []), f"a change of a constant lists {got}, expected test_direct"
    got = nlc.changed_tests(base, far)
    assert got == (["test_deep"], []), (
        f"a change of a helper two steps away lists {got}, expected test_deep"
    )
    got = nlc.changed_tests(base, fixture)
    assert got == (["test_param"], []), f"a change of a fixture lists {got}, expected test_param"
    got = nlc.changed_tests(base, near)
    assert got == (["test_deep"], []), f"a change of a helper lists {got}, expected test_deep"
    assert nlc.changed_tests(base, base) == ([], []), "an unchanged file lists a test"


def test_a_reason_must_be_real_not_just_long():
    assert nlc.reason_problem(REASON) == "", "a full reason was refused"
    assert "placeholder" in nlc.reason_problem("ok"), "a one-word reason was accepted"
    assert "placeholder" in nlc.reason_problem("n/a"), "a placeholder was accepted"
    assert "fewer than" in nlc.reason_problem("killing mutant B1"), (
        "a three-word reason was accepted"
    )
    assert "names no killing mutant" in nlc.reason_problem(
        "this changed in a way that matters a lot"
    ), "a long reason that names no mutant, run, plant or control was accepted"
    for good in (
        "fails on the old code: 2 failed",
        "plant: a bad input is refused",
        "control: unchanged behaviour passes on the old head",
    ):
        assert nlc.reason_problem(good) == "", f"a real reason was refused: {good}"


def _git(path, *args):
    git = shutil.which("git")
    assert git, "git was not found"
    subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git, "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=path,
        check=True,
        capture_output=True,
    )


def _repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _git(tmp_path, "init", "-q")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_one.py").write_text(OLD, encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    return "HEAD"


def test_a_base_that_does_not_resolve_is_one_problem_and_an_option_is_no_base(
    tmp_path, monkeypatch
):
    base = _repo(tmp_path, monkeypatch)
    (tmp_path / "tests" / "test_one.py").write_text(NEW, encoding="utf-8")
    notes = row("test_one.py", "test_b") + row("test_one.py", "test_c")
    assert nlc.base_resolves(base), "the commit HEAD was not found"
    assert nlc.check(base, notes, ["tests/test_one.py"]) == [], (
        "a changed file with its rows failed"
    )
    assert nlc.check("0" * 40, notes, ["tests/test_one.py"]) == [
        f"the base commit {'0' * 40!r} does not resolve: every test would look new"
    ], "a base that does not exist was not refused as one problem"
    assert not nlc.base_resolves("--all"), "an option was taken as a base"
    (tmp_path / "notes.md").write_text(notes, encoding="utf-8")
    assert nlc.main(["0" * 40, "notes.md", "tests/test_one.py"]) == 1, "a bad base passed"
    assert nlc.main(["--auto", "0" * 40]) == 1, "a bad base passed with --auto"
    assert nlc.main(["--bogus"]) == 2, "a wrong command line was not refused"


def test_auto_reads_the_changed_test_and_notes_files_and_says_when_there_are_no_notes(
    tmp_path, monkeypatch, capsys
):
    base = _repo(tmp_path, monkeypatch)
    (tmp_path / "tests" / "test_one.py").write_text(NEW, encoding="utf-8")
    (tmp_path / "tests" / "sub").mkdir()
    (tmp_path / "tests" / "sub" / "test_deep.py").write_text(
        "def test_deep():\n    assert 1\n", encoding="utf-8"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "tests changed")
    assert nlc.auto_files(f"{base}~1") == (
        ["tests/sub/test_deep.py", "tests/test_one.py"],
        [],
    ), "the changed test files of the change (a nested one too) were not found"
    assert nlc.main(["--auto", f"{base}~1"]) == 1, "changed tests with no notes file passed"
    assert "no builder notes file" in capsys.readouterr().out, "the missing notes were not said"
    notes_dir = tmp_path / "handover" / "evidence" / "T-1" / "b1"
    notes_dir.mkdir(parents=True)
    (notes_dir / "NOTES.md").write_text(
        row("test_one.py", "test_b") + row("test_deep.py", "test_deep"), encoding="utf-8"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "notes")
    assert nlc.main(["--auto", f"{base}~2"]) == 1, "test_c has no row but --auto passed"
    assert "test_c" in capsys.readouterr().out, "the test with no row was not named"
    (notes_dir / "NOTES.md").write_text(
        row("test_one.py", "test_b")
        + row("test_one.py", "test_c")
        + row("test_deep.py", "test_deep"),
        encoding="utf-8",
    )
    assert nlc.main(["--auto", f"{base}~2"]) == 0, "a change with all its rows failed"


def test_auto_says_nothing_to_check_when_no_test_file_changed(tmp_path, monkeypatch, capsys):
    base = _repo(tmp_path, monkeypatch)
    (tmp_path / "other.txt").write_text("x", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "no test change")
    assert nlc.main(["--auto", f"{base}~1"]) == 0, "a change with no test file failed"
    assert "no test file changed" in capsys.readouterr().out, "the empty change was not said"
