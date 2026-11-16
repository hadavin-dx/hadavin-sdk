import re, sys
ci = open("/home/user/hadavin-sdk/.github/workflows/ci.yml", encoding="utf-8").read().split("\n")
g4 = open("../evidence-handoff-v11/gate4.sh", encoding="utf-8").read().split("\n")
want = {}
for n in (79, 81, 88, 94, 119):
    l = ci[n-1]; m = re.search(r"run:\s*(.*)$", l)
    want[n] = m.group(1).strip() if m else None
    print("ci.yml:%d -> %r" % (n, l.strip()))
# gate4 commands: lines that start with a tool name and redirect
cmds = []
for l in g4:
    m = re.match(r"^(ruff|pytest|bandit)\b(.*?)\s*>\s*\"\$p-(\w+)\.txt\"", l)
    if m: cmds.append((m.group(1) + m.group(2)).strip())
print("gate4 commands:"); [print("  ", c) for c in cmds]
ok = True
for (n, w), c in zip(want.items(), cmds):
    same = (w == c); ok &= same
    print("line %d: ci=%r gate4=%r %s" % (n, w, c, "SAME" if same else "DIFF"))
print("count ci=%d gate4=%d" % (len(want), len(cmds)))
# is env of ci steps replicated? ci lines 86-87,92-93 set HADAVIN_TEST_PG_DSN / VAULT_ADDR
print("gate4 mentions HADAVIN_TEST_PG_DSN:", any("HADAVIN_TEST_PG_DSN" in l for l in g4), "VAULT_ADDR:", any("VAULT_ADDR" in l for l in g4))
print("ALL SAME" if ok and len(cmds) == len(want) else "DIFFERENCES FOUND")
