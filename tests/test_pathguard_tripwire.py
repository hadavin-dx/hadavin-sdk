"""A tripwire for the class "a file operation on a path nobody checked" in the whole package.

The scan reads the source of every ``src/hadavin_sdk/**/*.py`` except ``pathguard.py`` itself (the AST, nothing is run).
Inside each function it flags a banned call (``open``, ``os.open``, ``os.replace``, ``os.remove``, ``os.rename``,
``os.listdir``, ``os.scandir``, ``os.walk``, ``os.makedirs``, ``os.mkdir``, ``os.rmdir``, ``os.unlink``, ``shutil.*``, and
the methods ``.read_bytes .read_text .write_bytes .write_text .open .mkdir .iterdir .glob .rglob .unlink .rmdir .touch
.symlink_to .hardlink_to .chmod``, plus ``.replace(x)`` and ``.rename(x)`` with ONE argument: ``str.replace`` takes two, so
one argument is the ``Path`` method) unless every path argument (the receiver for a method, the first argument for ``open``
and ``os.*`` calls that take one path, every argument for ``os.replace``, ``os.rename`` and ``shutil.*``) is a plain NAME
whose latest earlier assignment in the same function is a call ``pathguard.join``, ``pathguard.inside``,
``pathguard.operator_dir``, ``pathguard.operator_file`` or ``confined``. ``pathguard.component`` and
``pathguard.operator_text`` do NOT count: they return a string or nothing, not a checked path. That is the only allow rule
in the code: there is no comment switch.

A hit that is not guarded must be listed, with its reason, in ``tests/fixtures/pathguard_exceptions.txt``: one line per
function, ``file | function | origin | reason``, where origin is one of ``operator`` (typed by the person, no outer folder),
``config`` (a path in the config file), ``fixed`` (a constant of ours, or a fixed name under a folder checked elsewhere),
``package`` (a file shipped inside the package) or ``checked`` (validated by the caller or by a check this scan cannot
follow; the reason names it). An unlisted hit fails the test, and so does a listed row that matches no hit any more.

Limits, stated plainly: the scan follows one function only. A path passed in from another function is not trusted, so the
function that receives it must re-check it or be listed; a name assigned in a branch that does not run before the call is
not seen; a path built from a guarded one by ``/`` or ``.parent`` is NOT trusted and needs its own ``pathguard`` call. It
cannot see a file operation made through a library call (``json.load(open_file)``, ``yaml.safe_load(path.open())`` is seen
only as the ``.open``). The two seeded fixtures in ``tests/fixtures`` prove the scan reports bad code and lets good code
pass.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from hadavin_sdk import pathguard

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "hadavin_sdk"
FIX = Path(__file__).resolve().parent / "fixtures"

# One line per banned name, so a test (and a mutant) can remove exactly one. "first": the first argument is the path;
# "two": the first two arguments are paths; "all": every argument; "dir": the ``dir=`` keyword (absent means the system
# folder, which is a file operation on a folder nobody checked: it must be listed); "fd": a file descriptor that must come
# from ``os.open`` or ``tempfile.mkstemp`` in the same function (the path of that call is checked on its own).
BANNED_CALLS = {
    "open": "first",
    "io.open": "first",
    "builtins.open": "first",
    "codecs.open": "first",
    "gzip.open": "first",
    "os.open": "first",
    "os.remove": "first",
    "os.unlink": "first",
    "os.listdir": "first",
    "os.scandir": "first",
    "os.walk": "first",
    "os.makedirs": "first",
    "os.mkdir": "first",
    "os.rmdir": "first",
    "os.removedirs": "first",
    "os.link": "two",
    "os.symlink": "two",
    "os.chmod": "first",
    "os.chown": "first",
    "os.utime": "first",
    "os.truncate": "first",
    "os.stat": "first",
    "os.lstat": "first",
    "os.readlink": "first",
    "os.replace": "two",
    "os.rename": "two",
    "os.fdopen": "fd",
    "os.path.exists": "first",
    "os.path.lexists": "first",
    "os.path.isfile": "first",
    "os.path.isdir": "first",
    "os.path.islink": "first",
    "os.path.ismount": "first",
    "os.path.getsize": "first",
    "os.path.getmtime": "first",
    "os.path.getatime": "first",
    "os.path.getctime": "first",
    "os.path.realpath": "first",
    "os.path.samefile": "two",
    "tempfile.mkstemp": "dir",
    "tempfile.mkdtemp": "dir",
    "tempfile.NamedTemporaryFile": "dir",
    "tempfile.TemporaryFile": "dir",
    "tempfile.TemporaryDirectory": "dir",
    "tempfile.SpooledTemporaryFile": "dir",
    "sqlite3.connect": "first",
}
# every call of a name that starts with one of these (``shutil.copy``, ``glob.glob``, ...)
BANNED_PREFIXES = {
    "shutil.": "all",
    "glob.": "first",
}
BANNED_METHODS = {
    "read_bytes",
    "read_text",
    "write_bytes",
    "write_text",
    "open",
    "mkdir",
    "iterdir",
    "glob",
    "rglob",
    "unlink",
    "rmdir",
    "touch",
    "symlink_to",
    "hardlink_to",
    "chmod",
    "lchmod",
    "exists",
    "is_file",
    "is_dir",
    "is_symlink",
    "is_mount",
    "stat",
    "lstat",
    "resolve",
    "samefile",
    "readlink",
    "walk",
    "owner",
    "group",
}
# A method name alone also matches other objects (``match.group(1)``, ``ast.walk(tree)``, ``deps.resolve(name)``,
# ``store.touch(run_id)``). For these names the call is taken as the ``Path`` method only when its arguments have the shape
# ``pathlib`` gives it: (most positional arguments, the keyword names allowed). Any other shape is not a path call.
PATH_METHOD_SHAPE = {
    "resolve": (1, {"strict"}),
    "group": (0, set()),
    "owner": (0, {"follow_symlinks"}),
    "walk": (0, {"top_down", "on_error", "follow_symlinks"}),
    "touch": (2, {"mode", "exist_ok"}),
    "exists": (0, {"follow_symlinks"}),
    "is_file": (0, {"follow_symlinks"}),
    "is_dir": (0, {"follow_symlinks"}),
    "stat": (0, {"follow_symlinks"}),
}
# ``Path.replace(target)`` and ``Path.rename(target)`` take ONE argument; ``str.replace(old, new)`` takes two or more.
BANNED_ONE_ARG = {"replace", "rename"}
GUARD_FUNCTIONS = {"join", "inside", "operator_dir", "operator_file", "confined"}
ORIGINS = {"operator", "config", "fixed", "package", "checked"}
# a module name that an ``import`` or ``from ... import`` may be written with: the dotted name it stands for
MODULES = {
    "os",
    "os.path",
    "posixpath",
    "ntpath",
    "shutil",
    "tempfile",
    "io",
    "sqlite3",
    "builtins",
    "glob",
    "codecs",
    "gzip",
}
_CANON = {"posixpath": "os.path", "ntpath": "os.path"}
FD_SOURCES = {"os.open", "tempfile.mkstemp"}


def _canon(dotted: str) -> str:
    head, _, rest = dotted.partition(".")
    for long, short in _CANON.items():
        if dotted == long or dotted.startswith(long + "."):
            return short + dotted[len(long) :]
    return dotted if not rest else head + "." + rest


def _aliases(tree: ast.Module) -> dict[str, str]:
    """name -> dotted module or function it stands for, from every ``import`` in the file (``import os as _o`` maps
    ``_o`` to ``os``; ``from os import replace as r`` maps ``r`` to ``os.replace``; ``from os import path`` maps
    ``path`` to ``os.path``). Imports inside functions count for the whole file (a wider net, never a narrower one)."""
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                found[a.asname or a.name.split(".")[0]] = (
                    a.name if a.asname else a.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for a in node.names:
                found[a.asname or a.name] = f"{node.module}.{a.name}"
    return {k: _canon(v) for k, v in found.items()}


def _dotted(node: ast.AST, aliases: dict[str, str]) -> str | None:
    """The dotted name a call target stands for (``os.path.exists``, ``shutil.copy``, ``open``), after alias
    resolution; ``__import__("os").replace`` is read as ``os.replace``. ``None`` when it is not a plain dotted name."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "__import__"
    ):
        if (
            node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            root = node.args[0].value
        else:
            return None
    elif isinstance(node, ast.Name):
        root = aliases.get(node.id, node.id)
    else:
        return None
    return _canon(".".join([root, *reversed(parts)]))


def _is_guard_call(node: ast.AST | None) -> bool:
    """``pathguard.join(...)`` and the other functions that return a CHECKED path; ``confined(...)`` is the older
    config-folder check, which delegates to ``pathguard.inside``. ``pathguard.component`` is not here: it returns a string."""
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    if isinstance(f, ast.Attribute):
        return (
            isinstance(f.value, ast.Name)
            and f.value.id == "pathguard"
            and f.attr in GUARD_FUNCTIONS
        )
    return isinstance(f, ast.Name) and f.id == "confined"


def _own_nodes(scope: ast.AST):
    """Every node of ``scope`` except the insides of nested functions (they are scopes of their own). A lambda is NOT a
    scope of its own: its body is part of the function around it, so a banned call inside a lambda is seen."""
    todo = list(ast.iter_child_nodes(scope))
    while todo:
        node = todo.pop()
        yield node
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            todo.extend(ast.iter_child_nodes(node))


def _is_fd_source(node: ast.AST | None, aliases: dict[str, str]) -> bool:
    return isinstance(node, ast.Call) and _dotted(node.func, aliases) in FD_SOURCES


def _assignments(func: ast.AST, aliases: dict[str, str]) -> dict[str, list[tuple[int, str]]]:
    """name -> [(line, kind)] for plain-name targets (also ``with ... as``, ``for``, walrus). kind is ``guard`` (assigned
    from a pathguard call), ``fd`` (assigned from ``os.open`` or the first item of ``tempfile.mkstemp``) or ``other``."""
    found: dict[str, list[tuple[int, str]]] = {}

    def add(target: ast.AST, line: int, kind: str) -> None:
        if isinstance(target, ast.Name):
            found.setdefault(target.id, []).append((line, kind))
        elif isinstance(target, ast.Tuple | ast.List):
            for i, t in enumerate(target.elts):
                add(t, line, "fd" if kind == "fd-tuple" and i == 0 else "other")

    def kind_of(value: ast.AST | None) -> str:
        if _is_guard_call(value):
            return "guard"
        if isinstance(value, ast.Call):
            name = _dotted(value.func, aliases)
            if name == "os.open":
                return "fd"
            if name == "tempfile.mkstemp":
                return "fd-tuple"
        return "other"

    for node in _own_nodes(func):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                add(t, node.lineno, kind_of(node.value))
        elif (isinstance(node, ast.AnnAssign) and node.value is not None) or isinstance(
            node, ast.NamedExpr
        ):
            add(node.target, node.lineno, kind_of(node.value))
        elif isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
            add(node.target, node.target.lineno, "other")
        elif isinstance(node, ast.With | ast.AsyncWith):
            for item in node.items:
                if item.optional_vars is not None:
                    add(item.optional_vars, node.lineno, "other")
        elif isinstance(
            node, ast.Lambda
        ):  # a parameter of a lambda shadows the name of the function around it
            for a in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
                add(ast.Name(id=a.arg), node.lineno, "other")
    return found


def _guarded(
    arg: ast.AST, line: int, assigned: dict[str, list[tuple[int, str]]], want: str
) -> bool:
    if not isinstance(arg, ast.Name):
        return False
    earlier = [(ln, k) for ln, k in assigned.get(arg.id, []) if ln <= line]
    return bool(earlier) and max(earlier)[1] == want


def _path_shaped(attr: str, call: ast.Call) -> bool:
    shape = PATH_METHOD_SHAPE.get(attr)
    if shape is None:
        return True
    most, keywords = shape
    return (
        len(call.args) <= most
        and all(isinstance(a, ast.Constant) for a in call.args)
        and all(kw.arg in keywords for kw in call.keywords)
    )


def _banned(call: ast.Call, aliases: dict[str, str]) -> tuple[str, str, list[ast.AST]] | None:
    """(printed name, kind of argument wanted, the path arguments) when ``call`` is a banned file operation."""
    f = call.func
    dotted = _dotted(f, aliases)
    if dotted is not None:
        how = BANNED_CALLS.get(dotted)
        if how is None:
            for prefix, h in BANNED_PREFIXES.items():
                if dotted.startswith(prefix):
                    how = h
        if how == "first":
            return dotted, "guard", call.args[:1]
        if how == "two":
            return dotted, "guard", call.args[:2]
        if how == "all":
            return dotted, "guard", list(call.args)
        if how == "dir":
            return dotted, "guard", [kw.value for kw in call.keywords if kw.arg == "dir"]
        if how == "fd":
            return dotted, "fd", call.args[:1]
    if isinstance(f, ast.Attribute):
        if f.attr in BANNED_METHODS and _path_shaped(f.attr, call):
            return f".{f.attr}", "guard", [f.value]
        if f.attr in BANNED_ONE_ARG and len(call.args) == 1 and not call.keywords:
            return f".{f.attr}", "guard", [f.value]
    return None


def _scopes(tree: ast.Module):
    """(qualified name, node) for the module and every function, methods as ``Class.method``."""
    yield "<module>", tree

    def walk(node: ast.AST, prefix: str):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                name = f"{prefix}{child.name}"
                yield name, child
                yield from walk(child, f"{name}.")
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, f"{prefix}{child.name}.")
            else:
                yield from walk(child, prefix)

    yield from walk(tree, "")


