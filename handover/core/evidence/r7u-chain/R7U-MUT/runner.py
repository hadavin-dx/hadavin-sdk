"""R7U-MUT runner: usage runner.py <treecopy> <tmpdir> <result.tsv> <id...>. One mutant at a time; restore from tree-R7U and sha256-verify after every mutant."""
import hashlib, os, subprocess, sys, time
sys.path.insert(0, "/home/user/build/rr6/out/R7U-MUT")
from mutants import M
from kmap import K
R = "/home/user/build/rr6/"; O = R + "out/R7U-MUT/"
cp, tmp, res = O + sys.argv[1] + "/", O + sys.argv[2], O + sys.argv[3]; ids = sys.argv[4:]
os.makedirs(tmp, exist_ok=True)
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def run(tests, wide=False):
    env = dict(os.environ, PYTHONPATH=cp + "src", PYTHONDONTWRITEBYTECODE="1", TMPDIR=tmp, PATH=R + "bin:" + os.environ["PATH"],
               GITLEAKS_BIN=R + "bin/gitleaks", DPLD_REQUIRE_SCAN="1", DPLD_REQUIRE_DEMO="1")
    cmd = ["unshare", "-n", "python", R + "src-v6/drivers/lo_up-q4g.py", R + "venv-br/bin/python", "-m", "pytest", "-q",
           "-p", "no:cacheprovider", "-rfs", "-x"] + tests
    t = time.time()
    try:
        r = subprocess.run(cmd, cwd=cp, env=env, capture_output=True, text=True, timeout=1500)
        fails = [l for l in r.stdout.splitlines() if l.startswith("FAILED")][:2]
        return ("KILLED" if r.returncode == 1 else "SURVIVED" if r.returncode == 0 else "ERR rc=%d" % r.returncode), fails, int(time.time() - t), r.stdout[-1500:]
    except subprocess.TimeoutExpired:
        return "TIMEOUT", [], int(time.time() - t), ""
out = open(res, "a")
for mid, kind, f, old, new, exp, tests in M:
    if mid not in ids: continue
    p = cp + f; orig = open(p, "rb").read(); h0 = sha(p); s = orig.decode()
    if s.count(old) != 1:
        out.write(f"{mid}\t{f}\tNOT-APPLIED count={s.count(old)}\n"); out.flush(); continue
    line = s[:s.index(old)].count("\n") + 1
    try:
        open(p, "wb").write(s.replace(old, new).encode())
        files, kx = K[mid]
        v, fails, sec, tail = run(files + ["-k", kx])
        wide = ""
    finally:
        open(p, "wb").write(orig)
    eq = sha(p) == h0
    open(O + f"raw-{mid}.txt", "w").write(tail)
    out.write(f"{mid}\t{f}:{line}\t{v}\t{sec}s\t{fails}\trestored={eq}\twide={wide}\n"); out.flush()
    if not eq: sys.exit("restore failed " + mid)
