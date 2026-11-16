"""Structural gate for scan loops (DF5 A12): every place that reaches the model must carry the scan stop rule (``extract.TransportStreak``).

``violations(source, module)`` reads one module's source and returns the problems found, as short strings:
* a call to ``process`` / ``extract_parsed`` (from ``pipeline`` / ``extract``) outside the defining module must pass ``streak=`` and either forward its own
  ``streak`` parameter or sit in a function that reads ``.stop`` or ``.wall``;
* a call to ``GuardedModel`` / ``build_guarded`` outside ``model`` must sit in a function that handles a streak (a ``streak`` parameter or the name
  ``TransportStreak``) and reads ``.stop`` or ``.wall``;
* every other way of reaching those names is a violation: a renaming import, an alias assignment, passing the function on (``functools.partial``, a callback
  argument), ``getattr`` with a constant or a folded string.
No file is exempt: the caller scans the whole source tree recursively."""

from __future__ import annotations

import ast

TARGETS = {"process": "pipeline", "extract_parsed": "extract", "GuardedModel": "model", "build_guarded": "model"}
FACTORIES = {"GuardedModel", "build_guarded"}
MODULES = set(TARGETS.values())


def _fold(n: ast.AST) -> str | None:
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        a, b = _fold(n.left), _fold(n.right)
        return a + b if a is not None and b is not None else None
    if isinstance(n, ast.JoinedStr):
        parts = [v.value for v in n.values if isinstance(v, ast.Constant) and isinstance(v.value, str)]
        return "".join(parts) if len(parts) == len(n.values) else None
    return None


def _enclosing(parents: dict, node: ast.AST):
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            return node
    return None


def violations(source: str, module: str) -> list[str]:
    tree = ast.parse(source)
    parents = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    out: list[str] = []
    direct: set[str] = set()  # target names imported without renaming
    modnames: dict[str, str] = {}  # local name -> module stem (pipeline / extract / model)
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if a.name in TARGETS and TARGETS[a.name] != module:
                    if a.asname and a.asname != a.name:
                        out.append(f"line {n.lineno}: {a.name} imported under another name")
                    else:
                        direct.add(a.name)
                if a.name in MODULES:
                    modnames[a.asname or a.name] = a.name
        elif isinstance(n, ast.Import):
            for a in n.names:
                stem = a.name.rsplit(".", 1)[-1]
                if stem in MODULES:
                    modnames[a.asname or stem] = stem

    def target_of(func: ast.AST) -> str | None:
        if isinstance(func, ast.Name) and func.id in direct:
            return func.id
        if isinstance(func, ast.Attribute) and func.attr in TARGETS and TARGETS[func.attr] != module:
            base = func.value
            if isinstance(base, ast.Name) and modnames.get(base.id) == TARGETS[func.attr]:
                return func.attr
            if isinstance(base, ast.Attribute) and base.attr == TARGETS[func.attr]:
                return func.attr
        return None

    call_funcs = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name) and n.func.id == "getattr" and len(n.args) >= 2:
                s = _fold(n.args[1])
                if s in TARGETS and TARGETS[s] != module:
                    out.append(f"line {n.lineno}: getattr reaches {s}")
            t = target_of(n.func)
            if t is None:
                continue
            fn = _enclosing(parents, n)
            names = {x.attr for x in ast.walk(fn) if isinstance(x, ast.Attribute)} if fn else set()
            ids = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name)} if fn else set()
            params = {a.arg for a in (fn.args.args + fn.args.kwonlyargs)} if fn else set()
            reads_stop = bool(names & {"stop", "wall"})
            if t in FACTORIES:
                if not (("streak" in params or "TransportStreak" in names | ids) and reads_stop):
                    out.append(f"line {n.lineno}: {t} called where no streak is created or read")
                continue
            kw = next((k for k in n.keywords if k.arg == "streak"), None)
            if kw is None:
                out.append(f"line {n.lineno}: {t} called without streak=")  # mut:gate_no_kw
            elif not (isinstance(kw.value, ast.Name) and kw.value.id == "streak" and "streak" in params) and not reads_stop:
                out.append(f"line {n.lineno}: {t} called but the caller never reads .stop or .wall")
        elif isinstance(n, ast.Name) and n.id in direct and id(n) not in call_funcs and not isinstance(n.ctx, ast.Store):
            out.append(f"line {n.lineno}: {n.id} used without being called")
        elif isinstance(n, ast.Attribute) and n.attr in TARGETS and TARGETS[n.attr] != module and id(n) not in call_funcs:
            if target_of(n) is not None:
                out.append(f"line {n.lineno}: {n.attr} used without being called")
    return out
