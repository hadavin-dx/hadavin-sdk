"""R7U-MUT wide re-run of a survivor: usage wide.py <treecopy> <tmpdir> <result.tsv> <timeout_s> <id...>. Restore + sha256 after each."""
import hashlib, os, subprocess, sys, time
sys.path.insert(0, "/home/user/build/rr6/out/R7U-MUT")
from mutants import M
R = "/home/user/build/rr6/"; O = R + "out/R7U-MUT/"
cp, tmp, res, tmo = O + sys.argv[1] + "/", O + sys.argv[2], O + sys.argv[3], int(sys.argv[4]); ids = sys.argv[5:]
os.makedirs(tmp, exist_ok=True)
T = lambda n: "tests/" + n + ".py"
ZSET = [T("test_r7u_c_findings"), T("test_r7t_findings"), T("test_r7_fake_bad_requests"), T("test_bind_refusals"), T("test_codeant_fakes"), T("test_file_call_guard")]
RSET = [T("test_real_check_dry"), T("test_r7t_findings"), T("test_r7u_a_findings"), T("test_r7u_b_findings"), T("test_r7u_c_findings"), T("test_file_call_guard")]
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
out = open(res, "a")
for mid, kind, f, old, new, exp, tests in M:
    if mid not in ids: continue
    p = cp + f; orig = open(p, "rb").read(); h0 = sha(p); s = orig.decode()
    if s.count(old) != 1:
        out.write(f"{mid}\tNOT-APPLIED\n"); continue
    env = dict(os.environ, PYTHONPATH=cp + "src", PYTHONDONTWRITEBYTECODE="1", TMPDIR=tmp, PATH=R + "bin:" + os.environ["PATH"],
               GITLEAKS_BIN=R + "bin/gitleaks", DPLD_REQUIRE_SCAN="1", DPLD_REQUIRE_DEMO="1")
    cmd = ["unshare", "-n", "python", R + "src-v6/drivers/lo_up-q4g.py", R + "venv-br/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfs", "-x"] + (ZSET if mid.startswith("Z") else RSET)
    t = time.time()
    try:
        open(p, "wb").write(s.replace(old, new).encode())
        try:
            r = subprocess.run(cmd, cwd=cp, env=env, capture_output=True, text=True, timeout=tmo)
            fails = [l for l in r.stdout.splitlines() if l.startswith("FAILED")][:2]
            v = ("KILLED" if r.returncode == 1 else "SURVIVED-FULL-WIDE-SET" if r.returncode == 0 else "ERR rc=%d" % r.returncode)
            tail = r.stdout.strip().splitlines()[-1:]
        except subprocess.TimeoutExpired as e:
            v = "SURVIVED-UNTIL-TIMEOUT"; fails = []; tail = [((e.stdout or b"")[-200:]).decode(errors="replace") if isinstance(e.stdout, bytes) else str(e.stdout)[-200:]]
    finally:
        open(p, "wb").write(orig)
    eq = sha(p) == h0
    out.write(f"{mid}\t{v}\t{int(time.time()-t)}s\t{fails}\t{tail}\trestored={eq}\n"); out.flush()
    if not eq: sys.exit("restore failed")
