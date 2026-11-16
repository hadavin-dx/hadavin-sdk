import sys,shutil,os,subprocess
SRC="/home/user/hadavin-sdk/handover"
# id, file, line, old, new
M=[
("M2","check_flows.py",1213,'fname_ in OPTS["accept_nosave"] and trig_types','(fname_ in OPTS["accept_nosave"] or OPTS["accept_nosave"]) and trig_types'),
("M3","check_flows.py",1213,'fname_ in OPTS["accept_nosave"] and trig_types','(fname_ in OPTS["accept_nosave"] or (OPTS["accept_nosave"] and fname_.startswith("mf-"))) and trig_types'),
("M7","check_flows.py",1492,'if s.get("saveManualExecutions") is not want_manual:','if False and s.get("saveManualExecutions") is not want_manual:'),
("M10","take_check.sh",64,'|^WARN accept-no-save',''),
("M12","take_check.sh",86,'exit status $RC.','exit status 0.'),
("TCMISS","run_all.sh",76,'TCMISS=""',': #'),
("N01","check_flows.py",1835,'return 1 if FAILS else 0','return 0'),
("N02","check_flows.py",1835,'return 1 if FAILS else 0','return 1 if len(FAILS) > 1 else 0'),
("N03","check_flows.py",1198,'len(nodes) != expect["nodes"]','len(nodes) < expect["nodes"]'),
("N04","check_flows.py",1200,'ncon != expect["connections"]','ncon < expect["connections"]'),
("N05","check_flows.py",1489,'s.get(k) != want','s.get(k) == want'),
("N06","check_flows.py",1492,'is not want_manual','is want_manual'),
("N07","check_flows.py",1741,'if have != sorted(dfiles):','if False:'),
("N08","check_flows.py",1210,'is False','is True'),
("N09","check_flows.py",1209,'== "none"','== "all"'),
("N10","check_flows.py",158,'FAILS.append(f"{where}: {msg}")','pass'),
("N11","check_flows.py",None,'if not blocks or not all(','if not blocks and not all('),
("N12","check_flows.py",None,'if miss and not absent:','if miss and absent:'),
("N13","check_flows.py",None,'        if absent:\n            SQL_DONE["tbl_warn"]','        if absent and False:\n            SQL_DONE["tbl_warn"]'),
("N14","check_flows.py",231,'if SQL_DONE["checked"] == 0:','if SQL_DONE["checked"] != 0:'),
("N15","check_flows.py",None,'    if dups:\n','    if False:\n'),
("N16","check_flows.py",None,'elif w not in SQL_WORDS and nxt != "(":','elif w not in SQL_WORDS and nxt == "(":'),
]
def build(mid):
    d=f"/tmp/e7m/{mid}"
    shutil.rmtree(d,ignore_errors=True)
    os.makedirs(d+"/flows-audit")
    os.symlink(SRC+"/demo",d+"/demo")
    shutil.copytree(SRC+"/flows-audit/patches",d+"/flows-audit/patches")
    shutil.copytree(SRC+"/flows-audit/flow-check",d+"/flows-audit/flow-check",ignore=shutil.ignore_patterns("raw*","selftest-output*","evidence*","review*","m1","__pycache__"))
    return d
if __name__=="__main__":
    out=[]
    for mid,f,ln,old,new in M:
        d=build(mid); p=f"{d}/flows-audit/flow-check/{f}"
        t=open(p).read(); 
        if mid=="TCMISS": pass
        c=t.count(old)
        if ln:
            L=t.split("\n"); 
            if old not in L[ln-1]:
                # find actual line
                idx=[i+1 for i,l in enumerate(L) if old in l]; print(mid,"line mismatch, actual",idx); 
                if len(idx)!=1: sys.exit("bad "+mid)
                ln=idx[0]
            L[ln-1]=L[ln-1].replace(old,new,1); t2="\n".join(L)
        else:
            assert c==1,(mid,c); ln=t[:t.index(old)].count("\n")+1; t2=t.replace(old,new,1)
        open(p,"w").write(t2)
        print(mid,f,"line",ln,"|",old.strip()[:50],"->",new.strip()[:60])
