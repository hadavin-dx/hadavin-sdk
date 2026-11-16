"""Plants mutations into COPIES of REPORT-c6p.md (never the original), runs indep_c6p.py on each. Control (no change) must exit 0; every mutation must exit 1.
Fake secret shapes are built from parts. Output: mut/<name>.out.txt and mutation-summary.txt"""
import re, subprocess, sys, os, tempfile
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
E = D + "evidence-c6p-independent/"
os.makedirs(E + "mut", exist_ok=True)
rep = open(D + "REPORT-c6p.md", encoding="utf-8").read()
L = rep.split("\n")


def rowline(t, k):
    ls = t.split("\n")
    return [i for i, l in enumerate(ls) if l.startswith("| %d | NOT APPLIED" % k)][0]


def sub_once(t, a, b, nth=0):
    idx = -1
    for _ in range(nth + 1):
        idx = t.find(a, idx + 1)
        assert idx >= 0, a
    return t[:idx] + b + t[idx + len(a):]


def in_row(t, k, a, b):
    ls = t.split("\n")
    i = rowline(t, k)
    assert a in ls[i], (k, a)
    ls[i] = ls[i].replace(a, b, 1)
    return "\n".join(ls)


def del_line(t, pred):
    ls = t.split("\n")
    i = [j for j, l in enumerate(ls) if pred(l)][0]
    del ls[i]
    return "\n".join(ls)


def in_line(t, startswith, a, b):
    ls = t.split("\n")
    i = [j for j, l in enumerate(ls) if l.startswith(startswith) and a in l][0]
    ls[i] = ls[i].replace(a, b, 1)
    return "\n".join(ls)


aws = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
sk = "s" + "k-" + "abcdefghijklmnopqrstuvwx"
ghp = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123"
M = {}
M["00-control-unchanged"] = rep
M["01-old-text-altered-row5"] = None
r5 = L[rowline(rep, 5)]
old5 = re.match(r"^\| 5 \| [^|]*\| [^|]* \| \d+ \| .*? \| `(.*?)` \|", r5).group(1)
M["01-old-text-altered-row5"] = in_row(rep, 5, "`" + old5 + "`", "`" + old5[:-1] + "Z`") if len(old5) > 3 else None
ln20 = re.match(r"^\| 20 \| [^|]*\| [^|]* \| (\d+) \|", L[rowline(rep, 20)]).group(1)
M["02-line-number-off-by-one-row20"] = in_row(rep, 20, "| %s |" % ln20, "| %d |" % (int(ln20) + 1))
M["03-row-50-deleted"] = del_line(rep, lambda l: l.startswith("| 50 | NOT APPLIED"))
M["04-duplicate-id-51-as-50"] = in_row(rep, 51, "| 51 |", "| 50 |")
M["05-ready-to-default-row5"] = in_row(rep, 5, "NOT APPLIED; ready", "NOT APPLIED; on the default of L-SAVE")
M["06-ready-to-check-row6"] = in_row(rep, 6, "NOT APPLIED; ready", "NOT APPLIED; after check C-8")
M["07-default-to-NOT-FILMABLE-row13"] = in_row(rep, 13, "NOT APPLIED; on the default of L-CARD, L-CARDLEN, L-LEASE", "NOT APPLIED; NOT FILMABLE until an answer")
M["08-card-extra-word-row13"] = in_row(rep, 13, "processed once. We make", "processed once now. We make")
M["09-box-115-to-110-words"] = sub_once(rep, "exactly 115 words", "exactly 110 words") if "exactly 115 words" in rep.split("## 0.")[0] else sub_once(rep, "115 words", "110 words")
M["10-money-IST-1804-wrong"] = sub_once(rep, "18:04 UTC = 23:34 IST", "18:04 UTC = 23:35 IST")
M["11-money-IST-1829-wrong"] = sub_once(rep, "18:29 UTC = 23:59 IST", "18:29 UTC = 23:58 IST")
M["12-weekday-wed-18-nov-wrong"] = sub_once(rep, "Wed 18 Nov", "Thu 18 Nov")
M["13-weekday-mon-23-nov-wrong"] = sub_once(rep, "Mon 23 Nov 2026", "Tue 23 Nov 2026")
M["14-range-61.8"] = sub_once(rep, "60.1 to 61.9", "60.1 to 61.8", 3)
M["15-range-54.8"] = sub_once(rep, "52.8 to 54.9", "52.8 to 54.8", 1)
M["16-runs-done-9"] = sub_once(rep, "10 runs done", "9 runs done")
M["17-voided-label-dropped"] = None
ls = L[:]
for j, l in enumerate(ls):
    if "18 kept runs" in l and "VOID-fl45k6c" in l and "VOID-fl45k3b" in l and not l.startswith("| "):
        ls[j] = l.replace("VOID-fl45k6c", "the other voided run")
        M["17-voided-label-dropped"] = "\n".join(ls)
        break
