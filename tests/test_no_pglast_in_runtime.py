"""Guard: pglast is GPL-3.0-or-later, so it stays in the `test` dependency group (the CI oracle) and never
reaches shipped code (src/, demos/, tools/) or a runtime dependency (owner decision 2026-11-01)."""

import ast
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREES = ("src", "demos", "tools")


def _norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _is(
    dep,
):  # a PEP 508 string such as " PGLAST_x[a]>=1 ; marker"; a dict (include-group) is not a name
    return (
        isinstance(dep, str)
        and _norm(re.split(r"[ ;\[<>=!~@(]", dep.strip(), maxsplit=1)[0]) == "pglast"
    )


def _flat(groups, name, seen=()):  # entries of a group with include-group resolved
    for d in groups.get(name, []):
        if isinstance(d, dict) and d.get("include-group") not in seen:
            yield from _flat(groups, d["include-group"], (*seen, name))
        else:
            yield d


def _hit(deps):
    return any(_is(d["name"] if isinstance(d, dict) else d) for d in deps)


def _code(root, tree):
    files = [p for p in (root / tree).rglob("*") if p.is_file()] if (root / tree).is_dir() else []
    bad = [f"{tree}: vendored {p.name}" for p in files if p.suffix in (".so", ".pyd")]
    bad += [f"{tree}: vendored dir" for p in (root / tree).rglob("*") if p.is_dir() and _is(p.name)]
    py = [p for p in files if p.suffix in (".py", ".pyi")]
    if not py:
        bad.append(f"{tree}: no python file scanned")
    for p in py:
        for n in ast.walk(ast.parse(p.read_text("utf-8"))):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else []
            mods += [n.module or ""] if isinstance(n, ast.ImportFrom) else []
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                mods += [n.value] if re.fullmatch(r"(?i)pglast(\.\w+)*", n.value) else []
            if any(_norm(m.split(".")[0]) == "pglast" for m in mods):
                bad.append(f"{tree}: {p.relative_to(root / tree).as_posix()} imports pglast")
    return bad


def _lock(root, name):
    lock = (
        tomllib.loads((root / "uv.lock").read_text("utf-8")) if (root / "uv.lock").is_file() else {}
    )
    bad = [] if lock else ["uv.lock missing"]
    for p in lock.get("package", []):
        if _norm(p["name"]) == "pglast":
            continue
        top = _norm(p["name"]) == name
        sections = {"dependencies": p.get("dependencies", [])}
        sections |= {f"extra {k}": v for k, v in p.get("optional-dependencies", {}).items()}
        sections |= {
            f"group {k}": v
            for k, v in p.get("dev-dependencies", {}).items()
            if not top or k != "test"
        }
        meta = p.get("metadata", {})
        sections |= {"requires-dist": meta.get("requires-dist", [])}
        sections |= {
            f"requires-dev {k}": v for k, v in meta.get("requires-dev", {}).items() if k != "test"
        }
        bad += [f"uv.lock {p['name']}: {k}" for k, v in sections.items() if _hit(v)]
    return bad


def violations(root):
    """Where pglast reaches shipped code or a runtime dependency under `root`; empty when clean."""
    meta = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))
    groups, uv = meta.get("dependency-groups", {}), meta.get("tool", {}).get("uv", {})
    bad = [b for t in TREES for b in _code(root, t)]
    bad += _lock(root, _norm(meta["project"]["name"]))
    bad += [f"dependencies: {d}" for d in meta["project"].get("dependencies", []) if _is(d)]
    for k, v in meta["project"].get("optional-dependencies", {}).items():
        bad += [f"extra {k}" for d in v if _is(d)][:1]
    bad += [f"group {g}" for g in groups if g != "test" and _hit(_flat(groups, g))]
    bad += [
        f"tool.uv {k}"
        for k in ("dev-dependencies", "constraint-dependencies", "override-dependencies")
        if _hit(uv.get(k, []))
    ]
    return bad + (
        ["tool.uv sources"] if "pglast" in {_norm(k) for k in uv.get("sources", {})} else []
    )


def test_repository_ships_no_pglast():
    assert violations(ROOT) == []


PYPROJECT = '[project]\nname="x"\ndependencies=[]\n[dependency-groups]\ntest=["pglast==8.7"]\ndev=["pytest"]\n'
LOCK = (
    '[[package]]\nname="x"\n[package.dev-dependencies]\ntest=[{name="pglast"}]\n'
    '[[package]]\nname="pglast"\n[[package]]\nname="other"\ndependencies=[{name="requests"}]\n'
)
MUTANTS = {
    "clean": ({}, []),
    "non-test group": ({"pyproject.toml": PYPROJECT + 'ci=["pglast==8.7"]\n'}, ["group ci"]),
    "uppercase and leading space": (
        {"pyproject.toml": PYPROJECT + "ci=[\" PGLAST ; python_version>'3'\"]\n"},
        ["group ci"],
    ),
    "at-form": ({"pyproject.toml": PYPROJECT + 'ci=["pglast@https://e.x/p.whl"]\n'}, ["group ci"]),
    "include-group": (
        {"pyproject.toml": PYPROJECT + 'ci=[{include-group="test"}]\n'},
        ["group ci"],
    ),
    "runtime dependency": (
        {"pyproject.toml": PYPROJECT.replace("=[]", '=["pglast==8.7"]', 1)},
        ["dependencies: pglast==8.7"],
    ),
    "tool.uv constraint": (
        {"pyproject.toml": PYPROJECT + '[tool.uv]\nconstraint-dependencies=["pglast<9"]\n'},
        ["tool.uv constraint-dependencies"],
    ),
    "lock edge from runtime package": (
        {"uv.lock": LOCK.replace('{name="requests"}', '{name="pglast"}')},
        ["uv.lock other: dependencies"],
    ),
    "lock group other than test": (
        {
            "uv.lock": LOCK.replace(
                "[package.dev-dependencies]\ntest", "[package.dev-dependencies]\nci"
            )
        },
        ["uv.lock x: group ci"],
    ),
    "import in src": ({"src/m.py": "import pglast\n"}, ["src: m.py imports pglast"]),
    "import submodule": ({"src/m.py": "import pglast.x\n"}, ["src: m.py imports pglast"]),
    "from submodule": ({"demos/m.py": "from pglast.x import y\n"}, ["demos: m.py imports pglast"]),
    "import_module string": (
        {"tools/m.py": "import importlib\nimportlib.import_module('pglast.ast')\n"},
        ["tools: m.py imports pglast"],
    ),
    "prose string is fine": ({"src/m.py": "x = 'pglast.x is GPL'\n"}, []),
    "missing src": ({"src/m.py": None}, ["src: no python file scanned"]),
    "vendored dir": ({"src/pglast/__init__.py": ""}, ["src: vendored dir"]),
    "vendored binary": ({"src/_pglast.so": ""}, ["src: vendored _pglast.so"]),
}


@pytest.mark.parametrize("case", MUTANTS)
def test_guard_catches(tmp_path, case):
    files = {"pyproject.toml": PYPROJECT, "uv.lock": LOCK} | {f"{t}/m.py": "x = 1\n" for t in TREES}
    files |= MUTANTS[case][0]
    for rel, text in files.items():
        if text is not None:
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / rel).write_text(text, "utf-8")
    assert violations(tmp_path) == MUTANTS[case][1]
