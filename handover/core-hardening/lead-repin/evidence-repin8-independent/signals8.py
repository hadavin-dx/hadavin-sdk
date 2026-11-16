import subprocess, os, signal, time, glob, shutil
for shell in ("dash","bash"):
  for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
    for delay in (0.4, 1.2, 2.5):
        d="/tmp/hd8i/sig2"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        env=dict(os.environ, TMPDIR=d)
        p=subprocess.Popen([shell,"/tmp/hd8i/v8.sh","/tmp/hd8i/take"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env,start_new_session=True,preexec_fn=None)
        time.sleep(delay)
        if p.poll() is None: os.kill(p.pid, sig)   # signal only the shell, as kill <pid> would
        try: out,_=p.communicate(timeout=30)
        except subprocess.TimeoutExpired: p.kill(); out,_=p.communicate(); 
        time.sleep(0.5)
        left=glob.glob(d+"/lead-repin.*")
        kids=subprocess.run(["pgrep","-f","/tmp/hd8i/v8.sh|lead-repin"],capture_output=True,text=True).stdout.split()
        print(f"{shell} {signal.Signals(sig).name} delay={delay} exit={p.returncode} workdir_left={len(left)} files_left={sum(len(os.listdir(x)) for x in left)} stray_procs={len(kids)} out_lines={len(out.splitlines())}",flush=True)
