import re, os, sys
E = os.path.dirname(os.path.abspath(__file__))
H = "/home/user/hadavin-sdk"
src = open(H + "/tests/test_no_reference_material.py", encoding="utf-8").read()
ns = {}
m = re.search(r"^BANNED\s*(?::[^=]*)?=\s*(\(.*?\n\)|\[.*?\n\])", src, re.S | re.M)
B = list(eval(m.group(1), {}, ns))
SEC = [r"AK"+r"IA[A-Z0-9]{16}", r"s"+r"k-[A-Za-z0-9_-]{16,}", r"gh"+r"[pous]_[A-Za-z0-9]{20,}", r"xox"+r"[bpa]-[0-9A-Za-z-]{8,}", r"-----BEGIN [A-Z ]*PRIVATE KEY", r"AI"+r"za[0-9A-Za-z_-]{30,}", r"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\."]
MAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+")
files = [H + "/handover/core-hardening/c6-skip-audit/REPORT-c6v.md", H + "/handover/core-hardening/c6-skip-audit/c6v-CHANGES.md", H + "/handover/core-hardening/c6-skip-audit/checkpoint-c6v.md"]
for base in ("evidence-c6v", "evidence-c6v-independent"):
    for r, d, fs in os.walk(H + "/handover/core-hardening/c6-skip-audit/" + base):
        if "/steps-snapshot" in r or "/mut" in r or "/neg" in r: continue
        files += [os.path.join(r, f) for f in fs]
tb = ts = tm = tmx = 0; bad = []
for f in sorted(files):
    if f.endswith("myscan.py") or f.endswith("scan-independent.txt"): continue
    t = open(f, encoding="utf-8", errors="replace").read()
    b = sum(t.lower().count(s.lower()) for s in B)
    s = sum(1 for p in SEC for x in re.finditer(p, t) if x.group(0) != "AKIAIOSFODNN7EXAMPLE")
    ml = [x.group(0) for x in MAIL.finditer(t)]
    ml = [x for x in ml if not x.endswith("noreply@anthropic.com")]
    ok = [x for x in ml if re.search(r"@(example\.(test|com|org)|[a-z0-9-]*\.test|example)$", x)]
    tmx += len(ok); ml = [x for x in ml if x not in ok]
    tb += b; ts += s; tm += len(ml)
    if b or s or ml: bad.append("%s banned=%d secret=%d mail=%d" % (f.replace(H, ""), b, s, len(ml)))
print("banned list entries read at run time:", len(B)); print("files scanned:", len(files)); print("mail-shaped but reserved/example domain (excluded):", tmx); print("totals banned=%d secret-shape=%d mail-shape=%d" % (tb, ts, tm)); print("\n".join(bad[:40]))
