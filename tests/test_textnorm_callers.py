"""The caller rule of the text fold, as a lint over ``src/hadavin_sdk/**`` (outside ``guard/textnorm.py``).

An ALLOW caller calls ``allow_equal`` and lets ANY exception propagate to its own refusing top level; a DENY caller treats any
``TextnormError`` as REFUSE. The lint reports, by AST:

(a) a handler of ``Exception``, ``BaseException``, ``ValueError``, ``TypeError``, ``AttributeError`` or a bare ``except`` whose ``try``
    body calls a textnorm name (the broad handler swallows a refusal);
(b) a handler that names ``TextnormError`` or one of its subclasses (an ALLOWLIST: the enclosing function must be in ``REFUSAL_HANDLERS``),
    also as a tuple, a dotted name, a module alias, a name alias, or ``contextlib.suppress(...)``.

The banned class names are built at TEST time from ``textnorm.__all__`` (every class that is a subclass of ``TextnormError``, plus
``TextnormError``), so a new subclass is banned without a lint edit. ``REFUSAL_HANDLERS`` exempts ban (b) only. The lint catches the named
shapes and is not a proof: other swallowing patterns are not detected. The nine fixture rows below are the pin (8 reported, 1 allowed).
"""

import ast
import inspect
from pathlib import Path

import pytest

from hadavin_sdk.guard import textnorm

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "hadavin_sdk"
# ``path-below-hadavin_sdk::function``. UNVERIFIED names: the P2d-2 withhold function and the P5a closed-code mapper are named by the
# authors of those packages; this list is edited when they land.
REFUSAL_HANDLERS = frozenset(
    {
        "guard/redact.py::check_lookalike",
        "guard/redact.py::_withhold",
        "runtime/closed_codes.py::textnorm_code",
    }
)
BROAD = frozenset({"Exception", "BaseException", "ValueError", "TypeError", "AttributeError"})
BANNED = frozenset(
    {"TextnormError"}
    | {
        name
        for name in textnorm.__all__
        if inspect.isclass(getattr(textnorm, name))
        and issubclass(getattr(textnorm, name), textnorm.TextnormError)
    }
)
TEXTNORM_NAMES = frozenset(textnorm.__all__)


class _Names:
    """What the module imports from textnorm: the module aliases and the name aliases."""

    def __init__(self, tree):
        self.modules = {"textnorm"}
        self.names = {}  # local name -> textnorm name
        self.suppress = {"suppress"}
        self.contextlib = {"contextlib"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.endswith("textnorm"):
                        self.modules.add(a.asname or a.name.split(".")[-1])
                    if a.name == "contextlib":
                        self.contextlib.add(a.asname or "contextlib")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for a in node.names:
                    if mod.endswith("textnorm"):
                        self.names[a.asname or a.name] = a.name
                    elif a.name == "textnorm":
                        self.modules.add(a.asname or "textnorm")
                    elif mod == "contextlib" and a.name == "suppress":
                        self.suppress.add(a.asname or "suppress")

    def textnorm_name(self, node):
        """The textnorm name an expression refers to, or None."""
        if isinstance(node, ast.Name):
            return self.names.get(node.id)
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in self.modules
        ):
            return node.attr
        return None

    def exception_names(self, node):
        """Every name a handler type or a suppress argument spells, textnorm names resolved, plain builtin names as written."""
        if node is None:
            return {"<bare>"}
        if isinstance(node, ast.Tuple):
            return (
                set().union(*(self.exception_names(e) for e in node.elts)) if node.elts else set()
            )
        resolved = self.textnorm_name(node)
        if resolved:
            return {resolved}
        if isinstance(node, ast.Name):
            return {node.id}
        return set()


