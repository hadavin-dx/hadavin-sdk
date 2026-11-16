"""Count banned vendor strings in the v20 files. BANNED is read at run time from the repo test; it is never copied here."""
import ast, os, sys
src = open("/home/user/hadavin-sdk/tests/test_no_reference_material.py", encoding="utf-8").read()
banned = None
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "BANNED" for t in node.targets):
        banned = [str(x).lower() for x in ast.literal_eval(node.value)]
assert banned, "BANNED not found"
roots = sys.argv[1:]
tot = 0
files = 0
paths = []
for r in roots:
    if os.path.isfile(r):
        paths.append(r)
    else:
        for d, _, fs in os.walk(r):
            paths.extend(os.path.join(d, f) for f in fs)
if True:
    for p in paths:
        try:
            t = open(p, encoding="utf-8").read().lower()
        except (UnicodeDecodeError, OSError):
            print("UNREADABLE as UTF-8:", p); tot += 1; continue
        files += 1
        n = sum(t.count(b) for b in banned)
        if n:
            print("HIT", p, n); tot += n
print(f"files scanned {files}; strings checked {len(banned)}; hits {tot}")
sys.exit(1 if tot else 0)