def scan_hits(source: str, filename: str) -> list[tuple[str, str, int, str]]:
    """Every banned call whose path is not guarded, as (file, function, line, call)."""
    tree = ast.parse(source, filename=filename)
    aliases = _aliases(tree)
    hits = []
    for qualname, scope in _scopes(tree):
        assigned = _assignments(scope, aliases)
        for node in _own_nodes(scope):
            found = _banned(node, aliases) if isinstance(node, ast.Call) else None
            if found is None:
                continue
            name, want, args = found
            if not args or not all(_guarded(a, node.lineno, assigned, want) for a in args):
                hits.append((filename, qualname, node.lineno, name))
    return sorted(hits, key=lambda h: (h[1], h[2], h[3]))


def scan_source(source: str, filename: str) -> list[str]:
    """``scan_hits`` as ``file:line: call: reason`` text."""
    return [
        f"{f}:{line}: {call}: the path is not a name assigned from a pathguard call (in {fn})"
        for f, fn, line, call in scan_hits(source, filename)
    ]


EXCEPTIONS = FIX / "pathguard_exceptions.txt"


def _targets() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if p.name != "pathguard.py" or p.parent != SRC)


Row = tuple[
    str, str, str, int, str, str, str
]  # file, function, call, count, origin, validator, reason


