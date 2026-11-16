"""EVIDENCE RUNNER (independent): writes >=15 changed copies of REPORT-c6w.md under hostile/, runs verify-c6w.py on each, records exit and failing check names. Never prints banned strings."""
import re, os, subprocess, sys, json
E = os.path.dirname(os.path.abspath(__file__)) + "/"
D = os.path.dirname(E.rstrip("/")) + "/"
rep = open(D + "REPORT-c6w.md", encoding="utf-8").read()
src = open(D + "../../../tests/test_no_reference_material.py", encoding="utf-8").read()
BAN = list(eval(re.search(r"BANNED\s*=\s*(\(.*?\n\))", src, re.S).group(1)))
M = {}
def sub1(name, a, b, count=1):
    assert a in rep, (name, "absent")
    M[name] = rep.replace(a, b, count)
sub1("01-utc-ist-answer-pair", "2026-11-16T20:00:00Z = 2026-11-17T01:30:00 IST", "2026-11-16T20:00:00Z = 2026-11-17T01:45:00 IST")
sub1("02-check-time-ist-seconds", "19:44:12 UTC = 01:14:12 IST", "19:44:12 UTC = 01:15:12 IST")
sub1("03-weekday-post-due", "Wed 25 Nov 2026 15:00 UTC = 20:30 IST", "Tue 25 Nov 2026 15:00 UTC = 20:30 IST")
sub1("04-weekday-mon23", "Mon 23 Nov", "Tue 23 Nov")
sub1("05-row-count-104-first", "holds 104 proposed", "holds 103 proposed")
sub1("06-ready-57-first", "READY (57:", "READY (56:")
sub1("07-card-87-words-first", "the card then holds 87 words", "the card then holds 88 words")
sub1("08-row-list-swap", "rows 23, 58, 59, which need n8n", "rows 23, 58, 60, which need n8n")
sub1("09-lease-45-to-55-first", "LEASE = a 45-second setting", "LEASE = a 55-second setting")
sub1("10-wake-30-to-20-first", "it wakes every 30 seconds", "it wakes every 20 seconds")
sub1("11-G12-open-to-closed", "It is OPEN: I do not approve it", "It is CLOSED: I approve it")
sub1("12-post-due-ist-arith", "15:00 UTC = 20:30 IST", "15:00 UTC = 20:00 IST")
sub1("13-K3B-5-to-6-first", "K3B 5, K3 3", "K3B 6, K3 3")
sub1("14-title-c6w-to-c6v", "# REPORT-c6w:", "# REPORT-c6v:")
sub1("15-wave1-95-to-96-first", "95 of the 104 rows", "96 of the 104 rows")
sub1("16-reviewer-order-swapped", "builder: builder-A; reviewers: reviewer-B, reviewer-C", "builder: builder-A; reviewers: reviewer-C, reviewer-B")
sub1("17-box-words-2465-to-2466", "This box holds 2465 words", "This box holds 2466 words")
sub1("18-Wed18Nov-to-Thu", "Wed 18 Nov 2026", "Thu 18 Nov 2026")
sub1("19-lease-sentence-45-second-card", "the 45-second setting", "the 50-second setting")
sub1("20-fake-key-from-parts", "WHAT THE LINE DOES NOT DO:", "WHAT THE LINE DOES NOT DO: " + "AK" + "IAQWERTY123456" + " ")
sub1("21-banned-name-inserted", "WHAT THE LINE DOES NOT DO:", "WHAT THE LINE DOES NOT DO: " + BAN[0] + " ")
sub1("22-mail-shaped", "WHAT THE LINE DOES NOT DO:", "WHAT THE LINE DOES NOT DO: " + "jane.doe" + "@" + "mailbox" + ".org ")
sub1("23-ghp-token-from-parts", "WHAT THE LINE DOES NOT DO:", "WHAT THE LINE DOES NOT DO: " + "gh" + "p_" + "abcdefghij0123456789 ")
L = rep.split("\n")
i = [k for k, l in enumerate(L) if l.startswith("`## ANSWER (studio lead")][0]
M["24-answer-line-deleted"] = "\n".join(L[:i] + L[i+1:])
i = [k for k, l in enumerate(L) if l.startswith("| 50 | NOT APPLIED")][0]
M["25-row-50-deleted"] = "\n".join(L[:i] + L[i+1:])
M["26-row-30-old-text-changed"] = "\n".join(L[:i] if False else [ (l.replace("`", "`X", 1) if l.startswith("| 30 | NOT APPLIED") else l) for l in L])
i = [k for k, l in enumerate(L) if l.startswith("WHAT THE LINE DOES NOT DO")][0]
M["27-does-not-do-line-deleted"] = "\n".join(L[:i] + L[i+1:])
M["28-trailing-whitespace-only(control: expect pass)"] = rep + "\n"
M["29-one-word-added-in-detail-section"] = rep.replace("\n## Start here, part 2", " Extra.\n## Start here, part 2", 1) if "\n## Start here, part 2" in rep else None
M["30-one-word-added-in-box"] = rep.replace("WORDS YOU NEED (the short list;", "WORDS YOU NEED (the short short list;", 1)
res = []
for n, t in M.items():
    if t is None or (t == rep and "control" not in n):
        res.append("%-55s SKIPPED (no change made)" % n); continue
    d = E + "hostile/" + n.split("(")[0] + "/"; os.makedirs(d, exist_ok=True)
    open(d + "REPORT-c6w.md", "w", encoding="utf-8").write(t)
    open(d + "c6w-CHANGES.md", "w", encoding="utf-8").write(open(D + "c6w-CHANGES.md", encoding="utf-8").read())
    r = subprocess.run([sys.executable, "-B", "-I", E + "verify-c6w.py", d + "REPORT-c6w.md"], capture_output=True, text=True)
    fl = [l.split(" :: ")[0][:90] for l in r.stdout.split("\n") if l.startswith("FAIL")]
    open(d + "out.txt", "w").write(r.stdout[-4000:] + r.stderr[-800:] + "\nEXIT %d\n" % r.returncode)
    res.append("%-55s exit %d  %s  failed=%d %s" % (n, r.returncode, "CAUGHT" if r.returncode else "MISSED", len(fl), "; ".join(fl[:3])))
open(E + "hostile-output.txt", "w").write("\n".join(res) + "\n")
print("\n".join(res))
