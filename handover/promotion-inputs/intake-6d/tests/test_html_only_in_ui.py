"""Only ui.py builds HTML (portal plan B2.2). A plain AST scan of every .py under src/intake except ui.py. Forbidden, each a plain rule:
1. a string or bytes literal (f-string parts included) that contains the character <, unless its file lists that exact literal in the allowlist;
2. any use of the name Html except inside a type annotation or an import;
3. a class with str among its bases, unless a base is an enum class;
5. any use of a private name of the ui module through any alias (ui._x, import intake.ui as u, x = ui, intake.ui._x, getattr(ui, ...), import_module,
   sys.modules, from ui import _x) or of the
   private fields ._s and ._v; 6. the attributes __setattr__, __new__ and __class__ (ways round the sealed types);
4. any import of the html module (escape, unescape, parser), a markup or template library, or string.Template; a chr(60) call.
A scan of our own files, not a proof: a determined author can build the character some other way, which a reviewer reads for.
Regenerate the allowlist after a reviewed change with:  python tests/test_html_only_in_ui.py"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "intake"
ALLOWLIST = ROOT / "tests" / "fixtures" / "html_literal_allowlist.json"
BANNED_MODULES = frozenset(
    "html markupsafe jinja2 mako chevron pystache genshi django.template xml.sax.saxutils bleach lxml.html bs4 htmlmin yattag dominate airspeed".split()
)
ENUM_BASES = frozenset({"Enum", "StrEnum", "IntEnum", "Flag", "IntFlag", "ReprEnum"})
# existing modules that decode character references in INVOICE TEXT before matching numbers (html.unescape); they never build markup. Lead review row.
IMPORT_ALLOW = {"checks.py": {"html"}, "invoicecheck.py": {"html"}}
REASONS = {
    "core_copy/textnorm.py": "regular-expression text of a core copy; not markup",
    "budget.py": "less-than operators in sentences and messages; not markup",
    "model_anthropic.py": "prompt delimiter text sent to the AI model; not markup",
    "reader.py": "invoice delimiter text the reader refuses in files; not markup",
    "model_fake.py": "message text; not markup",
}


def _digest(lit: str | bytes) -> str:
    raw = lit if isinstance(lit, bytes) else lit.encode("utf-8", "surrogatepass")
    return hashlib.sha256(raw).hexdigest()[:16]


def _docstrings(tree: ast.AST) -> set[int]:
    out: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body:
            first = n.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                out.add(id(first.value))
    return out


def _annotation_ids(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for n in ast.walk(tree):
        anns = []
        if isinstance(n, ast.arg) and n.annotation:
            anns.append(n.annotation)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns:
            anns.append(n.returns)
        elif isinstance(n, ast.AnnAssign):
            anns.append(n.annotation)
        for a in anns:
            ids.update(id(x) for x in ast.walk(a))
    return ids


def literals_with_angle(source: str) -> list[str]:
    tree = ast.parse(source)
    doc = _docstrings(tree)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and id(n) not in doc:
            if isinstance(n.value, str) and "<" in n.value:
                out.append(n.value)
            elif isinstance(n.value, bytes) and b"<" in n.value:
                out.append(n.value)
    return out


def _ui_aliases(tree: ast.AST) -> set[str]:
    """Names that refer to the ui module: ``import intake.ui as u``, ``from intake import ui as U``, ``from . import ui``, plain ``ui``."""
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.update(a.asname for a in n.names if a.name.split(".")[-1] == "ui" and a.asname)
        elif isinstance(n, ast.ImportFrom) and (n.module or "") in ("", "intake"):
            out.update(a.asname or a.name for a in n.names if a.name == "ui")
    out |= {"ui"}
    for _ in range(3):  # x = ui; y = x; a, b = ui, 1; z: object = ui
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign):
                if isinstance(n.value, ast.Name) and n.value.id in out:
                    out.update(t.id for t in n.targets if isinstance(t, ast.Name))
                for t in n.targets:
                    if isinstance(t, (ast.Tuple, ast.List)) and isinstance(n.value, (ast.Tuple, ast.List)):
                        for tt, vv in zip(t.elts, n.value.elts, strict=False):
                            if isinstance(tt, ast.Name) and isinstance(vv, ast.Name) and vv.id in out:
                                out.add(tt.id)
            elif isinstance(n, ast.AnnAssign) and isinstance(n.value, ast.Name) and n.value.id in out and isinstance(n.target, ast.Name):
                out.add(n.target.id)
    return out


def _is_ui_ref(node: ast.AST, aliases: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in aliases
    # intake.ui used through the package name
    return isinstance(node, ast.Attribute) and node.attr == "ui" and isinstance(node.value, ast.Name) and node.value.id == "intake"


def scan(source: str, rel: str, allow: dict[str, list[str]]) -> list[str]:
    """Violations of rules 1 to 4 for one file's source text."""
    tree = ast.parse(source)
    bad: list[str] = []
    ok = set(allow.get(rel, []))
    for lit in literals_with_angle(source):
        if _digest(lit) not in ok:
            bad.append(f"rule 1: literal with '<' not on the allowlist: {str(lit)[:50]!r}")
    ann = _annotation_ids(tree)
    aliases = _ui_aliases(tree)
    uses_ui = any(
        (isinstance(n, ast.ImportFrom) and ((n.module or "").split(".")[-1] == "ui" or any(a.name == "ui" for a in n.names)))
        or (isinstance(n, ast.Import) and any(a.name.split(".")[-1] == "ui" for a in n.names))
        for n in ast.walk(tree)
    )
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id == "Html" and id(n) not in ann:
            bad.append(f"rule 2: Html used outside an annotation (line {n.lineno})")
        if isinstance(n, ast.Attribute) and n.attr == "Html" and id(n) not in ann:
            bad.append(f"rule 2: .Html used outside an annotation (line {n.lineno})")
        if isinstance(n, ast.ClassDef):
            names = {b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else "" for b in n.bases}
            if "str" in names and not names & ENUM_BASES:
                bad.append(f"rule 3: class {n.name} has str as a base (line {n.lineno})")
        mods: list[str] = []
        if isinstance(n, ast.Import):
            mods = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            mods = [n.module or ""]
            if n.module == "string" and any(a.name == "Template" for a in n.names):
                bad.append(f"rule 4: string.Template imported (line {n.lineno})")
        for m in mods:
            if m in IMPORT_ALLOW.get(rel, ()):
                continue
            if any(m == b or m.startswith(b + ".") for b in BANNED_MODULES):
                bad.append(f"rule 4: import of {m} (line {n.lineno})")
        if isinstance(n, ast.Attribute) and n.attr == "Template" and isinstance(n.value, ast.Name) and n.value.id == "string":
            bad.append(f"rule 4: string.Template (line {n.lineno})")
        if uses_ui and isinstance(n, ast.Attribute) and n.attr in ("_s", "_v"):
            bad.append(f"rule 5: private Html or Url field .{n.attr} (line {n.lineno})")
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "import_module" and n.args:
            a0 = n.args[0]
            if not (isinstance(a0, ast.Constant) and isinstance(a0.value, str)) or a0.value.split(".")[-1] == "ui":
                bad.append(f"rule 5: import_module of the ui module or of a computed name (line {n.lineno})")
        if isinstance(n, ast.Subscript) and getattr(n.value, "attr", "") == "modules":
            k = n.slice
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)) or k.value.split(".")[-1] == "ui":
                bad.append(f"rule 5: sys.modules lookup of the ui module or of a computed name (line {n.lineno})")
        if isinstance(n, ast.Attribute) and n.attr in (
            "__globals__",
            "__builtins__",
            "__code__",
            "__closure__",
            "__dict__",
            "__defaults__",
        ):
            bad.append(f"rule 6: .{n.attr} (a way into a function's namespace, line {n.lineno})")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "import_module"):
            a0 = n.args[0] if n.args else None
            if not (isinstance(a0, ast.Constant) and isinstance(a0.value, str)) or a0.value.split(".")[-1] == "ui":
                bad.append(f"rule 5: {n.func.id}() of the ui module or of a computed name (line {n.lineno})")
        if (
            isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") in ("get", "pop", "setdefault")
            and getattr(n.func.value, "attr", "") == "modules"
        ):
            bad.append(f"rule 5: sys.modules.{n.func.attr}(...) (line {n.lineno})")
        if isinstance(n, ast.ImportFrom) and n.module == "sys" and any(a.name == "modules" for a in n.names):
            bad.append(f"rule 5: from sys import modules (line {n.lineno})")
        if isinstance(n, ast.Attribute) and n.attr in ("__setattr__", "__new__", "__class__"):
            bad.append(f"rule 6: .{n.attr} (a way round the sealed types, line {n.lineno})")
        if isinstance(n, ast.Attribute) and n.attr.startswith("_") and _is_ui_ref(n.value, aliases):
            bad.append(f"rule 5: private name {n.attr} of the ui module (line {n.lineno})")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("getattr", "setattr", "hasattr", "vars") and n.args:
            if _is_ui_ref(n.args[0], aliases):
                bad.append(f"rule 5: {n.func.id}() on the ui module (line {n.lineno})")
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[-1] == "ui" and (n.module or "") != "ui":
            if any(a.name.startswith("_") or a.name == "*" for a in n.names):
                bad.append(f"rule 5: import of a private name or * from ui (line {n.lineno})")
        if isinstance(n, ast.ImportFrom) and n.module == "ui" and n.level and any(a.name.startswith("_") or a.name == "*" for a in n.names):
            bad.append(f"rule 5: import of a private name or * from ui (line {n.lineno})")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "chr" and n.args:
            a = n.args[0]
            if isinstance(a, ast.Constant) and a.value in (60, 0x3C):
                bad.append(f"rule 4: chr(60) (line {n.lineno})")
    return bad


