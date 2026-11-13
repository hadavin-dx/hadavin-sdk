"""List the tests (and the files that make tests pass or fail) that are new or changed against a base commit and check
that a builder's notes hold a row for each.

    python tools/notes_lines_check.py <base-commit> <notes.md> <file> [<file> ...]
    python tools/notes_lines_check.py --auto <base-commit> [--head <commit>]

The one rule: a change of a file under `tests/` lists every test unless the check proves that nothing can reach that
file. Wherever it meets something it cannot read (a module name worked out at run time, a path it cannot work out, a
file that does not parse, a base class it cannot find ...) it records a reason through ONE collector,
`unresolved_edge`; with one reason or more in the tests tree, a change of any file under `tests/` lists every test
(the first five reasons are printed). Only a file that no code can read (`.md`, `.rst`) is exempt. The resolver
follows an alias of an alias (`imp = importlib.import_module`, then `imp2 = imp`) for at most 8 passes; a longer
chain of aliases is not followed.

What it reads. In each test file it reads every `test_*` function (plain or `async`; also one assigned as
`test_x = factory()`, or defined under an `if`, `try`, `with` or `match`) and every `test_*` method, also an inherited
one and one of a nested class, of a class whose name starts with `Test` or that has any base class other than `object`
(it may be a `unittest.TestCase` through its base: named `Class::test_x`).
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
- the code of every `conftest.py` above the test file (each top-level function and class and each module-level
  statement of it), the `__init__.py` of every package folder on the way, and the text of every module a
  `pytest_plugins` list names (in any form: `=`, `+=`, `.append`) or a `-p name` in `addopts` of a settings file
  loads (they act on every test). Every function of a conftest whose name starts with `pytest_` (a hook) acts on
  every test below it, and so do the other 14 names a test file or conftest can use to switch tests on or off:
  `__test__`, `setup_module`, `teardown_module`, `setUpModule`, `tearDownModule`, `setup_function`,
  `teardown_function`, `pytest_generate_tests`, `pytest_collection_modifyitems`, `pytest_configure`,
  `pytest_runtest_setup`, `pytest_plugins`, `collect_ignore` and `collect_ignore_glob`;
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
file name. The pytest settings of the repository (`pytest.ini`, `.pytest.ini`, `pytest.toml`, `tox.ini`, `setup.cfg`, and the `[tool.pytest]`
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
`tests/`: a test written another way (generated at run time, or collected by a plugin that is installed as a
package and found through its entry point), a change in `src/` or `tools/` that a test uses (those have their own
mutants), a change to a file outside the kinds above (a workflow, a lock file, an environment variable of the test
run such as `PYTEST_ADDOPTS`, a `-p` plugin named only on the command line) and a dependency version are not seen.
A module loaded from a path (`runpy.run_path`, `importlib.util.spec_from_file_location`) is followed when the path
can be worked out from `__file__`, `Path`, `/` and texts; `getattr` on a module of `tests` with a name that is no
text, `exec`, and a path that cannot be read are unresolved edges. A fixture whose name is built at run time
(`request.getfixturevalue(name)`, `usefixtures(*names)`, `parametrize(names, indirect=True)`, `lazy_fixture`) is read as
every fixture the file and the conftests above it hold; `@pytest.fixture(name="alias")` is the name `alias`. A
file that imports with `importlib`, `pkgutil` or `__import__` is read as reaching the modules it names as text and
every Python file below each package folder it imports from; a module name built at run time (`import_module(f"tests.x.
dyn_{n}")`) reaches every Python file whose dotted name starts with the text the name starts with, and a name that starts
with a value (`import_module(name)`, or no name at all) reaches every Python file under `tests` (the one rule: a name
that cannot be read lists every test of the file); a name that starts with the `__name__` of a package of `tests` that
the file imports is the exception, it is that package's folder. The name is the first argument or `name=`, and
another name of the function (`imp = importlib.import_module`, `from importlib import import_module as imp`) is the
same call; the function handed on as a value (`map(import_module, names)`) is a call with a name that cannot be read. The notes files of the change are read
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
import hashlib
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

MIN_WORDS = 4  # words of the reason cell
CONFTEST_CODE = "conftest module code"  # the unit that holds every top-level statement of a conftest that is no name
ALLOWED_SUFFIXES = (
    ".md",
    ".rst",
)  # a file under tests/ no code reads: the only exemption of a changed file
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


def unresolved_edge(sink: list[str], reason: str) -> None:
    """The ONE collector of the places where the check meets something it cannot read (an import by a name worked
    out at run time, a file that does not parse, a plugin it cannot name ...). Each such place calls this with a
    reason; one reason or more makes the check list EVERY test whenever a file under `tests/` changes (see
    `_Signatures.closure`): the check must never silently reach nothing."""
    if reason not in sink:
        sink.append(reason)


def _autouse_keyword(call: ast.Call) -> bool:
    """True when a `fixture(...)` call may switch autouse on: any `autouse=` value that is not the constant False or
    None (`True`, `1`, a name such as `AUTO`, an expression) is read as on."""
    return any(
        k.arg == "autouse"
        and not (isinstance(k.value, ast.Constant) and k.value.value in (False, None))
        for k in call.keywords
    )


def _is_autouse(fn: ast.AST) -> bool:
    """True for a function decorated `@pytest.fixture(..., autouse=<anything but False>, ...)` (or `@fixture(...)`)."""
    for d in getattr(fn, "decorator_list", []):
        if isinstance(d, ast.Call):
            callee = d.func.attr if isinstance(d.func, ast.Attribute) else getattr(d.func, "id", "")
            if callee == "fixture" and _autouse_keyword(d):
                return True
    return False


def _autouse_calls(tree: ast.AST) -> list[str]:
    """The names an assignment gives to a fixture made as `f = pytest.fixture(autouse=True)(_impl)`: the assigned
    name counts as an autouse fixture of the file (the function it wraps is reached through the assignment, so it
    needs no name of its own)."""
    out: list[str] = []
    for n in ast.walk(tree):
        if not isinstance(n, (ast.Assign, ast.AnnAssign)):
            continue
        call = n.value
        if (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Call)
            and _dotted(call.func.func)[-1:] == ["fixture"]
            and _autouse_keyword(call.func)
        ):
            if isinstance(n, ast.Assign):
                out += [name for t in n.targets for name in _target_names(t)]
            elif isinstance(n, ast.AnnAssign):
                out += _target_names(n.target)
    return out


def _path_parts(
    e: ast.AST | None,
    rel: str,
    values: dict[str, list[ast.AST]],
    depth: int = 0,
    lookup: Callable[[str], tuple[str, dict[str, list[ast.AST]], ast.AST] | None] | None = None,
) -> list[str] | None:
    """The folders and file of a path an expression builds, from the root of the repository, with `*` for a part that
    is worked out at run time (`Path(__file__).resolve().parents[2] / "demos" / f"{name}.py"` gives
    `demos`, `*.py`); None when the expression cannot be read."""
    if e is None or depth > 8:
        return None
    if isinstance(e, ast.Constant) and isinstance(e.value, str):
        return [p for p in e.value.split("/") if p]
    if isinstance(e, ast.JoinedStr):
        text = "".join(
            v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else "*"
            for v in e.values
        )
        return [p for p in text.split("/") if p]
    if isinstance(e, ast.Name):
        if e.id == "__file__":
            return rel.split("/")
        got = values.get(e.id, [])
        if len(got) == 1:
            return _path_parts(got[0], rel, values, depth + 1, lookup)
        far = (
            lookup(e.id) if lookup and not got else None
        )  # a name imported from another module of `tests`
        return _path_parts(far[2], far[0], far[1], depth + 1, lookup) if far else None
    if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Div):
        left = _path_parts(e.left, rel, values, depth + 1, lookup)
        right = _path_parts(e.right, rel, values, depth + 1, lookup)
        return None if left is None or right is None else [*left, *right]
    if isinstance(e, ast.Attribute) and e.attr == "parent":
        base = _path_parts(e.value, rel, values, depth + 1, lookup)
        return None if base is None else base[:-1]
    if (
        isinstance(e, ast.Subscript)
        and isinstance(e.value, ast.Attribute)
        and e.value.attr == "parents"
        and isinstance(e.slice, ast.Constant)
        and isinstance(e.slice.value, int)
    ):
        base = _path_parts(e.value.value, rel, values, depth + 1, lookup)
        cut = e.slice.value + 1
        return None if base is None or cut > len(base) else base[: len(base) - cut]
    if isinstance(e, ast.Call):
        callee = [_base_name(e.func)]
        if callee in (["resolve"], ["absolute"]) and isinstance(e.func, ast.Attribute):
            return _path_parts(e.func.value, rel, values, depth + 1, lookup)
        if callee in (["Path"], ["PurePath"], ["join"], ["joinpath"]) and e.args:
            parts: list[str] = []
            if callee == ["joinpath"] and isinstance(e.func, ast.Attribute):
                head = _path_parts(e.func.value, rel, values, depth + 1, lookup)
                if head is None:
                    return None
                parts = head
            for a in e.args:
                got_parts = _path_parts(a, rel, values, depth + 1, lookup)
                if got_parts is None:
                    return None
                parts += got_parts
            return parts
    return None


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


def _header_nodes(n: ast.AST) -> list[ast.AST]:
    """The parts of a function or class definition that run when the definition itself runs (the decorators, the
    default values, the annotations, the bases): a walrus in one of them binds a module name; the body does not."""
    out: list[ast.AST] = list(getattr(n, "decorator_list", []))
    if isinstance(n, ast.ClassDef):
        out += [*n.bases, *(k.value for k in n.keywords)]
    elif isinstance(n, _FUNCS):
        a = n.args
        out += [*a.defaults, *(d for d in a.kw_defaults if d is not None)]
        out += [x.annotation for x in (*a.posonlyargs, *a.args, *a.kwonlyargs) if x.annotation]
        out += [x for x in (n.returns,) if x is not None]
    return out


def _fixture_alias(fn: ast.AST) -> str | None:
    """The name a fixture is registered under when it is written `@pytest.fixture(name="alias")`, else None."""
    for d in getattr(fn, "decorator_list", []):
        if isinstance(d, ast.Call):
            callee = d.func.attr if isinstance(d.func, ast.Attribute) else getattr(d.func, "id", "")
            if callee == "fixture":
                for k in d.keywords:
                    if (
                        k.arg == "name"
                        and isinstance(k.value, ast.Constant)
                        and isinstance(k.value.value, str)
                    ):
                        return k.value.value
    return None


def _text_names(exprs: list[ast.AST]) -> set[str]:
    """The fixture names a call spells as texts; an argument that is no text (a variable, an f-string, `*names`)
    cannot be read, so the name `DYNAMIC_FIXTURE` stands for every fixture in reach."""
    out: set[str] = set()
    for e in exprs:
        if isinstance(e, ast.Constant):
            if isinstance(e.value, str):
                out.add(e.value)
        else:
            out.add(DYNAMIC_FIXTURE)
    return out


def _parametrize_names(call: ast.Call) -> set[str]:
    """The fixtures `parametrize("a,b", ..., indirect=True)` hands its values to: the argument names it spells (a
    text, or a list or tuple of texts). Names that are no test parameter are the same names a test already uses, so
    reading them without looking at `indirect` lists the same tests; names that cannot be read count only with
    `indirect` (without it they are plain parameters of the test)."""
    first = call.args[0] if call.args else None
    out: set[str] = set()
    readable = False
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        out |= {x.strip() for x in first.value.split(",") if x.strip()}
        readable = True
    elif isinstance(first, (ast.List, ast.Tuple)) and all(
        isinstance(e, ast.Constant) and isinstance(e.value, str) for e in first.elts
    ):
        out |= {e.value for e in first.elts if isinstance(e, ast.Constant)}
        readable = True
    if not readable and any(k.arg == "indirect" for k in call.keywords):
        out.add(DYNAMIC_FIXTURE)
    return out


def _stem(rel: str, level: int, module: str | None) -> str | None:
    """The path stem of the module an import names, or None when it is not under `tests`. `from tests.x import a`
    names tests/x; `from . import x` or `from .x import a` in tests/y.py names tests/x."""
    parts = module.split(".") if module else []
    if level:
        here = rel.split("/")[:-1]
        parts = [*(here[: len(here) - (level - 1)] if level > 1 else here), *parts]
    return "/".join(parts) if parts and parts[0] == "tests" else None


def _imports(
    tree: ast.AST,
    rel: str,
    sink: list[str] | None = None,
    bare: list[tuple[str, str, str | None]] | None = None,
) -> dict[str, tuple[str, str | None]]:
    """local name -> (path stem of a module under `tests`, the name taken from it or None for the module itself),
    for every import of the file that reaches such a module (module level or inside a function). A relative import
    that does not end under `tests` is an unresolved edge; an absolute import whose first name is no module under
    `tests` is listed in `bare` as (local name, dotted module, name taken) so the tree can tell whether it is a
    module next to the file (`from helpers import x`)."""
    out: dict[str, tuple[str, str | None]] = {}
    sink = sink if sink is not None else []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            stem = _stem(rel, n.level, n.module)
            if stem is not None:
                # a star import binds no name of its own: `_star_stems` reads it (every name of the module)
                out.update({a.asname or a.name: (stem, a.name) for a in n.names if a.name != "*"})
            elif n.level:
                unresolved_edge(sink, f"{rel}: a relative import that does not end under tests")
            elif bare is not None and n.module:
                bare += [(a.asname or a.name, n.module, a.name) for a in n.names if a.name != "*"]
        elif isinstance(n, ast.Import):
            for a in n.names:
                stem = _stem(rel, 0, a.name)
                if stem is not None:
                    # `import tests.x as y` binds y; `import tests.x` binds the dotted name `tests.x` (two such imports
                    # must not share the key `tests`)
                    out[a.asname or a.name] = (stem, None)
                elif bare is not None:
                    bare.append((a.asname or a.name, a.name, None))
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
DYNAMIC_IMPORTS = (
    ["import_module"],
    ["iter_modules"],
    ["walk_packages"],
    ["__import__"],
    ["importorskip"],
    ["find_spec"],
    ["run_module"],
)
# The loaders that take a PATH (not a module name): the path is worked out by `_path_parts`; a file under `tests` is
# reached, a path outside `tests` reaches nothing of it, a path that cannot be read is an unresolved edge.
PATH_LOADERS = (["spec_from_file_location"], ["run_path"])
# The calls that run a spec's code; the spec itself comes from `find_spec` or a path loader.
SPEC_MAKERS = (["find_spec"], ["spec_from_file_location"], ["spec_from_loader"])
EXEC_CALLS = (["exec_module"], ["load_module"])
# The options of `PYTEST_ADDOPTS` that can load code or change where tests are read from; any other option (a
# `--deselect`, `-q`) cannot make a file of `tests` run that did not run before.
LOADING_OPTIONS = (
    "-p",
    "-c",
    "-o",
    "--rootdir",
    "--confcutdir",
    "--import-mode",
    "--pyargs",
    "--override-ini",
)
ENV_CALLS = ("setenv", "delenv", "get", "setdefault", "putenv", "pop", "getenv", "unsetenv")
# The names a name-reading loader reads as the module name (the first argument or `name=`), and the position and
# keyword of the path of a path loader.
PATH_ARG = {"spec_from_file_location": (1, "location"), "run_path": (0, "path_name")}
# The calls that name a fixture as a text, not as a parameter.
FIXTURE_BY_TEXT = (["usefixtures"], ["getfixturevalue"], ["getfuncargvalue"])
# The plugin calls that name a fixture as a text (`lazy_fixture("x")`, the short form `lf("x")`) and the call that
# can name a fixture as the name of a parameter (`parametrize("x", ..., indirect=True)`).
LAZY_FIXTURES = (["lazy_fixture"], ["lf"])
PARAMETRIZE = ["parametrize"]
# The name a fixture text that cannot be read stands for: every fixture the file and the conftests above it hold
# (`request.getfixturevalue(f"fx_{n}")`, `request.getfixturevalue(name)`, `usefixtures(*names)`).
DYNAMIC_FIXTURE = "<a fixture named at run time>"


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
                # `def f(a=(X := 1))` and `@(D := deco)` bind X and D at module level
                for header in _header_nodes(n):
                    bound = _walrus_names(header)
                    self._value(bound, header)
                    names += bound
                alias = _fixture_alias(n)
                if alias:
                    names.append(alias)
                    self.nodes[alias] = n
            elif isinstance(n, ast.Assign) and _is_declaration(n):
                names = [name for t in n.targets for name in _target_names(t)]
                self._value(names, n.value)
                names += _walrus_names(n.value)
                self._value(
                    _walrus_names(n.value), n.value
                )  # a name a walrus binds is built from the same value
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and _is_declaration(n):
                # `X += ...` changes what X is, so it is joined to the dump of X
                names = _target_names(n.target)
                if n.value is not None:
                    self._value(names, n.value)
                    names += _walrus_names(n.value)
                    self._value(_walrus_names(n.value), n.value)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                names = [_bound(a) for a in n.names]
            else:
                continue
            for name in names:
                self.dumps[name] = self.dumps.get(name, "") + ast.dump(n)
        self.source = source
        # every place where something cannot be read is one entry here (`unresolved_edge`)
        self.unresolved: list[str] = []
        self.bare: list[tuple[str, str, str | None]] = []
        self.imports = _imports(self.tree, rel, self.unresolved, self.bare)
        self.stars = _star_stems(self.tree, rel)
        # the modules a `pytest_plugins` list names (a text): pytest imports them, so each acts on every test
        # under the folder of the conftest like the conftest itself. Every form is read: `=`, an annotated `=`,
        # `+=`, `.append(...)`, `.extend([...])`, at any depth; a value that is no text or list of texts is an
        # unresolved edge
        self.plugin_names: list[str] = []
        for n in ast.walk(self.tree):
            if (
                isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                and "pytest_plugins" in _assigned_names(n)
                and n.value is not None
            ):
                value = n.value
            elif (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and _dotted(n.func.value) == ["pytest_plugins"]
                and n.func.attr in ("append", "extend", "insert")
            ):
                value = ast.Tuple(elts=list(n.args), ctx=ast.Load())
            else:
                continue
            texts = [
                c
                for c in ast.walk(value)
                if isinstance(c, ast.Constant) and isinstance(c.value, str)
            ]
            readable = all(
                isinstance(x, (ast.Constant, ast.List, ast.Tuple, ast.Load, ast.BinOp, ast.Add))
                for x in ast.walk(value)
            )
            if not readable:
                unresolved_edge(
                    self.unresolved,
                    f"{rel}: pytest_plugins is built by an expression it cannot read",
                )
            self.plugin_names += [c.value for c in texts]
        covered: set[int] = set()
        for n in ast.walk(self.tree):
            # `env["PYTEST_ADDOPTS"] = value`: read when the value has only text and the options that load no code
            if (
                isinstance(n, ast.Assign)
                and isinstance(n.targets[0], ast.Subscript)
                and isinstance(n.targets[0].slice, ast.Constant)
                and n.targets[0].slice.value == "PYTEST_ADDOPTS"
            ):
                words = " ".join(
                    c.value
                    for c in ast.walk(n.value)
                    if isinstance(c, ast.Constant) and isinstance(c.value, str)
                ).split()
                if words and not any(w.startswith(LOADING_OPTIONS) for w in words):
                    covered.add(id(n.targets[0].slice))
        for n in ast.walk(self.tree):
            # the environment variable that adds pytest options (a plugin) to a run: its value is not in the tree
            used = (
                (isinstance(n, ast.Subscript) and n.slice)
                or (
                    isinstance(n, ast.Call)
                    and n.func
                    and _base_name(n.func) in ENV_CALLS
                    and n.args
                    and n.args[0]
                )
                or None
            )
            keys = [used] if used is not None else []
            if isinstance(n, ast.Dict):
                keys += [k for k in n.keys if k is not None]
            for k in keys:
                if (
                    isinstance(k, ast.Constant)
                    and k.value == "PYTEST_ADDOPTS"
                    and id(k) not in covered
                ):
                    unresolved_edge(
                        self.unresolved,
                        f"{rel}: PYTEST_ADDOPTS is used, its options are not in the tree",
                    )
            # a fixture named by a value, or a parametrize with `indirect` and names it cannot read
            if isinstance(n, ast.Call):
                last = _dotted(n.func)[-1:]
                if last in (*FIXTURE_BY_TEXT, *LAZY_FIXTURES) and any(
                    not (isinstance(a, ast.Constant) and isinstance(a.value, str))
                    for a in [*n.args, *(k.value for k in n.keywords)]
                ):
                    unresolved_edge(
                        self.unresolved, f"{rel}: a fixture is named by a value it cannot read"
                    )
                elif last == PARAMETRIZE and DYNAMIC_FIXTURE in _parametrize_names(n):
                    unresolved_edge(
                        self.unresolved,
                        f"{rel}: parametrize with indirect and names it cannot read",
                    )
                elif last == ["getattr"] and len(n.args) >= 2:
                    # getattr on a module of `tests` with a name that is no text reaches a member it cannot name
                    first = _dotted(n.args[0])
                    if (
                        first
                        and first[0] in self.imports
                        and not (
                            isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str)
                        )
                    ):
                        unresolved_edge(
                            self.unresolved,
                            f"{rel}: getattr on a module of tests with a name it cannot read",
                        )
        self.autouse = [
            n.name for n in _block_nodes(self.tree.body) if isinstance(n, _FUNCS) and _is_autouse(n)
        ]
        self.autouse += [x for x in _autouse_calls(self.tree) if x not in self.autouse]
        # module-level statements that bind nothing the table above knows (`if`, `try`, `for`, `with`, a call such
        # as `pytest.skip(allow_module_level=True)` or `collect_ignore.append(...)`, an assignment to a subscript
        # or an attribute): code that runs when the file is collected and can switch every test of it off or on,
        # so it is part of every unit of the file
        self.glue = [n for n in self.tree.body if not _is_declaration(n)]
        self.glue_dump = "".join(ast.dump(n) for n in self.glue)
        # modules that the file imports by a name worked out at run time (`importlib.import_module(...)`,
        # `pkgutil.iter_modules(...)`, `__import__(...)`, `pytest.importorskip(...)`, a spec ...): see
        # `_Signatures.closure`
        self.dynamic = False
        self.dynamic_names: list[str] = []  # the dotted names written as text in such a call
        # a name built at run time (`import_module(f"tests.x.dyn_{n}")`, `import_module("tests.x." + n)`): the text it
        # starts with ("tests.x.dyn_"), or "" when it starts with a value (`import_module(name)`)
        self.dynamic_prefixes: list[str] = []
        self.path_args: list[ast.AST | None] = []  # the path expression of each path loader call
        self.package_names: list[
            str
        ] = []  # packages of `tests` a name starts with (`pkg.__name__ + "." + x`)
        aliases = _dynamic_aliases(self.tree)
        called = {id(n.func) for n in ast.walk(self.tree) if isinstance(n, ast.Call)}
        # the right side of `imp = importlib.import_module` only gives the function another name: no call, no hand-on
        called |= {
            id(n.value)
            for n in ast.walk(self.tree)
            if isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
            and n.value is not None
            and isinstance(n.value, (ast.Name, ast.Attribute))
        }
        calls = [
            (n, _callee(n.func, aliases)) for n in ast.walk(self.tree) if isinstance(n, ast.Call)
        ]
        makes_spec = any(c in SPEC_MAKERS or c in PATH_LOADERS for _, c in calls)
        for n in ast.walk(self.tree):
            callee = _callee(n.func if isinstance(n, ast.Call) else n, aliases)
            if isinstance(n, ast.Call) and callee in EXEC_CALLS:
                # runs the code of a spec: the spec is made by a call this file makes (read below), or it comes from
                # somewhere this file cannot see
                self.dynamic = True
                if not makes_spec:
                    unresolved_edge(
                        self.unresolved, f"{rel}: exec_module of a spec this file does not make"
                    )
            elif isinstance(n, ast.Call) and callee in PATH_LOADERS:
                self.dynamic = True
                self._path_loader(n, callee)
            elif isinstance(n, ast.Call) and callee in DYNAMIC_IMPORTS:
                self.dynamic = True
                # the module name is the first argument or the keyword `name=`
                named = [k.value for k in n.keywords if k.arg == "name"]
                self.dynamic_names += [
                    a.value
                    for a in (*n.args, *named)
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)
                ]
                if callee in (["iter_modules"], ["walk_packages"]):
                    # a package of tests, `pkg.__path__` (its folder is reached through the imports)
                    chain = _dotted(n.args[0]) if n.args else []
                    if not (
                        len(chain) == 2 and chain[1] == "__path__" and chain[0] in self.imports
                    ):
                        unresolved_edge(
                            self.unresolved,
                            f"{rel}: iter_modules or walk_packages of a path it cannot read",
                        )
                    continue
                first = n.args[0] if n.args else (named[0] if named else None)
                if first is None:
                    unresolved_edge(self.unresolved, f"{rel}: an import call with no module name")
                    continue
                prefix = _literal_start(first)
                package = _package_name_prefix(first)
                if package is not None and prefix == "":
                    # `f"{pkg.__name__}.{x}"`: a module inside the package `pkg` that the file imports from `tests`
                    # (checked against the tree: `_Signatures._cross_checks`); its folder is reached through the imports
                    self.package_names.append(package)
                elif (
                    prefix is None
                ):  # a plain text: followed as written, a leading dot is a relative name
                    if first.value.startswith("."):  # type: ignore[attr-defined]
                        unresolved_edge(
                            self.unresolved,
                            f"{rel}: a relative module name written as one text (starts with a dot)",
                        )
                elif prefix == "":
                    unresolved_edge(
                        self.unresolved, f"{rel}: a module name that starts with a value"
                    )
                elif prefix.startswith("."):
                    unresolved_edge(
                        self.unresolved,
                        f"{rel}: a relative module name built from parts (starts with a dot)",
                    )
                elif "tests".startswith(prefix) or prefix.startswith("tests"):
                    self.dynamic_prefixes.append(prefix)
            # (a name that is the target of `imp = ...` hands nothing on: its context is Store)
            elif (
                isinstance(n, (ast.Name, ast.Attribute))
                and id(n) not in called
                and not isinstance(n.ctx, ast.Store)
                and (callee in DYNAMIC_IMPORTS or callee in PATH_LOADERS)
            ):
                # the function handed on as a value (`map(importlib.import_module, names)`): it is called somewhere
                # we cannot see, with names we cannot read
                self.dynamic = True
                unresolved_edge(self.unresolved, f"{rel}: a loader is handed on as a value")

    def _path_loader(self, call: ast.Call, callee: list[str]) -> None:
        """`spec_from_file_location(name, path)` and `runpy.run_path(path)`: the path expression is kept; the tree
        reads it (`_Signatures.path_folders`): a file under `tests` is reached, one outside it reaches nothing of
        `tests`, one that cannot be read is an unresolved edge."""
        position, keyword = PATH_ARG[callee[0]]
        arg = call.args[position] if len(call.args) > position else None
        self.path_args.append(
            arg or next((k.value for k in call.keywords if k.arg == keyword), None)
        )

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


def _callee(func: ast.AST, aliases: dict[str, str]) -> list[str]:
    """The name a call or a reference stands for, as `_dotted(...)[-1:]` gives it, after a local alias is read back to
    the function it stands for (`imp = importlib.import_module`, `from importlib import import_module as imp`)."""
    last = _dotted(func)[-1:]
    if len(last) == 1 and len(_dotted(func)) == 1 and last[0] in aliases:
        return [aliases[last[0]]]
    return last


def _dynamic_aliases(tree: ast.AST) -> dict[str, str]:
    """local name -> the function of `DYNAMIC_IMPORTS` it is another name for: a name taken with `from importlib import
    import_module as imp`, and a name an assignment gives (`imp = importlib.import_module`, also `imp2 = imp`)."""
    known = {c[0] for c in DYNAMIC_IMPORTS}
    out: dict[str, str] = {}
    for _ in range(8):  # an alias of an alias settles in a few passes
        before = dict(out)
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                out.update({a.asname: a.name for a in n.names if a.asname and a.name in known})
            elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and n.value is not None:
                last = _dotted(n.value)[-1:]
                if not last:
                    continue
                target = out.get(last[0], last[0]) if len(_dotted(n.value)) == 1 else last[0]
                if target in known:
                    targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                    out.update({t.id: target for t in targets if isinstance(t, ast.Name)})
        if out == before:
            break
    return out


def _block_nodes(body: list[ast.stmt]) -> list[ast.stmt]:
    """The statements of a body and, inside every `if`, `try`, `with`, `for` and `while` of it, theirs too (a test or
    a fixture defined under a condition is still defined)."""
    out: list[ast.stmt] = []
    for n in body:
        out.append(n)
        for field in ("body", "orelse", "finalbody"):
            out += _block_nodes(
                getattr(n, field, []) if not isinstance(n, _FUNCS + (ast.ClassDef,)) else []
            )
        for h in getattr(n, "handlers", []) if not isinstance(n, _FUNCS + (ast.ClassDef,)) else []:
            out += _block_nodes(h.body)
        for c in getattr(n, "cases", []):
            out += _block_nodes(c.body)
    return out


def _package_name_prefix(a: ast.AST) -> str | None:
    """The local name `pkg` when a module name is built as `pkg.__name__` followed by a text that starts with a dot
    (`f"{pkg.__name__}.{x}"`, `pkg.__name__ + "." + x`), else None. Whether `pkg` is a package of `tests` is checked
    against the tree: anything else that starts with a value is a name the check cannot read."""
    if isinstance(a, ast.JoinedStr) and len(a.values) >= 2:
        head, nxt = a.values[0], a.values[1]
        first = head.value if isinstance(head, ast.FormattedValue) else None
    elif isinstance(a, ast.BinOp) and isinstance(a.op, ast.Add):
        operands: list[ast.AST] = []
        node: ast.AST = a
        while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            operands.insert(0, node.right)
            node = node.left
        operands.insert(0, node)
        if len(operands) < 2:
            return None
        first, nxt = operands[0], operands[1]
    else:
        return None
    chain = _dotted(first) if first is not None else []
    if (
        len(chain) == 2
        and chain[1] == "__name__"
        and isinstance(nxt, ast.Constant)
        and isinstance(nxt.value, str)
        and nxt.value.startswith(".")
    ):
        return chain[0]
    return None


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
        if isinstance(n, ast.Call) and _dotted(n.func)[-1:] in (*FIXTURE_BY_TEXT, *LAZY_FIXTURES):
            # `@pytest.mark.usefixtures("a", "b")` and `request.getfixturevalue("a")` name a fixture as a text; a
            # text that cannot be read (a variable, an f-string) stands for every fixture in reach
            used |= _text_names([*n.args, *(k.value for k in n.keywords)])
        elif isinstance(n, ast.Call) and _dotted(n.func)[-1:] == PARAMETRIZE:
            used |= _parametrize_names(n)
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
        self.sources: dict[str, str] = {}
        self.syntax_errors: list[str] = []
        self._tree: dict[str, tuple[list[str], str]] = {}
        self._stems: set[str] | None = None
        self._paths: dict[str, tuple[list[str], list[str]]] = {}
        self._present = set(self.files)

    def module(self, rel: str, source: str | None = None) -> _Module | None:
        text = source if source is not None else (self.loader(rel) if self.loader else "")
        cached = self.modules.get(rel, False)
        if cached is not False and self.sources.get(rel) == text:
            return cached  # type: ignore[return-value]
        self.sources[rel] = text
        try:
            mod = _Module(rel, text) if text else None
        except SyntaxError:
            mod = None
            if rel.startswith("tests/") or kind_of(rel) == "conftest":
                unresolved_edge(self.syntax_errors, f"{rel}: the file does not parse")
        if mod is not None:
            self._bare_imports(mod)
        self.modules[rel] = mod
        return mod

    def _bare_imports(self, mod: _Module) -> None:
        """An absolute import whose first name is a module or package next to the file (`from helpers import x` in
        `tests/test_a.py` reads `tests/helpers.py`, as pytest puts the folder on the import path) is followed like an
        import of `tests`; a first name that is a stem of files in other folders of `tests` only is an unresolved edge
        (the check cannot tell which one runs); any other name (the standard library, a package, `src`) is outside."""
        here = "/".join(mod.rel.split("/")[:-1])
        for local, dotted, taken in mod.bare:
            top, _, rest = dotted.partition(".")
            if top in sys.stdlib_module_names:
                continue
            base = f"{here}/{top}" if here else top
            if self._file_of(base) or self._file_of(
                f"{base}/{rest.replace('.', '/')}" if rest else base
            ):
                stem = f"{base}/{rest.replace('.', '/')}" if rest else base
                mod.imports[local] = (stem, taken)
            elif top in self._test_stems():
                unresolved_edge(
                    mod.unresolved,
                    f"{mod.rel}: the import of {top} may be a module of tests in another folder",
                )

    def path_folders(self, m: _Module) -> tuple[list[str], list[str]]:
        """(the folders and files under `tests` that the path loaders of `m` read from, the reasons for each path that
        cannot be read). A path outside `tests` (`demos/...`) reaches nothing of `tests`."""
        if m.rel in self._paths:
            return self._paths[m.rel]
        folders: list[str] = []
        reasons: list[str] = []

        def lookup(name: str) -> tuple[str, dict[str, list[ast.AST]], ast.AST] | None:
            head, attr = self._head(m.imports, name)
            if head is None:
                return None
            target, member = self._imported(m.imports, head, attr)
            got = target.values.get(member, []) if target is not None else []
            return (
                (target.rel, target.values, got[0])
                if target is not None and len(got) == 1
                else None
            )

        for arg in m.path_args:
            parts = _path_parts(arg, m.rel, m.values, lookup=lookup)
            if not parts or parts[0] == "*" or ".." in parts:
                unresolved_edge(reasons, f"{m.rel}: a file is loaded from a path it cannot read")
            elif parts[0] == "tests":
                lead = parts[: next((i for i, p in enumerate(parts) if "*" in p), len(parts))]
                folders.append("/".join(lead))
        self._paths[m.rel] = (folders, reasons)
        return self._paths[m.rel]

    def _test_stems(self) -> set[str]:
        """The names of every module and package under `tests/` (the stem of each file, each folder with an
        `__init__.py`)."""
        if self._stems is None:
            self._stems = set()
            for f in self.files:
                if f.startswith("tests/") and f.endswith(".py"):
                    parts = f.removesuffix(".py").split("/")
                    self._stems.add(
                        parts[-2] if parts[-1] == "__init__" and len(parts) > 1 else parts[-1]
                    )
        return self._stems

    def inits(self, rel: str) -> list[_Module]:
        """The `__init__.py` of every package folder on the way to the file `rel` (pytest runs each one when it
        collects the file, so a change to it can change any test under the folder)."""
        parts = rel.split("/")[:-1]
        out = []
        for i in range(1, len(parts) + 1):
            candidate = "/".join([*parts[:i], "__init__.py"])
            if candidate == rel:
                continue
            mod = self.module(candidate)
            if mod is not None:
                out.append(mod)
        return out

    def _with_run_time_reach(self, paths: list[str]) -> list[str]:
        """`paths` and every file a file of them can reach by a name worked out at run time, again for each file added
        (batch 18: a prefix such as `"t"` reaches `tools/helper.py`, and a run-time import inside that file is a reason
        and its text is part of the digest, just like a file of `tests/`)."""
        seen = list(paths)
        todo = list(paths)
        while todo:
            rel = todo.pop()
            m = self.module(rel) if rel.endswith(".py") else None
            if m is None or not m.dynamic:
                continue
            for reached in self._dynamic_files(m):
                if reached not in seen:
                    seen.append(reached)
                    todo.append(reached)
        return seen

    def tree_state(self, mod: _Module) -> tuple[list[str], str]:
        """(the reasons the check cannot read the tests tree, a digest of every file that can act on a test). With
        the paths of the state (`files`) the whole tree is read; without them only the file itself and what it reaches
        through its conftests. Every file under `tests/` is part of the digest except a note in `.md` or `.rst`
        (an allow-list of suffixes no code reads); a state with a reason lists every unit of every file when the
        digest changes."""
        key = "" if self.files else mod.rel
        if key in self._tree:
            return self._tree[key]
        paths = [f for f in self.files if f.startswith("tests/") or f == "conftest.py"] or [
            mod.rel,
            *(c.rel for c in self.conftests(mod.rel)),
            *(i.rel for i in self.inits(mod.rel)),
        ]
        paths = self._with_run_time_reach(paths)
        # empty on purpose: the merge after the walk is the only source of syntax errors
        reasons: list[str] = []
        for rel in sorted(paths):
            if rel.endswith(".py"):
                m = self.module(rel)
                if m is None:
                    continue
                for reason in self.path_folders(m)[1]:
                    unresolved_edge(reasons, reason)
                self._cross_checks(m, reasons)
                if kind_of(rel) == "test":
                    _units_of_tests(
                        m, self
                    )  # reads the base classes: a base it cannot read is a reason
                for reason in m.unresolved:
                    unresolved_edge(reasons, reason)
        for reason in self.syntax_errors:
            unresolved_edge(reasons, reason)
        digest = hashlib.sha256()
        for rel in sorted(
            paths if reasons else []
        ):  # read only when there is a reason to list every test
            if rel.endswith(ALLOWED_SUFFIXES):
                continue
            digest.update(f"\0{rel}\0".encode())
            digest.update(
                (self.sources.get(rel) if rel in self.sources else self._text(rel)).encode(
                    "utf-8", "replace"
                )
            )
        self._tree[key] = (reasons, digest.hexdigest())
        return self._tree[key]

    def _text(self, rel: str) -> str:
        return self.loader(rel) if self.loader else ""

    def _cross_checks(self, m: _Module, reasons: list[str]) -> None:
        """The edges that need the whole tree: an import of a module under `tests` that is not there, and a plugin
        name that names no file."""
        for stem, taken in m.imports.values():
            file = self._file_of(stem)
            if file is None:
                # (a folder with files and no `__init__.py` is a namespace package: the import is fine)
                if not any(f.startswith(stem + "/") for f in self.files):
                    unresolved_edge(
                        reasons,
                        f"{m.rel}: it imports {stem.replace('/', '.')}, which is not in the tree",
                    )
                continue
            target = self.module(file)
            if (
                taken
                and target is not None
                and taken not in target.dumps
                and not target.stars
                and self._file_of(f"{stem}/{taken}") is None
            ):
                unresolved_edge(
                    reasons,
                    f"{m.rel}: it imports {taken} from {stem.replace('/', '.')}, which does not define it",
                )
        for local in m.package_names:
            stem, taken = m.imports.get(local, ("", None))
            folder = stem if taken is None else f"{stem}/{taken}"
            if (
                not stem
                or self._file_of(f"{folder}/__init__") is None
                and not (
                    f"{folder}/__init__.py" in self._present or self.module(f"{folder}/__init__.py")
                )
            ):
                unresolved_edge(
                    reasons,
                    f"{m.rel}: {local}.__name__ starts a module name but {local} is no package of tests",
                )
        for dotted in m.plugin_names:
            stem = _stem(m.rel, 0, dotted)
            if stem is not None and self._file_of(stem) is None:
                unresolved_edge(reasons, f"{m.rel}: the plugin {dotted} is not in the tree")
        for dotted in m.dynamic_names:
            stem = _stem(m.rel, 0, dotted)
            if (
                stem is not None
                and self._file_of(stem) is None
                and not any(f.startswith(stem + "/") for f in self.files)
            ):
                unresolved_edge(
                    reasons, f"{m.rel}: it imports {dotted} by name, which is not in the tree"
                )

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
        """The file of the module `stem` names (`stem.py`, or the `__init__.py` of the package, which may be empty)."""
        for c in (f"{stem}.py", f"{stem}/__init__.py"):
            if c in self._present if self._present else self.module(c):
                return c
        return None

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
        # a name built at run time: every module whose dotted name starts with the text the name starts with (a
        # package, its `__init__.py`, is the module `tests.zz` and the text `tests.zz.` reaches it); a name that
        # starts with a value cannot be read, whatever else the file imports, so it reaches every Python file under
        # `tests` (the one rule: a name that cannot be read lists every test of the file)
        for folder in self.path_folders(m)[0]:
            found |= {
                f for f in self.files if f == folder or f.startswith(folder.rstrip("/") + "/")
            }
        for prefix in m.dynamic_prefixes:
            # `dynamic_prefixes` holds only a readable start of a name, never an empty text: a name that cannot be read
            # is one `unresolved_edge` reason, and one reason lists every test whenever a file under `tests/` changes
            # (`closure`, `tree_state`). A test pins both halves (batch 18: nothing enforced the pairing before); an
            # empty text stored here would be every file, which is the safe side
            found |= {f for f in self.files if _dotted_path(f).startswith(prefix)}
            found |= {
                f
                for f in self.files
                if f.endswith("/__init__.py") and f"{_dotted_path(f)}.".startswith(prefix)
            }
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
            for rel in (
                "pyproject.toml",
                "pytest.ini",
                ".pytest.ini",
                "pytest.toml",
                "tox.ini",
                "setup.cfg",
            ):
                text = self.loader(rel) if self.loader else ""
                for line in re.findall(
                    r"addopts\s*[=:]\s*(.*?)(?:\n\s*\n|\n\S|\Z)", text, re.DOTALL
                ):
                    words = re.findall(r"[^\s\"',\[\]]+", line)
                    for i, w in enumerate(words):
                        name = words[i + 1] if w == "-p" and i + 1 < len(words) else None
                        name = name or (w[2:] if w.startswith("-p") and len(w) > 2 else None)
                        if name:  # (`-p no:name` names no module of `tests`: `_stem` leaves it out)
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
            # every hook of the conftest (a name that starts with `pytest_`: a session, collection or run hook acts on every
            # test below it, whatever its name), the 14 switch names and the autouse fixtures
            todo += [
                (conf, n)
                for n in conf.dumps
                if n in SWITCH_NAMES or n.startswith("pytest_") or n in conf.autouse
            ]
            for rel in self._named_files(conf.plugin_names, conf.rel):
                plugin = self.module(rel)
                if plugin is not None:
                    touch(plugin)
                    todo.extend((plugin, n) for n in sorted(plugin.dumps))
        for init in self.inits(mod.rel):
            # pytest runs the `__init__.py` of each package folder when it collects the file: all of its text acts
            touch(init)
            parts.append(f"|init {init.rel}={ast.dump(init.tree)}")
            todo.extend((init, n) for n in sorted(init.dumps))
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
            if name == DYNAMIC_FIXTURE:
                # a fixture named by a text that cannot be read: any fixture of the file or of a conftest above it
                for scope in (m, *self.conftests(m.rel)):
                    todo += [(scope, k) for k, v in scope.nodes.items() if _is_fixture(v)]
                    todo += [
                        (scope, k) for k in scope.imports
                    ]  # a fixture imported from another module
                continue
            if name in m.dumps:
                parts.append(f"|{m.rel}:{name}={m.dumps[name]}")
                # what the definition of the name uses, and what the values behind an assignment of it use
                todo += [(m, u) for u in m.children_of(name)]
                own_node = m.nodes.get(name)
                if isinstance(own_node, _FUNCS) and name in {
                    a.arg
                    for a in (
                        *own_node.args.posonlyargs,
                        *own_node.args.args,
                        *own_node.args.kwonlyargs,
                    )
                }:
                    # a fixture that takes the fixture of its own name (`def client(client)`) overrides the one of a
                    # nearer or farther conftest: that one is part of it
                    todo += [
                        (c, name) for c in self.conftests(m.rel) if c is not m and name in c.dumps
                    ]
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
        reasons, digest = self.tree_state(mod)
        if reasons:
            # something in the tree cannot be read: any change to a file under `tests/` changes every unit
            parts.append(f"|tree {digest}")
        return ast.dump(node) + "".join(sorted(parts))


def _is_fixture(fn: ast.AST) -> bool:
    """True for a function decorated `@pytest.fixture` or `@fixture` (with or without a call)."""
    for d in getattr(fn, "decorator_list", []):
        target = d.func if isinstance(d, ast.Call) else d
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
        if name == "fixture":
            return True
    return False


def _base_name(b: ast.AST) -> str:
    return b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", "")


def _is_test_class(n: ast.ClassDef) -> bool:
    """pytest collects a class whose name starts with `Test` and, whatever its name, a `unittest.TestCase`. The check
    reads a superset: any class that has a base other than `object` may be a `TestCase` through its base (a mixin,
    `IsolatedAsyncioTestCase`, `TestCase as TC`, a project base), so it is read as one when it has tests."""
    if n.name.startswith("Test"):
        return True
    return any(_base_name(b) != "object" for b in n.bases)


def _class_chain(
    cls: ast.ClassDef,
    mod: _Module,
    sigs: _Signatures | None,
    seen: set[tuple[str, str]] | None = None,
) -> list[tuple[ast.ClassDef, _Module]]:
    """The class and every base class the tree can find (a base in the same file, or imported from a module of
    `tests`), nearest first. A base that is no name or attribute is an unresolved edge; a base that is not found in
    the tree is outside it (`unittest.TestCase`, `object`)."""
    seen = seen if seen is not None else set()
    if (mod.rel, cls.name) in seen:
        return []
    seen.add((mod.rel, cls.name))
    out: list[tuple[ast.ClassDef, _Module]] = [(cls, mod)]
    for b in cls.bases:
        chain = _dotted(b)
        if not chain:
            unresolved_edge(
                mod.unresolved,
                f"{mod.rel}: the base of class {cls.name} is an expression it cannot read",
            )
            continue
        found = mod.nodes.get(chain[-1]) if len(chain) == 1 else None
        if isinstance(found, ast.ClassDef):
            out += _class_chain(found, mod, sigs, seen)
        elif sigs is not None:
            head, attr = sigs._head(mod.imports, ".".join(chain))
            if head is not None:
                target, member = sigs._imported(mod.imports, head, attr)
                base = target.nodes.get(member) if target is not None else None
                if isinstance(base, ast.ClassDef) and target is not None:
                    out += _class_chain(base, target, sigs, seen)
                else:
                    unresolved_edge(
                        mod.unresolved,
                        f"{mod.rel}: the base {'.'.join(chain)} is not found in the module it comes from",
                    )
    return out


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


def _units_of_tests(
    mod: _Module, sigs: _Signatures | None = None
) -> dict[str, tuple[ast.AST, tuple[ast.AST, ...]]]:
    """key -> (node, extras): `name` for a test function (plain or async) or a name a `test*` assignment binds
    (`test_x = factory()`), anywhere at module level (also under `if`, `try`, `with`), `Class::name` for a method of a
    test class, `Outer::Inner::name` for a nested one. The tests a class inherits from a base class of the tree count
    as its own (`class TestA(Base): pass`). A test function or method is one whose name starts with `test`, and a test
    class is read by `_is_test_class`. The extras of a method are those of `_class_extras` of every class in its chain
    (a class-level `pytestmark` or `@pytest.mark.skip` switches every method off)."""
    out: dict[str, tuple[ast.AST, tuple[ast.AST, ...]]] = {}

    def add(key: str, node: ast.AST, extras: tuple[ast.AST, ...]) -> None:
        if key in out:  # the same name under two branches of an `if`: both are part of it
            out[key] = (out[key][0], (*out[key][1], node, *extras))
        else:
            out[key] = (node, extras)

    def visit_class(cls: ast.ClassDef, prefix: str, outer: tuple[ast.AST, ...]) -> None:
        chain = _class_chain(cls, mod, sigs)
        for owner, _owner_mod in chain:
            for m in _block_nodes(owner.body):
                names = (
                    [m.name]
                    if isinstance(m, _FUNCS)
                    else [t.id for t in m.targets if isinstance(t, ast.Name)]
                    if isinstance(m, ast.Assign)
                    else []
                )
                for name in names:
                    if name.startswith("test"):
                        extras = tuple(e for o, _ in chain for e in _class_extras(o, m))
                        add(f"{prefix}{cls.name}::{name}", m, (*extras, *outer))
            for inner in owner.body:
                if isinstance(inner, ast.ClassDef) and _is_test_class(inner):
                    visit_class(
                        inner, f"{prefix}{cls.name}::", (*_class_extras(cls, inner), *outer)
                    )

    for n in _block_nodes(mod.tree.body):
        if isinstance(n, _FUNCS) and n.name.startswith("test"):
            add(n.name, n, ())
        elif isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id.startswith("test") for t in n.targets
        ):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id.startswith("test"):
                    add(t.id, n, ())
        elif isinstance(n, ast.ClassDef) and _is_test_class(n):
            visit_class(n, "", ())
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
_CONFIG_FILE = re.compile(r"(?:pyproject\.toml|\.?pytest\.ini|pytest\.toml|tox\.ini|setup\.cfg)")
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


def _sigs_for(loader: Loader | None, rel: str = "", source: str | None = None) -> _Signatures:
    """One `_Signatures` per loader (every file of a state is parsed once, and the tree is scanned once), unless the
    text given for `rel` is not the text the loader has for it: then a fresh one."""
    if loader is None or (source is not None and loader(rel) != source):
        return _Signatures(loader)
    sigs = getattr(loader, "_sigs", None)
    if sigs is None:
        sigs = _Signatures(loader)
        try:
            loader._sigs = sigs  # type: ignore[attr-defined]
        except AttributeError:
            pass
    return sigs


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
    sigs = _sigs_for(loader, rel, source)
    mod = sigs.module(rel, source)
    if mod is None:
        return {}
    if kind == "mutants":
        return _mutant_units(mod)
    nodes = _units_of_tests(mod, sigs) if kind == "test" else _units_of_functions(mod)
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
            units[rel] = frozenset(_unit_names(rel, kind, load(rel), _sigs_for(load)))
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


def _unit_names(rel: str, kind: str, source: str, sigs: _Signatures | None = None) -> list[str]:
    """The names of the units of a file in scope, without the signatures (cheap): see `units_of`."""
    if not source:
        return []
    if kind in ("fixture", "data", "config"):
        return [Path(rel).name]
    sigs = sigs or _Signatures(None)
    mod = sigs.module(rel, source)
    if mod is None:
        return []
    if kind == "mutants":
        return list(_mutant_units(mod))
    return list(_units_of_tests(mod, sigs) if kind == "test" else _units_of_functions(mod))


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
    reasons = _tree_reasons(new_load) + [
        r for r in _tree_reasons(old_load) if r not in _tree_reasons(new_load)
    ]
    if bad and reasons:
        bad.insert(0, _listed_because(reasons))
    return bad


def _listed_because(reasons: list[str]) -> str:
    """The first line of a report when every test is listed: the first five reasons in the order the tree walk found
    them, then the count of the rest."""
    shown = "; ".join(reasons[:5]) + (f" (and {len(reasons) - 5} more)" if len(reasons) > 5 else "")
    return f"every test is listed because the check cannot read part of the tests tree: {shown}"


def _tree_reasons(load: Loader) -> list[str]:
    """The reasons the tests tree of a state cannot be read (empty when it can), see `_Signatures.tree_state`."""
    sigs = _sigs_for(load)
    if not sigs.files:
        return []
    root = next((m for m in sigs.modules.values() if m is not None), None)
    return sigs.tree_state(root)[0] if root is not None else []


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
