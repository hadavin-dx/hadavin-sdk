"""EV7T mutant runner. usage: python mut3.py <copydir> <outfile> <setfile.py> [ids]. One runner per copy.
setfile defines muts=[(id, file, old, new, [pytest args])]. Each file restored from tree-a and compared byte for byte."""
import filecmp, os, shutil, subprocess, sys
R="/home/user/build/rr6/"; O=R+"out/EV7T/"; M=O+sys.argv[1]+"/"; S=O+"tree-a/"; TMP=O+"tmp-mut-"+sys.argv[1]; os.makedirs(TMP,exist_ok=True)
ns={}; exec(open(sys.argv[3]).read(),ns); muts=ns["muts"]
only=sys.argv[4:]
out=open(O+sys.argv[2],"a")
for mid,f,old,new,args in muts:
    if only and mid not in only: continue
    p=M+f; s=open(p,encoding="utf-8",newline="").read()
    if s.count(old)!=1:
        out.write(f"{mid}\t{f}\tNOT-APPLIED count={s.count(old)}\n"); out.flush(); continue
    open(p,"w",encoding="utf-8",newline="").write(s.replace(old,new))
    try:
        env=dict(os.environ,PYTHONPATH=M+"src",PYTHONDONTWRITEBYTECODE="1",TMPDIR=TMP,PATH=R+"bin:"+os.environ["PATH"],GITLEAKS_BIN=R+"bin/gitleaks",DPLD_REQUIRE_SCAN="1",DPLD_REQUIRE_DEMO="1")
        cmd=["unshare","-n","python",R+"src-v6/drivers/lo_up-q4g.py",R+"venv-br/bin/python","-m","pytest","-q","-p","no:cacheprovider","-x",*args]
        try:
            r=subprocess.run(cmd,cwd=M,env=env,capture_output=True,text=True,timeout=900)
            res="KILLED" if r.returncode==1 else ("SURVIVED" if r.returncode==0 else "ERR rc=%d"%r.returncode)
            tail=r.stdout.strip().splitlines()[-1:]
            open(O+f"mutraw-{sys.argv[2]}-{mid}.txt","w").write(r.stdout[-2000:])
        except subprocess.TimeoutExpired:
            res="TIMEOUT"; tail=[]
        out.write(f"{mid}\t{f}\t{' '.join(args)}\t{res}\t{tail}\n"); out.flush()
    finally:
        shutil.copyfile(S+f,p); same=filecmp.cmp(S+f,p,shallow=False)
        out.write(f"{mid}\trestored-byte-equal={same}\n"); out.flush()
