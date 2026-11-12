"""Guard: pglast is GPL-3.0-or-later, so it stays in the `test` dependency group (the CI oracle)
and never reaches shipped code (src/, demos/, tools/) or a runtime dependency (owner decision
2026-11-01).

Best effort, not a proof. What it reads: import statements (including the names in
`from x import y`), string constants that are exactly a pglast module name (so
`importlib.import_module("pglast.ast")` and `importlib.util.find_spec("pglast")` are caught), PEP 723
inline script metadata blocks (`# /// script` ... `# ///`: the `dependencies` list and
`[tool.uv.sources]`; a block that is not valid TOML is reported), the dependency tables of
pyproject.toml, and uv.lock. The guard walks the working folder with os.walk and does NOT use
`git ls-files` (design choice kept on purpose: a copy not yet added to git is also seen, and the
unreadable-folder, symbolic-link and .venv cases are handled here by their own rules and tests).
What it flags (the "src: ..." line names the tree):
- "compiled <name>": a file under src, demos or tools whose name ends in one of the listed suffixes
  .so, .pyd, .dylib, .dll, .lib, .o or .bundle (any letter case), optionally followed by version
  numbers (`.so.1`); other binaries (.a, .exe, .node, .wasm, .pyc) are not flagged by this rule;
- "vendored dir <name>": a folder whose lower-case name matches the pattern VENDORED (not `_norm`):
  `pglast` or `_pglast`, alone or followed by `.libs`, `.dist-info`, `.egg-info`, a packing suffix,
  or a digit-led tail (`pglast-8.7`, `pglast8`; so an unrelated `pglast8x` is also flagged, which
  only over-flags); not `pglastic` or `pglast_utils`;
- "vendored archive <name>": a file whose name matches VENDORED and ends in .whl, .egg, .zip, .a,
  .7z, .gz, .tgz, .txz, .tbz2, .tar, .tar.gz, .tar.xz or .tar.bz2 (judged by name, never opened);
- "symlinked dir <name>": any symbolic link to a folder under the three trees, except a link named
  `.venv` or `node_modules` directly under a tree (skipped, see the limits). A link is never
  followed, so what it points to is not scanned; the report is the control;
- "imports pglast": a python file (.py, .pyi, .pyw in any letter case, or a file without a suffix
  whose first line is a python shebang, read with a byte order mark allowed) that imports pglast or
  holds a string constant that is a pglast module name. A bare `"pglast"` constant and the piece
  `"pglast"` of `f"pglast{x}"` are flagged too (over-flags only);
- "cannot parse": a python file that is not valid python; "script metadata ...": see above;
- the dependency tables: [project] dependencies and optional-dependencies, every dependency group
  except `test`, [tool.uv] dev-dependencies, constraint-dependencies, override-dependencies and
  sources, and in uv.lock every package's dependencies, optional-dependencies, metadata
  requires-dist, and dev-dependencies or requires-dev groups other than `test`.
Names are compared after the normaliser `_norm` (lower case, runs of `-`, `_`, `.` become one
`-`, edge separators dropped; PEP 503 and PEP 735); two group names that collide after
normalising are reported. Only src must hold at least one python file; demos and tools may be
absent or empty.
Limits, stated plainly (each is NOT checked and would pass this guard):
- an import whose name is built at run time (`"pg" + "last"` given to `__import__`), source text
  run through `exec(...)`, `python -c` or a subprocess, and `pip install pglast` run from python;
- a copy of the pglast code under another name; a single-file `pglast.py` is scanned only as source;
- `.pyc` and Cython `.pyx` files; archives are judged by name, not content; notebooks (`.ipynb`),
  zipapps (`.pyz`), path files (`.pth`) and scripts that carry a suffix other than .py, .pyi and
  .pyw (for example a shebang script named `run.txt`) are not parsed; the names `pglast-stubs`,
  `types-pglast` and `.egg-link` and Windows junctions are not flagged;
- inside a PEP 723 block only `dependencies` and `[tool.uv.sources]` are read; other `[tool.uv]`
  keys there (constraint, override, build and metadata keys) are not;
- dependency lists outside pyproject.toml, uv.lock and PEP 723 blocks: requirements*.txt,
  setup.py, Dockerfiles, CI `pip install` lines, `[build-system] requires`, the tables of other
  build tools (hatch, poetry, pdm), and in pyproject the uv tables `build-constraint-dependencies`,
  `extra-build-dependencies` and `dependency-metadata`, and the `[manifest]` table of uv.lock;
- the dependency group named `test` is exempt by name (that is where pglast belongs), in
  pyproject and, for the top package only, in uv.lock `dev-dependencies`; the uv.lock
  `requires-dev` group `test` is skipped for every package (safe, but not the same rule);
- `.venv` and `node_modules` directly under src, demos or tools are skipped on purpose (other
  people's code): pglast placed there is NOT seen. The same names deeper down ARE scanned;
- an unreadable or vanished python-named or suffix-less file, or folder (permission denied, a
  broken symbolic link, a folder removed during the scan), a missing pyproject.toml and an invalid
  uv.lock RAISE (fail loud); any other file (for example a broken link named `x.txt` or `x.whl`)
  is never opened, so it is neither read nor reported.
"""

