"""Hot-file table check (v13 independent). Reads the merge table of the main document; for every file named in
column 5, lists which PR rows name it, whether each mention carries an 'also' naming the other PRs, and whether the file exists
in the tree (new files marked '(new)' excepted). usage: python -I hotfiles_v13.py <repo> <doc>"""
import re, sys, os, collections
repo, doc = sys.argv[1], sys.argv[2]
rows = []
for l in open(doc, encoding="utf-8"):
    m = re.match(r"\| (\d+) \| ([A-Za-z0-9-]+) \| ([^|]*)\| ([^|]*)\| (.*)\|\s*$", l)
    if m and m.group(2) in ("S-1","S-2a","S-2b","DB-1","DB-2","PR-2","R","K1","A1","G-W","G","H-0","H-1","H-2"):
        rows.append((int(m.group(1)), m.group(2), m.group(5)))
print("rows:", len(rows), [r[1] for r in rows])
ment = collections.defaultdict(list)
for n, pr, cell in rows:
    for m in re.finditer(r"`([\w./-]+\.(?:py|sql|yml|properties|md)|[\w./-]*CODEOWNERS|[\w./-]+/)`([^`]*?)(?=`[\w./-]+\.(?:py|sql)`|,\s*`|$)", cell):
        f = m.group(1); tail = m.group(2)
        also = re.search(r"also ([A-Za-z0-9, -]+?)[;)]", tail)
        ment[f].append((pr, also.group(1).replace(" ", "") if also else None, "(new)" in tail))
def exists(f):
    for pre in ("src/hadavin_sdk/", "src/hadavin_sdk/store/", "", "src/hadavin_sdk/audit/"):
        if os.path.exists(os.path.join(repo, pre + f)): return True
    return False
bad = 0
for f, ms in sorted(ment.items()):
    prs = [m[0] for m in ms]
    ex = exists(f)
    flags = []
    if not ex and not any(m[2] for m in ms): flags.append("NOT-IN-TREE-and-not-marked-new")
    if len(set(prs)) > 1:
        for pr, also, _ in ms:
            others = set(prs) - {pr}
            said = set((also or "").split(","))
            if not others <= said: flags.append("%s lacks also=%s (says %s)" % (pr, sorted(others - said), also))
    if flags: bad += 1
    print("%-34s rows=%s exists=%s %s" % (f, ",".join(prs), ex, "; ".join(flags)))
print("files with a flag:", bad)
