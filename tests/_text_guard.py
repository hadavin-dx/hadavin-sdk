"""The message-site guard of Q8a-1 (round 12, Issue 2): a value that a person or a log can read must be PROVEN to be
written in the code, or the site must be in the allowance table with a true reason.

Before round 12 the guard was a list of spellings that mean "text from a configuration file" (`name`, `path`,
`settings.x` ...). Four reviews each found another spelling. This module turns the rule round: at every site that builds
message text it asks "is every inserted value proven code-owned?". A value is code-owned when it is

* a literal (text, number, bytes), or an UPPER_CASE constant, or a class name (`type(x).__name__`);
* a number: `len(x)`, `int(x)`, arithmetic, a loop counter (`range`, the first part of `enumerate`), a name or an
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
import re

SAFE_CALLS = frozenset(
    {
        "len", "int", "float", "bool", "round", "abs", "ord", "id", "hash", "isinstance", "any", "all",
        "callable", "hasattr", "range", "enumerate", "zip", "divmod", "chr", "type", "isfinite",
        "shown_name", "_named", "shown_names", "digest_prefix", "error_where", "word_like", "is_digest",
    }
)  # fmt: skip
PASS_CALLS = frozenset(
    {
        "sorted", "list", "tuple", "set", "frozenset", "reversed", "min", "max", "str", "repr", "format",
        "ascii", "iter", "next", "dict", "sum", "filter", "map",
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
# the receivers of `.append(...)`, `.extend(...)`, `.add(...)` that collect text for a person
PROBLEM_LIST = re.compile(
    r"problem|error|err|issue|message|msg|note|warn|reason|finding|violation|fail|detail|lines|refus",
    re.IGNORECASE,
)
UPPER = re.compile(r"^_*[A-Z][A-Z0-9_]*$")
NUMBER_SPEC = re.compile(r"[0-9.,_<>^+ -]*[dfxXeEgGbo%]")
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


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


def _own(root):
    """The nodes of one scope: not those of a function or a class defined inside it (but the definition itself)."""
    todo = list(ast.iter_child_nodes(root))
    while todo:
        n = todo.pop()
        yield n
        if not isinstance(n, (*FUNCS, ast.Lambda, ast.ClassDef)):
            todo.extend(ast.iter_child_nodes(n))


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
        self.fsafe: set[str] = set()  # function names whose every return is code-owned
        self.attr_assigns: dict[str, list] = {}  # attribute name -> [(value expr, scope)]
        self.attr_unsafe: set[str] = set()
        self.attr_number: set[str] = set()
        self.attr_safe: set[str] = set()
        self._envs: dict[int, frozenset[str]] = {}
        self._collect()
        self._solve()

    # ---- collecting ---------------------------------------------------------------------------------------------
    def _collect(self):
        for module, tree in self.trees.items():
            self._walk(module, tree, tree, None)
        names = {d["name"] for d in self.defs}
        classes = {d["cls"] for d in self.defs if d["cls"]}
        for tree in self.trees.values():
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

    def _walk(self, module, node, scope, cls):
        for ch in ast.iter_child_nodes(node):
            self.parent[id(ch)] = node
            self.scope_of[id(ch)] = scope
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
                self._walk(module, ch, ch, ch.name)
            else:
                if isinstance(ch, ast.Call):
                    self.calls.append((module, ch, scope))
                if isinstance(ch, ast.Assign):
                    for t in ch.targets:
                        for a in self._attr_targets(t):
                            self.attr_assigns.setdefault(a, []).append((ch.value, scope))
                elif (
                    isinstance(ch, ast.AugAssign)
                    and isinstance(ch.target, ast.Attribute)
                    or isinstance(ch, ast.AnnAssign)
                    and isinstance(ch.target, ast.Attribute)
                ):
                    self.attr_assigns.setdefault(ch.target.attr, []).append((ch.value, scope))
                elif isinstance(ch, ast.AnnAssign) and isinstance(ch.target, ast.Name):
                    if isinstance(
                        node, ast.ClassDef
                    ):  # a class field: filled from outside unless a number
                        if _is_number_annotation(ch.annotation):
                            self.attr_number.add(ch.target.id)
                        else:
                            self.attr_unsafe.add(ch.target.id)
                elif isinstance(ch, ast.Assign) and isinstance(node, ast.ClassDef):
                    for t in ch.targets:
                        for nm in _targets(t):
                            self.attr_assigns.setdefault(nm.id, []).append((ch.value, scope))
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
        self.fsafe = {d["name"] for d in self.defs}
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
            for name in sorted(self.fsafe):
                if not self._func_ok(name):
                    self.fsafe.discard(name)
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

    def _func_ok(self, name) -> bool:
        for d in self.defs:
            if d["name"] != name:
                continue
            fn = d["node"]
            env = self.env_of(fn)
            rets = [r.value for r in _own(fn) if isinstance(r, ast.Return)]
            if not rets or any(v is None or not self.safe(v, env) for v in rets):
                return False
        return True

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
                if _is_number_annotation(arg.annotation) or (
                    idx is not None and (idx, arg.arg) in self.psafe
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
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    for nm in _targets(t):
                        bindings.setdefault(nm.id, []).append(("assign", n.value))
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                if _is_number_annotation(n.annotation):
                    bindings.setdefault(n.target.id, [])
                elif n.value is not None:
                    bindings.setdefault(n.target.id, []).append(("assign", n.value))
                else:
                    unsafe.add(n.target.id)
            elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
                bindings.setdefault(n.target.id, []).append(("aug", n.value))
            elif isinstance(n, (ast.For, ast.AsyncFor)):
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
                    else:
                        ok = self.safe(val, frozenset(env))
                    if not ok:
                        break
                if not ok:
                    env.discard(name)
                    changed = True
        return frozenset(env)

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
            return e.id in env or bool(UPPER.match(e.id)) or e.id in {"__name__", "__file__"}
        if isinstance(e, ast.Attribute):
            if e.attr in {"__name__", "__qualname__", "__module__"} or UPPER.match(e.attr):
                return True
            return e.attr in self.attr_safe or (
                e.attr in self.attr_number and e.attr not in self.attr_unsafe
            )
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
                return (
                    True  # these cannot make text (`/` is left out: a path `root / name` is text)
                )
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
            if f.id in SAFE_CALLS:
                return True
            if f.id in PASS_CALLS:
                return all(self.safe(a, env) for a in args)
            return f.id in self.fsafe and f.id not in self.escaped
        if isinstance(f, ast.Attribute):
            if f.attr in TEXT_METHODS:
                return self.safe(f.value, env) and all(self.safe(a, env) for a in args)
            return (
                f.attr in self.fsafe
                and isinstance(f.value, ast.Name)
                and f.value.id in {"self", "cls"}
            )
        return False

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
            plain = [
                a
                for a in args
                if not isinstance(a, (ast.BinOp, ast.JoinedStr)) and not self._is_text_call(a)
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
                hit = not safe(node.value, env)
            elif isinstance(node, ast.Call):
                f = node.func
                args = [*node.args, *(k.value for k in node.keywords)]
                fa = f.attr if isinstance(f, ast.Attribute) else None
                fn = f.id if isinstance(f, ast.Name) else None
                if fa in {"format", "format_map", "join"}:
                    hit = not safe(f.value, env) or any(not safe(a, env) for a in args)
                elif fn == "Template" or fa in {"substitute", "safe_substitute"}:
                    hit = any(not safe(a, env) for a in args)
                elif (
                    fa in LOG_METHODS
                    or fa == "add_note"
                    or fn == "print"
                    or fa == "write"
                    and _recv(f.value) in {"stderr", "stdout"}
                    or fa in {"append", "extend", "add", "insert"}
                    and PROBLEM_LIST.search(_recv(f.value))
                ):
                    hit = bare_unsafe(args, env)
                elif fa in {"dumps", "dump"} and _recv(f.value) == "json":
                    hit = any(not safe(a, env) for a in args)
            elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                args = [*node.exc.args, *(k.value for k in node.exc.keywords)]
                hit = bare_unsafe(args, env)
                site = node.exc
            if hit:
                inside.update(id(n) for n in ast.walk(site) if n is not site)
                out.append((site, "message"))
            if (
                isinstance(node, ast.Raise)
                and node.cause is not None
                and not isinstance(node.cause, ast.Constant)
            ):
                out.append((node, "cause"))
        return out

    @staticmethod
    def _is_text_call(a) -> bool:
        return (
            isinstance(a, ast.Call)
            and isinstance(a.func, ast.Attribute)
            and a.func.attr in {"format", "format_map", "join"}
        )


def violations(sources, allowed, exempt):
    """(found, stale): sites not in `allowed` (keyed by (module, site text); a `cause` site by its whole raise
    statement), and allowance entries that match no site."""
    every = set(sources)
    sources = {m: t for m, t in sources.items() if not any(m.startswith(e) for e in exempt)}
    an = Analysis(sources)
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
