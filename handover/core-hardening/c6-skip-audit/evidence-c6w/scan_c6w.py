"""c6w scan: banned names (read at run time from tests/test_no_reference_material.py, never written here), secret shapes and e-mail addresses in REPORT-c6w.md and in every file of evidence-c6w (counts only; names of files, never the hits).
Usage: python3 -B -I scan_c6w.py   Output: scan-c6w-output.txt. Exit 1 on any hit."""
import re, os, sys
E = os.path.dirname(os.path.abspath(__file__)) + "/"
H = E.rsplit("/handover/", 1)[0] + "/"
src = open(H + "tests/test_no_reference_material.py", encoding="utf-8").read()
B = list(eval(re.search(r"BANNED\s*=\s*(\(.*?\n\))", src, re.S).group(1)))
SECRET = [("AK" + "IA[A-Z0-9]{12,}", "aws-key-shape"), ("s" + "k-[A-Za-z0-9_-]{16,}", "sk-shape"), ("gh" + "p_[A-Za-z0-9]{16,}", "ghp-shape"), ("xox" + "[bp]-[0-9]", "slack-shape"), ("-----BEGIN [A-Z ]*PRIVATE", "private-key")]
MAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
files = [H + "handover/core-hardening/c6-skip-audit/REPORT-c6w.md"]
for r, d, fs in os.walk(E):
    d[:] = [x for x in d if x not in ("tree", "steps-snapshot")]   # copies of the audited demo files and of the owner sheets are not this run's output
    if "/neg" in r.replace(E, "/") and r != E.rstrip("/"):
        pass
    for f in fs:
        files.append(os.path.join(r, f))
out, bad = [], 0
tot = {"banned": 0, "secret": 0, "mail": 0}
for f in sorted(files):
    if f.endswith("scan-c6w-output.txt") or f.endswith("scan_c6w.py"):
        continue
    t = open(f, encoding="utf-8", errors="replace").read()
    b = sum(t.count(s) for s in B)
    sec = sum(len(re.findall(p, t)) for p, _ in SECRET) - t.count("AKIAIOSFODNN7EXAMPLE") * 0
    sec = sum(1 for p, _ in SECRET for m in re.finditer(p, t) if m.group(0) != "AKIAIOSFODNN7EXAMPLE")
    ml = [m.group(0) for m in MAIL.finditer(t)]
    ml = [m for m in ml if not re.match(r"^[^A-Za-z0-9]*@", m) and not re.search(r"@(example\.(test|com|org)|[a-z0-9-]*\.test)$", m) and not m.endswith("noreply@anthropic.com")]
    tot["banned"] += b; tot["secret"] += sec; tot["mail"] += len(ml)
    if b or sec or ml:
        out.append("HIT %s: banned %d, secret-shaped %d, other e-mail-shaped %d" % (f.replace(H, ""), b, sec, len(ml)))
out.append("SCANNED (own output only; folders tree/ and steps-snapshot/ are skipped): %s" % ", ".join(sorted(set(os.path.relpath(f, H) .split("/")[-2] + "/" for f in files))))
out.append("SCANNED %d files; banned names list has %d entries (read at run time); totals %s" % (len(files), len(B), tot))
open(E + "scan-c6w-output.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
sys.exit(1 if any(tot.values()) else 0)
