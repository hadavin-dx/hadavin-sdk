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
    assert nlc.changed_tests("a\n", "a\nb\n", rel) == (["policy_sources_2026-11-11.txt"], []), (
        "a changed fixture file was not one unit named by its file name"
    )
    assert nlc.changed_tests("a\n", "a\n", rel) == ([], []), "an unchanged fixture file was listed"
    assert nlc.kind_of("tests/fixtures/other.txt") is None, (
        "a fixture of another family is in scope"
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
