import hashlib, json, subprocess, sys, ast, os
T="/home/user/build/rr6/tree-T3"; R="/home/user/build/rr6"
muts={m[0].split()[0]:m for m in json.load(open(R+"/src-v6/drivers/mutants/muts2.json"))}
name=sys.argv[1]; m=muts[name]; path=f"{T}/{m[1]}"
orig=open(path).read(); h=hashlib.sha256(orig.encode()).hexdigest()
assert orig.count(m[2])==1, orig.count(m[2])
new=orig.replace(m[2],m[3],1)
print(name,"AST equal ignoring Pass:", ast.dump(ast.parse(orig))==ast.dump(ast.parse(new).__class__(body=[n for n in ast.parse(new).body])) if False else "see below")
class S(ast.NodeTransformer):
    def visit_Pass(self,n): return None
strip=lambda s: ast.dump(S().visit(ast.parse(s)))
print("AST identical after dropping Pass nodes:", strip(orig)==strip(new))
open(path,"w").write(new)
try:
    env=dict(os.environ,TMPDIR=T+"/.tmp-run",PYTHONPATH=T+"/src")
    r=subprocess.run([R+"/venv312/bin/python","-m","pytest","-q","-p","no:cacheprovider","-rfs"]+sys.argv[2:],cwd=T,env=env,capture_output=True,text=True)
    print(r.stdout[-1500:],r.stderr[-500:]); print("rc",r.returncode)
finally:
    open(path,"w").write(orig)
    assert hashlib.sha256(open(path,"rb").read()).hexdigest()==h; print("restored ok")
