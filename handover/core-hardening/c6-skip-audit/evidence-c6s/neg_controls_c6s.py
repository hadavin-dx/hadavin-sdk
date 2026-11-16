"""Negative controls for verify-c6r.py. Builds changed copies of REPORT-c6q.md (never edits it), runs verify-c6r.py on each and records the exit code
and the raw output. A control copy with no change must exit 0; every changed copy must exit non-zero. Fake key-shaped strings are built from parts here.
Usage: python3 neg_controls_c6r.py   Output: neg/<name>.txt per copy and neg-output.txt (summary). Exit 1 if any changed copy exits 0."""
import re, subprocess, sys, os, tempfile
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
E = D + "evidence-c6r/"
os.makedirs(E + "neg", exist_ok=True)
rep = open(D + "REPORT-c6r.md", encoding="utf-8").read()
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
box_end = rep.index("## 0. Failures")
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
# c6p classes (updated to the c6q text)
M["N1-card-word-count-wrong-in-row13"] = mut_row(rep, 13, "new", lambda s: s.replace("processed once.", "processed once now.", 1))
M["N2-row11-says-103-words"] = mut_row(rep, 11, "new", lambda s: re.sub(r"\b90 words", "103 words", s, count=1))
M["N3-row-N-reference-in-new-text"] = mut_row(rep, 21, "new", lambda s: s + " (row 13 explains)")
M["N4-accepted-exit-in-row8"] = mut_row(rep, 8, "new", lambda s: s + " The lease question is accepted.")
i5 = [i for i, l in enumerate(rep.split("\n")) if l.startswith("| 87 | page statements, line")][0]
ls = rep.split("\n"); del ls[i5]
M["N5-5a-page-row-missing"] = "\n".join(ls)
M["N6-newest-sheet-claim-stale-v27"] = rep.replace("v29", "v27")
M["N7-row90-broken-sentence-and-third-place"] = mut_row(rep, 90, "new", lambda s: s.rstrip() + " owned by a third place")
M["N8-row6-claims-deletion-erases"] = mut_row(rep, 6, "new", lambda s: s.replace("NOT verified that deleting a run erases it", "Deleting a run erases it", 1))
M["N9-row8-latest-start-missing"] = mut_row(rep, 8, "new", lambda s: s.replace("18:04 UTC = 23:34 IST", "18:29 UTC = 23:59 IST", 1))
M["N10-144.3-unlabelled-row47"] = mut_row(rep, 47, "new", lambda s: s.replace("144.3 s after n8n came back up", "144.3 s", 1))
M["N11-lease-none-meaning-missing"] = rep.replace("WHAT 'NONE' CLAIMS, HONESTLY", "WHAT IT CLAIMS", 1)
M["N12-label-GATE-used-before-defined-in-box"] = rep.replace("You answer with ONE line", "You answer with ONE GATE line", 1)
M["N13-box-too-long"] = rep[:box_end] + ("filler words here " * 1100) + "\n" + rep[box_end:]
M["N14-L-SCENES-question-back"] = rep.replace("| L-CUT | studio lead |", "| L-SCENES | studio lead | x | 1 | No | y | 2 |\n| L-CUT | studio lead |", 1)
M["N15-row13-NOT-FILMABLE-back"] = mut_row(rep, 13, "st", lambda s: "NOT APPLIED; NOT FILMABLE until L-LEASE is answered")
M["N16-stale-103-words-line"] = rep + "\nThe spoken card holds 103 words.\n"
M["N17-box-names-an-n8n-setting"] = rep[:box_end] + " saveDataSuccessExecution " + rep[box_end:]
M["N18-lease-sentence-on-the-card-by-default-row13"] = mut_row(rep, 13, "new", lambda s: s + " We make this claim only when the second send comes within 45 seconds of the first send.")
M["N19-death-of-5a-counts-wrong-3b"] = re.sub(r"(\| L-SAVE \| )(\d+)", lambda m: m.group(1) + str(int(m.group(2)) + 1), rep, count=1)
def once(a, b, text=None):
    t = text if text is not None else rep
    assert t.count(a) >= 1, a[:60]
    return t.replace(a, b, 1)


