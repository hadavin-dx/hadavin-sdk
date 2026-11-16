"""Negative controls for verify-c6p.py. Builds changed copies of REPORT-c6p.md (never edits it), runs verify-c6p.py on each and records the exit code
and the raw output. A control copy with no change must exit 0; every changed copy must exit non-zero. Fake key-shaped strings are built from parts here.
Usage: python3 neg_controls_c6p.py   Output: neg/<name>.txt per copy and neg-output.txt (summary). Exit 1 if any changed copy exits 0."""
import re, subprocess, sys, os, tempfile
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
E = D + "evidence-c6p/"
os.makedirs(E + "neg", exist_ok=True)
rep = open(D + "REPORT-c6p.md", encoding="utf-8").read()
PAT = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
L = rep.split("\n")


def rowidx(k):
    return [i for i, l in enumerate(L) if l.startswith("| %d | NOT APPLIED" % k)][0]


def mut_row(text, k, field, fn):
    ls = text.split("\n")
    i = [j for j, l in enumerate(ls) if l.startswith("| %d | NOT APPLIED" % k)][0]
    g = list(PAT.match(ls[i]).groups())
    idx = dict(st=1, view=4, old=5, new=6, why=7)[field]
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
box_end = rep.index("WORDS (more")
M["V0-control-unchanged"] = rep
M["V1a-oldquote-row1"] = mut_row(rep, 1, "old", lambda s: s.replace("Scene 4 caption", "Scene 4 captionX", 1))
M["V1b-oldquote-row40"] = mut_row(rep, 40, "old", lambda s: s[:12] + "X" + s[12:])
M["V2b-61.1-everywhere"] = rep.replace("60.1 to 61.9", "60.1 to 61.1")
M["V2c-61.1-in-NEW-text-row39"] = mut_row(rep, 39, "new", lambda s: s.replace("60.1 to 61.9", "60.1 to 61.1"))
tl = two_labels(rep)
M["V3a-VOID-label-removed-prose"] = sub_line(rep, tl[0], "VOID-fl45k6c", "VOID-x", 99)
M["V3c-VOID-label-removed-in-NEW-text-row39"] = mut_row(rep, 39, "new", lambda s: s.replace("VOID-fl45k6c", "VOID-x"))
M["V4a-IST-arith-wrong"] = rep.replace("18:19 UTC = 23:49 IST", "18:19 UTC = 23:19 IST", 1)
M["V4c-IST-word-broken-in-NEW-text-row6"] = mut_row(rep, 6, "new", lambda s: s.replace("IST", "1ST", 1))
for nm, key in (("akia", AK), ("sk", SK), ("ghp", GH)):
    M["V5-fakekey-%s-in-row1-NEWtext" % nm] = mut_row(rep, 1, "new", lambda s, k=key: s + " " + k)
ls = rep.split("\n")
del ls[rowidx(50)]
M["V6-one-row-deleted"] = "\n".join(ls)
M["V7-split-wrong-11-runs-done"] = rep.replace("10 runs done", "11 runs done", 1)
M["V10-index-not-seen-accepted-back-in-row8"] = mut_row(rep, 8, "new", lambda s: s + " index not seen, accepted")
# c6p classes
M["N1-card-word-count-wrong-in-row13"] = mut_row(rep, 13, "new", lambda s: s.replace("processed once.", "processed once now.", 1))
M["N2-row11-says-103-words"] = mut_row(rep, 11, "new", lambda s: re.sub(r"\b115 words", "103 words", s, count=1))
M["N3-row-N-reference-in-new-text"] = mut_row(rep, 21, "new", lambda s: s + " (row 13 explains)")
M["N4-accepted-exit-in-row8"] = mut_row(rep, 8, "new", lambda s: s + " The lease question is accepted.")
i5 = [i for i, l in enumerate(rep.split("\n")) if l.startswith("| 87 | page statements, line")][0]
ls = rep.split("\n"); del ls[i5]
M["N5-5a-page-row-missing"] = "\n".join(ls)
M["N6-newest-sheet-claim-stale-v27"] = rep.replace("v28", "v27")
M["N7-row90-broken-sentence-and-third-place"] = mut_row(rep, 90, "new", lambda s: s.rstrip() + " owned by a third place")
M["N8-row6-claims-deletion-erases"] = mut_row(rep, 6, "new", lambda s: s.replace("NOT verified that deleting a run erases it", "Deleting a run erases it", 1))
M["N9-row8-latest-start-missing"] = mut_row(rep, 8, "new", lambda s: s.replace("18:04 UTC = 23:34 IST", "18:29 UTC = 23:59 IST", 1))
M["N10-144.3-unlabelled-row47"] = mut_row(rep, 47, "new", lambda s: s.replace("144.3 s after n8n came back up", "144.3 s", 1))
M["N11-lease-none-meaning-missing"] = rep.replace("NONE = no lease sentence anywhere", "OTHER = no lease sentence anywhere", 1)
M["N12-label-GATE-used-before-defined-in-box"] = rep.replace("You answer with ONE line", "You answer with ONE GATE line", 1)
M["N13-box-too-long"] = rep[:box_end] + ("filler words here " * 1100) + "\n" + rep[box_end:]
M["N14-L-SCENES-question-back"] = rep.replace("| L-CUT | studio lead |", "| L-SCENES | studio lead | x | 1 | No | y | 2 |\n| L-CUT | studio lead |", 1)
M["N15-row13-NOT-FILMABLE-back"] = mut_row(rep, 13, "st", lambda s: "NOT APPLIED; NOT FILMABLE until L-LEASE is answered")
M["N16-stale-103-words-line"] = rep + "\nThe spoken card holds 103 words.\n"
M["N17-box-names-an-n8n-setting"] = rep[:box_end] + " saveDataSuccessExecution " + rep[box_end:]
M["N18-lease-sentence-missing-in-row13"] = mut_row(rep, 13, "new", lambda s: s.replace("within 45 seconds of the first send", "soon after", 1))
M["N19-death-of-5a-counts-wrong-3b"] = rep.replace("| L-SAVE | 23,", "| L-SAVE | 24,", 1)
rep_c6o = open(D + "REPORT-c6o.md", encoding="utf-8").read()
M["O-REPORT-c6o-itself-must-fail"] = rep_c6o
out = []
bad = 0
for name, text in M.items():
    if text is None:
        out.append("%-48s SKIPPED (mutation target absent)" % name)
        bad += 1
        continue
    p = os.path.join(tempfile.mkdtemp(), "REPORT-copy.md")
    open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run([sys.executable, "-I", E + "verify-c6p.py", p], capture_output=True, text=True)
    open(E + "neg/" + name + ".txt", "w").write(r.stdout[-6000:] + r.stderr[-1500:] + "\nEXIT CODE %d\n" % r.returncode)
    failed = [l for l in r.stdout.split("\n") if l.startswith("FAIL")]
    want_zero = name.startswith("V0")
    ok = (r.returncode == 0) if want_zero else (r.returncode != 0)
    if not ok:
        bad += 1
    out.append("%-48s exit %d  %s  failed checks: %d; first: %s" % (name, r.returncode, "OK" if ok else "WRONG", len(failed), (failed[0][:110] if failed else "none")))
out.append("SUMMARY: %d copies, %d wrong" % (len(M), bad))
open(E + "neg-output.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
sys.exit(1 if bad else 0)