def _files() -> list[Path]:
    return [p for p in sorted(SRC.rglob("*.py")) if p.name != "ui.py" or p.parent != SRC]


def _allow() -> dict[str, list[str]]:
    return {k: v["literals"] for k, v in json.loads(ALLOWLIST.read_text(encoding="utf-8")).items()}


def test_only_ui_py_builds_html():
    allow = _allow()
    bad = []
    for p in _files():
        rel = p.relative_to(SRC).as_posix()
        bad += [f"{rel}: {b}" for b in scan(p.read_text(encoding="utf-8"), rel, allow)]
    assert not bad, bad


def _ui_tree() -> ast.Module:
    return ast.parse((SRC / "ui.py").read_text(encoding="utf-8"))


def _h_calls(tree: ast.Module) -> list[ast.Call]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "h"]


def test_every_h_call_in_ui_py_takes_a_literal_template_with_quoted_attributes_and_no_stray_brace():
    import re

    calls = _h_calls(_ui_tree())
    assert len(calls) > 50
    slot = re.compile(r"\{\{|\}\}|\{([a-z][a-z0-9_]*)\}")
    for c in calls:
        arg = c.args[0]
        assert isinstance(arg, ast.Constant) and isinstance(arg.value, str), f"line {c.lineno}: the template is not a plain string literal"
        t = arg.value
        assert not re.search(r"[{}]", slot.sub("", t)), f"line {c.lineno}: stray brace"
        assert not re.search(r"\s[a-z-]+=\{", t), f"line {c.lineno}: unquoted attribute"
        names = {m.group(1) for m in slot.finditer(t) if m.group(1)}
        assert names == {k.arg for k in c.keywords}, f"line {c.lineno}: slots and values differ"


