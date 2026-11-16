"""Shows that the first-copy-only edits of repeated card numbers pass the c6w checks (exit 0, no failed check) on the c6w text. Reads REPORT-c6w.md, never edits it; copies go to a temp folder.
Usage: python3 -B -I prove_on_c6w.py > prove-on-c6w-output.txt"""
import os, subprocess, sys, tempfile, shutil
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
W = D + "evidence-c6w/"
rep = open(D + "REPORT-c6w.md", encoding="utf-8").read()
env = dict(os.environ, C6V_STEPS=W + "steps-frozen")
env.pop("C6V_STEPS_LIVE", None)
def run(name, text):
    td = tempfile.mkdtemp()
    p = td + "/REPORT-c6w.md"
    open(p, "w", encoding="utf-8").write(text)
    shutil.copy(D + "c6w-CHANGES.md", td + "/c6w-CHANGES.md")
    r = subprocess.run([sys.executable, "-B", "-I", W + "verify-c6w.py", p], capture_output=True, text=True, env=env)
    f = [l[:90] for l in r.stdout.split("\n") if l.startswith("FAIL")]
    print("%-34s exit %d  failed checks: %d  %s" % (name, r.returncode, len(f), f[:1]))
    return r.returncode, len(f)
base = run("unchanged c6w text", rep)
n0 = base[1]
rows = []
for a, b, tag in (("90 words", "91 words", "card-words-90-first"), ("about 36 s", "about 37 s", "card-seconds-36-first"), ("budget 40 s", "budget 45 s", "budget-40-first"), ("87 words", "88 words", "card-words-87-first")):
    i = rep.find(a)
    rows.append((tag, run(tag, rep[:i] + b + rep[i + len(a):]) if i >= 0 else None))
passed = [t for t, r in rows if r and r[1] <= n0]
print("PROOF: %d of %d first-copy edits make no new check fail on the c6w text (so c6w would have called them fine): %s" % (len(passed), len(rows), passed))
