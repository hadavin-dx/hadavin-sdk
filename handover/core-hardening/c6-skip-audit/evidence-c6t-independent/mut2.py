import re,subprocess,os
W=os.path.dirname(os.path.abspath(__file__)); ev=W+"/handover/core-hardening/c6-skip-audit/evidence-c6t"
src=open(W+"/REPORT-c6t.orig.md",encoding="utf-8").read()
def run(name,t):
    assert t!=src,name
    open(W+"/mut.md","w",encoding="utf-8").write(t)
    r=subprocess.run(["python3","-B","-I","verify-c6t.py",W+"/mut.md"],cwd=ev,capture_output=True,text=True)
    print(name,"|","CAUGHT" if r.returncode else "MISSED","|",len(re.findall(r"^FAIL",r.stdout,re.M)))
run("29 box word count 2495 -> 2496 (first)",src.replace("2495","2496",1))
run("29b box word count 2495 -> 2496 (all)",src.replace("2495","2496"))
run("40 'Of the 94 rows' -> 95 (all)",src.replace("Of the 94 rows","Of the 95 rows"))
run("41 R-number R447 added to box",src.replace("WORDS YOU NEED (the short list;","WORDS YOU NEED R447 (the short list;",1))