def parse_rows(text: str, name: str = EXCEPTIONS.name) -> list[Row]:
    rows: list[Row] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(" | ")]
        assert len(parts) == 7 and all(parts), (
            f"{name}:{number}: need file | function | call | count | origin | validator | reason"
        )
        assert parts[3].isdigit() and int(parts[3]) >= 1, f"{name}:{number}: count must be a number"
        assert parts[4] in ORIGINS, f"{name}:{number}: origin must be one of {sorted(ORIGINS)}"
        rows.append((parts[0], parts[1], parts[2], int(parts[3]), parts[4], parts[5], parts[6]))
    return rows


def _exception_rows() -> list[Row]:
    return parse_rows(EXCEPTIONS.read_text(encoding="utf-8"))


def _all_hits() -> list[tuple[str, str, int, str]]:
    hits: list[tuple[str, str, int, str]] = []
    for path in _targets():
        hits += scan_hits(path.read_text(encoding="utf-8"), path.relative_to(ROOT).as_posix())
    return hits


def compare(rows: list[Row], hits: list[tuple[str, str, int, str]]) -> list[str]:
    """Problems between the listed rows and the hits: a hit with no row, a row with no hit, and a count that is not
    exact in either direction (one more hit in a listed function is a new, unreviewed file operation)."""
    found: dict[tuple[str, str, str], int] = {}
    for f, fn, _, call in hits:
        found[(f, fn, call)] = found.get((f, fn, call), 0) + 1
    listed: dict[tuple[str, str, str], int] = {}
    problems = []
    for f, fn, call, count, *_ in rows:
        if (f, fn, call) in listed:
            problems.append(f"{f} | {fn} | {call}: listed twice")
        listed[(f, fn, call)] = count
    for key, n in sorted(found.items()):
        if key not in listed:
            problems.append(f"{key[0]} | {key[1]} | {key[2]}: {n} hit(s), not listed")
        elif listed[key] != n:
            problems.append(
                f"{key[0]} | {key[1]} | {key[2]}: {n} hit(s), the list says {listed[key]}"
            )
    for key, n in sorted(listed.items()):
        if key not in found:
            problems.append(f"{key[0]} | {key[1]} | {key[2]}: listed ({n}) but no hit is left")
    return problems


