"""Counts only. Reads BANNED from tests/test_no_reference_material.py at run time (ast), scans the v15 files (case-sensitive like the repo test, and case-insensitive as an extra). Never prints a banned string."""
import ast, os, sys
repo = "/home/user/hadavin-sdk"; adir = repo + "/handover/core-hardening/audit-r460"
tree = ast.parse(open(repo + "/tests/test_no_reference_material.py", encoding="utf-8").read())
banned = None
for n in ast.walk(tree):
    if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "BANNED" for t in n.targets): banned = list(ast.literal_eval(n.value))
print("banned strings loaded:", len(banned))
files = [adir + "/CORE-PR-HANDOFF-v15.md", adir + "/CORE-PR-HANDOFF-v15-other-tracks.md", adir + "/checkpoint-handoff-v15.md"]
for d, ds, fs in os.walk(adir + "/evidence-handoff-v15"):
    files += [os.path.join(d, f) for f in fs]
tot = tot_i = 0; nfiles = 0; hit_files = 0
for p in sorted(files):
    t = open(p, encoding="utf-8", errors="replace").read(); nfiles += 1
    c = sum(t.count(b) for b in banned); ci = sum(t.lower().count(b.lower()) for b in banned)
    tot += c; tot_i += ci; hit_files += bool(ci)
print("files scanned:", nfiles, "| files with a case-insensitive hit:", hit_files)
print("TOTAL case-sensitive matches:", tot, "| TOTAL case-insensitive matches:", tot_i)
