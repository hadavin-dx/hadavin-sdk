# The mutants in tests/stage_mutants.py quote this file text exactly, so the file keeps its layout (a formatter would
# break every quoted line). The check of the layout is the mutant list itself: a quoted line that no longer matches fails.
# fmt: off
"""The message-site guard of Q8a-1 (round 12, Issue 2): a value that a person or a log can read must be PROVEN to be
written in the code, or the site must be in the allowance table with a true reason.

Before round 12 the guard was a list of spellings that mean "text from a configuration file" (`name`, `path`,
`settings.x` ...). Four reviews each found another spelling. This module turns the rule round: at every site that builds
message text it asks "is every inserted value proven code-owned?". A value is code-owned when it is

* a literal (text, number, bytes), or an UPPER_CASE constant, or a class name (`type(x).__name__`);
* a number: `len(x)`, arithmetic, `int(x)` or `float(x)` (only when `x` is itself a number or a written value: `int` is a
  pass-through, not a proof, so `int(text_from_a_file)` is a finding), a loop counter (`range`, the first part of `enumerate`), a name or an
  attribute that is annotated `int`, `float`, `bool` or `Literal[...]`;
* the result of a filter that hides the text (`shown_name`, `_named`, `error_where` ...);
* a name or attribute that is only ever bound to code-owned values (checked over the whole scanned tree: every
  assignment, every default, every call that passes a value to a parameter, every function return);
* text made of code-owned parts (`str()`, `.join`, `.format`, `+`, `%`, an f-string, a conditional, a table lookup).

Everything else is NOT proven and is a site: an unknown name, a parameter nobody proves, `exc` of `except ... as exc`,
a `with ... as x` name, an attribute of anything not proven, a call of a function that is not proven to return fixed
text. Names do not decide, only the proof and the allowance table do. What an AST scan cannot see is said in the
CHANGELOG: a value that is handed to another module through a call it cannot resolve by name (a callback, `getattr`, a
dynamic dispatch) and the text a library puts into its own error.
"""

from __future__ import annotations

import ast
import builtins
import re

SAFE_CALLS = frozenset(
    {
        "len", "bool", "round", "abs", "ord", "id", "hash", "isinstance", "any", "all",
        "callable", "hasattr", "range", "divmod", "chr", "type", "isfinite",
        "shown_name", "_named", "shown_names", "digest_prefix", "error_where", "word_like", "is_digest", "status_text", "shown_id",
    }
)  # fmt: skip
# Round 15 (Issue 1e): these names are filters of this package. A call of one of them is trusted only when the name is the
# package's own function: not a parameter or a local name, and not imported from outside the scanned tree.
FILTERS = frozenset(
    {
        "shown_name", "_named", "shown_names", "digest_prefix", "error_where", "word_like", "is_digest", "status_text", "shown_id",
    }
)  # fmt: skip
FILTER_MODULE = "errors.py"  # the module that defines the package's text filters (Round 16, Issue 3c)
LITERAL_BUILDERS = frozenset(
    {"frozenset", "tuple", "set", "list", "dict", "sorted", "str", "int", "float", "bytes", "len", "compile",
     "MappingProxyType", "Template", "Literal", "Decimal", "re", "escape", "range", "max", "min", "sum"}
)  # fmt: skip
# calls that build an error object: the object is a message site whether or not it is raised (Round 15, Issue 1b)
ERROR_SUFFIXES = (
    "Error",
    "Refused",
    "Failed",
    "Unavailable",
    "Exception",
    "Exhausted",
    "NotFound",
    "StaleState",
)
# `.exception(...)`, `traceback.print_exc()` and `exc_info=True` print the whole chain, including the library text
CHAIN_PRINTERS = frozenset(
    {"print_exc", "format_exc", "print_exception", "format_exception", "format_exception_only", "TracebackException", "from_exception", "print_last"}
)
MUTATORS = frozenset(
    {"update", "append", "extend", "add", "insert", "pop", "popitem", "clear", "remove", "discard", "setdefault", "sort", "reverse"}
)  # fmt: skip
PASS_CALLS = frozenset(
    {
        "int", "float", "sorted", "list", "tuple", "set", "frozenset", "reversed", "min", "max", "str", "repr", "format",
        "ascii", "iter", "next", "dict", "sum", "filter", "map", "zip", "enumerate",
    }
)  # fmt: skip
# a method of text or of a mapping returns (a part of) its receiver or its arguments, or a number or a truth value
TEXT_METHODS = frozenset(
    {
        "lower", "upper", "strip", "lstrip", "rstrip", "title", "casefold", "replace", "removeprefix",
        "removesuffix", "decode", "encode", "hex", "join", "format", "format_map", "capitalize", "swapcase",
        "split", "rsplit", "partition", "rpartition", "splitlines", "zfill", "ljust", "rjust", "center",
        "expandtabs", "translate", "get", "items", "keys", "values", "copy", "pop", "setdefault",
        "isoformat", "total_seconds", "count", "index", "find", "rfind", "startswith", "endswith", "isdigit",
        "isalnum", "isalpha", "islower", "isupper", "isidentifier", "isspace", "fullmatch", "match",
        "search", "group", "groups", "hexdigest", "digest", "span", "start", "end",
    }
)  # fmt: skip
NUMBER_ANNOTATIONS = frozenset({"int", "float", "bool", "Literal"})
LOG_METHODS = frozenset(
    {"warning", "info", "error", "debug", "exception", "warn", "critical", "fatal", "log"}
)
# `.append(...)`, `.extend(...)`, `.add(...)`, `.insert(...)` collect values into a list that may be joined, printed or
# raised later. Round 14 (Issue 6): the receiver's NAME no longer decides (a list called `out` was not seen). A call is a
# site when it is given a value that is not proven code-owned and the collection REACHES a message: the same collection
# (a local name in its function, an attribute anywhere in its module) is read inside a join, a format, an f-string, a
# `%`, a `+`, a log call, a print, a write to stderr or stdout, or a raise; or it is returned and the value added is text
# made by `str`, `repr`, an f-string, a format or a sum. A list of data objects that is only returned is not a message.
COLLECTORS = frozenset({"append", "extend", "add", "insert"})
UPPER = re.compile(r"^_*[A-Z][A-Z0-9_]*$")
NUMBER_SPEC = re.compile(r"[0-9.,_<>^+ -]*[dfxXeEgGbo%]")
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


_PRINT_HOW = {"file", "flush"}
# Round 17 (Issue 1b): a call whose name starts with one of these puts its positional arguments into a store, a queue, a file or a
# query. An argument made from an error (`rec.update(exc)`, `q.put(exc)`, `cur.execute(sql, (exc,))`) is a site.
STORE_CALL_PREFIXES = ("update", "insert", "write", "execute", "append", "put")


def _is_number(e) -> bool:
    return isinstance(e, ast.Constant) and not isinstance(e.value, (str, bytes))


def _is_number_annotation(a) -> bool:
    if isinstance(a, ast.Name):
        return a.id in NUMBER_ANNOTATIONS
    if isinstance(a, ast.Subscript) and isinstance(a.value, ast.Name):
        return a.value.id == "Literal"
    if isinstance(a, ast.Constant) and isinstance(a.value, str):  # a string annotation: `"int"`
        return a.value in NUMBER_ANNOTATIONS
    return False


def _targets(t):
    if isinstance(t, ast.Name):
        yield t
    elif isinstance(t, (ast.Tuple, ast.List)):
        for x in t.elts:
            yield from _targets(x)
    elif isinstance(t, ast.Starred):
        yield from _targets(t.value)


def _all_args(args):
    """Every parameter of a function: positional only, positional, keyword only, `*args` and `**kwargs`."""
    return [*args.posonlyargs, *args.args, *args.kwonlyargs, *(a for a in (args.vararg, args.kwarg) if a)]


def _own(root):
    """The nodes of one scope: not those of a function or a class defined inside it (but the definition itself)."""
    todo = list(ast.iter_child_nodes(root))
    while todo:
        n = todo.pop()
        yield n
        if not isinstance(n, (*FUNCS, ast.Lambda, ast.ClassDef)):
            todo.extend(ast.iter_child_nodes(n))


def _root(v):
    """The collection a receiver stands for: `a[k]`, `a.setdefault(k, [])` and `a.b[k]` are all `a` or `a.b`."""
    while True:
        if isinstance(v, ast.Subscript):
            v = v.value
        elif isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute):
            v = v.func.value
        else:
            return v


NUMBER_CALLS = frozenset(
    {"len", "int", "float", "bool", "sum", "any", "all", "isinstance", "round", "abs"}
)


def _read_parts(n):
    """The nodes under `n`, except what is only counted or tested (`len(x)`, `bool(x)`, `x is None`): a collection that
    is only counted does not put its values into text."""
    todo = [n]
    while todo:
        x = todo.pop()
        yield x
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id in NUMBER_CALLS:
            continue
        if isinstance(x, ast.Compare):
            continue
        todo.extend(ast.iter_child_nodes(x))


def _adds_to(call) -> bool:
    """`x.append(v)`, `x.extend(v)`, `x.add(v)`, `x.insert(i, v)`, `x.update(v)`, `x.setdefault(k, v)`: values go into x."""
    return isinstance(call.func, ast.Attribute) and call.func.attr in COLLECTORS | {
        "update",
        "setdefault",
    }


def _recv(v) -> str:
    if isinstance(v, ast.Name):
        return v.id
    if isinstance(v, ast.Attribute):
        return v.attr
    return ""


