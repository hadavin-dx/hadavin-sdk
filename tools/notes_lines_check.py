"""List the tests (and the files that make tests pass or fail) that are new or changed against a base commit and check
that a builder's notes hold a row for each.

    python tools/notes_lines_check.py <base-commit> <notes.md> <file> [<file> ...]
    python tools/notes_lines_check.py --auto <base-commit> [--head <commit>]

What it reads. In each test file it reads every top-level `test_*` function (plain or `async`) and every `test_*`
method of a top-level class whose name starts with `Test` or that is a `unittest.TestCase` (named `Class::test_x`).
A test is "new or changed" when it is missing from the base commit's copy of the file, or when its own syntax tree
differs, or when the syntax tree of anything it uses differs, to any depth and through every link:
- a module-level function, class, import, `+=`, or constant it names; a constant is followed through the value that
  is behind it (`B = A + 1`, `X = _build()`, a tuple target `A, B = 1, 2`, an annotated or augmented assignment), so
  `SKIP = False` read by `pytestmark = pytest.mark.skipif(SKIP, ...)` lists every test when `SKIP` turns `True`;
- a fixture it names as a parameter, looked up in its own file and then in the nearest `conftest.py` above it
  (a changed conftest fixture lists the tests that take it), and every fixture marked `autouse=True`;
- the ways a whole file or class is switched off or changed: a module-level `pytestmark`, `__test__`,
  `setup_module`, `teardown_module`, `setup_function`, `pytest_generate_tests`, every other module-level statement
  that runs at collection (an `if`, a `try`, a `for`, a call); in a test class its decorators, bases, every helper
  method that is no test, `setup_method`, `setup_class`, and a class-level fixture;
- the code of every `conftest.py` above the test file (its hooks and its module-level statements), and the text of
  every module a `pytest_plugins` list names or a `-p name` in `addopts` loads (they act on every test);
- the ways a unittest class is set up and torn down (`setUp`, `setUpClass`, `tearDown`, `tearDownClass`, the async
  forms, and `setUpModule`, `tearDownModule`), a fixture a test names as a text (`usefixtures("x")`,
  `request.getfixturevalue("x")`), a name a walrus binds at module level (`W = (X := 1)` binds X too), and a star
  import (`from tests.x import *` makes every name of the module part of the file);
- what a name imported from another test module is, followed from helper to helper to any depth (`from tests.x
  import name`, `from tests import x` then `x.name`, `import tests.x as x`, a relative form, also inside a
  function), so a helper two imports away lists the test that reaches it.
A change to a helper therefore lists every test that uses it. With `--auto`, when any file under `tests/` changed,
EVERY test file of the head commit is read, so a change to a helper alone lists the tests of the files that import
it. A new module-level function or constant that nothing in the tree names (no test, fixture, conftest, import or
mutant reaches it) is a unit of no test, so it needs no row: it cannot change a run until something uses it, and
the change that uses it lists the user.

Six kinds of file are in scope, because a change to any of them can make a test pass or fail without touching a
test function. `tests/test_*.py` and `tests/*_test.py` (pytest's default file patterns, at any depth): the tests, as
above. `tests/policy_mutants.py` and `tests/stage_mutants.py`: each `mutant(...)` (or `Mutant(...)`) call whose first
argument is a text is one unit named by that text, and its signature also holds every helper of the file that the
call reaches; a mutant that is new or altered needs a row, a mutant that is gone is a problem, and so is a count
that fell. `conftest.py` (also the one at the root of the repository): each top-level function or class is one unit,
each name a module-level assignment binds (`pytest_plugins`, `collect_ignore`, a constant) is one unit with all
assignments of that name, and every other top-level statement (a `for`, an `if`, `collect_ignore.append(...)`) is
the unit `conftest module code`. `tests/fixtures/policy_sources_*.txt`: the whole file is one unit named by its
file name. The pytest settings of the repository (`pytest.ini`, `tox.ini`, `setup.cfg`, and the `[tool.pytest]`
tables of `pyproject.toml`; a change of a dependency is no change): one unit named by the file. Any other file
under `tests/` that is not Python (data, a script): one unit named by the file name.

What the notes must hold. A table row (a line that starts with `|`) whose FIRST cell is the file (its name, or the
end of its path that starts at a path part, ending `.py` or `.txt`; a bare file name serves only a file that no
other path of the tree shares the name of) and whose SECOND cell names the unit in backticks (`test_x`,
`Class::test_x`, a function of a conftest, a file name; for a mutant the full text of its name, in backticks or, when
the name holds a backtick itself, written in the cell); the id is read from that cell only, so a name mentioned in
another cell or another row counts for nothing, and the same name in two files needs a row for each file. The LAST
cell is the reason; it must pass `reason_problem`: at least `MIN_WORDS` words, not a placeholder, one of
`REASON_MARKERS` as a whole word or phrase (a killing mutant, a failing run on the old code, a plant, or the
control reason), and after the marker an identifier (a backticked text, a file name, a mutant code such as B11,
a test name or a commit id) that a reader can look up. With `--auto` each `test_x` the reason names must be a test
of the head commit, each `x.log` a file under a `logs/` folder, and each backticked mutant name (it starts with a
mutant code and a space) a mutant of a mutant file. A mutant row is found by its whole cell or one exact `;` item
of it, never by a part. A unit that existed in the base and is gone now is a problem too.

What it does NOT show. It does not show that a test was not weakened: it lists the changed units and checks that a
reason with something to look up was written; whether the reason is true is for the reviewer reading the diff. It
reads only the syntax of Python files, the settings files named above and the text of the other files under
`tests/`: a test written another way (generated at run time, or collected by a plugin that is not in a conftest), a
change in `src/` or `tools/` that a test uses (those have their own mutants), a change to a file outside the kinds
above (a workflow, a lock file, an environment variable of the test run, a `-p` plugin named only on the command
line) and a dependency version are not seen. A name built at run time with `getattr` or `exec` is not followed. A
file that imports with `importlib`, `pkgutil` or `__import__` is read as reaching the modules it names as text and
every Python file below each package folder it imports from; a module name built at run time (`import_module(f"tests.x.
dyn_{n}")`) reaches every Python file whose dotted name starts with the text the name starts with, and a name that starts
with a value (`import_module(name)`) in a file that imports no package of `tests` reaches every Python file under
`tests` (the one rule: a name that cannot be read lists every test of the file). The notes files of the change are read
as ONE table (rows of all of them, the last row of a name wins), because the change is read against the merge base and
not against the last batch: a row of an older batch's notes file serves a unit that a later batch changed again, and
the tool cannot tell; the reviewer reading the diff of the batch does. A text a function reads from a file at run time is seen only through the fixture and data file kinds. A
row is checked for form and for the existence of what it names, never for truth: a reason that names a real mutant
that does not cover the test passes. The unit cell of a row must name a test, a mutant or a unit of the head
commit, and each row of a notes file is checked against the units of its file, so a row that names a unit that
exists nowhere is a problem.

Exit codes: 0 when every listed unit has its row; 1 with one plain line per problem; 1 when the base commit does not
resolve (a mistyped base would make every test look new); 1 when git cannot give the change (a failed `merge-base`
or `diff`: never read as "nothing changed"); 2 for a wrong command line. `--auto <base>` is for a pull request: it
reads the change as `git diff --no-renames <merge-base of base and head> <head>` and every file's text as the blob of
that head (`git show <head>:path`), never the working tree, so the answer is the same whatever is checked out, and
each run covers the whole pull request, not the last push. `--head` defaults to HEAD. With no file of the six kinds
in the change there is nothing to check (and it says so); with a changed unit and no notes file in the change,
every changed unit is a problem (no row). It runs `git` only, with a fixed argument list and no shell, and reads
files; it never writes."""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

