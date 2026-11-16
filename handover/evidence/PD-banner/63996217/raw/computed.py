import sys
sys.path.insert(0,'.');sys.path.insert(0,'tests')
from pathlib import Path
import banner_mutants as b, test_banner_mutant_table as t
from tools.mutation_runner import run_mutants
rows=[m for m in b.M if m.name.split(" ",1)[0] in t.COMPUTED_EXPECT]
fl={}
res=run_mutants(Path('.').resolve(),b.M,[b.T_MB,b.T_G],extra_dirs=("tests","tools","templates","demos"),only=[m.name for m in rows],first_lines=fl)
resd={n:(v,g) for n,v,_,g in res}
for m in rows:
    line=fl.get(m.name,"")
    print(m.name.split(" ",1)[0], resd.get(m.name), "expect_in_first_line=",m.expect in line, "|", repr(m.expect[:50]), "| first:", line[:110].replace("\n"," "))
