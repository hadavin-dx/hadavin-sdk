"""Count banned vendor strings in the v19 files. BANNED is read at run time from the repo test; it is never copied here."""
import ast, os, sys
src = open("/home/user/hadavin-sdk/tests/test_no_reference_material.py", encoding="utf-8").read()
banned = None
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "BANNED" for t in node.targets):
        banned = [str(x).lower() for x in ast.literal_eval(node.value)]
assert banned, "BANNED not found"
root = sys.argv[1]
tot = 0
files = 0
for d, _, fs in os.walk(root):
    for f in fs:
        p = os.path.join(d, f)
        if "/baseline/" in p:   # the v16 baseline output is a carried raw file
            pass
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
