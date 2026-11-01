"""Repository rules: proprietary licence everywhere, and the core never depends on a demo."""

import ast
import subprocess
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LICENCE_TEXT = (
    "Copyright (c) 2026 Hadavin. All rights reserved.\n"
    "\n"
    "This source code is proprietary and confidential. No licence is granted to use, copy,\n"
    "modify, distribute or create derivative works of it, except under a separate written\n"
    "agreement with Hadavin. Viewing this repository on GitHub does not grant any such licence.\n"
)


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"],  # noqa: S607 - git from PATH, fixed argv
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.splitlines()


def licence_problems(root: Path, files: list[str]) -> list[str]:
    """Every tracked LICENSE and pyproject.toml must be proprietary."""
    problems = []
    for name in files:
        path = root / name
        if path.name == "LICENSE" and path.read_text(encoding="utf-8") != LICENCE_TEXT:
            problems.append(f"{name}: not the proprietary licence text")
        if path.name == "pyproject.toml":
            project = tomllib.loads(path.read_text(encoding="utf-8")).get("project", {})
            if project.get("license") != "LicenseRef-Proprietary":
                problems.append(f"{name}: license is not LicenseRef-Proprietary")
            if project.get("authors") != [{"name": "Hadavin"}]:
                problems.append(f"{name}: authors is not Hadavin")
    return problems


def core_imports_demos(core_dir: Path) -> list[str]:
    """Any import of the demos package from inside the core."""
    hits = []
    for path in core_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            hits += [
                f"{path.name}: {n}" for n in names if n.split(".")[0] in {"demos", "demo", "tests"}
            ]
    return hits


