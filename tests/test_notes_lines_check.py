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
        "fails on the old code (`fail-before.log`): 2 failed",
        "plant: a bad input is refused, see test_plant_a_bad_input",
        "control: unchanged behaviour, the helper has killing mutant B11 for it",
        "fails before the fix (commit 351f2b8b): AttributeError at the first line",
    ):
        assert nlc.reason_problem(good) == "", f"a real reason was refused: {good}"


def test_a_marker_is_a_whole_word_and_something_to_look_up_follows_it():
    # whole words: "implant" is not "plant", "controller" is not "control"
    for bad in (
        "an implant of the new rule with B11 in it",
        "the controller of the loop with B11 in it",
        "the replant B11 changed the day here",
    ):
        assert "names no killing mutant" in nlc.reason_problem(bad), (
            f"a marker found inside another word was accepted: {bad}"
        )
    # "passes on" is not a reason
    assert "names no killing mutant" in nlc.reason_problem(
        "this passes on the old head because nothing changed there at all"
    ), "the phrase `passes on` alone was accepted as a reason"
    # something to look up must follow the marker
    for bad in (
        "plant: the rule is fed a wrong input and refuses it",
        "fails on the old code with a clear message here",
        "killing mutant: it is caught by the tests that look at it",
        "control: nothing of the behaviour changed in this edit",
    ):
        assert "gives nothing to look up" in nlc.reason_problem(bad), (
            f"a reason with no mutant code, test name, file name or commit id after the marker was accepted: {bad}"
        )
    # an identifier BEFORE the marker does not count
    assert "gives nothing to look up" in nlc.reason_problem(
        "B11 is touched here and the plant is described in words only"
    ), "an identifier before the marker was counted as one after it"


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
    found = nlc.auto_files(f"{base}~1")
    assert not isinstance(found, str), f"auto_files refused a good change: {found}"
    assert (found[2], found[3]) == (
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
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "all rows")
    assert nlc.main(["--auto", f"{base}~3"]) == 0, "a change with all its rows failed"


def test_auto_says_nothing_to_check_when_no_test_file_changed(tmp_path, monkeypatch, capsys):
    base = _repo(tmp_path, monkeypatch)
    (tmp_path / "other.txt").write_text("x", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "no test change")
    assert nlc.main(["--auto", f"{base}~1"]) == 0, "a change with no test file failed"
    assert "no test file changed" in capsys.readouterr().out, "the empty change was not said"


# ------------------------------------------------------------------ what the check sees (batch 12)

HELPER_OLD = "VALUE = 1\n\n\ndef helper():\n    return VALUE\n"
HELPER_NEW = "VALUE = 2\n\n\ndef helper():\n    return VALUE\n"


def _loader(files: dict[str, str]):
    return lambda rel: files.get(rel, "")


def _used_through(import_text: str, use_text: str, inside: bool = False):
    """(changed, gone) for a test that uses `helper` of tests/helpers.py through the import form given, when that
    helper changed and the test file did not."""
    if inside:
        source = f"def test_uses():\n    {import_text}\n    assert {use_text}\n\n\ndef test_free():\n    assert 1\n"
    else:
        source = f"{import_text}\n\n\ndef test_uses():\n    assert {use_text}\n\n\ndef test_free():\n    assert 1\n"
    old = _loader({"tests/helpers.py": HELPER_OLD})
    new = _loader({"tests/helpers.py": HELPER_NEW})
    return nlc.changed_tests(source, source, "tests/test_x.py", old, new), nlc.changed_tests(
        source, source, "tests/test_x.py", old, old
    )


def test_a_helper_imported_from_another_tests_module_lists_each_test_that_uses_it():
    # every way a test module names what another test module holds
    listed = (["test_uses"], [])
    for changed, unchanged in (_used_through("from tests.helpers import helper", "helper()"),):
        assert changed == listed, "a helper used by a test through a from-import was not listed"
        assert unchanged == ([], []), "an unchanged helper used through a from-import listed a test"
    changed, unchanged = _used_through("from tests import helpers", "helpers.helper()")
    assert changed == listed, "a helper used by a test through a module import was not listed"
    assert unchanged == ([], []), "an unchanged helper used through a module import listed a test"
    changed, unchanged = _used_through("import tests.helpers as h", "h.helper()")
    assert changed == listed, "a helper used by a test through an import as was not listed"
    assert unchanged == ([], []), "an unchanged helper used through an import as listed a test"
    changed, unchanged = _used_through("from .helpers import helper", "helper()")
    assert changed == listed, "a helper used by a test through a relative import was not listed"
    assert unchanged == ([], []), "an unchanged helper used through a relative import listed a test"
    changed, unchanged = _used_through("from tests.helpers import helper", "helper()", inside=True)
    assert changed == listed, (
        "a helper used by a test through an import inside the test was not listed"
    )
    assert unchanged == ([], []), (
        "an unchanged helper used through an import inside the test listed a test"
    )


def test_a_changed_module_level_import_or_augmented_assignment_lists_the_tests_that_use_the_name():
    base = (
        "import json as codec\nLIMIT = 1\nLIMIT += 1\n\n\n"
        "def test_import():\n    assert codec\n\n\n"
        "def test_limit():\n    assert LIMIT\n\n\n"
        "def test_free():\n    assert 1\n"
    )
    other_import = base.replace("import json as codec", "import pickle as codec")
    other_add = base.replace("LIMIT += 1", "LIMIT += 2")
    assert nlc.changed_tests(base, other_import) == (["test_import"], []), (
        "a changed module-level import did not list the test that uses the name"
    )
    assert nlc.changed_tests(base, other_add) == (["test_limit"], []), (
        "a changed `+=` of a module-level name did not list the test that uses the name"
    )


def test_an_autouse_fixture_that_changed_lists_every_test_of_the_file_and_another_fixture_does_not():
    base = (
        "import pytest\n\n\n"
        "@pytest.fixture(autouse=True)\ndef always():\n    return 1\n\n\n"
        "@pytest.fixture\ndef named():\n    return 1\n\n\n"
        "def test_a():\n    assert 1\n\n\ndef test_b():\n    assert 2\n"
    )
    changed_autouse = base.replace("def always():\n    return 1", "def always():\n    return 2")
    changed_named = base.replace("def named():\n    return 1", "def named():\n    return 2")
    assert nlc.changed_tests(base, changed_autouse) == (["test_a", "test_b"], []), (
        "a changed autouse fixture did not list every test of the file"
    )
    assert nlc.changed_tests(base, changed_named) == ([], []), (
        "a changed fixture that no test names listed a test"
    )


MUTANTS_OLD = (
    "def mutant(name, file):\n    return (name, file)\n\n\n"
    "M = [\n    mutant('A one', 'f'),\n    mutant('A two', 'f'),\n    mutant('A three', 'f'),\n]\n"
)


def test_a_new_altered_or_removed_mutant_and_a_fall_in_the_count_are_seen_in_the_mutant_files():
    rel = "tests/policy_mutants.py"
    new = MUTANTS_OLD.replace("mutant('A one', 'f')", "mutant('A one', 'g')")
    added = MUTANTS_OLD.replace("]\n", "    mutant('A four', 'f'),\n]\n")
    removed = MUTANTS_OLD.replace("    mutant('A three', 'f'),\n", "")
    builder = MUTANTS_OLD.replace("return (name, file)", "return (file, name)")
    assert nlc.changed_tests(MUTANTS_OLD, new, rel) == (["A one"], []), (
        "an altered mutant was not listed"
    )
    assert nlc.changed_tests(MUTANTS_OLD, added, rel) == (["A four"], []), (
        "a new mutant was not listed"
    )
    assert nlc.changed_tests(MUTANTS_OLD, removed, rel) == ([], ["A three"]), (
        "a removed mutant was not reported gone"
    )
    assert nlc.changed_tests(MUTANTS_OLD, builder, rel)[0] == ["A one", "A three", "A two"], (
        "a change of the mutant builder did not list every mutant"
    )
    found = nlc.problems([], ["A three"], "", rel, counts=(3, 2))
    assert any("the mutant count fell from 3 to 2" in p for p in found), (
        f"a fall in the mutant count was not reported: {found}"
    )
    assert not any("count fell" in p for p in nlc.problems([], [], "", rel, counts=(3, 3))), (
        "an equal mutant count was reported as a fall"
    )
    notes = "| policy_mutants.py | `A one` | altered | killing mutant: B12 the day scan, see `fail-before.log` |\n"
    assert nlc.problems(["A one"], [], notes, rel) == [], (
        "a mutant row written in backticks was refused"
    )
    tick = "| policy_mutants.py | A a `.call` of the client | new | killing mutant: A1 see `fail-before.log` |\n"
    assert nlc.problems(["A a `.call` of the client"], [], tick, rel) == [], (
        "a mutant whose name holds a backtick, written in the cell, was refused"
    )
    assert nlc.problems(["A four"], [], notes, rel), "a mutant with no row passed"


def test_a_conftest_function_and_a_fixture_file_are_units_and_a_file_outside_the_kinds_is_none():
    conf = "def make():\n    return 1\n\n\nclass Box:\n    size = 1\n"
    changed, gone = nlc.changed_tests(
        conf, conf.replace("return 1", "return 2"), "tests/conftest.py"
    )
    assert (changed, gone) == (["make"], []), (
        f"a changed conftest function was not the only unit: {changed}"
    )
    rel = "tests/fixtures/policy_sources_2026-11-11.txt"
    assert nlc.kind_of(rel) == "fixture", "a changed fixture file was not of the fixture kind"
    assert nlc.changed_tests("a\n", "a\nb\n", rel) == (["policy_sources_2026-11-11.txt"], []), (
        "a changed fixture file was not one unit named by its file name"
    )
    assert nlc.changed_tests("a\n", "a\n", rel) == ([], []), "an unchanged fixture file was listed"
    assert nlc.kind_of("tests/fixtures/other.txt") == "data", (
        "a data file of another family under tests/ is not in scope (batch 14: any file under tests/ that is "
        "not Python is one unit named by its file name)"
    )
    assert nlc.kind_of("src/hadavin_sdk/x.py") is None, "a file of src is in scope"
    assert nlc.kind_of("tests/test_x.py") == "test"
    assert nlc.kind_of("tests/stage_mutants.py") == "mutants"
    assert nlc.kind_of("tests/sub/conftest.py") == "conftest"


def _rev(path, *args):
    git = shutil.which("git")
    assert git, "git was not found"
    return subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git, "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_auto_diffs_from_the_merge_base_to_the_head_commit_and_reads_blobs_not_the_working_folder(
    tmp_path, monkeypatch, capsys
):
    _repo(tmp_path, monkeypatch)
    _rev(tmp_path, "branch", "-m", "main")
    base = _rev(tmp_path, "rev-parse", "HEAD")
    _rev(tmp_path, "checkout", "-q", "-b", "pr")
    (tmp_path / "tests" / "test_one.py").write_text(NEW, encoding="utf-8")
    notes_dir = tmp_path / "handover" / "evidence" / "T-1" / "b1"
    notes_dir.mkdir(parents=True)
    (notes_dir / "NOTES.md").write_text(
        row("test_one.py", "test_b") + row("test_one.py", "test_c"), encoding="utf-8"
    )
    _rev(tmp_path, "add", "-A")
    _rev(tmp_path, "commit", "-q", "-m", "pr head")
    head = _rev(tmp_path, "rev-parse", "HEAD")
    _rev(tmp_path, "checkout", "-q", "main")
    (tmp_path / "tests" / "test_main_only.py").write_text(
        "def test_m():\n    assert 1\n", encoding="utf-8"
    )
    _rev(tmp_path, "add", "-A")
    _rev(tmp_path, "commit", "-q", "-m", "main moves on")
    moved = _rev(tmp_path, "rev-parse", "HEAD")
    _rev(tmp_path, "merge", "-q", "--no-ff", "-m", "merge", "pr")  # the shape the runner checks out
    # the base is the tip of main (moved), the head is the pull request commit: the change is what `pr` did
    # since it left main, not what main did after that
    found = nlc.auto_files(moved, head)
    assert not isinstance(found, str), f"auto_files refused a made-up merge: {found}"
    assert found[0] == base, (
        f"the merge base is {found[0]}, expected the commit the branch left main at"
    )
    assert found[2] == ["tests/test_one.py"], (
        f"the change lists {found[2]}: a test only main changed was listed, or the head's file was not"
    )
    # blobs of the head commit: edit and delete files in the working folder, the answer stays the same
    (tmp_path / "tests" / "test_one.py").write_text(
        "def test_a():\n    assert 1\n", encoding="utf-8"
    )
    (notes_dir / "NOTES.md").write_text("nothing\n", encoding="utf-8")
    assert nlc.main(["--auto", moved, "--head", head]) == 0, (
        "the check read the working folder, not the blobs of the head commit"
    )
    # a head that does not resolve is one problem line
    assert isinstance(nlc.auto_files(moved, "0" * 40), str), (
        "a head that does not resolve was taken"
    )
    assert nlc.main(["--auto", moved, "--head", "0" * 40]) == 1, (
        "a head that does not resolve passed"
    )


def test_auto_reads_a_failed_diff_or_a_missing_common_ancestor_as_a_problem_never_as_no_change(
    tmp_path, monkeypatch, capsys
):
    base = _repo(tmp_path, monkeypatch)
    (tmp_path / "tests" / "test_one.py").write_text(NEW, encoding="utf-8")
    _rev(tmp_path, "add", "-A")
    _rev(tmp_path, "commit", "-q", "-m", "change")
    real = nlc._git

    def failing(*args):
        if args[0] == "diff":
            return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: bad object")
        return real(*args)

    monkeypatch.setattr(nlc, "_git", failing)
    found = nlc.auto_files(f"{base}~1")
    assert isinstance(found, str) and "failed" in found, (
        f"a failed diff was read as a result: {found}"
    )
    assert nlc.main(["--auto", f"{base}~1"]) == 1, "a failed diff passed as no change"
    monkeypatch.setattr(nlc, "_git", real)
    # histories with no common ancestor (a shallow checkout looks like this)
    _rev(tmp_path, "checkout", "-q", "--orphan", "other")
    _rev(tmp_path, "rm", "-rf", "-q", ".")
    (tmp_path / "x.txt").write_text("x", encoding="utf-8")
    _rev(tmp_path, "add", "-A")
    _rev(tmp_path, "commit", "-q", "-m", "unrelated")
    unrelated = _rev(tmp_path, "rev-parse", "HEAD")
    found = (
        nlc.auto_files(unrelated, "main")
        if _rev(tmp_path, "branch", "--list", "main")
        else nlc.auto_files(unrelated, "master")
    )
    assert isinstance(found, str) and "fetch-depth: 0" in found, (
        f"no common ancestor was not one problem naming the full fetch: {found}"
    )


