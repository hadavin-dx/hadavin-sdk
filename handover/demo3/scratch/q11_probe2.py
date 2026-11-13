import os, subprocess, sys, time
def test_probe2():
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", "lead_desk.server", "x"])
    time.sleep(0.5)
    o=[]
    def ps(label, **kw):
        r=subprocess.run(["ps","-p",str(p.pid),"-o","args="],capture_output=True,text=True,**kw)
        o.append("%-34s len=%d" % (label, len(r.stdout.rstrip("\n"))))
    ps("default")
    ps("env without COLUMNS/LINES", env={k:v for k,v in os.environ.items() if k not in("COLUMNS","LINES")})
    ps("env={}", env={})
    ps("env COLUMNS=500", env={**os.environ,"COLUMNS":"500"})
    ps("stdin=DEVNULL", stdin=subprocess.DEVNULL)
    o.append("fd0=%s fd1=%s fd2=%s" % tuple(os.readlink("/proc/self/fd/%d"%i) for i in range(3)))
    o.append("env keys with COL/LIN: %s" % [k for k in os.environ if k in ("COLUMNS","LINES")])
    p.kill(); p.wait()
    open(os.environ["PROBE_OUT"],"w").write("\n".join(o)+"\n")
