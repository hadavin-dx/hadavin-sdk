"""Table of every place where the SDK builds a ``ConfigError``, rebuilt from the source text and checked in CI.

The table (``tests/data/config_error_sites.csv``) has three columns: ``site``, ``class`` and ``reason``. ``site`` is
``<file>::<symbol>::<hash>::<k>`` with no line number. ``class`` is the reviewed class: ``LITERAL`` (words we wrote),
``OPERATOR`` (a value an operator typed in configuration) or ``FOREIGN`` (text of an exception, a response, a document or
a model). The automatic values (``kind``, ``auto_class``, ``auto_reason``) are computed by ``scan()`` on every run and are
never stored, so a person who edits the table cannot weaken a lock.

Standard library only. This tool never imports the SDK and never runs repository code: it only parses text.

What the table proves, and what it does not (stated plainly). A row's key hashes the construction node only (plus, for
constructions with identical text in one function, what guards them). So the table proves that every construction CALL SITE
was seen and given a reviewed class. It does not prove the claim in an OPERATOR or FOREIGN reason about the PRODUCERS of the
values that reach the site (who builds the string, what it holds): a later edit to a producer, in another function or file, does
not change the key and does not fail the check. The reasons are a reviewer's statement at the time of review, not a checked
property; P5b3 must guard the producers (module-wide, not only the constructor arguments).

What the scan does not detect: ``type(x)(...)``, ``getattr(mod, "ConfigError")(...)``, a raiser helper called as a method
(``self.f(...)``, ``obj.f(...)``), a relay of exception text that is not a construction (``out.append(str(exc))`` where ``exc`` is a
site class caught in a handler) and a non-exception foreign value (document or model text) passed into a raiser helper. A site
class used as a value (``kind = ConfigError``, ``raise_as(ConfigError, ...)``, ``functools.partial(ConfigError, ...)``) is refused
with ``SitesError``: the name may only be called, caught, tested with ``isinstance``/``issubclass``, named as a base or an
annotation, imported, or raised bare. Only ``ConfigError`` and its subclasses are in scope; other exception types reach the screen
through an existing site. Taint does not cross function calls, aliases of the ``traceback`` module (``import traceback as tb``) and
does not cross into an inner ``def``, ``lambda`` or class body. A gap in taint never lets a row pass: it lands in ``unproven-origin``
and needs a person.

Site classes: the body may hold a docstring, ``pass``, plain class fields, ``__init__`` and ``__reduce__``. ``__init__`` holds only
assignments to attributes of ``self`` and one ``super().__init__(<expr>)`` statement; any route that rewrites ``args`` (``setattr``,
``__dict__``, ``vars``, ``add_note``, ``.args``) is refused. ``__reduce__`` must be exactly ``return (type(self), (self.attr, ...))``.
``__reduce_ex__``, ``__getstate__`` and ``__setstate__`` are refused.

Command line: ``python -m tools.gen_config_error_sites --check|--write|--review [--root PATH] [--csv PATH]``.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

PACKAGE_DIR = "src/hadavin_sdk"
CSV_PATH = "tests/data/config_error_sites.csv"
BASE_CLASS = "ConfigError"
BASE_CLASS_BASE = "ValueError"
HASH_LEN = 16
CLASSES = ("LITERAL", "OPERATOR", "FOREIGN")
COLUMNS = ("site", "class", "reason")
REASON_MAX = 200
UNPROVEN = "unproven-origin"
EXC_VAR = "exception-variable"
CONSTANT = "constant"
MUTATORS = ("append", "extend", "insert", "add", "update", "appendleft")
TAINT_CALLS = ("exc_info", "exception", "format_exc", "format_exception", "format_exception_only")
TAINT_MODULES = ("sys", "traceback")
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)
# The one method besides ``__init__`` a site class may define: ``__reduce__`` with the single shape ``return (type(self),
# (self.attr, ...))`` (see ``_check_reduce``). ``__reduce_ex__``, ``__getstate__`` and ``__setstate__`` are refused: they can change
# what a copy or an unpickled object prints.
REDUCE_DEF = "__reduce__"
# Names an ``__init__`` must not use: each is a route to change ``args`` (and so ``str(exc)``) or the instance behind ``super()``.
INIT_BAD_NAMES = (
    "setattr",
    "delattr",
    "vars",
    "globals",
    "locals",
    "exec",
    "eval",
    "compile",
    "object",
)
INIT_BAD_ATTRS = (
    "args",
    "__dict__",
    "__setattr__",
    "__class__",
    "add_note",
    "__notes__",
    "__reduce__",
)
# Class names whose attribute access is not a use of the class as a value, apart from these dunder attributes.
CLASS_ATTR_OK = ("__name__", "__qualname__", "__module__", "__doc__")
# Statements and expressions whose header guards what they contain; a duplicated construction is told apart by them.
GUARD_FIELDS = {
    "If": ("test",),
    "While": ("test",),
    "For": ("target", "iter"),
    "AsyncFor": ("target", "iter"),
    "With": ("items",),
    "AsyncWith": ("items",),
    "ExceptHandler": ("type", "name"),
    "IfExp": ("test",),
    "Match": ("subject",),
    "match_case": ("pattern", "guard"),
    "comprehension": ("target", "iter", "ifs"),
}


class SitesError(Exception):
    """Every refusal of this tool. A refusal always means the check fails."""


@dataclass(frozen=True)
class Site:
    file: str
    symbol: str
    kind: str
    snippet_hash: str
    k: int
    auto_class: str
    auto_reason: str
    lineno: int
    origin_hints: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.file}::{self.symbol}::{self.snippet_hash}::{self.k}"


@dataclass(frozen=True)
class Row:
    site: str
    klass: str  # the CSV column ``class``
    reason: str


@dataclass(frozen=True)
class Report:
    unclassified: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    blank_class: list[str] = field(default_factory=list)
    locked_downgrade: list[str] = field(default_factory=list)
    wrong_literal: list[str] = field(default_factory=list)
    missing_reason: list[str] = field(default_factory=list)
    rows: int = 0
    per_class: tuple[tuple[str, int], ...] = ()
    locked: int = 0

    @property
    def ok(self) -> bool:
        return not (
            self.unclassified
            or self.stale
            or self.blank_class
            or self.locked_downgrade
            or self.wrong_literal
            or self.missing_reason
        )

    def render(self) -> str:
        lines: list[str] = []
        titles = (
            ("unclassified", "in the code, not in the table"),
            ("stale", "in the table, not in the code"),
            ("blank_class", "class is blank"),
            ("locked_downgrade", "text of an exception is pasted in; class must be FOREIGN"),
            ("wrong_literal", "class LITERAL and automatic class LITERAL must go together"),
            ("missing_reason", "a reason is required"),
        )
        for name, why in titles:
            items = getattr(self, name)
            if items:
                lines.append(f"{name} ({why}): {len(items)}")
                lines.extend(f"  {item}" for item in items)
        if lines:
            lines.append(
                "fix: run python -m tools.gen_config_error_sites --review and decide, then --write"
            )
        counts = " ".join(f"{name}={n}" for name, n in self.per_class)
        lines.append(f"rows={self.rows} {counts} locked={self.locked}")
        return "\n".join(lines)


# --------------------------------------------------------------------------------------------------------------------
# hash of a syntax tree


def _canon(node: object, out: list[str]) -> None:
    if isinstance(node, ast.AST):
        out.append("(" + type(node).__name__)
        for name in node._fields:
            if name in ("ctx", "type_comment"):
                continue
            if isinstance(node, ast.Constant) and name == "kind":
                continue
            value = getattr(node, name, None)
            if value is None or value == []:
                continue
            out.append(" " + name + "=")
            _canon(value, out)
        out.append(")")
    elif isinstance(node, list):
        out.append("[")
        for item in node:
            _canon(item, out)
            out.append(",")
        out.append("]")
    else:
        out.append(type(node).__name__ + ":" + repr(node))


def node_hash(node: ast.AST) -> str:
    """First ``HASH_LEN`` hex characters of sha256 over a canonical walk of the tree (no positions, no ``ast.dump``)."""
    out: list[str] = []
    try:
        _canon(node, out)
    except RecursionError as exc:
        raise SitesError("syntax tree too deep to hash") from exc
    return hashlib.sha256("".join(out).encode("utf-8")).hexdigest()[:HASH_LEN]


# --------------------------------------------------------------------------------------------------------------------
# scopes and taint


def _scope_nodes(root: ast.AST) -> list[ast.AST]:
    """Nodes of one scope: the nested ``def``, ``lambda`` and class nodes are listed but not entered."""
    found: list[ast.AST] = []
    if isinstance(root, DEFS):
        stack: list[ast.AST] = list(reversed(root.body))
    elif isinstance(root, ast.Lambda):
        stack = [root.body]
    else:
        stack = list(reversed(list(ast.iter_child_nodes(root))))
    while stack:
        node = stack.pop()
        found.append(node)
        if isinstance(node, SCOPES):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))
    return found


def _is_taint_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return (
            isinstance(func.value, ast.Name)
            and func.value.id in TAINT_MODULES
            and func.attr in TAINT_CALLS
        )
    return isinstance(func, ast.Name) and func.id in TAINT_CALLS and func.id != "exception"


def _mentions(expr: ast.AST, names: frozenset[str] | set[str]) -> bool:
    for node in ast.walk(expr):
        if isinstance(node, ast.Name) and node.id in names:
            return True
        if _is_taint_call(node):
            return True
    return False


def _target_names(target: ast.AST) -> list[str]:
    """Names a store target taints: plain names, tuple elements, and the root name of a subscript or attribute."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        return [n for elt in target.elts for n in _target_names(elt)]
    if isinstance(target, (ast.Subscript, ast.Attribute)):
        return _target_names(target.value)
    return []


