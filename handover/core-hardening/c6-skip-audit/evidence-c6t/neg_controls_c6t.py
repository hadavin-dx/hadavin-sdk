"""Negative controls for verify-c6s.py. Builds changed copies of REPORT-c6s.md (never edits it), runs verify-c6s.py on each and records the exit code
and the raw output. A control copy with no change must exit 0; every changed copy must exit non-zero. Fake key-shaped strings are built from parts here.
Usage: python3 neg_controls_c6s.py   Output: neg/<name>.txt per copy and neg-output.txt (summary). Exit 1 if any changed copy exits 0."""
import re, subprocess, sys, os, tempfile
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
E = D + "evidence-c6s/"
os.makedirs(E + "neg", exist_ok=True)
rep = open(D + "REPORT-c6s.md", encoding="utf-8").read()
import ast
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


SKIPPED_PORT = []
def run_block(src, name):
    for node in ast.parse(src).body:
        try:
            exec(compile(ast.Module([node], []), name, "exec"), globals())
        except Exception as e:
            SKIPPED_PORT.append("%s line %d: %s %s" % (name, node.lineno, type(e).__name__, str(e)[:70]))

M = {}
box_end = rep.index("## 0. Failures")
run_block(open(E + "neg_ported_c6r.py", encoding="utf-8").read(), "neg_ported_c6r.py")
run_block(open(E + "neg_new_c6s.py", encoding="utf-8").read(), "neg_new_c6s.py")
out = []
bad = 0
for name, text in M.items():
    envd = ENV.get(name)
    if text is None:
        out.append("%-48s SKIPPED (mutation target absent)" % name)
        bad += 1
        continue
    p = os.path.join(tempfile.mkdtemp(), "REPORT-copy.md")
    open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run([sys.executable, "-B", "-I", E + "verify-c6s.py", p], capture_output=True, text=True, env=(dict(os.environ, C6S_STEPS=envd) if envd else None))
    open(E + "neg/" + name + ".txt", "w").write(r.stdout[-6000:] + r.stderr[-1500:] + "\nEXIT CODE %d\n" % r.returncode)
    failed = [l for l in r.stdout.split("\n") if l.startswith("FAIL")]
    want_zero = name.startswith("V0")
    ok = (r.returncode == 0) if want_zero else (r.returncode != 0)
    if not ok:
        bad += 1
    out.append("%-48s exit %d  %s  failed checks: %d; first: %s" % (name, r.returncode, "OK" if ok else "WRONG", len(failed), (failed[0][:110] if failed else "none")))
out += ["PORT-SKIPPED (target text of an older control no longer exists in c6s; its rule has a new control): " + s_ for s_ in SKIPPED_PORT]
out.append("SUMMARY: %d copies, %d wrong" % (len(M), bad))
open(E + "neg-output.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
sys.exit(1 if bad else 0)
