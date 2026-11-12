"""Meta-tests of the mutant list of the mutation runner: the list names real killers, and every search string is usable.

These tests read ``tests/mutation_runner_mutants.py`` (the mutants) and the files the mutants target. They are NOT in the test
list the mutants run against (a mutant tree holds the runner's own test file, the keyword test file and the conftest the keyword tests use,
but not this file), so they are checked on the real tree only.
Checks: (a) the list is the test placement table and every killer exists, (g) every search string occurs exactly once in the file it
targets; the script that runs the list exits 2 when its filter selects nothing.
"""

import ast
import subprocess
import sys
from pathlib import Path

from tests import mutation_runner_mutants as mm

ROOT = Path(__file__).resolve().parents[1]
RUNNER_TESTS = ROOT / "tests" / "test_mutation_runner.py"
KEYWORD_TESTS = ROOT / "tests" / "test_mutation_runner_keywords.py"

# every test of the runner file (the first 21 came from an earlier version, with the refuses-paths test split one per guard; later fixes added
# the rest); the manifest test is the last function of the file and has no mutant
MOVED = (
    "test_mutation_judge_verdicts",
    "test_the_runner_kills_a_mutant_of_a_tiny_package",
    "test_a_mutant_path_that_is_absolute_or_names_a_drive_is_refused",
    "test_a_mutant_path_with_a_dotdot_part_is_refused",
    "test_a_mutant_path_with_a_stream_name_is_refused",
    "test_a_mutant_with_a_short_expect_is_refused",
    "test_inside_refuses_a_path_through_a_link_out_of_the_tree",
    "test_inside_refuses_the_tree_itself",
    "test_locate_does_not_list_a_file_link_out_of_the_tree",
    "test_locate_does_not_list_a_file_through_a_folder_link_out_of_the_tree",
    "test_the_runner_checks_a_forged_mutant_path_again",
    "test_run_mutants_refuses_test_and_fixture_paths_that_leave_the_tree",
    "test_the_runner_children_see_an_allowlisted_environment_only",
    "test_an_edit_of_the_tree_during_the_run_does_not_leak_into_a_later_mutant",
    "test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run",
    "test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option",
    "test_a_path_that_starts_with_a_dash_is_refused_in_both_grammars_and_dot_slash_is_the_way_out",
    "test_a_path_that_starts_with_an_at_sign_is_refused_because_pytest_reads_it_as_an_argument_file",
    "test_a_failing_tree_kill_still_kills_the_child",
    "test_the_baseline_run_gets_its_own_timeout",
    "test_a_baseline_timeout_of_zero_is_not_unset",
    "test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout",
    "test_a_timeout_kills_the_whole_process_tree_not_only_pytest",
    "test_an_interrupt_while_waiting_kills_the_run_and_is_not_swallowed",
    "test_a_background_process_left_by_a_finished_run_is_killed_too",
    "test_a_pytest_ini_planted_in_a_parent_folder_is_not_picked_up",
    "test_a_setup_failure_for_one_mutant_is_a_result_row_and_a_blip_is_retried",
    "test_the_runner_keeps_a_symlink_a_link",
    "test_a_test_file_that_is_not_among_the_copied_tests_fails_before_any_mutant_runs",
    "test_junit_with_a_doctype_or_entity_is_refused_not_parsed",
    "test_the_runner_wires_pinned_so_another_failing_test_is_other_test",
    "test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on",
    "test_a_junit_text_over_the_ceiling_is_refused",
    "test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one",
    "test_the_leading_class_of_an_error_line_is_parsed_not_searched",
    "test_allow_crash_without_a_crash_type_is_refused",
    "test_a_truncated_junit_marks_the_mutant_error_and_the_run_goes_on",
    "test_taskkill_is_resolved_under_system_root",
    "test_a_termination_signal_cleans_up_the_run",
    "test_the_signal_handlers_are_restored_and_an_ignored_sighup_stays_ignored",
    "test_a_refused_run_leaves_no_temp_folder",
    "test_the_first_lines_of_an_earlier_run_do_not_leak_into_the_next",
    "test_a_finished_run_does_not_kill_the_tree_on_windows",
    "test_a_signal_during_the_cleanup_does_not_cut_the_cleanup_short",
    "test_a_second_signal_cannot_cut_short_the_cleanup_of_the_first",
    "test_a_signal_while_the_child_is_being_started_still_kills_the_child",
    "test_a_signal_while_the_temp_folders_are_removed_leaves_none",
    "test_the_process_group_is_killed_while_its_leader_is_not_yet_reaped",
    "test_the_pytest_run_writes_no_file_into_its_working_folder_and_leaves_no_temp_folder",
    "test_a_leader_reaped_by_someone_else_is_known_as_ended_so_its_group_is_not_signalled",
    "test_run_mutants_is_not_re_entrant_and_a_nested_call_leaves_the_outer_one_alone",
    "test_a_relative_link_that_points_out_of_the_tree_is_refused_at_snapshot_time",
    "test_a_junction_under_src_or_a_fixture_folder_is_refused_before_the_copy",
    "test_the_colon_refusal_says_a_path_may_not_contain_a_colon_and_the_docstring_states_it",
    "test_a_child_reaped_by_someone_else_is_an_error_result_not_exit_code_zero",
    "test_a_reaped_child_is_an_error_row_for_a_mutant",
    "test_a_reaped_baseline_is_refused_as_reaped_not_as_a_failing_baseline",
    "test_a_junction_as_the_folder_itself_or_a_part_of_its_path_is_refused",
)
EXPECTED_MUTANTS = 329
MANIFEST_TEST = "test_the_manifest_pins_the_files_a_demo_copies"