def tainted_names(func: ast.AST) -> frozenset[str]:
    """Names that hold, or are derived from, the exception bound by an ``except ... as NAME`` in this one scope."""
    nodes = _scope_nodes(func)
    tainted: set[str] = {
        n.name for n in nodes if isinstance(n, ast.ExceptHandler) and n.name is not None
    }
    changed = True
    while changed:
        changed = False
        before = len(tainted)
        for node in nodes:
            pairs: list[tuple[ast.AST | None, list[ast.AST]]] = []
            if isinstance(node, ast.Assign):
                pairs.append((node.value, list(node.targets)))
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                pairs.append((node.value, [node.target]))
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
                pairs.append((node.iter, [node.target]))
            elif isinstance(node, ast.NamedExpr):
                pairs.append((node.value, [node.target]))
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if item.optional_vars is not None:
                        pairs.append((item.context_expr, [item.optional_vars]))
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in MUTATORS
            ):
                values = [*node.args, *(kw.value for kw in node.keywords)]
                if any(_mentions(v, tainted) for v in values):
                    tainted.update(_target_names(node.func.value))
            for value, targets in pairs:
                if value is not None and _mentions(value, tainted):
                    for target in targets:
                        tainted.update(_target_names(target))
        changed = len(tainted) != before
    return frozenset(tainted)


# --------------------------------------------------------------------------------------------------------------------
# the scan


@dataclass
class _Module:
    file: str
    name: str  # dotted name below the package folder ("" for the package's own __init__)
    source: str
    tree: ast.Module
    aliases: dict[str, str] = field(
        default_factory=dict
    )  # local name -> original class/function name
    mod_names: dict[str, str] = field(default_factory=dict)  # local name -> dotted module name
    func_imports: dict[str, tuple[str, str]] = field(
        default_factory=dict
    )  # local -> (module, name)
    top_defs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = field(default_factory=dict)


@dataclass
class _Helper:
    module: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    params: list[str]
    interpolated: set[str]
    kind: str