class Analysis:
    """The proof state over a set of modules: {module path: source text}."""

    def __init__(self, sources: dict[str, str]):
        self.trees = {m: ast.parse(t) for m, t in sources.items()}
        self.parent: dict[int, ast.AST] = {}
        self.scope_of: dict[int, ast.AST] = {}
        self.defs: list[dict] = []  # {node, name, cls, params, module}
        self.calls: list[tuple] = []  # (module, call node, scope)
        self.escaped: set[str] = set()
        self.psafe: set[tuple[int, str]] = set()
        self.fsafe: set[int] = set()  # indexes of `defs` whose every return is code-owned
        self.module_of: dict[int, str] = {}
        self.imports: dict[
            str, dict[str, set]
        ] = {}  # module -> local name -> {(module key or None, name)}
        self._shadow: dict[int, frozenset[str]] = {}
        self.attr_assigns: dict[str, list] = {}  # attribute name -> [(value expr, scope)]
        self.attr_unsafe: set[str] = set()
        self.attr_number: set[str] = set()
        self.attr_safe: set[str] = set()
        self._with_cache: dict = {}
        self.cls_attrs: dict[str, set[str]] = {}  # class name -> attribute names it assigns or declares
        self.cls_bases: dict[str, list[str]] = {}  # class name -> names of its bases
        self._envs: dict[int, frozenset[str]] = {}
        self.changed_in_function: set[str] = (
            set()
        )  # outer names that a function changes (see `_note_changed`)
        self.upper_assigned: set[str] = (
            set()
        )  # UPPER_CASE names bound at least once, always to a written value
        self.upper_bad: set[str] = (
            set()
        )  # UPPER_CASE names filled or changed at run time (Round 15, Issue 1f)
        self.upper_outside: dict[
            str, set[str]
        ] = {}  # module -> UPPER names imported from outside the scanned tree
        self._collect()
        self._scan_upper()
        self._solve()

    # ---- collecting ---------------------------------------------------------------------------------------------
    def _collect(self):
        for module, tree in self.trees.items():
            self.module_of[id(tree)] = module
            self._walk(module, tree, tree, None)
            self._read_imports(module, tree)
        names = {d["name"] for d in self.defs}
        classes = {d["cls"] for d in self.defs if d["cls"]}
        for module, tree in self.trees.items():
            if module.startswith("~callers/"):
                continue
            for n in ast.walk(tree):
                # a function used as a value (a callback, a decorator argument) has callers we cannot see
                if (
                    isinstance(n, ast.Name)
                    and isinstance(n.ctx, ast.Load)
                    and n.id in names | classes
                ):
                    p = self.parent.get(id(n))
                    if not (isinstance(p, ast.Call) and p.func is n):
                        self.escaped.add(n.id)
                elif (
                    isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Load) and n.attr in names
                ):
                    p = self.parent.get(id(n))
                    if not (isinstance(p, ast.Call) and p.func is n):
                        self.escaped.add(n.attr)

    def _literalish(self, e) -> bool:
        """A value written in the code: a literal, a collection of literals, a text made of them, another UPPER_CASE name,
        or a standard conversion of them (`frozenset({...})`, `re.compile("...")`). `{}` and `[]` count: what makes such a
        name unsafe is a later change (see `_scan_upper`)."""
        if isinstance(e, ast.Constant):
            return True
        if isinstance(e, ast.JoinedStr):
            return all(self._literalish(v) for v in e.values)
        if isinstance(e, ast.FormattedValue):
            return self._literalish(e.value)
        if isinstance(e, (ast.Tuple, ast.List, ast.Set)):
            return all(self._literalish(x) for x in e.elts)
        if isinstance(e, ast.Dict):
            return all(k is None or self._literalish(k) for k in e.keys) and all(
                self._literalish(v) for v in e.values
            )
        if isinstance(e, ast.UnaryOp):
            return self._literalish(e.operand)
        if isinstance(e, ast.BinOp):
            return self._literalish(e.left) and self._literalish(e.right)
        if isinstance(e, ast.Lambda):
            return True  # a function written in the code is not text
        if isinstance(e, ast.Name):
            return bool(UPPER.match(e.id)) or e.id in self._code_names
        if isinstance(e, ast.Attribute):
            return bool(UPPER.match(e.attr)) or self._literalish(e.value)
        if isinstance(e, ast.Subscript):
            return self._literalish(e.value) and self._literalish(e.slice)
        if isinstance(e, ast.Call):
            f = e.func
            # a class or a function of this tree called over written values (`Grant(...)`, `Entry(...)`, `_aws("x")`) at module level is a
            # table row; a function that reads the environment is the limit the CHANGELOG names
            ok_name = isinstance(f, ast.Name) and (
                f.id in LITERAL_BUILDERS or f.id in self._code_names
            )
            ok_attr = isinstance(f, ast.Attribute) and (
                f.attr in LITERAL_BUILDERS or f.attr in TEXT_METHODS
            )
            if not (ok_name or ok_attr):
                return False
            if (
                isinstance(f, ast.Attribute)
                and f.attr in TEXT_METHODS
                and not self._literalish(f.value)
            ):
                return False
            return all(self._literalish(a) for a in [*e.args, *(k.value for k in e.keywords)])
        return False

    @property
    def _code_names(self) -> set[str]:
        if not hasattr(self, "_code_names_cache"):
            names = {d["name"] for d in self.defs}
            for tree in self.trees.values():
                names |= {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
            self._code_names_cache = names
        return self._code_names_cache

    def _scan_upper(self):
        """Round 15, Issue 1f: an UPPER_CASE name is code-owned only if every place that binds it in the scanned tree
        binds a written value, nothing changes it (`NAME[k] = v`, `NAME.update(...)`, `NAME += ...`, `global NAME`), and
        it is not imported from outside the tree. `_LOADED = {}` filled at run time, and `_LOADED.get(k)`, are not."""
        for module, tree in self.trees.items():
            if module.startswith("~callers/"):
                continue
            for n in ast.walk(tree):
                self._note_changed(n)
                if (
                    isinstance(n, ast.Name)
                    and UPPER.match(n.id)
                    and isinstance(n.ctx, (ast.Store, ast.Del))
                ):
                    p = self.parent.get(id(n))
                    value = None
                    if (isinstance(p, ast.Assign) and n in p.targets) or (
                        isinstance(p, ast.AnnAssign) and p.target is n
                    ):
                        value = p.value
                    if value is not None and self._literalish(value):
                        self.upper_assigned.add(n.id)
                    else:
                        self.upper_bad.add(n.id)
                elif isinstance(n, ast.arg) and UPPER.match(n.arg):
                    self.upper_bad.add(n.arg)
                elif isinstance(n, (ast.Global, ast.Nonlocal)):
                    self.upper_bad.update(x for x in n.names if UPPER.match(x))
                elif isinstance(n, (ast.Subscript, ast.Attribute)) and isinstance(
                    n.ctx, (ast.Store, ast.Del)
                ):
                    r = _root(n)
                    while isinstance(r, ast.Attribute):
                        r = r.value
                        r = _root(r)
                    if isinstance(r, ast.Name) and UPPER.match(r.id):
                        self.upper_bad.add(r.id)
                    if isinstance(n, ast.Attribute) and UPPER.match(n.attr):
                        self.upper_bad.add(n.attr)
                elif isinstance(n, ast.AugAssign):
                    r = _root(n.target)
                    if isinstance(r, ast.Name) and UPPER.match(r.id):
                        self.upper_bad.add(r.id)
                elif (
                    isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr in MUTATORS
                ):
                    r = _root(n.func.value)
                    if isinstance(r, ast.Name) and UPPER.match(r.id):
                        self.upper_bad.add(r.id)
                elif isinstance(n, ast.ImportFrom):
                    key = self._module_key(n.module or "", n.level, module)
                    if key is None:
                        self.upper_outside.setdefault(module, set()).update(
                            al.asname or al.name
                            for al in n.names
                            if UPPER.match(al.asname or al.name)
                        )
                elif isinstance(n, (*FUNCS, ast.ClassDef)) and UPPER.match(n.name):
                    self.upper_bad.add(n.name)

    def _class_ref(self, e) -> bool:
        """A name that stands for a class: defined in the scanned tree, or imported at the top of its module with a
        CapitalWord name, and not rebound by a parameter or a local name. A class is not text from a file."""
        name = e.id
        if not name[:1].isupper() or UPPER.match(name) or self._shadowed(e, name):
            return False
        if name in self._code_names and any(
            isinstance(n, ast.ClassDef) and n.name == name
            for t in self.trees.values()
            for n in ast.walk(t)
        ):
            return True
        if isinstance(getattr(builtins, name, None), type):
            return True  # `ValueError`, `KeyError` ...
        module = self.module_of.get(id(e))
        return name in self.imports.get(module, {})

    def _note_changed(self, n):
        """A name of the outer (module) scope that a function changes: `NAME[k] = v`, `NAME.update(...)`, `NAME += x`,
        `global NAME`. The module-level proof of the name ("only ever bound to written values") does not see these, so such
        a name is not code-owned (Round 15, Issue 1f). Names that the function binds itself are its own."""
        root = None
        if isinstance(n, (ast.Subscript, ast.Attribute)) and isinstance(
            n.ctx, (ast.Store, ast.Del)
        ):
            root = _root(n)
        elif isinstance(n, ast.AugAssign):
            root = _root(n.target)
        elif (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr in MUTATORS
        ):
            root = _root(n.func.value)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            self.changed_in_function.update(n.names)
            return
        if (
            isinstance(root, ast.Name)
            and isinstance(self.scope_of.get(id(n)), FUNCS)
            and not self._shadowed(n, root.id)
        ):
            self.changed_in_function.add(root.id)

    def _note_class_attr(self, node, scope, attr):
        """`self.attr = value` inside a method of class C (or a class-body assignment) makes `attr` an attribute of C."""
        cls = node.name if isinstance(node, ast.ClassDef) else None
        if cls is None:
            fn = scope
            while fn is not None and not isinstance(fn, ast.Module):
                if isinstance(fn, FUNCS):
                    d = next((x for x in self.defs if x["node"] is fn), None)
                    if d and d["cls"]:
                        cls = d["cls"]
                        break
                fn = self.scope_of.get(id(fn))
        if cls:
            self.cls_attrs.setdefault(cls, set()).add(attr)

    def _enclosing_def(self, node):
        fn = self.scope_of.get(id(node))
        while fn is not None and not isinstance(fn, ast.Module):
            if isinstance(fn, FUNCS):
                return fn
            fn = self.scope_of.get(id(fn))
        return None

    def _enclosing_class(self, node):
        fn = self.scope_of.get(id(node))
        while fn is not None and not isinstance(fn, ast.Module):
            if isinstance(fn, FUNCS):
                d = next((x for x in self.defs if x["node"] is fn), None)
                if d and d["cls"]:
                    return d["cls"]
            fn = self.scope_of.get(id(fn))
        return None

    def _class_has_attr(self, cls, attr, seen=None) -> bool:
        seen = seen or set()
        if cls in seen:
            return False
        seen.add(cls)
        return attr in self.cls_attrs.get(cls, ()) or any(
            self._class_has_attr(b, attr, seen) for b in self.cls_bases.get(cls, ())
        )

    def _library_receiver(self, e) -> bool:
        """Round 16 (Issue 3a): the receiver of an attribute is the error object of an `except`, text made from one, a
        name bound by `with`, or an imported name: an object of a library, whose attributes the package does not write."""
        root = e.value
        while isinstance(root, (ast.Attribute, ast.Subscript, ast.Call)):
            root = root.func if isinstance(root, ast.Call) else root.value
        if not isinstance(root, ast.Name):
            return False
        scope = self.scope_of.get(id(e))
        if root.id in self.taint_of(scope if scope is not None else next(iter(self.trees.values()))):
            return True
        module = self.module_of.get(id(e))
        if root.id in self.imports.get(module, {}):
            return True
        return self._bound_by_with(scope, root.id)

    def _bound_by_with(self, scope, name) -> bool:
        key = ("with", id(scope))
        if key not in self._with_cache:
            names: set[str] = set()
            if scope is not None:
                for n in _own(scope):
                    if isinstance(n, (ast.With, ast.AsyncWith)):
                        for it in n.items:
                            if it.optional_vars is not None:
                                names.update(nm.id for nm in _targets(it.optional_vars))
            self._with_cache[key] = names
        return name in self._with_cache[key]

    def _attr_read_ok(self, e) -> bool:
        """An attribute is code-owned when the package writes it only with code-owned values (`attr_safe`) or declares
        it a number, the receiver is not an object of a library, and a read through `self` is of an attribute that the
        class (or a base of it in the package) writes: the class's own `self.msg` is not proven by another class's
        `self.msg = "literal"` (Round 16, Issue 3a)."""
        a = e.attr
        if not (a in self.attr_safe or (a in self.attr_number and a not in self.attr_unsafe)):
            return False
        if self._library_receiver(e):
            return False
        if isinstance(e.value, ast.Name) and e.value.id in {"self", "cls"}:
            cls = self._enclosing_class(e)
            return cls is not None and self._class_has_attr(cls, a)
        # Round 17 (Issue 1a): any other receiver is trusted only when it is a name bound, in the same function, to a call of a
        # class of the package that writes the attribute (`k = K()` then `k.name`). A parameter, a call result or an object of
        # a library (a caught exception handed on as a parameter has a `.reason`) is not proven by a write elsewhere.
        return isinstance(e.value, ast.Name) and self._bound_to_class_with(e, e.value.id, a)

    def _bound_to_class_with(self, e, name, attr) -> bool:
        scope = self.scope_of.get(id(e))
        if scope is None:
            return False
        if isinstance(scope, FUNCS):
            for arg in _all_args(scope.args):
                if arg.arg == name:
                    # a parameter declared as a class of the package that holds the attribute (a declaration, not a run-time
                    # check: the same trust as a number annotation); any other parameter is not proven
                    ann = arg.annotation
                    cname = (
                        ann.id
                        if isinstance(ann, ast.Name)
                        else ann.value.split(".")[-1]
                        if isinstance(ann, ast.Constant) and isinstance(ann.value, str)
                        else ann.attr
                        if isinstance(ann, ast.Attribute)
                        else None
                    )
                    return cname in self.cls_attrs and self._class_has_attr(cname, attr)
        seen = False
        for n in _own(scope):
            if isinstance(n, ast.Assign) and any(name in {t.id for t in _targets(tt)} for tt in n.targets):
                f = n.value.func if isinstance(n.value, ast.Call) else None
                cname = f.id if isinstance(f, ast.Name) else None
                if cname is None or cname not in self.cls_attrs or not self._class_has_attr(cname, attr):
                    return False
                seen = True
            elif isinstance(n, (ast.AugAssign, ast.AnnAssign, ast.NamedExpr, ast.For, ast.AsyncFor)) and name in {
                t.id for t in _targets(n.target)
            }:
                return False
        return seen

    def _upper_ok(self, name, node) -> bool:
        """An UPPER_CASE name that is bound only to written values in the tree (see `_scan_upper`)."""
        module = self.module_of.get(id(node))
        if name in self.upper_bad or name in self.upper_outside.get(module, ()):
            return False
        return name in self.upper_assigned or name in {"TYPE_CHECKING"}

    def _walk(self, module, node, scope, cls):
        for ch in ast.iter_child_nodes(node):
            self.parent[id(ch)] = node
            self.scope_of[id(ch)] = scope
            self.module_of[id(ch)] = module
            if module.startswith("~callers/"):
                # a module outside the package (a demo): only its calls are read, to see what it passes to a parameter
                if isinstance(ch, ast.Call):
                    self.calls.append((module, ch, scope))
                self._walk(module, ch, ch if isinstance(ch, (*FUNCS, ast.ClassDef)) else scope, None)
                continue
            if isinstance(ch, FUNCS):
                params = [a.arg for a in [*ch.args.posonlyargs, *ch.args.args]]
                is_method = isinstance(node, ast.ClassDef) and params[:1] in (["self"], ["cls"])
                self.defs.append(
                    {
                        "node": ch,
                        "name": ch.name,
                        "cls": node.name if isinstance(node, ast.ClassDef) else None,
                        "params": params[1:] if is_method else params,
                        "module": module,
                    }
                )
                self._walk(module, ch, ch, None)
            elif isinstance(ch, ast.ClassDef):
                self.cls_bases.setdefault(ch.name, []).extend(
                    b.id if isinstance(b, ast.Name) else b.attr
                    for b in ch.bases
                    if isinstance(b, (ast.Name, ast.Attribute))
                )
                self._walk(module, ch, ch, ch.name)
            else:
                if isinstance(ch, ast.Call):
                    self.calls.append((module, ch, scope))
                if isinstance(ch, ast.Assign):
                    for t in ch.targets:
                        for a in self._attr_targets(t):
                            self.attr_assigns.setdefault(a, []).append((ch.value, scope))
                            self._note_class_attr(node, scope, a)
                elif (
                    isinstance(ch, ast.AugAssign)
                    and isinstance(ch.target, ast.Attribute)
                    or isinstance(ch, ast.AnnAssign)
                    and isinstance(ch.target, ast.Attribute)
                ):
                    self.attr_assigns.setdefault(ch.target.attr, []).append((ch.value, scope))
                    self._note_class_attr(node, scope, ch.target.attr)
                elif isinstance(ch, ast.AnnAssign) and isinstance(ch.target, ast.Name):
                    if isinstance(
                        node, ast.ClassDef
                    ):  # a class field: filled from outside unless a number
                        self.cls_attrs.setdefault(node.name, set()).add(ch.target.id)
                        if _is_number_annotation(ch.annotation):
                            self.attr_number.add(ch.target.id)
                        else:
                            self.attr_unsafe.add(ch.target.id)
                elif isinstance(ch, ast.Assign) and isinstance(node, ast.ClassDef):
                    for t in ch.targets:
                        for nm in _targets(t):
                            self.attr_assigns.setdefault(nm.id, []).append((ch.value, scope))
                            self.cls_attrs.setdefault(node.name, set()).add(nm.id)
                if isinstance(ch, ast.Call) and _adds_to(ch):
                    root = _root(ch.func.value)
                    if isinstance(root, ast.Attribute):
                        for a in [*ch.args, *(k.value for k in ch.keywords)]:
                            self.attr_assigns.setdefault(root.attr, []).append((a, scope))
                if (
                    isinstance(ch, ast.Call)
                    and isinstance(ch.func, ast.Attribute)
                    and ch.func.attr == "__setattr__"
                    and len(ch.args) == 3
                    and isinstance(ch.args[1], ast.Constant)
                    and isinstance(ch.args[1].value, str)
                ):
                    self.attr_assigns.setdefault(ch.args[1].value, []).append((ch.args[2], scope))
                if (
                    isinstance(ch, ast.Call)
                    and isinstance(ch.func, ast.Name)
                    and ch.func.id == "setattr"
                ):
                    if len(ch.args) == 3 and isinstance(ch.args[1], ast.Constant):
                        self.attr_assigns.setdefault(str(ch.args[1].value), []).append(
                            (ch.args[2], scope)
                        )
                    else:
                        self.attr_unsafe.add("*")
                self._walk(module, ch, scope, cls)

    def _module_key(self, dotted: str, level: int, module: str) -> str | None:
        """The key in `self.trees` of the module that an import names, or None when it is outside the scanned tree."""
        parts = dotted.split(".") if dotted else []
        if level:  # a relative import: the folder of the importing module, `level - 1` folders up
            here = module.split("/")[:-1]
            here = here[: len(here) - (level - 1)] if level > 1 else here
            parts = [*here, *parts]
        elif parts[:1] == ["hadavin_sdk"]:
            parts = parts[1:]
        else:
            return None
        for cand in ("/".join(parts) + ".py", "/".join([*parts, "__init__.py"])):
            if cand in self.trees:
                return cand
        return None

    def _read_imports(self, module, tree):
        """Which tree definition a local name stands for. A name imported from outside the scanned tree maps to
        `(None, name)`: a call of it is not a call of a function of the tree, whatever a tree function is called."""
        table = self.imports.setdefault(module, {})
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                key = self._module_key(n.module or "", n.level, module)
                for al in n.names:
                    local = al.asname or al.name
                    if key is None:
                        table.setdefault(local, set()).add((None, al.name))
                    else:
                        sub = self._module_key(
                            f"{n.module or ''}.{al.name}".strip("."), n.level, module
                        )
                        table.setdefault(local, set()).add((sub or key, None if sub else al.name))
            elif isinstance(n, ast.Import):
                for al in n.names:
                    local = (al.asname or al.name).split(".")[0]
                    table.setdefault(local, set()).add((None, al.name))

    def _shadowed(self, node, name) -> bool:
        """Is `name` bound by a parameter, an assignment, a loop, a `with`, an `except` or a local import in a function
        around `node`? Then a call of it is not a call of the function of that name."""
        scope = self.scope_of.get(id(node))
        while scope is not None and not isinstance(scope, ast.Module):
            if isinstance(scope, FUNCS):
                key = id(scope)
                if key not in self._shadow:
                    a = scope.args
                    names = {x.arg for x in [*a.posonlyargs, *a.args, *a.kwonlyargs] if x}
                    names |= {x.arg for x in (a.vararg, a.kwarg) if x}
                    for n in _own(scope):
                        if isinstance(n, ast.Assign):
                            names |= {t.id for tt in n.targets for t in _targets(tt)}
                        elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and isinstance(
                            n.target, ast.Name
                        ):
                            names.add(n.target.id)
                        elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
                            names |= {t.id for t in _targets(n.target)}
                        elif isinstance(n, ast.NamedExpr):
                            names.add(n.target.id)
                        elif isinstance(n, ast.ExceptHandler) and n.name:
                            names.add(n.name)
                        elif isinstance(n, (ast.With, ast.AsyncWith)):
                            for it in n.items:
                                if it.optional_vars is not None:
                                    names |= {t.id for t in _targets(it.optional_vars)}
                    self._shadow[key] = frozenset(names)
                if name in self._shadow[key]:
                    return True
            scope = self.scope_of.get(id(scope))
        return False

    def resolve(self, call) -> list[int] | None:
        """The indexes of the definitions that this call can reach, found by the REAL definition (the module that
        defines it, or the module it is imported from) and not by the bare name; None when the call may reach code
        outside the scanned tree (an imported library function that has the same name as a function of the tree is
        not that function)."""
        module = self.module_of.get(id(call))
        f = call.func
        if module is None:
            return None
        if isinstance(f, ast.Name):
            if self._shadowed(call, f.id):
                return None
            found: list[int] = []
            for i, d in enumerate(self.defs):
                if d["name"] == f.id and d["cls"] is None and d["module"] == module:
                    found.append(i)
            for key, orig in self.imports.get(module, {}).get(f.id, ()):
                if key is None or orig is None:
                    return None
                found += [
                    i
                    for i, d in enumerate(self.defs)
                    if d["name"] == orig and d["cls"] is None and d["module"] == key
                ]
            return found or None
        if (
            isinstance(f, ast.Attribute)
            and isinstance(f.value, ast.Name)
            and f.value.id in {"self", "cls"}
        ):
            scope, klass = self.scope_of.get(id(call)), None
            while scope is not None and not isinstance(scope, ast.Module):
                if isinstance(scope, ast.ClassDef):
                    klass = scope.name
                    break
                scope = self.scope_of.get(id(scope))
            mine = [
                i
                for i, d in enumerate(self.defs)
                if d["name"] == f.attr and d["cls"] == klass and d["module"] == module
            ]
            if mine:
                return mine
            # inherited or mixed in: every method of that name in the tree must be proven
            return [i for i, d in enumerate(self.defs) if d["name"] == f.attr and d["cls"]] or None
        return None

    @staticmethod
    def _attr_targets(t):
        if isinstance(t, ast.Attribute):
            yield t.attr
        elif isinstance(t, (ast.Tuple, ast.List)):
            for x in t.elts:
                yield from Analysis._attr_targets(x)

    # ---- the proof ----------------------------------------------------------------------------------------------
    def _def_candidates(self):
        """(index of def, parameter name) pairs that may be proven: a def called by name from the tree, not used as a
        value, not decorated (other than staticmethod / classmethod), not a dunder method but `__init__`."""
        by_name: dict[str, list[int]] = {}
        for i, d in enumerate(self.defs):
            by_name.setdefault(d["name"], []).append(i)
            if d["name"] == "__init__" and d["cls"]:
                by_name.setdefault(d["cls"], []).append(i)
        return by_name

    def _solve(self):
        by_name = self._def_candidates()
        self.by_name = by_name
        callers: dict[int, list[tuple]] = {}
        for _module, call, scope in self.calls:
            f = call.func
            fname = (
                f.id
                if isinstance(f, ast.Name)
                else f.attr
                if isinstance(f, ast.Attribute)
                else None
            )
            if fname is None:
                continue
            for i in by_name.get(fname, []):
                callers.setdefault(i, []).append((call, scope))
        self.callers = callers
        cand: set[tuple[int, str]] = set()
        for i, d in enumerate(self.defs):
            fn = d["node"]
            decorated = any(
                not (isinstance(x, ast.Name) and x.id in {"staticmethod", "classmethod"})
                for x in fn.decorator_list
            )
            dunder = d["name"].startswith("__") and d["name"] != "__init__"
            key = d["cls"] if d["name"] == "__init__" and d["cls"] else d["name"]
            if decorated or dunder or d["name"] in self.escaped or key in self.escaped:
                continue
            if not callers.get(i):
                continue
            for p in d["params"]:
                cand.add((i, p))
        self.psafe = cand
        self.fsafe = set(range(len(self.defs)))
        self.attr_safe = set(self.attr_assigns) - self.attr_unsafe
        if "*" in self.attr_unsafe:
            self.attr_safe = set()
        changed = True
        while changed:
            self._envs.clear()
            changed = False
            for i, p in sorted(self.psafe):
                if not self._param_ok(i, p):
                    self.psafe.discard((i, p))
                    changed = True
            for i in sorted(self.fsafe):
                if not self._func_ok(i):
                    self.fsafe.discard(i)
                    changed = True
            for a in sorted(self.attr_safe):
                if not all(
                    self.safe(v, self.env_of(s)) for v, s in self.attr_assigns[a] if v is not None
                ) or any(v is None for v, _ in self.attr_assigns[a]):
                    self.attr_safe.discard(a)
                    changed = True
        self._envs.clear()

    def _param_ok(self, i, p) -> bool:
        d = self.defs[i]
        fn = d["node"]
        pos = d["params"].index(p)
        is_method = len(d["params"]) < len([*fn.args.posonlyargs, *fn.args.args])
        for call, scope in self.callers[i]:
            if any(isinstance(a, ast.Starred) for a in call.args) or any(
                k.arg is None for k in call.keywords
            ):
                return False
            env = self.env_of(scope)
            arg = None
            if pos < len(call.args):
                # `Class.method(self, x)` called through the class is not told apart: positions are as written
                arg = call.args[pos]
            else:
                for k in call.keywords:
                    if k.arg == p:
                        arg = k.value
            if arg is None:
                dflt = self._default(fn, p, is_method)
                if dflt is not None and not self.safe(dflt, frozenset()):
                    return False
                if dflt is None:
                    return False
                continue
            if not self.safe(arg, env):
                return False
        return True

    @staticmethod
    def _default(fn, p, is_method):
        a = fn.args
        plain = [*a.posonlyargs, *a.args]
        defaults = [None] * (len(plain) - len(a.defaults)) + list(a.defaults)
        for arg, dv in zip(plain, defaults, strict=True):
            if arg.arg == p:
                return dv
        for arg, dv in zip(a.kwonlyargs, a.kw_defaults, strict=True):
            if arg.arg == p:
                return dv
        return None

    def _func_ok(self, i) -> bool:
        fn = self.defs[i]["node"]
        env = self.env_of(fn)
        rets = [r.value for r in _own(fn) if isinstance(r, ast.Return)]
        return bool(rets) and all(v is not None and self.safe(v, env) for v in rets)

    def env_of(self, scope) -> frozenset[str]:
        key = id(scope)
        if key in self._envs:
            return self._envs[key]
        outer: frozenset[str] = frozenset()
        parent_scope = self.scope_of.get(key)
        if parent_scope is not None and parent_scope is not scope:
            outer = self.env_of(parent_scope)
        self._envs[key] = outer  # a guard against recursion
        env = self._scope_env(scope, outer)
        self._envs[key] = env
        return env

    def _scope_env(self, scope, outer) -> frozenset[str]:
        bindings: dict[str, list] = {}
        unsafe: set[str] = set()
        if isinstance(scope, FUNCS):
            a = scope.args
            idx = next((i for i, d in enumerate(self.defs) if d["node"] is scope), None)
            for arg in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg]:
                if arg is None:
                    continue
                # Round 16 (Issue 2, 3): a parameter annotated as a number is trusted only when every caller in the
                # scanned tree passes a number (or a proven value); with no caller in the tree the annotation is all
                # there is to read (an entry point called from outside)
                if (idx is not None and (idx, arg.arg) in self.psafe) or (
                    _is_number_annotation(arg.annotation)
                    and (idx is None or self._callers_pass_numbers(idx, arg.arg))
                ):
                    bindings.setdefault(arg.arg, [])
                else:
                    unsafe.add(arg.arg)
        for n in _own(scope):
            # `call_class_only(call, make_error)` hands `make_error` the CLASS NAME of the library error only
            # (errors.py): the parameter of that lambda is code-owned text
            if (
                isinstance(n, ast.Call)
                and _recv(n.func) == "call_class_only"
                and len(n.args) >= 2
                and isinstance(n.args[1], ast.Lambda)
            ):
                for arg in n.args[1].args.args:
                    bindings.setdefault(arg.arg, [])
            if isinstance(n, ast.Call) and _adds_to(n):
                # `x.append(v)`, `x[k].extend(v)`, `x.add(v)`: the list is as safe as what is added to it (round 14)
                root = _root(n.func.value)
                if isinstance(root, ast.Name):
                    for a in [*n.args, *(k.value for k in n.keywords)]:
                        bindings.setdefault(root.id, []).append(("assign", a))
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    for nm in _targets(t):
                        bindings.setdefault(nm.id, []).append(("assign", n.value))
                    if isinstance(t, ast.Subscript) and isinstance(_root(t), ast.Name):
                        bindings.setdefault(_root(t).id, []).append(("assign", n.value))
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                if _is_number_annotation(n.annotation) and n.value is None:
                    bindings.setdefault(n.target.id, [])
                elif _is_number_annotation(n.annotation):
                    # the annotation alone proves nothing: the value must be a number (round 16)
                    bindings.setdefault(n.target.id, []).append(("number", n.value))
                elif n.value is not None:
                    bindings.setdefault(n.target.id, []).append(("assign", n.value))
                else:
                    unsafe.add(n.target.id)
            elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
                bindings.setdefault(n.target.id, []).append(("aug", n.value))
            elif isinstance(n, ast.AugAssign) and isinstance(_root(n.target), ast.Name):
                bindings.setdefault(_root(n.target).id, []).append(("aug", n.value))
            elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
                # a comprehension's `for` binds like a loop's (`for i, op in enumerate(x, start=1)`)
                for nm in _targets(n.target):
                    bindings.setdefault(nm.id, []).append(("for", n))
            elif isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name):
                bindings.setdefault(n.target.id, []).append(("assign", n.value))
            elif isinstance(n, ast.ExceptHandler) and n.name:
                unsafe.add(n.name)
            elif isinstance(n, (ast.With, ast.AsyncWith)):
                for it in n.items:
                    if it.optional_vars is not None:
                        unsafe.update(nm.id for nm in _targets(it.optional_vars))
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                unsafe.update((al.asname or al.name).split(".")[0] for al in n.names)
            elif isinstance(n, (*FUNCS, ast.ClassDef)):
                unsafe.add(n.name)
            elif isinstance(n, (ast.Global, ast.Nonlocal)):
                unsafe.update(n.names)
        cand = {k for k in bindings if k not in unsafe}
        if isinstance(scope, ast.Module):
            cand -= (
                self.changed_in_function
            )  # a function changes it: not "only ever a written value"
        env = (set(outer) - set(bindings) - unsafe) | cand
        changed = True
        while changed:
            changed = False
            for name in sorted(cand):
                if name not in env:
                    continue
                ok = True
                for kind, val in bindings[name]:
                    if kind == "for":
                        ok = self._for_binds(val, name, frozenset(env))
                    elif kind == "number":
                        ok = self.number_valued(val, frozenset(env))
                    elif kind == "aug":
                        # `text += number` is a TypeError: an added number puts no text in the name
                        ok = self.safe(val, frozenset(env)) or self.number_valued(val, frozenset(env))
                    else:
                        ok = self.safe(val, frozenset(env))
                    if not ok:
                        break
                if not ok:
                    env.discard(name)
                    changed = True
        return frozenset(env)

    # ---- Round 16: values that are numbers by their form ----------------------------------------------------------
    _NUMBER_METHODS = frozenset({"find", "rfind", "index", "rindex", "count", "total_seconds"})
    _NUMBER_CALLS = frozenset({"len", "abs", "round", "ord", "hash", "id", "min", "max", "sum", "int", "float", "divmod"})

    def number_valued(self, e, env) -> bool:
        """True when the expression is a number whatever its operands hold: a number literal, a name proven code-owned or
        annotated as a number, `len(x)`, arithmetic of numbers, `min`/`max`/`sum`/`abs`/`round`/`int`/`float` of numbers,
        a call of a method that gives a position or a count (`find`, `index`, `count`)."""
        if isinstance(e, ast.Constant):
            return not isinstance(e.value, (str, bytes))
        if isinstance(e, ast.Name):
            return e.id in env
        if isinstance(e, ast.Attribute):
            return (
                e.attr in self.attr_number
                and e.attr not in self.attr_unsafe
                and not self._library_receiver(e)
            ) or self.safe(e, env)
        if isinstance(e, ast.UnaryOp):
            return self.number_valued(e.operand, env)
        if isinstance(e, ast.BinOp) and not isinstance(e.op, ast.Mod):
            return self.number_valued(e.left, env) and self.number_valued(e.right, env)
        if isinstance(e, ast.BinOp):
            return self.number_valued(e.left, env)
        if isinstance(e, ast.IfExp):
            return self.number_valued(e.body, env) and self.number_valued(e.orelse, env)
        if isinstance(e, ast.BoolOp):
            return all(self.number_valued(v, env) for v in e.values)
        if isinstance(e, ast.Call):
            f = e.func
            if isinstance(f, ast.Name) and f.id == "len":
                return True
            if isinstance(f, ast.Name) and f.id in self._NUMBER_CALLS:
                args = [*e.args, *(k.value for k in e.keywords)]
                return bool(args) and all(
                    self.number_valued(a, env)
                    or (
                        isinstance(a, (ast.GeneratorExp, ast.ListComp))
                        and self.number_valued(a.elt, env)
                    )
                    for a in args
                )
            if isinstance(f, ast.Attribute) and f.attr in self._NUMBER_METHODS:
                return True
            if self._declared_number_function(f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")):
                return True  # a function of the tree whose every definition is declared `-> int` or `-> float`
        return self.safe(e, env) and not self._is_texty(e)

    def _declared_number_function(self, name) -> bool:
        """Round 17 (Issue 1d): every function of the scanned tree with this name is declared to return `int` or `float`
        (`purge_tool_calls(...) -> int`). At least one definition must exist."""
        found = [d["node"] for d in self.defs if d["name"] == name]
        return bool(name) and bool(found) and all(
            n.returns is not None and ast.unparse(n.returns) in {"int", "float"} for n in found
        )

    def _callers_pass_numbers(self, i, p) -> bool:
        """Every caller in the scanned tree gives the parameter a number (or a proven value). No caller: True."""
        d = self.defs[i]
        fn = d["node"]
        pos = d["params"].index(p) if p in d["params"] else None
        is_method = len(d["params"]) < len([*fn.args.posonlyargs, *fn.args.args])
        for call, scope in getattr(self, "callers", {}).get(i, []):
            if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
                return False
            arg = (
                call.args[pos]
                if pos is not None and pos < len(call.args)
                else next((k.value for k in call.keywords if k.arg == p), None)
            )
            if arg is None:
                dflt = self._default(fn, p, is_method)
                if dflt is not None and not self.number_valued(dflt, frozenset()):
                    return False
                continue
            if not self.number_valued(arg, self.env_of(scope)):
                return False
        return True

    def _for_binds(self, forn, name, env) -> bool:
        """Does this `for` loop bind `name` to a code-owned value: a counter, or an item of a code-owned collection."""
        it = forn.iter
        call = it if isinstance(it, ast.Call) else None
        fname = call.func.id if call is not None and isinstance(call.func, ast.Name) else None
        t = forn.target
        if fname == "range":
            return True
        if fname == "enumerate" and isinstance(t, ast.Tuple) and len(t.elts) == 2:
            if name in {n.id for n in _targets(t.elts[0])}:
                return True
            inner = call.args[0] if call.args else None
            return inner is not None and self.safe(inner, env)
        return self.safe(it, env)

    def safe(self, e, env) -> bool:
        """True when the expression is proven code-owned (see the module text)."""
        if isinstance(e, ast.Constant):
            return True
        if isinstance(e, ast.JoinedStr):
            return all(self.safe(p, env) for p in e.values)
        if isinstance(e, ast.FormattedValue):
            spec = e.format_spec
            number = (
                isinstance(spec, ast.JoinedStr)
                and len(spec.values) == 1
                and isinstance(spec.values[0], ast.Constant)
                and isinstance(spec.values[0].value, str)
                and NUMBER_SPEC.fullmatch(spec.values[0].value) is not None
            )
            return number or self.safe(e.value, env)
        if isinstance(e, ast.Name):
            return (
                e.id in env
                or (bool(UPPER.match(e.id)) and self._upper_ok(e.id, e))
                or e.id in {"__name__", "__file__"}
                or self._class_ref(e)
            )
        if isinstance(e, ast.Attribute):
            if e.attr in {"__name__", "__qualname__", "__module__"}:
                return True
            if UPPER.match(e.attr):
                return e.attr not in self.upper_bad
            return self._attr_read_ok(e)
        if isinstance(e, ast.Call):
            return self._call_safe(e, env)
        if isinstance(e, ast.BinOp):
            if isinstance(
                e.op,
                (
                    ast.Sub,
                    ast.FloorDiv,
                    ast.Pow,
                    ast.BitAnd,
                    ast.BitOr,
                    ast.BitXor,
                    ast.LShift,
                    ast.RShift,
                ),
            ):
                # Round 16 (Issue 3b): these make no text, but `set(names) - ALLOWED` and `a | b` of sets make a collection
                # that a message can show: safe only when both operands are proven or are numbers
                return all(self.safe(x, env) or self.number_valued(x, env) for x in (e.left, e.right))
            if isinstance(e.op, ast.Add) and (_is_number(e.left) or _is_number(e.right)):
                return True  # `name + 1` is a number sum
            if isinstance(e.op, ast.Mod) and _is_number(e.left):
                return True
            return self.safe(e.left, env) and self.safe(e.right, env)
        if isinstance(e, ast.UnaryOp):
            return True if isinstance(e.op, ast.Not) else self.safe(e.operand, env)
        if isinstance(e, ast.Compare):
            return True
        if isinstance(e, ast.BoolOp):
            return all(self.safe(v, env) for v in e.values)
        if isinstance(e, ast.IfExp):
            return self.safe(e.body, env) and self.safe(e.orelse, env)
        if isinstance(e, (ast.Tuple, ast.List, ast.Set)):
            return all(self.safe(x, env) for x in e.elts)
        if isinstance(e, ast.Dict):
            return all(k is None or self.safe(k, env) for k in e.keys) and all(
                self.safe(v, env) for v in e.values
            )
        if isinstance(e, ast.Starred):
            return self.safe(e.value, env)
        if isinstance(e, ast.Subscript):
            return self.safe(
                e.value, env
            )  # a lookup in a code-owned table gives what the table holds
        if isinstance(e, ast.Lambda):
            return True
        if isinstance(e, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
            inner = set(env)
            for g in e.generators:
                fake = ast.For(target=g.target, iter=g.iter, body=[], orelse=[])
                for nm in _targets(g.target):
                    if self._for_binds(fake, nm.id, frozenset(inner)):
                        inner.add(nm.id)
                    else:
                        inner.discard(nm.id)
            if isinstance(e, ast.DictComp):
                return self.safe(e.key, frozenset(inner)) and self.safe(e.value, frozenset(inner))
            return self.safe(e.elt, frozenset(inner))
        if isinstance(e, ast.NamedExpr):
            return self.safe(e.value, env)
        return False

    def _call_safe(self, e, env) -> bool:
        f = e.func
        args = [*e.args, *(k.value for k in e.keywords)]
        if isinstance(f, ast.Name):
            if f.id in FILTERS:
                return self._filter_is_ours(e)
            if f.id in SAFE_CALLS:
                return True
            if f.id in PASS_CALLS:
                return all(self.safe(a, env) for a in args)
            return self._resolved_safe(e)
        if isinstance(f, ast.Attribute):
            if f.attr in TEXT_METHODS:
                return self.safe(f.value, env) and all(self.safe(a, env) for a in args)
            return self._resolved_safe(e)
        return False

    def _filter_is_ours(self, call) -> bool:
        """Round 15, Issue 1e: `shown_name(x)` hides the text only when `shown_name` is the package's own function: not a
        parameter or local name that happens to be called that, and not imported from a library."""
        name = call.func.id
        if self._shadowed(call, name):
            return False
        module = self.module_of.get(id(call))
        # Round 16 (Issue 3c): the filter is the function defined in `FILTER_MODULE` (errors.py), by module and name, not
        # any function of the tree that has the name; its body is read by the guard (`return x` in it is a site)
        mine = [d for d in self.defs if d["name"] == name and not d["cls"]]
        if not mine:
            return False
        if all(d["module"] == FILTER_MODULE for d in mine):
            if module == FILTER_MODULE:
                return True
            found = self.imports.get(module, {}).get(name, ())
            return bool(found) and all(key == FILTER_MODULE for key, _orig in found)
        # a wrapper of one line in another module: `def _named(x): return shown_name(x)`
        return all(self._is_wrapper(d) for d in mine) and all(d["module"] == module for d in mine)

    def _is_wrapper(self, d, depth=0) -> bool:
        body = [b for b in d["node"].body if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant))]
        if depth > 2 or len(body) != 1 or not isinstance(body[0], ast.Return):
            return False
        v = body[0].value
        return (
            isinstance(v, ast.Call)
            and isinstance(v.func, ast.Name)
            and v.func.id in FILTERS
            and v.func.id != d["name"]
            and self._filter_is_ours(v)
        )

    def _resolved_safe(self, call) -> bool:
        """Every definition the call can reach (by module and class, see `resolve`) returns code-owned text."""
        f = call.func
        name = f.id if isinstance(f, ast.Name) else f.attr
        if name in self.escaped:
            return False
        found = self.resolve(call)
        # a function declared `-> int`, `-> float`, `-> bool` or `-> Literal[...]` makes no text: a declaration, not a run-time
        # check (batch 17: the exit code of `main`, which was proven through an attribute read the guard no longer trusts)
        return bool(found) and all(
            i in self.fsafe or _is_number_annotation(self.defs[i]["node"].returns) for i in found
        )

    # ---- the sites ----------------------------------------------------------------------------------------------
    def sites(self, module):
        """[(node, kind)] of every place in `module` that builds message text from a value not proven code-owned."""
        tree = self.trees[module]
        out = []
        inside: set[int] = set()
        safe = self.safe

        def env_for(node):
            return self.env_of(self.scope_of.get(id(node), tree))

        def bare_unsafe(args, env):
            # `+` and `%` and f-strings are sites of their own; a `/` (a path join) is not, so it is read here
            plain = [
                a
                for a in args
                if not (isinstance(a, ast.BinOp) and not isinstance(a.op, ast.Div))
                and not isinstance(a, ast.JoinedStr)
                and not self._is_text_call(a)
            ]
            return any(not safe(a, env) for a in plain)

        for node in ast.walk(tree):
            if id(node) in inside:
                continue
            env = env_for(node)
            hit, site = False, node
            if isinstance(node, ast.JoinedStr):
                hit = not safe(node, env)
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                hit = not _is_number(node.left) and not safe(node.right, env)
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                hit = not (_is_number(node.left) or _is_number(node.right)) and not safe(node, env)
            elif isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
                # `text += number` is a TypeError, so an added value that is a number (a count) puts no text in the target
                hit = not (safe(node.value, env) or self.number_valued(node.value, env))
            elif isinstance(node, ast.Call):
                f = node.func
                args = [*node.args, *(k.value for k in node.keywords)]
                if isinstance(f, ast.Name) and f.id == "print":
                    # `file=` and `flush=` of print say where and how, never what: not text. `sep=` and `end=` are put between and after
                    # the text, so they ARE scanned (a name as the separator is a site; pinned by mutant Z34)
                    args = [
                        *node.args,
                        *(k.value for k in node.keywords if k.arg not in _PRINT_HOW),
                    ]
                fa = f.attr if isinstance(f, ast.Attribute) else None
                fn = f.id if isinstance(f, ast.Name) else None
                if fa in {"format", "format_map", "join"}:
                    hit = not safe(f.value, env) or any(not safe(a, env) for a in args)
                elif fn == "Template" or fa in {"substitute", "safe_substitute"}:
                    hit = any(not safe(a, env) for a in args)
                elif fa in COLLECTORS:
                    # an f-string, a sum, a `%`, a format or a join that is not proven is a site of its own (read there)
                    unsafe = [
                        a
                        for a in args
                        if not safe(a, env)
                        and not isinstance(a, (ast.JoinedStr, ast.BinOp))
                        and not self._is_text_call(a)
                    ]
                    hit = bool(unsafe) and (
                        self._reaches_message(node, tree)
                        or (
                            self._returned(node, tree)
                            and any(
                                self._is_texty(a)
                                or isinstance(a, (ast.Name, ast.Attribute, ast.Subscript))
                                for a in unsafe
                            )
                        )
                    )
                elif (
                    fa in LOG_METHODS
                    or fa == "add_note"
                    or fn == "print"
                    or fa in {"write", "writelines"}
                    and (
                        _recv(f.value) in {"stderr", "stdout"}
                        or (isinstance(f.value, ast.Name) and f.value.id in self._streams(node))
                    )
                ):
                    if fa in LOG_METHODS:
                        args = self._without_number_directives(node, args, env)
                    hit = bare_unsafe(args, env)
                elif fa in {"dumps", "dump"} and _recv(f.value) == "json":
                    hit = any(not safe(a, env) for a in args)
                elif fa == "exit" and _recv(f.value) == "sys":
                    hit = bare_unsafe(args, env)  # `sys.exit(text)` prints the text
                elif fn in {"exit", "quit"}:
                    hit = bare_unsafe(args, env)  # the builtins `exit(text)` and `quit(text)` print the text like `sys.exit`
                elif fn == "getLogger" or fa == "getLogger":
                    hit = any(not safe(a, env) for a in args)  # the logger's name is on every line it writes
                elif fn == "Thread" or fa == "Thread":
                    # the thread's name is in every log line that has `%(threadName)s` and in every thread dump
                    hit = any(not safe(k.value, env) for k in node.keywords if k.arg == "name")
                if not hit and (
                    fa == "exception"
                    or fa in CHAIN_PRINTERS
                    or fn in CHAIN_PRINTERS
                    or any(
                        k.arg == "exc_info"
                        and not (isinstance(k.value, ast.Constant) and not k.value.value)
                        for k in node.keywords
                    )
                ):
                    hit = True  # these print the whole chain of the error, library text included (Round 15, Issue 1d)
                if (
                    not hit
                    and self._builds_error(fn or fa or "")
                    and not isinstance(self.parent.get(id(node)), ast.Raise)
                ):
                    hit = bare_unsafe(
                        args, env
                    )  # an error object built outside a `raise` (Issue 1b)
                tn = self.taint_of(self.scope_of.get(id(node), tree))
                if not hit:
                    # a keyword that carries text of an error or made on the spot: `Result(error_code=str(exc))`, or
                    # through a local name bound to it (Round 16, Issue 2)
                    hit = any(
                        self._tainted(k.value, tn, env) for k in node.keywords if k.arg not in _PRINT_HOW
                    )
                if not hit and fn is not None and fn[:1].isupper() and not isinstance(self.parent.get(id(node)), ast.Raise):
                    # a positional argument of a class of the package: `Result(str(exc))` (Round 16, Issue 2)
                    hit = any(self._tainted(a, tn, env) for a in node.args)
                if not hit and fa in COLLECTORS:
                    hit = any(self._tainted(a, tn, env) for a in args)
                if not hit and fa is not None and fa.startswith(STORE_CALL_PREFIXES):
                    # Round 17 (Issue 1b): a positional argument of `update`, `insert`, `write`, `execute`, `append`, `put` and their
                    # relatives (`updatemany`, `put_nowait`, `executemany`) that is made from an error
                    hit = any(self._tainted(a, tn, env) for a in node.args)
                if not hit and self._is_conversion(node):
                    # `str(x)`, `repr(x)`, `format(x)`, `ascii(x)` of a value not proven code-owned makes text on the spot
                    hit = any(not safe(a, env) for a in node.args)
                if not hit and self._raising_helper_in_handler(node):
                    hit = True  # a helper that raises, called inside an `except`: the library error is its `__context__`
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and any(
                isinstance(t, (ast.Attribute, ast.Subscript))
                for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
            ):
                # an attribute or an item set to text of an error or made on the spot: `self.error_code = str(exc)`,
                # `rec["error"] = text` with `text = str(exc)` (Round 16, Issue 2)
                hit = node.value is not None and self._tainted(
                    node.value, self.taint_of(self.scope_of.get(id(node), tree)), env
                )
                site = node
            elif isinstance(node, ast.Dict):
                tn = self.taint_of(self.scope_of.get(id(node), tree))
                for v in node.values:  # the value is the site, not the whole dict
                    if v is not None and self._tainted(v, tn, env):
                        out.append((v, "message"))
            elif isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)) and node.value is not None:
                hit = self._tainted(
                    node.value, self.taint_of(self.scope_of.get(id(node), tree)), env
                )
                if not hit and module == FILTER_MODULE and isinstance(node, ast.Return):
                    # the body of a text filter is read like any other code: it returns text that is not proven code-owned
                    # when `return x` gives back its argument (`def shown_name(x): return x`)
                    fn_def = self._enclosing_def(node)
                    hit = fn_def is not None and fn_def.name in FILTERS and not safe(node.value, env)
                    if hit:
                        site = node.value  # the value is the site: the one row of a filter body names the value
            elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                args = [*node.exc.args, *(k.value for k in node.exc.keywords)]
                hit = bare_unsafe(args, env)
                site = node.exc
            elif isinstance(node, ast.Assert) and node.msg is not None:
                # `assert ok, name`: the message is the text of the AssertionError that the traceback prints (Round 17, Issue 1c)
                hit = bare_unsafe([node.msg], env)
                site = node.msg
            if hit:
                inside.update(id(n) for n in ast.walk(site) if n is not site)
                out.append((site, "message"))
            if (
                isinstance(node, ast.Raise)
                and node.cause is not None
                and not isinstance(node.cause, ast.Constant)
            ):
                out.append((node, "cause"))
            elif (
                isinstance(node, ast.Raise)
                and node.exc is not None
                and node.cause is None
                and self._in_handler(node)
            ):
                # `raise X("fixed")` inside an `except` with no `from`: the old error stays as `__context__` and the
                # traceback prints it (Round 15, Issue 1d). `from None` and a raise after the block are not sites.
                out.append((node, "context"))
        return out

    # ---- Round 16 (Issue 2): taint ------------------------------------------------------------------------------
    def taint_of(self, scope) -> frozenset[str]:
        """The names of one scope that hold the error object of an `except ... as name`, or text made from one or from a
        value not proven code-owned (`text = str(exc)`, `first = exc.args[0]`), followed through further assignments."""
        key = ("taint", id(scope))
        if key in self._envs:
            return self._envs[key]
        env = self.env_of(scope)
        tainted: set[str] = set()
        nodes = list(_own(scope))
        for n in nodes:
            if isinstance(n, ast.ExceptHandler) and n.name:
                tainted.add(n.name)
        changed = True
        while changed:
            changed = False
            for n in nodes:
                pairs = []
                if isinstance(n, ast.Assign):
                    pairs = [(nm.id, n.value) for t in n.targets for nm in _targets(t)]
                elif ((isinstance(n, ast.AnnAssign) and n.value) or isinstance(n, ast.NamedExpr)) and isinstance(n.target, ast.Name):
                    pairs = [(n.target.id, n.value)]
                for name, val in pairs:
                    if name not in tainted and self._tainted(val, frozenset(tainted), env):
                        tainted.add(name)
                        changed = True
        self._envs[key] = frozenset(tainted)
        return self._envs[key]

    def _tainted(self, e, tainted, env) -> bool:
        """Is the expression the error object, a part of it, or text made on the spot from a value not proven code-owned."""
        if isinstance(e, ast.Name):
            return e.id in tainted
        if isinstance(e, (ast.Attribute, ast.Subscript)):
            root = _root(e.value) if isinstance(e, ast.Attribute) else _root(e)
            while isinstance(root, ast.Attribute):
                root = root.value
            return isinstance(root, ast.Name) and root.id in tainted
        if isinstance(e, ast.Call):
            if self._is_conversion(e):
                return any(self._tainted(a, tainted, env) or not self.safe(a, env) for a in e.args)
            f = e.func
            if isinstance(f, ast.Attribute) and f.attr in TEXT_METHODS:
                return self._tainted(f.value, tainted, env)
            return False
        if isinstance(e, ast.IfExp):
            return self._tainted(e.body, tainted, env) or self._tainted(e.orelse, tainted, env)
        if isinstance(e, ast.BoolOp):
            return any(self._tainted(v, tainted, env) for v in e.values)
        # Round 17 (Issue 1b): a collection that holds a tainted value is tainted: the wrapper hides nothing
        if isinstance(e, ast.Tuple):
            return any(self._tainted(x, tainted, env) for x in e.elts)
        if isinstance(e, ast.List):
            return any(self._tainted(x, tainted, env) for x in e.elts)
        if isinstance(e, ast.Set):
            return any(self._tainted(x, tainted, env) for x in e.elts)
        if isinstance(e, ast.Dict):
            return any(
                v is not None and self._tainted(v, tainted, env) for v in [*e.keys, *e.values]
            )
        if isinstance(e, ast.Starred):
            return self._tainted(e.value, tainted, env)
        return False

    def _raising_helper_in_handler(self, call) -> bool:
        """A call, inside an `except` block, of a function of the package that raises with no `from None`: the library
        error stays as its `__context__` and a printed traceback shows its text (Round 16, Issue 2)."""
        if not self._in_handler(call) or isinstance(self.parent.get(id(call)), ast.Raise):
            return False
        found = self.resolve(call)
        if not found:
            return False
        for i in found:
            for r in _own(self.defs[i]["node"]):
                if isinstance(r, ast.Raise) and isinstance(r.exc, ast.Call) and not (
                    isinstance(r.cause, ast.Constant) and r.cause.value is None
                ):
                    return True
        return False

    _DIRECTIVE = re.compile(r"%(?:\([^)]*\))?[#0\- +]*(?:\*|\d+)?(?:\.(?:\*|\d+))?[hlL]?([a-zA-Z%])")

    def _streams(self, node) -> frozenset[str]:
        """Names of the scope around `node` that are bound to `sys.stderr` or `sys.stdout` (`err = sys.stderr`), and names
        imported from `sys` (`from sys import stderr as err`): writing to them is printing (Round 17, Issue 1c)."""
        scope = self.scope_of.get(id(node))
        names: set[str] = set()
        for sc in {id(scope): scope, id(self.trees.get(self.module_of.get(id(node)))): self.trees.get(self.module_of.get(id(node)))}.values():
            if sc is None:
                continue
            for n in _own(sc):
                if isinstance(n, ast.Assign) and isinstance(n.value, ast.Attribute) and n.value.attr in {"stderr", "stdout"} and _recv(n.value.value) == "sys":
                    names |= {t.id for tt in n.targets for t in _targets(tt)}
                elif isinstance(n, ast.ImportFrom) and n.module == "sys":
                    names |= {al.asname or al.name for al in n.names if al.name in {"stderr", "stdout"}}
        return frozenset(names)

    def _without_number_directives(self, call, args, env=frozenset()):
        """A logging call `log.error("seq %d", seq)`: an argument that meets a number directive (`%d`, `%i`, `%f`...) is
        shown as a number or the call fails with the class of the error, never with the value (Round 16)."""
        pos = [a for a in call.args]
        for k, a in enumerate(pos):
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                kinds = [m for m in self._DIRECTIVE.findall(a.value) if m != "%"]
                rest = pos[k + 1 :]
                # Round 17 (Issue 1d): an argument is dropped only when it is PROVEN a number: a `%d` of a text makes the logging
                # module fail, and its failure handler prints the message and the arguments (`Message:` and `Arguments:`)
                drop = {
                    id(rest[j])
                    for j, c in enumerate(kinds)
                    if j < len(rest) and c in "dixXofeEgG" and self.number_valued(rest[j], env)
                }
                return [x for x in args if id(x) not in drop]
        return args

    def _error_classes(self) -> frozenset[str]:
        """Round 16 (Issue 2): the classes of the scanned tree that are errors: a class whose base is a built-in
        exception, a name that ends in a library error suffix, or another class found here. Derived from the bases, not from
        the spelling of the class's own name (`DuplicateEvent` and `Unqualified` end in no suffix)."""
        if self._errs is not None:
            return self._errs
        bases: dict[str, list[str]] = {}
        for t in self.trees.values():
            for n in ast.walk(t):
                if isinstance(n, ast.ClassDef):
                    names = [b.id if isinstance(b, ast.Name) else b.attr for b in n.bases if isinstance(b, (ast.Name, ast.Attribute))]
                    bases.setdefault(n.name, []).extend(names)
        errs: set[str] = set()
        changed = True
        while changed:
            changed = False
            for cls, bs in bases.items():
                if cls in errs:
                    continue
                if any(
                    b in errs
                    or (isinstance(getattr(builtins, b, None), type) and issubclass(getattr(builtins, b), BaseException))
                    or (b not in bases and b.endswith(ERROR_SUFFIXES))
                    for b in bs
                ):
                    errs.add(cls)
                    changed = True
        self._errs = frozenset(errs)
        return self._errs

    def _builds_error(self, name: str) -> bool:
        """A call of a class that is an error: a class of the scanned tree that derives from an exception, or a name
        outside the tree that ends in a library error suffix. A class of the tree that derives from none (the context
        manager `Failed`) is not an error object, whatever its name says."""
        if name in self._error_classes():
            return True
        if self._defined is None:
            self._defined = frozenset(
                n.name for t in self.trees.values() for n in ast.walk(t) if isinstance(n, ast.ClassDef)
            )
        return name not in self._defined and name.endswith(ERROR_SUFFIXES)

    _errs: frozenset[str] | None = None
    _defined: frozenset[str] | None = None

    def _in_handler(self, node) -> bool:
        p = self.parent.get(id(node))
        while p is not None and not isinstance(p, (*FUNCS, ast.Module, ast.ClassDef, ast.Lambda)):
            if isinstance(p, ast.ExceptHandler):
                return True
            p = self.parent.get(id(p))
        return False

    def _reaches_message(self, call, tree, depth=0) -> bool:
        """Is the collection that `call` adds to read, in the same scope, by something that makes or shows text. A list
        that is a PARAMETER is an out-parameter: the caller's own list is read there (Round 15, Issue 1c)."""
        recv = _root(call.func.value)
        if isinstance(recv, ast.Name) and depth < 3:
            fn = self.scope_of.get(id(call), tree)
            if isinstance(fn, FUNCS):
                i = next((k for k, d in enumerate(self.defs) if d["node"] is fn), None)
                if i is not None and recv.id in self.defs[i]["params"]:
                    pos = self.defs[i]["params"].index(recv.id)
                    for c, scope in self.callers.get(i, []):
                        arg = c.args[pos] if pos < len(c.args) else None
                        if arg is not None and isinstance(arg, ast.Name):
                            probe = ast.Call(
                                func=ast.Attribute(value=arg, attr="append", ctx=ast.Load()),
                                args=[],
                                keywords=[],
                            )
                            self.scope_of[id(probe)] = scope
                            self.parent[id(probe)] = c
                            if self._reaches_message(probe, tree, depth + 1):
                                return True
        if isinstance(recv, ast.Name):
            nodes = _own(self.scope_of.get(id(call), tree))

            def mentioned(n):
                return any(isinstance(x, ast.Name) and x.id == recv.id for x in _read_parts(n))
        elif isinstance(recv, ast.Attribute):
            nodes = ast.walk(tree)

            def mentioned(n):
                return any(
                    isinstance(x, ast.Attribute) and x.attr == recv.attr for x in _read_parts(n)
                )
        else:
            return True  # a collection we cannot name: assume it reaches a message
        for n in nodes:
            if n is call:
                continue
            if isinstance(n, ast.Raise) and n.exc is not None and mentioned(n.exc):
                return True
            if isinstance(n, ast.JoinedStr) and mentioned(n):
                return True
            if (
                isinstance(n, ast.BinOp)
                and isinstance(n.op, (ast.Mod, ast.Add))
                and mentioned(n)
                and not _is_number(n.left)
                and not _is_number(n.right)
            ):
                return True
            if isinstance(n, ast.Call):
                f = n.func
                fa = f.attr if isinstance(f, ast.Attribute) else None
                fn = f.id if isinstance(f, ast.Name) else None
                sink = (
                    fa in {"format", "format_map", "join", "add_note"}
                    or fa in LOG_METHODS
                    or fn == "print"
                    or (fa == "write" and _recv(f.value) in {"stderr", "stdout"})
                )
                if sink and mentioned(n):
                    return True
        return False

    def _returned(self, call, tree) -> bool:
        recv = _root(call.func.value)
        if not isinstance(recv, ast.Name):
            return False
        for n in _own(self.scope_of.get(id(call), tree)):
            if (
                isinstance(n, (ast.Return, ast.Yield))
                and n.value is not None
                and any(isinstance(x, ast.Name) and x.id == recv.id for x in ast.walk(n.value))
            ):
                return True
        return False

    @staticmethod
    def _is_conversion(a) -> bool:
        """`str(x)`, `repr(x)`, `ascii(x)`, `format(x)`: text made from a value on the spot."""
        return (
            isinstance(a, ast.Call)
            and isinstance(a.func, ast.Name)
            and a.func.id in {"str", "repr", "format", "ascii"}
        )

    @staticmethod
    def _is_texty(a) -> bool:
        """A value that is text made on the spot: `str(x)`, `repr(x)`, an f-string, a format, a join, a sum, a `%`."""
        if isinstance(a, (ast.JoinedStr, ast.BinOp)):
            return True
        return isinstance(a, ast.Call) and (
            (isinstance(a.func, ast.Name) and a.func.id in {"str", "repr", "format", "ascii"})
            or (
                isinstance(a.func, ast.Attribute)
                and a.func.attr in {"format", "format_map", "join"}
            )
        )

    @staticmethod
    def _is_text_call(a) -> bool:
        return (
            isinstance(a, ast.Call)
            and isinstance(a.func, ast.Attribute)
            and a.func.attr in {"format", "format_map", "join"}
        )


def violations(sources, allowed, exempt, callers=None):
    """(found, stale): sites not in `allowed` (keyed by (module, site text); a `cause` site by its whole raise
    statement), and allowance entries that match no site."""
    every = set(sources)
    sources = {m: t for m, t in sources.items() if not any(m.startswith(e) for e in exempt)}
    # Round 16 (Issue 2): `callers` are modules outside the package (the demos) that call the package's functions: they
    # are read for what they pass to a parameter, but no site is looked for in them
    an = Analysis({**sources, **{f"~callers/{m}": t for m, t in (callers or {}).items()}})
    found, matched = [], set()
    for module in sources:
        for node, kind in an.sites(module):
            key = (module, ast.unparse(node))
            if key in allowed:
                matched.add(key)
            else:
                found.append(f"{module}:{node.lineno}: [{kind}] {ast.unparse(node)}")
    stale = [f"{k[0]}: {k[1]}" for k in allowed if k not in matched]
    stale += [
        f"exempt {e}: no such module" for e in exempt if not any(m.startswith(e) for m in every)
    ]
    return found, stale