def test_auto_lists_both_names_of_a_renamed_test_file_so_the_old_tests_are_not_lost(
    tmp_path, monkeypatch, capsys
):
    base = _repo(tmp_path, monkeypatch)
    _rev(tmp_path, "mv", "tests/test_one.py", "tests/test_renamed.py")
    _rev(tmp_path, "commit", "-q", "-m", "rename only")
    found = nlc.auto_files(f"{base}~1")
    assert not isinstance(found, str), found
    assert found[2] == ["tests/test_one.py", "tests/test_renamed.py"], (
        f"a renamed test file lists {found[2]}: the old name is hidden by rename detection"
    )
    assert nlc.main(["--auto", f"{base}~1"]) == 1, "a renamed test file passed with no rows"
    out = capsys.readouterr().out
    assert "existed in the base commit and is gone" in out, (
        f"the tests of the old file name were not reported gone: {out}"
    )


def test_two_mutant_names_that_hold_the_same_backticked_word_each_need_their_own_row():
    rel = "tests/policy_mutants.py"
    one = "A the setting `path_prefix` is read as one part only"
    two = "A a part of the setting `path_prefix` is not ended by a slash"
    row = "| policy_mutants.py | {} | new | killing mutant: A1 see `fail-before.log` |\n"
    both = row.format(one) + row.format(two)
    assert nlc.problems([one, two], [], both, rel) == [], (
        "two rows with the same backticked word were refused"
    )
    shared = (
        f"| policy_mutants.py | {one}; {two} | new | killing mutant: A1 see `fail-before.log` |\n"
    )
    assert nlc.problems([one, two], [], shared, rel) == [], (
        "two mutant names written in one cell were not both found"
    )
    only_two = nlc.problems([one, two], [], row.format(two), rel)
    assert len(only_two) == 1 and one in only_two[0] and "has no row" in only_two[0], (
        f"a mutant whose name shares a backticked word with a mutant that has a row was taken as having a row: {only_two}"
    )
    only_one = nlc.problems([one, two], [], row.format(one), rel)
    assert len(only_one) == 1 and two in only_one[0] and "has no row" in only_one[0], (
        f"the second mutant of the same backticked word was taken as having a row: {only_one}"
    )


# ------------------------------------------------------------------ what the check sees (batch 13)