def _read_modules(package_dir: Path) -> list[_Module]:
    if not package_dir.is_dir():
        raise SitesError(f"package folder not found: {package_dir.name}")
    paths: list[Path] = []
    pending = [package_dir]
    while pending:
        folder = pending.pop()
        for entry in sorted(folder.iterdir()):
            if entry.is_symlink():
                raise SitesError(f"symlink under the package folder: {entry.name}")
            if entry.is_dir():
                if entry.name != "__pycache__":
                    pending.append(entry)
            elif entry.suffix == ".py":
                paths.append(entry)
    if not paths:
        raise SitesError("no .py file under the package folder")
    modules: list[_Module] = []
    for path in sorted(paths, key=lambda p: p.relative_to(package_dir).as_posix()):
        rel = path.relative_to(package_dir).as_posix()
        if not rel.isascii():
            raise SitesError(f"non-ASCII file name: {rel!r}")
        try:
            source = path.read_bytes().decode("utf-8")
            tree = ast.parse(source)
        except (UnicodeDecodeError, SyntaxError, ValueError, RecursionError) as exc:
            raise SitesError(f"cannot parse {rel}: {type(exc).__name__}") from exc
        parts = rel[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules.append(_Module(rel, ".".join(parts), source, tree))
    return modules


def _resolve_module(dotted: str, pkg: str, known: set[str]) -> str | None:
    """Dotted import name -> module name below the package folder, or None when it is not one of ours."""
    if dotted == pkg:
        return "" if "" in known else None
    if dotted.startswith(pkg + "."):
        dotted = dotted[len(pkg) + 1 :]
    return dotted if dotted in known else None


def _index_imports(mod: _Module, pkg: str, known: set[str], is_pkg_init: bool) -> None:
    for node in ast.walk(mod.tree):
        if isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = mod.name.split(".") if mod.name else []
                keep = len(parts) - (node.level - (1 if is_pkg_init else 0))
                prefix = parts[: max(keep, 0)]
                base = ".".join([*prefix, *([base] if base else [])])
                resolved = base if base in known or base == "" else None
            else:
                resolved = _resolve_module(base, pkg, known)
            for alias in node.names:
                local = alias.asname or alias.name
                mod.aliases[local] = alias.name
                sub = f"{resolved}.{alias.name}" if resolved else alias.name
                if resolved is not None and sub in known:
                    mod.mod_names[local] = sub
                elif resolved is not None:
                    mod.func_imports[local] = (resolved, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    found = _resolve_module(alias.name, pkg, known)
                    if found is not None:
                        mod.mod_names[alias.asname] = found
                else:
                    first = alias.name.split(".")[0]
                    if first == pkg:
                        mod.mod_names[first] = ""
                    elif first in known:
                        mod.mod_names[first] = first


def _dotted(expr: ast.AST) -> list[str] | None:
    parts: list[str] = []
    while isinstance(expr, ast.Attribute):
        parts.append(expr.attr)
        expr = expr.value
    if isinstance(expr, ast.Name):
        parts.append(expr.id)
        return parts[::-1]
    return None


def _canon_name(expr: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(expr, ast.Name):
        return aliases.get(expr.id, expr.id)
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def _site_classes(modules: list[_Module]) -> set[str]:
    classes = {BASE_CLASS}
    defined = False
    changed = True
    while changed:
        changed = False
        for mod in modules:
            for node in ast.walk(mod.tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if node.name == BASE_CLASS:
                    defined = True
                if node.name in classes:
                    continue
                if any(_canon_name(b, mod.aliases) in classes for b in node.bases):
                    classes.add(node.name)
                    changed = True
    if not defined:
        raise SitesError(f"class {BASE_CLASS} is not defined in the package folder")
    return classes


def _is_super_init(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "__init__"
        and isinstance(node.func.value, ast.Call)
        and isinstance(node.func.value.func, ast.Name)
        and node.func.value.func.id == "super"
        and not node.func.value.args
    )


def _is_self_attr(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def _check_init(cls: ast.ClassDef, init: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
    """BN-8: the body holds one ``super().__init__(<expr>)`` statement and assignments to attributes of ``self``, nothing else
    (no local, no ``if``, no loop); and no route that rewrites ``args`` or the instance."""
    if isinstance(init, ast.AsyncFunctionDef) or init.decorator_list:
        raise SitesError(f"{cls.name}.__init__ must be a plain def")
    base_calls = [
        n
        for n in ast.walk(init)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "__init__"
    ]
    supers = [n for n in base_calls if _is_super_init(n)]
    if len(base_calls) != 1 or len(supers) != 1:
        raise SitesError(f"{cls.name}.__init__ must call the base initialiser exactly once")
    if not any(isinstance(stmt, ast.Expr) and stmt.value is supers[0] for stmt in init.body):
        raise SitesError(f"{cls.name}.__init__ must call super().__init__(...) as a statement")
    for stmt in init.body:
        if isinstance(stmt, ast.Expr) and (
            stmt.value is supers[0]
            or (isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))
        ):
            continue
        if isinstance(stmt, ast.Assign) and all(_is_self_attr(t) for t in stmt.targets):
            continue
        if (
            isinstance(stmt, ast.AnnAssign)
            and stmt.value is not None
            and _is_self_attr(stmt.target)
        ):
            continue
        raise SitesError(
            f"{cls.name}.__init__ may only assign attributes of self and call super().__init__(...)"
        )
    for node in ast.walk(init):
        if isinstance(node, ast.Name) and node.id in INIT_BAD_NAMES:
            raise SitesError(
                f"{cls.name}.__init__ uses {node.id}; the text must go through super()"
            )
        if isinstance(node, ast.Attribute) and node.attr in INIT_BAD_ATTRS:
            raise SitesError(
                f"{cls.name}.__init__ uses .{node.attr}; the text must go through super()"
            )


def _check_reduce(cls: ast.ClassDef, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
    """The only allowed ``__reduce__``: ``def __reduce__(self): return (type(self), (self.a, ...))`` (a docstring may come first)."""
    a = fn.args
    plain = (
        isinstance(fn, ast.FunctionDef)
        and not fn.decorator_list
        and fn.returns is None
        and [x.arg for x in a.args] == ["self"]
        and not (
            a.posonlyargs or a.kwonlyargs or a.vararg or a.kwarg or a.defaults or a.kw_defaults
        )
    )
    body = [
        st
        for st in fn.body
        if not (
            isinstance(st, ast.Expr)
            and isinstance(st.value, ast.Constant)
            and isinstance(st.value.value, str)
        )
    ]
    ok = plain and len(body) == 1 and isinstance(body[0], ast.Return)
    if ok:
        value = body[0].value
        ok = (
            isinstance(value, ast.Tuple)
            and len(value.elts) == 2
            and isinstance(value.elts[0], ast.Call)
            and isinstance(value.elts[0].func, ast.Name)
            and value.elts[0].func.id == "type"
            and not value.elts[0].keywords
            and len(value.elts[0].args) == 1
            and isinstance(value.elts[0].args[0], ast.Name)
            and value.elts[0].args[0].id == "self"
            and isinstance(value.elts[1], ast.Tuple)
            and bool(value.elts[1].elts)
            and all(
                isinstance(e, ast.Attribute) and _is_self_attr(e) and not e.attr.startswith("__")
                for e in value.elts[1].elts
            )
        )
    if not ok:
        raise SitesError(
            f"{cls.name}.__reduce__ must be exactly: return (type(self), (self.attr, ...))"
        )


def _check_site_class(cls: ast.ClassDef, classes: set[str], aliases: dict[str, str]) -> None:
    if cls.decorator_list:
        raise SitesError(f"site class {cls.name} has a decorator")
    if cls.keywords:
        raise SitesError(f"site class {cls.name} has a class keyword")
    names = [_canon_name(b, aliases) for b in cls.bases]
    if cls.name == BASE_CLASS:
        if names != [BASE_CLASS_BASE]:
            raise SitesError(f"{BASE_CLASS} must have exactly the base {BASE_CLASS_BASE}")
    elif len(names) != 1 or names[0] not in classes:
        raise SitesError(f"site class {cls.name} must have exactly one site class as base")
    inits = 0
    reduces = 0
    for stmt in cls.body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            continue
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            if all(
                isinstance(t, ast.Name) and not (t.id.startswith("__") and t.id.endswith("__"))
                for t in targets
            ):
                continue
            raise SitesError(f"site class {cls.name} assigns a dunder or complex name")
        if isinstance(stmt, DEFS) and stmt.name == "__init__":
            inits += 1
            if inits > 1:
                raise SitesError(f"site class {cls.name} defines __init__ twice")
            _check_init(cls, stmt)
            continue
        if isinstance(stmt, DEFS) and stmt.name == REDUCE_DEF:
            reduces += 1
            if reduces > 1:
                raise SitesError(f"site class {cls.name} defines {REDUCE_DEF} twice")
            _check_reduce(cls, stmt)
            continue
        raise SitesError(f"site class {cls.name} holds more than a docstring and plain fields")


def _params(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    a = fn.args
    names = [x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs]]
    if a.vararg:
        names.append(a.vararg.arg)
    if a.kwarg:
        names.append(a.kwarg.arg)
    return names


def _all_args(call: ast.Call) -> list[ast.AST]:
    return [*call.args, *(kw.value for kw in call.keywords)]


def _interpolated_params(call: ast.Call, params: list[str]) -> set[str]:
    found: set[str] = set()
    for arg in _all_args(call):
        for node in ast.walk(arg):
            if isinstance(node, ast.Name) and node.id in params:
                found.add(node.id)
    return found


# file, symbol, kind, hash, auto class, auto reason, line, origin hints, column, node
_Raw = tuple[str, str, str, str, str, str, int, tuple[str, ...], int, ast.AST]


def _guard_text(node: ast.AST, parents: dict[int, ast.AST]) -> str:
    """What guards a construction inside its function: for every enclosing statement or expression up to the ``def``, its kind,
    the field the construction sits in, and the header (``if`` test, ``for`` iterator, ``except`` type ...). No position."""
    out: list[str] = []
    child = node
    cur = parents.get(id(child))
    while cur is not None and not isinstance(cur, (*SCOPES, ast.Module)):
        kind = type(cur).__name__
        where = ""
        for name, value in ast.iter_fields(cur):
            if value is child or (isinstance(value, list) and any(v is child for v in value)):
                where = name
                break
        out.append(f"<{kind}.{where}")
        for name in GUARD_FIELDS.get(kind, ()):
            part: list[str] = []
            _canon(getattr(cur, name, None), part)
            out.append(" " + name + "=" + "".join(part))
        out.append(">")
        child = cur
        cur = parents.get(id(child))
    return "".join(out)


def guarded_hash(node: ast.AST, guard: str) -> str:
    """``node_hash`` seeded with the guard text, for a construction whose plain hash is shared by another in the same function."""
    out: list[str] = []
    try:
        _canon(node, out)
    except RecursionError as exc:
        raise SitesError("syntax tree too deep to hash") from exc
    text = "".join(out) + "|guard|" + guard
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:HASH_LEN]


def _plain_class_attr(attr: str) -> bool:
    """``ConfigError.attr`` is not a use of the class as a value, unless ``attr`` is a dunder (``__call__``, ``__new__`` ...)."""
    return not attr.startswith("__") or attr in CLASS_ATTR_OK


def _flat_names(expr: ast.AST) -> list[ast.AST]:
    """``Name``/``Attribute`` nodes of ``expr`` itself or of a tuple or list of them (``except (A, B)``, ``isinstance(x, (A, B))``, ``isinstance(x, A | B)``)."""
    if isinstance(expr, (ast.Name, ast.Attribute)):
        return [expr]
    if isinstance(expr, (ast.Tuple, ast.List)):
        return [n for e in expr.elts for n in _flat_names(e)]
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitOr):  # A | B
        return [*_flat_names(expr.left), *_flat_names(expr.right)]
    return []


class _Scanner:
    def __init__(self, package_dir: Path) -> None:
        self.modules = _read_modules(package_dir)
        self.pkg = package_dir.name
        self.known = {m.name for m in self.modules}
        self.by_name = {m.name: m for m in self.modules}
        for mod in self.modules:
            _index_imports(mod, self.pkg, self.known, mod.file.endswith("__init__.py"))
        self.classes = _site_classes(self.modules)
        for mod in self.modules:
            for node in ast.walk(mod.tree):
                if isinstance(node, ast.ClassDef) and node.name in self.classes:
                    _check_site_class(node, self.classes, mod.aliases)
        self.parents: dict[int, ast.AST] = {}
        for mod in self.modules:
            for parent in ast.walk(mod.tree):
                for child in ast.iter_child_nodes(parent):
                    self.parents[id(child)] = parent
            self._check_class_values(mod)
        self.taint_cache: dict[int, frozenset[str]] = {}
        self.factories: dict[tuple[str, str], _Helper] = {}
        self.raisers: dict[tuple[str, str], _Helper] = {}
        self.callers: dict[tuple[str, str], list[str]] = {}
        self._find_helpers()

    def _check_class_values(self, mod: _Module) -> None:
        """A site class may be called, caught, tested with ``isinstance``/``issubclass``, named as a base, an annotation or the
        target of a bare ``raise``. Any other use of its name makes it a value that could build a site the scan cannot see
        (``kind = ConfigError; raise kind(...)``, ``raise_as(ConfigError, ...)``) and is refused."""
        allowed: set[int] = set()
        for node in ast.walk(mod.tree):
            if isinstance(node, ast.ExceptHandler) and node.type is not None:
                allowed.update(id(n) for n in _flat_names(node.type))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, (ast.Name, ast.Attribute)):
                    allowed.add(id(node.func))
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id in ("isinstance", "issubclass")
                    and len(node.args) == 2
                ):
                    allowed.update(id(n) for n in _flat_names(node.args[1]))
            elif isinstance(node, ast.ClassDef):
                allowed.update(id(n) for n in _flat_names(ast.Tuple(elts=node.bases)))
            elif isinstance(node, ast.Raise) and node.exc is not None:
                allowed.update(id(n) for n in _flat_names(node.exc))
            elif (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, (ast.Name, ast.Attribute))
                and _plain_class_attr(node.attr)
            ):
                allowed.add(id(node.value))
            notes: list[ast.AST] = []
            if isinstance(node, ast.arg) and node.annotation is not None:
                notes.append(node.annotation)
            elif isinstance(node, DEFS) and node.returns is not None:
                notes.append(node.returns)
            elif isinstance(node, ast.AnnAssign):
                notes.append(node.annotation)
            for note in notes:
                allowed.update(id(n) for n in ast.walk(note))
        for node in ast.walk(mod.tree):
            if (
                isinstance(node, (ast.Name, ast.Attribute))
                and _canon_name(node, mod.aliases) in self.classes
                and id(node) not in allowed
            ):
                raise SitesError(
                    f"{mod.file}:{getattr(node, 'lineno', 0)}: a site class is used as a value; "
                    "call it directly so the scan sees the construction"
                )

    # -- helpers -------------------------------------------------------------------------------------------------
    def is_construction(self, node: ast.AST, mod: _Module) -> str | None:
        if isinstance(node, ast.Call):
            name = _canon_name(node.func, mod.aliases)
            if name in self.classes:
                return name
        return None

    def taint_of(self, scope: ast.AST) -> frozenset[str]:
        got = self.taint_cache.get(id(scope))
        if got is None:
            got = tainted_names(scope)
            self.taint_cache[id(scope)] = got
        return got

    def _find_helpers(self) -> None:
        for mod in self.modules:
            for node in mod.tree.body:
                if isinstance(node, DEFS):
                    mod.top_defs[node.name] = node
        for mod in self.modules:
            for name, fn in mod.top_defs.items():
                params = _params(fn)
                nodes = _scope_nodes(fn)
                built: set[str] = set()
                for n in nodes:
                    if isinstance(n, ast.Assign) and self.is_construction(n.value, mod):
                        built.update(t.id for t in n.targets if isinstance(t, ast.Name))
                for n in nodes:
                    if (
                        isinstance(n, ast.Return)
                        and isinstance(n.value, ast.Name)
                        and n.value.id in built
                    ):
                        raise SitesError(
                            f"{mod.file}::{name} returns a name that holds a site "
                            "construction; return the construction directly"
                        )
                for n in nodes:
                    if isinstance(n, ast.Return) and n.value is not None:
                        kind = self.is_construction(n.value, mod)
                        if kind and isinstance(n.value, ast.Call):
                            used = _interpolated_params(n.value, params)
                            if used and (mod.name, name) not in self.factories:
                                self.factories[(mod.name, name)] = _Helper(
                                    mod.name, fn, params, used, kind
                                )
                            elif used:
                                self.factories[(mod.name, name)].interpolated.update(used)
                    if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call):
                        kind = self.is_construction(n.exc, mod)
                        if kind:
                            used = _interpolated_params(n.exc, params)
                            if used and (mod.name, name) not in self.raisers:
                                self.raisers[(mod.name, name)] = _Helper(
                                    mod.name, fn, params, used, kind
                                )
                            elif used:
                                self.raisers[(mod.name, name)].interpolated.update(used)
        for mod in self.modules:
            for fn in mod.top_defs.values():
                for n in _scope_nodes(fn):
                    if (
                        isinstance(n, ast.Return)
                        and isinstance(n.value, ast.Call)
                        and self.resolve(n.value, mod, self.factories) is not None
                    ):
                        raise SitesError(
                            f"{mod.file}::{fn.name} returns a factory call; "
                            "a factory called through a factory is not supported"
                        )

    def resolve(
        self, call: ast.Call, mod: _Module, table: dict[tuple[str, str], _Helper]
    ) -> _Helper | None:
        """The helper a call names, in the three forms BN-17 allows; method calls are never resolved."""
        func = call.func
        if isinstance(func, ast.Name):
            if func.id in mod.func_imports:
                m, orig = mod.func_imports[func.id]
                return table.get((m, orig))
            if func.id in mod.top_defs:
                return table.get((mod.name, func.id))
            return None
        chain = _dotted(func)
        if chain is None or len(chain) < 2:
            return None
        first = chain[0]
        if first not in mod.mod_names:
            return None
        target = ".".join(p for p in [mod.mod_names[first], *chain[1:-1]] if p)
        if target not in self.known:
            return None
        return table.get((target, chain[-1]))

    def bound(self, call: ast.Call, helper: _Helper) -> dict[str, ast.AST] | None:
        """Parameter name -> argument expression; None when a star argument makes the binding unknown."""
        if _has_star(call):
            return None
        positional = [a.arg for a in [*helper.node.args.posonlyargs, *helper.node.args.args]]
        found: dict[str, ast.AST] = {}
        for i, arg in enumerate(call.args):
            found[positional[i] if i < len(positional) else "*"] = arg
        for kw in call.keywords:
            found[kw.arg or "**"] = kw.value
        return found

    def bind(self, call: ast.Call, helper: _Helper) -> list[ast.AST]:
        """The argument expressions that reach the parameters the helper interpolates."""
        found = self.bound(call, helper)
        if found is None:
            return _all_args(call)
        return [
            expr
            for name, expr in found.items()
            if name in helper.interpolated or name not in helper.params
        ]

    # -- classification ------------------------------------------------------------------------------------------
    def classify(self, args: list[ast.AST], taint: frozenset[str]) -> tuple[str, str]:
        if any(_mentions(a, taint) for a in args):
            return "FOREIGN", EXC_VAR
        return "FOREIGN", UNPROVEN

    def classify_construction(self, call: ast.Call, taint: frozenset[str]) -> tuple[str, str]:
        if _literal_shape(call):
            return "LITERAL", CONSTANT
        return self.classify(_all_args(call), taint)

    def classify_helper_call(
        self, call: ast.Call, helper: _Helper, taint: frozenset[str]
    ) -> tuple[str, str]:
        found = self.bound(call, helper)
        if (
            found is not None
            and helper.interpolated <= found.keys()
            and all(_plain_string(found[p]) for p in helper.interpolated)
        ):
            return "LITERAL", CONSTANT
        return self.classify(self.bind(call, helper), taint)

    # -- the walk ------------------------------------------------------------------------------------------------
    def collect(self) -> list[Site]:
        raw: list[_Raw] = []
        for mod in self.modules:
            self._walk(mod, mod.tree, [], mod.tree, raw)
        groups: dict[tuple[str, str, str], list[int]] = {}
        for i, item in enumerate(raw):
            groups.setdefault((item[0], item[1], item[3]), []).append(i)
        # Several constructions with the same text in one function: the plain hash cannot tell them apart, so the order of
        # the source would decide which table row is which, and swapping two blocks would move the labels unseen. Seed the hash
        # of every member of such a group with what guards it; only members still tied after that are numbered by position.
        final: dict[tuple[str, str, str], list[tuple[int, int, int]]] = {}
        for members in groups.values():
            for i in members:
                f, sym, _kind, h, _ac, _ar, line, _hints, col, node = raw[i]
                if len(members) > 1:
                    h = guarded_hash(node, _guard_text(node, self.parents))
                final.setdefault((f, sym, h), []).append((line, col, i))
        sites: list[Site] = []
        for (f, sym, h), members in final.items():
            for k, (_line, _col, i) in enumerate(sorted(members), start=1):
                _f, _sym, kind, _h, ac, ar, line, hints, _c, _n = raw[i]
                sites.append(Site(f, sym, kind, h, k, ac, ar, line, hints))
        sites.sort(key=lambda s: s.key)
        return self._add_caller_hints(sites)

    def _add_caller_hints(self, sites: list[Site]) -> list[Site]:
        """A raiser's own construction rows list the callers the scan can resolve (for the review sheet)."""
        out: list[Site] = []
        for site in sites:
            callers = self.callers.get((site.file, site.symbol), [])
            out.append(
                replace(site, origin_hints=(*site.origin_hints, *callers)) if callers else site
            )
        return out

    def _symbol(self, stack: list[str]) -> str:
        symbol = ".".join(stack) if stack else "<module>"
        if not symbol.isascii():
            raise SitesError(f"non-ASCII name in a symbol chain: {symbol!r}")
        return symbol

    def _walk(
        self,
        mod: _Module,
        node: ast.AST,
        stack: list[str],
        scope: ast.AST,
        raw: list[_Raw],
    ) -> None:
        pending: list[tuple[ast.AST, list[str], ast.AST]] = [(node, stack, scope)]
        while pending:
            cur, cstack, cscope = pending.pop()
            self._visit(mod, cur, cstack, cscope, raw)
            for child, ch_stack, ch_scope in self._children(cur, cstack, cscope):
                pending.append((child, ch_stack, ch_scope))

    def _children(
        self, node: ast.AST, stack: list[str], scope: ast.AST
    ) -> list[tuple[ast.AST, list[str], ast.AST]]:
        out: list[tuple[ast.AST, list[str], ast.AST]] = []
        if isinstance(node, DEFS):
            inner = [*stack, node.name]
            outer_parts: list[ast.AST] = [*node.decorator_list, node.args]
            if node.returns is not None:
                outer_parts.append(node.returns)
            for part in outer_parts:
                out.append((part, stack, scope))
            out.extend((s, inner, node) for s in node.body)
        elif isinstance(node, ast.ClassDef):
            inner = [*stack, node.name]
            outer_parts = [*node.decorator_list, *node.bases, *node.keywords]
            out.extend((p, stack, scope) for p in outer_parts)
            out.extend((s, inner, node) for s in node.body)
        elif isinstance(node, ast.Lambda):
            out.append((node.args, stack, scope))
            out.append((node.body, stack, node))
        else:
            out.extend((c, stack, scope) for c in ast.iter_child_nodes(node))
        return out

    def _visit(
        self,
        mod: _Module,
        node: ast.AST,
        stack: list[str],
        scope: ast.AST,
        raw: list[_Raw],
    ) -> None:
        line = getattr(node, "lineno", 0)
        col = getattr(node, "col_offset", 0)
        taint = self.taint_of(scope)
        if isinstance(node, ast.Raise) and node.exc is not None:
            exc = node.exc
            if isinstance(exc, (ast.Name, ast.Attribute)):
                name = _canon_name(exc, mod.aliases)
                if name in self.classes:
                    raw.append(
                        (
                            mod.file,
                            self._symbol(stack),
                            name,
                            node_hash(exc),
                            "LITERAL",
                            CONSTANT,
                            line,
                            (),
                            col,
                            node,
                        )
                    )
            return
        if not isinstance(node, ast.Call):
            return
        symbol = self._symbol(stack)
        kind = self.is_construction(node, mod)
        if kind:
            ac, ar = self.classify_construction(node, taint)
            hints = _hints(node, scope, mod)
            raw.append((mod.file, symbol, kind, node_hash(node), ac, ar, line, hints, col, node))
            return
        if _is_super_init(node) and isinstance(scope, ast.FunctionDef) and scope.name == "__init__":
            cls_name = stack[-2] if len(stack) >= 2 else ""
            if cls_name in self.classes:
                ac, ar = self.classify_construction(node, taint)
                raw.append(
                    (
                        mod.file,
                        symbol,
                        cls_name,
                        node_hash(node),
                        ac,
                        ar,
                        line,
                        _hints(node, scope, mod),
                        col,
                        node,
                    )
                )
            return
        helper = self.resolve(node, mod, self.factories)
        if helper is not None:
            ac, ar = self.classify_helper_call(node, helper, taint)
            raw.append(
                (
                    mod.file,
                    symbol,
                    helper.kind,
                    node_hash(node),
                    ac,
                    ar,
                    line,
                    _hints(node, scope, mod),
                    col,
                    node,
                )
            )
            return
        raiser = self.resolve(node, mod, self.raisers)
        if raiser is not None:
            home = self.by_name[raiser.module].file
            note = f"caller {mod.file}:{line} in {symbol}"
            self.callers.setdefault((home, raiser.node.name), []).append(note)
        if raiser is not None and any(_mentions(a, taint) for a in self.bind(node, raiser)):
            raw.append(
                (
                    mod.file,
                    symbol,
                    raiser.kind,
                    node_hash(node),
                    "FOREIGN",
                    EXC_VAR,
                    line,
                    _hints(node, scope, mod),
                    col,
                    node,
                )
            )