M["18-fake-aws-key"] = rep + "\nkey " + aws + "\n"
M["19-fake-sk-key"] = rep + "\nkey " + sk + "\n"
M["20-fake-ghp-token"] = rep + "\ntoken " + ghp + "\n"
M["21-email-address"] = rep + "\nwrite to " + "a.person" + "@" + "example-mail.org" + "\n"
M["22-box-row-count-93"] = sub_once(rep, "holds 94 proposed", "holds 93 proposed")
M["23-3b-total-ready-48"] = sub_once(rep, "ready 49, on defaults only 42", "ready 48, on defaults only 42")
M["24-row-ref-in-new-runsheet-text-row17"] = in_row(rep, 17, "` | `", "` | `(see row 12) ")
M["25-5a-row-15-deleted"] = del_line(rep, lambda l: l.startswith("| 15 | run sheet, line"))
M["26-5a-view-text-changed-row21"] = in_line(rep, "| 21 | run sheet, line", "Scene 3 caption", "Scene 4 caption")
M["27-setting-name-in-box"] = sub_once(rep, "NOTHING IN THIS REPORT HAS BEEN APPLIED", "NOTHING IN THIS REPORT (EXECUTIONS_DATA_PRUNE) HAS BEEN APPLIED")
M["28-section0-ready-list-drops-22"] = sub_once(rep, "19, 22, 25, 26", "19, 25, 26")
M["29-3c-default-list-drops-24"] = sub_once(rep, "21, 24, 29, 31, 33", "21, 29, 31, 33")
M["30-option-b-extra-word"] = sub_once(rep, "processed once, claimed only when", "processed once, claimed only ever when")
M["31-option-b-35s-to-36s"] = in_line(rep, "| L-CARDLEN | studio lead", "about 35 s, budget 35 s", "about 36 s, budget 36 s")
M["32-box-200s-to-210s"] = sub_once(rep, "about 200 s", "about 210 s")
M["33-reading2-extra-word"] = sub_once(rep, "2 = 'The 45 seconds is a setting", "2 = 'The 45 seconds is now a setting")
M["34-utc-without-ist-in-new-text-row8"] = in_row(rep, 8, "`", "`", ) if False else None
r8 = L[rowline(rep, 8)]
parts = r8.split(" | `")
M["34-utc-without-ist-in-new-text-row8"] = in_row(rep, 8, "` | `", "` | `At 09:00 UTC. ", ) if len(parts) >= 3 else None
M["35-section3-tied-column-changed"] = in_line(rep, "| L-ONEDB | studio lead", "| 90, 91 |", "| 90 |")
M["36-label-used-before-definition-GATE"] = sub_once(rep, "NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE.", "NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE (a GATE is open).")
M["37-undefined-L-label-in-box"] = sub_once(rep, "You answer with ONE line", "You answer L-FOO with ONE line")
M["38-stale-89-rows"] = sub_once(rep, "91 wave 1 rows" if "91 wave 1 rows" in rep else "91 rows", "89 rows", 0)
M["39-weekday-tue-17-nov-wrong"] = sub_once(rep, "Tue 17 Nov", "Mon 17 Nov")
M["40-IST-dropped-from-sheet-check-line"] = sub_once(rep, "16:01 UTC = 21:31 IST", "16:01 UTC", 0) if "16:01 UTC = 21:31 IST" in rep else None
M["41-two-rows-swapped-10-11"] = None
ls = rep.split("\n")
a, b = rowline(rep, 10), rowline(rep, 11)
ls[a], ls[b] = ls[b], ls[a]
M["41-two-rows-swapped-10-11"] = "\n".join(ls)
M["42-voided-run-IST-swap-noon"] = sub_once(rep, "23:49 IST", "23:48 IST")
M["43-repeat-sentence-changed-to-30s-in-row21-old-text-moved"] = in_row(rep, 21, "| 32 |", "| 31 |") if "| 32 |" in L[rowline(rep, 21)] else None

out, bad = [], 0
for name, t in M.items():
    if t is None:
        out.append("%-60s SKIPPED (target absent)" % name)
        bad += 1
        continue
    if name[:3] != "00-" and t == rep:
        out.append("%-60s NOT CHANGED (mutation failed to apply)" % name)
        bad += 1
        continue
    p = os.path.join(tempfile.mkdtemp(), "REPORT-copy.md")
    open(p, "w", encoding="utf-8").write(t)
    r = subprocess.run([sys.executable, "-B", "-I", E + "indep_c6p.py", p], capture_output=True, text=True)
    open(E + "mut/" + name + ".out.txt", "w").write(r.stdout[-5000:] + r.stderr[-800:] + "\nEXIT %d\n" % r.returncode)
    fl = [l for l in r.stdout.split("\n") if l.startswith("FAIL")]
    ok = (r.returncode == 0) if name.startswith("00-") else (r.returncode == 1)
    bad += 0 if ok else 1
    out.append("%-60s exit %d %s  fails: %d  first: %s" % (name, r.returncode, "OK" if ok else "WRONG", len(fl), fl[0][:100] if fl else "-"))
out.append("SUMMARY: %d copies (1 control), %d wrong or skipped" % (len(M), bad))
open(E + "mutation-summary.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
