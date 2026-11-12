"""Guard: pglast is GPL-3.0-or-later, so it stays in the `test` dependency group (the CI oracle)
and never reaches shipped code (src/, demos/, tools/) or a runtime dependency (owner decision
2026-11-01).

Best effort, not a proof. The code scan reads import statements (including the names in
`from x import y`) and string literals that are exactly a pglast module name. NOT checked:
- an import whose name is built at run time (for example `"pg" + "last"` passed to
  `importlib.import_module` or `__import__`) or in an f-string piece such as `f"pglast.{x}"`;
- a copy of the pglast code under another name;
- a single-file `pglast.py` or `pglast.pyi` is scanned only as source (an import inside it is
  not an import of pglast);
- compiled `.pyc` files and Cython `.pyx` source (not scanned, not flagged);
- dependency lists outside pyproject.toml and uv.lock: requirements*.txt, setup.py, Dockerfiles,
  CI `pip install` lines and `[build-system] requires`; the tables of other build tools (hatch,
  poetry, pdm) are not read either.
Names are compared after one normaliser (`_norm`: lower case, runs of `-`, `_`, `.` become one
`-`, edge separators dropped). A folder, or a packed copy (.whl, .egg, .zip, .tar.gz, .tgz, .a),
is flagged ("vendored dir", "vendored archive") when its lower-case name is `pglast` or `_pglast`,
alone or followed by `.libs`, a version or a packing suffix: `pglast.libs`,
`pglast-8.7.dist-info`, `PGLast-8.7.tar.gz`; not `pglastic` or `pglast_utils`.
ANY compiled file under src, demos or tools is flagged ("compiled <name>"), whatever its name: its
name ends in .so, .pyd, .dylib or .dll in any letter case, optionally followed by version numbers
(`libpg_query-<hash>.so.1`). Python files are .py, .pyi, .pyw and files without a suffix whose
first line is a python shebang; they are read with a byte order mark allowed. Dependency-group
names are compared normalised (PEP 735); two names that collide after normalising are reported.

Folders: `.venv` and `node_modules` directly under src, demos or tools are skipped on purpose,
because they hold other people's code. This IS a bypass: pglast placed there is not seen. The same
names deeper down ARE scanned (they may be shipped code).
Symbolic links: a linked folder is listed by its own name (so a link called `pglast` is flagged)
but is NOT entered, so pglast code behind a link with another name is not scanned (recorded by
the test `test_symlinked_dir_is_not_entered`). An unreadable folder raises; a .py or .pyi file
that cannot be parsed is reported as a violation ("cannot parse")."""

import ast
import os
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREES = ("src", "demos", "tools")
BINARY = re.compile(r"(?i).*\.(so|pyd|dylib|dll)(\.\d+)*")  # compiled modules, versioned .so.N too
ARCHIVES = (".whl", ".egg", ".zip", ".tar.gz", ".tgz", ".a")  # packed copies
SKIP_DIRS = {".venv", "node_modules"}  # other people's code, never shipped from here


def _norm(name):  # PEP 503 name; edge separators dropped so `_pglast` and `pglast.libs` match
    return re.sub(r"[-_.]+", "-", name).lower().strip("-")


VENDORED = re.compile(  # pglast itself, not pglastic or pglast_utils (`_` and `.` join names alike)
    r"_?pglast(\.libs|\.dist-info|\.egg-info|[-_.]?\d.*|\.(a|egg|zip|whl|tgz|tar\.gz))?"
)


def _vendored(name):  # a folder or packed copy: pglast, pglast.libs, pglast-8.7.dist-info, _pglast
    return VENDORED.fullmatch(name.lower()) is not None


def _is(
    dep,
):  # a PEP 508 string such as " PGLAST_x[a]>=1 ; marker"; a dict (include-group) is not a name
    return (
        isinstance(dep, str)
        and _norm(re.split(r"[\s;\[<>=!~@(]", dep.strip(), maxsplit=1)[0]) == "pglast"
    )