def test_a_change_to_a_helper_file_alone_lists_the_tests_of_the_files_that_import_it(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    _git(tmp_path, "init", "-q")
    for d in ("tests/contracts", "tests/fixtures"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "tests" / "contracts" / "vault_fake.py").write_text(HELPER_OLD, encoding="utf-8")
    (tmp_path / "tests" / "fixtures" / "fake_slack.py").write_text(HELPER_OLD, encoding="utf-8")
    (tmp_path / "tests" / "test_uses_contract.py").write_text(
        "from tests.contracts.vault_fake import helper\n\n\ndef test_c():\n    assert helper()\n\n\n"
        "def test_free():\n    assert 1\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_uses_fixture.py").write_text(
        "import tests.fixtures.fake_slack\n\n\ndef test_f():\n    assert tests.fixtures.fake_slack.helper()\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    (tmp_path / "tests" / "contracts" / "vault_fake.py").write_text(HELPER_NEW, encoding="utf-8")
    (tmp_path / "tests" / "fixtures" / "fake_slack.py").write_text(HELPER_NEW, encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "helpers only")
    assert nlc.main(["--auto", "HEAD~1"]) == 1, (
        "a change that touches only helper files under tests/ passed as nothing to check"
    )
    out = capsys.readouterr().out
    assert "tests/test_uses_contract.py: the test test_c is new or changed" in out, (
        f"the test that imports a changed helper by `from` was not listed: {out}"
    )
    assert "tests/test_uses_fixture.py: the test test_f is new or changed" in out, (
        f"the test that imports a changed helper by a plain `import tests.x.y` was not listed: {out}"
    )
    assert "test_free" not in out, f"a test that does not use the helper was listed: {out}"


def test_a_plain_import_of_a_tests_module_is_followed_through_its_dotted_chain():
    source = (
        "import tests.helpers\nimport tests.other\n\n\ndef test_a():\n"
        "    assert tests.helpers.helper()\n\n\ndef test_b():\n    assert tests.other.helper()\n"
    )
    other = "VALUE = 5\n\n\ndef helper():\n    return VALUE\n"
    old = _loader({"tests/helpers.py": HELPER_OLD, "tests/other.py": other})
    new = _loader({"tests/helpers.py": HELPER_NEW, "tests/other.py": other})
    got = nlc.changed_tests(source, source, "tests/test_x.py", old, new)
    assert got == (["test_a"], []), (
        f"with two plain imports of tests modules the changed one lists {got}, expected only test_a"
    )
    new_other = _loader({"tests/helpers.py": HELPER_OLD, "tests/other.py": other.replace("5", "6")})
    got = nlc.changed_tests(source, source, "tests/test_x.py", old, new_other)
    assert got == (["test_b"], []), (
        f"the second plain import was not followed: {got}, expected only test_b"
    )


def test_a_bare_file_name_in_a_row_serves_only_a_file_whose_name_no_other_path_has():
    notes = row("test_x.py", "test_a")
    both = frozenset({"tests/test_x.py", "tests/contracts/test_x.py"})
    assert nlc.problems(["test_a"], [], notes, "tests/test_x.py", None, both), (
        "a bare file name in a row served a file whose name another path also has"
    )
    assert nlc.problems(["test_a"], [], notes, "tests/contracts/test_x.py", None, both), (
        "a bare file name in a row served the second file of the same name"
    )
    assert (
        nlc.problems(
            ["test_a"],
            [],
            row("contracts/test_x.py", "test_a"),
            "tests/contracts/test_x.py",
            None,
            both,
        )
        == []
    ), "a row with the end of the path was refused"
    assert (
        nlc.problems(
            ["test_a"], [], row("tests/test_x.py", "test_a"), "tests/test_x.py", None, both
        )
        == []
    ), "a row with the whole path was refused"
    alone = frozenset({"tests/test_x.py", "tests/test_y.py"})
    assert nlc.problems(["test_a"], [], notes, "tests/test_x.py", None, alone) == [], (
        "a bare file name no other path shares was refused"
    )


def test_a_module_level_mark_a_class_mark_and_module_level_code_list_every_test_of_the_file():
    body = "\n\ndef test_a():\n    assert 1\n\n\nclass TestK:\n    def test_m(self):\n        assert 1\n"
    marked = "import pytest\n\npytestmark = pytest.mark.skip(reason='r')\n" + body
    plain = "import pytest\n\npytestmark = pytest.mark.skipif(False, reason='r')\n" + body
    got = nlc.changed_tests(plain, marked)
    assert got == (["TestK::test_m", "test_a"], []), (
        f"a changed module-level pytestmark lists {got}, expected both tests"
    )
    cls_old = "import pytest\n\n\nclass TestK:\n    def test_m(self):\n        assert 1\n"
    cls_new = cls_old.replace("class TestK:", "@pytest.mark.skip\nclass TestK:")
    assert nlc.changed_tests(cls_old, cls_new) == (["TestK::test_m"], []), (
        "a class decorator that skips the class lists no method"
    )
    cls_attr = cls_old.replace("class TestK:\n", "class TestK:\n    pytestmark = 1\n")
    assert nlc.changed_tests(cls_old, cls_attr) == (["TestK::test_m"], []), (
        "a class-level pytestmark lists no method"
    )
    code_old = "import pytest\n\nif False:\n    pytest.skip('s', allow_module_level=True)\n" + body
    code_new = code_old.replace("if False", "if True")
    assert nlc.changed_tests(code_old, code_new) == (["TestK::test_m", "test_a"], []), (
        "module-level code that skips the file lists no test"
    )
    assert nlc.changed_tests(code_old, code_old) == ([], []), (
        "unchanged module-level code lists a test"
    )


def test_a_conftest_assignment_is_a_unit_with_all_assignments_of_its_name():
    rel = "tests/conftest.py"
    old = "collect_ignore = ['a.py']\n\n\ndef fx():\n    return 1\n"
    new = "collect_ignore = ['a.py', 'b.py']\n\n\ndef fx():\n    return 1\n"
    assert nlc.changed_tests(old, new, rel) == (["collect_ignore"], []), (
        "a changed collect_ignore of a conftest is not a unit"
    )
    more = old + "collect_ignore += ['c.py']\n"
    assert nlc.changed_tests(old, more, rel) == (["collect_ignore"], []), (
        "an added `+=` of a conftest name is not part of the unit"
    )
    plugins = "pytest_plugins = ['x']\n"
    assert nlc.changed_tests("", plugins, rel) == (["pytest_plugins"], []), (
        "a new pytest_plugins of a conftest is not a unit"
    )
    assert nlc.changed_tests(old, old, rel) == ([], []), "an unchanged conftest lists a unit"


# ------------------------------------------------------------------ a row must be whole and must point at something real (batch 13)


def test_a_mutant_row_serves_only_the_mutant_whose_whole_cell_or_exact_item_it_is():
    # the name holds a backtick, so it is written in the cell and not in backticks; `X `a`` must not borrow the row of
    # the longer name `X `a` b` (a substring), and an exact `;` item of a cell is that name's row
    rel = "tests/policy_mutants.py"
    reason = "killing mutant B1 in `policy_mutants.py`"
    longer = f"| policy_mutants.py | X `a` b | new | {reason} |\n"
    assert nlc.problems(["X `a`"], [], longer, rel), (
        "a mutant with no row of its own borrowed the row of a longer name by substring"
    )
    assert nlc.problems(["X `a` b"], [], longer, rel) == [], "the row of the whole name was refused"
    listed = f"| policy_mutants.py | X `a`; Y `b` | new | {reason} |\n"
    assert nlc.problems(["Y `b`"], [], listed, rel) == [], "an exact `;` item of a cell was refused"
    assert nlc.problems(["Y"], [], listed, rel), "a part of an item of a cell served as its row"


def test_a_reason_must_point_at_a_test_a_log_file_and_a_mutant_that_exist():
    refs = nlc.Refs(
        frozenset({"test_real"}), frozenset({"B1 a real mutant"}), frozenset({"real.log"})
    )
    good = "killing mutant `B1 a real mutant` through test_real; raw output in real.log"
    assert nlc.reference_problems(good, refs) == [], "names that exist were refused"
    bad = nlc.reference_problems("killing mutant `B1 no such mutant`, test_gone and gone.log", refs)
    assert len(bad) == 3 and any("no such mutant" in b for b in bad), (
        f"a mutant, a test and a log file that do not exist were not each reported: {bad}"
    )
    rows = row("test_x.py", "test_a", "control: see test_gone for the failing case")
    found = nlc.problems(["test_a"], [], rows, "tests/test_x.py", None, None, refs)
    assert len(found) == 1 and "points at nothing" in found[0], (
        f"a row naming a test that is in no test file passed: {found}"
    )
    assert nlc.problems(["test_a"], [], rows, "tests/test_x.py") == [], (
        "without refs a row is checked for form only (the unit-test default)"
    )


def test_the_refs_of_a_tree_are_its_tests_its_mutant_names_and_the_files_of_its_logs_folders():
    files = {
        "tests/test_a.py": "def test_one():\n    assert 1\n\n\nclass TestK:\n    def test_two(self):\n        assert 1\n",
        "tests/policy_mutants.py": "M = [mutant('B1 first', 'f', 'o', 'n', 'test_one', 'e')]\n",
    }
    tree = [*files, "handover/evidence/x/logs/run.log", "handover/evidence/x/NOTES.md"]
    refs = nlc._refs(tree, _loader(files))
    assert refs.tests == {"test_one", "test_two", "test_a"}, (
        f"the tests of the tree and the names of its test files are {sorted(refs.tests)}"
    )
    assert refs.mutants == {"B1 first"}, f"the mutants of the tree are {sorted(refs.mutants)}"
    assert refs.logs == {"handover/evidence/x/logs/run.log"}, (
        f"the logs of the tree are {sorted(refs.logs)}"
    )


def test_auto_refuses_a_row_whose_reason_names_a_test_or_a_log_file_that_is_in_no_file_of_the_commit(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    _git(tmp_path, "init", "-q")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    assert 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    assert 2\n", encoding="utf-8")
    notes_dir = tmp_path / "handover" / "evidence" / "x"
    (notes_dir / "logs").mkdir(parents=True)
    (notes_dir / "logs" / "run.log").write_text("raw\n", encoding="utf-8")

    def write(reason: str) -> None:
        (notes_dir / "NOTES.md").write_text(row("test_a.py", "test_a", reason), encoding="utf-8")
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "notes")

    write("fails on the base commit, see test_a and run.log for the raw output")
    assert nlc.main(["--auto", "HEAD~1"]) == 0, (
        f"a row naming a test and a log file that exist was refused: {capsys.readouterr().out}"
    )
    write("fails on the base commit, see test_gone and gone.log for the raw output")
    assert nlc.main(["--auto", "HEAD~2"]) == 1, (
        "a row naming a test and a log file that are in no file of the commit passed `--auto`"
    )
    out = capsys.readouterr().out
    assert "test_gone is in no test file" in out and "gone.log is in no logs/ folder" in out, (
        f"the missing test and the missing log file were not each named: {out}"
    )


# ------------------------------------------------------------------ every link between code and tests (batch 14)

_BODY = "\n\ndef test_a():\n    assert 1\n\n\ndef test_b():\n    assert 2\n"


class _Tree(dict):
    """A loader for `changed_tests` that also carries the paths of the files (`.files`), like the real one."""

    def __init__(self, files):
        super().__init__(files)
        self.files = sorted(files)

    def __call__(self, rel):
        return self.get(rel, "")


def _changed(old, new, rel="tests/test_x.py", before=None, after=None):
    """The changed units of a file; `before` and `after` are the files around it (path -> text) before and after."""
    if before is None and after is None:
        return nlc.changed_tests(old, new, rel)[0]
    if isinstance(before, _Tree):  # a loader that carries the paths of its files
        return nlc.changed_tests(old, new, rel, before, after)[0]
    return nlc.changed_tests(
        old, new, rel, lambda r: (before or {}).get(r, ""), lambda r: (after or {}).get(r, "")
    )[0]


def test_a_constant_is_followed_through_the_value_behind_it():
    skip = "import pytest\nSKIP = {}\npytestmark = pytest.mark.skipif(SKIP, reason='r')\n" + _BODY
    got = _changed(skip.format("False"), skip.format("True"))
    assert got == ["test_a", "test_b"], (
        f"a changed SKIP read by pytestmark listed {got}, not both tests"
    )
    chain = "A = {}\nB = A + 1\n\n\ndef test_a():\n    assert B\n\n\ndef test_b():\n    assert 2\n"
    got = _changed(chain.format(1), chain.format(2))
    assert got == ["test_a"], f"a change of A, read through B = A + 1, listed {got}, not test_a"
    built = "def _build():\n    return {}\n\n\nX = _build()\n\n\ndef test_a():\n    assert X\n\n\ndef test_b():\n    assert 2\n"
    got = _changed(built.format(1), built.format(2))
    assert got == ["test_a"], (
        f"a change of the function that builds a constant listed {got}, not test_a"
    )
    pair = "A, B = 1, {}\n\n\ndef test_a():\n    assert B\n\n\ndef test_b():\n    assert 2\n"
    got = _changed(pair.format(2), pair.format(3))
    assert got == ["test_a"], f"a change of a tuple target listed {got}, not test_a"
    typed = (
        "LIMIT: int = {}\n\n\ndef test_a():\n    assert LIMIT\n\n\ndef test_b():\n    assert 2\n"
    )
    got = _changed(typed.format(1), typed.format(2))
    assert got == ["test_a"], f"a change of an annotated constant listed {got}, not test_a"
    assert _changed(skip.format("False"), skip.format("False")) == [], (
        "an unchanged constant listed a test"
    )


def test_each_way_a_file_or_a_class_is_switched_off_or_changed_lists_the_tests_it_acts_on():
    both = ["test_a", "test_b"]
    k = "import pytest\n\n\nclass TestK:\n{}\n    def test_m(self):\n        assert 1\n"
    fn = "def {}(x):\n    {}\n" + _BODY
    got = _changed("__test__ = True" + _BODY, "__test__ = False" + _BODY)
    assert got == both, f"a changed __test__ listed {got}, expected both tests"
    assert _changed("__test__ = True" + _BODY, "__test__ = True" + _BODY) == [], (
        "an unchanged __test__ listed a test"
    )
    got = _changed(fn.format("setup_module", "pass"), fn.format("setup_module", "raise SystemExit"))
    assert got == both, f"a changed setup_module listed {got}, expected both tests"
    got = _changed(
        fn.format("teardown_module", "pass"), fn.format("teardown_module", "raise SystemExit")
    )
    assert got == both, f"a changed teardown_module listed {got}, expected both tests"
    got = _changed(
        fn.format("setup_function", "pass"), fn.format("setup_function", "raise SystemExit")
    )
    assert got == both, f"a changed setup_function listed {got}, expected both tests"
    got = _changed(
        fn.format("teardown_function", "pass"), fn.format("teardown_function", "raise SystemExit")
    )
    assert got == both, f"a changed teardown_function listed {got}, expected both tests"
    got = _changed(
        fn.format("pytest_generate_tests", "pass"), fn.format("pytest_generate_tests", "return 0")
    )
    assert got == both, f"a changed pytest_generate_tests listed {got}, expected both tests"
    got = _changed(
        fn.format("pytest_collection_modifyitems", "pass"),
        fn.format("pytest_collection_modifyitems", "return 0"),
    )
    assert got == both, f"a changed pytest_collection_modifyitems listed {got}, expected both tests"
    helper = "    def _h(self):\n        return {}\n"
    with_h = k.format(helper).replace("assert 1", "assert self._h()")
    got = _changed(with_h.format(1), with_h.format(0))
    assert got == ["TestK::test_m"], f"a changed helper method of a test class listed {got}"
    setup = "    def setup_method(self, m):\n        {}\n"
    got = _changed(k.format(setup.format("pass")), k.format(setup.format("pytest.skip('s')")))
    assert got == ["TestK::test_m"], f"a changed setup_method listed {got}"
    klass = "    @classmethod\n    def setup_class(cls):\n        {}\n"
    got = _changed(k.format(klass.format("pass")), k.format(klass.format("pytest.skip('s')")))
    assert got == ["TestK::test_m"], f"a changed setup_class listed {got}"
    fixture = "    @pytest.fixture(autouse=True)\n    def f(self):\n        yield {}\n"
    got = _changed(k.format(fixture.format(1)), k.format(fixture.format(2)))
    assert got == ["TestK::test_m"], f"a changed autouse fixture of a test class listed {got}"
    unreached = k.format(helper)
    assert _changed(unreached.format(1), unreached.format(0)) == [], (
        "a helper method that the test does not reach listed a test through self"
    )


def test_a_unittest_class_and_a_file_ending_in_test_are_read_like_a_test_class_and_a_test_file():
    case = "import unittest\n\n\nclass Foo(unittest.TestCase):\n    def test_m(self):\n        self.assertTrue({})\n"
    got = _changed(case.format(1), case.format(0))
    assert got == ["Foo::test_m"], f"a changed method of a unittest.TestCase listed {got}"
    for rel in ("tests/x_test.py", "tests/sub/deep/test_y.py", "tests/sub/z_test.py"):
        assert nlc.kind_of(rel) == "test", f"{rel} is a test file of pytest and was not read as one"
    assert nlc.kind_of("tests/helper.py") is None, (
        "a plain python file under tests was read as a test"
    )


def test_module_code_and_a_fixture_of_a_conftest_list_what_they_act_on():
    rel = "tests/conftest.py"
    loop = "import os\nfor k in ('A',):\n    os.environ.pop(k, None)\n\n\ndef fx():\n    return 1\n"
    no_loop = "import os\n\n\ndef fx():\n    return 1\n"
    _, gone = nlc.changed_tests(loop, no_loop, rel)
    assert gone == [nlc.CONFTEST_CODE], (
        f"a deleted `for` block of a conftest left {gone}, not its code unit"
    )
    appended = "collect_ignore = []\ncollect_ignore.append('a.py')\n"
    assert nlc.changed_tests(appended, "collect_ignore = []\n", rel)[1] == [nlc.CONFTEST_CODE], (
        "a deleted collect_ignore.append call of a conftest was not seen as a gone unit"
    )
    sub = "import os\nos.environ['A'] = {}\n"
    assert nlc.CONFTEST_CODE in nlc.changed_tests(sub.format("'x'"), sub.format("'y'"), rel)[0], (
        "a changed subscript assignment of a conftest is not part of its code unit"
    )
    fixture = "import pytest\n\n\n@pytest.fixture\ndef thing():\n    return {}\n"
    uses = "def test_a(thing):\n    assert thing\n\n\ndef test_b():\n    assert 1\n"
    before, after = {rel: fixture.format(1)}, {rel: fixture.format(0)}
    assert _changed(uses, uses, "tests/test_x.py", before, after) == ["test_a"], (
        "a changed conftest fixture did not list the test that takes it as a parameter"
    )
    deeper = {"tests/sub/conftest.py": fixture.format(5)}
    assert (
        _changed(uses, uses, "tests/sub/test_x.py", {**before, **deeper}, {**after, **deeper}) == []
    ), "a fixture of a conftest further away listed a test that a nearer conftest serves"


def test_a_pytest_settings_file_a_root_conftest_and_a_data_file_are_units_and_a_dependency_change_is_not():
    ini = "[tool.pytest.ini_options]\naddopts = '{}'\n\n[project]\ndependencies = ['{}']\n"
    got = nlc.changed_tests(
        ini.format("-q", "a"), ini.format("-q --ignore=tests", "a"), "pyproject.toml"
    )
    assert got == (["pyproject.toml"], []), (
        f"a changed pytest option of pyproject.toml listed {got}"
    )
    got = nlc.changed_tests(ini.format("-q", "a"), ini.format("-q", "b"), "pyproject.toml")
    assert got == ([], []), f"a changed dependency of pyproject.toml listed {got}"
    old, new = "[pytest]\naddopts = -q\n", "[pytest]\naddopts = -x\n"
    got = nlc.changed_tests(old, new, "pytest.ini")
    assert got == (["pytest.ini"], []), f"a changed pytest.ini listed {got}"
    got = nlc.changed_tests(old, new, "tox.ini")
    assert got == (["tox.ini"], []), f"a changed tox.ini listed {got}"
    got = nlc.changed_tests(old, new, "setup.cfg")
    assert got == (["setup.cfg"], []), f"a changed setup.cfg listed {got}"
    got = nlc.changed_tests("def fx():\n    return 1\n", "def fx():\n    return 2\n", "conftest.py")
    assert got == (["fx"], []), f"a changed conftest at the root listed {got}"
    got = nlc.changed_tests("a\n", "b\n", "tests/data/cases.json")
    assert got == (["cases.json"], []), f"a changed data file under tests listed {got}"
    assert nlc.kind_of("src/hadavin_sdk/x.json") is None, (
        "a file outside tests was read as a data file"
    )


def test_a_helper_two_imports_away_lists_the_test_that_reaches_it_in_each_direction():
    use = "from tests.helpers import helper\n\n\ndef test_uses():\n    assert helper()\n\n\ndef test_free():\n    assert 1\n"
    middle = "from tests.contracts.kinds.deep import deep\n\n\ndef helper():\n    return deep()\n"
    deep = "def deep():\n    return {}\n"
    files = {"tests/helpers.py": middle}
    before = {**files, "tests/contracts/kinds/deep.py": deep.format(1)}
    after = {**files, "tests/contracts/kinds/deep.py": deep.format(2)}
    got = _changed(use, use, "tests/test_x.py", before, after)
    assert got == ["test_uses"], (
        f"a helper reached through another helper listed {got}, not test_uses"
    )
    got = _changed(use, use, "tests/test_x.py", before, before)
    assert got == [], "an unchanged helper of a second level listed a test"
    middle_plain = (
        "import tests.contracts.kinds.deep as d\n\n\ndef helper():\n    return d.deep()\n"
    )
    files = {"tests/helpers.py": middle_plain}
    before = {**files, "tests/contracts/kinds/deep.py": deep.format(1)}
    after = {**files, "tests/contracts/kinds/deep.py": deep.format(2)}
    assert _changed(use, use, "tests/test_x.py", before, after) == ["test_uses"], (
        "a helper reached through an import as of another helper was not followed"
    )


def test_a_file_that_imports_modules_by_a_name_worked_out_at_run_time_lists_what_it_reaches():
    # `tests/contracts/conftest.py` imports every module of `tests/contracts/kinds/` with pkgutil and importlib; a
    # change of such a module (here the value `azure_secret_client` returns) changes what the contract tests do
    conftest = (
        "import importlib\nimport pkgutil\n\nfrom tests.contracts import kinds\n\n"
        "for _m in pkgutil.iter_modules(kinds.__path__):\n"
        "    importlib.import_module(f'{kinds.__name__}.{_m.name}')\n"
    )
    kind = "def make():\n    return {}\n"
    test = "def test_a():\n    assert 1\n"
    base = {
        "tests/contracts/conftest.py": conftest,
        "tests/contracts/kinds/__init__.py": "",
        "tests/contracts/test_k.py": test,
    }
    before = _Tree({**base, "tests/contracts/kinds/k.py": kind.format(1)})
    after = _Tree({**base, "tests/contracts/kinds/k.py": kind.format(2)})
    got = _changed(test, test, "tests/contracts/test_k.py", before, after)
    assert got == ["test_a"], (
        f"a change of a module the conftest imports by a run-time name listed {got}, not test_a"
    )
    same = _changed(test, test, "tests/contracts/test_k.py", before, before)
    assert same == [], f"an unchanged module reached by a run-time import listed {same}"
    named = (
        conftest.replace(
            "for _m in pkgutil.iter_modules(kinds.__path__):\n"
            "    importlib.import_module(f'{kinds.__name__}.{_m.name}')\n",
            "importlib.import_module('tests.contracts.kinds.k')\n",
        )
        .replace("import pkgutil\n", "")
        .replace("from tests.contracts import kinds\n\n", "")
    )
    base["tests/contracts/conftest.py"] = named
    before = _Tree({**base, "tests/contracts/kinds/k.py": kind.format(1)})
    after = _Tree({**base, "tests/contracts/kinds/k.py": kind.format(2)})
    got = _changed(test, test, "tests/contracts/test_k.py", before, after)
    assert got == ["test_a"], (
        f"a module named as text in an import_module call listed {got}, not test_a"
    )
    base["tests/contracts/conftest.py"] = conftest
    elsewhere = _Tree({**base, "tests/other/k.py": kind.format(1)})
    moved = _Tree({**base, "tests/other/k.py": kind.format(2)})
    assert _changed(test, test, "tests/contracts/test_k.py", elsewhere, moved) == [], (
        "a module outside every named or imported folder listed a test"
    )
    own = (
        "import importlib\nfrom tests import contracts\n\nimportlib.import_module('x')\n\n\n"
        "def test_a():\n    assert 1\n\n\ndef test_b():\n    assert {}\n"
    )
    folder = {"tests/contracts/__init__.py": ""}
    got = _changed(
        own.format(1),
        own.format(2),
        "tests/contracts/test_own.py",
        _Tree({**folder, "tests/contracts/test_own.py": own.format(1)}),
        _Tree({**folder, "tests/contracts/test_own.py": own.format(2)}),
    )
    assert got == ["test_b"], (
        f"a file inside the folder it imports by a run-time name listed {got}, not only test_b"
    )


def test_a_new_function_that_nothing_uses_needs_no_row_and_the_one_that_a_test_uses_does():
    # the rule written in the module docstring: a unit that no test, fixture, conftest, import or mutant reaches
    # changes no run, so it has no row; the change that makes a test use it lists that test
    helper = "VALUE = 1\n\n\ndef helper():\n    return VALUE\n"
    plus = helper + "\n\ndef unused():\n    return 5\n"
    use = "from tests.helpers import helper\n\n\ndef test_uses():\n    assert helper()\n\n\ndef test_free():\n    assert 1\n"
    got = _changed(
        use, use, "tests/test_x.py", {"tests/helpers.py": helper}, {"tests/helpers.py": plus}
    )
    assert got == [], f"a new function that nothing uses listed {got}"
    uses_new = use.replace("assert helper()", "assert helper() and unused()").replace(
        "import helper", "import helper, unused"
    )
    got = _changed(
        use, uses_new, "tests/test_x.py", {"tests/helpers.py": plus}, {"tests/helpers.py": plus}
    )
    assert got == ["test_uses"], f"a test that began to use the new function listed {got}"
    assert "needs no row" in nlc.__doc__, (
        "the rule for a new unused function is not written in the docstring"
    )


def test_a_row_whose_unit_cell_names_a_mutant_or_a_test_that_exists_nowhere_is_a_problem():
    refs = nlc.Refs(
        frozenset({"test_real"}),
        frozenset({"B1 real one"}),
        frozenset(),
        {
            "tests/policy_mutants.py": frozenset({"B1 real one"}),
            "tests/test_x.py": frozenset({"test_real"}),
        },
    )
    reason = "killing mutant `B1 real one` here"
    notes = (
        f"| policy_mutants.py | `B99 no such mutant exists here` | new | {reason} |\n"
        f"| test_x.py | `test_gone` | new | {reason} |\n"
        f"| test_x.py | `test_real` | new | {reason} |\n"
        f"| policy_mutants.py | B1 real one | new | {reason} |\n"
    )
    found = nlc.stale_row_problems(notes, refs)
    assert len(found) == 2, (
        f"a row naming a mutant and a row naming a test that exist nowhere gave {found}"
    )
    assert any("B99 no such mutant" in f for f in found), (
        f"the unit cell with a mutant that exists nowhere: {found}"
    )
    assert any("test_gone" in f for f in found), (
        f"the unit cell with a test that exists nowhere: {found}"
    )


def test_a_helper_that_a_mutant_call_reaches_is_part_of_the_mutant():
    src = "def helper():\n    return {}\n\n\ndef other():\n    return 1\n\n\nM = [mutant('B1 n', f, 'a', helper(), 't', 'e'), mutant('B2 m', f, 'a', 'b', 't', 'e')]\n"
    got = nlc.changed_tests(src.format(1), src.format(2), "tests/policy_mutants.py")
    assert got == (["B1 n"], []), (
        f"a changed helper that one mutant calls listed {got}, not only B1"
    )


# ------------------------------------------------------------------ the reference check (batch 14)


def test_a_mutant_name_without_a_code_is_checked_and_a_quote_of_a_message_is_not():
    refs = nlc.Refs(
        frozenset({"test_real"}),
        frozenset({"B1 real one", "Kinds: a kind moved", "m6 a key twice"}),
        frozenset(),
    )
    for name in ("Kinds: a kind moved", "m6 a key twice", "B1 real one"):
        found = nlc.reference_problems(f"killing mutant `{name}`", refs)
        assert found == [], "a mutant name that exists was refused"
    found = nlc.reference_problems("killing mutant `Kinds: a kind nowhere`", refs)
    assert found and "is in no mutant file" in found[0], (
        f"a mutant name without a code that exists nowhere was accepted: {found}"
    )
    found = nlc.reference_problems("killing mutant `m6 a wrong name`", refs)
    assert found and "is in no mutant file" in found[0], (
        f"a mutant name with a lower-case code that exists nowhere was accepted: {found}"
    )
    found = nlc.reference_problems("killing mutant `B99 no such mutant`", refs)
    assert found and "is in no mutant file" in found[0], (
        f"a mutant name with a code that no mutant has was accepted: {found}"
    )
    quote = "killing mutant `B1 real one`, killed by test_real with `the empty change was not said`"
    assert nlc.reference_problems(quote, refs) == [], (
        "a quote of a message was read as a mutant name"
    )


def test_a_log_is_found_in_the_folder_of_the_notes_that_names_it_or_by_the_end_of_its_path():
    refs = nlc.Refs(
        frozenset(),
        frozenset(),
        frozenset({"handover/evidence/x/logs/a.log", "handover/evidence/y/logs/b.log"}),
    )
    reason = "fails on abc1234 with the output in {}"
    ok = nlc.reference_problems(reason.format("a.log"), refs, "handover/evidence/x")
    assert ok == [], f"a log in the folder of its notes was refused: {ok}"
    wrong = nlc.reference_problems(reason.format("b.log"), refs, "handover/evidence/x")
    assert wrong and "b.log" in wrong[0], "a log of another folder served the notes of this folder"
    by_path = nlc.reference_problems(reason.format("y/logs/b.log"), refs, "handover/evidence/x")
    assert by_path == [], f"a log written with the end of its path was refused: {by_path}"
    gone = nlc.reference_problems(reason.format("x/logs/b.log"), refs, "handover/evidence/x")
    assert gone, "a log written with a path that holds no such file was accepted"


# ---- batch 15 (round 14 group 3): links between a changed unit and the tests that use it that were not followed ----


def test_a_constant_bound_by_a_walrus_inside_another_assignment_lists_the_test_that_reads_it():
    src = "W = (WALRUS := {})\n\n\ndef test_a():\n    assert WALRUS\n\n\ndef test_b():\n    assert 1\n"
    got = _changed(src.format(1), src.format(2))
    assert got == ["test_a"], f"a changed walrus constant listed {got}, expected only test_a"
    assert _changed(src.format(1), src.format(1)) == [], "an unchanged walrus listed a test"
    annotated = src.replace("W = (", "W: int = (")
    got = _changed(annotated.format(1), annotated.format(2))
    assert got == ["test_a"], f"a changed walrus behind an annotated assignment listed {got}"


def test_the_set_up_and_tear_down_methods_of_a_unittest_case_list_its_tests():
    case = (
        "import unittest\n\n\nclass Case(unittest.TestCase):\n    {}\n"
        "    def test_one(self):\n        self.assertTrue(1)\n"
    )
    for name, body in (
        ("setUp", "def setUp(self):\n        self.x = {}"),
        ("setUpClass", "@classmethod\n    def setUpClass(cls):\n        cls.x = {}"),
        ("tearDown", "def tearDown(self):\n        self.x = {}"),
        ("tearDownClass", "@classmethod\n    def tearDownClass(cls):\n        cls.x = {}"),
        ("asyncSetUp", "async def asyncSetUp(self):\n        self.x = {}"),
    ):
        got = _changed(case.format(body.format(1)), case.format(body.format(2)))
        assert got == ["Case::test_one"], f"a changed {name} listed {got}, expected Case::test_one"
    module = "import unittest\n\n\ndef {}():\n    pass\n" + _BODY
    for name in ("setUpModule", "tearDownModule"):
        got = _changed(module.format(name), module.format(name).replace("pass", "raise SystemExit"))
        assert got == ["test_a", "test_b"], f"a changed {name} listed {got}, expected both tests"


def test_a_fixture_named_as_a_text_by_usefixtures_or_getfixturevalue_lists_the_test():
    base = (
        "import pytest\n\n\n@pytest.fixture\ndef fx():\n    return {}\n\n\n"
        "{}\n\n\ndef test_use(request):\n    {}\n\n\ndef test_free():\n    assert 1\n"
    )
    by_mark = base.format("{}", '@pytest.mark.usefixtures("fx")', "assert 1")
    got = _changed(by_mark.format(1), by_mark.format(2))
    assert got == ["test_use"], f"a fixture named by usefixtures listed {got}, expected test_use"
    by_call = base.format("{}", "", "assert request.getfixturevalue('fx')")
    got = _changed(by_call.format(1), by_call.format(2))
    assert got == ["test_use"], (
        f"a fixture named by getfixturevalue listed {got}, expected test_use"
    )
    mark_all = "pytestmark = pytest.mark.usefixtures('fx')\n"
    whole = by_call.replace("assert request.getfixturevalue('fx')", "assert 1").replace(
        "\n\n\ndef test_use", f"\n\n{mark_all}\n\ndef test_use", 1
    )
    got = _changed(whole.format(1), whole.format(2))
    assert got == ["test_free", "test_use"], f"a module-wide usefixtures listed {got}"


def test_a_module_named_in_pytest_plugins_or_in_addopts_acts_on_the_tests_below_the_conftest():
    conftest = "pytest_plugins = ['tests.plugmod']\n"
    test = "def test_pp():\n    assert 1\n"
    plugin = (
        "import pytest\n\n\n@pytest.fixture(autouse=True)\ndef pm_fx():\n    yield {}\n\n\n"
        "def pytest_collection_modifyitems(config, items):\n    items[:] = items[:{}]\n"
    )
    files = {"tests/conftest.py": conftest, "tests/test_pp.py": test}
    before = _Tree({**files, "tests/plugmod.py": plugin.format(1, 5)})
    for label, new_plugin in (
        ("autouse fixture", plugin.format(2, 5)),
        ("hook", plugin.format(1, 6)),
    ):
        after = _Tree({**files, "tests/plugmod.py": new_plugin})
        got = _changed(test, test, "tests/test_pp.py", before, after)
        assert got == ["test_pp"], f"a changed {label} of a pytest_plugins module listed {got}"
    same = _changed(test, test, "tests/test_pp.py", before, before)
    assert same == [], f"an unchanged pytest_plugins module listed {same}"
    other = _Tree({"tests/test_pp.py": test, "tests/plugmod.py": plugin.format(1, 5)})
    moved = _Tree({"tests/test_pp.py": test, "tests/plugmod.py": plugin.format(2, 5)})
    assert _changed(test, test, "tests/test_pp.py", other, moved) == [], (
        "a module that no conftest and no setting names listed a test"
    )
    toml = '[tool.pytest.ini_options]\naddopts = "-q -p tests.plugmod -p no:cacheprovider"\n'
    settings = {"pyproject.toml": toml, "tests/test_pp.py": test}
    got = _changed(
        test,
        test,
        "tests/test_pp.py",
        _Tree({**settings, "tests/plugmod.py": plugin.format(1, 5)}),
        _Tree({**settings, "tests/plugmod.py": plugin.format(2, 5)}),
    )
    assert got == ["test_pp"], f"a plugin named by -p in addopts listed {got}, expected test_pp"


def test_a_module_imported_by_a_name_built_at_run_time_lists_every_test_that_could_reach_it():
    test = (
        "import importlib\n{}\n\ndef test_dyn(n=1):\n"
        "    assert importlib.import_module({}).run()\n\n\ndef test_other():\n    assert 1\n"
    )
    mod = "def run():\n    return {}\n"
    # the name starts with a text (`tests.zz.dyn_`): it reaches the files whose dotted name starts with that text and
    # no other (the import of a package of tests, as here, gives no further reach and takes none away)
    pkg = {"tests/yy/__init__.py": ""}
    for name in ('f"tests.zz.dyn_{n}"', '"tests.zz.dyn_" + str(n)'):
        src = test.format("from tests import yy", name)
        files = {**pkg, "tests/zz/dyn_c.py": mod.format(1), "tests/test_d.py": src}
        files2 = {**pkg, "tests/zz/dyn_c.py": mod.format(2), "tests/test_d.py": src}
        got = _changed(src, src, "tests/test_d.py", _Tree(files), _Tree(files2))
        assert got == ["test_dyn", "test_other"], f"{name}: a changed module listed {got}"
        far = {**pkg, "tests/zz/other_c.py": mod.format(1), "tests/test_d.py": src}
        far2 = {**pkg, "tests/zz/other_c.py": mod.format(2), "tests/test_d.py": src}
        got = _changed(src, src, "tests/test_d.py", _Tree(far), _Tree(far2))
        assert got == [], f"a module outside the text the name starts with listed {got}"
    # a name that starts with a value, in a file that imports no package of tests: every Python file under tests
    src = test.format("", "name_from_somewhere")
    files = {"tests/zz/dyn_c.py": mod.format(1), "tests/test_d.py": src}
    files2 = {"tests/zz/dyn_c.py": mod.format(2), "tests/test_d.py": src}
    got = _changed(src, src, "tests/test_d.py", _Tree(files), _Tree(files2))
    assert got == ["test_dyn", "test_other"], f"an unreadable name: a changed module listed {got}"


def test_an_unreadable_run_time_import_name_is_a_reason_and_is_never_stored_as_an_empty_text():
    """Batch 18 (D17-1): `_dynamic_files` reaches nothing for an empty text, because an unreadable name is one reason
    (`unresolved_edge`) and one reason lists every test. Nothing else enforced that pairing, so this test does: for
    every way to write a name the check cannot read, the module holds a reason and no empty text; for a name that
    starts with a readable text the module holds that text and no reason."""
    unreadable = (
        "",  # no name at all
        "**kw",  # no name that can be read
        "name",  # a value
        'f"{a}.b"',  # starts with a value
        'f".{x}"',  # a relative name built from parts
        '".a" + x',
        'name + "x"',
    )
    for expr in unreadable:
        src = f"import importlib\nimportlib.import_module({expr})\n"
        m = nlc._Module("tests/test_a.py", src)
        assert m.unresolved, f"an unreadable name {expr!r} listed no reason: {m.unresolved}"
        assert "" not in m.dynamic_prefixes, (
            f"an unreadable name {expr!r} stored an empty text: {m.dynamic_prefixes}"
        )
    handed = nlc._Module("tests/test_a.py", "import importlib\nmap(importlib.import_module, n)\n")
    assert handed.unresolved and "" not in handed.dynamic_prefixes, (
        f"a loader handed on as a value stored an empty text: {handed.dynamic_prefixes}"
    )
    for expr, text in (('f"tests.{x}"', "tests."), ('"t" + x', "t")):
        m = nlc._Module("tests/test_a.py", f"import importlib\nimportlib.import_module({expr})\n")
        assert m.dynamic_prefixes == [text] and not m.unresolved, (
            f"a readable start {expr!r} gave {m.dynamic_prefixes} and {m.unresolved}"
        )


def test_a_run_time_import_in_a_python_file_outside_tests_that_a_prefix_reaches_is_a_reason():
    """Batch 18 (C17-1): the text `"t"` reaches `tools/helper.py` (`tools.helper` starts with `t`). The reasons of the tree
    are collected over every file a file of `tests` can reach at run time, not only over `tests/`: a run-time import
    inside `tools/helper.py` is a reason, and its text (a comment too) is part of the digest that changes every unit."""
    test = (
        "import importlib\n\n\ndef test_one(n=1):\n"
        '    assert importlib.import_module("t" + str(n))\n\n\ndef test_two():\n    assert 1\n'
    )
    helper = "import importlib\n# note {}\nLIMIT = 1\n\n\ndef load(name):\n    return importlib.import_module(name)\n"
    before = _Tree({"tests/test_a.py": test, "tools/helper.py": helper.format(1)})
    after = _Tree({"tests/test_a.py": test, "tools/helper.py": helper.format(2)})
    got = _changed(test, test, "tests/test_a.py", before, after)
    assert got == ["test_one", "test_two"], (
        f"a changed file with a reason, reached by a prefix, listed {got}"
    )
    # (the reasons are read after a file was parsed, as `check` does)
    reasons = nlc._tree_reasons(before)
    assert any("tools/helper.py" in r for r in reasons), (
        f"a run-time import in a file outside tests listed no reason: {reasons}"
    )
    # two steps: `te` reaches `terraform/gen.py`, whose own `"t" + n` reaches `tools/helper.py` (the reach is followed again)
    hop_test = test.replace('"t" + str(n)', '"te" + str(n)')
    gen = 'import importlib\n\n\ndef gen(n):\n    return importlib.import_module("t" + n)\n'
    hop = _Tree(
        {"tests/test_a.py": hop_test, "terraform/gen.py": gen, "tools/helper.py": helper.format(1)}
    )
    hop2 = _Tree(
        {"tests/test_a.py": hop_test, "terraform/gen.py": gen, "tools/helper.py": helper.format(2)}
    )
    got = _changed(hop_test, hop_test, "tests/test_a.py", hop, hop2)
    assert got == ["test_one", "test_two"], (
        f"a file reached through a file reached at run time listed {got}"
    )
    # a file the prefix does not reach is no part of the tree state
    far = _Tree({"tests/test_a.py": test, "docs/helper.py": helper.format(1)})
    _changed(test, test, "tests/test_a.py", far, far)
    assert nlc._tree_reasons(far) == [], "a file no prefix reaches gave a reason"


def test_a_star_import_of_a_test_module_makes_every_name_of_it_part_of_the_file():
    test = "from tests.helpers import *\n\n\ndef test_a():\n    assert LIMIT\n"
    helper = "LIMIT = {}\n"
    before = _Tree({"tests/helpers.py": helper.format(1), "tests/test_a.py": test})
    after = _Tree({"tests/helpers.py": helper.format(2), "tests/test_a.py": test})
    got = _changed(test, test, "tests/test_a.py", before, after)
    assert got == ["test_a"], f"a changed helper behind a star import listed {got}, not test_a"
    assert _changed(test, test, "tests/test_a.py", before, before) == [], (
        "an unchanged star import listed a test"
    )


def test_a_row_of_any_notes_file_of_the_change_counts_for_a_unit_and_the_tool_says_so():
    """The limit (round 14, C5): the notes files of the change are read as ONE table, so a row of an older batch's
    notes file serves a unit that a later batch changed again. The tool cannot tell batches apart (the change is
    read against the merge base, not against the last batch), so the limit is stated in its docstring."""
    row_old = "| tests/test_x.py | `test_b` | changed | killing mutant: B1 `old batch` |\n"
    marked = f"{nlc._FOLDER_MARK}handover/evidence/Q/b3\n{row_old}"
    assert nlc.problems(["test_b"], [], marked, "tests/test_x.py") == [], (
        "a row of an older notes file was refused"
    )
    assert "ONE table" in (nlc.__doc__ or ""), "the limit of the one table is not stated"


# ------------------------------------------------------------------------------------------------ batch 16 (round 15)

_DYN_TEST = "import importlib\n{}\n\ndef test_dyn(n=1):\n    assert {}.run()\n\n\ndef test_other():\n    assert 1\n"
_DYN_MOD = "def run():\n    return {}\n"


def _dyn_listed(src: str, changed: str, extra: dict | None = None) -> list[str]:
    """The tests of `tests/test_d.py` (text `src`) that a change of the module file `changed` lists."""
    base = {"tests/test_d.py": src, **(extra or {})}
    before = _Tree({**base, changed: _DYN_MOD.format(1)})
    after = _Tree({**base, changed: _DYN_MOD.format(2)})
    return _changed(src, src, "tests/test_d.py", before, after)


def test_an_unreadable_run_time_import_name_lists_every_test_even_when_the_file_imports_a_package_of_tests():
    # the one rule: a name that cannot be read lists every test of the file, whatever else the file imports
    src = _DYN_TEST.format("from tests.helpers import make", "make(importlib.import_module(name))")
    helpers = {"tests/helpers.py": "def make(m):\n    return m\n"}
    got = _dyn_listed(src, "tests/zz/dyn_c.py", helpers)
    assert got == ["test_dyn", "test_other"], (
        f"a file that imports a package of tests and a run-time name: a changed module listed {got}"
    )
    # the name of an imported package IS readable: it is that package's folder, reached through the import
    pkg = _DYN_TEST.format("from tests import yy", "importlib.import_module(f'{yy.__name__}.{n}')")
    folder = {"tests/yy/__init__.py": ""}
    got = _dyn_listed(pkg, "tests/zz/other_c.py", folder)
    assert got == [], (
        f"a module outside the imported package listed {got} for a package-named import"
    )
    got = _dyn_listed(pkg, "tests/yy/k.py", folder)
    assert got == ["test_dyn", "test_other"], f"a module inside the imported package listed {got}"
    joined = _DYN_TEST.format(
        "from tests import yy", "importlib.import_module(yy.__name__ + '.' + n)"
    )
    assert _dyn_listed(joined, "tests/zz/other_c.py", folder) == [], (
        "a module outside the imported package listed a test for a package name joined with +"
    )


def test_a_run_time_import_name_given_as_the_keyword_name_is_read_like_the_first_argument():
    for call in (
        'importlib.import_module(name=f"tests.zz.dyn_{n}")',
        'importlib.import_module(name="tests.zz.dyn_c")',
    ):
        src = _DYN_TEST.format("", call)
        got = _dyn_listed(src, "tests/zz/dyn_c.py")
        assert got == ["test_dyn", "test_other"], f"{call}: a changed module listed {got}"
        got = _dyn_listed(src, "tests/zz/other_c.py", {"tests/zz/dyn_c.py": _DYN_MOD.format(0)})
        assert got == [], (
            f"{call}: a module outside the text the keyword name starts with listed {got}"
        )
    # a call with no readable name at all (`**kw`, or no argument) reaches every Python file under tests
    for call in ("importlib.import_module(**{'name': n})", "importlib.import_module()"):
        src = _DYN_TEST.format("", call)
        got = _dyn_listed(src, "tests/zz/dyn_c.py")
        assert got == ["test_dyn", "test_other"], (
            f"{call}: a call with no readable name listed {got}"
        )


def test_a_package_is_reached_by_the_text_that_a_run_time_import_name_starts_with():
    # the package `tests.zz` is the file tests/zz/__init__.py: the text `tests.zz.` starts the names of its modules
    # and is the start of the name of the package itself
    src = _DYN_TEST.format("", "importlib.import_module('tests.zz.' + str(n))")
    got = _dyn_listed(src, "tests/zz/__init__.py")
    assert got == ["test_dyn", "test_other"], f"a changed package file listed {got}"
    assert _dyn_listed(src, "tests/yy/__init__.py") == [], (
        "the package file of another package listed a test"
    )


def test_a_call_through_another_name_of_import_module_or_a_function_handed_on_is_the_same_call():
    forms = (
        ("imp = importlib.import_module\n", "imp(f'tests.zz.dyn_{n}')"),
        ("from importlib import import_module as imp\n", "imp(f'tests.zz.dyn_{n}')"),
        ("imp = importlib.import_module\nimp2 = imp\n", "imp2(f'tests.zz.dyn_{n}')"),
    )
    for head, call in forms:
        src = _DYN_TEST.format(head, call)
        got = _dyn_listed(src, "tests/zz/dyn_c.py")
        assert got == ["test_dyn", "test_other"], (
            f"{head.strip()!r}: a call by the alias listed {got}"
        )
        got = _dyn_listed(src, "tests/zz/other_c.py")
        assert got == [], (
            f"{head.strip()!r}: a module outside the text the alias call starts with listed {got}"
        )
    # the function handed on as a value is called somewhere we cannot see, with names we cannot read
    src = _DYN_TEST.format(
        "NAMES = ['tests.zz.dyn_c']", "list(map(importlib.import_module, NAMES))[0]"
    )
    got = _dyn_listed(src, "tests/zz/other_c.py")
    assert got == ["test_dyn", "test_other"], f"a function handed on as a value listed {got}"
    # a function of another name that is no import call is no import call
    src = _DYN_TEST.format("def load(x):\n    return x\n", "load(f'tests.zz.dyn_{n}')")
    assert _dyn_listed(src, "tests/zz/dyn_c.py") == [], (
        "a call of a function that imports nothing listed a test"
    )


def test_a_name_built_at_run_time_with_a_percent_format_or_through_dunder_import_is_read_like_the_others():
    for call in (
        'importlib.import_module("tests.zz.dyn_%s" % n)',
        '__import__(f"tests.zz.dyn_{n}")',
    ):
        src = _DYN_TEST.format("", call)
        got = _dyn_listed(src, "tests/zz/dyn_c.py")
        assert got == ["test_dyn", "test_other"], f"{call}: a changed module listed {got}"
        got = _dyn_listed(src, "tests/zz/other_c.py")
        assert got == [], f"{call}: a module outside the text the name starts with listed {got}"


_FX = (
    "import pytest\n\n\n@pytest.fixture\ndef fx_a():\n    return {}\n\n\n{}\n\n\n"
    "def test_dyn(request):\n    {}\n\n\ndef test_free():\n    assert 1\n"
)


def test_a_fixture_registered_under_an_alias_lists_the_test_that_takes_the_alias():
    own = (
        "import pytest\n\n\n@pytest.fixture(name='alias')\ndef _impl():\n    return {}\n\n\n"
        "def test_use(alias):\n    assert alias\n\n\ndef test_free():\n    assert 1\n"
    )
    got = _changed(own.format(1), own.format(2))
    assert got == ["test_use"], f"a changed fixture with an alias listed {got}, not test_use"
    conf = "import pytest\n\n\n@pytest.fixture(name='alias')\ndef _impl():\n    return {}\n"
    test = "def test_use(alias):\n    assert alias\n\n\ndef test_free():\n    assert 1\n"
    got = _changed(
        test,
        test,
        "tests/test_u.py",
        {"tests/conftest.py": conf.format(1)},
        {"tests/conftest.py": conf.format(2)},
    )
    assert got == ["test_use"], (
        f"a changed conftest fixture with an alias listed {got}, not test_use"
    )


def test_a_fixture_named_by_a_text_that_cannot_be_read_lists_the_test_for_every_fixture_in_reach():
    fx_b = "@pytest.fixture\ndef fx_b():\n    return 5\n"
    for body in (
        "assert request.getfixturevalue(NAME)",
        "assert request.getfixturevalue('fx_%s' % NAME)",
    ):
        src = _FX.format("{}", fx_b, body)
        got = _changed(src.format(1), src.format(2))
        assert got == ["test_dyn"], f"{body}: a changed fixture listed {got}, not test_dyn"
    # a fixture of a conftest above the file is in reach too
    conf = "import pytest\n\n\n@pytest.fixture\ndef fx_c():\n    return {}\n"
    test = "def test_dyn(request):\n    assert request.getfixturevalue(NAME)\n\n\ndef test_free():\n    assert 1\n"
    got = _changed(
        test,
        test,
        "tests/test_u.py",
        {"tests/conftest.py": conf.format(1)},
        {"tests/conftest.py": conf.format(2)},
    )
    assert got == ["test_dyn"], f"a changed conftest fixture listed {got}, not test_dyn"
    # `usefixtures(*names)` cannot be read either
    mark = "@pytest.mark.usefixtures(*NAMES)\ndef test_dyn(request):\n    {}\n"
    src = _FX.format("{}", fx_b, "assert 1").replace(
        "def test_dyn(request):\n    assert 1\n", mark.format("assert 1")
    )
    got = _changed(src.format(1), src.format(2))
    assert got == ["test_dyn"], f"usefixtures(*names) listed {got}, not test_dyn"
    # a fixture that no call reaches does not list a test that reads no fixture by text
    plain = _FX.format("{}", fx_b, "assert 1")
    assert _changed(plain.format(1), plain.format(2)) == [], (
        "a changed fixture nobody names listed a test"
    )


def test_a_fixture_named_by_lazy_fixture_or_by_parametrize_indirect_lists_the_test():
    lazy = (
        "import pytest\nfrom pytest_lazyfixture import lazy_fixture\n\n\n@pytest.fixture\ndef fx_a():\n    return {}\n\n\n"
        "@pytest.mark.parametrize('v', [lazy_fixture('fx_a')])\ndef test_lazy(v):\n    assert v\n\n\n"
        "def test_free():\n    assert 1\n"
    )
    got = _changed(lazy.format(1), lazy.format(2))
    assert got == ["test_lazy"], f"a fixture named by lazy_fixture listed {got}, not test_lazy"
    ind = (
        "import pytest\n\n\n@pytest.fixture\ndef fx_a(request):\n    return {}\n\n\n"
        "pytestmark = pytest.mark.parametrize({}, [1, 2], indirect=True)\n\n\n"
        "def test_ind():\n    assert 1\n\n\ndef test_free():\n    assert 1\n"
    )
    # (the tests below name no fixture themselves: only the text of the mark names it)
    for names in ("'fx_a'", "'fx_a,other'", "['fx_a']", "('fx_a',)"):
        src = ind.replace("{}, [1", names + ", [1").replace("return {}", "return {n}")
        got = _changed(src.format(n=1), src.format(n=2))
        assert sorted(got) == ["test_free", "test_ind"], (
            f"parametrize({names}, indirect=True) listed {got}"
        )
    unreadable = ind.replace("{}, [1", "NAMES, [1").replace("return {}", "return {n}")
    got = _changed(unreadable.format(n=1), unreadable.format(n=2))
    assert sorted(got) == ["test_free", "test_ind"], (
        f"parametrize(NAMES, indirect=True) listed {got}"
    )
    plain = unreadable.replace(", indirect=True", "")
    assert _changed(plain.format(n=1), plain.format(n=2)) == [], (
        "a parametrize with names that cannot be read and no indirect listed a fixture nobody takes"
    )


def test_a_name_bound_by_a_walrus_in_a_definition_header_or_behind_an_assignment_is_followed():
    src = (
        "def deco(fn):\n    return fn{d}\n\n\ndef helper():\n    return {h}\n\n\nW = (X := helper())\n\n\n"
        "def f(a=(LIMIT := {l})):\n    return a\n\n\n@(D := deco)\ndef g():\n    return 1\n\n\n"
        "def test_x():\n    assert X\n\n\ndef test_limit():\n    assert LIMIT\n\n\n"
        "def test_d():\n    assert D\n\n\ndef test_free():\n    assert 1\n"
    )
    base = {"d": "", "h": "1", "l": "5"}
    got = _changed(src.format(**base), src.format(**{**base, "h": "2"}))
    assert got == ["test_x"], (
        f"a walrus behind an assignment: a change of helper listed {got}, not test_x"
    )
    got = _changed(src.format(**base), src.format(**{**base, "l": "6"}))
    assert got == ["test_limit"], (
        f"a walrus in a default argument: a change listed {got}, not test_limit"
    )
    got = _changed(src.format(**base), src.format(**{**base, "d": " + 1"}))
    assert got == ["test_d"], f"a walrus in a decorator: a change of deco listed {got}, not test_d"
    aug = "X = 1\nX += (Y := helper())\n\n\ndef helper():\n    return {}\n\n\ndef test_y():\n    assert Y\n\n\ndef test_free():\n    assert 1\n"
    got = _changed(aug.format(1), aug.format(2))
    assert got == ["test_y"], f"a walrus in an augmented assignment listed {got}, not test_y"
    ann = "X: int = 1\nZ: int = (V := helper())\n\n\ndef helper():\n    return {}\n\n\ndef test_v():\n    assert V\n\n\ndef test_free():\n    assert 1\n"
    got = _changed(ann.format(1), ann.format(2))
    assert got == ["test_v"], f"a walrus behind an annotated assignment listed {got}, not test_v"


def test_the_name_of_a_fixture_that_the_call_getfuncargvalue_names_lists_the_test():
    src = _FX.format("{}", "", "assert request.getfuncargvalue('fx_a')")
    got = _changed(src.format(1), src.format(2))
    assert got == ["test_dyn"], f"getfuncargvalue listed {got}, not test_dyn"


_PLUG = "import pytest\n\n\n@pytest.fixture(autouse=True)\ndef pm_fx():\n    yield {}\n"


def test_a_plugin_is_followed_through_the_attached_p_option_and_through_each_settings_file_and_an_annotated_list():
    test = "def test_pp():\n    assert 1\n"
    for name, text in (
        ("pyproject.toml", '[tool.pytest.ini_options]\naddopts = "-q -ptests.plugmod"\n'),
        ("pytest.ini", "[pytest]\naddopts = -q -p tests.plugmod\n"),
        ("tox.ini", "[pytest]\naddopts = -q -p tests.plugmod\n"),
        ("setup.cfg", "[tool:pytest]\naddopts = -q -p tests.plugmod\n"),
    ):
        files = {name: text, "tests/test_pp.py": test}
        got = _changed(
            test,
            test,
            "tests/test_pp.py",
            _Tree({**files, "tests/plugmod.py": _PLUG.format(1)}),
            _Tree({**files, "tests/plugmod.py": _PLUG.format(2)}),
        )
        assert got == ["test_pp"], (
            f"{name}: a plugin named by -p in addopts listed {got}, not test_pp"
        )
    conf = "pytest_plugins: list[str] = ['tests.plugmod']\n"
    files = {"tests/conftest.py": conf, "tests/test_pp.py": test}
    got = _changed(
        test,
        test,
        "tests/test_pp.py",
        _Tree({**files, "tests/plugmod.py": _PLUG.format(1)}),
        _Tree({**files, "tests/plugmod.py": _PLUG.format(2)}),
    )
    assert got == ["test_pp"], (
        f"a plugin named by an annotated pytest_plugins listed {got}, not test_pp"
    )


def test_a_star_import_is_followed_in_its_relative_form_and_through_a_module_that_only_re_exports():
    test = "from .helpers import *\n\n\ndef test_a():\n    assert LIMIT\n"
    helper = "LIMIT = {}\n"
    got = _changed(
        test,
        test,
        "tests/test_a.py",
        _Tree({"tests/helpers.py": helper.format(1), "tests/test_a.py": test}),
        _Tree({"tests/helpers.py": helper.format(2), "tests/test_a.py": test}),
    )
    assert got == ["test_a"], (
        f"a changed helper behind a relative star import listed {got}, not test_a"
    )
    test = "from tests.h1 import *\n\n\ndef test_a():\n    assert LIMIT\n"
    reexport = "from tests.h2 import *\n"
    files = {"tests/h1.py": reexport, "tests/test_a.py": test}
    got = _changed(
        test,
        test,
        "tests/test_a.py",
        _Tree({**files, "tests/h2.py": helper.format(1)}),
        _Tree({**files, "tests/h2.py": helper.format(2)}),
    )
    assert got == ["test_a"], (
        f"a helper behind a module that only re-exports listed {got}, not test_a"
    )


def test_the_limits_of_the_notes_check_are_stated_in_its_docstring_and_in_the_changelog():
    from pathlib import Path

    changelog = (Path(__file__).resolve().parents[1] / "CHANGELOG.md").read_text(encoding="utf-8")
    flat = " ".join((nlc.__doc__ or "").split())
    for limit in ("entry point", "PYTEST_ADDOPTS", "spec_from_file_location", "`getattr`"):
        assert limit in flat, f"the limit `{limit}` is not stated in the tool docstring"
        assert limit in changelog, f"the limit `{limit}` is not stated in the changelog"
    doc = " ".join(
        (nlc.__doc__ or "").split()
    )  # the line breaks of the docstring are not part of the wording
    assert "starts with a value" in doc and "every Python file under `tests`" in doc, (
        "the rule for a name that cannot be read is not stated in the tool docstring"
    )
    assert "in a file that imports no package of `tests`" not in (nlc.__doc__ or ""), (
        "the docstring still says that a file that imports a package of tests is exempt"
    )


# ---------------------------------------------------------------- batch 17: the fail-closed default (one rule)

_B17_TESTS = "def test_one():\n    assert 1\n\n\ndef test_two():\n    assert 2\n"
_B17_BOTH = ["test_one", "test_two"]
_B17_BASE = {
    "tests/__init__.py": "",
    "tests/helpers.py": "def make(x):\n    return x\n\n\ndef other():\n    return 1\n",
}
_B17_PLAIN = "def zzz():\n    return {}\n"  # a file nothing in the tests tree reaches: the changed file of the cases


def _b17(source, extra=None, change="tests/unrelated.py", test="tests/test_d.py"):
    """The units of `tests/test_d.py` (text `source`) that a change of `change` lists, in a tree of `_B17_BASE`
    plus the files `extra` (a change of a file nothing reaches lists nothing, unless something in the tree cannot be
    read: then it lists every unit)."""
    files = {**_B17_BASE, test: source, **(extra or {})}
    old = _Tree({**files, change: _B17_PLAIN.format(1)})
    new = _Tree({**files, change: _B17_PLAIN.format(2)})
    return _changed(source, source, test, old, new)


# tag -> (the text of tests/test_d.py or of the extra file, the extra files): each one holds something the resolver
# cannot read, so a change of an unrelated file under tests/ must list every test
_B17_UNREADABLE = {
    "relative": ("from .. import helpers\n" + _B17_TESTS, {}),
    "bare-ambiguous": ("import helpers2\n" + _B17_TESTS, {"tests/a/helpers2.py": "X = 1\n"}),
    "plugins-expression": (_B17_TESTS, {"tests/conftest.py": "pytest_plugins = make_names()\n"}),
    "plugins-augmented": (
        _B17_TESTS,
        {"tests/conftest.py": "pytest_plugins = []\npytest_plugins += OTHER\n"},
    ),
    "plugins-append": (
        _B17_TESTS,
        {"tests/conftest.py": "pytest_plugins = []\npytest_plugins.append(name)\n"},
    ),
    "addopts": ('import os\nos.environ["PYTEST_ADDOPTS"] = "-p x"\n' + _B17_TESTS, {}),
    "fixture-by-value": (
        "def test_one(request):\n    request.getfixturevalue(name)\n\n\ndef test_two():\n    assert 2\n",
        {},
    ),
    "fixture-keyword-by-value": (
        "def test_one(request):\n    request.getfixturevalue(argname=name)\n\n\ndef test_two():\n    assert 2\n",
        {},
    ),
    "indirect": (
        (
            "import pytest\n\n\n@pytest.mark.parametrize(names, [1], indirect=True)\ndef test_one(x):\n    assert x\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "getattr-module": (
        (
            "from tests import helpers\n\n\ndef test_one():\n    assert getattr(helpers, name)\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "exec-without-spec": (
        "def test_one(spec):\n    spec.loader.exec_module(spec)\n\n\ndef test_two():\n    assert 2\n",
        {},
    ),
    "iter-modules-path": (
        (
            "import pkgutil\n\n\ndef test_one(path):\n    list(pkgutil.iter_modules(path))\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "walk-packages-unnamed": (
        (
            "import pkgutil\n\n\ndef test_one():\n    list(pkgutil.walk_packages())\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "no-name": (
        "import importlib\n\n\ndef test_one():\n    importlib.import_module()\n\n\ndef test_two():\n    assert 2\n",
        {},
    ),
    "value-start": (
        (
            "import importlib\n\n\ndef test_one(name):\n    importlib.import_module(name)\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "dot-text": (
        (
            "import importlib\n\n\ndef test_one():\n    importlib.import_module('.helpers', 'tests')\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "dot-plus": (
        (
            "import importlib\n\n\ndef test_one(n):\n    importlib.import_module('.' + n, 'tests')\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "dot-fstring": (
        (
            "import importlib\n\n\ndef test_one(n):\n    importlib.import_module(f'.{n}', 'tests')\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "handed-on": (
        (
            "import importlib\n\n\ndef test_one(names):\n    list(map(importlib.import_module, names))\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "path-unreadable": (
        (
            "import importlib.util\n\n\ndef test_one(path):\n    spec = importlib.util.spec_from_file_location('m', path)\n"
            "    spec.loader.exec_module(spec)\n\n\ndef test_two():\n    assert 2\n"
        ),
        {},
    ),
    "run-path-unreadable": (
        "import runpy\n\n\ndef test_one(path):\n    runpy.run_path(path)\n\n\ndef test_two():\n    assert 2\n",
        {},
    ),
    "base-expression": (
        "class TestA(make_base()):\n    def test_one(self):\n        assert 1\n\n\ndef test_two():\n    assert 2\n",
        {},
    ),
    "base-not-found": (
        (
            "from tests.basemod import Base\n\n\nclass TestA(Base):\n    def test_one(self):\n        assert 1\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {"tests/basemod.py": "def make():\n    return object\n\n\nBase = make()\n"},
    ),
    "base-expression-elsewhere": (
        _B17_TESTS,
        {
            "tests/other/test_far.py": "class TestF(make_base()):\n    def test_f(self):\n        assert 1\n"
        },
    ),
    "base-not-found-elsewhere": (
        _B17_TESTS,
        {
            "tests/other/test_far.py": "from tests.basemod import Base\n\n\nclass TestF(Base):\n"
            "    def test_f(self):\n        assert 1\n",
            "tests/basemod.py": "def make():\n    return object\n\n\nBase = make()\n",
        },
    ),
    "package-attr-not-name": (
        (
            "import importlib\nfrom tests import kinds\n\n\ndef test_one(n):\n"
            "    importlib.import_module(f'{kinds.other}.{n}')\n\n\ndef test_two():\n    assert 2\n"
        ),
        {"tests/kinds/__init__.py": "", "tests/kinds/k.py": "X = 1\n"},
    ),
    "package-name-longer-chain": (
        (
            "import importlib\nfrom tests import kinds\n\n\ndef test_one(n):\n"
            "    importlib.import_module(f'{kinds.__name__.x}.{n}')\n\n\ndef test_two():\n    assert 2\n"
        ),
        {"tests/kinds/__init__.py": "", "tests/kinds/k.py": "X = 1\n"},
    ),
    "iter-modules-not-path": (
        (
            "import pkgutil\nfrom tests import kinds\n\n\ndef test_one():\n    list(pkgutil.iter_modules(kinds.paths))\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {"tests/kinds/__init__.py": "", "tests/kinds/k.py": "X = 1\n"},
    ),
    "iter-modules-longer-chain": (
        (
            "import pkgutil\nfrom tests import kinds\n\n\ndef test_one():\n    list(pkgutil.iter_modules(kinds.__path__.x))\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {"tests/kinds/__init__.py": "", "tests/kinds/k.py": "X = 1\n"},
    ),
    "iter-modules-local-name": (
        (
            "import pkgutil\n\n\ndef test_one(kinds):\n    list(pkgutil.iter_modules(kinds.__path__))\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "syntax": (_B17_TESTS, {"tests/broken.py": "def (:\n"}),
    "import-missing-module": ("from tests.nowhere import x\n" + _B17_TESTS, {}),
    "import-missing-name": ("from tests.helpers import nothing\n" + _B17_TESTS, {}),
    "plugin-missing": (_B17_TESTS, {"tests/conftest.py": "pytest_plugins = ['tests.nowhere']\n"}),
    "dynamic-name-missing": (
        (
            "import importlib\n\n\ndef test_one():\n    importlib.import_module('tests.nowhere')\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "package-name-of-a-function": (
        (
            "import importlib\nfrom tests.helpers import make\n\n\ndef test_one(n):\n"
            "    importlib.import_module(f'{make.__name__}.{n}')\n\n\ndef test_two():\n    assert 2\n"
        ),
        {},
    ),
    "package-name-without-a-dot": (
        (
            "import importlib\nfrom tests import helpers\n\n\ndef test_one():\n"
            "    importlib.import_module(f'{helpers.__name__}_v2')\n\n\ndef test_two():\n    assert 2\n"
        ),
        {},
    ),
    "package-name-plus-text": (
        (
            "import importlib\nfrom tests.helpers import make\n\n\ndef test_one():\n"
            "    importlib.import_module(make.__name__ + 'x')\n\n\ndef test_two():\n    assert 2\n"
        ),
        {},
    ),
    "relative-import-in-conftest": (
        _B17_TESTS,
        {"tests/conftest.py": "from ... import something\n"},
    ),
}

# a tree the check CAN read: a change of a file nothing reaches lists nothing (the fail-closed default is not a
# blanket: it applies only when something cannot be read)
_B17_READABLE = {
    "outside-name": (
        "import importlib\n\n\ndef test_one():\n    importlib.import_module('json')\n\n\ndef test_two():\n    assert 2\n",
        {},
    ),
    "importorskip-outside": (
        "import pytest\n\n\ndef test_one():\n    pytest.importorskip('psycopg')\n\n\ndef test_two():\n    assert 2\n",
        {},
    ),
    "path-outside": (
        (
            "import importlib.util\nfrom pathlib import Path\n\nDEMO = Path(__file__).resolve().parents[1] / 'demos'\n\n\n"
            "def test_one(n):\n    spec = importlib.util.spec_from_file_location('m', DEMO / f'{n}.py')\n"
            "    spec.loader.exec_module(spec)\n\n\ndef test_two():\n    assert 2\n"
        ),
        {},
    ),
    "getattr-literal": (
        (
            "from tests import helpers\n\n\ndef test_one():\n    assert getattr(helpers, 'other')\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {},
    ),
    "addopts-deselect": (
        'import os\nos.environ["PYTEST_ADDOPTS"] = "--deselect a"\n' + _B17_TESTS,
        {},
    ),
    "package-name-with-a-dot": (
        (
            "import importlib\nfrom tests import kinds\n\n\ndef test_one(n):\n    importlib.import_module(f'{kinds.__name__}.{n}')\n\n\n"
            "def test_two():\n    assert 2\n"
        ),
        {"tests/kinds/__init__.py": "", "tests/kinds/k.py": "X = 1\n"},
    ),
    "bare-sibling": ("import helpers\n" + _B17_TESTS, {}),
}


_B17_CHANGES = (
    "tests/unrelated.py",
    "tests/data/blob.json",
)  # a module of the tree and a file that is no module


def test_a_change_under_tests_lists_every_test_when_the_check_cannot_read_something_and_nothing_otherwise():
    for tag, (source, extra) in _B17_UNREADABLE.items():
        every = _b17_units(source, extra)
        for change in _B17_CHANGES:
            got = _b17(source, extra, change)
            assert got == every and len(every) >= 2, (
                f"{tag}: a change of {change}, which nothing reaches, listed {got}, not every test {every}"
            )
    for tag, (source, extra) in _B17_READABLE.items():
        for change in _B17_CHANGES:
            got = _b17(source, extra, change)
            assert got == [], (
                f"{tag}: a readable tree listed {got} for a change of {change}, which nothing reaches"
            )
    # a note that no code reads changes nothing, whatever the tree holds
    unreadable = _b17(
        _B17_TESTS, {"tests/conftest.py": "pytest_plugins = make_names()\n"}, "tests/NOTE.md"
    )
    assert unreadable == [], f"a .md note listed {unreadable}"
    # the fail-closed default is global: a change of a file under tests lists the tests of EVERY file
    far = _b17(
        _B17_TESTS, {"tests/other/test_far.py": "import importlib\nimportlib.import_module(name)\n"}
    )
    assert far == _B17_BOTH, (
        f"the unreadable file of another folder did not list this file's tests: {far}"
    )


def test_a_tree_with_one_file_that_does_not_parse_has_exactly_that_one_reason():
    files = {"tests/__init__.py": "", "tests/test_d.py": _B17_TESTS, "tests/broken.py": "def (:\n"}
    sigs = nlc._sigs_for(_Tree(files))
    reasons = sigs.tree_state(sigs.module("tests/test_d.py"))[0]
    assert reasons == ["tests/broken.py: the file does not parse"], (
        f"the only unreadable file did not give exactly its own reason: {reasons}"
    )
    # a change of a file that nothing reaches lists every test
    assert _b17(_B17_TESTS, {"tests/broken.py": "def (:\n"}) == _B17_BOTH, "not every test listed"


def test_control_a_tree_that_can_be_read_has_no_reason():
    # control: the same tree without the broken file gives no reason (it kills no mutant by itself)
    files = {"tests/__init__.py": "", "tests/test_d.py": _B17_TESTS}
    sigs = nlc._sigs_for(_Tree(files))
    assert sigs.tree_state(sigs.module("tests/test_d.py"))[0] == [], "a readable tree gave a reason"


def test_a_file_that_does_not_parse_and_is_read_during_the_walk_is_named_when_the_loader_carries_no_paths():
    # a loader with no `.files`: the module is first read inside the walk (by `_cross_checks`), after the walk began
    broken = "tests/broken.py"
    source = "from tests.broken import thing\n" + _B17_TESTS
    files = {"tests/__init__.py": "", "tests/test_x.py": source, broken: "def (:\n"}
    sigs = nlc._sigs_for(lambda rel: files.get(rel, ""))
    reasons = sigs.tree_state(sigs.module("tests/test_x.py"))[0]
    named = f"{broken}: the file does not parse"
    assert reasons.count(named) == 1, (
        f"the file that does not parse was read during the walk but is not named once: {reasons}"
    )
    assert "tests/test_x.py: it imports tests.broken, which is not in the tree" in reasons, reasons


def test_pin_the_first_five_reasons_in_walk_order_then_the_count_of_the_rest():
    # pin: the files that do not parse come after the reasons of the walk, and only five reasons are shown
    files = {"tests/__init__.py": "", "tests/test_d.py": _B17_TESTS}
    files.update({f"tests/a{i}.py": f"from tests.nowhere{i} import x\n" for i in range(1, 5)})
    files.update({"tests/b1.py": "def (:\n", "tests/b2.py": "def (:\n", "tests/b3.py": "def (:\n"})
    load = _Tree(files)
    sigs = nlc._sigs_for(load)
    sigs.module("tests/test_d.py")
    reasons = nlc._tree_reasons(load)
    assert len(reasons) == 7, reasons
    expected = (
        "every test is listed because the check cannot read part of the tests tree: "
        + "; ".join(
            [
                *(
                    f"tests/a{i}.py: it imports tests.nowhere{i}, which is not in the tree"
                    for i in range(1, 5)
                ),
                "tests/b3.py: the file does not parse",  # the files are read last name first
            ]
        )
        + " (and 2 more)"
    )
    assert nlc._listed_because(reasons) == expected, nlc._listed_because(reasons)


def _b17_units(source, extra=None, rel="tests/test_d.py"):
    files = {**_B17_BASE, rel: source, **(extra or {})}
    return sorted(nlc.units_of(rel, source, _Tree(files)))


def test_every_test_is_a_unit_whatever_its_form_or_base_class():
    forms = {
        "inherited": (
            "from tests.mixin import Base\n\n\nclass TestA(Base):\n    pass\n",
            {"tests/mixin.py": "class Base:\n    def test_m(self):\n        assert 1\n"},
            ["TestA::test_m"],
        ),
        "inherited in the same file": (
            "class Base:\n    def test_m(self):\n        assert 1\n\n\nclass TestA(Base):\n    pass\n",
            {},
            ["TestA::test_m"],
        ),
        "async unittest base": (
            "import unittest\n\n\nclass T(unittest.IsolatedAsyncioTestCase):\n    async def test_x(self):\n        assert 1\n",
            {},
            ["T::test_x"],
        ),
        "renamed TestCase": (
            "from unittest import TestCase as TC\n\n\nclass T(TC):\n    def test_x(self):\n        assert 1\n",
            {},
            ["T::test_x"],
        ),
        "project base": (
            "from tests.helpers import make\n\n\nclass FooTests(make):\n    def test_x(self):\n        assert 1\n",
            {},
            ["FooTests::test_x"],
        ),
        "under if": (
            "import sys\nif sys.platform:\n    def test_x():\n        assert 1\n",
            {},
            ["test_x"],
        ),
        "under try": (
            "try:\n    def test_x():\n        assert 1\nexcept ImportError:\n    pass\n",
            {},
            ["test_x"],
        ),
        "under with": (
            "import contextlib\nwith contextlib.suppress(Exception):\n    def test_x():\n        assert 1\n",
            {},
            ["test_x"],
        ),
        "nested class": (
            "class TestA:\n    class TestB:\n        def test_x(self):\n            assert 1\n",
            {},
            ["TestA::TestB::test_x"],
        ),
        "assigned": (
            "def factory():\n    return lambda: 1\n\n\ntest_x = factory()\n",
            {},
            ["test_x"],
        ),
        "class assigned": (
            "class TestA:\n    test_x = staticmethod(lambda: 1)\n",
            {},
            ["TestA::test_x"],
        ),
        "only in else": (
            "import sys\nif sys.platform:\n    pass\nelse:\n    def test_y():\n        assert 1\n",
            {},
            ["test_y"],
        ),
        "only in finally": (
            "try:\n    pass\nfinally:\n    def test_z():\n        assert 1\n",
            {},
            ["test_z"],
        ),
        "only in except": (
            "try:\n    import json\nexcept ImportError:\n    def test_h():\n        assert 1\n",
            {},
            ["test_h"],
        ),
        "only under match": (
            "match 1:\n    case 1:\n        def test_c():\n            assert 1\n",
            {},
            ["test_c"],
        ),
        "nested class of a base": (
            (
                "class Base:\n    class TestInner:\n        def test_i(self):\n            assert 1\n\n\n"
                "class TestA(Base):\n    pass\n"
            ),
            {},
            ["TestA::TestInner::test_i"],
        ),
        "else branch": (
            "import sys\nif sys.platform:\n    def test_x():\n        assert 1\nelse:\n    def test_x():\n        assert 2\n",
            {},
            ["test_x"],
        ),
    }
    for tag, (source, extra, expected) in forms.items():
        got = [u for u in _b17_units(source, extra) if "test" in u]
        assert got == expected, f"{tag}: the units read are {got}, expected {expected}"
    # the same name under two branches of an `if`: a change in either branch changes the one unit
    for tag, branches in (
        (
            "else",
            "import sys\nif sys.platform:\n    def test_x():\n        assert 1\nelse:\n    def test_x():\n        assert {}\n",
        ),
        (
            "if",
            "import sys\nif sys.platform:\n    def test_x():\n        assert {}\nelse:\n    def test_x():\n        assert 1\n",
        ),
    ):
        got = nlc.changed_tests(branches.format(1), branches.format(2))[0]
        assert got == ["test_x"], (
            f"a change in the {tag} branch of a test defined twice listed {got}, not test_x"
        )
    # a test written twice one after the other (the second replaces the first): a change of the first is listed too
    for tag, redefined, name in (
        (
            "module level",
            "def test_x():\n    assert {}\n\n\ndef test_x():\n    assert 1\n",
            "test_x",
        ),
        (
            "in a class",
            "class TestA:\n    def test_x(self):\n        assert {}\n\n    def test_x(self):\n        assert 1\n",
            "TestA::test_x",
        ),
    ):
        got = nlc.changed_tests(redefined.format(1), redefined.format(2))[0]
        assert got == [name], (
            f"a change of the first of a test written twice ({tag}) listed {got}, not {name}"
        )
    # a change of the mixin lists the inherited test, and a change of the same-file base too
    mixin = "class Base:\n    def helper(self):\n        return {}\n\n    def test_m(self):\n        assert self.helper()\n"
    source = "from tests.mixin import Base\n\n\nclass TestA(Base):\n    pass\n"
    files = {**_B17_BASE, "tests/test_d.py": source}
    got = _changed(
        source,
        source,
        "tests/test_d.py",
        _Tree({**files, "tests/mixin.py": mixin.format(1)}),
        _Tree({**files, "tests/mixin.py": mixin.format(2)}),
    )
    assert got == ["TestA::test_m"], f"a change of the mixin of an inherited test listed {got}"


def test_the_init_file_of_a_tests_package_acts_on_every_test_under_its_folder():
    source = _B17_TESTS
    for init in ("tests/__init__.py", "tests/sub/__init__.py"):
        rel = "tests/sub/test_s.py"
        files = {**_B17_BASE, rel: source, "tests/sub/__init__.py": ""}
        old = _Tree({**files, init: "X = 1\n"})
        new = _Tree({**files, init: "X = 2\n"})
        got = _changed(source, source, rel, old, new)
        assert got == _B17_BOTH, (
            f"{init}: a change of the package init listed {got}, not every test under it"
        )
    files = {**_B17_BASE, "tests/sub/test_s.py": source, "tests/other/__init__.py": "X = 1\n"}
    moved = {**files, "tests/other/__init__.py": "X = 2\n"}
    got = _changed(source, source, "tests/sub/test_s.py", _Tree(files), _Tree(moved))
    assert got == [], f"the init of a package that is not on the way to the file listed {got}"


def test_a_fixture_that_overrides_the_fixture_of_its_own_name_follows_the_one_it_overrides():
    test = "def test_one(client):\n    assert client\n\n\ndef test_two():\n    assert 2\n"
    far = "import pytest\n\n\n@pytest.fixture\ndef {0}():\n    return {1}\n"
    near = "import pytest\n\n\n@pytest.fixture\ndef {0}({0}):\n    return {0}\n"
    for tag, name in (("client", "client"), ("db", "db")):
        files = {
            **_B17_BASE,
            "tests/sub/test_s.py": test.replace("client", name),
            "tests/sub/conftest.py": near.format(name),
        }
        old = _Tree({**files, "tests/conftest.py": far.format(name, 1)})
        new = _Tree({**files, "tests/conftest.py": far.format(name, 2)})
        got = _changed(
            files["tests/sub/test_s.py"],
            files["tests/sub/test_s.py"],
            "tests/sub/test_s.py",
            old,
            new,
        )
        assert got == ["test_one"], (
            f"{tag}: the overridden fixture of a farther conftest listed {got}, not test_one"
        )
    # the override in the test file itself, of a conftest fixture
    own = "import pytest\n\n\n@pytest.fixture\ndef client(client):\n    return client\n\n\ndef test_one(client):\n    assert client\n"
    files = {**_B17_BASE, "tests/test_o.py": own}
    got = _changed(
        own,
        own,
        "tests/test_o.py",
        _Tree({**files, "tests/conftest.py": far.format("client", 1)}),
        _Tree({**files, "tests/conftest.py": far.format("client", 2)}),
    )
    assert got == ["test_one"], (
        f"the conftest fixture a test file overrides listed {got}, not test_one"
    )


def test_autouse_is_read_in_every_form_it_is_written():
    forms = {
        "constant name": (
            "AUTO = True\n\n\n@pytest.fixture(autouse=AUTO)\ndef f():\n    return {}\n"
        ),
        "number": "@pytest.fixture(autouse=1)\ndef f():\n    return {}\n",
        "call": "def _impl():\n    return {}\n\n\nf = pytest.fixture(autouse=True)(_impl)\n",
        "under if": "if True:\n    @pytest.fixture(autouse=True)\n    def f():\n        return {}\n",
        "bare fixture name": "from pytest import fixture\n\n\n@fixture(autouse=True)\ndef f():\n    return {}\n",
        "call with no assignment": "def _impl():\n    return {}\n\n\npytest.fixture(autouse=True)(_impl)\n",
        "call on a lambda": "f = pytest.fixture(autouse=True)(lambda: {})\n",
        "annotated call on a lambda": "f: object = pytest.fixture(autouse=True)(lambda: {})\n",
    }
    for tag, body in forms.items():
        source = "import pytest\n\n" + body + "\n\ndef test_one():\n    assert 1\n"
        got = nlc.changed_tests(source.format(1), source.format(2))[0]
        assert got == ["test_one"], f"{tag}: a changed autouse fixture listed {got}, not test_one"
    nested = (
        "import pytest\n\n\nclass TestK:\n    class TestN:\n        @pytest.fixture(autouse=AUTO)\n"
        "        def f(self):\n            return {}\n\n        def test_m(self):\n            assert 1\n"
    )
    got = nlc.changed_tests(nested.format(1), nested.format(2))[0]
    assert got == ["TestK::TestN::test_m"], f"an autouse fixture of a nested class listed {got}"
    for value in ("False", "None", "0"):
        off = f"import pytest\n\n\n@pytest.fixture(autouse={value})\ndef f():\n    return {{}}\n\n\ndef test_one():\n    assert 1\n"
        assert nlc.changed_tests(off.format(1), off.format(2))[0] == [], (
            f"a fixture with autouse={value} listed a test"
        )


def test_plugins_named_in_every_form_and_the_hidden_pytest_settings_files_are_read():
    plugin = "def hook():\n    return {}\n"
    test = "def test_one():\n    assert 1\n"
    forms = {
        "plain": "pytest_plugins = ['tests.plug']\n",
        "annotated": "pytest_plugins: list[str] = ['tests.plug']\n",
        "augmented": "pytest_plugins = []\npytest_plugins += ['tests.plug']\n",
        "append": "pytest_plugins = []\npytest_plugins.append('tests.plug')\n",
        "extend": "pytest_plugins = []\npytest_plugins.extend(['tests.plug'])\n",
        "insert": "pytest_plugins = []\npytest_plugins.insert(0, 'tests.plug')\n",
        "under if": "if True:\n    pytest_plugins = ['tests.plug']\n",
    }
    for tag, conftest in forms.items():
        files = {**_B17_BASE, "tests/test_p.py": test, "tests/conftest.py": conftest}
        got = _changed(
            test,
            test,
            "tests/test_p.py",
            _Tree({**files, "tests/plug.py": plugin.format(1)}),
            _Tree({**files, "tests/plug.py": plugin.format(2)}),
        )
        assert got == ["test_one"], f"{tag}: a plugin named in this form listed {got}, not test_one"
    for name, text in (
        (".pytest.ini", "[pytest]\naddopts = -p tests.plug\n"),
        ("pytest.toml", '[pytest]\naddopts = "-p tests.plug"\n'),
    ):
        files = {**_B17_BASE, "tests/test_p.py": test, name: text}
        got = _changed(
            test,
            test,
            "tests/test_p.py",
            _Tree({**files, "tests/plug.py": plugin.format(1)}),
            _Tree({**files, "tests/plug.py": plugin.format(2)}),
        )
        assert got == ["test_one"], (
            f"{name}: a plugin of this settings file listed {got}, not test_one"
        )
        assert nlc.kind_of(name) == "config", f"{name} is not read as a pytest settings file"
    # `-p no:name` switches a plugin off: it names no module, so it is no unresolved edge and lists nothing
    files = {
        **_B17_BASE,
        "tests/test_p.py": test,
        "pytest.ini": "[pytest]\naddopts = -p no:cacheprovider\n",
    }
    got = _changed(
        test,
        test,
        "tests/test_p.py",
        _Tree({**files, "tests/unrelated.py": "X = 1\n"}),
        _Tree({**files, "tests/unrelated.py": "X = 2\n"}),
    )
    assert got == [], f"a -p no: option listed {got}"


def test_every_hook_of_a_conftest_acts_on_every_test_below_it():
    test = "def test_one():\n    assert 1\n\n\ndef test_two():\n    assert 2\n"
    for hook in (
        "pytest_sessionstart",
        "pytest_runtest_call",
        "pytest_fixture_setup",
        "pytest_unconfigure",
    ):
        conftest = f"def {hook}(*args):\n    return {{}}\n"
        files = {**_B17_BASE, "tests/sub/test_h.py": test}
        got = _changed(
            test,
            test,
            "tests/sub/test_h.py",
            _Tree({**files, "tests/sub/conftest.py": conftest.format(1)}),
            _Tree({**files, "tests/sub/conftest.py": conftest.format(2)}),
        )
        assert got == _B17_BOTH, (
            f"{hook}: a change of this hook of a conftest listed {got}, not every test below it"
        )
        far = _changed(
            test,
            test,
            "tests/sub/test_h.py",
            _Tree({**files, "tests/other/conftest.py": conftest.format(1)}),
            _Tree({**files, "tests/other/conftest.py": conftest.format(2)}),
        )
        assert far == [], f"{hook}: a hook of a conftest in another folder listed {far}"
    helper = "def helper():\n    return {}\n"
    files = {**_B17_BASE, "tests/sub/test_h.py": test}
    got = _changed(
        test,
        test,
        "tests/sub/test_h.py",
        _Tree({**files, "tests/sub/conftest.py": helper.format(1)}),
        _Tree({**files, "tests/sub/conftest.py": helper.format(2)}),
    )
    assert got == [], f"a helper of a conftest that no test and no hook uses listed {got}"


def test_a_module_loaded_by_name_or_by_path_is_reached_in_every_loader_form():
    mod = "def run():\n    return {}\n"
    forms = {
        "importorskip": "import pytest\n\n\ndef test_one():\n    pytest.importorskip('tests.zz.m')\n",
        "find_spec": "import importlib.util\n\n\ndef test_one():\n    spec = importlib.util.find_spec('tests.zz.m')\n    spec.loader.exec_module(spec)\n",
        "import_module keyword": "import importlib\n\n\ndef test_one():\n    importlib.import_module(name='tests.zz.m')\n",
        "run_module": "import runpy\n\n\ndef test_one():\n    runpy.run_module('tests.zz.m')\n",
        "run_path": "import runpy\n\n\ndef test_one():\n    runpy.run_path('tests/zz/m.py')\n",
        "spec_from_file_location": (
            "import importlib.util\n\n\ndef test_one():\n    spec = importlib.util.spec_from_file_location('m', 'tests/zz/m.py')\n"
            "    spec.loader.exec_module(spec)\n"
        ),
        "path folder": (
            "import importlib.util\nfrom pathlib import Path\n\nHERE = Path(__file__).resolve().parent\n\n\ndef test_one(n):\n"
            "    spec = importlib.util.spec_from_file_location('m', HERE / 'zz' / f'{n}.py')\n    spec.loader.exec_module(spec)\n"
        ),
    }
    for tag, source in forms.items():
        files = {**_B17_BASE, "tests/test_l.py": source}
        got = _changed(
            source,
            source,
            "tests/test_l.py",
            _Tree({**files, "tests/zz/m.py": mod.format(1)}),
            _Tree({**files, "tests/zz/m.py": mod.format(2)}),
        )
        assert got == ["test_one"], (
            f"{tag}: the module this loader reads listed {got}, not test_one"
        )
        far = _changed(
            source,
            source,
            "tests/test_l.py",
            _Tree({**files, "tests/zz/m.py": mod.format(1), "tests/yy/n.py": mod.format(1)}),
            _Tree({**files, "tests/zz/m.py": mod.format(1), "tests/yy/n.py": mod.format(2)}),
        )
        assert far == [], f"{tag}: a module this loader does not read listed {far}"
    # a path of the import table: `from tests.dirs import DEMO` is followed to its value
    helper = "from pathlib import Path\n\nDEMO = Path(__file__).resolve().parent / 'zz'\n"
    source = (
        "import importlib.util\nfrom tests.dirs import DEMO\n\n\ndef test_one(n):\n"
        "    spec = importlib.util.spec_from_file_location('m', DEMO / f'{n}.py')\n    spec.loader.exec_module(spec)\n"
    )
    files = {**_B17_BASE, "tests/test_l.py": source, "tests/dirs.py": helper}
    got = _changed(
        source,
        source,
        "tests/test_l.py",
        _Tree({**files, "tests/zz/m.py": mod.format(1)}),
        _Tree({**files, "tests/zz/m.py": mod.format(2)}),
    )
    assert got == ["test_one"], f"a path built from an imported constant listed {got}, not test_one"


def test_a_bare_import_of_a_module_next_to_the_file_is_followed():
    source = "from helpers import value\n\n\ndef test_one():\n    assert value()\n\n\ndef test_two():\n    assert 2\n"
    helper = "def value():\n    return {}\n"
    files = {**_B17_BASE, "tests/sub/test_b.py": source}
    got = _changed(
        source,
        source,
        "tests/sub/test_b.py",
        _Tree({**files, "tests/sub/helpers.py": helper.format(1)}),
        _Tree({**files, "tests/sub/helpers.py": helper.format(2)}),
    )
    assert got == ["test_one"], f"a bare import of a sibling module listed {got}, not test_one"
    stdlib = "import json\n\n\ndef test_one():\n    assert json\n"
    assert _b17(stdlib) == [], "an import of the standard library was read as an unresolved edge"


def test_a_walrus_in_every_part_of_a_definition_header_binds_a_module_name():
    forms = {
        "class base": "class C((W := {})):\n    pass\n",
        "class keyword": "class C(metaclass=(W := {})):\n    pass\n",
        "keyword-only default": "def f(*, a=(W := {})):\n    return a\n",
        "positional default": "def f(a=(W := {})):\n    return a\n",
        "annotation": "def f(a: (W := {})):\n    return a\n",
        "keyword-only annotation": "def f(*, a: (W := {})):\n    return a\n",
        "positional-only annotation": "def f(a: (W := {}), /):\n    return a\n",
        "positional-only default": "def f(a=(W := {}), /):\n    return a\n",
        "return annotation": "def f() -> (W := {}):\n    return 1\n",
        "decorator": "@(W := {})\ndef f():\n    return 1\n",
    }
    for tag, header in forms.items():
        source = header + "\n\ndef test_one():\n    assert W\n\n\ndef test_two():\n    assert 2\n"
        got = nlc.changed_tests(source.format("int"), source.format("str"))[0]
        assert got == ["test_one"], (
            f"{tag}: the name a walrus binds there listed {got}, not test_one"
        )


def test_a_fixture_named_in_the_short_forms_the_keyword_forms_and_by_alias_is_followed():
    fixture = "import pytest\n\n\n@pytest.fixture\ndef fx():\n    return {}\n"
    cases = {
        "lf short form": (
            "from pytest_lazyfixture import lazy_fixture as lf\n\n\n@pytest.mark.parametrize('a', [lf('fx')])\n"
            "def test_one(a):\n    assert a\n"
        ),
        "getfixturevalue keyword": "def test_one(request):\n    assert request.getfixturevalue(argname='fx')\n",
        "usefixtures keyword": "@pytest.mark.usefixtures(names='fx')\ndef test_one():\n    assert 1\n",
        "getfixturevalue text": "def test_one(request):\n    assert request.getfixturevalue('fx')\n",
    }
    for tag, test in cases.items():
        source = fixture + "\n" + test + "\n\ndef test_two():\n    assert 2\n"
        got = nlc.changed_tests(source.format(1), source.format(2))[0]
        assert got == ["test_one"], f"{tag}: the fixture named there listed {got}, not test_one"
    bare = (
        "from pytest import fixture\n\n\n@fixture(name='alias')\ndef impl():\n    return {}\n\n\n"
        "def test_one(alias):\n    assert alias\n\n\ndef test_two():\n    assert 2\n"
    )
    got = nlc.changed_tests(bare.format(1), bare.format(2))[0]
    assert got == ["test_one"], f"a bare @fixture(name=...) alias listed {got}, not test_one"
    keyword = (
        "import importlib\n\n\ndef test_one(n):\n    importlib.__import__(name=f'tests.zz.dyn_{n}')\n\n\n"
        "def test_two():\n    assert 2\n"
    )
    files = {**_B17_BASE, "tests/test_k.py": keyword}
    for changed, expected in (
        ("tests/zz/dyn_c.py", ["test_one", "test_two"]),
        ("tests/zz/other_c.py", []),
    ):
        got = _changed(
            keyword,
            keyword,
            "tests/test_k.py",
            _Tree({**files, changed: "X = 1\n", "tests/zz/dyn_c.py": "X = 0\n"}),
            _Tree(
                {
                    **files,
                    changed: "X = 2\n",
                    "tests/zz/dyn_c.py": "X = 0\n" if changed != "tests/zz/dyn_c.py" else "X = 2\n",
                }
            ),
        )
        assert got == expected, (
            f"__import__(name=...): a change of {changed} listed {got}, not {expected}"
        )