def lint_source(source, rel="x.py", handlers=REFUSAL_HANDLERS):
    """The findings (``rel:line: reason``) of one module's source."""
    tree = ast.parse(source)
    names = _Names(tree)
    found = []

    def calls_textnorm(body):
        return any(
            isinstance(n, ast.Call) and names.textnorm_name(n.func) in TEXTNORM_NAMES
            for stmt in body
            for n in ast.walk(stmt)
        )

    def visit(node, function):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function = node.name
        if isinstance(node, ast.Try):
            for h in node.handlers:
                spelled = names.exception_names(h.type)
                if spelled & BANNED and f"{rel}::{function}" not in handlers:
                    found.append(
                        f"{rel}:{h.lineno}: a handler names {sorted(spelled & BANNED)} outside REFUSAL_HANDLERS"
                    )
                if (spelled & BROAD or "<bare>" in spelled) and calls_textnorm(node.body):
                    found.append(f"{rel}:{h.lineno}: a broad handler around a textnorm call")
        if isinstance(node, ast.Call):
            f = node.func
            is_suppress = (isinstance(f, ast.Name) and f.id in names.suppress) or (
                isinstance(f, ast.Attribute)
                and f.attr == "suppress"
                and isinstance(f.value, ast.Name)
                and f.value.id in names.contextlib
            )
            if is_suppress:
                spelled = (
                    set().union(*(names.exception_names(a) for a in node.args))
                    if node.args
                    else set()
                )
                if spelled & BANNED and f"{rel}::{function}" not in handlers:
                    found.append(
                        f"{rel}:{node.lineno}: suppress({sorted(spelled & BANNED)}) outside REFUSAL_HANDLERS"
                    )
        for child in ast.iter_child_nodes(node):
            visit(child, function)

    visit(tree, "<module>")
    return found


ROWS = [
    (
        "1 TextnormError",
        "from hadavin_sdk.guard.textnorm import TextnormError, fold\ndef f(x):\n    try:\n        fold(x)\n    except TextnormError:\n        pass\n",
        True,
    ),
    (
        "2 TextTooLong",
        "from hadavin_sdk.guard.textnorm import TextTooLong, fold\ndef f(x):\n    try:\n        fold(x)\n    except TextTooLong:\n        pass\n",
        True,
    ),
    (
        "3 tuple",
        "from hadavin_sdk.guard.textnorm import NotText, fold\ndef f(x):\n    try:\n        fold(x)\n    except (NotText, KeyError):\n        pass\n",
        True,
    ),
    (
        "4 dotted",
        "from hadavin_sdk.guard import textnorm\ndef f(x):\n    try:\n        textnorm.fold(x)\n    except textnorm.NotText:\n        pass\n",
        True,
    ),
    (
        "5 module alias",
        "import hadavin_sdk.guard.textnorm as tn\ndef f(x):\n    try:\n        tn.fold(x)\n    except tn.FoldNotConverged:\n        pass\n",
        True,
    ),
    (
        "6 name alias",
        "from hadavin_sdk.guard.textnorm import UnidataMismatch as Gone, fold\ndef f(x):\n    try:\n        fold(x)\n    except Gone:\n        pass\n",
        True,
    ),
    (
        "7 suppress",
        "import contextlib\nfrom hadavin_sdk.guard.textnorm import TextnormError, fold\ndef f(x):\n    with contextlib.suppress(TextnormError):\n        fold(x)\n",
        True,
    ),
    (
        "8 broad handler",
        "from hadavin_sdk.guard.textnorm import fold\ndef f(x):\n    try:\n        fold(x)\n    except Exception:\n        pass\n",
        True,
    ),
    (
        "9 listed function",
        "from hadavin_sdk.guard.textnorm import TextnormError, fold\ndef check_lookalike(x):\n    try:\n        fold(x)\n    except TextnormError:\n        return 1\n",
        False,
    ),
]


@pytest.mark.parametrize(("name", "source", "reported"), ROWS, ids=[r[0] for r in ROWS])
def test_fixture_row(name, source, reported):
    findings = lint_source(source, rel="guard/redact.py" if "listed" in name else "x.py")
    assert bool(findings) is reported, f"{name}: {findings}"


def test_the_nine_rows_are_eight_reported_and_one_allowed():
    assert len(ROWS) == 9 and sum(r[2] for r in ROWS) == 8


def test_refusal_handlers_has_three_entries_and_the_banned_names_follow_textnorm():
    assert len(REFUSAL_HANDLERS) == 3
    assert BANNED == {
        "TextnormError",
        "TextTooLong",
        "NotText",
        "UnidataMismatch",
        "FoldNotConverged",
        "EmptyView",
        "ViewTooShort",
        "CoverageRefused",
    }, "a new TextnormError subclass: it is banned automatically; update this list on purpose"


def test_the_source_tree_has_no_handler_of_a_textnorm_refusal_outside_the_list():
    findings = []
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        if rel == "guard/textnorm.py":
            continue
        findings += lint_source(path.read_text(encoding="utf-8"), rel=rel)
    assert not findings, "\n".join(findings)
