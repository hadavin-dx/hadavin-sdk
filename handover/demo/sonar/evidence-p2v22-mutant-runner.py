import subprocess, sys, os, time
ST=sys.argv[1]; PY="/tmp/work/civenv/bin/python"
exec(open("/tmp/work/rv22-main/mut.py").read().split("sel=sys.argv")[0].split("M=[",1)[0].replace("ST=","_=").replace("PY=","_p="))
src=open("/tmp/work/rv22-main/mut.py").read()
M=eval("["+src.split("M=[",1)[1].split("\n]\n",1)[0]+"\n]")
want=("M01","M04","M06","M08","M09","M10","M26")
for name,f,old,new in M:
    if not name.startswith(want): continue
    p=os.path.join(ST,f); orig=open(p).read()
    if orig.count(old)!=1: print(name,"PATTERN COUNT",orig.count(old)); continue
    open(p,"w").write(orig.replace(old,new))
    try:
        r=subprocess.run([PY,"-u","-m","pytest","-q","-p","no:cacheprovider","tests/test_sonar_p2_gaps.py"],cwd=ST,capture_output=True,text=True)
        fails=[l.split("::")[1].split(" ")[0] for l in r.stdout.splitlines() if l.startswith("FAILED")]
        print(name,"KILLED" if r.returncode else "SURVIVED","|",len(fails),"failing:",", ".join(sorted(set(fails)))[:160],flush=True)
    finally: open(p,"w").write(orig)
