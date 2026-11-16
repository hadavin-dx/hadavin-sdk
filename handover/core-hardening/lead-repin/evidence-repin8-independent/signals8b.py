import subprocess, os, signal, time, shutil
for shell in ("dash","bash"):
  for sig in (signal.SIGHUP, signal.SIGTERM):
    for delay in (0.4, 1.5):
        d="/tmp/hd8i/sig3"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        p=subprocess.Popen([shell,"/tmp/hd8i/v8.sh","/tmp/hd8i/take"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=dict(os.environ,TMPDIR=d),start_new_session=True)
        time.sleep(delay); os.kill(p.pid, sig); p.wait(); 
        a=subprocess.run(["ps","-o","pid,stat,etime,args","-g",str(p.pid)],capture_output=True,text=True).stdout.strip().splitlines()[1:]
        time.sleep(3)
        b=subprocess.run(["ps","-o","pid,stat,args","-g",str(p.pid)],capture_output=True,text=True).stdout.strip().splitlines()[1:]
        print(shell,signal.Signals(sig).name,delay,"exit",p.returncode,"after0s:",[x.split(None,3)[-1][:50] for x in a],"after3s:",len(b),"workdirs",len(os.listdir(d)),flush=True)
        for x in b: os.system("kill -9 %s 2>/dev/null" % x.split()[0])
