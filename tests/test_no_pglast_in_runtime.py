"""Guard: pglast is GPL-3.0-or-later, so it stays in the `test` dependency group (the CI oracle) and never
reaches `src/` or a runtime dependency list (licence scan, owner decision 2026-11-01)."""

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _names(tree):
    """Every module name imported, plus every string constant (importlib.import_module("pglast"))."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            yield from (a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            yield n.module or ""
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield n.value


def violations(root):
    """Where pglast reaches the shipped package under `root`; empty when clean."""
    found = [
        p.relative_to(root).as_posix()
        for p in sorted((root / "src").rglob("*.py"))
        if any(m.split(".")[0] == "pglast" for m in _names(ast.parse(p.read_text("utf-8"))))
    ]
    meta = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))
    lists = {"dependencies": meta["project"]["dependencies"]}
    lists |= {f"extra {k}": v for k, v in meta["project"].get("optional-dependencies", {}).items()}
    lists |= {f"group {k}": v for k, v in meta.get("dependency-groups", {}).items() if k != "test"}
    return found + [
        k for k, v in lists.items() if any(str(d).lower().startswith("pglast") for d in v)
    ]


def test_repository_ships_no_pglast():
    assert violations(ROOT) == []


def test_detects_each_way_in(tmp_path):
    def tree(py="x = 1\n", deps="[]"):
        (tmp_path / "src").mkdir(exist_ok=True)
        (tmp_path / "src" / "m.py").write_text(py, "utf-8")
        toml = (
            f'[project]\nname="x"\ndependencies={deps}\n[project.optional-dependencies]\ne={deps}\n'
        )
        (tmp_path / "pyproject.toml").write_text(
            toml + '[dependency-groups]\ntest=["pglast==8.7"]\n'
        )
        return violations(tmp_path)

    assert tree() == []
    for py in (
        "import pglast\n",
        "from pglast import ast\n",
        "import importlib\nimportlib.import_module('pglast')\n",
    ):
        assert tree(py) == ["src/m.py"], py
    assert tree(deps='["pglast==8.7"]') == ["dependencies", "extra e"]