def test_every_href_and_action_slot_is_filled_from_the_link_gate():
    import re

    found = 0
    for c in _h_calls(_ui_tree()):
        t = c.args[0].value
        kw = {k.arg: k.value for k in c.keywords}
        for m in re.finditer(r'(?:href|action)="\{([a-z_]+)\}"', t):
            found += 1
            v = kw[m.group(1)]
            assert isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "_u", (
                f"line {c.lineno}: a link slot not filled by _u()"
            )
        assert not re.search(r"(?:href|action)=\"(?!\{)", t) or 'href="#main"' in t, f"line {c.lineno}: a literal link"
    assert found >= 10


def test_ui_py_has_no_style_attribute_and_no_unsafe_inline():
    src = (SRC / "ui.py").read_text(encoding="utf-8")
    assert " style=" not in src and "unsafe-inline" not in src


def test_the_scan_covers_every_module_and_ui_py_is_the_only_exception():
    names = {p.relative_to(SRC).as_posix() for p in _files()}
    assert "ui.py" not in names and "safe_text.py" in names and "routes.py" in names and "core_copy/textnorm.py" in names


def test_every_allowlist_row_has_a_reason_and_a_live_literal():
    data = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    for rel, row in data.items():
        assert row["reason"].strip(), rel
        live = {_digest(lit) for lit in literals_with_angle((SRC / rel).read_text(encoding="utf-8"))}
        assert set(row["literals"]) <= live, f"{rel}: stale allowlist entries (a reviewed literal was removed or changed)"


