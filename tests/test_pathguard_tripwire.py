"""A tripwire for the class "a file operation on a path nobody checked" in the K1b code and the command line.

The scan reads the source of ``src/hadavin_sdk/k1b/*.py`` and ``src/hadavin_sdk/cli.py`` (the AST, nothing is run). Inside
each function it flags a banned call (``open``, ``os.open``, ``os.replace``, ``os.remove``, ``os.rename``, ``os.listdir``,
``os.scandir``, ``os.walk``, ``os.makedirs``, ``os.mkdir``, ``os.rmdir``, ``os.unlink``, ``shutil.*``, and the methods
``.read_bytes .read_text .write_bytes .write_text .open .mkdir .iterdir .glob .rglob .unlink``) unless every path argument
(the receiver for a method, the first argument for ``open`` and ``os.*`` calls that take one path, every argument for
``os.replace``, ``os.rename`` and ``shutil.*``) is a plain NAME whose latest earlier assignment in the same function is a
call ``pathguard.<something>(...)``. That is the only allow rule: there is no comment switch.

Limits, stated plainly: the scan follows one function only. A path passed in from another function is not trusted, so the
function that receives it must re-check it; a name assigned in a branch that does not run before the call is not seen;
a path built from a guarded one by ``/`` or ``.parent`` is NOT trusted and needs its own ``pathguard`` call. It cannot see a
file operation made through a library call (``json.load(open_file)``, ``Path.touch``). The two seeded fixtures in
``tests/fixtures`` prove the scan reports bad code and lets good code pass.
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
}
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
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "pathguard"
    )


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
    return None


def scan_source(source: str, filename: str) -> list[str]:
    """Every banned call whose path is not guarded, as ``file:line: call: reason``."""
    tree = ast.parse(source, filename=filename)
    problems = []
    scopes: list[ast.AST] = [
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
    ]
    scopes.append(tree)  # module level code
    for scope in scopes:
        assigned = _assignments(scope)
        for node in _own_nodes(scope):
            hit = _banned(node) if isinstance(node, ast.Call) else None
            if hit is None:
                continue
            name, args = hit
            if not args or not all(_guarded(a, node.lineno, assigned) for a in args):
                problems.append(
                    f"{filename}:{node.lineno}: {name}: the path is not a name assigned from a pathguard call"
                )
    return problems


def _targets() -> list[Path]:
    return sorted((SRC / "k1b").glob("*.py")) + [SRC / "cli.py"]


def test_no_file_operation_in_k1b_or_the_cli_works_on_an_unchecked_path():
    problems: list[str] = []
    for path in _targets():
        problems += scan_source(
            path.read_text(encoding="utf-8"), f"{path.relative_to(ROOT).as_posix()}"
        )
    assert problems == [], "unchecked paths:\n" + "\n".join(problems)


def test_the_seeded_bad_fixture_is_reported_function_by_function():
    text = (FIX / "pathguard_tripwire_bad.py").read_text(encoding="utf-8")
    problems = scan_source(text, "bad.py")
    lines = {int(p.split(":")[1]) for p in problems}
    tree = ast.parse(text)
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
        inside = {n for n in range(fn.lineno, fn.end_lineno + 1)}
        assert inside & lines, f"the tripwire missed {fn.name}"
    assert all(": the path is not a name assigned from a pathguard call" in p for p in problems)
    assert len(problems) >= 11, problems


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
    ],
)
def test_one_line_plants_are_caught(code):
    assert scan_source(code, "plant.py"), code
