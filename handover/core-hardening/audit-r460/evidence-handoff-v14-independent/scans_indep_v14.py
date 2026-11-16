"""Banned-string scan (list read at run time, counts only) and secret-shape scan (patterns built from parts; prints file:line and kind only, never the match).
usage: python -I scans_indep_v14.py <audit_dir> <own_dir>"""
import ast, re, sys
from pathlib import Path
R = Path("/home/user/hadavin-sdk"); A = Path(sys.argv[1]); OWN = Path(sys.argv[2])
t = ast.parse((R / "tests/test_no_reference_material.py").read_text(encoding="utf-8"))
best = []
for n in ast.walk(t):
    if isinstance(n, (ast.Assign, ast.AnnAssign)) and getattr(n, "targets", [getattr(n, "target", None)])[0] is not None and n.value is not None:
        tg = n.targets[0] if isinstance(n, ast.Assign) else n.target
        if getattr(tg, "id", "") == "BANNED":
            best = list(ast.literal_eval(n.value))
print("BANNED entries read at run time:", len(best))
targets = {"doc v14": [A / "CORE-PR-HANDOFF-v14.md"], "doc v14 other-tracks": [A / "CORE-PR-HANDOFF-v14-other-tracks.md"],
           "builder evidence v14": [p for p in (A / "evidence-handoff-v14").rglob("*") if p.is_file()],
           "my folder": [p for p in OWN.rglob("*") if p.is_file() and p.suffix != ".pyc"]}
for name, fl in targets.items():
    cs = ci = 0; hitfiles = set()
    for p in fl:
        try: tx = p.read_text(encoding="utf-8", errors="replace")
        except Exception: continue
        low = tx.lower()
        for s in best:
            a = tx.count(s); b = low.count(s.lower()); cs += a; ci += b
            if b: hitfiles.add(p.name)
    print(f"banned scan | {name} | files {len(fl)} | case-sensitive hits {cs} | case-insensitive hits {ci} | files with a hit {len(hitfiles)}")
# secret shapes, built from parts
P = {
 "aws_key_id": re.compile("AK" + "IA" + "[0-9A-Z]{16}"),
 "aws_temp_id": re.compile("AS" + "IA" + "[0-9A-Z]{16}"),
 "github_token": re.compile("gh" + "[pousr]_" + "[A-Za-z0-9]{30,}"),
 "api_key_sk": re.compile(r"\bs" + "k-" + "[A-Za-z0-9_-]{20,}"),
 "slack_token": re.compile("xo" + "x[abprs]-" + "[A-Za-z0-9-]{10,}"),
 "private_key": re.compile("-----BEGIN " + "[A-Z ]*PRIVATE" + " KEY-----"),
 "jwt": re.compile(r"\bey" + r"J[A-Za-z0-9_-]{10,}\.ey" + r"J[A-Za-z0-9_-]{10,}\."),
 "assignment": re.compile(r"(?i)\b(pass" + r"word|secr" + r"et|tok" + r"en|api_?key)\b\s*[:=]\s*[\"']?[A-Za-z0-9/+=_-]{16,}"),
 "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}\b"),
 "arn_with_account": re.compile(r"arn:aws:[a-z0-9-]*:[a-z0-9-]*:\d{12}:"),
 "twelve_digit_account_word": re.compile(r"(?i)account[ _-]?(?:id|number)?\W{0,3}\d{12}\b"),
}
ALLOWED = "AKIAIOSFODNN7EXAMPLE"
for name, fl in targets.items():
    tot = {}; where = []
    for p in fl:
        try: lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
        except Exception: continue
        for i, l in enumerate(lines, 1):
            for k, rx in P.items():
                for mt in rx.finditer(l):
                    if mt.group(0) == ALLOWED: tot["allowed_example_key"] = tot.get("allowed_example_key", 0) + 1; continue
                    tot[k] = tot.get(k, 0) + 1; where.append(f"{p.name}:{i}:{k}")
    print(f"secret-shape scan | {name} | {dict(sorted(tot.items()))}")
    for w in where[:25]: print("   at", w)
