import re, subprocess, sys, os
E = os.path.dirname(os.path.abspath(__file__))
rep = open(E + "/../REPORT-c6v.md", encoding="utf-8").read()
L = rep.split("\n")
def sub(old, new, count=1):
    assert rep.count(old) >= 1, old
    return rep.replace(old, new, count)
def drop_line(n):  # 1-based
    return "\n".join(L[:n-1] + L[n:])
def dup_line(n):
    return "\n".join(L[:n] + [L[n-1]] + L[n:])
row50 = [i+1 for i,l in enumerate(L) if l.startswith("| 50 | NOT APPLIED")][0]
M = {
"I01-stale-row-count-intro": sub("holds 104 proposed text changes", "holds 103 proposed text changes"),
"I02-ready-count": sub("Of the 104 rows, 57 are ready", "Of the 104 rows, 58 are ready"),
"I03-wrong-IST-example-line": sub("2026-11-16T19:20:00Z = 2026-11-17T00:50:00 IST", "2026-11-16T19:20:00Z = 2026-11-17T00:20:00 IST"),
"I04-wrong-IST-check-time-one-place": sub("19:04:44 UTC = 00:34:44 IST", "19:04:44 UTC = 00:44:44 IST"),
"I05-check-time-UTC-one-place": sub("2026-11-16T19:04:44Z = 00:34:44 IST (the check", "2026-11-16T19:04:45Z = 00:34:44 IST (the check"),
"I06-G12-hold-removed-L-LEASE": sub("and need the G12 approval first", "and need approval first"),
"I07-card-words-line1": sub("line 1 (11 words)", "line 1 (12 words)"),
"I08-wrong-sheet-version-one-place": sub("none of OWNER-SHEET-v34-A.md, OWNER-SHEET-v34-B.md", "none of OWNER-SHEET-v33-A.md, OWNER-SHEET-v34-B.md"),
"I09-drop-row-50": drop_line(row50),
"I10-duplicate-row-50": dup_line(row50),
"I11-box-word-count-stated": sub("This box holds 2478 words", "This box holds 2476 words"),
"I12-99-of-104": sub("(99 of 104 rows name files", "(98 of 104 rows name files"),
"I13-five-open-to-four": sub("Five items are OPEN", "Four items are OPEN"),
"I14-release-note-line-cite": sub("release note v14 line 33", "release note v14 line 34"),
"I15-wrong-version-name-release-note": sub("LEAD-RELEASE-NOTE-v18.md carries the 45-second", "LEAD-RELEASE-NOTE-v17.md carries the 45-second"),
"I16-waiting-rows-3-to-4": sub("the 3 rows that wait for a check", "the 4 rows that wait for a check"),
}
os.makedirs(E + "/mut", exist_ok=True)
env = dict(os.environ, C6V_STEPS=E + "/steps-snapshot")
out = []
for k, v in M.items():
    assert v != rep, k
    p = E + "/mut/" + k + ".md"
    open(p, "w", encoding="utf-8").write(v)
    r = subprocess.run([sys.executable, "-B", "-I", E + "/verify-c6v.py", p], capture_output=True, text=True, env=env)
    fails = [l for l in r.stdout.split("\n") if l.startswith("FAIL")]
    base = [l for l in fails if "every evidence-c6v file the report names exists" in l]
    nf = len(fails) - len(base)
    out.append("%s rc=%d new_FAILs=%d %s" % (k, r.returncode, nf, "CAUGHT" if nf > 0 else "MISSED") + ("  first: " + [l for l in fails if l not in base][0][:110] if nf else ""))
# CHANGES forgeries: no verifier reads c6v-CHANGES.md
ch = open(E + "/../c6v-CHANGES.md", encoding="utf-8").read()
for k, a, b in [("I17-CHANGES-forged-267", "267 changed copies", "300 changed copies"), ("I18-CHANGES-forged-heavy-runs", "6 full run_all.sh runs", "3 full run_all.sh runs")]:
    out.append("%s: present in CHANGES=%s; verify-c6v.py/part2/part3 read c6v-CHANGES.md: %s" % (k, a in ch, any("CHANGES" in open(E + "/" + f).read() and "c6v-CHANGES" in open(E + "/" + f).read() for f in ["verify-c6v.py", "verify_c6v_part2.py", "verify_c6v_part3.py"])))
open(E + "/mutations-output.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
