"""Reads BANNED from tests/test_no_reference_material.py at run time (ast), prints COUNTS ONLY, never the strings."""
import ast, sys, os, re
src = open("/home/user/hadavin-sdk/tests/test_no_reference_material.py", encoding="utf-8").read()
tree = ast.parse(src)
banned = None
for n in ast.walk(tree):
    if isinstance(n, (ast.Assign, ast.AnnAssign)):
        tg = n.targets[0] if isinstance(n, ast.Assign) else n.target
        if isinstance(tg, ast.Name) and tg.id == "BANNED":
            banned = ast.literal_eval(n.value)
if banned is None:
    print("BANNED not found as a literal"); sys.exit(2)
items = list(banned.keys()) if isinstance(banned, dict) else list(banned)
items = [str(x) for x in items]
print("BANNED entries read: %d (type %s)" % (len(items), type(banned).__name__))
tot = 0
for p in sys.argv[1:]:
    paths = []
    if os.path.isdir(p):
        for d, _, fs in os.walk(p):
            paths += [os.path.join(d, f) for f in fs if f != "banned_scan.py"]
    else:
        paths = [p]
    n = 0; files = 0
    for q in paths:
        t = open(q, encoding="utf-8", errors="replace").read().lower()
        c = sum(t.count(b.lower()) for b in items)
        if c: files += 1
        n += c
    print("%s: files scanned %d, total hits %d, files with hits %d" % (os.path.basename(p.rstrip("/")), len(paths), n, files))
    tot += n
sys.exit(1 if tot else 0)
