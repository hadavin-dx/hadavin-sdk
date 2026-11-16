# v9 signal evidence: HUP INT TERM QUIT sent to the shell only, no nohup, dash and bash. usage: python3 -I signals9.py SCRIPT TAKE_DIR
import subprocess, os, signal, time, glob, shutil, sys, hashlib
script, take = sys.argv[1], sys.argv[2]
print("SCRIPT-SHA256", hashlib.sha256(open(script,"rb").read()).hexdigest(), flush=True)
for shell in ("dash","bash"):
  for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
    for delay in (0.4, 1.2, 2.5):
        d="/tmp/hd9/sg/w"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        env=dict(os.environ, TMPDIR=d)
        p=subprocess.Popen([shell,script,take],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        time.sleep(delay)
        if p.poll() is None: os.kill(p.pid, sig)
        try: out,_=p.communicate(timeout=30)
        except subprocess.TimeoutExpired: p.kill(); out,_=p.communicate()
        time.sleep(3)
        left=glob.glob(d+"/lead-repin.*")
        kids=subprocess.run(["ps","-o","pid,stat,comm","-g",str(p.pid),"--no-headers"],capture_output=True,text=True).stdout.splitlines()
        print(f"{shell} {signal.Signals(sig).name} delay={delay} exit={p.returncode} workdir_left={len(left)} stray_procs={len(kids)} {";".join(k.split()[1]+":"+k.split()[2] for k in kids)} out_lines={len(out.splitlines())}",flush=True)
