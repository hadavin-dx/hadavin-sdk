"""Negative controls for verify-c6o.py. Builds changed copies of REPORT-c6o.md (never edits it), runs verify-c6o.py on each and records the exit code
and the raw output. A control copy with no change must exit 0; every changed copy must exit non-zero. Fake key-shaped strings are built from parts here.
Usage: python3 neg_controls_c6o.py   Output: neg/<name>.txt per copy and neg-output.txt (summary). Exit 1 if any changed copy exits 0."""
import re, subprocess, sys, os, tempfile
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
E = D + "evidence-c6o/"
os.makedirs(E + "neg", exist_ok=True)
rep = open(D + "REPORT-c6o.md", encoding="utf-8").read()
PAT = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
L = rep.split("\n")


def rowidx(k):
    return [i for i, l in enumerate(L) if l.startswith("| %d | NOT APPLIED" % k)][0]


def mut_row(text, k, field, fn):
    ls = text.split("\n")
    i = [j for j, l in enumerate(ls) if l.startswith("| %d | NOT APPLIED" % k)][0]
    g = list(PAT.match(ls[i]).groups())
    idx = dict(old=5, new=6, why=7)[field]
    g[idx] = fn(g[idx])
    ls[i] = "| %s | %s | %s | %s | %s | `%s` | `%s` | %s | %s |" % tuple(g)
    return "\n".join(ls)


def prose_lines(text, needle):
    return [i for i, l in enumerate(text.split("\n")) if needle in l and not PAT.match(l)]


def sub_line(text, i, a, b, count=1):
    ls = text.split("\n")
    assert a in ls[i], (i, a)
    ls[i] = ls[i].replace(a, b, count)
    return "\n".join(ls)


def two_labels(text):
    return [i for i, l in enumerate(text.split("\n")) if "VOID-fl45k3b" in l and "VOID-fl45k6c" in l and re.search(r"\b18 (kept )?(crash )?runs?\b|each of 18|all 18", l, re.I) and not PAT.match(l)]


AK = "AK" + "IA" + "QWERTY123456"
SK = "s" + "k-" + "abcdefghij012345"
GH = "gh" + "p_" + "abcdefghij012345"
M = {}
M["V0-control-unchanged"] = rep
M["V1a-oldquote-row1"] = mut_row(rep, 1, "old", lambda s: s.replace("Scene 4 caption", "Scene 4 captionX", 1))
M["V1b-oldquote-row40"] = mut_row(rep, 40, "old", lambda s: s[:12] + "X" + s[12:])
s4 = rep.index("## 4. Plain-word glossary")
M["V2a-61.1-glossary-only"] = rep[:s4] + rep[s4:].replace("60.1 to 61.9", "60.1 to 61.1", 1) if "60.1 to 61.9" in rep[s4:] else None
M["V2b-61.1-everywhere"] = rep.replace("60.1 to 61.9", "60.1 to 61.1")
M["V2c-61.1-in-NEW-text-row39"] = mut_row(rep, 39, "new", lambda s: s.replace("60.1 to 61.9", "60.1 to 61.1"))
pl = prose_lines(rep, "60.1 to 61.9")[0]
M["V2d-61.1-new-text-and-prose"] = sub_line(mut_row(rep, 39, "new", lambda s: s.replace("60.1 to 61.9", "60.1 to 61.1")), pl, "60.1 to 61.9", "60.1 to 61.1")
tl = two_labels(rep)
M["V3a-VOID-label-removed-prose-1"] = sub_line(rep, tl[0], "VOID-fl45k6c", "VOID-x", 99)
M["V3b-VOID-label-removed-prose-2"] = sub_line(rep, tl[-1], "VOID-fl45k3b", "VOID-x", 99)
M["V3c-VOID-label-removed-in-NEW-text-row39"] = mut_row(rep, 39, "new", lambda s: s.replace("VOID-fl45k6c", "VOID-x"))
i59 = prose_lines(rep, "23:59 IST")[0]
M["V4a-one-IST-time"] = sub_line(rep, i59, "23:59 IST", "23:58 IST", 1)
M["V4b-all-23:59-IST"] = rep.replace("23:59 IST", "23:58 IST")
M["V4c-IST-word-broken-in-NEW-text-row6"] = mut_row(rep, 6, "new", lambda s: s.replace("IST", "1ST", 1))
for nm, key in (("akia", AK), ("sk", SK), ("ghp", GH)):
    M["V5-fakekey-%s-in-row1-NEWtext" % nm] = mut_row(rep, 1, "new", lambda s, k=key: s + " " + k)
    M["V5-fakekey-%s-in-row1-reason" % nm] = mut_row(rep, 1, "why", lambda s, k=key: s + " " + k)
ls = rep.split("\n")
del ls[rowidx(50)]
M["V6-one-row-deleted"] = "\n".join(ls)
M["V7-split-wrong-11-runs-done"] = rep.replace("10 runs done", "11 runs done", 1)
M["V8-IST-arithmetic-wrong"] = rep.replace("18:19 UTC = 23:49 IST", "18:19 UTC = 23:19 IST", 1)
M["V9-NOT-FILMABLE-sentence-back-in-row13"] = mut_row(rep, 13, "new", lambda s: s + " We say this only when the second send comes within 45 seconds of the first send.")
M["V10-index-not-seen-accepted-back-in-row8"] = mut_row(rep, 8, "new", lambda s: s + " index not seen, accepted")
out = []
bad = 0
for name, text in M.items():
    if text is None:
        out.append("%-48s SKIPPED (mutation target absent)" % name)
        bad += 1
        continue
    p = os.path.join(tempfile.mkdtemp(), "REPORT-copy.md")
    open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run([sys.executable, E + "verify-c6o.py", p], capture_output=True, text=True)
    open(E + "neg/" + name + ".txt", "w").write(r.stdout[-6000:] + r.stderr[-1500:] + "\nEXIT CODE %d\n" % r.returncode)
    failed = [l for l in r.stdout.split("\n") if l.startswith("FAIL")]
    want_zero = name.startswith("V0")
    ok = (r.returncode == 0) if want_zero else (r.returncode != 0)
    if not ok:
        bad += 1
    out.append("%-48s exit %d  %s  first failed check: %s" % (name, r.returncode, "OK" if ok else "WRONG", (failed[0][:110] if failed else "none")))
out.append("SUMMARY: %d copies, %d wrong" % (len(M), bad))
open(E + "neg-output.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
sys.exit(1 if bad else 0)