def _functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def _string_constants(path: Path, name: str) -> list[str]:
    """Every string constant in the function ``name`` of ``path`` (the parts of an f-string included)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    (fn,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    return [
        n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]


def test_a_the_test_file_holds_the_moved_tests_and_the_manifest_test_once_each():
    names = _functions(RUNNER_TESTS)
    tests = [n for n in names if n.startswith("test_")]
    assert len(tests) == len(set(tests)), (
        "a test name is defined twice: the first would be shadowed"
    )
    assert sorted(tests) == sorted((*MOVED, MANIFEST_TEST))
    assert tests[-1] == MANIFEST_TEST, "the manifest test stays last on purpose"


def test_a_no_test_name_is_defined_twice_in_the_keyword_test_file():
    """A second ``def`` of the same name replaces the first, so the first test (and the mutants that name it as their killer) would never run."""
    names = [n for n in _functions(KEYWORD_TESTS) if n.startswith("test_")]
    assert len(names) > 100, "the keyword test file was not read"
    twice = sorted({n for n in names if names.count(n) > 1})
    assert not twice, f"defined twice in the keyword test file: {twice}"


def test_a_there_are_the_listed_number_of_mutants_with_unique_names():
    names = [m.name for m in mm.M]
    assert len(names) == EXPECTED_MUTANTS and len(set(names)) == EXPECTED_MUTANTS, names
    assert {m.file for m in mm.M} == {
        mm.MU,
        mm.MR,
        "tests/conftest.py",
    }  # the guard fixture of the database address is mutated too
    assert sum(m.file == mm.MU for m in mm.M) == 13
    assert sum(m.file == "tests/conftest.py" for m in mm.M) == 4
    assert (
        sum(m.file == mm.MR for m in mm.M) == EXPECTED_MUTANTS - 13 - 4
    )  # not the judge, not the conftest


def test_a_every_mutant_names_its_test_file_and_its_killer_and_the_killer_exists():
    defined = {}
    for m in mm.M:
        assert m.test_file and m.only_test, f"{m.name}: test_file and only_test are both required"
        path = ROOT / m.test_file
        assert path.is_file(), (m.name, m.test_file)
        defined.setdefault(m.test_file, _functions(path))
        assert m.only_test in defined[m.test_file], (m.name, m.only_test, "is not in", m.test_file)
        if m.test_file == mm.TEST:
            assert m.only_test in MOVED, (
                m.name,
                m.only_test,
                "is not one of the runner file's tests",
            )
        else:  # the only other killer file: the keyword tests
            assert m.test_file == mm.KW, (m.name, m.test_file)
        # the judge looks for ``expect`` in the first E line only (not in the test id). A fragment of the killer's own name is
        # still forbidden, so a mutant that breaks another guard of the same test is never counted: ``expect`` must come from the
        # assertion message of the guard
        assert m.expect != m.only_test, (m.name, "expect is the killer's name")
        assert m.expect not in m.only_test, (m.name, "expect is a part of the killer's name")
        assert m.only_test not in m.expect, (m.name, "expect holds the killer's name")
        assert m.expect not in m.pinned, (m.name, "expect is a part of the pinned test id")
        # an ``expect`` that appears nowhere in the killer can never be matched by an assertion message: the mutant would not be
        # killed for the reason it names. The three crash mutants are the exception: their ``expect`` is the text of the exception
        # that the mutant raises (the reason is the class, which ``crash_type`` pins), not a message written in the test
        if not m.allow_crash:
            texts = _string_constants(path, m.only_test)
            assert any(m.expect in t for t in texts), (
                m.name,
                "expect is in no string of the killer",
            )
        # and every mutant pins its own killer, so another failing test is OTHER_TEST and not a kill
        pin = mm.PIN if m.test_file == mm.TEST else mm.KWPIN
        assert m.pinned == pin + m.only_test, (m.name, m.pinned)


def test_a_the_four_crash_mutants_declare_their_exception_class_and_the_others_do_not():
    crash = {m.name: m.crash_type for m in mm.M if m.allow_crash}
    assert crash == {
        "runner: a failing tree kill is not caught": "PermissionError",
        "b2: a refused junit stops the run": "ValueError",
        "runner: a truncated junit stops the run": "ParseError",
        "runner: a JUnit file that cannot be read stops the run": "PermissionError",
    }
    assert sum(not m.allow_crash and not m.crash_type for m in mm.M) == EXPECTED_MUTANTS - 4


def _dotted(node: ast.expr) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


# the functions of ``os`` that Windows does not have: ``hasattr(os, name)`` is false there
WINDOWS_LACKS = frozenset({"waitid"})


def _true_on_windows(node: ast.expr) -> bool:
    """Whether the condition ``node`` of a ``skipif`` is true when ``sys.platform`` is ``"win32"`` and ``os.name`` is ``"nt"``. Only these are
    read: a comparison of ``sys.platform`` or ``os.name`` with a text, ``hasattr(os, "<name>")`` for a name of ``WINDOWS_LACKS``, ``or``, ``and`` and
    ``not``. Any other condition is a ``ValueError`` (it is NOT read as "no skip": a condition this reader cannot evaluate would otherwise hide a
    killer that Windows skips)."""
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.comparators[0], ast.Constant)
    ):
        known = {"sys.platform": "win32", "os.name": "nt"}.get(_dotted(node.left))
        if known is not None and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            return (known == node.comparators[0].value) == isinstance(node.ops[0], ast.Eq)
    elif isinstance(node, ast.BoolOp):
        values = [_true_on_windows(v) for v in node.values]
        return any(values) if isinstance(node.op, ast.Or) else all(values)
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _true_on_windows(node.operand)
    elif (
        isinstance(node, ast.Call)
        and _dotted(node.func) == "hasattr"
        and len(node.args) == 2
        and _dotted(node.args[0]) == "os"
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value in WINDOWS_LACKS
    ):
        return False
    raise ValueError(
        f"a skipif condition that cannot be evaluated for Windows: {ast.unparse(node)}"
    )


def _mark_true_on_windows(node: ast.expr, marks: dict[str, bool]) -> bool:
    """Whether the mark expression ``node`` (a decorator or a part of ``pytestmark``) makes pytest skip on Windows. A name of ``marks`` is a
    module-level ``NAME = pytest.mark.skipif(...)``; ``pytest.mark.skip`` skips everywhere; the other pytest marks (``parametrize``, ``usefixtures``)
    skip nothing; ``pytest.mark.skipif`` is read by ``_true_on_windows``; any other expression is a ``ValueError``."""
    if isinstance(node, ast.Name) and node.id in marks:
        return marks[node.id]
    target = node.func if isinstance(node, ast.Call) else node
    name = _dotted(target)
    if name == "pytest.mark.skip":
        return True
    if name == "pytest.mark.skipif" and isinstance(node, ast.Call):
        condition = (
            node.args[0]
            if node.args
            else next(k.value for k in node.keywords if k.arg == "condition")
        )
        return _true_on_windows(condition)
    if name in ("pytest.mark.parametrize", "pytest.mark.usefixtures"):
        return False
    raise ValueError(f"a decorator or mark that cannot be read for Windows: {ast.unparse(node)}")


def _module_marks(tree: ast.Module) -> tuple[dict[str, bool], bool]:
    """``(marks, whole)``: ``marks`` maps the name of each module-level ``NAME = pytest.mark.skipif(...)`` (like ``posix_only``) to whether it skips
    on Windows; ``whole`` is true when the module-level ``pytestmark`` skips every test of the file on Windows."""
    marks: dict[str, bool] = {}
    whole = False
    for node in tree.body:
        if not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            continue
        name = node.targets[0].id
        value = node.value
        if name == "pytestmark":
            parts = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
            read = [
                _mark_true_on_windows(part, marks) for part in parts
            ]  # EVERY part is read: an unreadable one raises
            whole = any(read)
        elif isinstance(value, ast.Call) and _dotted(value.func).startswith("pytest.mark."):
            marks[name] = _mark_true_on_windows(value, marks)
    return marks, whole


def _windows_skip_mark(function: ast.FunctionDef, marks: dict[str, bool], whole: bool) -> bool:
    """True when the module's ``pytestmark`` (``whole``) or a decorator of ``function`` makes pytest skip it on Windows. EVERY decorator is read, also
    after one that is already true (``posix_only``), so an unreadable decorator anywhere in the list raises ``ValueError``."""
    read = [_mark_true_on_windows(d, marks) for d in function.decorator_list]
    return whole or any(read)


def _functions_of(path: Path) -> tuple[dict[str, ast.FunctionDef], dict[str, bool], bool]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    marks, whole = _module_marks(tree)
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}, marks, whole


def _windows_skip_killers() -> list[str]:
    """The names of the mutants whose killer is skipped on Windows by a mark (read from the decorators and the module-level ``pytestmark``, not typed)."""
    found: dict[str, tuple[dict[str, ast.FunctionDef], dict[str, bool], bool]] = {
        file: _functions_of(path)
        for file, path in ((mm.TEST, RUNNER_TESTS), (mm.KW, KEYWORD_TESTS))
    }
    return [
        m.name
        for m in mm.M
        if _windows_skip_mark(found[m.test_file][0][m.only_test], *found[m.test_file][1:])
    ]


def _calls_skip(
    name: str, functions: dict[str, ast.FunctionDef], seen: frozenset[str] = frozenset()
) -> bool:
    """Whether the function ``name`` calls ``pytest.skip``, directly or through a function of the same file that it calls."""
    for node in ast.walk(functions[name]):
        if isinstance(node, ast.Call):
            called = _dotted(node.func)
            if called == "pytest.skip":
                return True
            if (
                called in functions
                and called != name
                and called not in seen
                and _calls_skip(called, functions, seen | {name})
            ):
                return True
    return False


def _body_skip_killers() -> list[str]:
    """The names of the mutants whose killer calls ``pytest.skip`` in its body (or in a helper of its file): no mark shows it."""
    found = {
        file: _functions_of(path)[0]
        for file, path in ((mm.TEST, RUNNER_TESTS), (mm.KW, KEYWORD_TESTS))
    }
    return [m.name for m in mm.M if _calls_skip(m.only_test, found[m.test_file])]


def _named_between(begin: str, end: str) -> list[str]:
    lines = (mm.__doc__ or "").splitlines()
    return [line.strip() for line in lines[lines.index(begin) + 1 : lines.index(end)]]


def test_a_skipif_condition_the_reader_cannot_evaluate_is_an_error_not_no_skip():
    def parse(text):
        return ast.parse(text, mode="eval").body

    assert _true_on_windows(parse('sys.platform == "win32"')) is True
    assert _true_on_windows(parse('os.name == "nt"')) is True
    assert _true_on_windows(parse('sys.platform != "win32"')) is False
    assert _true_on_windows(parse('sys.platform == "win32" or not hasattr(os, "waitid")')) is True
    assert _true_on_windows(parse('hasattr(os, "waitid")')) is False
    for text in (
        'sys.platform.startswith("win")',
        "not _CI_FILE.is_file()",
        'platform.system() == "Windows"',
        'sys.platform == "win32" or something_else',
        'hasattr(os, "fork")',
        "True",
        'sys.platform in ("win32", "cygwin")',
    ):
        try:
            got = _true_on_windows(parse(text))
        except ValueError as exc:
            assert "cannot be evaluated for Windows" in str(exc)
        else:
            raise AssertionError(f"the condition {text!r} was read without an error: {got}")


def test_a_module_level_pytestmark_and_a_named_mark_are_read_and_an_unknown_decorator_is_an_error():
    tree = ast.parse(
        "import pytest\nposix_only = pytest.mark.skipif(sys.platform == 'win32', reason='x')\n"
        "pytestmark = [pytest.mark.parametrize('a', [1]), posix_only]\n"
        "@some.decorator\ndef test_a(): pass\n@posix_only\ndef test_b(): pass\n"
    )
    marks, whole = _module_marks(tree)
    assert marks == {"posix_only": True} and whole is True, (marks, whole)
    plain = ast.parse("pytestmark = pytest.mark.skipif(sys.platform == 'linux', reason='x')\n")
    assert _module_marks(plain) == ({}, False)
    function = ast.parse("@some.decorator\ndef test_a(): pass\n").body[0]
    try:
        _windows_skip_mark(function, {}, False)
    except ValueError as exc:
        assert "cannot be read for Windows" in str(exc)
    else:
        raise AssertionError("a decorator that cannot be read was taken as no skip")
    plain_function = ast.parse("def test_a(): pass\n").body[0]
    assert _windows_skip_mark(plain_function, {}, True) is True, (
        "the module-level pytestmark was not applied to a test"
    )
    try:
        _windows_skip_mark(
            function, {}, True
        )  # the whole-file mark does not excuse an unreadable decorator
    except ValueError as exc:
        assert "cannot be read for Windows" in str(exc)
    else:
        raise AssertionError(
            "an unreadable decorator was not read because the whole file is marked"
        )


def test_the_header_names_every_mutant_whose_killer_skips_inside_its_body_and_each_skip_is_there():
    """A killer that calls ``pytest.skip`` in its body (or in a helper of its file) has no mark. The header names those mutants between its second pair of
    marker lines, and this test compares that list with the killers it reads, in both directions: a named killer with no ``pytest.skip`` call, or a
    killer with one that the header does not name, fails."""
    named = _named_between("BODY-SKIP-MUTANTS-BEGIN", "BODY-SKIP-MUTANTS-END")
    derived = _body_skip_killers()
    assert len(derived) >= 10, f"the body skips of the killers were not read: {len(derived)} found"
    assert sorted(named) == sorted(derived), (
        f"header only: {sorted(set(named) - set(derived))}; calls pytest.skip only: {sorted(set(derived) - set(named))}"
    )
    assert len(set(named)) == len(named), (
        "a mutant is named twice in the body-skip list of the header"
    )


# killers that read ``os.name`` in their body and are in no derived list, but still kill their mutant on Windows (another case of the same test does)
STILL_KILLED_ON_WINDOWS = (
    "runner: the descriptor leaks when no file object is made",
    "runner: a JUnit path that is no regular file is read",
)


def _system_name_killers() -> list[str]:
    """The names of the mutants whose killer reads ``os.name`` or ``sys.platform`` in its own body (not in a helper) and that no mark and no ``pytest.skip`` call names."""
    found = {
        file: _functions_of(path)[0]
        for file, path in ((mm.TEST, RUNNER_TESTS), (mm.KW, KEYWORD_TESTS))
    }
    listed = set(_windows_skip_killers()) | set(_body_skip_killers())
    out = []
    for m in mm.M:
        if m.name in listed:
            continue
        if any(
            isinstance(node, ast.Attribute) and ast.unparse(node) in ("os.name", "sys.platform")
            for node in ast.walk(found[m.test_file][m.only_test])
        ):
            out.append(m.name)
    return out


def test_the_header_names_the_killers_that_drop_a_case_by_the_system_name_and_both_lists_are_checked():
    """Two killers drop a case by ``os.name`` and have no mark and no ``pytest.skip``: the header names them between a third pair of marker lines, which is kept by
    hand. This test reads the killers that use ``os.name`` or ``sys.platform`` in their body and compares: every killer found is in the hand list or in
    ``STILL_KILLED_ON_WINDOWS``, and every name in either list is a mutant whose killer is found."""
    named = _named_between("OS-BRANCH-MUTANTS-BEGIN", "OS-BRANCH-MUTANTS-END")
    found = _system_name_killers()
    assert len(found) >= 2, f"the system-name killers were not read: {found}"
    assert sorted(found) == sorted([*named, *STILL_KILLED_ON_WINDOWS]), (
        f"found only: {sorted(set(found) - set(named) - set(STILL_KILLED_ON_WINDOWS))}; "
        f"listed only: {sorted((set(named) | set(STILL_KILLED_ON_WINDOWS)) - set(found))}"
    )
    assert len(set(named)) == len(named) == 2 and not set(named) & set(STILL_KILLED_ON_WINDOWS)


def test_every_decorator_is_read_even_after_a_true_mark_and_an_unreadable_one_raises():
    """The old reader stopped at the first mark that is true (``posix_only``), so an unreadable decorator after it was never read. Same for the parts of a module-level ``pytestmark``."""
    function = ast.parse("@posix_only\n@some.decorator\ndef test_a(): pass\n").body[0]
    try:
        _windows_skip_mark(function, {"posix_only": True}, False)
    except ValueError as exc:
        assert "cannot be read for Windows" in str(exc)
    else:
        raise AssertionError("an unreadable decorator after a true mark was not read")
    both = ast.parse("pytestmark = [pytest.mark.skip, some.thing]\n")
    try:
        _module_marks(both)
    except ValueError as exc:
        assert "cannot be read for Windows" in str(exc)
    else:
        raise AssertionError("an unreadable part of pytestmark after a true one was not read")


def test_the_header_names_every_mutant_whose_killer_is_skipped_on_windows_derived_from_the_skip_marks():
    """The header of the mutant list says which mutants survive on Windows. The list between its two marker lines is compared with the one read
    from the decorators of the killers, so a killer that gets (or loses) a Windows skip mark makes this test fail until the header agrees.
    A killer that skips INSIDE its body (``pytest.skip(...)``) has no mark: those are in the second list of the header (compared by the test below)."""
    named = _named_between("POSIX-ONLY-MUTANTS-BEGIN", "POSIX-ONLY-MUTANTS-END")
    derived = _windows_skip_killers()
    assert len(derived) > 40, f"the skip marks of the killers were not read: {len(derived)} found"
    assert sorted(named) == sorted(derived), (
        f"header only: {sorted(set(named) - set(derived))}; marks only: {sorted(set(derived) - set(named))}"
    )
    assert len(set(named)) == len(named), "a mutant is named twice in the header"
    all_names = {m.name for m in mm.M}
    assert set(named) <= all_names, "the header names a mutant that does not exist"
    assert "Every other killer is written to run on both systems" not in (mm.__doc__ or ""), (
        "the header says every other killer runs on both systems: a skip inside a killer's body is not read from a mark"
    )


def test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets():
    lines = []
    for m in mm.M:
        text = (ROOT / m.file).read_text(encoding="utf-8")
        count = text.count(m.old)
        assert count == 1, f"{m.name}: the search string occurs {count} times in {m.file}"
        assert m.new != m.old, m.name
        lines.append(f"{m.name}: occurs once in {m.file}")
    assert len(lines) == EXPECTED_MUTANTS
    print("\n".join(lines))  # shown by ``pytest -rP``


def test_the_mutants_script_exits_2_when_the_filter_selects_no_mutant():
    script = ROOT / "tests" / "mutation_runner_mutants.py"
    done = subprocess.run(  # noqa: S603  # our own interpreter and a file of this repository, no shell
        [sys.executable, str(script), "no mutant has a name like this zzz"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert done.returncode == 2, (done.returncode, done.stdout[-200:], done.stderr[-200:])
    assert "nothing was run" in done.stderr
