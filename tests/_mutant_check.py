"""The cheap check of a mutant list (Q8a-1 batch 18, Issue 4): a mutant whose text is no longer in its file cannot apply, so
it proves nothing, and the slow run (`python tests/stage_mutants.py`) would only say so after an hour. This reads the list and the
files and names every mutant that cannot apply (the mutant lists themselves are not searched for an `expect`). Used by `tests/test_q8a1_b18_fixes.py` for each list of mutants."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from tests._dynamic_expects_baseline import DYNAMIC_EXPECTS


def _functions(path: Path) -> set[str]:
    return {
        n.name
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def mutant_problems(root: Path, mutants) -> list[str]:
    """One line per mutant that cannot apply: its file is missing, its `old` text is not in the file (the runner reports that as
    SNIPPET NOT FOUND), its `old` text equals its `new` text (a mutant that changes nothing), or its killer test function does not
    exist in its test file."""
    problems: list[str] = []
    seen: set[str] = set()
    for m in mutants:
        if m.name in seen:
            problems.append(f"{m.name}: the name is used twice")
        seen.add(m.name)
        path = root / m.file
        if not path.is_file():
            problems.append(f"{m.name}: the file {m.file} does not exist")
            continue
        text = path.read_text(encoding="utf-8")
        if m.old not in text:
            problems.append(f"{m.name}: the text to replace is not in {m.file}")
        if m.old == m.new:
            problems.append(f"{m.name}: the new text equals the old text")
        if m.test_file and m.only_test:
            test_path = root / m.test_file
            if not test_path.is_file() or m.only_test not in _functions(test_path):
                problems.append(f"{m.name}: the killer {m.only_test} is not in {m.test_file}")
        # `pinned` is the test id that must be the one failing: it names the killer, and the file of the killer (batch 19, 9g)
        if m.pinned and m.only_test:
            want_file = (m.test_file or "").removesuffix(".py")
            if not m.pinned.startswith(want_file + "::" + m.only_test):
                problems.append(f"{m.name}: pinned {m.pinned!r} is not the killer {m.only_test}")
            elif m.pinned.count("[") and m.pinned not in _collected_ids(root, m.test_file or ""):
                # batch 20 (B2): the id must be one the test file really has (collected, parametrized ids included), or the
                # slow run would call the right failure the wrong test (OTHER_TEST)
                problems.append(f"{m.name}: pinned {m.pinned!r} is not a test id of {m.test_file}")
        # `expect` is a fragment of the intended failing message: it must exist in the tests or the source, or no failure can
        # ever hold it (the runner would report WRONG_REASON after the slow run); a crash names an exception class instead
        if (
            not m.allow_crash
            and not _in_tree(root, m.expect)
            and (m.name, m.expect) not in DYNAMIC_EXPECTS
        ):
            problems.append(
                f"{m.name}: the expected text {m.expect!r} is in no file of tests or src"
            )
    return problems


def _is_mutant_list(p: Path) -> bool:
    """A file that holds mutant lists or the frozen list of expected texts built at run time: each `expect` is a literal there,
    so a search that includes it can never fail (batch 20, B2)."""
    return p.name.endswith("mutants.py") or p.name == "_dynamic_expects_baseline.py"


_IDS: dict[Path, frozenset[str]] = {}


def _collected_ids(root: Path, test_file: str) -> frozenset[str]:
    """The test ids pytest collects from one file, written as the runner writes them (`tests/test_x::test_y[param]`)."""
    path = root / test_file
    if path not in _IDS:
        out = subprocess.run(  # noqa: S603 - our own interpreter and a repo file
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                "-p",
                "no:cacheprovider",
                str(path),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        ).stdout
        _IDS[path] = frozenset(
            line.replace(".py::", "::", 1) for line in out.splitlines() if ".py::" in line
        )
    return _IDS[path]


def _in_tree(root: Path, fragment: str) -> bool:
    """The fragment is in a file of `tests` or `src` that is not a mutant list."""
    for sub in ("tests", "src"):
        for p in (root / sub).rglob("*.py"):
            if not _is_mutant_list(p) and fragment in _read(p):
                return True
    return False


_CACHE: dict[Path, str] = {}


def _read(p: Path) -> str:
    if p not in _CACHE:
        _CACHE[p] = p.read_text(encoding="utf-8")
    return _CACHE[p]
