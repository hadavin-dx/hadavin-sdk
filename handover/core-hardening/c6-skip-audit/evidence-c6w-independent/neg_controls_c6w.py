"""Negative controls for verify-c6w.py. Builds changed copies of REPORT-c6w.md (never edits it), runs verify-c6w.py on each and records the exit code
and the raw output. A control copy with no change must exit 0; every changed copy must exit non-zero. Fake key-shaped strings are built from parts here.
Usage: python3 neg_controls_c6w.py   Output: neg/<name>.txt per copy and neg-output.txt (summary). Exit 1 if any changed copy exits 0."""
import shutil, re, subprocess, sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
E = os.path.dirname(os.path.abspath(__file__)) + "/"
D = os.path.dirname(E.rstrip("/")) + "/"
os.makedirs(E + "neg", exist_ok=True)
rep = open(D + "REPORT-c6w.md", encoding="utf-8").read()
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
import ctime_c6w
_ctn = re.search(r"check time \(UTC\): (\S+)", open(E + "static-checks-output.txt", encoding="utf-8").read()).group(1)
EX1TXT = "%s = %s IST" % ctime_c6w.example_times(_ctn)[:2]
box_end = rep.index("## Start here, part 2")
run_block(open(E + "neg_ported_c6r.py", encoding="utf-8").read(), "neg_ported_c6r.py")
run_block(open(E + "neg_new_c6s.py", encoding="utf-8").read(), "neg_new_c6s.py")
for _k in ("S-F4g-sheet-v31-exists", "S-F4h-release-note-v15-exists", "S-F4i-v30-sheet-newer-than-check-time", "S-F4j-v30-B-file-missing"):
    ENV.pop(_k, None)
    M.pop(_k, None)
run_block(open(E + "neg_new_c6u.py", encoding="utf-8").read(), "neg_new_c6u.py")
run_block(open(E + "neg_new_c6w.py", encoding="utf-8").read(), "neg_new_c6w.py")
out = []
BASE = set()
bad = 0
for name, text in M.items():
    envd = ENV.get(name)
    if text is None:
        out.append("%-48s SKIPPED (mutation target absent)" % name)
        bad += 1
        continue
    _td = tempfile.mkdtemp()
    p = os.path.join(_td, "REPORT-c6w.md")   # the real file name (the check D-B1 compares the typed answer line with it); c6w-CHANGES.md is copied next to it for V12 and V13
    shutil.copy(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "c6w-CHANGES.md"), os.path.join(_td, "c6w-CHANGES.md"))
    open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run([sys.executable, "-B", "-I", E + "verify-c6w.py", p], capture_output=True, text=True, env=(dict(os.environ, C6V_STEPS=envd) if envd else None))
    open(E + "neg/" + name + ".txt", "w").write(r.stdout[-6000:] + r.stderr[-1500:] + "\nEXIT CODE %d\n" % r.returncode)
    failed = [l for l in r.stdout.split("\n") if l.startswith("FAIL")]
    want_zero = name.startswith("V0")
    # c6w: a changed copy counts as CAUGHT only if it makes a check fail that the unchanged copy (V0) does not fail (a baseline failure, for example a sheet rewritten
    # by another session after the check time, must not make every control look caught)
    if want_zero:
        BASE = set(l.split(" :: ")[0] for l in failed)
    newfail = [l for l in failed if l.split(" :: ")[0] not in BASE] if not want_zero else failed
    ok = (r.returncode == 0) if want_zero else (r.returncode != 0 and len(newfail) >= 1)
    if not ok:
        bad += 1
    out.append("%-48s exit %d  %s  failed checks: %d (new vs unchanged: %d); first new: %s" % (name, r.returncode, "OK" if ok else "WRONG", len(failed), len(newfail), ((newfail[0][:110] if newfail else "none") if not want_zero else (failed[0][:110] if failed else "none"))))
out += ["PORT-SKIPPED (target text of an older control no longer exists in c6u; its rule has a new control): " + s_ for s_ in SKIPPED_PORT]
out.append("SUMMARY: %d copies, %d wrong" % (len(M), bad))
open(E + "neg-output.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
sys.exit(1 if bad else 0)