# ---- the scan must catch what it claims to catch (a scan that cannot fail is worthless)
@pytest.mark.parametrize(
    ("snippet", "rule"),
    [
        ('x = "<b>" + y', "rule 1"),
        ('x = f"<td>{y}</td>"', "rule 1"),
        ('x = b"<b>"', "rule 1"),
        ("from intake.ui import Html\nx = Html('a')", "rule 2"),
        ("from intake import ui\nx = ui.Html('a')", "rule 2"),
        ("class A(str):\n    pass", "rule 3"),
        ("import enum\nclass A(str, enum.Enum):\n    pass\nclass B(str):\n    pass", "rule 3"),
        ("import html\nx = html.escape('a')", "rule 4"),
        ("from html import escape", "rule 4"),
        ("import html.parser", "rule 4"),
        ("import jinja2", "rule 4"),
        ("from markupsafe import Markup", "rule 4"),
        ("from string import Template", "rule 4"),
        ("import string\nx = string.Template('a')", "rule 4"),
        ("x = chr(60)", "rule 4"),
        ("import xml.sax.saxutils", "rule 4"),
    ],
)
def test_scan_catches_each_forbidden_pattern(snippet, rule):
    assert any(b.startswith(rule) for b in scan(snippet, "x.py", {})), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        '"""docstring with <b> and < signs"""\nx = 1',
        "import enum\nclass A(str, enum.Enum):\n    pass",
        "from __future__ import annotations\nfrom intake.ui import Html\ndef f(x: Html) -> Html:\n    return x",
        "x = 1 < 2",
    ],
)
def test_scan_allows_the_permitted_patterns(snippet):
    assert scan(snippet, "x.py", {}) == []


def test_import_allowlist_is_narrow_and_live():
    for rel, mods in IMPORT_ALLOW.items():
        t = (SRC / rel).read_text(encoding="utf-8")
        assert mods == {"html"} and "html.unescape" in t and "escape(" not in t.replace("unescape(", "")
        assert scan("import html.parser", rel, {}), rel
    assert scan("import html", "ui_like.py", {}) != []


def test_allowlist_is_exact_per_literal():
    src = 'a = "x <= y"\nb = "x < y"'
    digest = _digest("x <= y")
    assert len(scan(src, "x.py", {"x.py": [digest]})) == 1
    assert scan(src, "other.py", {"x.py": [digest]}) != []


def _regen() -> None:  # pragma: no cover (maintenance helper)
    out = {}
    for p in _files():
        rel = p.relative_to(SRC).as_posix()
        lits = sorted({_digest(x) for x in literals_with_angle(p.read_text(encoding="utf-8"))})
        if lits:
            out[rel] = {
                "reason": REASONS.get(rel, "less-than operator, regular-expression text, SQL or message text; not markup"),
                "literals": lits,
            }
    ALLOWLIST.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    _regen()


@pytest.mark.parametrize(
    "snippet",
    [
        "from intake import ui\nx = ui._mk('a')",
        "from intake import ui\nx = ui._KEY",
        "from intake.ui import _mk",
        "from . import ui\ny = ui._esc",
        "from intake import ui\nx = obj._s",
        "from intake import ui\nx = obj._v",
    ],
)
def test_scan_catches_private_ui_names(snippet):
    assert any(b.startswith("rule 5") for b in scan(snippet, "x.py", {})), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "import intake.ui as u\nx = u._mk('a')",
        "import intake.ui\nx = intake.ui._mk('a')",
        "from intake import ui as U\nx = U._KEY",
        "from . import ui as U\nx = U._esc",
        "from intake import ui\nx = getattr(ui, '_mk')",
        "import intake.ui as u\nx = getattr(u, name)",
        "from intake.ui import *",
        "from .ui import _mk",
        "from intake import ui\nobject.__setattr__(x, '_s', 'y')",
        "x = y.__new__(z)",
        "x = y.__class__",
    ],
)
def test_scan_catches_the_alias_and_sealed_type_bypasses(snippet):
    assert any(b.startswith(("rule 5", "rule 6")) for b in scan(snippet, "x.py", {})), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "from intake import ui\nx = ui.text('a')",
        "import intake.ui as u\nx = u.url('home')",
        "from intake.ui import text, h\nx = text('a')",
        "class A:\n    _s = 1\nx = A()._s",
    ],
)
def test_scan_allows_the_public_api_of_ui(snippet):
    assert scan(snippet, "x.py", {}) == []


