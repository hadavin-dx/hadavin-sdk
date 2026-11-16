"""Run ONE command with a timeout, save its raw output, append one JSON line to the stage log.
usage: step.py WORKDIR STAGE NAME TIMEOUT_SECONDS [--cwd DIR] [--env K=V ...] -- cmd...
Never judges: records the command, the exit code (124 = timed out here), the seconds and the raw file."""
import json, os, signal, subprocess, sys, time

def main():
    a = sys.argv[1:]
    w, stage, name, tmo = a[0], a[1], a[2], int(a[3]); a = a[4:]
    cwd, env = None, dict(os.environ)
    while a and a[0] != "--":
        if a[0] == "--cwd": cwd = a[1]; a = a[2:]
        elif a[0] == "--env": k, v = a[1].split("=", 1); env[k] = v; a = a[2:]
        else: sys.exit("step.py: bad option " + a[0])
    cmd = a[1:]
    raw_dir = os.path.join(w, "raw"); os.makedirs(raw_dir, exist_ok=True)
    raw = os.path.join(raw_dir, f"{stage}-{name}.txt")
    t0 = time.time(); timed_out = False
    with open(raw, "w") as f:
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        try: rc = p.wait(tmo)
        except subprocess.TimeoutExpired:
            timed_out = True
            try: os.killpg(p.pid, signal.SIGKILL)  # only the group this script started
            except ProcessLookupError: pass
            p.wait(); rc = 124
    rec = {"stage": int(stage), "name": name, "cmd": " ".join(cmd), "cwd": cwd, "exit": rc, "timed_out": timed_out,
           "seconds": round(time.time() - t0, 1), "raw": raw, "timeout_limit": tmo}
    with open(os.path.join(w, "stages.jsonl"), "a") as f: f.write(json.dumps(rec) + "\n")
    print(f"[stage {stage}] {name}: exit={rc}{' (TIMED OUT)' if timed_out else ''} {rec['seconds']}s -> {raw}", flush=True)

main()