MIN_WORDS = 4  # words of the reason cell
CONFTEST_CODE = "conftest module code"  # the unit that holds every top-level statement of a conftest that is no name
PLACEHOLDERS = frozenset(
    {"ok", "todo", "tbd", "x", "n/a", "na", "same", "none", "-", "...", "later"}
)
# Whole words or phrases (a word boundary on both sides: "plant" is not found in "implant", "control" is not found in
# "controller"). "passes on" is not a reason: that a test passes on the old code is a fact to explain, not an
# explanation.
REASON_MARKERS = (
    "killing mutant",
    "fails on",
    "fail-before",
    "fails before",
    "plant",
    "control",
)
_MARKER = re.compile(
    r"\b(?:killing mutants?|fails? on|fail-before|fails? before|plants?|controls?)\b", re.IGNORECASE
)
# Something a reader can look up after the marker: a backticked text, a file name, a mutant code (B11, P09b), a test
# name, or a commit id of 7 to 40 hex digits (with at least one digit, so a word like "defaced" is not one).
_IDENTIFIER = re.compile(
    r"`[^`]+`"
    r"|[\w./-]+\.(?:txt|log|md|json|py)\b"
    r"|\b[A-Z]{1,3}\d+[a-z]?\b"
    r"|\btest_\w+"
    r"|\b(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b"
)
_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)
_MUTANT_CALLS = ("mutant", "Mutant")

Loader = Callable[
    [str], str
]  # path of a file -> its text in the state being read ("" when it is not there)


# ----------------------------------------------------------------------------------------------- reading a module


_DECLARATIONS = (
    *_FUNCS,
    ast.ClassDef,
    ast.Assign,
    ast.AnnAssign,
    ast.AugAssign,
    ast.Import,
    ast.ImportFrom,
)


def _is_declaration(n: ast.stmt) -> bool:
    """True for a statement the module table covers (a definition, an assignment, an import) and for a docstring."""
    if (
        isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Constant)
        and isinstance(n.value.value, str)
    ):
        return True
    if isinstance(n, ast.Assign):
        return all(_plain_target(t) for t in n.targets)
    if isinstance(n, (ast.AnnAssign, ast.AugAssign)):
        return _plain_target(n.target)
    return isinstance(n, _DECLARATIONS)


def _plain_target(t: ast.AST) -> bool:
    """True when an assignment target binds only names (`X`, `A, B`, `[A, *B]`); a subscript or an attribute
    (`collect_ignore[0] = ...`, `settings.x = ...`) changes something that already exists: module code."""
    if isinstance(t, ast.Name):
        return True
    if isinstance(t, (ast.Tuple, ast.List)):
        return all(_plain_target(e) for e in t.elts)
    if isinstance(t, ast.Starred):
        return _plain_target(t.value)
    return False


def _target_names(t: ast.AST) -> list[str]:
    """Every name an assignment target binds, tuples and lists included."""
    if isinstance(t, ast.Name):
        return [t.id]
    if isinstance(t, (ast.Tuple, ast.List)):
        return [n for e in t.elts for n in _target_names(e)]
    if isinstance(t, ast.Starred):
        return _target_names(t.value)
    return []


def _bound(alias: ast.alias) -> str:
    return alias.asname or alias.name.split(".")[0]


def _is_autouse(fn: ast.AST) -> bool:
    """True for a function decorated `@pytest.fixture(..., autouse=True, ...)` (or `@fixture(...)`)."""
    for d in getattr(fn, "decorator_list", []):
        if isinstance(d, ast.Call):
            callee = d.func.attr if isinstance(d.func, ast.Attribute) else getattr(d.func, "id", "")
            if callee == "fixture" and any(
                k.arg == "autouse" and isinstance(k.value, ast.Constant) and k.value.value is True
                for k in d.keywords
            ):
                return True
    return False


def _star_stems(tree: ast.AST, rel: str) -> list[str]:
    """The path stems of the modules under `tests` that the file imports with `from tests.x import *`: such an
    import makes every name of the module a name of the file, so a change of any of them is part of every unit."""
    return sorted(
        {
            stem
            for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names)
            for stem in [_stem(rel, n.level, n.module)]
            if stem is not None
        }
    )


def _walrus_names(node: ast.AST) -> list[str]:
    """The names a walrus (`(NAME := value)`) binds anywhere inside `node`: at module level they are module
    constants too, although the statement that holds them binds another name (`W = (NAME := 1)`)."""
    return sorted({n.target.id for n in ast.walk(node) if isinstance(n, ast.NamedExpr)})


def _stem(rel: str, level: int, module: str | None) -> str | None:
    """The path stem of the module an import names, or None when it is not under `tests`. `from tests.x import a`
    names tests/x; `from . import x` or `from .x import a` in tests/y.py names tests/x."""
    parts = module.split(".") if module else []
    if level:
        here = rel.split("/")[:-1]
        parts = [*(here[: len(here) - (level - 1)] if level > 1 else here), *parts]
    return "/".join(parts) if parts and parts[0] == "tests" else None


def _imports(tree: ast.AST, rel: str) -> dict[str, tuple[str, str | None]]:
    """local name -> (path stem of a module under `tests`, the name taken from it or None for the module itself),
    for every import of the file that reaches such a module (module level or inside a function)."""
    out: dict[str, tuple[str, str | None]] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            stem = _stem(rel, n.level, n.module)
            if stem is not None:
                # a star import binds no name of its own: `_star_stems` reads it (every name of the module)
                out.update({a.asname or a.name: (stem, a.name) for a in n.names if a.name != "*"})
        elif isinstance(n, ast.Import):
            for a in n.names:
                stem = _stem(rel, 0, a.name)
                if stem is not None:
                    # `import tests.x as y` binds y; `import tests.x` binds the dotted name `tests.x` (two such imports
                    # must not share the key `tests`)
                    out[a.asname or a.name] = (stem, None)
    return out


# Names that switch tests off or change how they are collected or set up, wherever they are defined in a file: a
# change to any of them is part of every unit of the file (and, in a conftest, of every test under its folder).
SWITCH_NAMES = (
    "__test__",
    "setup_module",
    "teardown_module",
    "setUpModule",
    "tearDownModule",
    "setup_function",
    "teardown_function",
    "pytest_generate_tests",
    "pytest_collection_modifyitems",
    "pytest_configure",
    "pytest_runtest_setup",
    "pytest_plugins",
    "collect_ignore",
    "collect_ignore_glob",
)


# The calls that import a module by a name that may be worked out at run time. A file that makes one (a conftest that
# imports every module of a folder at collection) depends on the text of every module it can reach that way.
DYNAMIC_IMPORTS = (["import_module"], ["iter_modules"], ["walk_packages"], ["__import__"])
# The calls that name a fixture as a text, not as a parameter.
FIXTURE_BY_TEXT = (["usefixtures"], ["getfixturevalue"], ["getfuncargvalue"])


