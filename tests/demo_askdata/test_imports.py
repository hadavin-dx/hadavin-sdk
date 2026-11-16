"""Demo-local lock-in guard (the core guard scans src/, not demos/): vendor imports live only in their module,
and the execution path has exactly one place that sends SQL."""

import ast
from pathlib import Path

from tests.demo_askdata.conftest import DEMO

VENDOR_HOME = {"psycopg": "pgsource.py", "sqlglot": "validate.py"}
CALLS_THAT_SEND = {"execute", "executemany", "copy", "stream", "executescript"}


def _imports(tree: ast.AST) -> set[str]:
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def _demo_python_files() -> list[Path]:
    return sorted(p for p in DEMO.rglob("*.py") if "__pycache__" not in p.parts)


def test_vendor_imports_stay_in_their_module():
    seen = {name: set() for name in VENDOR_HOME}
    for path in _demo_python_files():
        mods = _imports(ast.parse(path.read_text(encoding="utf-8")))
        for vendor in VENDOR_HOME:
            if vendor in mods:
                seen[vendor].add(path.name)
    assert seen == {v: {home} for v, home in VENDOR_HOME.items()}, seen


def test_pgsource_has_exactly_one_call_that_sends_sql():
    tree = ast.parse((DEMO / "askdata" / "pgsource.py").read_text(encoding="utf-8"))
    sends = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in CALLS_THAT_SEND
    ]  # fmt: skip
    assert len(sends) == 1, [n.lineno for n in sends]
    send_fn = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_send"
    )
    assert sends[0] in list(ast.walk(send_fn))


def test_the_import_check_itself_catches_a_planted_violation():
    planted = ast.parse("import psycopg\nfrom sqlglot import exp")
    assert _imports(planted) == {"psycopg", "sqlglot"}