def _flat(groups, name, seen=()):  # entries of a group with include-group resolved
    for d in groups.get(name, []):  # `groups` has normalised names (PEP 735)
        inc = _norm(str(d.get("include-group"))) if isinstance(d, dict) else None
        if inc is not None and inc not in seen:
            yield from _flat(groups, inc, (*seen, name))
        else:
            yield d


def _hit(deps):  # an include-group dict has no `name` (a cyclic group is yielded as is): skip it
    return any(_is(d.get("name") if isinstance(d, dict) else d) for d in deps)


def _fail(err):  # an unreadable folder must stop the scan, never be skipped silently
    raise err


def _walk(base):  # (files, dirs) under base; SKIP_DIRS are skipped only directly under base
    files, dirs = [], []
    for here, names, leaves in os.walk(base, onerror=_fail):
        if Path(here) == base:
            names[:] = [n for n in names if n not in SKIP_DIRS]
        dirs += [Path(here) / n for n in names]
        files += [Path(here) / n for n in leaves]
    return files, dirs


def _script(path):  # a file without suffix whose first line is a python shebang
    if path.suffix:
        return False
    with path.open("rb") as f:
        first = f.readline(200)
    return first.startswith(b"#!") and b"python" in first


def _code(root, tree):
    files, dirs = _walk(root / tree) if (root / tree).is_dir() else ([], [])  # absent: no files
    bad = [f"{tree}: compiled {p.name}" for p in files if BINARY.fullmatch(p.name)]
    bad += [f"{tree}: vendored dir {p.name}" for p in dirs if _vendored(p.name)]
    bad += [
        f"{tree}: vendored archive {p.name}"
        for p in files
        if _vendored(p.name) and p.name.lower().endswith(ARCHIVES)
    ]
    py = [p for p in files if p.suffix in (".py", ".pyi", ".pyw") or _script(p)]
    if not py:
        bad.append(f"{tree}: no python file scanned")
    for p in py:
        rel = p.relative_to(root / tree).as_posix()
        try:
            nodes = list(ast.walk(ast.parse(p.read_text("utf-8-sig"))))
        except (SyntaxError, ValueError, UnicodeDecodeError):
            bad.append(f"{tree}: {rel} cannot parse")
            continue
        for n in nodes:
            mods = [a.name for a in n.names] if isinstance(n, (ast.Import, ast.ImportFrom)) else []
            mods += [n.module or ""] if isinstance(n, ast.ImportFrom) else []
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                mods += [n.value] if re.fullmatch(r"(?i)_?pglast(\.\w+)*", n.value) else []
            if any(_norm(m.split(".")[0]) == "pglast" for m in mods):
                bad.append(f"{tree}: {rel} imports pglast")
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
            if not top or _norm(k) != "test"
        }
        meta = p.get("metadata", {})
        sections |= {"requires-dist": meta.get("requires-dist", [])}
        sections |= {
            f"requires-dev {k}": v
            for k, v in meta.get("requires-dev", {}).items()
            if _norm(k) != "test"
        }
        bad += [f"uv.lock {p['name']}: {k}" for k, v in sections.items() if _hit(v)]
    return bad


def violations(root):
    """Where pglast reaches shipped code or a runtime dependency under `root`; empty when clean."""
    meta = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))
    uv = meta.get("tool", {}).get("uv", {})
    raw = meta.get("dependency-groups", {})
    groups = {_norm(k): v for k, v in raw.items()}
    bad = ["dependency-groups: names collide after normalising"] * (len(groups) != len(raw))
    bad += [b for t in TREES for b in _code(root, t)]
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


