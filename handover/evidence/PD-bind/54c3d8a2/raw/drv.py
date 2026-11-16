import sys,re
sys.path.insert(0,'/home/user/build/wt/ER-pdbind12'); sys.path.insert(0,'/home/user/build/wt/ER-pdbind12/tests')
import bind_mutants as bm
from tools.mutation_runner import run_mutants
ids=open(sys.argv[1]).read().split()
only=[i+" " for i in ids]
fl={}
res=run_mutants(bm.ROOT,bm.M,[bm.T_BG,bm.T_NG,bm.T_SITES],extra_dirs=("tests","tools","demos","docs"),only=only,first_lines=fl)
exp={m.name:m for m in bm.M}
bad=0
for n,v,t,g in res:
    m=exp[n]; line=fl.get(n,""); has=m.expect in line
    if not has: bad+=1
    print(("OK " if (g and has) else "CHK"),v.name if hasattr(v,'name') else v,n[:60],"| expect-in-first-line=",has,"|",line[:110].replace("\n"," "))
print("rows",len(res),"good",sum(1 for r in res if r[3]),"expect-missing",bad)
