import ast, subprocess, sys, json
old, new = sys.argv[1], sys.argv[2]
files = [f for f in subprocess.check_output(["git","diff","--name-only",old,new],text=True).split() if f.startswith("tests/") and f.endswith(".py")]
def funcs(rev, f):
    try: t = subprocess.check_output(["git","show",f"{rev}:{f}"],text=True,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError: return {}
    tree = ast.parse(t); d = {}
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): d[n.name]=ast.unparse(n)
    return d
res = {}
for f in files:
    o, n = funcs(old,f), funcs(new,f)
    ch = sorted(k for k,v in n.items() if k.startswith("test_") and o.get(k)!=v)
    # module-level data changes are not functions: record count
    res[f] = ch
json.dump(res, open(sys.argv[3],"w"), indent=1)
for f,c in res.items(): print(f, len(c))