def missing_rollback_tests(root: Path, action_dirs: list[Path]) -> list[str]:
    """Every reversible contract must name a rollback_test that exists (file + test function)."""
    problems = []
    for folder in action_dirs:
        for path in sorted(folder.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if data.get("risk_class") != "reversible":
                continue
            node = data.get("rollback_test") or ""
            file, _, func = node.partition("::")
            target = root / file
            if not func or not target.is_file() or f"def {func}(" not in target.read_text("utf-8"):
                problems.append(f"{path.name}: rollback_test {node!r} not found")
    return problems


def missing_undo_tests(root: Path, action_dirs: list[Path]) -> list[str]:
    """Every manual contract must name an undo_test that exists (file + test function): K3."""
    problems = []
    for folder in action_dirs:
        for path in sorted(folder.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if (data.get("executor") or {}).get("kind") != "manual":
                continue
            node = data.get("undo_test") or ""
            file, _, func = node.partition("::")
            target = root / file
            if not func or not target.is_file() or f"def {func}(" not in target.read_text("utf-8"):
                problems.append(f"{path.name}: undo_test {node!r} not found")
    return problems


def action_dirs(root: Path) -> list[Path]:
    return [root / "tests/fixtures/config/actions", *root.glob("demos/*/config/actions")]


def test_every_manual_contract_names_an_existing_undo_test():
    assert missing_undo_tests(ROOT, action_dirs(ROOT)) == []


def test_plant_missing_undo_test_is_caught(tmp_path):
    actions = tmp_path / "actions"
    actions.mkdir()
    (actions / "m.yaml").write_text(
        "executor: {kind: manual}\nundo_test: tests/t.py::test_gone\n", encoding="utf-8"
    )
    (actions / "h.yaml").write_text("executor: {kind: http}\n", encoding="utf-8")
    assert missing_undo_tests(tmp_path, [actions]) == [
        "m.yaml: undo_test 'tests/t.py::test_gone' not found"
    ]


def test_licences_are_proprietary():
    files = tracked_files(ROOT)
    assert {"LICENSE", "pyproject.toml"} <= set(files)
    assert licence_problems(ROOT, files) == []


def test_core_never_imports_demos():
    assert core_imports_demos(ROOT / "src" / "hadavin_sdk") == []


def test_every_reversible_contract_names_an_existing_rollback_test():
    assert missing_rollback_tests(ROOT, action_dirs(ROOT)) == []


SECRET_HOLDERS = {
    "hadavin_sdk.actions.secrets",
    "hadavin_sdk.actions.secrets_env",
    "hadavin_sdk.actions.secrets_aws",
    "hadavin_sdk.actions.secrets_vault",
    "hadavin_sdk.actions.secrets_azure",
    "hadavin_sdk.actions.secrets_gcp",
    "hadavin_sdk.actions.secrets_file",
    "hadavin_sdk.actions.secrets_cache",
    "hadavin_sdk.actions.executor",
    "hadavin_sdk.backends.platform_secrets",  # backends' own secrets (design 4.4)
}


def secret_imports(pkg_dirs: list[Path]) -> list[str]:
    """runtime, approvals and llm must never import the secret provider or the executor."""
    hits = []
    for d in pkg_dirs:
        for path in d.rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
                hits += [f"{path.name}: {n}" for n in names if n in SECRET_HOLDERS]
    return hits


def test_import_boundary_runtime_approvals_llm_never_see_secrets():
    core = ROOT / "src" / "hadavin_sdk"
    assert secret_imports([core / "runtime", core / "approvals", core / "llm"]) == []


def test_plant_runtime_importing_executor_is_caught(tmp_path):
    (tmp_path / "bad.py").write_text("from hadavin_sdk.actions import executor\n", encoding="utf-8")
    assert secret_imports([tmp_path]) == ["bad.py: hadavin_sdk.actions.executor"]


def test_plant_runtime_importing_platform_secrets_is_caught(tmp_path):
    (tmp_path / "bad.py").write_text(
        "from hadavin_sdk.backends.platform_secrets import bound\n", encoding="utf-8"
    )
    assert secret_imports([tmp_path]) == ["bad.py: hadavin_sdk.backends.platform_secrets"]


def test_plant_missing_rollback_test_is_caught(tmp_path):
    actions = tmp_path / "actions"
    actions.mkdir()
    (actions / "a.yaml").write_text(
        "risk_class: reversible\nrollback_test: tests/t.py::test_gone\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
    assert missing_rollback_tests(tmp_path, [actions]) == [
        "a.yaml: rollback_test 'tests/t.py::test_gone' not found"
    ]


# Plant checks: each guard must catch a planted violation.
def test_plant_apache_licence_is_caught(tmp_path):
    (tmp_path / "LICENSE").write_text("Apache License\nVersion 2.0\n", encoding="utf-8")
    assert licence_problems(tmp_path, ["LICENSE"]) == ["LICENSE: not the proprietary licence text"]


def test_plant_open_pyproject_is_caught(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nlicense = "Apache-2.0"\nauthors = [{ name = "Someone" }]\n',
        encoding="utf-8",
    )
    assert len(licence_problems(tmp_path, ["pyproject.toml"])) == 2


def test_plant_core_importing_a_demo_is_caught(tmp_path):
    (tmp_path / "bad.py").write_text("from demos.invoice_po import app\n", encoding="utf-8")
    assert core_imports_demos(tmp_path) == ["bad.py: demos.invoice_po"]


# --- K5 (M21): no secret holder is reachable from runtime, approvals, llm or the tools, even transitively -------
def _module_path(src: Path, module: str) -> Path | None:
    rel = Path(*module.split("."))
    for candidate in (src / rel.with_suffix(".py"), src / rel / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _static_imports(tree: ast.AST) -> list[str]:
    """Every module a file imports, lazy imports inside functions included, `if TYPE_CHECKING:` bodies not."""
    found: list[str] = []

    def walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If) and getattr(child.test, "id", "") == "TYPE_CHECKING":
                continue
            if isinstance(child, ast.Import):
                found.extend(a.name for a in child.names)
            elif isinstance(child, ast.ImportFrom) and child.module:
                found.append(child.module)
                found.extend(f"{child.module}.{a.name}" for a in child.names)
            walk(child)

    walk(tree)
    return found


def transitive_imports(src: Path, starts: list[str], pkg: str = "hadavin_sdk") -> set[str]:
    """The modules of `pkg` reachable from `starts` by imports, each module's parent packages included (importing
    `a.b.c` runs `a/__init__` and `a/b/__init__`)."""
    seen: set[str] = set()
    todo = list(starts)
    while todo:
        module = todo.pop()
        if module in seen:
            continue
        seen.add(module)
        path = _module_path(src, module)
        if path is None:
            continue
        for name in _static_imports(ast.parse(path.read_text(encoding="utf-8"))):
            if name.split(".")[0] != pkg or _module_path(src, name) is None:
                continue
            parts = name.split(".")
            todo.extend(".".join(parts[:i]) for i in range(1, len(parts) + 1))
    return seen


def _modules_in(src: Path, folder: str) -> list[str]:
    root = src / "hadavin_sdk"
    return [
        ".".join(p.relative_to(src).with_suffix("").parts).removesuffix(".__init__")
        for p in sorted((root / folder).rglob("*.py"))
    ]


SECRET_FREE = ["runtime", "approvals", "llm", "sources"]
SECRET_FREE_MODULES = [
    "hadavin_sdk.tools",
    "hadavin_sdk.guard.http",
    "hadavin_sdk.guard.runmap",
    "hadavin_sdk.guard.egress",
]


def test_k5_no_secret_holder_is_reachable_from_runtime_approvals_llm_or_tools():
    src = ROOT / "src"
    starts = SECRET_FREE_MODULES + [m for f in SECRET_FREE for m in _modules_in(src, f)]
    reached = transitive_imports(src, starts)
    assert sorted(reached & SECRET_HOLDERS) == []


def test_k5_no_transitive_import_of_actions_from_tools():
    reached = transitive_imports(ROOT / "src", ["hadavin_sdk.tools"])
    assert sorted(m for m in reached if m.startswith("hadavin_sdk.actions")) == []


NL = chr(10)


def _plant_pkg(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = tmp_path / "hadavin_sdk" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_plant_transitive_secret_import_is_caught(tmp_path):
    src = _plant_pkg(
        tmp_path,
        {
            "__init__.py": "",
            "tools.py": "from hadavin_sdk import helper" + NL,
            "helper.py": "def f():" + NL + "    from hadavin_sdk.actions import executor" + NL,
            "actions/__init__.py": "",
            "actions/executor.py": "",
        },
    )
    reached = transitive_imports(src, ["hadavin_sdk.tools"])
    assert "hadavin_sdk.actions.executor" in reached and reached & SECRET_HOLDERS


def test_plant_parent_package_import_is_followed(tmp_path):
    src = _plant_pkg(
        tmp_path,
        {
            "__init__.py": "",
            "tools.py": "import hadavin_sdk.guard.http" + NL,
            "guard/__init__.py": "from hadavin_sdk.actions import secrets" + NL,
            "guard/http.py": "",
            "actions/__init__.py": "",
            "actions/secrets.py": "",
        },
    )
    assert "hadavin_sdk.actions.secrets" in transitive_imports(src, ["hadavin_sdk.tools"])


def test_a_type_checking_import_is_not_a_runtime_import(tmp_path):
    guarded = "from typing import TYPE_CHECKING" + NL + "if TYPE_CHECKING:" + NL
    src = _plant_pkg(
        tmp_path,
        {
            "__init__.py": "",
            "tools.py": guarded + "    from hadavin_sdk import app" + NL,
            "app.py": "",
        },
    )
    assert "hadavin_sdk.app" not in transitive_imports(src, ["hadavin_sdk.tools"])


def backends_name_imports(files: list[Path]) -> list[str]:
    """`from hadavin_sdk.backends import <name>` hides the factory (and so the secret providers) behind a package
    attribute where a static scan cannot see it. Only the submodule `table` may be imported that way."""
    hits = []
    for path in files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module == "hadavin_sdk.backends":
                hits += [f"{path.name}: {a.name}" for a in node.names if a.name != "table"]
    return hits


def _secret_free_files() -> list[Path]:
    root = ROOT / "src" / "hadavin_sdk"
    files = [root / "tools.py", root / "guard" / "http.py", root / "guard" / "runmap.py"]
    for folder in SECRET_FREE:
        files += sorted((root / folder).rglob("*.py"))
    return files


def test_k5_secret_free_packages_never_import_a_name_from_backends():
    assert len(_secret_free_files()) > 10
    assert backends_name_imports(_secret_free_files()) == []


def test_plant_a_backends_name_import_is_caught(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text(
        "from hadavin_sdk.backends import make"
        + NL
        + "from hadavin_sdk.backends import table"
        + NL,
        encoding="utf-8",
    )
    assert backends_name_imports([bad]) == ["bad.py: make"]


def test_k5_the_backends_package_file_imports_nothing():
    tree = ast.parse((ROOT / "src" / "hadavin_sdk" / "backends" / "__init__.py").read_text("utf-8"))
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Import | ast.ImportFrom)]
