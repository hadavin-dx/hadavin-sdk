import re, subprocess, sys, os
C = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
SRC = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover"
HERE = C + "evidence-c6q-independent/"
rep = open(C + "REPORT-c6q.md", encoding="utf-8").read()
ROW = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*) \| (handover/\S+) \| (\d+) \| (.*?) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
def row(text, k, field, fn):
    ls = text.split("\n")
    i = [j for j, l in enumerate(ls) if l.startswith("| %d | NOT APPLIED" % k)][0]
    g = list(ROW.match(ls[i]).groups())
    idx = dict(id=0, st=1, ln=3, view=4, old=5, new=6, why=7)[field]
    g[idx] = fn(g[idx])
    ls[i] = "| %s | %s | %s | %s | %s | `%s` | `%s` | %s | %s |" % tuple(g)
    return "\n".join(ls)
def rp(a, b, n=1):
    assert a in rep, a
    return rep.replace(a, b, n)
M = {}
M["M01-wrong-count-48-ready"] = rp("49 are ready", "48 are ready")
M["M02-wrong-count-41-default"] = rp("42 apply on the default", "41 apply on the default")
M["M03-wave1-90"] = rp("applies wave 1 (every row except the 3 that wait for a check), 91 rows", "applies wave 1 (every row except the 3 that wait for a check), 90 rows")
M["M04-stale-58s-in-box"] = rp("budget 40 s.", "budget 40 s, earlier estimate about 58 s.") if "budget 40 s." in rep else rp("about 36 s", "about 58 s")
M["M05-row11-card-58s"] = row(rep, 11, "new", lambda s: s.replace("closing card 40 s", "closing card 58 s", 1))
M["M06-label-leak-row-N"] = row(rep, 21, "new", lambda s: s + " (see row 13)")
M["M07-label-leak-KEYdigits"] = row(rep, 21, "new", lambda s: s + " RS:41")
M["M08-label-leak-reading-1"] = row(rep, 14, "new", lambda s: s.replace("Not tested:", "Not tested (reading 1):", 1))
M["M09-label-leak-this-report"] = row(rep, 13, "new", lambda s: s.replace("processed once", "processed once, as this report says", 1))
M["M10-label-leak-lease-question"] = row(rep, 21, "new", lambda s: s + " The lease question is open.")
M["M11-wrong-IST-money-stop"] = rp("18:04 UTC = 23:34 IST", "18:04 UTC = 23:44 IST", 99)
M["M12-wrong-IST-post-due"] = rp("15:00 UTC = 20:30 IST", "15:00 UTC = 21:30 IST", 99)
M["M13-lease-sentence-on-card"] = row(rep, 13, "new", lambda s: s.replace('processed once."', 'processed once. We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim."', 1))
M["M14-lease-sentence-on-caption"] = row(rep, 21, "new", lambda s: s.replace("processed once\"", "processed once. The 45 seconds is a setting called the lease.\"", 1))
M["M15-row90-broken-end"] = row(rep, 90, "new", lambda s: s.rstrip()[:-len("database `n8n`")] + "own state")
M["M16-weekday-Mon-to-Tue"] = rp("Mon 23 Nov", "Tue 23 Nov", 99)
M["M17-weekday-Wed-to-Thu"] = rp("Wed 18 Nov 2026", "Thu 18 Nov 2026", 99)
M["M18-card-line2-word-removed"] = row(rep, 14, "new", lambda s: s.replace("it sends one alert,", "it sends alert,", 1))
M["M19-table-seconds-wrong"] = rp("| 46.0 |", "| 45.0 |")
M["M20-table-budget-wrong"] = rp("| 52.0 | 55 s |", "| 52.0 | 50 s |")
M["M21-old-text-altered"] = row(rep, 5, "old", lambda s: s[:-1] + ("X" if s[-1] != "X" else "Y"))
M["M22-line-number-off-by-one"] = row(rep, 5, "ln", lambda s: str(int(s) + 1))
M["M23-row-50-deleted"] = "\n".join(l for l in rep.split("\n") if not l.startswith("| 50 | NOT APPLIED"))
M["M24-duplicate-row-id"] = row(rep, 50, "id", lambda s: "49")
M["M25-status-ready-to-default"] = row(rep, 1, "st", lambda s: "NOT APPLIED; on the default of L-KILL")
M["M26-term-used-before-defined-intro"] = rp("NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE.", "NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE the n8n lease uses.")
M["M27-secret-shaped"] = rep + "\nkey sk-" + "a" * 24 + "\n"
M["M28-clock-UTC-without-IST"] = rp("NOTHING IN THIS REPORT", "At 17:00 UTC the take starts. NOTHING IN THIS REPORT")
M["M29-row-count-93-in-section0"] = rp("Of the 94 rows", "Of the 93 rows")
M["M30-stale-61.1-range"] = rp("60.1 to 61.9", "60.1 to 61.1", 1)
M["M31-wrong-sum-card-90-to-100"] = rp("Total 90 words, about 36 s, budget 40 s", "Total 100 words, about 40 s, budget 40 s") if "Total 90 words, about 36 s, budget 40 s" in rep else None
M["M32-lease-sentence-in-spoken-line1-via-row14"] = row(rep, 14, "new", lambda s: s.replace("Line 3, retention", "Line 3, retention (within 45 seconds)", 1))
M["N0-control-unchanged"] = rep
out = []
def names(text, cmd):
    p = HERE + "mut/" + "tmp.md"; open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run(cmd + [p] if cmd[-1] != "SRC" else cmd, capture_output=True, text=True)
    return set(l[5:].split(" :: ")[0] for l in r.stdout.split("\n") if l.startswith("FAIL")), r
os.makedirs(HERE + "mut", exist_ok=True)
indep = [sys.executable, "-B", "-I", HERE + "indep_check.py"]
build = [sys.executable, "-B", HERE + "bcopy/verify-c6q.py"]
def run_i(text):
    p = HERE + "mut/tmp.md"; open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run(indep + [p, SRC], capture_output=True, text=True)
    return set(l[5:].split(" :: ")[0] for l in r.stdout.split("\n") if l.startswith("FAIL")), r
def run_b(text):
    p = HERE + "mut/tmp.md"; open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run(build + [p], capture_output=True, text=True)
    return set(l[5:].split(" :: ")[0] for l in r.stdout.split("\n") if l.startswith("FAIL")), r
bi, _ = run_i(rep); bb, _ = run_b(rep)
lines = ["baseline fails: indep=%d builder=%d" % (len(bi), len(bb))]
ci = cb = n = 0
for k, t in M.items():
    if t is None: lines.append("%-48s SKIPPED" % k); continue
    n += 1
    fi, _ = run_i(t); fb, _ = run_b(t)
    ni, nb = sorted(fi - bi), sorted(fb - bb)
    ci += bool(ni); cb += bool(nb)
    lines.append("%-48s indep:%-6s builder:%-6s | %s | %s" % (k, "CAUGHT" if ni else "MISSED", "CAUGHT" if nb else "MISSED", (ni[0][:70] if ni else "-"), (nb[0][:70] if nb else "-")))
lines.append("TOTAL mutations incl control: %d; indep caught %d, builder caught %d" % (n, ci, cb))
open(HERE + "mutation-results.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
