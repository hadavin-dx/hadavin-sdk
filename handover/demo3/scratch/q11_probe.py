import os, subprocess, sys, time
def test_probe():
    code = "import time; time.sleep(30)"
    p = subprocess.Popen([sys.executable, "-c", code, "lead_desk.server", "x"])
    time.sleep(0.5)
    out=[]
    out.append("COLUMNS=%r LINES=%r TERM=%r" % (os.environ.get("COLUMNS"), os.environ.get("LINES"), os.environ.get("TERM")))
    out.append("isatty stdin/out/err: %s %s %s" % (os.isatty(0), os.isatty(1), os.isatty(2)))
    out.append("ps args=      : %r" % subprocess.run(["ps","-p",str(p.pid),"-o","args="],capture_output=True,text=True).stdout)
    out.append("ps -ww args=  : %r" % subprocess.run(["ps","-ww","-p",str(p.pid),"-o","args="],capture_output=True,text=True).stdout)
    out.append("cmdline      : %r" % open("/proc/%d/cmdline"%p.pid).read().replace("\0"," "))
    out.append("len(cmdline) : %d" % len(open("/proc/%d/cmdline"%p.pid).read()))
    out.append("executable   : %s" % sys.executable)
    out.append("pgid/sid/ppid: %s %s %s" % (os.getpgid(0), os.getsid(0), os.getppid()))
    out.append("parent cmd   : %r" % open("/proc/%d/cmdline"%os.getppid()).read().replace("\0"," ")[:200])
    p.kill(); p.wait()
    open(os.environ["PROBE_OUT"],"a").write("\n".join(out)+"\n---\n")