M["C1-check-label-C-8-back-in-row70"] = mut_row(rep, 70, "new", lambda s: s + " (true only after check C-8)")
M["C2-source-cite-RES97-in-row25"] = mut_row(rep, 25, "new", lambda s: s + " (RES:97)")
M["C3-reading-1-in-row13"] = mut_row(rep, 13, "new", lambda s: s + " (reading 1)")
M["C4-this-report-in-row21-view"] = mut_row(rep, 21, "view", lambda s: s + " this report")
M["C5-L-SCENES-back-in-3e"] = once("| Repeat-send check (rehearsal list item 13)", "| L-SCENES in 3e | Repeat-send check (rehearsal list item 13)")
M["C6-length-table-number-wrong"] = once("| (a) | 115 | 46.0 |", "| (a) | 116 | 46.0 |")
M["C8-C10b-pass-cell-says-only-b"] = once("all of (a), (b) and (c) are shown with line numbers", "(b) is shown")
M["C9-Q27-reading-sentence-twice-in-box"] = once("TO REVERSE A DEFAULT", "this report applies the strictest reading of your answer Q27\nTO REVERSE A DEFAULT")
M["C10-row90-ends-with-own-state"] = mut_row(rep, 90, "new", lambda s: s.rstrip()[: s.rstrip().rindex("`n8n`")] + "own state")
b9 = [l for l in rep.split("\n") if l.startswith("- [needs-lead] Gate G12")][0]
M["C11-section9-duplicate-bullet"] = rep.rstrip("\n") + "\n" + b9 + "\n"
M["C12-G12-gone-from-L-LEASE"] = "\n".join(l.replace("G12", "GX") if l.startswith("| L-LEASE | studio lead") else l for l in rep.split("\n"))
M["C13-ORD147-departure-gone-from-section0"] = once("- DEPARTURE FROM ORD:147, STATED:", "- NOTE:")
M["C14-item15-without-real-value"] = mut_row(rep, 6, "new", lambda s: s.replace("the real value of the customer-list key", "the customer-list key", 1))
M["C15-L-POST-gone-from-box"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| L-POST |"))
M["C16-1051-line-without-UNVERIFIED"] = rep + "\nThe plan line 1051 is stale.\n"
M["C17-ready-used-before-defined-in-box-intro"] = once("Every question has a default", "Every ready question has a default")
M["C18-check-time-not-in-report"] = rep.replace(CTU_PLACEHOLDER, "00:00:00") if False else re.sub(r"2026-11-16T16:\d\d:\d\dZ", "2026-11-16T10:00:00Z", rep)
M["C19-row11-total-wrong"] = mut_row(rep, 11, "new", lambda s: s.replace("about 190 s in all", "about 200 s in all", 1))
M["C20-add-16-wording-back"] = rep + "\nThe longer sentence adds +16 s.\n"
M["C21-tied-column-lacks-L-POST"] = re.sub(r"(\| L-POST \(new in c6q\).*\| )(11, 13, 21) \|$", r"\1 13, 21 |", rep, count=1, flags=re.M)

# ---- c6r: the eight mutations the independent evidence of c6q did not catch, and the new classes of c6r
M["E1-weekday-wrong-Thu-18-Nov"] = once("Wed 18 Nov 2026", "Thu 18 Nov 2026")
M["E1b-weekday-wrong-Tue-23-Nov"] = once("Mon 23 Nov 2026", "Tue 23 Nov 2026")
M["E2-lease-sentence-on-caption-row21"] = mut_row(rep, 21, "new", lambda s: s + " We make this claim only when the second send comes within 45 seconds of the first send.")
M["E3-capital-The-lease-question-in-row13"] = mut_row(rep, 13, "new", lambda s: s + " The lease question is open.")
M["E4-wrong-count-42-apply"] = once("36 apply on the default", "42 apply on the default")
M["E5-wrong-wave1-91-rows"] = once("85 wave 1 rows", "91 wave 1 rows") if "85 wave 1 rows" in rep else once("applies the 85 wave 1", "applies the 91 wave 1 rows")
M["E6-stale-58-s-in-box"] = rep[:box_end] + " The card needs about 58 s. " + rep[box_end:]
M["E7-within-45-seconds-row14"] = mut_row(rep, 14, "new", lambda s: s + " (within 45 seconds)")
M["E8-v29-file-missing-from-line"] = once("OWNER-SHEET-v29-B.md (written", "OWNER-SHEET-v29-X.md (written")
M["R1-M-A-gate-removed-row8"] = mut_row(rep, 8, "new", lambda s: s.replace("lease wording approved", "lease wording seen"))
M["R2-M-B-one-alert-fact-row14"] = mut_row(rep, 14, "new", lambda s: s.replace("it sends an alert, a warning mail", "it sends one alert, a warning mail", 1))
M["R3-M-C-assumption-label-gone-box"] = once("MY ASSUMPTION", "THE RULE")
M["R4-M-D-command-line-allowed-row6"] = mut_row(rep, 6, "new", lambda s: s.replace("never on a command line", "on a command line if short", 1))
M["R5-M-D-hit-means-nothing-row6"] = mut_row(rep, 6, "new", lambda s: s.replace("cancels or replaces that key at once", "writes it down", 1))
M["R6-M-E-row92-error-all"] = mut_row(rep, 92, "new", lambda s: s.replace('"saveDataErrorExecution": "none"', '"saveDataErrorExecution": "all"', 1))
M["R7-M-E-row53-ready-again"] = mut_row(rep, 53, "st", lambda s: "NOT APPLIED; ready")
M["R8-M-F-24-word-rewrite-back"] = rep + "\nWith answer 1 and option (b), line 1 is a 24-word rewrite.\n"
M["R9-take-over-back-in-box"] = once("TO REVERSE A DEFAULT", "the recovery flow takes over the contact\nTO REVERSE A DEFAULT") if False else rep.replace("claim the contact again", "take over the contact", 1)
M["R10-pipe-in-row-text"] = mut_row(rep, 15, "new", lambda s: s + " a | b")
M["R11-source-copy-statement-gone"] = rep.replace("89 of the 94 rows", "most rows", 1)
M["R12-L-SAVEERR-default-yes"] = "\n".join(l.replace("| No |", "| Yes |") if l.startswith("| L-SAVEERR | studio lead") else l for l in rep.split("\n"))
M["R13-item12-made-up-domain-check-gone"] = mut_row(rep, 6, "new", lambda s: s.replace("made-up e-mail domain and the name marker", "made-up domain", 1))
M["R14-IST-missing-next-to-22-10-example"] = rep.replace("22:10:00 IST", "22:10:00", 1)
M["O-REPORT-c6q-itself-must-fail"] = open(D + "REPORT-c6q.md", encoding="utf-8").read()
out = []
bad = 0
for name, text in M.items():
    if text is None:
        out.append("%-48s SKIPPED (mutation target absent)" % name)
        bad += 1
        continue
    p = os.path.join(tempfile.mkdtemp(), "REPORT-copy.md")
    open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run([sys.executable, "-I", E + "verify-c6r.py", p], capture_output=True, text=True)
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
