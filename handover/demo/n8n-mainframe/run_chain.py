"""Runs the Design A tests ONE PER RUN (fresh work folder, fresh n8n, fresh Postgres container each) and copies the raw outputs out.
  python run_chain.py --tests "T8 T13 K1 K2 K3B K3 K4 K5 T10 T11" --reps 8 --out OUTDIR --work-root WORKROOT --node-dir NODEDIR --node-modules DIR_WITH_NPM_CI_OUTPUT
Environment it needs (set before calling): N8N_HARNESS_DIR (harness folder of the public repo), DN1_DESK_REPO (desk checkout), and python/node on PATH.
No result is interpreted here; OUTDIR/<test>/ gets mf_result_<test>.json, driver.out and the stand-in logs. Run folders are removed after each test (they hold node_modules)."""
import argparse, os, shutil, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--tests", required=True); ap.add_argument("--reps", default="8"); ap.add_argument("--lease", default="20")
ap.add_argument("--out", required=True); ap.add_argument("--work-root", required=True); ap.add_argument("--node-dir", required=True); ap.add_argument("--node-modules", required=True, help="folder holding node_modules, package.json, package-lock.json from npm ci")
ap.add_argument("--tag", default=os.environ.get("RUN_ID") or "r"); ap.add_argument("--min-idle", default="80")
a = ap.parse_args()
os.environ["MF_REPS"] = a.reps; os.environ["MF_LEASE"] = a.lease
os.makedirs(a.out, exist_ok=True); os.makedirs(a.work_root, exist_ok=True)
def now(): return time.strftime("%H:%M:%SZ", time.gmtime())
for t in a.tests.split():
    name = "%s-%s-%d" % (a.tag, t, int(time.time())); w = os.path.join(a.work_root, name)
    os.makedirs(w)
    for f in ("package.json", "package-lock.json"): shutil.copy(os.path.join(a.node_modules, f), w)
    shutil.copytree(os.path.join(a.node_modules, "node_modules"), os.path.join(w, "node_modules"), symlinks=True)
    print("%s start %s" % (name, now()), flush=True)
    o = os.path.join(a.out, name); os.makedirs(o)
    with open(os.path.join(o, "driver.out"), "w") as lg:
        rc = subprocess.run([sys.executable, os.path.join(HERE, "run_mf.py"), "--work-dir", w, "--node-dir", a.node_dir, "--min-idle", a.min_idle, "--skip-args", t], stdout=lg, stderr=subprocess.STDOUT).returncode
    for pat in ("mf_result_", "master_dn1.out", "n8n2.log", "run_manifest.json"):
        for f in os.listdir(w):
            if f.startswith(pat) or f == pat: shutil.copy(os.path.join(w, f), o)
    d = os.path.join(w, "dn1")
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.endswith((".log", ".jsonl", ".conn")): shutil.copy(os.path.join(d, f), o)
    shutil.rmtree(w, ignore_errors=True)
    print("%s end %s rc %d" % (name, now(), rc), flush=True)