PYPROJECT = (
    '[project]\nname="x"\ndependencies=[]\n'
    '[dependency-groups]\ntest=["pglast==8.7"]\ndev=["pytest"]\n'
)
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
    "optional extra": (
        {"pyproject.toml": PYPROJECT + '[project.optional-dependencies]\nfoo=["pglast"]\n'},
        ["extra foo"],
    ),
    "tool.uv sources": (
        {"pyproject.toml": PYPROJECT + '[tool.uv.sources]\nPGLast={url="https://e.x/p.whl"}\n'},
        ["tool.uv sources"],
    ),
    "uv.lock missing": ({"uv.lock": None}, ["uv.lock missing"]),
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
    "vendored dir": ({"src/pglast/__init__.py": ""}, ["src: vendored dir pglast"]),
    "vendored binary": ({"src/_pglast.so": ""}, ["src: compiled _pglast.so"]),
    "vendored macOS binary": ({"src/_pglast.dylib": ""}, ["src: compiled _pglast.dylib"]),
    "vendored Windows binary": ({"tools/_pglast.pyd": ""}, ["tools: compiled _pglast.pyd"]),
    "cyclic include-group has no name": (
        {"pyproject.toml": PYPROJECT + 'ci=[{include-group="ci"}]\n'},
        [],
    ),
    "cyclic pair still finds pglast": (
        {
            "pyproject.toml": PYPROJECT
            + 'a=[{include-group="b"},"pglast"]\nb=[{include-group="a"}]\n'
        },
        ["group a", "group b"],
    ),
    "top-level .venv import is skipped": ({"src/.venv/lib/m.py": "import pglast\n"}, []),
    "top-level node_modules vendored is skipped": (
        {"demos/node_modules/pglast/x.py": "", "demos/node_modules/_p.so": ""},
        [],
    ),
    "top-level .venv alone is not a scanned file": (
        {"src/m.py": None, "src/.venv/m.py": "x = 1\n"},
        ["src: no python file scanned"],
    ),
    "nested .venv import is scanned": (
        {"src/pkg/.venv/m.py": "import pglast\n"},
        ["src: pkg/.venv/m.py imports pglast"],
    ),
    "nested node_modules vendored is scanned": (
        {"demos/pkg/node_modules/pglast/x.py": "", "demos/pkg/node_modules/_p.so": ""},
        ["demos: compiled _p.so", "demos: vendored dir pglast"],
    ),
    "nested .venv under tools is scanned": (
        {"tools/a/b/.venv/_pglast.dll": ""},
        ["tools: compiled _pglast.dll"],
    ),
    "unparsable python file": ({"src/bad.py": "def (:\n"}, ["src: bad.py cannot parse"]),
    "unparsable stub file": ({"tools/bad.pyi": "class :\n"}, ["tools: bad.pyi cannot parse"]),
    "null byte in python file": ({"src/nul.py": "x = 1\0\n"}, ["src: nul.py cannot parse"]),
    "upper-case binary suffix": ({"src/_pglast.SO": ""}, ["src: compiled _pglast.SO"]),
    "pglast.libs folder (wheel bundle)": (
        {"src/pglast.libs/x.txt": ""},
        ["src: vendored dir pglast.libs"],
    ),
    "dist-info folder": (
        {"tools/pglast-8.7.dist-info/METADATA": ""},
        ["tools: vendored dir pglast-8.7.dist-info"],
    ),
    "underscore-prefixed folder": ({"demos/_pglast/x.txt": ""}, ["demos: vendored dir _pglast"]),
    "upper-case dotted folder": ({"src/PGLast.Libs/x.txt": ""}, ["src: vendored dir PGLast.Libs"]),
    "versioned shared library": (
        {"src/libpg_query-0a1b2c3d.so.1": ""},
        ["src: compiled libpg_query-0a1b2c3d.so.1"],
    ),
    "doubly versioned shared library": (
        {"tools/libpg_query.SO.1.2": ""},
        ["tools: compiled libpg_query.SO.1.2"],
    ),
    "shared library suffix is not a version": ({"src/lib.so.old": ""}, []),
    "import of the compiled module": (
        {"src/m.py": "import _pglast\n"},
        ["src: m.py imports pglast"],
    ),
    "python file with a byte order mark": (
        {"src/m.py": "\ufeffimport pglast\n"},
        ["src: m.py imports pglast"],
    ),
    "group name written in another form": (
        {"pyproject.toml": PYPROJECT.replace("test=", "Test=") + 'ci=[{include-group="TEST"}]\n'},
        ["group ci"],
    ),
    "lock group name written in another form": (
        {
            "uv.lock": LOCK.replace(
                "[package.dev-dependencies]\ntest", "[package.dev-dependencies]\nTEST"
            )
        },
        [],
    ),
    "similar name pglastic is fine": (
        {"src/pglastic/x.txt": "", "tools/pglast_utils/y.txt": ""},
        [],
    ),
    "wheel archive": (
        {"src/pglast-8.7-cp312-linux.whl": ""},
        ["src: vendored archive pglast-8.7-cp312-linux.whl"],
    ),
    "source archive": (
        {"demos/PGLast-8.7.tar.gz": ""},
        ["demos: vendored archive PGLast-8.7.tar.gz"],
    ),
    "egg zip and static library": (
        {"tools/pglast.egg": "", "tools/pglast_8.7.zip": "", "tools/pglast.a": ""},
        [
            "tools: vendored archive pglast.egg",
            "tools: vendored archive pglast_8.7.zip",
            "tools: vendored archive pglast.a",
        ],
    ),
    "similar archive name is fine": ({"src/pglastic-1.whl": "", "src/pglast.py": "x = 1\n"}, []),
    "python script with a shebang": (
        {"tools/run": "#!/usr/bin/env python3\nimport pglast\n"},
        ["tools: run imports pglast"],
    ),
    "windowed python script": ({"src/run.pyw": "import pglast\n"}, ["src: run.pyw imports pglast"]),
    "shell script is not parsed": ({"src/run": "#!/bin/sh\nimport pglast (\n"}, []),
    "relative import of a module named pglast": (
        {"src/m.py": "from . import pglast\n"},
        ["src: m.py imports pglast"],
    ),
    "import of a name from a package": ({"src/m.py": "from os import path\n"}, []),
    "group names that collide after normalising": (
        {"pyproject.toml": PYPROJECT + 'Test=["pytest"]\n'},
        ["dependency-groups: names collide after normalising"],
    ),
    "tab after the dependency name": (
        {"pyproject.toml": PYPROJECT + 'ci=["pglast\\t>=1"]\n'},
        ["group ci"],
    ),
    "venv-like name outside the skip list is scanned": (
        {"src/venv/m.py": "import pglast\n"},
        ["src: venv/m.py imports pglast"],
    ),
}


