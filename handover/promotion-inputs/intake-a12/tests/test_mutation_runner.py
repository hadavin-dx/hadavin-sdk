"""The mutation runner's own kill rule: only an assertion-class failure of the named test is a kill (an allowlist)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("mutate_p45", Path(__file__).parent / "mutation_runner" / "mutate_p45.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

NODE = "tests/test_x.py::test_a"


def failed(msg: str, node: str = NODE) -> str:
    return f"FAILED {node} - {msg}\n"


def test_a_plain_assertion_failure_of_the_named_test_is_a_kill():
    assert runner.is_kill(1, failed("assert 1 == 2"), NODE)[0]


def test_a_parameter_id_is_ignored_when_comparing_the_named_test():
    assert runner.is_kill(1, failed("assert 1 == 2", NODE + "[x]"), NODE)[0]


def test_an_import_attribute_or_syntax_error_is_not_a_kill():
    for msg in ("ImportError: cannot import name", "AttributeError: module has no attribute", "SyntaxError: bad", "NameError: x"):
        assert not runner.is_kill(1, failed(msg), NODE)[0], msg


def test_any_other_exception_is_not_a_kill():  # TypeError, KeyError and UnboundLocalError counted as kills under the old denylist
    for msg in ("TypeError: x", "KeyError: 'a'", "UnboundLocalError: y", "RuntimeError: z", "ValueError: v"):
        assert not runner.is_kill(1, failed(msg), NODE)[0], msg


def test_assertion_style_messages_are_kills():
    for msg in (
        "assert 1 == 2",
        "AssertionError: boom",
        "Failed: DID NOT RAISE",
        "[XPASS(strict)] reason",
        "model_support.UnexpectedCall: unexpected call",
    ):
        assert runner.is_kill(1, failed(msg), NODE)[0], msg


def test_a_parameter_id_with_spaces_is_read_whole():
    out = failed("assert 1 == 2", "tests/test_x.py::test_a[Claude Opus 5.5-True]")
    assert runner.first_failed(out) == "tests/test_x.py::test_a[Claude Opus 5.5-True]"
    assert runner.is_kill(1, out, NODE)[0]


def test_a_collection_error_is_not_a_kill():
    assert not runner.is_kill(1, failed("assert 1 == 2") + "ERROR tests/test_y.py - boom\n", NODE)[0]


def test_another_test_failing_first_is_not_a_kill_of_the_named_one():
    assert not runner.is_kill(1, failed("assert 1 == 2", "tests/test_x.py::test_other"), NODE)[0]


def test_rc_other_than_one_is_not_a_kill():
    for rc in (0, 2, 4, 5, -9):
        assert not runner.is_kill(rc, failed("assert 1"), NODE)[0]


def test_the_scratch_copy_holds_tracked_files_only_and_no_symlinks():
    root = runner.ROOT
    work = runner.scratch_copy()
    try:
        assert (work / "src" / "intake" / "extract.py").is_file() and (work / "tests" / "conftest.py").is_file()
        assert not any(p.is_symlink() for p in work.rglob("*"))
        assert not (work / ".venv").exists() and not (work / ".git").exists()
        tracked = {
            p for p in __import__("subprocess").run(["git", "ls-files"], cwd=root, capture_output=True, text=True).stdout.splitlines() if p
        }
        copied = {str(p.relative_to(work)).replace("\\", "/") for p in work.rglob("*") if p.is_file()}
        assert copied <= tracked  # nothing the repository does not track (no .env, no local data)
    finally:
        __import__("shutil").rmtree(work.parent, ignore_errors=True)