def _plain_string(expr: ast.AST) -> bool:
    if isinstance(expr, ast.Constant):
        return isinstance(expr.value, str)
    if isinstance(expr, ast.JoinedStr):
        return not any(isinstance(v, ast.FormattedValue) for v in expr.values)
    return False


def _has_star(call: ast.Call) -> bool:
    return any(isinstance(a, ast.Starred) for a in call.args) or any(
        kw.arg is None for kw in call.keywords
    )


def _literal_shape(call: ast.Call) -> bool:
    if call.keywords or any(isinstance(a, ast.Starred) for a in call.args):
        return False
    if len(call.args) > 1:
        return False
    return not call.args or _plain_string(call.args[0])


def _callee(call: ast.Call) -> str:
    chain = _dotted(call.func)
    return ".".join(chain) if chain else type(call.func).__name__


def _expr_hint(expr: ast.AST, scope: ast.AST, mod: _Module) -> str:
    if isinstance(expr, ast.Name):
        name = expr.id
        if isinstance(scope, (*DEFS, ast.Lambda)) and name in _params_of(scope):
            label = getattr(scope, "name", "<lambda>")
            return f"param {name} of {label}"
        for n in _scope_nodes(scope):
            if isinstance(n, ast.Assign) and any(name in _target_names(t) for t in n.targets):
                if isinstance(n.value, ast.Call):
                    return f"local {name} assigned from call {_callee(n.value)}"
                return f"local {name} assigned from {type(n.value).__name__}"
            if isinstance(n, (ast.For, ast.AsyncFor)) and name in _target_names(n.target):
                return f"loop variable {name}"
            if isinstance(n, ast.comprehension) and name in _target_names(n.target):
                return f"loop variable {name}"
        for top in mod.tree.body:
            if isinstance(top, (ast.Assign, ast.AnnAssign)):
                targets = top.targets if isinstance(top, ast.Assign) else [top.target]
                if any(name in _target_names(t) for t in targets):
                    return f"module constant {name}"
        return f"name {name}"
    chain = _dotted(expr)
    if chain is not None:
        return "attribute " + ".".join(chain)
    if isinstance(expr, ast.Call):
        if isinstance(expr.func, ast.Attribute) and expr.func.attr == "join" and expr.args:
            inner = expr.args[0]
            label = inner.id if isinstance(inner, ast.Name) else type(inner).__name__
            return f"join of {label}"
        return f"call {_callee(expr)}"
    return type(expr).__name__


