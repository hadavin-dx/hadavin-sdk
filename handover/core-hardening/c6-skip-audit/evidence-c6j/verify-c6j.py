"""Independent check: reads REPORT-c6j.md only (not build_c6j.py), compares every old text to its file line,
checks every cited short-name:line exists, then applies all edits to COPIES in a temp dir and greps for stale phrases."""
import re, sys, os, shutil, tempfile
R = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/REPORT-c6j.md"
txt = open(R, encoding="utf-8").read().split("\n")
# short names table (section 8)
paths = {}
for l in txt:
    m = re.match(r"^\| ([A-Z0-9]+) \| (/[^|]+) \|$", l)
    if m: paths[m.group(1)] = m.group(2).strip()
def rd(p): return open(p, encoding="utf-8", errors="replace").read().split("\n")
bad = 0; n = 0; edits = []
for l in txt:
    m = re.match(r"^\| (\d+) \| (/[^|]+?) \| (\d+) \| `(.*?)` \| `(.*?)` \| (.*) \| (NOT APPLIED) \|$", l)
    if not m: continue
    num, f, ln, old, new, why, st = m.groups(); ln = int(ln); old = old.replace("<br>", "\n"); new = new.replace("<br>", "\n")
    n += 1; fl = rd(f)
    # old text may span several lines only if it has newline; all ours are single-line
    ok = ln <= len(fl) and fl[ln-1].count(old) == 1
    # whole-file uniqueness is not required, only line uniqueness
    if not ok: bad += 1
    print("MATCH" if ok else "MISMATCH", num, f.split("/")[-1], ln, repr(old[:50]))
    edits.append((int(num), f, ln, old, new))
print("edit rows", n, "mismatch", bad)
cites = set(re.findall(r"\b(RS|PG|NS|MF|JF|JH|JR|JS|ONE|DEC|PLAN|FND|RES|H6|RD|RN|RDES|R6I|ORD|QST|EV1|EV):(\d+)\b", "\n".join(txt)))
cb = 0
for k, v in sorted(cites):
    v = int(v); fl = rd(paths[k]); ok = 1 <= v <= len(fl) and fl[v-1].strip() != ""
    if not ok: cb += 1; print("BAD CITE", k, v)
print("cites", len(cites), "bad", cb)
# simulate apply on copies
tmp = tempfile.mkdtemp(prefix="c6j-sim-", dir="/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad")
cp = {}
for num, f, ln, old, new in edits:
    if f not in cp:
        d = os.path.join(tmp, str(len(cp)) + "-" + os.path.basename(f)); shutil.copy(f, d); cp[f] = d
    L = open(cp[f], encoding="utf-8").read().split("\n")
    # lines shift when an edit adds lines, so locate by text on the original line number offset
    idx = [i for i, x in enumerate(L) if old in x]
    assert len(idx) == 1, (num, len(idx))
    L[idx[0]] = L[idx[0]].replace(old, new, 1)
    open(cp[f], "w", encoding="utf-8").write("\n".join(L))
print("applied all", len(edits), "edits to copies in", tmp)
def after(name): return open(cp[[k for k in cp if k.endswith(name)][0]], encoding="utf-8").read()
rs, pg = after("VIDEO-RUNSHEET.md"), after("PAGE-STATEMENTS-V4.md")
stale = [("lease plus 25 to 30 s (an estimate", rs), ("killed after the mail left", rs), ("killed after the mail left", pg), ("60.1 to 61.9", rs), ("From n8n up: 52.9", rs), ("Raw not seen by me", rs), ("scenes 1 to 5", rs), ("80 kills", rs), ("up to 13 min late", rs), ("about a minute after the crash", pg)]
for s, t in stale:
    c = t.count(s); print("STALE-CHECK", repr(s), "remaining", c)
