import subprocess, sys, os, shutil
ST=sys.argv[1]; PY="/tmp/work/civenv/bin/python"
src=open("/tmp/work/rv30-main/m/mut30.py").read()
head=src.split("sel=sys.argv")[0]
ns={}
exec(head.replace('WIDE=os.environ["WIDEFILES"].split()','WIDE=[]').replace('ST="/tmp/work/rv30-main/stack"','ST0=1'),ns)
M=ns["M"]
for name,f,old,new in M:
    p=os.path.join(ST,f); orig=open(p).read()
    if orig.count(old)!=1: print(name,"PATTERN COUNT",orig.count(old),flush=True); continue
    open(p,"w").write(orig.replace(old,new))
    try:
        r=subprocess.run([PY,"-m","pytest","-q","-p","no:cacheprovider","tests/test_sonar_p2_gaps.py"],cwd=ST,capture_output=True,text=True,timeout=300)
        fails=sorted({l.split("::")[1].split(" ")[0].split("[")[0] for l in r.stdout.splitlines() if l.startswith("FAILED")})
        print(name,"KILLED (%d: %s)"%(len(fails),",".join(fails)) if r.returncode else "SURVIVED",flush=True)
    finally: open(p,"w").write(orig)