def _params_of(scope: ast.AST) -> list[str]:
    if isinstance(scope, DEFS):
        return _params(scope)
    if isinstance(scope, ast.Lambda):
        a = scope.args
        return [x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs]]
    return []


def _hints(call: ast.Call, scope: ast.AST, mod: _Module) -> tuple[str, ...]:
    hints: list[str] = []
    for arg in _all_args(call):
        parts: list[ast.AST] = []
        if isinstance(arg, ast.JoinedStr):
            parts = [v.value for v in arg.values if isinstance(v, ast.FormattedValue)]
        elif not _plain_string(arg):
            parts = [arg]
        hints.extend(_expr_hint(p, scope, mod) for p in parts)
    return tuple(hints)


def scan(package_dir: Path) -> list[Site]:
    """Every construction of ``ConfigError`` and its subclasses under ``package_dir``, sorted by key."""
    try:
        return _Scanner(package_dir).collect()
    except RecursionError as exc:
        raise SitesError("syntax tree too deep") from exc


# --------------------------------------------------------------------------------------------------------------------
# the table


def load_csv(path: Path) -> list[Row]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SitesError(f"cannot read the table: {type(exc).__name__}") from exc
    if not raw.isascii():
        raise SitesError("the table holds a non-ASCII byte")
    text = raw.decode("ascii")
    reader = csv.reader(text.splitlines(keepends=True))
    try:
        records = list(reader)
    except csv.Error as exc:
        raise SitesError("the table is not valid CSV") from exc
    if not records or tuple(records[0]) != COLUMNS:
        raise SitesError(f"wrong header; expected {','.join(COLUMNS)}")
    rows: list[Row] = []
    seen: set[str] = set()
    for number, rec in enumerate(records[1:], start=2):
        if len(rec) != len(COLUMNS):
            raise SitesError(f"line {number}: expected {len(COLUMNS)} fields")
        site, klass, reason = rec
        if not site or any(ord(c) < 32 or ord(c) == 127 for c in site + klass):
            raise SitesError(f"line {number}: bad site or class")
        if klass != "" and klass not in CLASSES:
            raise SitesError(f"line {number}: class {klass!r} is not one of {CLASSES}")
        if site in seen:
            raise SitesError(f"line {number}: duplicate site")
        if len(reason) > REASON_MAX:
            raise SitesError(f"line {number}: reason over {REASON_MAX} characters")
        if any(ord(c) < 32 or ord(c) == 127 for c in reason):
            raise SitesError(f"line {number}: reason holds a control character or a line break")
        seen.add(site)
        rows.append(Row(site, klass, reason))
    return rows