import ast
import os
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREES = ("src", "demos", "tools")
BINARY = re.compile(r"(?i).*\.(so|pyd|dylib|dll|lib|o|bundle)(\.\d+)*")  # compiled, .so.N too
ARCHIVES = (  # packed copies (judged by name, never opened)
    (".whl", ".egg", ".zip", ".a", ".7z", ".gz", ".tgz", ".txz", ".tbz2")
    + (".tar", ".tar.xz", ".tar.bz2")  # .tar.gz ends in .gz
)
PY_SUFFIXES = (".py", ".pyi", ".pyw")  # compared in lower case
# PEP 723 inline script metadata: the reference expression from the specification
SCRIPT_BLOCK = re.compile(r"(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<body>(^#(| .*)$\s)+)^# ///$")
SKIP_DIRS = {".venv", "node_modules"}  # other people's code, never shipped from here


def _norm(name):  # PEP 503 name; edge separators dropped so `_pglast` and `pglast.libs` match
    return re.sub(r"[-_.]+", "-", name).lower().strip("-")


VENDORED = re.compile(  # pglast itself, not pglastic or pglast_utils (`_` and `.` join names alike)
    r"_?pglast(\.libs|\.dist-info|\.egg-info|[-_.]?\d.*"
    r"|\.(a|egg|zip|whl|gz|tgz|txz|tbz2|tar|tar\.gz|tar\.xz|tar\.bz2))?"
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


def _script_metadata(text):  # the tables of every PEP 723 `script` block; bad TOML raises
    for m in SCRIPT_BLOCK.finditer(text):
        if m["type"] == "script":
            lines = m["body"].splitlines(keepends=True)
            yield tomllib.loads("".join(ln[2:] if ln.startswith("# ") else ln[1:] for ln in lines))


def _script_names_pglast(text):  # a script block that depends on pglast, or cannot be read
    try:
        for meta in _script_metadata(text):
            deps = meta.get("dependencies", [])
            uv_sources = meta.get("tool", {}).get("uv", {}).get("sources", {})
            if not isinstance(deps, list):  # a string would be read one letter at a time
                return "script metadata cannot parse"
            if _hit(deps) or "pglast" in {_norm(k) for k in uv_sources}:
                return "script metadata names pglast"
    except (tomllib.TOMLDecodeError, AttributeError):  # AttributeError: `tool` is not a table
        return "script metadata cannot parse"
    return None


def _imports_pglast(nodes):  # import statements and pglast-named string constants
    for n in nodes:
        mods = [a.name for a in n.names] if isinstance(n, (ast.Import, ast.ImportFrom)) else []
        mods += [n.module or ""] if isinstance(n, ast.ImportFrom) else []
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            mods += [n.value] if re.fullmatch(r"(?i)_?pglast(\.\w+)*", n.value) else []
        if any(_norm(m.split(".")[0]) == "pglast" for m in mods):
            return True
    return False


def _code(root, tree):
    files, dirs = _walk(root / tree) if (root / tree).is_dir() else ([], [])  # absent: no files
    bad = [f"{tree}: compiled {p.name}" for p in files if BINARY.fullmatch(p.name)]
    bad += [f"{tree}: vendored dir {p.name}" for p in dirs if _vendored(p.name)]
    bad += [f"{tree}: symlinked dir {p.name}" for p in dirs if p.is_symlink()]  # never followed
    bad += [
        f"{tree}: vendored archive {p.name}"
        for p in files
        if _vendored(p.name) and p.name.lower().endswith(ARCHIVES)
    ]
    py = [p for p in files if p.suffix.lower() in PY_SUFFIXES or _script(p)]
    # only src must hold python; demos and tools may be absent or empty
    if tree == "src" and not py:
        bad.append(f"{tree}: no python file scanned")
    for p in py:
        rel = p.relative_to(root / tree).as_posix()
        try:
            text = p.read_text("utf-8-sig")
            nodes = list(ast.walk(ast.parse(text)))
        except (SyntaxError, ValueError, UnicodeDecodeError):
            bad.append(f"{tree}: {rel} cannot parse")
            continue
        bad += [f"{tree}: {rel} imports pglast"] * _imports_pglast(nodes)
        meta_problem = _script_names_pglast(text)
        bad += [f"{tree}: {rel} {meta_problem}"] * (meta_problem is not None)
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
    # --- review round 3 (P0a-r3-1 to P0a-r3-4): each row below is new or newly pinned
    "tools tree absent is clean": ({"tools/m.py": None}, []),
    "demos tree absent is clean": ({"demos/m.py": None}, []),
    "empty demos and tools trees are clean": (
        {"demos/m.py": None, "tools/m.py": None, "demos/notes.txt": "", "tools/notes.txt": ""},
        [],
    ),
    "src with data files only still fails": (
        {"src/m.py": None, "src/notes.txt": ""},
        ["src: no python file scanned"],
    ),
    "tar.xz archive": (
        {"src/pglast-8.7.tar.xz": "", "src/_pglast.tar.xz": ""},
        ["src: vendored archive pglast-8.7.tar.xz", "src: vendored archive _pglast.tar.xz"],
    ),
    "tar.bz2 archive": (
        {"src/pglast-8.7.tar.bz2": "", "src/pglast.tar.bz2": ""},
        ["src: vendored archive pglast-8.7.tar.bz2", "src: vendored archive pglast.tar.bz2"],
    ),
    "plain tar and tbz2 and txz archives": (
        {"demos/pglast.tar": "", "demos/pglast-8.7.tbz2": "", "demos/pglast_8.7.txz": ""},
        [
            "demos: vendored archive pglast.tar",
            "demos: vendored archive pglast-8.7.tbz2",
            "demos: vendored archive pglast_8.7.txz",
        ],
    ),
    "7z and gz archives": (
        {"tools/pglast-8.7.7z": "", "tools/_pglast.gz": ""},
        ["tools: vendored archive pglast-8.7.7z", "tools: vendored archive _pglast.gz"],
    ),
    "tgz archive": ({"src/PGLast-8.7.tgz": ""}, ["src: vendored archive PGLast-8.7.tgz"]),
    "similar name tar.xz is fine": ({"src/pglastic-1.tar.xz": ""}, []),
    "static library lib": ({"src/_pglast.lib": ""}, ["src: compiled _pglast.lib"]),
    "object file": ({"tools/query.O": ""}, ["tools: compiled query.O"]),
    "macOS bundle": ({"demos/q.bundle": ""}, ["demos: compiled q.bundle"]),
    "suffix lib is not a version": ({"src/mylib.libx": "", "src/o": ""}, []),
    "symlinked directory with another name": (
        {"ext/m.py": "import pglast\n", "src/other": ("dir", "ext")},
        ["src: symlinked dir other"],
    ),
    "symlinked directory named pglast": (
        {"ext/m.py": "x = 1\n", "src/pglast": ("dir", "ext")},
        ["src: symlinked dir pglast", "src: vendored dir pglast"],
    ),
    "symlinked directory deep under tools": (
        {"ext/m.py": "x = 1\n", "tools/a/b/ln": ("dir", "ext")},
        ["tools: symlinked dir ln"],
    ),
    "symlinked top-level .venv is skipped": (
        {"ext/m.py": "import pglast\n", "src/.venv": ("dir", "ext")},
        [],
    ),
    "symlinked python file is read through": (
        {"ext/m.py": "import pglast\n", "src/link.py": ("file", "ext/m.py")},
        ["src: link.py imports pglast"],
    ),
    "upper-case python suffix": ({"src/Up.PY": "import pglast\n"}, ["src: Up.PY imports pglast"]),
    "upper-case stub suffix": ({"tools/M.PYI": "import pglast\n"}, ["tools: M.PYI imports pglast"]),
    "stub file that imports pglast": (
        {"src/m.pyi": "import pglast\n"},
        ["src: m.pyi imports pglast"],
    ),
    "find_spec with a literal name": (
        {"src/m.py": "import importlib.util\nimportlib.util.find_spec('pglast')\n"},
        ["src: m.py imports pglast"],
    ),
    "PEP 723 block names pglast": (
        {
            "tools/run.py": "# /// script\n# dependencies = [\n#   'pglast>=8',\n# ]\n# ///\nx = 1\n",
        },
        ["tools: run.py script metadata names pglast"],
    ),
    "PEP 723 block with another name is fine": (
        {"tools/run.py": "# /// script\n# dependencies = ['requests', 'pglastic']\n# ///\nx = 1\n"},
        [],
    ),
    "PEP 723 block with a source for pglast": (
        {
            "tools/run.py": "# /// script\n# [tool.uv.sources]\n"
            "# pglast = { url = 'https://e.x/p.whl' }\n# ///\nx = 1\n"
        },
        ["tools: run.py script metadata names pglast"],
    ),
    "PEP 723 block that is not TOML": (
        {"src/run.py": "# /// script\n# dependencies = [\n# ///\nx = 1\n"},
        ["src: run.py script metadata cannot parse"],
    ),
    "PEP 723 dependencies that is a string": (
        {"tools/run.py": "# /// script\n# dependencies = 'pglast'\n# ///\nx = 1\n"},
        ["tools: run.py script metadata cannot parse"],
    ),
    "PEP 723 tool that is not a table": (
        {"tools/run.py": "# /// script\n# tool = 'x'\n# ///\nx = 1\n"},
        ["tools: run.py script metadata cannot parse"],
    ),
    "PEP 723 block of another type is not read": (
        {"src/run.py": "# /// other\n# dependencies = ['pglast']\n# ///\nx = 1\n"},
        [],
    ),
    "lock optional dependency of another package": (
        {"uv.lock": LOCK + '[package.optional-dependencies]\nfoo=[{name="pglast"}]\n'},
        ["uv.lock other: extra foo"],
    ),
    "lock requires-dist": (
        {"uv.lock": LOCK + '[package.metadata]\nrequires-dist=[{name="pglast"}]\n'},
        ["uv.lock other: requires-dist"],
    ),
    "lock requires-dev group other than test": (
        {"uv.lock": LOCK + '[package.metadata.requires-dev]\nci=[{name="pglast"}]\n'},
        ["uv.lock other: requires-dev ci"],
    ),
    "lock requires-dev group test is exempt": (
        {"uv.lock": LOCK + '[package.metadata.requires-dev]\ntest=[{name="pglast"}]\n'},
        [],
    ),
    "lock edge from the top package": (
        {"uv.lock": LOCK.replace('name="x"\n', 'name="x"\ndependencies=[{name="pglast"}]\n', 1)},
        ["uv.lock x: dependencies"],
    ),
    "lock test group of another package is not exempt": (
        {"uv.lock": LOCK + '[package.dev-dependencies]\ntest=[{name="pglast"}]\n'},
        ["uv.lock other: group test"],
    ),
    "tool.uv dev-dependencies": (
        {"pyproject.toml": PYPROJECT + '[tool.uv]\ndev-dependencies=["pglast"]\n'},
        ["tool.uv dev-dependencies"],
    ),
    "tool.uv override-dependencies": (
        {"pyproject.toml": PYPROJECT + '[tool.uv]\noverride-dependencies=["pglast==8.7"]\n'},
        ["tool.uv override-dependencies"],
    ),
    "egg-info folder": (
        {"tools/pglast.egg-info/PKG-INFO": ""},
        ["tools: vendored dir pglast.egg-info"],
    ),
    "folder with a digit tail": ({"src/pglast8/x.txt": ""}, ["src: vendored dir pglast8"]),
    "folder with a version tail": (
        {"demos/pglast-8.7/x.txt": "", "demos/pglast_8.7/y.txt": ""},
        ["demos: vendored dir pglast-8.7", "demos: vendored dir pglast_8.7"],
    ),
    "digit-free dist-info folder": (
        {"src/pglast.dist-info/METADATA": ""},
        ["src: vendored dir pglast.dist-info"],
    ),
    "digit-free wheel": ({"src/pglast.whl": ""}, ["src: vendored archive pglast.whl"]),
    "digit-free zip": ({"src/pglast.zip": ""}, ["src: vendored archive pglast.zip"]),
    "digit-free tgz": ({"src/pglast.tgz": ""}, ["src: vendored archive pglast.tgz"]),
    "digit-free 7z": ({"src/pglast.7z": ""}, ["src: vendored archive pglast.7z"]),
    "digit-free txz": ({"src/pglast.txz": ""}, ["src: vendored archive pglast.txz"]),
    "digit-free tbz2": ({"src/pglast.tbz2": ""}, ["src: vendored archive pglast.tbz2"]),
    "digit-free tar.gz": ({"src/pglast.tar.gz": ""}, ["src: vendored archive pglast.tar.gz"]),
    "digit-led unrelated folder is flagged too (over-flags only)": (
        {"src/pglast8x/x.txt": ""},
        ["src: vendored dir pglast8x"],
    ),
}

