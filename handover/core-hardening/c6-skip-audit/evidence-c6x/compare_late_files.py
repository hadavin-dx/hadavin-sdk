"""c6x: compares the files written after the freeze (owner sheet v35 A and B, release note v19) with their predecessors (v34 A and B, v18) by script.
Words changed (inserted or deleted, after the version numbers are made equal) are listed, and the script prints whether any changed word is one of the report's topics.
Usage: python3 -B -I compare_late_files.py [steps-edits folder]   Reads only; writes nothing. Exit 0 always (it states a result, it is not a gate)."""
import difflib, re, sys, os
H = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
S = sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, "core-hardening", "steps-edits")
TOPICS = ("lease", "g12", "closing card", "card line", "45-second", "45 s", "database", "n8n", "hubspot", "read-only", "alert", "processed once")
pairs = [("OWNER-SHEET-v34-A.md", "OWNER-SHEET-v35-A.md"), ("OWNER-SHEET-v34-B.md", "OWNER-SHEET-v35-B.md"), ("LEAD-RELEASE-NOTE-v18.md", "LEAD-RELEASE-NOTE-v19.md")]
for a, b in pairs:
    ta = open(os.path.join(S, a), encoding="utf-8").read()
    tb = open(os.path.join(S, b), encoding="utf-8").read()
    va, vb = re.search(r"v(\d+)", a).group(1), re.search(r"v(\d+)", b).group(1)
    ta2 = re.sub(r"v%s\b" % va, "v%s" % vb, ta)
    print("== %s -> %s: %s after the version number is made equal" % (a, b, "IDENTICAL" if ta2 == tb else "DIFFERENT"))
    if ta2 == tb:
        continue
    wa, wb = ta2.split(), tb.split()
    sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    dels, ins = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("replace", "delete"): dels.append(" ".join(wa[i1:i2]))
        if op in ("replace", "insert"): ins.append(" ".join(wb[j1:j2]))
    print("   changed passages: %d deleted/replaced, %d inserted/replaced; words deleted %d, inserted %d" % (len(dels), len(ins), sum(len(x.split()) for x in dels), sum(len(x.split()) for x in ins)))
    hit = sorted({t for t in TOPICS for x in dels + ins if t in x.lower()})
    print("   report topics found inside the changed words: %s" % (hit if hit else "none"))
    for x in (dels + ins)[:60]:
        if any(t in x.lower() for t in TOPICS):
            print("   TOPIC PASSAGE: " + x[:220])
# the four lines of release note v14 that the report cites (lines 8, 33, 149, 150): equal in v18 and in v19?
ra = lambda n: open(os.path.join(S, n), encoding="utf-8").read().split("\n")
v14, v18, v19 = ra("LEAD-RELEASE-NOTE-v14.md"), ra("LEAD-RELEASE-NOTE-v18.md"), ra("LEAD-RELEASE-NOTE-v19.md")
for n in (8, 33, 149, 150):
    print("RELEASE NOTE LINE %d: v14 equals v18: %s; v18 equals v19: %s; v14 equals v19: %s" % (n, v14[n - 1] == v18[n - 1], v18[n - 1] == v19[n - 1], v14[n - 1] == v19[n - 1]))