def compare(sites: list[Site], rows: list[Row]) -> Report:
    by_site = {s.key: s for s in sites}
    by_row = {r.site: r for r in rows}
    unclassified = sorted(k for k in by_site if k not in by_row)
    stale = sorted(k for k in by_row if k not in by_site)
    blank: list[str] = []
    downgrade: list[str] = []
    wrong: list[str] = []
    missing: list[str] = []
    per_class = {c: 0 for c in CLASSES}
    per_class["blank"] = 0
    for key in sorted(by_site.keys() & by_row.keys()):
        site, row = by_site[key], by_row[key]
        per_class[row.klass or "blank"] += 1
        if row.klass == "":
            blank.append(key)
        elif site.auto_reason == EXC_VAR and row.klass != "FOREIGN":
            downgrade.append(key)
        elif (row.klass == "LITERAL") != (site.auto_class == "LITERAL"):
            wrong.append(key)
        elif not row.reason.strip() and (
            row.klass == "OPERATOR" or (row.klass == "FOREIGN" and site.auto_reason == UNPROVEN)
        ):
            missing.append(key)
    return Report(
        unclassified,
        stale,
        blank,
        downgrade,
        wrong,
        missing,
        rows=len(rows),
        per_class=tuple(per_class.items()),
        locked=sum(1 for s in sites if s.auto_reason == EXC_VAR),
    )