def _dotted_path(rel: str) -> str:
    """`tests/x/y.py` -> `tests.x.y` (a package's `__init__.py` is the package)."""
    return rel.removesuffix(".py").removesuffix("/__init__").replace("/", ".")


class _Module:
    """One parsed Python file: the dump of every module-level binding (every name an assignment binds, tuple targets
    too), the value nodes behind those names, the nodes of its functions and classes, the imports of the whole file
    (also inside a function), its autouse fixtures and the module code that runs when the file is collected."""

    def __init__(self, rel: str, source: str) -> None:
        self.rel = rel
        self.tree = ast.parse(source)
        self.dumps: dict[str, str] = {}
        self.nodes: dict[str, ast.AST] = {}
        self.values: dict[str, list[ast.AST]] = {}
        for n in self.tree.body:
            if isinstance(n, (*_FUNCS, ast.ClassDef)):
                names = [n.name]
                self.nodes[n.name] = n
            elif isinstance(n, ast.Assign) and _is_declaration(n):
                names = [name for t in n.targets for name in _target_names(t)]
                self._value(names, n.value)
                names += _walrus_names(n.value)
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and _is_declaration(n):
                # `X += ...` changes what X is, so it is joined to the dump of X
                names = _target_names(n.target)
                if n.value is not None:
                    self._value(names, n.value)
                    names += _walrus_names(n.value)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                names = [_bound(a) for a in n.names]
            else:
                continue
            for name in names:
                self.dumps[name] = self.dumps.get(name, "") + ast.dump(n)
        self.imports = _imports(self.tree, rel)
        self.stars = _star_stems(self.tree, rel)
        # the modules a `pytest_plugins = [...]` list names (a text): pytest imports them, so each acts on every test
        # under the folder of the conftest like the conftest itself
        self.plugin_names: list[str] = [
            c.value
            for n in self.tree.body
            if isinstance(n, (ast.Assign, ast.AnnAssign))
            and "pytest_plugins" in _assigned_names(n)
            and n.value is not None
            for c in ast.walk(n.value)
            if isinstance(c, ast.Constant) and isinstance(c.value, str)
        ]
        self.autouse = [n.name for n in self.tree.body if isinstance(n, _FUNCS) and _is_autouse(n)]
        # module-level statements that bind nothing the table above knows (`if`, `try`, `for`, `with`, a call such
        # as `pytest.skip(allow_module_level=True)` or `collect_ignore.append(...)`, an assignment to a subscript
        # or an attribute): code that runs when the file is collected and can switch every test of it off or on,
        # so it is part of every unit of the file
        self.glue = [n for n in self.tree.body if not _is_declaration(n)]
        self.glue_dump = "".join(ast.dump(n) for n in self.glue)
        # modules that the file imports by a name worked out at run time (`importlib.import_module(...)`,
        # `pkgutil.iter_modules(...)`, `__import__(...)`): see `_Signatures.closure`
        self.dynamic = False
        self.dynamic_names: list[str] = []  # the dotted names written as text in such a call
        # a name built at run time (`import_module(f"tests.x.dyn_{n}")`, `import_module("tests.x." + n)`): the text it
        # starts with ("tests.x.dyn_"), or "" when it starts with a value (`import_module(name)`)
        self.dynamic_prefixes: list[str] = []
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Call) and _dotted(n.func)[-1:] in DYNAMIC_IMPORTS:
                self.dynamic = True
                self.dynamic_names += [
                    a.value
                    for a in n.args
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)
                ]
                if _dotted(n.func)[-1:] in (["import_module"], ["__import__"]) and n.args:
                    prefix = _literal_start(n.args[0])
                    if prefix is not None:
                        self.dynamic_prefixes.append(prefix)

    def _value(self, names: list[str], value: ast.AST) -> None:
        for name in names:
            self.values.setdefault(name, []).append(value)

    def children_of(self, name: str) -> list[str]:
        """The names the definition of `name` uses: what a function or class uses, and what the values behind an
        assignment of the name use (`X = _build()`, `B = A + 1`, `pytestmark = pytest.mark.skipif(SKIP)`)."""
        out: set[str] = set()
        if name in self.nodes:
            out |= _used(self.nodes[name])
        for value in self.values.get(name, []):
            out |= _used(value)
        return sorted(out)


def _literal_start(a: ast.AST) -> str | None:
    """The text a module name starts with when the name is built at run time: `f"tests.x.dyn_{n}"` gives
    "tests.x.dyn_", `"tests.x." + name` gives "tests.x.", a name that starts with a value (`name`, `f"{p}.x"`) gives
    "". A plain text (a constant) gives None: it is followed as written (`dynamic_names`)."""
    if isinstance(a, ast.Constant) and isinstance(a.value, str):
        return None
    if isinstance(a, ast.JoinedStr):
        first = a.values[0] if a.values else None
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
        return ""
    if isinstance(a, ast.BinOp) and isinstance(a.op, (ast.Add, ast.Mod)):
        left = a.left
        while isinstance(left, ast.BinOp) and isinstance(left.op, ast.Add):
            left = left.left
        if isinstance(left, ast.Constant) and isinstance(left.value, str):
            return left.value.split("%", 1)[0]
        return ""
    return ""


def _dotted(n: ast.AST) -> list[str]:
    """['a', 'b', 'c'] for the expression `a.b.c` (names and attributes only), else []."""
    parts: list[str] = []
    while isinstance(n, ast.Attribute):
        parts.append(n.attr)
        n = n.value
    if not isinstance(n, ast.Name):
        return []
    return [n.id, *reversed(parts)]


