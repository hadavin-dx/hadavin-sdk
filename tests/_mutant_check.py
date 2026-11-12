"""The cheap check of a mutant list (Q8a-1 batch 18, Issue 4): a mutant whose text is no longer in its file cannot apply, so
it proves nothing, and the slow run (`python tests/stage_mutants.py`) would only say so after an hour. This reads the list and the
files and names every mutant that cannot apply. Used by `tests/test_q8a1_b18_fixes.py` for each list of mutants."""

from __future__ import annotations

import ast
from pathlib import Path


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
    return problems