def _rebound(fn: ast.FunctionDef | None, name: str) -> bool:
    """True if the name is bound in the function in any way other than a plain assignment (augmented assignment, loop, walrus, parameter, with,
    import, comprehension target, tuple target, delete)."""
    if fn is None:
        return False
    if any(a.arg == name for a in (*fn.args.args, *fn.args.kwonlyargs, *fn.args.posonlyargs)):
        return True
    for n in ast.walk(fn):
        if isinstance(n, (ast.AugAssign, ast.AnnAssign)) and isinstance(n.target, ast.Name) and n.target.id == name:
            return True
        if isinstance(n, (ast.For, ast.comprehension)) and any(isinstance(t, ast.Name) and t.id == name for t in ast.walk(n.target)):
            return True
        if isinstance(n, ast.NamedExpr) and n.target.id == name:
            return True
        if isinstance(n, ast.With) and any(
            i.optional_vars is not None and any(isinstance(t, ast.Name) and t.id == name for t in ast.walk(i.optional_vars))
            for i in n.items
        ):
            return True
        if isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.asname or a.name).split(".")[0] == name for a in n.names):
            return True
        if isinstance(n, ast.Assign) and any(
            not isinstance(t, ast.Name) and any(isinstance(x, ast.Name) and x.id == name for x in ast.walk(t)) for t in n.targets
        ):
            return True  # tuple or starred targets
        if isinstance(n, ast.Delete) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return True
    return False


def _safe_markup_expr(a: ast.AST, fn: ast.FunctionDef | None, depth: int = 0) -> bool:
    """A literal, a constant choice, a known-safe call, or a name whose only binding in the same function is a plain assignment of such an
    expression (escaped parts only). A ``.join`` is trusted only as ``_esc(sep).join(_esc(x) for ...)``."""
    safe_calls = {"_tone", "_shown", "_esc"}
    if isinstance(a, ast.Constant):
        return isinstance(a.value, str)
    if isinstance(a, ast.IfExp):
        return _safe_markup_expr(a.body, fn, depth) and _safe_markup_expr(a.orelse, fn, depth)
    if isinstance(a, ast.JoinedStr):  # an f-string whose every inserted part is a safe expression
        return all(_safe_markup_expr(v.value, fn, depth) for v in a.values if isinstance(v, ast.FormattedValue))
    if isinstance(a, ast.Call):
        f = a.func
        if isinstance(f, ast.Name) and f.id in safe_calls:
            return True
        if (
            isinstance(f, ast.Attribute)
            and f.attr == "join"
            and isinstance(f.value, ast.Call)
            and getattr(f.value.func, "id", "") == "_esc"
        ):
            return (
                len(a.args) == 1
                and isinstance(a.args[0], ast.GeneratorExp)
                and isinstance(a.args[0].elt, ast.Call)
                and getattr(a.args[0].elt.func, "id", "") == "_esc"
            )
        if (
            isinstance(f, ast.Attribute) and f.attr == "sub" and getattr(f.value, "id", "") == "_SLOT"
        ):  # h(): the slot substitution of a literal template
            return True
        return False
    if isinstance(a, ast.Name) and a.id == "_CSS":  # the style sheet read from the package at import (checked for markup there)
        return True
    if isinstance(a, ast.Name) and fn is not None and depth < 3:
        if _rebound(fn, a.id):
            return False
        assigns = [
            n.value for n in ast.walk(fn) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == a.id for t in n.targets)
        ]
        return bool(assigns) and all(_safe_markup_expr(v, fn, depth + 1) for v in assigns)
    return False


def test_every_mk_argument_in_ui_py_is_built_from_literals_escaped_parts_or_known_safe_calls():
    tree = _ui_tree()
    funcs = {id(c): f for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) for c in ast.walk(f)}
    n_checked = 0
    for c in ast.walk(tree):
        if not (isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "_mk"):
            continue
        n_checked += 1
        fn = funcs.get(id(c))
        if fn is not None and fn.name == "_mk":
            continue  # the constructor wrapper itself
        assert _safe_markup_expr(c.args[0], fn), f"line {c.lineno}: _mk() takes something that is not built from safe parts"
    assert n_checked > 30