def _used(node: ast.AST) -> set[str]:
    """The names a function uses: every name it reads, every dotted chain `a.b.c` and each prefix of it (the walk visits
    the inner attribute nodes too; a module's member, also through `import tests.x`), and every parameter (a fixture is a
    parameter)."""
    used: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and _dotted(n.func)[-1:] in FIXTURE_BY_TEXT:
            # `@pytest.mark.usefixtures("a", "b")` and `request.getfixturevalue("a")` name a fixture as a text
            used |= {
                a.value for a in n.args if isinstance(a, ast.Constant) and isinstance(a.value, str)
            }
        if isinstance(n, ast.Name):
            used.add(n.id)
        elif isinstance(n, ast.Attribute):
            chain = _dotted(
                n
            )  # `tests.x.name` (the walk also reaches the inner `tests.x`, so each prefix is used)
            if chain:
                used.add(".".join(chain))
    if isinstance(node, _FUNCS):
        args = node.args
        used |= {a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    return used


class _Signatures:
    """The signature of a unit: its own dump plus the dump of everything it uses, to any depth, across the files
    under `tests` that it imports from (each file is parsed once)."""

    def __init__(self, loader: Loader | None) -> None:
        self.loader = loader
        self.modules: dict[str, _Module | None] = {}
        # the paths of the files of the state being read (a loader may carry them as `.files`): needed to find the
        # modules that a file imports by a name worked out at run time
        self.files: list[str] = list(getattr(loader, "files", None) or [])
        self._plugins: list[str] | None = None

    def module(self, rel: str, source: str | None = None) -> _Module | None:
        if rel not in self.modules:
            text = source if source is not None else (self.loader(rel) if self.loader else "")
            try:
                self.modules[rel] = _Module(rel, text) if text else None
            except SyntaxError:
                self.modules[rel] = None
        return self.modules[rel]

    def conftests(self, rel: str) -> list[_Module]:
        """The conftests that act on the file `rel`, the one nearest to it LAST: `conftest.py` at the root and
        one in each folder on the way to the file (a fixture or a hook of any of them reaches the file's tests)."""
        parts = rel.split("/")[:-1]
        out = []
        for i in range(len(parts) + 1):
            candidate = "/".join([*parts[:i], "conftest.py"])
            if candidate == rel:
                continue
            mod = self.module(candidate)
            if mod is not None:
                out.append(mod)
        return out

    def _file_of(self, stem: str) -> str | None:
        return next((c for c in (f"{stem}.py", f"{stem}/__init__.py") if self.module(c)), None)

    def _dynamic_files(self, m: _Module) -> list[str]:
        """The files a file that imports by a run-time name can reach: each module it names as text in such a call
        (`import_module("tests.x.y")`), and every Python file below each package folder it imports a name from
        (`from tests.contracts import kinds`, then `importlib.import_module(f"{kinds.__name__}.{name}")` or
        `pkgutil.iter_modules(kinds.__path__)`)."""
        found: set[str] = set()
        for dotted in m.dynamic_names:
            stem = _stem(m.rel, 0, dotted)
            file = self._file_of(stem) if stem else None
            if file:
                found.add(file)
        for stem, taken in m.imports.values():
            folder = stem if taken is None else f"{stem}/{taken}"
            found |= {f for f in self.files if f.startswith(folder + "/") and f.endswith(".py")}
        # a name built at run time: every module whose dotted name starts with the text the name starts with; a name
        # that starts with a value reaches the package folders imported above, and, when the file imports none, every
        # Python file under `tests` (the rule: a name that cannot be read lists every test of the file)
        for prefix in m.dynamic_prefixes:
            if prefix:
                found |= {f for f in self.files if _dotted_path(f).startswith(prefix)}
            elif not any(stem for stem, _ in m.imports.values()):
                found |= {f for f in self.files if f.startswith("tests/") and f.endswith(".py")}
        found.discard(m.rel)
        return sorted(found)

    def _named_files(self, names: list[str], rel: str) -> list[str]:
        """The files of the modules a list of dotted names (a `pytest_plugins` list, a `-p` option) names."""
        out: set[str] = set()
        for dotted in names:
            stem = _stem(rel, 0, dotted)
            file = self._file_of(stem) if stem else None
            if file:
                out.add(file)
        return sorted(out)

    def _config_plugins(self) -> list[str]:
        """The dotted names of the plugins the pytest settings of the repository load on every run (`-p name` in
        `addopts`); a `-p no:name` switches a plugin off and names no module."""
        if self._plugins is None:
            self._plugins = []
            for rel in ("pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg"):
                text = self.loader(rel) if self.loader else ""
                for line in re.findall(
                    r"addopts\s*[=:]\s*(.*?)(?:\n\s*\n|\n\S|\Z)", text, re.DOTALL
                ):
                    words = re.findall(r"[^\s\"',\[\]]+", line)
                    for i, w in enumerate(words):
                        name = words[i + 1] if w == "-p" and i + 1 < len(words) else None
                        name = name or (w[2:] if w.startswith("-p") and len(w) > 2 else None)
                        if name and not name.startswith("no:"):
                            self._plugins.append(name)
        return self._plugins

    def _imported(
        self, table: dict[str, tuple[str, str | None]], head: str, attr: str
    ) -> tuple[_Module | None, str]:
        """(the module and member that the import `head` (+ `.attr`) of the table stands for, the member name)."""
        stem, taken = table[head]
        if taken is None:  # `import tests.x as head`: head.attr is a member of tests/x.py
            return self.module(self._file_of(stem) or ""), attr
        file = self._file_of(stem)
        inner = self.module(file) if file else None
        if (
            inner is not None and taken in inner.dumps
        ):  # `from tests.x import taken`: a member of tests/x.py
            return inner, taken
        sub = self._file_of(
            f"{stem}/{taken}"
        )  # `from tests import taken`: taken is the module tests/taken.py
        return self.module(sub) if sub else None, attr

    @staticmethod
    def _head(table: dict[str, tuple[str, str | None]], name: str) -> tuple[str | None, str]:
        """(the longest dotted prefix of `name` that is a key of the import table, the part after it)."""
        parts = name.split(".")
        for i in range(len(parts), 0, -1):
            head = ".".join(parts[:i])
            if head in table:
                return head, parts[i] if i < len(parts) else ""
        return None, ""

    def closure(
        self, mod: _Module, node: ast.AST, own: str, extra: tuple[ast.AST, ...] = ()
    ) -> str:
        """The signature text of `node`, a unit of `mod` named `own`. `extra` are further nodes that act on the unit
        (the body statements and decorators of the class of a test method)."""
        parts: list[str] = []
        seen: set[tuple[str, str]] = {(mod.rel, own)}
        todo: list[tuple[_Module, str]] = []
        touched: set[str] = set()

        def touch(
            m: _Module,
        ) -> None:  # the collect-time code of a file is part of every unit that reaches the file
            if m.rel in touched:
                return
            touched.add(m.rel)
            if m.glue_dump:
                parts.append(f"|glue {m.rel}={m.glue_dump}")
                for g in m.glue:
                    todo.extend((m, u) for u in sorted(_used(g)))
            # `from tests.x import *`: every name of the module is a name of the file
            for stem in m.stars:
                star = self.module(self._file_of(stem) or "")
                if star is not None:
                    touch(star)
                    todo.extend((star, n) for n in sorted(star.dumps))
            if m.dynamic:
                # the file imports modules by a name worked out at run time: every module it can reach that way is
                # part of every unit that reaches the file, and so is everything those modules use
                for rel in self._dynamic_files(m):
                    other = self.module(rel)
                    if other is not None:
                        touch(other)
                        todo.extend((other, n) for n in sorted(other.dumps))

        touch(mod)
        # the plugins the settings load on every run, and the modules a `pytest_plugins` list names, act on every
        # test: their text is part of every unit
        for rel in self._named_files(self._config_plugins(), mod.rel):
            plugin = self.module(rel)
            if plugin is not None:
                touch(plugin)
                todo.extend((plugin, n) for n in sorted(plugin.dumps))
        for conf in self.conftests(mod.rel):
            # a conftest acts on every test under its folder: its collect-time code, its hooks and switches and its
            # autouse fixtures are part of the unit; a fixture a unit names as a parameter is looked up below
            touch(conf)
            todo += [(conf, n) for n in (*SWITCH_NAMES, *conf.autouse) if n in conf.dumps]
            for rel in self._named_files(conf.plugin_names, conf.rel):
                plugin = self.module(rel)
                if plugin is not None:
                    touch(plugin)
                    todo.extend((plugin, n) for n in sorted(plugin.dumps))
        if kind_of(mod.rel) != "conftest":  # (a conftest's own switches are its own units)
            todo += [(mod, n) for n in SWITCH_NAMES if n in mod.dumps]
        todo += [(mod, u) for u in sorted(_used(node))]
        for e in extra:
            parts.append(f"|class {mod.rel}={ast.dump(e)}")
            todo += [(mod, u) for u in sorted(_used(e))]
        todo += [(mod, a) for a in mod.autouse]
        if (
            "pytestmark" in mod.dumps
        ):  # a module-level mark (skip, xfail) acts on every test of the file
            todo.append((mod, "pytestmark"))
        while todo:
            m, name = todo.pop()
            if (m.rel, name) in seen:
                continue
            seen.add((m.rel, name))
            touch(m)
            if name in m.dumps:
                parts.append(f"|{m.rel}:{name}={m.dumps[name]}")
                # what the definition of the name uses, and what the values behind an assignment of it use
                todo += [(m, u) for u in m.children_of(name)]
            else:
                # a name the file does not define: a fixture of the nearest conftest that defines it
                for conf in reversed(self.conftests(m.rel)):
                    if name in conf.dumps:
                        todo.append((conf, name))
                        break
            # (every import of the file, also one inside a function: see `_imports`)
            head, attr = self._head(m.imports, name)
            if head is None:
                continue
            target, member = self._imported(m.imports, head, attr)
            if target is None:
                continue
            touch(target)
            if member and member in target.dumps:
                todo.append((target, member))
            elif (
                not member
            ):  # the module itself is used as a value: its whole text is the dependency
                parts.append(f"|module {target.rel}={ast.dump(target.tree)}")
        return ast.dump(node) + "".join(sorted(parts))


def _is_fixture(fn: ast.AST) -> bool:
    """True for a function decorated `@pytest.fixture` or `@fixture` (with or without a call)."""
    for d in getattr(fn, "decorator_list", []):
        target = d.func if isinstance(d, ast.Call) else d
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
        if name == "fixture":
            return True
    return False


def _is_test_class(n: ast.ClassDef) -> bool:
    """pytest collects a class whose name starts with `Test` and, whatever its name, a `unittest.TestCase`."""
    if n.name.startswith("Test"):
        return True
    return any(
        (b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", "")) == "TestCase"
        for b in n.bases
    )


def _class_extras(cls: ast.ClassDef, method: ast.AST) -> tuple[ast.AST, ...]:
    """What acts on a test method besides its own body: the decorators and bases of its class, the class-level
    statements that are no method (`pytestmark`, an attribute), every `setup*` and `teardown*` method and every
    fixture of the class (they run for every test of it), and each other method the test reaches through
    `self.name` or `cls.name`, to any depth (a helper method)."""
    helpers = {
        m.name: m for m in cls.body if isinstance(m, _FUNCS) and not m.name.startswith("test")
    }
    # (`setUp`, `setUpClass`, `tearDown`, `tearDownClass` of a unittest.TestCase and pytest's `setup_method`: the
    # words are compared in lower case)
    always = [
        m
        for m in helpers.values()
        if m.name.lower().startswith(("setup", "teardown", "asyncsetup", "asynctear"))
        or _is_fixture(m)
    ]
    reached: list[ast.AST] = []
    seen: set[str] = set()
    todo = [method]
    while todo:
        for used in _used(todo.pop()):
            parts = used.split(".")
            if (
                len(parts) > 1
                and parts[0] in ("self", "cls")
                and parts[1] in helpers
                and parts[1] not in seen
            ):
                seen.add(parts[1])
                reached.append(helpers[parts[1]])
                todo.append(helpers[parts[1]])
    plain = [m for m in cls.body if not isinstance(m, _FUNCS) and not _is_declaration_doc(m)]
    return (*cls.decorator_list, *cls.bases, *plain, *always, *reached)


def _units_of_tests(mod: _Module) -> dict[str, tuple[ast.AST, tuple[ast.AST, ...]]]:
    """key -> (node, extras): `name` for a top-level test function (plain or async), `Class::name` for a method of a
    top-level test class. A test function or method is one whose name starts with `test` (pytest's default), and a
    test class is one whose name starts with `Test` or that is a `unittest.TestCase`. The extras of a method are
    those of `_class_extras` (a class-level `pytestmark` or `@pytest.mark.skip` switches every method off)."""
    out: dict[str, tuple[ast.AST, tuple[ast.AST, ...]]] = {}
    for n in mod.tree.body:
        if isinstance(n, _FUNCS) and n.name.startswith("test"):
            out[n.name] = (n, ())
        elif isinstance(n, ast.ClassDef) and _is_test_class(n):
            for m in n.body:
                if isinstance(m, _FUNCS) and m.name.startswith("test"):
                    out[f"{n.name}::{m.name}"] = (m, _class_extras(n, m))
    return out


def _is_declaration_doc(n: ast.stmt) -> bool:
    return (
        isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Constant)
        and isinstance(n.value.value, str)
    )


def _units_of_functions(mod: _Module) -> dict[str, tuple[ast.AST, tuple[ast.AST, ...]]]:
    """key -> (node, extras) for every top-level function or class of a conftest, and for every name that a module-level
    assignment of a conftest binds (`pytest_plugins`, `collect_ignore`, a constant): all assignments of one name are
    one unit."""
    out: dict[str, tuple[ast.AST, tuple[ast.AST, ...]]] = {
        n.name: (n, ()) for n in mod.tree.body if isinstance(n, (*_FUNCS, ast.ClassDef))
    }
    if (
        mod.glue
    ):  # the module code that runs when the conftest is read: `for`, `if`, `try`, calls, subscripts
        out[CONFTEST_CODE] = (ast.Module(body=list(mod.glue), type_ignores=[]), ())
    for n in mod.tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and _is_declaration(n):
            for name in sorted(_assigned_names(n)):
                if name not in out:
                    group = [
                        g
                        for g in mod.tree.body
                        if isinstance(g, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                        and name in _assigned_names(g)
                    ]
                    out[name] = (ast.Module(body=group, type_ignores=[]), ())
    return out


def _assigned_names(n: ast.stmt) -> set[str]:
    if isinstance(n, ast.Assign):
        return {name for t in n.targets for name in _target_names(t)}
    target = getattr(n, "target", None)
    return set(_target_names(target)) if target is not None else set()


def _reached(mod: _Module, names: set[str]) -> str:
    """The dump of everything a mutant call reaches in its own file: each module-level function, class, constant
    and import the call names, and what those use, to any depth (the helper that builds a search text is part of
    the mutant, not only the call that names it). The collect-time code of the file is not part of it."""
    seen: set[str] = set()
    todo = sorted(names)
    parts: list[str] = []
    while todo:
        name = todo.pop()
        if name in seen or name not in mod.dumps:
            continue
        seen.add(name)
        parts.append(f"|{name}={mod.dumps[name]}")
        todo += mod.children_of(name)
    return "".join(sorted(parts))


def _mutant_units(mod: _Module) -> dict[str, str]:
    """name -> dump, for every `mutant(...)` or `Mutant(...)` call with a text as first argument, in the whole file
    (the dumps of the same name are joined). The dump of the builder function `mutant` is part of every one: a change
    of the builder changes what every mutant is; so is a change of a helper, constant or import of the same file
    that the call names (`_date_call(...)`, `KINDS_DECIDED_LINE`), to any depth."""
    builder = "".join(
        ast.dump(n) for n in mod.tree.body if isinstance(n, _FUNCS) and n.name in _MUTANT_CALLS
    )
    out: dict[str, str] = {}
    for n in ast.walk(mod.tree):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in _MUTANT_CALLS
            and n.args
            and isinstance(n.args[0], ast.Constant)
            and isinstance(n.args[0].value, str)
        ):
            out[n.args[0].value] = (
                out.get(n.args[0].value, "")
                + ast.dump(n)
                + _reached(mod, _used(n) - set(_MUTANT_CALLS))
            )
    return {k: v + "|" + builder for k, v in out.items()}


_TEST_FILE = re.compile(
    r"tests/(?:.+/)?(?:test_[^/]*|[^/]*_test)\.py"
)  # pytest's default file patterns
_MUTANT_FILE = re.compile(r"tests/(?:policy_mutants|stage_mutants)\.py")
_CONFTEST = re.compile(
    r"(?:tests/(?:.+/)?)?conftest\.py"
)  # also the one at the root of the repository
_FIXTURE_FILE = re.compile(r"tests/fixtures/policy_sources_[^/]*\.txt")
_CONFIG_FILE = re.compile(r"(?:pyproject\.toml|pytest\.ini|tox\.ini|setup\.cfg)")
_DATA_FILE = re.compile(
    r"tests/(?!.*__pycache__).+"
)  # any other file under tests/ (data, a plugin file, a script)
_NOTES_FILE = re.compile(r"handover/evidence/.+/NOTES\.md")


def kind_of(rel: str) -> str | None:
    """'test', 'mutants', 'conftest', 'fixture', 'config' (the pytest settings of the repository) or 'data' (any
    other file under tests/ that is not Python), or None for a file outside these kinds."""
    if _TEST_FILE.fullmatch(rel):
        return "test"
    if _MUTANT_FILE.fullmatch(rel):
        return "mutants"
    if _CONFTEST.fullmatch(rel):
        return "conftest"
    if _FIXTURE_FILE.fullmatch(rel):
        return "fixture"
    if _CONFIG_FILE.fullmatch(rel):
        return "config"
    if _DATA_FILE.fullmatch(rel) and not rel.endswith(".py"):
        return "data"
    return None


def _config_signature(rel: str, source: str) -> str:
    """What of a pytest settings file can change a test run: all of `pytest.ini`, `tox.ini` and `setup.cfg` (one
    text), and of `pyproject.toml` the `[tool.pytest]` tables only (a change of a dependency is no test change)."""
    if rel.endswith("pyproject.toml"):
        try:
            data = tomllib.loads(source)
        except tomllib.TOMLDecodeError:
            return source  # a file that does not parse is read whole: a change of it is a change
        return repr(data.get("tool", {}).get("pytest", {}))
    return source


def units_of(rel: str, source: str, loader: Loader | None = None) -> dict[str, str]:
    """key -> a signature, for the file `rel` with text `source`; `loader` gives the text of another file in the
    same state (to follow imports). An empty source has no units, and nor has a file that does not parse (a
    broken file is caught by the test run)."""
    if not source:
        return {}
    kind = kind_of(rel) or "test"
    if kind in ("fixture", "data"):
        return {Path(rel).name: source}
    if kind == "config":
        return {Path(rel).name: _config_signature(rel, source)}
    sigs = _Signatures(loader)
    mod = sigs.module(rel, source)
    if mod is None:
        return {}
    if kind == "mutants":
        return _mutant_units(mod)
    nodes = _units_of_tests(mod) if kind == "test" else _units_of_functions(mod)
    return {
        key: sigs.closure(mod, node, key.split("::")[-1], extra)
        for key, (node, extra) in nodes.items()
    }


def tests_of(
    source: str, rel: str = "tests/test_x.py", loader: Loader | None = None
) -> dict[str, str]:
    """key -> a signature of the test: the dump of the test itself and of everything it uses (see the module
    docstring), to any depth."""
    return units_of(rel, source, loader)


def changed_tests(
    old: str,
    new: str,
    rel: str = "tests/test_x.py",
    old_loader: Loader | None = None,
    new_loader: Loader | None = None,
) -> tuple[list[str], list[str]]:
    """(new or changed unit keys, keys that existed before and are gone), each sorted."""
    before = units_of(rel, old, old_loader)
    after = units_of(rel, new, new_loader)
    changed = sorted(n for n, d in after.items() if before.get(n) != d)
    gone = sorted(set(before) - set(after))
    return changed, gone


# ----------------------------------------------------------------------------------------------- the notes


def reason_problem(reason: str) -> str:
    """'' when the reason cell is a real reason, else why not."""
    if reason.strip(" .").lower() in PLACEHOLDERS or len(reason.split()) < MIN_WORDS:
        return f"the reason `{reason}` is a placeholder or has fewer than {MIN_WORDS} words"
    found = _MARKER.search(reason)
    if found is None:
        return (
            f"the reason `{reason[:60]}` names no killing mutant, failing run on the old code, "
            "plant or control reason (as whole words)"
        )
    if not _IDENTIFIER.search(reason[found.end() :]):
        return (
            f"the reason `{reason[:60]}` gives nothing to look up after `{found.group(0)}` (a mutant code or "
            "name, a test name, a log file name or a commit id)"
        )
    return ""


_TEST_NAME = re.compile(r"\btest_\w+")
_LOG_NAME = re.compile(
    r"[\w./-]+\.log\b"
)  # a bare name, or a path that ends at the file (`b12/logs/x.log`)
_MUTANT_CODE = re.compile(r"(?:[A-Z]{1,3}|[a-z])\d+[a-z]?\s|PROBE\s")
_COMMAND_WORDS = frozenset(
    {"python", "uv", "git", "pytest", "ruff", "bandit", "pip", "sh", "bash", "gitleaks"}
)


def _looks_like_a_mutant_name(token: str, leads: frozenset[str] = frozenset()) -> bool:
    """True for a backticked text that claims to be the name of a mutant: it starts with a mutant code and a space
    (`B12 `, `m6 `, `PROBE `), or it has two words or more and its first word is the first word of a mutant of the
    tree (`Kinds:`, `Dated`, `Ids:`: the names of the mutants that carry no code). A text that starts with another
    word is read as a quote (a message of a test, a path, a command), not as a name: a quote is never checked
    against the mutants. The limit is on purpose: a wrong name whose first word is no first word of any mutant and
    that carries no code is not found."""
    words = token.split()
    if len(words) < 2 or words[0].lower() in _COMMAND_WORDS:
        return False
    if re.search(r"[/\\=()\[\]{}<>*$#@|]|--|\.py\b|\.log\b|\.md\b", token):
        return False
    return bool(_MUTANT_CODE.match(token)) or words[0] in leads


class Refs:
    """What a reason may point at, read from the head commit: the names of the tests, the names of the mutants and
    the file names under a `logs/` folder. A reason that names one that is not there is a problem (a lookup that
    leads nowhere is no reason)."""

    def __init__(
        self,
        tests: frozenset[str],
        mutants: frozenset[str],
        logs: frozenset[str],
        units: dict[str, frozenset[str]] | None = None,
    ):
        """`logs` holds the paths of the files under a `logs/` folder (`handover/evidence/x/b1/logs/a.log`), `units`
        the unit names of each file in scope of the tree (to check that a row names a unit that exists)."""
        self.tests, self.mutants, self.logs = tests, mutants, logs
        self.units = units or {}


def reference_problems(reason: str, refs: Refs, folder: str | None = None) -> list[str]:
    """One line per name in the reason (after its marker) that does not exist: a `test_x` that is no test of the tree,
    a `x.log` that is in no `logs/` folder, a backticked mutant name (it starts with a mutant code such as `B12 `)
    that is no mutant of the mutant files (a text that `_looks_like_a_mutant_name` reads as a name: a mutant code, or
    the first word of a mutant of the tree). A log is looked up in the `logs/` folder of the notes file that names it
    (`folder`, the folder of that notes file); with no folder, in any `logs/` folder; a log written with a folder part
    (`b12/logs/x.log`) is found by the end of its path, in any notes folder."""
    found = _MARKER.search(reason)
    tail = reason[found.start() :] if found else reason
    out = []
    leads = frozenset(name.split()[0] for name in refs.mutants if name.split())
    for token in re.findall(r"`([^`]+)`", tail):
        if _looks_like_a_mutant_name(token, leads) and token not in refs.mutants:
            out.append(f"the mutant `{token}` is in no mutant file")
    bare = re.sub(r"`[^`]+`", " ", tail)
    ticked = " ".join(re.findall(r"`([^`]+)`", tail))
    for name in sorted(set(_TEST_NAME.findall(f"{bare} {ticked}"))):
        if name not in refs.tests:
            out.append(f"the test {name} is in no test file")
    for name in sorted(set(_LOG_NAME.findall(f"{bare} {ticked}"))):
        if "/" in name:  # written as a path: it must end a path of a `logs/` folder of the tree
            here = any(path == name or path.endswith("/" + name) for path in refs.logs)
        elif folder is None:
            here = any(path.rsplit("/", 1)[-1] == name for path in refs.logs)
        else:
            here = f"{folder}/logs/{name}" in refs.logs
        if not here:
            out.append(
                f"the log file {name} is in no logs/ folder"
                + (f" of {folder}" if folder is not None else "")
            )
    return out


def _cell_names(cell: str, name: str) -> bool:
    """True when `name` is the whole cell or one item of the cell when it is split at `;` (never a part of one). An
    item that is only a backticked text is read without its backticks; a name that holds a backtick is compared as
    written."""

    def same(item: str) -> bool:
        item = item.strip()
        wrapped = item.startswith("`") and item.endswith("`") and item.count("`") == 2
        return name in (item, item[1:-1] if wrapped else item)

    return same(cell) or any(same(i) for i in cell.split(";"))


_FOLDER_MARK = "\x00notes-folder:"  # a line `main` puts before the text of each notes file: the folder it is in


def rows_of(notes: str) -> list[tuple[str, list[str], str, str, str | None]]:
    """One entry per table row with at least three cells whose first cell names a file (a name ending in an
    extension) and whose second cell holds ids in backticks: (file cell, the ids in backticks of the second cell,
    the reason cell (the last cell), the second cell, the folder of the notes file the row is in or None)."""
    out = []
    folder: str | None = None
    for line in notes.splitlines():
        if line.startswith(_FOLDER_MARK):
            folder = line[len(_FOLDER_MARK) :] or None
            continue
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        file_cell = cells[0].strip("`").strip()
        if not re.search(r"\.\w+$", file_cell):
            continue
        out.append((file_cell, re.findall(r"`([^`]+)`", cells[1]), cells[-1], cells[1], folder))
    return out


def _row_names_a_unit(cell: str, names: list[str], units: frozenset[str]) -> bool:
    """True when the second cell of a row names a unit: the whole cell, one `;` item of it (a backticked item is read
    without its backticks), or, when the cell holds backticked ids, every one of them."""
    for item in (cell, *cell.split(";")):
        item = item.strip()
        wrapped = item.startswith("`") and item.endswith("`") and item.count("`") == 2
        if item in units or (wrapped and item[1:-1] in units):
            return True
    return bool(names) and all(n in units for n in names)


def stale_row_problems(notes: str, refs: Refs, known: frozenset[str] | None = None) -> list[str]:
    """One line for each table row whose first cell is a file of the tree in scope and whose second cell names no unit
    of that file (a mutant or test that does not exist, a typo, a name that was renamed): a row that names nothing
    is no row. A row whose file is not in scope or not found, or a bare file name that two files share, is not
    judged."""
    out = []
    for file_cell, names, _, cell, folder in rows_of(notes):
        files = [rel for rel in refs.units if _file_matches(file_cell, rel, known)]
        if len(files) != 1:
            continue
        if not _row_names_a_unit(cell, names, refs.units[files[0]]):
            where = f" (notes of {folder})" if folder else ""
            out.append(
                f"{files[0]}: a row of the notes{where} names `{cell[:90]}`, which is no test, mutant or unit "
                "of that file"
            )
    return sorted(set(out))


def _file_matches(file_cell: str, rel: str, known: frozenset[str] | None = None) -> bool:
    """True when the first cell of a row names the file `rel`: the whole path, or the end of it that starts at a path
    part. A cell that is a bare file name serves only when no other file of `known` (the paths of the tree) has that
    name: one row must never serve `tests/test_x.py` and `tests/contracts/test_x.py`."""
    if rel == file_cell:
        return True
    if not rel.endswith("/" + file_cell):
        return False
    if "/" in file_cell or not known:
        return True
    return not any(k != rel and k.rsplit("/", 1)[-1] == file_cell for k in known)


def problems(
    changed: list[str],
    gone: list[str],
    notes: str,
    label: str,
    counts: tuple[int, int] | None = None,
    known: frozenset[str] | None = None,
    refs: Refs | None = None,
) -> list[str]:
    """One line per problem for the file `label`: a changed unit with no row (file and id from the first two
    cells) or with a bad reason, and a unit that is gone. `counts` (units before, units now) is given for a file of
    mutants: a count that fell is a problem of its own. `known` holds the paths of the tree (a bare file name in a row
    counts only when no other path has it). `refs` (the names of the tests, the mutants and the logs of the tree) is
    given to check that a reason points at something that exists."""
    rows: dict[str, tuple[str, str, str | None]] = {}
    for file_cell, names, reason, cell, folder in rows_of(notes):
        if _file_matches(file_cell, label, known):
            # the whole cell is a key too: the names of two mutants that hold the same backticked word each keep
            # their own row (the backticked word alone would be one key); the last row wins
            for name in (*names, cell):
                rows[name] = (reason, cell, folder)
    word = "mutant" if kind_of(label) == "mutants" else "test"
    out = []
    for n in changed:
        found = rows.get(n)
        if (
            found is None and word == "mutant"
        ):  # a name with a backtick in it cannot be written in backticks
            found = next((v for v in rows.values() if _cell_names(v[1], n)), None)
        if found is None:
            out.append(
                f"{label}: the {word} {n} is new or changed and has no row of its own in the notes"
            )
            continue
        why = reason_problem(found[0])
        if why:
            out.append(f"{label}: the {word} {n} has a row but {why}")
        elif refs is not None:
            out += [
                f"{label}: the {word} {n} has a row whose reason points at nothing: {line}"
                for line in reference_problems(found[0], refs, found[2])
            ]
    out += [
        f"{label}: the {word} {n} existed in the base commit and is gone (never delete a {word})"
        for n in gone
    ]
    if counts is not None and counts[1] < counts[0]:
        out.append(f"{label}: the mutant count fell from {counts[0]} to {counts[1]}")
    return out


# ----------------------------------------------------------------------------------------------- git


def _git(*args: str) -> subprocess.CompletedProcess:
    git = shutil.which("git")
    if git is None:
        raise SystemExit("git was not found")
    return subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git, *args], capture_output=True, text=True, errors="replace", check=False
    )