# Inputs the guard cannot read: it must raise, never pass quietly.
RAISES = {
    "invalid uv.lock": ({"uv.lock": "[[package"}, tomllib.TOMLDecodeError),
    "missing pyproject.toml": ({"pyproject.toml": None}, FileNotFoundError),
    "dangling link with a python name": ({"src/gone.py": ("file", "nope")}, FileNotFoundError),
    "dangling link without a suffix": ({"tools/gone": ("file", "nope")}, FileNotFoundError),
}


def _build(tmp_path, extra):  # write the default clean tree, then `extra` (None removes a file)
    files = {"pyproject.toml": PYPROJECT, "uv.lock": LOCK} | {f"{t}/m.py": "x = 1\n" for t in TREES}
    files |= extra
    links = {}
    for rel, text in files.items():
        if isinstance(text, tuple):  # ("dir" or "file", target path under tmp_path): a link
            links[rel] = text
        elif text is not None:
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / rel).write_text(text, "utf-8")
    for rel, (kind, target) in links.items():  # after the files, so a target already exists
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        try:  # Windows without developer mode cannot create links
            (tmp_path / rel).symlink_to(tmp_path / target, target_is_directory=kind == "dir")
        except OSError as err:
            if os.name != "nt":
                raise
            pytest.skip(f"cannot create a symbolic link here: {err}")