def test_no_file_operation_in_the_package_works_on_an_unchecked_path_unless_listed_with_a_reason():
    problems = compare(_exception_rows(), _all_hits())
    assert problems == [], "unchecked paths:\n" + "\n".join(problems)


def test_the_comparator_refuses_one_more_hit_in_a_listed_function():
    rows: list[Row] = [("a.py", "f", ".read_text", 1, "fixed", "-", "x")]
    one = [("a.py", "f", 3, ".read_text")]
    assert compare(rows, one) == []
    assert (
        compare(rows, one + [("a.py", "f", 9, ".read_text")]) != []
    )  # a second hit of the same call
    assert (
        compare(rows, one + [("a.py", "f", 9, ".stat")]) != []
    )  # another call in the same function
    assert compare(rows, []) != []  # a row with no hit
    assert compare(rows + rows, one) != []  # a duplicate row


def _known_functions() -> set[str]:
    names = set(pathguard.__all__)
    for path in SRC.rglob("*.py"):
        names |= {
            n.name
            for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
    return names


def _called_names(path: Path) -> set[str]:
    out = set()
    for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Call):
            out.add(n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", ""))
    return out


def validator_problems(rows: list[Row], known: set[str], root: Path = ROOT) -> list[str]:
    problems = []
    for f, fn, call, _, origin, validator, _ in rows:
        where = f"{f} | {fn} | {call}"
        if origin in ("fixed", "package"):
            if validator != "-":
                problems.append(f"{where}: a {origin} row has no validator (write -)")
            continue
        if validator == "-" or validator not in known:
            problems.append(f"{where}: validator {validator!r} is not a function of the package")
        elif origin == "checked" and validator not in _called_names(root / f):
            problems.append(f"{where}: {validator} is never called in {f}")
    return problems


def test_every_listed_row_names_a_validator_that_exists_and_is_called():
    assert validator_problems(_exception_rows(), _known_functions()) == []


def test_the_validator_check_refuses_a_missing_or_uncalled_validator(tmp_path):
    (tmp_path / "m.py").write_text("def f(p):\n    return p\n", encoding="utf-8")
    known = {"f", "operator_dir"}
    base: Row = ("m.py", "g", ".read_text", 1, "checked", "f", "x")
    assert validator_problems([base], known, tmp_path) != []  # defined but never called in m.py
    assert (
        validator_problems([("m.py", "g", ".read_text", 1, "config", "nope", "x")], known, tmp_path)
        != []
    )
    assert (
        validator_problems([("m.py", "g", ".read_text", 1, "operator", "-", "x")], known, tmp_path)
        != []
    )
    assert (
        validator_problems([("m.py", "g", ".read_text", 1, "fixed", "f", "x")], known, tmp_path)
        != []
    )
    assert (
        validator_problems([("m.py", "g", ".read_text", 1, "fixed", "-", "x")], known, tmp_path)
        == []
    )
    (tmp_path / "m.py").write_text(
        "def f(p):\n    return p\n\n\ndef g(p):\n    return f(p)\n", encoding="utf-8"
    )
    assert validator_problems([base], known, tmp_path) == []


def test_nothing_in_the_listed_exceptions_names_a_file_that_is_gone():
    for f, *_ in _exception_rows():
        assert (ROOT / f).is_file(), f"{f} is listed but does not exist"


def test_the_seeded_bad_fixture_is_reported_function_by_function():
    text = (FIX / "pathguard_tripwire_bad.py").read_text(encoding="utf-8")
    problems = scan_source(text, "bad.py")
    lines = {int(p.split(":")[1]) for p in problems}
    tree = ast.parse(text)
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
        inside = {n for n in range(fn.lineno, fn.end_lineno + 1)}
        assert inside & lines, f"the tripwire missed {fn.name}"
    assert all(": the path is not a name assigned from a pathguard call" in p for p in problems)
    assert len(problems) >= 22, problems


def test_the_seeded_good_fixture_passes():
    text = (FIX / "pathguard_tripwire_good.py").read_text(encoding="utf-8")
    assert scan_source(text, "good.py") == []


@pytest.mark.parametrize(
    "code",
    [
        "def f(p):\n    p.read_text()\n",
        "def f():\n    open('x')\n",
        "def f(a):\n    (a / 'b').mkdir()\n",
        "def f(a):\n    import shutil\n    shutil.rmtree(a)\n",
        "def f(a, b):\n    a.replace(b)\n",
        "def f(a, b):\n    a.rename(b)\n",
        "def f(a):\n    a.rmdir()\n",
        "def f(a):\n    a.touch()\n",
        "def f(a, b):\n    a.symlink_to(b)\n",
        "def f(a):\n    a.chmod(0o600)\n",
        "def f(a):\n    a.write_bytes(b'x')\n",
        "def f(a):\n    a.write_text('x')\n",
        "def f(a):\n    a.open()\n",
        "def f(a, n):\n    p = pathguard.component(n, what='x')\n    p.read_text()\n",
        "def f(a, n):\n    pathguard.operator_text(n, what='x')\n    a.read_text()\n",
    ],
)
def test_one_line_plants_are_caught(code):
    assert scan_source(code, "plant.py"), code


@pytest.mark.parametrize(
    "code",
    [
        "def f(a):\n    return a.replace('x', 'y')\n",
        "def f(a):\n    return a.replace('x', 'y', 1)\n",
        "def f(a, n):\n    p = pathguard.join(a, n, what='x')\n    p.read_text()\n",
        "def f(a, n):\n    p = pathguard.inside(a, n, what='x')\n    p.read_text()\n",
        "def f(a):\n    p = pathguard.operator_dir(a, what='x')\n    p.rmdir()\n",
        "def f(a):\n    p = pathguard.operator_file(a, what='x')\n    p.chmod(0o600)\n",
        "def f(a, n):\n    p = confined(a, n)\n    p.read_text()\n",
    ],
)
def test_one_line_good_code_passes(code):
    assert scan_source(code, "plant.py") == [], code


@pytest.mark.parametrize(
    "code",
    [
        "import os\n\n\ndef f(p):\n    os.stat(p)\n",
        "import os\n\n\ndef f(p):\n    os.path.exists(p)\n",
        "import os\n\n\ndef f(p):\n    os.path.islink(p)\n",
        "import os\n\n\ndef f(p, q):\n    os.link(p, q)\n",
        "import os\n\n\ndef f(p, q):\n    os.symlink(p, q)\n",
        "import tempfile\n\n\ndef f(p):\n    tempfile.mkstemp(dir=p)\n",
        "import sqlite3\n\n\ndef f(p):\n    sqlite3.connect(p)\n",
        "def f(p):\n    p.exists()\n",
        "def f(p):\n    p.is_file()\n",
        "def f(p):\n    p.is_dir()\n",
        "def f(p):\n    p.is_symlink()\n",
        "def f(p):\n    p.stat()\n",
        "def f(p):\n    p.lstat()\n",
        "def f(p):\n    p.resolve()\n",
        "def f(p):\n    p.readlink()\n",
        "def f(p):\n    p.samefile(p)\n",
        "import os as o\n\n\ndef f(p):\n    o.remove(p)\n",
        "from os import remove as rm\n\n\ndef f(p):\n    rm(p)\n",
        "from os.path import exists as ex\n\n\ndef f(p):\n    ex(p)\n",
        "import shutil as sh\n\n\ndef f(p):\n    sh.rmtree(p)\n",
        "def f(p):\n    g = lambda: p.read_text()\n    return g()\n",
        "def f(p):\n    __import__('os').remove(p)\n",
        "def f(p, n):\n    q = pathguard.join(p, n, what='x')\n    return (lambda q: q.read_text())(p)\n",
    ],
)
def test_each_gap_in_the_first_scan_is_now_reported(code):
    assert scan_source(code, "gap.py"), code


@pytest.mark.parametrize(
    "code",
    [
        "import os\n\n\ndef f(p):\n    os.listdir(p)\n",
        "import os\n\n\ndef f(p):\n    os.scandir(p)\n",
        "import os\n\n\ndef f(p):\n    os.walk(p)\n",
        "import shutil\n\n\ndef f(p, q):\n    shutil.copy(p, q)\n",
        "import glob\n\n\ndef f(p):\n    glob.glob(p)\n",
        "import io\n\n\ndef f(p):\n    io.open(p)\n",
        "def f(p):\n    p.glob('*')\n",
        "def f(p):\n    p.rglob('*')\n",
        "def f(p):\n    p.iterdir()\n",
        "from pathlib import Path as P\n\n\ndef f(p):\n    P(p).read_text()\n",
        "def f(p):\n    return [q.read_text() for q in p]\n",
        "def f(p, n):\n    q = pathguard.join(p, n, what='x')\n    p.read_text()\n",
    ],
)
def test_pin_the_first_scan_already_reported_these_and_still_does(code):
    assert scan_source(code, "gap.py"), code


@pytest.mark.parametrize(
    "code",
    [
        "import os as o\n\n\ndef f(a, n):\n    p = pathguard.join(a, n, what='x')\n    o.remove(p)\n",
        "from os import remove as rm\n\n\ndef f(a, n):\n    p = pathguard.join(a, n, what='x')\n    rm(p)\n",
        "import os\n\n\ndef f(a, n):\n    p = pathguard.join(a, n, what='x')\n    os.stat(p)\n",
        "import os\n\n\ndef f(a, n):\n    p = pathguard.join(a, n, what='x')\n    os.link(p, p)\n",
        "def f(a, n):\n    p = pathguard.join(a, n, what='x')\n    return [q for q in p.iterdir()]\n",
        "def f(a, n):\n    p = pathguard.join(a, n, what='x')\n    return (lambda: p.read_text())()\n",
        "def f(m):\n    return m.group(1)\n",
        "import ast\n\n\ndef f(t):\n    return ast.walk(t)\n",
        "def f(d, name):\n    return d.resolve(name)\n",
    ],
)
def test_pin_the_guarded_twin_of_each_gap_passes(code):
    assert scan_source(code, "twin.py") == [], code


@pytest.mark.parametrize("code", ["def f(s, i):\n    s.touch(i)\n"])
def test_a_method_named_touch_on_a_non_path_name_is_not_a_hit(code):
    assert scan_source(code, "twin.py") == [], code
