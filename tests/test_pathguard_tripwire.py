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

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "hadavin_sdk"
FIX = Path(__file__).resolve().parent / "fixtures"

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
}
# ``Path.replace(target)`` and ``Path.rename(target)`` take ONE argument; ``str.replace(old, new)`` takes two or more.
BANNED_ONE_ARG = {"replace", "rename"}
GUARD_FUNCTIONS = {"join", "inside", "operator_dir", "operator_file", "confined"}
ORIGINS = {"operator", "config", "fixed", "package", "checked"}
OS_ONE_PATH = {
    "open",
    "remove",
    "listdir",
    "scandir",
    "walk",
    "makedirs",
    "mkdir",
    "rmdir",
    "unlink",
}
OS_TWO_PATHS = {"replace", "rename"}


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
    """Every node of ``scope`` except the insides of nested functions (they are scopes of their own)."""
    todo = list(ast.iter_child_nodes(scope))
    while todo:
        node = todo.pop()
        yield node
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            todo.extend(ast.iter_child_nodes(node))


def _assignments(func: ast.AST) -> dict[str, list[tuple[int, bool]]]:
    """name -> [(line, assigned from a pathguard call)], for plain-name targets (also ``with ... as``, ``for``, walrus)."""
    found: dict[str, list[tuple[int, bool]]] = {}

    def add(target: ast.AST, line: int, guarded: bool) -> None:
        if isinstance(target, ast.Name):
            found.setdefault(target.id, []).append((line, guarded))
        elif isinstance(target, ast.Tuple | ast.List):
            for t in target.elts:
                add(t, line, False)

    for node in _own_nodes(func):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                add(t, node.lineno, _is_guard_call(node.value))
        elif (isinstance(node, ast.AnnAssign) and node.value is not None) or isinstance(
            node, ast.NamedExpr
        ):
            add(node.target, node.lineno, _is_guard_call(node.value))
        elif isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
            add(node.target, node.target.lineno, False)
        elif isinstance(node, ast.With | ast.AsyncWith):
            for item in node.items:
                if item.optional_vars is not None:
                    add(item.optional_vars, node.lineno, False)
    return found


def _guarded(arg: ast.AST, line: int, assigned: dict[str, list[tuple[int, bool]]]) -> bool:
    if not isinstance(arg, ast.Name):
        return False
    earlier = [(ln, ok) for ln, ok in assigned.get(arg.id, []) if ln <= line]
    return bool(earlier) and max(earlier)[1]


def _banned(call: ast.Call) -> tuple[str, list[ast.AST]] | None:
    """(printed name, the path arguments that must be guarded) when ``call`` is a banned file operation."""
    f = call.func
    if isinstance(f, ast.Name) and f.id == "open":
        return "open", call.args[:1]
    if isinstance(f, ast.Attribute):
        if (
            isinstance(f.value, ast.Name)
            and f.value.id == "os"
            and f.attr in OS_ONE_PATH | OS_TWO_PATHS
        ):
            return f"os.{f.attr}", call.args[:2] if f.attr in OS_TWO_PATHS else call.args[:1]
        if isinstance(f.value, ast.Name) and f.value.id == "shutil":
            return f"shutil.{f.attr}", list(call.args)
        if f.attr in BANNED_METHODS:
            return f".{f.attr}", [f.value]
        if f.attr in BANNED_ONE_ARG and len(call.args) == 1 and not call.keywords:
            return f".{f.attr}", [f.value]
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
    hits = []
    for qualname, scope in _scopes(tree):
        assigned = _assignments(scope)
        for node in _own_nodes(scope):
            found = _banned(node) if isinstance(node, ast.Call) else None
            if found is None:
                continue
            name, args = found
            if not args or not all(_guarded(a, node.lineno, assigned) for a in args):
                hits.append((filename, qualname, node.lineno, name))
    return hits


def scan_source(source: str, filename: str) -> list[str]:
    """``scan_hits`` as ``file:line: call: reason`` text."""
    return [
        f"{f}:{line}: {call}: the path is not a name assigned from a pathguard call (in {fn})"
        for f, fn, line, call in scan_hits(source, filename)
    ]


EXCEPTIONS = FIX / "pathguard_exceptions.txt"


def _targets() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if p.name != "pathguard.py" or p.parent != SRC)


def _exception_rows() -> list[tuple[str, str, str, str]]:
    rows = []
    for number, line in enumerate(EXCEPTIONS.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(" | ")]
        assert len(parts) == 4 and all(parts), (
            f"{EXCEPTIONS.name}:{number}: need file | function | origin | reason"
        )
        assert parts[2] in ORIGINS, (
            f"{EXCEPTIONS.name}:{number}: origin must be one of {sorted(ORIGINS)}"
        )
        rows.append((parts[0], parts[1], parts[2], parts[3]))
    return rows


def _all_hits() -> list[tuple[str, str, int, str]]:
    hits: list[tuple[str, str, int, str]] = []
    for path in _targets():
        hits += scan_hits(path.read_text(encoding="utf-8"), path.relative_to(ROOT).as_posix())
    return hits


def test_no_file_operation_in_the_package_works_on_an_unchecked_path_unless_listed_with_a_reason():
    listed = {(f, fn) for f, fn, _, _ in _exception_rows()}
    problems = [
        f"{f}:{line}: {call} in {fn}: not guarded and not listed in {EXCEPTIONS.name}"
        for f, fn, line, call in _all_hits()
        if (f, fn) not in listed
    ]
    assert problems == [], "unchecked paths:\n" + "\n".join(problems)


def test_every_listed_exception_still_matches_a_hit_so_the_list_cannot_go_stale():
    hit_pairs = {(f, fn) for f, fn, _, _ in _all_hits()}
    stale = [f"{f} | {fn}" for f, fn, _, _ in _exception_rows() if (f, fn) not in hit_pairs]
    assert stale == [], "listed exceptions with no unguarded file operation left:\n" + "\n".join(
        stale
    )


def test_the_exception_list_has_no_duplicate_rows():
    keys = [(f, fn) for f, fn, _, _ in _exception_rows()]
    assert len(keys) == len(set(keys)), "a function is listed twice"


def test_nothing_in_the_listed_exceptions_names_a_file_that_is_gone():
    for f, _, _, _ in _exception_rows():
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