@pytest.mark.parametrize("case", MUTANTS)
def test_guard_catches(tmp_path, case):
    _build(tmp_path, MUTANTS[case][0])
    assert sorted(violations(tmp_path)) == sorted(MUTANTS[case][1])


@pytest.mark.parametrize("case", RAISES)
def test_guard_raises_when_it_cannot_read(tmp_path, case):
    _build(tmp_path, RAISES[case][0])
    with pytest.raises(RAISES[case][1]):
        violations(tmp_path)


def test_unreadable_python_file_raises(tmp_path, monkeypatch):  # root can read any mode: fake it
    _build(tmp_path, {"src/locked.py": "x = 1\n"})
    real = Path.read_text

    def deny(self, *args, **kwargs):
        if self.name == "locked.py":
            raise PermissionError(13, "denied", str(self))
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny)
    with pytest.raises(PermissionError):
        violations(tmp_path)


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


def test_symlinked_dir_is_reported_and_not_entered(tmp_path):
    # The code behind a link is not scanned (the link is not followed); the link itself is reported,
    # whatever its name, so it cannot hide a pglast folder.
    _build(tmp_path, {"ext/m.py": "import pglast\n", "src/other": ("dir", "ext")})
    assert _code(tmp_path, "src") == ["src: symlinked dir other"]
