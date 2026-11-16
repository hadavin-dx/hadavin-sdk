"""Count (never print) banned strings from tests/test_no_reference_material.py (BANNED tuple read with ast) in the given files.
usage: python -I banned_count_v9.py <repo_root> <file-or-dir>..."""
import ast, os, sys
root = sys.argv[1]
tree = ast.parse(open(os.path.join(root, "tests/test_no_reference_material.py"), encoding="utf-8").read())
banned = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "BANNED" for t in node.targets):
        banned = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
print("banned strings loaded:", len(banned))
total = 0
for a in sys.argv[2:]:
    paths = [os.path.join(d, f) for d, _, fs in os.walk(a) for f in fs] if os.path.isdir(a) else [a]
    for p in sorted(paths):
        t = open(p, encoding="utf-8", errors="replace").read().lower()
        c = sum(t.count(b.lower()) for b in banned); total += c
        print("%s: %d" % (os.path.relpath(p, root), c))
print("TOTAL banned-string matches:", total)
sys.exit(1 if total else 0)
