"""Run one pytest selection N times in a row (one at a time). Raw file = the output of every FAILING run plus a
count line. Records one JSON line like step.py. Never judges.
usage: conc.py WORKDIR STAGE TREE PYTHON TESTNAME N PER_RUN_TIMEOUT"""
import json, os, subprocess, sys, time
w, stage, tree, py, test, n, tmo = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6]), int(sys.argv[7])
os.makedirs(os.path.join(w, "raw"), exist_ok=True)
raw = os.path.join(w, "raw", f"{stage}-conc-{test}.txt")
env = {k: v for k, v in os.environ.items() if not k.startswith("DESK_")}; env["PYTHONPATH"] = os.path.join(tree, "src")
cmd = [py, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider", "--no-header", "-k", test]
ok = bad = tout = 0; last = ""; t0 = time.time()
with open(raw, "w") as f:
    for i in range(1, n + 1):
        try:
            r = subprocess.run(cmd, cwd=tree, env=env, capture_output=True, text=True, timeout=tmo)
            out, rc = r.stdout + r.stderr, r.returncode
        except subprocess.TimeoutExpired as e:
            out, rc = "TIMEOUT after %ss\n" % tmo, 124; tout += 1
        last = out.strip().splitlines()[-1] if out.strip() else ""
        if rc == 0: ok += 1
        else:
            bad += 1; f.write(f"=== run {i} exit={rc}\n{out}\n")
    f.write(f"COUNTS {test}: exit0={ok} nonzero={bad} (of which timeout={tout}) of {n}; last run summary line: {last}\n")
rec = {"stage": int(stage), "name": f"conc-{test}", "cmd": " ".join(cmd) + f"   (x{n}, one after another)", "cwd": tree,
       "exit": 0 if bad == 0 else 1, "timed_out": tout > 0, "seconds": round(time.time() - t0, 1), "raw": raw,
       "timeout_limit": tmo, "note": f"exit0={ok} nonzero={bad} of {n}; {last}"}
open(os.path.join(w, "stages.jsonl"), "a").write(json.dumps(rec) + "\n")
print(f"[stage {stage}] conc {test}: exit0={ok} nonzero={bad} of {n} ({rec['seconds']}s) -> {raw}", flush=True)
