"""Round 7C, finding C: the clean-tree guard of the test run, and the test of the guard itself.

The r7b guard skipped `.git`, `__pycache__`, `node_modules` and the tool caches as WHOLE folders and could not see an
empty folder, while the notes said it "hides and skips nothing". Now it compares everything except the short list in
tests/tree_guard.py. Each test plants a change in a scratch copy of a small tree and expects the guard to name it."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import conftest
import pytest
import tree_guard

# CONTROL labels (r7e): every test below passes on r7b ONLY when the r7c test-side helper is present
# (tests/tree_guard.py and the conftest hook; without them the file cannot be imported). Mutants of tree_guard.py
# that were really run in r7e (one scratch copy each, raw output out/R7E/raw/mutg-<letter>.log); each test names
# the mutants that make it fail:
#   A files are not recorded            B folders are not recorded         C changes() returns nothing
#   D changes() adds an invented entry  E node_modules is skipped again    F every file in a __pycache__ is skipped
#   G the .git folder entry is dropped  H3 links are followed and not recorded as links
#   I coverage.xml is no longer skipped J the insides of .git are compared
# Not killed (run, survived): H alone and H2 alone (a link to a folder still shows as one entry through the other
# half of the code); no mutant that skips one MORE kind of entry can fail the two "nothing changed" tests.


@pytest.fixture
def root(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    (r / "src").mkdir(parents=True)
    (r / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (r / ".git").mkdir()
    (r / ".git" / "HEAD").write_text("ref\n", encoding="utf-8")
    (r / "src" / "__pycache__").mkdir()
    (r / "src" / "__pycache__" / "a.cpython-312.pyc").write_bytes(b"\0")
    return r


def _changed(root: Path, act: Callable[[], object]) -> list[str]:
    before = tree_guard.snapshot(root)
    act()
    return tree_guard.changes(before, tree_guard.snapshot(root))


# CONTROL (r7e label, with the r7c helper): killed by mutant D (the guard invents a change); a guard that skips an
# entry kind cannot fail it.
def test_an_unchanged_tree_reports_nothing(root: Path) -> None:
    assert _changed(root, lambda: None) == []


# CONTROL (r7e label, with the r7c helper): killed by mutants A, C, D.
def test_a_planted_file_is_named(root: Path) -> None:
    assert _changed(root, lambda: (root / "stray.txt").write_text("x", encoding="utf-8")) == ["stray.txt"]


# CONTROL (r7e label, with the r7c helper): killed by mutants B, C, D.
def test_a_planted_empty_folder_is_named(root: Path) -> None:
    assert _changed(root, lambda: (root / "empty").mkdir()) == ["empty"]


# CONTROL (r7e label, with the r7c helper): killed by mutants A, C, D.
def test_a_file_with_a_line_break_in_its_name_is_named(root: Path) -> None:
    assert _changed(root, lambda: (root / "a\nb").write_text("x", encoding="utf-8")) == ["a\nb"]


# CONTROL (r7e label, with the r7c helper): killed by mutants A, C, D.
def test_a_changed_and_a_deleted_file_are_named(root: Path) -> None:
    def act() -> None:
        (root / "src" / "a.py").write_text("x = 22222\n", encoding="utf-8")

    assert _changed(root, act) == [os.path.join("src", "a.py")]
    assert _changed(root, lambda: (root / "src" / "a.py").unlink()) == [os.path.join("src", "a.py")]


# CONTROL (r7e label, with the r7c helper): killed by mutants B, C, D, E.
def test_a_folder_that_used_to_be_skipped_is_compared_now(root: Path) -> None:
    assert _changed(root, lambda: (root / "node_modules" / "p").mkdir(parents=True)) == [
        "node_modules",
        os.path.join("node_modules", "p"),
    ]


# CONTROL (r7e label, with the r7c helper): killed by mutants C, D, H3.
def test_a_link_is_one_entry_and_is_not_followed(root: Path) -> None:
    def act() -> None:
        (root / "to_src").symlink_to(root / "src")

    assert _changed(root, act) == ["to_src"]


# CONTROL (r7e label, with the r7c helper): killed by mutants D, I, J (it checks that the listed skips stay quiet).
def test_only_the_listed_things_are_skipped(root: Path) -> None:
    def quiet() -> None:
        (root / ".git" / "objects").mkdir()
        (root / ".git" / "index").write_text("i", encoding="utf-8")
        (root / "src" / "__pycache__" / "b.cpython-312.pyc").write_bytes(b"\0")
        (root / "scripts" / "__pycache__").mkdir(parents=True)
        (root / "scripts" / "__pycache__" / "c.cpython-312.pyc").write_bytes(b"\0")
        (root / ".pytest_cache").mkdir()
        (root / ".pytest_cache" / "v").write_text("1", encoding="utf-8")
        (root / ".coverage").write_text("c", encoding="utf-8")
        (root / "coverage.xml").write_text("c", encoding="utf-8")

    (root / "scripts").mkdir()
    assert _changed(root, quiet) == []


# CONTROL (r7e label, with the r7c helper): killed by mutants A, C, D, F.
def test_a_file_that_is_not_a_pyc_inside_a_cache_folder_is_named(root: Path) -> None:
    got = _changed(root, lambda: (root / "src" / "__pycache__" / "note.txt").write_text("x", encoding="utf-8"))
    assert os.path.join("src", "__pycache__", "note.txt") in got


# CONTROL (r7e label, with the r7c helper): killed by mutants B, C, D, G.
def test_the_git_folder_itself_is_still_compared(root: Path) -> None:
    def act() -> None:
        (root / ".git").rename(root / ".git-moved")

    assert ".git" in _changed(root, act)


def _finish(root: Path, monkeypatch: pytest.MonkeyPatch, act: Callable[[], object]) -> Any:
    """Point the real hook of conftest.py at the scratch tree, apply the change, return a fake session."""
    monkeypatch.setattr(conftest, "_REPO_ROOT", root)
    monkeypatch.setattr(conftest, "_TREE_BEFORE", tree_guard.snapshot(root))
    act()
    return SimpleNamespace(config=SimpleNamespace(getoption=lambda *_a: False), exitstatus=0)


# CONTROL (r7e label, with the r7c helper): killed by mutants A, C.
def test_the_session_hook_fails_the_run_and_names_the_planted_file(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    session = _finish(root, monkeypatch, lambda: (root / "stray.txt").write_text("x", encoding="utf-8"))
    conftest.pytest_sessionfinish(session, 0)
    assert session.exitstatus == 1 and "'stray.txt'" in capsys.readouterr().out


# CONTROL (r7e label, with the r7c helper): killed by mutants B, C.
def test_the_session_hook_fails_the_run_for_a_planted_empty_folder(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    session = _finish(root, monkeypatch, lambda: (root / "empty").mkdir())
    conftest.pytest_sessionfinish(session, 0)
    assert session.exitstatus == 1 and "'empty'" in capsys.readouterr().out


# CONTROL (r7e label, with the r7c helper): killed by mutants D.
def test_the_session_hook_stays_quiet_when_nothing_changed(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    session = _finish(root, monkeypatch, lambda: None)
    conftest.pytest_sessionfinish(session, 0)
    assert session.exitstatus == 0 and capsys.readouterr().out == ""
