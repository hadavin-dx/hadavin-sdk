import ast, sys, builtins, pathlib, importlib
# overlapping except + bare re-raise handlers + unused loop/assign names
EXC = {n: getattr(builtins, n) for n in dir(builtins) if isinstance(getattr(builtins, n), type) and issubclass(getattr(builtins, n), BaseException)}
import urllib.error, http.client, socket, sqlite3, json, subprocess, queue, smtplib, ssl, imaplib
def _res(n):
    if n in EXC and EXC[n] is not None: return EXC[n]
    mod, _, attr = n.rpartition('.')
    if mod:
        try: return getattr(importlib.import_module(mod), attr)
        except Exception: return None
    return None
def names(t):
    if t is None: return [None]
    if isinstance(t, ast.Tuple): return [n for e in t.elts for n in names(e)]
    return [ast.unparse(t)]
MODNS = {}
def cls(n):
    if not n: return BaseException
    r = _res(n)
    if r is None:
        first, _, rest = n.partition('.')
        o = MODNS.get(first)
        for part in (rest.split('.') if rest else []):
            o = getattr(o, part, None)
        r = o if isinstance(o, type) else None
    return r
for p in sys.argv[1:]:
    src = pathlib.Path(p).read_text(); tree = ast.parse(src)
    MODNS.clear()
    mn = p[:-3].replace('/', '.')
    if mn.startswith('src.'): mn = mn[4:]
    try: MODNS.update(vars(importlib.import_module(mn)))
    except Exception as ex: print('#cannot import', mn, type(ex).__name__)
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            seen = []
            for h in node.handlers:
                ns = names(h.type)
                # within one clause: duplicates / subclass pairs
                cs = [(n, cls(n)) for n in ns]
                for i, (n1, c1) in enumerate(cs):
                    for n2, c2 in cs[i+1:]:
                        if n1 == n2 or (c1 and c2 and (issubclass(c1, c2) or issubclass(c2, c1))):
                            print(f"{p}:{h.lineno}: OVERLAP-IN-CLAUSE {n1} / {n2}")
                for n, c in cs:
                    for pn, pc, pl in seen:
                        if n == pn or (c and pc and issubclass(c, pc)):
                            print(f"{p}:{h.lineno}: SHADOWED-CLAUSE {n} already caught by {pn} (line {pl})")
                for n, c in cs: seen.append((n, c, h.lineno))
                body = h.body
                if len(body) == 1 and isinstance(body[0], ast.Raise) and (body[0].exc is None or (h.name and isinstance(body[0].exc, ast.Name) and body[0].exc.id == h.name)):
                    print(f"{p}:{h.lineno}: IMMEDIATE-RERAISE except {ast.unparse(h.type) if h.type else ''}")
                elif body and isinstance(body[0], ast.Raise) and body[0].exc is None:
                    print(f"{p}:{h.lineno}: RERAISE-FIRST-STMT (more follows?) {len(body)}")
    # unused locals per function
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stores = {}; loads = set()
            for n in ast.walk(fn):
                if isinstance(n, ast.Name):
                    if isinstance(n.ctx, ast.Store): stores.setdefault(n.id, n.lineno)
                    else: loads.add(n.id)
            for k, ln in stores.items():
                if k not in loads and not k.startswith("_"):
                    print(f"{p}:{ln}: UNUSED-LOCAL {k} in {fn.name}")
