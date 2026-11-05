"""tests/held_modules.py stays a pair of literal tuples with ONE entry per line (one-line-deletion merges)."""

import ast
from pathlib import Path

HELD = Path(__file__).resolve().parent / "held_modules.py"


def format_problems(text: str) -> list[str]:
    problems = []
    seen = set()
    for node in ast.parse(text).body:
        if not (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)):
            continue
        name = node.targets[0].id
        if not isinstance(node.value, ast.Tuple):
            problems.append(f"{name}: not a literal tuple")
            continue
        seen.add(name)
        lines = [e.lineno for e in node.value.elts]
        if len(set(lines)) != len(lines):
            problems.append(f"{name}: more than one entry on a line")
        if any(isinstance(e, ast.Tuple) and e.lineno != e.end_lineno for e in node.value.elts):
            problems.append(f"{name}: an entry spans several lines")
        if node.value.elts and node.value.lineno == lines[0]:
            problems.append(f"{name}: first entry shares the opening line")
    if seen != {"HELD_MODULES", "PENDING"}:
        problems.append(f"expected exactly HELD_MODULES and PENDING, got {sorted(seen)}")
    return problems


def test_held_modules_one_entry_per_line():
    assert format_problems(HELD.read_text(encoding="utf-8")) == []


def test_parser_rejects_bad_layouts():
    assert format_problems('HELD_MODULES = ("a", "b")\nPENDING = ()\n')
    assert format_problems('HELD_MODULES = {"a"}\nPENDING = ()\n')
    assert format_problems('HELD_MODULES = (\n    "a", "b",\n)\nPENDING = ()\n')
    assert format_problems('HELD_MODULES = ("a",\n    "b",\n)\nPENDING = ()\n')
    assert format_problems('HELD_MODULES = (\n    "a",\n    "b",\n)\n')
    assert format_problems('HELD_MODULES = (\n    "a",\n)\nPENDING = (\n    ("x",\n     "y"),\n)\n')
    assert not format_problems('HELD_MODULES = (\n    "a",\n)\nPENDING = ()\n')
