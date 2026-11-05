"""Import closure (design 6.1): no module under src/jagrat reaches a dropped dependency or the reference package.

Two passes, both also run against throw-away trees in the tests below so a broken module is proven to fail:
  1. static (AST): every import statement, lazy ones inside functions included, is checked against the forbidden
     list, and every in-package `from .x import name` is resolved to a real module and a real top-level name;
  2. runtime: every module is imported in a fresh interpreter with a meta-path finder that refuses a forbidden
     top-level package when the importing module is `jagrat` or `jagrat.*` (core's own lazy imports are not flagged).
The reference package name is built from parts and is never written as a literal.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

from held_modules import HELD_MODULES, PENDING

SRC = Path(__file__).resolve().parent.parent / "src"
REF_NAME = "war" + "den"
FORBIDDEN = {
    "temporalio",
    "boto3",
    "botocore",
    "kubernetes",
    "psycopg",
    "torch",
    "transformers",
    "slack_sdk",
    "webauthn",
    "opentelemetry",
    "cryptography",
    REF_NAME,
}


def modules(root: Path) -> list[tuple[str, Path]]:
    out = []
    for p in sorted((root / "jagrat").rglob("*.py")):
        rel = p.relative_to(root).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__main__":
            continue  # running it starts the CLI; its imports are still read by the static pass
        if parts[-1] == "__init__":
            parts = parts[:-1]
        out.append((".".join(parts), p))
    return out


def all_files(root: Path) -> list[Path]:
    return sorted((root / "jagrat").rglob("*.py"))


def top_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()

    def visit(body: list[ast.stmt]) -> None:
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(n.name)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    names.update(x.id for x in ast.walk(t) if isinstance(x, ast.Name))
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                names.add(n.target.id)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                names.update((a.asname or a.name).split(".")[0] for a in n.names)
            elif isinstance(n, (ast.If, ast.Try)):
                visit(n.body)
                visit(getattr(n, "orelse", []))
                for h in getattr(n, "handlers", []):
                    visit(h.body)
                visit(getattr(n, "finalbody", []))

    visit(tree.body)
    return names


def resolve(root: Path, dotted: str) -> Path | None:
    base = root.joinpath(*dotted.split("."))
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def static_problems(root: Path) -> list[str]:
    problems: list[str] = []
    for path in all_files(root):
        rel = path.relative_to(root).with_suffix("")
        parts = list(rel.parts)
        pkg = parts[:-1]
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in FORBIDDEN:
                        problems.append(
                            f"{path.name}:{node.lineno}: forbidden import {a.name.split('.')[0]}"
                        )
                    elif (
                        a.name.split(".")[0] == "jagrat"
                        and resolve(root, a.name) is None
                        and (path.name, a.name) not in PENDING
                    ):
                        problems.append(f"{path.name}:{node.lineno}: unresolved module {a.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0:
                    top = (node.module or "").split(".")[0]
                    if top in FORBIDDEN:
                        problems.append(f"{path.name}:{node.lineno}: forbidden import {top}")
                        continue
                    if top != "jagrat":
                        continue
                    target = node.module or ""
                else:
                    anchor = pkg[: len(pkg) - (node.level - 1)] if node.level > 1 else pkg
                    target = ".".join([*anchor, *([node.module] if node.module else [])])
                tfile = resolve(root, target)
                if tfile is None and (path.name, target) in PENDING:
                    continue
                if tfile is None:
                    problems.append(f"{path.name}:{node.lineno}: unresolved module {target}")
                    continue
                known = top_level_names(ast.parse(tfile.read_text(encoding="utf-8")))
                for a in node.names:
                    if a.name == "*" or a.name in known or resolve(root, f"{target}.{a.name}"):
                        continue
                    problems.append(f"{path.name}:{node.lineno}: {target} has no name {a.name}")
    return problems


RUNTIME_SCRIPT = textwrap.dedent(
    """
    import importlib, importlib.abc, sys
    FORBIDDEN = set(sys.argv[2].split(","))
    class Guard(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name.split(".")[0] in FORBIDDEN:
                f = sys._getframe(1)
                while f is not None and f.f_globals.get("__name__", "").startswith(("importlib", "_frozen_importlib")):
                    f = f.f_back
                importer = f.f_globals.get("__name__", "") if f else ""
                if importer == "jagrat" or importer.startswith("jagrat."):
                    raise ImportError("forbidden by the closure test: " + name.split(".")[0])
            return None
    sys.meta_path.insert(0, Guard())
    sys.path.insert(0, sys.argv[1])
    failed = []
    for name in sys.argv[3].split(","):
        try:
            importlib.import_module(name)
        except BaseException as exc:  # noqa: BLE001
            failed.append(name + ": " + type(exc).__name__ + ": " + str(exc)[:160])
    print("\\n".join(failed))
    sys.exit(1 if failed else 0)
    """
)


def runtime_problems(root: Path) -> list[str]:
    names = ",".join(n for n, _ in modules(root))
    proc = subprocess.run(
        [sys.executable, "-I", "-c", RUNTIME_SCRIPT, str(root), ",".join(sorted(FORBIDDEN)), names],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


# ------------------------------------------------------------------------------------------ the real tree
def test_static_closure_of_src():
    assert static_problems(SRC) == []


def test_runtime_closure_of_src():
    assert runtime_problems(SRC) == []


def test_modules_are_found():
    names = {n for n, _ in modules(SRC)}
    assert {
        "jagrat",
        "jagrat.settings",
        "jagrat.facts",
        "jagrat.quarantine",
        "jagrat.gate_text",
    } <= names


# ------------------------------------------------------------------------------------------ the tests fail on bad trees
def make_tree(tmp_path: Path, body: str) -> Path:
    pkg = tmp_path / "jagrat"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "good.py").write_text("VALUE = 1\n")
    (pkg / "m.py").write_text(body)
    return tmp_path


def test_static_flags_top_level_lazy_and_reference_imports(tmp_path):
    body = (
        "import boto3\n"
        "from temporalio import workflow\n"
        f"import {REF_NAME}.x\n"
        "def f():\n"
        "    from cryptography.hazmat import primitives\n"
        "    import psycopg.rows\n"
    )
    probs = static_problems(make_tree(tmp_path, body))
    assert len(probs) == 5 and all("forbidden" in p for p in probs)


def test_static_flags_unresolved_and_missing_names(tmp_path):
    body = "from .good import VALUE, MISSING\nfrom .nowhere import x\nfrom . import good\n"
    probs = static_problems(make_tree(tmp_path, body))
    assert any("has no name MISSING" in p for p in probs)
    assert any("unresolved module jagrat.nowhere" in p for p in probs)
    assert len(probs) == 2


def test_static_accepts_clean_tree(tmp_path):
    assert static_problems(make_tree(tmp_path, "from .good import VALUE\nimport yaml\n")) == []


def test_runtime_flags_import_made_by_jagrat_only(tmp_path):
    bad = make_tree(tmp_path / "a", "import json\nimport boto3\n")
    assert any("forbidden by the closure test" in p for p in runtime_problems(bad))
    ok = make_tree(tmp_path / "b", "import json\nimport yaml\n")
    assert runtime_problems(ok) == []


def test_runtime_flags_reference_package_name(tmp_path):
    bad = make_tree(tmp_path, f"import {REF_NAME}\n")
    assert any("forbidden by the closure test" in p for p in runtime_problems(bad))


def test_pending_entries_are_not_stale():
    for fname, mod in PENDING:
        assert resolve(SRC, mod) is None, f"{mod} exists now: remove ({fname}, {mod}) from PENDING"
        assert (SRC / "jagrat" / fname).is_file()
    for mod in HELD_MODULES:
        assert resolve(SRC, mod) is None, (
            f"{mod} exists now: remove it from HELD_MODULES (its Part has built it)"
        )


def test_no_module_imports_a_held_module():
    """Nothing kept may depend on a held module (it would dangle): the static pass would also report it."""
    for path in all_files(SRC):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                target = "jagrat." + (node.module or "")
                names = {target} | {f"{target}.{a.name}".rstrip(".") for a in node.names}
                assert not names & set(HELD_MODULES), (
                    f"{path.name}:{node.lineno} imports a held module"
                )
