"""Counts only: how many banned-string occurrences (BANNED read from tests/test_no_reference_material.py at run time) in each v16 file."""
import ast, sys
from pathlib import Path
repo = Path(sys.argv[1]); base = Path(sys.argv[2])
tree = ast.parse((repo / "tests/test_no_reference_material.py").read_text())
banned = None
for n in ast.walk(tree):
    if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "BANNED" for t in n.targets):
        banned = ast.literal_eval(n.value)
print("INFO number of banned strings:", len(banned))
files = sorted({p for p in base.rglob("*") if p.is_file() and ("v16" in p.name or "v16" in p.parent.name or "v16" in str(p.relative_to(base).parts[0])) and "__pycache__" not in p.parts})
tot = tot_ci = 0; nonutf = 0
for p in files:
    try:
        t = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        nonutf += 1; print("NONUTF8", p.relative_to(base)); continue
    c = sum(t.count(b) for b in banned); ci = sum(t.lower().count(b.lower()) for b in banned)
    tot += c; tot_ci += ci
    if c or ci:
        print(f"HITS {p.relative_to(base)}: case-sensitive {c}, case-insensitive {ci}")
print(f"INFO files scanned {len(files)} (non-UTF8 {nonutf}); total case-sensitive {tot}; case-insensitive {tot_ci}")
