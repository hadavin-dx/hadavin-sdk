"""Own AST count (v13 independent): every call named `build` (any receiver) in tests/ and demos/ that passes an `llm`
keyword or a 2nd/3rd positional that is named like an llm; prints file:line, the llm argument text, and, when the
argument is a bare name, the assignment(s) of that name in the same function. Reads files only. usage: python -I count_build_llm_v13.py <repo>"""
import ast, os, sys
repo = sys.argv[1]
hits = []
for top in ("tests", "demos"):
    for d, ds, fs in os.walk(os.path.join(repo, top)):
        ds[:] = [x for x in ds if x not in ("__pycache__", ".venv")]
        for f in fs:
            if not f.endswith(".py"): continue
            p = os.path.join(d, f)
            try: tree = ast.parse(open(p, encoding="utf-8").read())
            except Exception: continue
            parents = {}
            for n in ast.walk(tree):
                for c in ast.iter_child_nodes(n): parents[c] = n
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    fn = n.func
                    name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                    if name != "build": continue
                    llmarg = None
                    for k in n.keywords:
                        if k.arg == "llm": llmarg = k.value
                    if llmarg is None: continue
                    fnode = n
                    while fnode in parents and not isinstance(fnode, (ast.FunctionDef, ast.AsyncFunctionDef)): fnode = parents[fnode]
                    assigns = []
                    if isinstance(llmarg, ast.Name) and isinstance(fnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for a in ast.walk(fnode):
                            if isinstance(a, ast.Assign) and any(isinstance(t, ast.Name) and t.id == llmarg.id for t in a.targets):
                                assigns.append("L%d %s" % (a.lineno, ast.unparse(a.value)[:70]))
                        if llmarg.id in [x.arg for x in fnode.args.args]: assigns.append("(function parameter of %s)" % fnode.name)
                    hits.append((os.path.relpath(p, repo), n.lineno, ast.unparse(llmarg)[:70], assigns, getattr(fnode, "name", "?")))
for h in sorted(hits): print("%s:%d in %s | llm=%s | %s" % (h[0], h[1], h[4], h[2], "; ".join(h[3]) or "-"))
print("TOTAL calls of build(...) with an llm keyword:", len(hits))
