"""Citation extraction for hand-off v9. usage: python -I cite_check_v9.py <repo_root> <doc> [<doc> ...]
For every cite of the form path.ext:LINE, :LINE-LINE, or a comma list of ':N' after a path, resolves the file by
path suffix under src/hadavin_sdk, tests, demos, .github, handover and prints: doc line, cite, the source line text
(first 90 chars), and ANCHOR ok/CHECK. ANCHOR = some identifier quoted in backticks earlier on the same doc line
(4+ chars, no ':') occurs in the cited range +-2 lines. CHECK means a human must look; it is not an error by itself.
Unresolved files and out-of-range lines are printed as MISSING / RANGE. Changes nothing."""
import os, re, sys
root = sys.argv[1]
files = {}
for top in ("src/hadavin_sdk", "tests", "demos", ".github", "handover", "src"):
    for d, ds, fs in os.walk(os.path.join(root, top)):
        ds[:] = [x for x in ds if x not in ("__pycache__", ".git")]
        for f in fs:
            p = os.path.join(d, f)
            files[os.path.relpath(p, root)] = p
def find(name):
    cands = [r for r in files if r == name or r.endswith("/" + name)]
    pref = [r for r in cands if r.startswith("src/hadavin_sdk/") or r.startswith("tests/") or r.startswith("demos/") or r.startswith(".github/")]
    return (pref or cands)[:3]
CITE = re.compile(r"([\w./-]*[\w-]+\.(?:py|sql|yml|md))((?::\d+(?:-\d+)?(?:\s*,\s*(?=:\d))?)+)")
cache = {}
def lines_of(p):
    if p not in cache:
        cache[p] = open(p, encoding="utf-8", errors="replace").read().split("\n")
    return cache[p]
tot = bad = chk = 0
for doc in sys.argv[2:]:
    print("=== " + doc)
    for n, line in enumerate(open(doc, encoding="utf-8").read().split("\n"), 1):
        for m in CITE.finditer(line):
            name, spans = m.group(1), m.group(2)
            if name.startswith("handover/") or "CORE-PR" in name or name.startswith("v9") :
                continue
            idents = [i for i in re.findall(r"`([^`]+)`", line[: m.start()]) if ":" not in i and len(i) >= 4]
            words = []
            for i in idents[-6:]:
                words += [w for w in re.findall(r"[A-Za-z_][A-Za-z_0-9]{3,}", i)]
            found = find(name)
            for sp in re.findall(r":(\d+)(?:-(\d+))?", spans):
                a = int(sp[0]); b = int(sp[1] or sp[0]); tot += 1
                if not found:
                    print("L%d MISSING file %s:%d" % (n, name, a)); bad += 1; continue
                src = lines_of(files[found[0]])
                if b > len(src) or a < 1:
                    print("L%d RANGE %s:%d-%d (file has %d lines)" % (n, found[0], a, b, len(src))); bad += 1; continue
                win = "\n".join(src[max(0, a - 3): b + 2])
                ok = (not words) or any(w in win for w in words)
                if not ok: chk += 1
                print("L%d %s:%d-%d | %s | %s%s" % (n, found[0], a, b, src[a - 1].strip()[:90], "ANCHOR ok" if ok else "CHECK words=" + ",".join(words[:4]), "" if len(found) == 1 else " (ambiguous file)"))
print("TOTAL cites=%d missing_or_range=%d anchor_check=%d" % (tot, bad, chk))
