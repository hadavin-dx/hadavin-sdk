import ast, os
src = open("/home/user/hadavin-sdk/tests/test_no_reference_material.py", encoding="utf-8").read()
banned = None
for n in ast.walk(ast.parse(src)):
    if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "BANNED" for t in n.targets): banned = ast.literal_eval(n.value)
print("BANNED strings loaded:", len(banned))
A = "/home/user/hadavin-sdk/handover/core-hardening/audit-r460/"
tot = 0; files = 0
for d, ds, fs in os.walk(A):
    for f in fs:
        p = os.path.join(d, f)
        if os.path.realpath(p) == os.path.realpath(__file__) or f.startswith("raw-banned"): continue
        try: t = open(p, encoding="utf-8", errors="replace").read()
        except Exception: continue
        files += 1
        c = sum(t.count(b) for b in banned)
        if c: tot += c; print("HIT count=%d path=%s" % (c, os.path.relpath(p, A)))
print("files scanned:", files, "total hits:", tot)
# also the two docs alone
for f in ("CORE-PR-HANDOFF-v11.md", "CORE-PR-HANDOFF-v11-other-tracks.md"):
    t = open(A + f, encoding="utf-8").read(); print(f, "hits:", sum(t.count(b) for b in banned))