def render_csv(rows: list[Row]) -> str:
    lines: list[str] = []

    class _Sink:
        def write(self, text: str) -> int:
            lines.append(text)
            return len(text)

    writer = csv.writer(_Sink(), lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in sorted(rows, key=lambda r: r.site):
        writer.writerow((row.site, row.klass, row.reason))
    return "".join(lines)


def _check_csv_path(csv_path: Path) -> None:
    if csv_path.suffix != ".csv":
        raise SitesError("the table path must end in .csv")


def write(package_dir: Path, csv_path: Path) -> None:
    """Rebuild the table: keep the human fields of unchanged rows, blank the new unproven ones, drop stale rows."""
    _check_csv_path(csv_path)
    sites = scan(package_dir)
    old = {r.site: r for r in load_csv(csv_path)} if csv_path.exists() else {}
    rows: list[Row] = []
    for site in sites:
        if site.key in old:
            rows.append(old[site.key])
        elif site.auto_class == "LITERAL":
            rows.append(Row(site.key, "LITERAL", ""))
        elif site.auto_reason == EXC_VAR:
            rows.append(Row(site.key, "FOREIGN", ""))
        else:
            rows.append(Row(site.key, "", ""))
    csv_path.write_bytes(render_csv(rows).encode("ascii"))


def review_sheet(sites: list[Site], rows: list[Row], package_dir: Path) -> str:
    by_row = {r.site: r for r in rows}
    out: list[str] = []
    last = ""
    for site in sites:
        row = by_row.get(site.key)
        if row is not None and row.klass not in ("", "OPERATOR"):
            continue
        head = f"{site.file}::{site.symbol}"
        if head != last:
            out.append(f"== {head}")
            last = head
        out.append(f"-- {site.key}")
        out.append(
            f"   line {site.lineno}; kind {site.kind}; auto {site.auto_class}/{site.auto_reason}"
        )
        out.append(
            f"   class {row.klass if row else '(not in table)'}; reason {row.reason if row else ''}"
        )
        out.extend(f"   origin: {h}" for h in site.origin_hints)
        text = _call_text(package_dir, site)
        if text:
            out.append(f"   source: {text}")
    return "\n".join(out).encode("ascii", "backslashreplace").decode("ascii")


def _call_text(package_dir: Path, site: Site) -> str:
    try:
        lines = (package_dir / site.file).read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    return " ".join(x.strip() for x in lines[site.lineno - 1 : site.lineno + 3])[:300]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gen_config_error_sites")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--review", action="store_true")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--csv", default=None)
    args = parser.parse_args(argv)
    root = Path(args.root)
    csv_path = Path(args.csv) if args.csv else Path(CSV_PATH)
    if not csv_path.is_absolute():
        csv_path = root / csv_path
    package_dir = root / PACKAGE_DIR
    try:
        _check_csv_path(csv_path)
        if args.write:
            write(package_dir, csv_path)
            print(f"wrote {csv_path.name}")
            return 0
        if args.review:
            rows = load_csv(csv_path) if csv_path.exists() else []
            print(review_sheet(scan(package_dir), rows, package_dir))
            return 0
        report = compare(scan(package_dir), load_csv(csv_path))
    except SitesError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
