"""Independent scans (counts and file:line only; the banned list is read at run time from the repo test and never printed or written).
Usage: python -I -B scan_indep.py <path>...   Exit 1 on any hit."""
import ast, os, re, sys, unicodedata
src = open("/home/user/hadavin-sdk/tests/test_no_reference_material.py", encoding="utf-8").read()
banned = None
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "BANNED" for t in node.targets):
        banned = [str(x) for x in ast.literal_eval(node.value)]
assert banned
ZW = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"), None)
def norm(t): return unicodedata.normalize("NFKC", t).translate(ZW).lower()
SECRET = {
 "aws-access-key-shape": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "private-key-block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY"),
 "github-token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"), "api-key-sk": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
 "slack-token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "google-key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
 "url-with-password": re.compile(r"[a-z][a-z0-9+.-]*://[^\s:/@'\"]+:[^\s@'\"/]{4,}@[^\s'\"]+"), "long-hex-40plus": re.compile(r"\b[0-9a-f]{40,}\b"),
 "email-address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}\b"), "twelve-digit-number": re.compile(r"(?<![0-9.])\d{12}(?![0-9])"),
 "password-literal": re.compile(r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"\s]{6,}['\"]"),
}
paths = []
for r in sys.argv[1:]:
    if os.path.isfile(r): paths.append(r)
    else:
        for d, _, fs in os.walk(r):
            if "__pycache__" in d: continue
            paths += [os.path.join(d, f) for f in fs]
bh = 0; bfiles = 0; sec = {k: [] for k in SECRET}; scanned = 0; unread = 0
for p in sorted(paths):
    try: t = open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError): unread += 1; print("UNREADABLE", p); continue
    scanned += 1; nt = norm(t); n = sum(nt.count(norm(b)) for b in banned)
    if n: bh += n; bfiles += 1; print("BANNED-HIT file", p, "count", n)
    for ln, line in enumerate(t.splitlines(), 1):
        for k, rx in SECRET.items():
            for mt in rx.finditer(line):
                if mt.group(0) == "AKIAIOSFODNN7EXAMPLE": continue
                sec[k].append(f"{p}:{ln}")
print(f"files scanned {scanned}; unreadable {unread}; banned strings checked {len(banned)}; banned hits {bh} in {bfiles} files (after NFKC and zero-width removal)")
tot = 0
for k, v in sec.items():
    print(f"secret-shape {k}: {len(v)} hits" + (" at " + ", ".join(sorted(set(v))[:6]) if v else "")); tot += len(v)
sys.exit(1 if (bh or tot or unread) else 0)