def base_resolves(base: str) -> bool:
    """True when `base` names a commit (a mistyped base would make every test look new)."""
    return _git("rev-parse", "--verify", "--quiet", f"{base}^{{commit}}").returncode == 0


def _show(rev: str, rel: str) -> str:
    proc = _git("show", f"{rev}:{rel}")
    return proc.stdout if proc.returncode == 0 else ""  # a file new since the base has no old text


def _tree(rev: str) -> list[str]:
    """Every path of the commit `rev` ([] when git cannot list it)."""
    proc = _git("ls-tree", "-r", "--name-only", "-z", rev)
    return [n for n in proc.stdout.split("\0") if n] if proc.returncode == 0 else []


def _refs(tree: list[str], load: Loader) -> Refs:
    """The test names, the mutant names and the log file names of the tree (the text of each file as `load` gives it)."""
    tests: set[str] = set()
    mutants: set[str] = set()
    units: dict[str, frozenset[str]] = {}
    for rel in tree:
        kind = kind_of(rel)
        if kind is not None:
            units[rel] = frozenset(_unit_names(rel, kind, load(rel)))
        if kind == "test":
            tests.update(
                re.findall(r"^[ \t]*(?:async[ \t]+)?def[ \t]+(test_\w+)", load(rel), re.MULTILINE)
            )
            # the name of a test file (`test_policy_guard`) names a file, not a test: a reason may say it
            tests.add(rel.rsplit("/", 1)[-1].removesuffix(".py"))
        elif kind == "mutants":
            mutants.update(units[rel])
    logs = {rel for rel in tree if "/logs/" in rel}
    return Refs(frozenset(tests), frozenset(mutants), frozenset(logs), units)