@pytest.mark.parametrize(
    "src",
    [
        "def f(x):\n    return _mk(x)",
        "def f(x):\n    y = x\n    return _mk(y)",
        "def f(x):\n    y = f'a{x}'\n    return _mk(y)",
        "def f(x):\n    return _mk(x + 'a')",
    ],
)
def test_the_mk_checker_refuses_unsafe_arguments(src):
    fn = ast.parse(src).body[0]
    call = next(n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_mk")
    assert not _safe_markup_expr(call.args[0], fn)


def test_the_mk_checker_accepts_the_real_patterns():
    for src in (
        "def f(x):\n    return _mk('a')",
        "def f(x):\n    t = 'a' if x else 'b'\n    return _mk(t)",
        "def f(x):\n    lab = f'a {_esc(x)}'\n    return _mk(lab)",
        "def f(x):\n    return _mk(_tone(x))",
    ):
        fn = ast.parse(src).body[0]
        call = next(n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_mk")
        assert _safe_markup_expr(call.args[0], fn), src


@pytest.mark.parametrize(
    "snippet",
    [
        "from intake import ui\nx = ui\ny = x._mk('a')",
        "from intake import ui\nx = ui\ny = x\nz = y._KEY",
        "import importlib\nm = importlib.import_module('intake.ui')",
        "import importlib\nm = importlib.import_module(name)",
        "import sys\nm = sys.modules['intake.ui']",
        "import sys\nm = sys.modules[name]",
    ],
)
def test_scan_catches_assignment_aliases_import_module_and_sys_modules(snippet):
    assert any(b.startswith("rule 5") for b in scan(snippet, "x.py", {})), snippet


def test_scan_allows_ordinary_import_module_and_sys_modules_use():
    assert scan("import importlib\nm = importlib.import_module('json')", "x.py", {}) == []
    assert scan("import sys\nm = sys.modules['json']", "x.py", {}) == []


@pytest.mark.parametrize(
    "src",
    [
        "def f(x):\n    y = 'a'\n    y += x\n    return _mk(y)",
        "def f(x):\n    y = 'a'\n    for y in x:\n        pass\n    return _mk(y)",
        "def f(x):\n    y = 'a'\n    (y := x)\n    return _mk(y)",
        "def f(x):\n    y = 'a'\n    y, z = x, 1\n    return _mk(y)",
        "def f(x):\n    y = 'a'\n    with x as y:\n        pass\n    return _mk(y)",
        "def f(x):\n    return _mk(_esc(x).join(x))",
        "def f(x):\n    return _mk(_esc(x).join([x]))",
        "def f(x):\n    return _mk(x)",
    ],
)
def test_the_mk_checker_refuses_every_other_way_of_binding_the_argument(src):
    fn = ast.parse(src).body[0]
    call = next(n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_mk")
    assert not _safe_markup_expr(call.args[0], fn)


def test_the_mk_checker_accepts_the_escaped_join_pattern():
    fn = ast.parse("def f(x, sep):\n    return _mk(_esc(sep).join(_esc(p) for p in x))").body[0]
    call = next(n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_mk")
    assert _safe_markup_expr(call.args[0], fn)


@pytest.mark.parametrize(
    "snippet",
    [
        "x = f.__globals__",
        "x = f.__builtins__",
        "x = f.__code__",
        "x = f.__closure__",
        "x = f.__dict__",
        "x = __import__('intake.ui')",
        "from importlib import import_module\nm = import_module('intake.ui')",
        "from importlib import import_module\nm = import_module(name)",
        "import sys\nm = sys.modules.get('intake.ui')",
        "import sys\nm = sys.modules.pop('intake.ui')",
        "from sys import modules\nm = modules['intake.ui']",
        "from intake import ui\na, b = ui, 1\nx = a._mk('x')",
        "from intake import ui\nz: object = ui\nx = z._KEY",
    ],
)
def test_scan_catches_the_namespace_and_alias_bypasses_of_round_five(snippet):
    assert any(b.startswith(("rule 5", "rule 6")) for b in scan(snippet, "x.py", {})), snippet
