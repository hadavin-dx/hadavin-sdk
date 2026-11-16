# Signal check with a python launcher (INT and QUIT cannot be sent reliably from a shell: a background job ignores them).
# For each shell (dash, bash), mode (main, mask) and signal: start the script, wait until it is busy, send the signal,
# then check: exit code, folders left in a private TMPDIR, programs left (the recorded pid of the slow fake program).
import os, subprocess, sys, time, signal, tempfile, shutil
script = sys.argv[1]
SIG = {"INT": (signal.SIGINT, 130), "TERM": (signal.SIGTERM, 143), "HUP": (signal.SIGHUP, 129), "QUIT": (signal.SIGQUIT, 131)}
def alive(pid):
    try:
        st = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[0]
    except OSError:
        return False
    return st != "Z"
bad = 0
for sh in ("dash", "bash"):
    for mode in ("main", "mask"):
        for name, (sg, want) in SIG.items():
            base = tempfile.mkdtemp(prefix="sigchk-")
            tmp = os.path.join(base, "tmp"); fake = os.path.join(base, "fake"); os.mkdir(tmp); os.mkdir(fake)
            tf = os.path.join(base, "take"); os.mkdir(tf); os.mkdir(os.path.join(tf, "scripts"))
            open(os.path.join(tf, "scripts", "run_real_check_n8n.py"), "w").write("# made-up\nx = 1\n")
            pidf = os.path.join(fake, "p.pid")
            open(os.path.join(fake, "git"), "w").write(f"#!/bin/sh\necho $$ > {pidf}\nexec sleep 33\n"); os.chmod(os.path.join(fake, "git"), 0o755)
            env = dict(os.environ, TMPDIR=tmp, LEAD_REPIN_NO_META="1")
            if mode == "main":
                env["PATH"] = fake + ":" + env["PATH"]
                p = subprocess.Popen([sh, script, tf], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                p = subprocess.Popen([sh, script, "--mask"], env=env, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            t0 = time.time()
            if mode == "main":
                while time.time() - t0 < 40 and not os.path.exists(pidf): time.sleep(0.2)
            else:
                time.sleep(4)   # past the start check; the script now waits for input
            gp = int(open(pidf).read().strip()) if os.path.exists(pidf) and open(pidf).read().strip() else 0
            ts = time.time(); p.send_signal(sg)
            try: rc = p.wait(timeout=20)
            except subprocess.TimeoutExpired: p.kill(); rc = "TIMEOUT"
            took = time.time() - ts
            time.sleep(1)
            left = len([x for x in os.listdir(tmp) if x.startswith("lead-repin.")])
            stray = 1 if (gp and alive(gp)) else 0
            if stray: os.kill(gp, 9)
            ok = (rc == want and left == 0 and stray == 0)
            bad += 0 if ok else 1
            print(f"{sh:5} {mode:5} {name:5} exit={rc} wanted={want} folders_left={left} stray_programs={stray} seconds_to_end={took:.1f} {'OK' if ok else 'BAD'}")
            shutil.rmtree(base, ignore_errors=True)
print("BAD rows:", bad)