def _unit_names(rel: str, kind: str, source: str) -> list[str]:
    """The names of the units of a file in scope, without the signatures (cheap): see `units_of`."""
    if not source:
        return []
    if kind in ("fixture", "data", "config"):
        return [Path(rel).name]
    try:
        mod = _Module(rel, source)
    except SyntaxError:
        return []
    if kind == "mutants":
        return list(_mutant_units(mod))
    return list(_units_of_tests(mod) if kind == "test" else _units_of_functions(mod))


def check(
    base: str, notes: str, files: list[str], head: str | None = None, cross: bool = False
) -> list[str]:
    """Every problem line for the files `files` against `base`; a file missing now counts as empty (its units
    are gone). With `head` the new text of every file (and of the test modules it imports) is the blob of that
    commit (`git show head:path`), else the file on disk."""
    if not base_resolves(base):
        return [f"the base commit {base!r} does not resolve: every test would look new"]
    if head is not None and not base_resolves(head):
        return [f"the head commit {head!r} does not resolve"]

    cache: dict[tuple[str, str], str] = {}

    def old_load(rel: str) -> str:
        if ("old", rel) not in cache:
            cache["old", rel] = _show(base, rel)
        return cache["old", rel]

    def new_load(rel: str) -> str:
        if ("new", rel) not in cache:
            if head is not None:
                cache["new", rel] = _show(head, rel)
            else:
                path = Path(rel)
                cache["new", rel] = path.read_text(encoding="utf-8") if path.is_file() else ""
        return cache["new", rel]

    tree = _tree(head or "HEAD")
    old_load.files = _tree(base)  # type: ignore[attr-defined]
    new_load.files = tree  # type: ignore[attr-defined]
    known = frozenset([*files, *tree])
    refs = _refs(tree, new_load) if cross else None
    bad: list[str] = []
    for rel in files:
        old, now = old_load(rel), new_load(rel)
        changed, gone = changed_tests(old, now, rel, old_load, new_load)
        counts = None
        if kind_of(rel) == "mutants":
            counts = (len(units_of(rel, old, old_load)), len(units_of(rel, now, new_load)))
        bad += problems(changed, gone, notes, rel, counts, known, refs)
    if refs is not None:
        bad += stale_row_problems(notes, refs, known)
    return bad