@pytest.mark.parametrize("case", MUTANTS)
def test_guard_catches(tmp_path, case):
    files = {"pyproject.toml": PYPROJECT, "uv.lock": LOCK} | {f"{t}/m.py": "x = 1\n" for t in TREES}
    files |= MUTANTS[case][0]
    for rel, text in files.items():
        if text is not None:
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / rel).write_text(text, "utf-8")
    assert sorted(violations(tmp_path)) == sorted(MUTANTS[case][1])


def test_unreadable_directory_raises(tmp_path, monkeypatch):
    (tmp_path / "src" / "sub").mkdir(parents=True)
    real = os.scandir

    def deny(path="."):
        if Path(path).name == "sub":
            raise PermissionError(13, "denied", str(path))
        return real(path)

    monkeypatch.setattr(os, "scandir", deny)
    with pytest.raises(PermissionError):
        _walk(tmp_path / "src")


def test_missing_tree_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        _walk(tmp_path / "nope")


def test_symlinked_dir_is_not_entered(tmp_path):
    # Recorded behaviour: a link is listed by name but not entered, so code behind a link with
    # another name is not scanned; a link named pglast is flagged as a vendored dir.
    (tmp_path / "ext").mkdir()
    (tmp_path / "ext" / "m.py").write_text("import pglast\n", "utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "m.py").write_text("x = 1\n", "utf-8")
    try:  # Windows without developer mode cannot create links
        (tmp_path / "src" / "other").symlink_to(tmp_path / "ext", target_is_directory=True)
    except OSError as err:
        if os.name != "nt":
            raise
        pytest.skip(f"cannot create a symbolic link here: {err}")
    assert _code(tmp_path, "src") == []
    (tmp_path / "src" / "pglast").symlink_to(tmp_path / "ext", target_is_directory=True)
    assert _code(tmp_path, "src") == ["src: vendored dir pglast"]