def auto_files(
    base: str, head: str = "HEAD"
) -> tuple[str, str, list[str], list[str], list[str]] | str:
    """(merge-base, head commit, changed files in scope, notes files present at head, every changed path) of the
    change, or ONE problem line
    when git cannot give it (the base or head does not resolve, there is no common ancestor, or `diff` fails: a
    failure is never read as "nothing changed"). The change is `git diff --no-renames merge-base head`."""
    if not base_resolves(base):
        return f"the base commit {base!r} does not resolve: every test would look new"
    if not base_resolves(head):
        return f"the head commit {head!r} does not resolve"
    sha = _git("rev-parse", head)
    merged = _git("merge-base", base, head)
    if sha.returncode != 0 or merged.returncode != 0 or not merged.stdout.strip():
        return (
            f"git found no common ancestor of {base!r} and {head!r} (a shallow checkout: fetch the full "
            "history, `fetch-depth: 0`)"
        )
    mb, head_sha = merged.stdout.strip(), sha.stdout.strip()
    diff = _git("diff", "--name-only", "--no-renames", "-z", mb, head_sha)
    if diff.returncode != 0:
        return (
            f"`git diff {mb[:12]} {head_sha[:12]}` failed (exit {diff.returncode}): "
            f"{diff.stderr.strip()[:200]}"
        )
    names = [n for n in diff.stdout.split("\0") if n]
    return (
        mb,
        head_sha,
        [n for n in names if kind_of(n)],
        sorted(n for n in names if _NOTES_FILE.fullmatch(n) and _show(head_sha, n)),
        names,
    )


def main(argv: list[str]) -> int:
    if argv[:1] == ["--auto"] and len(argv) in (2, 4) and (len(argv) == 2 or argv[2] == "--head"):
        found = auto_files(argv[1], argv[3] if len(argv) == 4 else "HEAD")
        if isinstance(found, str):
            print(found)
            return 1
        mb, head_sha, files, notes_files, names = found
        if not files and not any(n.startswith("tests/") for n in names):
            print(
                "no test file changed in this change (and no mutant file, conftest, pytest setting or "
                "file under tests/ either): nothing to check"
            )
            return 0
        # a change to a helper (a file under tests/ that is not a test file) lists the tests that import it, so every
        # test file of the head commit is read, not only the changed ones: the answer for a file that did not change
        # and imports nothing that changed is "no change"
        files = sorted({*files, *(n for n in _tree(head_sha) if kind_of(n) == "test")})
        notes = "\n".join(
            f"{_FOLDER_MARK}{n.rsplit('/', 1)[0]}\n{_show(head_sha, n)}" for n in notes_files
        )
        bad = check(mb, notes, files, head_sha, cross=True)
        if bad and not notes_files:
            bad.insert(0, "the change has no builder notes file (handover/evidence/**/NOTES.md)")
    elif len(argv) >= 3 and not argv[0].startswith("-"):
        notes = Path(argv[1]).read_text(encoding="utf-8")
        bad = check(argv[0], notes, argv[2:])
    else:
        print(
            "usage: notes_lines_check.py <base-commit> <notes.md> <file> [...]\n"
            "       notes_lines_check.py --auto <base-commit> [--head <commit>]",
            file=sys.stderr,
        )
        return 2
    for line in bad:
        print(line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
