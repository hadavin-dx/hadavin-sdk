import harness as h, json, os, subprocess, shutil
from concurrent.futures import ThreadPoolExecutor
K=h.K; T=h.T; TMP=h.TMP; PY=h.PY; OUT=h.OUT
LO=h.RR+"/src-v6/drivers/lo_up-q4g.py"
kf=TMP+"/n8n.key"; open(kf,"w").write("onewordkey123\n")
open(TMP+"/wf.json","w").write('{"name":"wf-one","nodes":[],"connections":{}}'); open(TMP+"/"+K+".json","w").write('{"name":"wf-one","nodes":[],"connections":{}}')
cs=[]
def A(sc,args,env,label,pre,lo=False): cs.append((sc,"n8n-stub" if lo else "env-full",args,env,label,pre,lo))
N=["scripts/n8n_api.py"]
base={"N8N_API_KEY_FILE":kf,"N8N_URL":"http://127.0.0.1:5679","LEAD_DESK_PATH_ROOTS":TMP}
stub=[OUT+"/stub_n8n.py"]+N
for args in [["list"],["list",K],[K],["--"+K],["import",K],["import",TMP+"/"+K+".json"],["import",TMP+"/wf.json"],["import",TMP+"/wf.json",K],["activate",K],["deactivate",K],["activate","wf-one"],["activate","wf-one",K],["activate",K,K],["--",K],["import","--",K],["lis"+K],["import",TMP+"/"+K+"/x.json"],["import","/etc/"+K]]:
    A("n8n_api",args,dict(base),"STUB "+" ".join(args),stub,True)
for v,val in [("N8N_URL","http://127.0.0.1:5679/"+K),("N8N_URL","http://"+K+"@127.0.0.1:5679"),("N8N_URL","https://"+K+":x@example.invalid"),("N8N_URL","http://127.0.0.1:"+K),("N8N_URL",K),("N8N_API_KEY_FILE",TMP+"/"+K),("N8N_API_KEY_FILE",K)]:
    e=dict(base); e[v]=val; A("n8n_api",["list"],e,"STUB ENV "+v+"="+val.replace(K,"<K>").replace(TMP,"$TMP")[:40],stub,True)
# key content in key file with bad shape: key text inside the file
open(TMP+"/bad.key","w").write(K+" second\n"); e=dict(base); e["N8N_API_KEY_FILE"]=TMP+"/bad.key"; A("n8n_api",["list"],e,"STUB key FILE CONTENT has space",stub,True)
open(TMP+"/bad2.key","w").write(K+"\nsecond\n"); e=dict(base); e["N8N_API_KEY_FILE"]=TMP+"/bad2.key"; A("n8n_api",["list"],e,"STUB key FILE CONTENT two lines",stub,True)
# server with full valid groups, one var = K
kfile=TMP+"/fake.key"
LIVEB={"DESK_QUALIFIER":"live_claude","DESK_LIVE_MODEL":"m1","DESK_LIVE_KEY_FILE":kfile,"DESK_LIVE_PRICE_DATE":"2026-11-01","DESK_LIVE_LEDGER_PATH":TMP+"/led","DESK_LIVE_RUN_ID":"r1","DESK_LIVE_BASE_URL":"http://127.0.0.1:9","DESK_LIVE_PRICE_IN_PER_MTOK":"1","DESK_LIVE_PRICE_OUT_PER_MTOK":"2","DESK_LIVE_CAP_RUN_USD":"1","DESK_LIVE_CAP_TOTAL_USD":"2"}
HSB={"DESK_CRM":"hubspot","DESK_HUBSPOT_KEY_FILE":kfile,"DESK_HUBSPOT_MAX_CALLS":"5","DESK_HUBSPOT_BASE_URL":"http://127.0.0.1:9"}
SMB={"DESK_OUTBOX":"smtp","DESK_SMTP_HOST":"127.0.0.1","DESK_SMTP_PORT":"25","DESK_SMTP_FROM":"a@example.test","DESK_SMTP_MESSAGE_ID_DOMAIN":"example.test"}
SPB={"DESK_OUTBOX":"smtp_provider","DESK_SMTPP_HOST":"smtp.example.test","DESK_SMTPP_USER":"u","DESK_SMTPP_PASSWORD_FILE":kfile,"DESK_SMTPP_FROM":"a@example.test","DESK_SMTPP_RECIPIENTS":"b@example.test","DESK_SMTPP_MAX_SENDS":"3"}
for b,extra in [(LIVEB,["DESK_LIVE_API_VERSION","DESK_LIVE_TIMEOUT_SECONDS","DESK_LIVE_MAX_TOKENS","DESK_LIVE_EFFORT","DESK_LIVE_ALLOW_ANY_BASE_URL"]),(HSB,["DESK_HUBSPOT_TIMEOUT_SECONDS","DESK_HUBSPOT_MAX_429_RETRIES","DESK_HUBSPOT_STATS_FILE","DESK_HUBSPOT_ALLOW_ANY_BASE_URL"]),(SMB,["DESK_SMTP_TIMEOUT_SECONDS"]),(SPB,["DESK_SMTPP_PORT","DESK_SMTPP_SECURITY","DESK_SMTPP_MESSAGE_ID_DOMAIN","DESK_SMTPP_TIMEOUT_SECONDS","DESK_SMTPP_STATS_FILE","DESK_SMTPP_CA_FILE"])]:
    for v in list(b)+extra:
        if v=="DESK_QUALIFIER": continue
        e=dict(b); e[v]=K
        A("server",[],e,"ENV(full group) "+v,["-m","lead_desk.server"])
        A("feed",["--source","form","--index","1"],e,"ENV(full group) "+v,["scripts/feed.py"])
# also DESK_QUALIFIER, DESK_CRM, DESK_OUTBOX with K on server already done in round 1
def run(i):
    sc,kind,args,env,label,pre,lo=cs[i]; d=h.sdir(5000+i)
    e={"PATH":os.environ["PATH"],"PYTHONPATH":T+"/src:"+T+"/scripts","TMPDIR":d,"HOME":d,"DESK_DB_PATH":d+"/d.sqlite3","DESK_PORT":"0","DESK_FAKES_PORT":"1"}
    e.update(env)
    cmd=["unshare","-n"]+([PY,LO] if False else [])+["timeout","20"]
    cmd+= ([PY,LO,PY] if lo else [PY])+pre+args
    try:
        p=subprocess.run(cmd,cwd=T,env=e,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=40,errors="replace"); rc=p.returncode; out=p.stdout+p.stderr
    except Exception as x: rc="ERR"; out=str(x)
    shutil.rmtree(d,ignore_errors=True)
    full=K in out; part=(not full) and (K[:6] in out or K[-6:] in out)
    line=next((l.strip()[:160].replace(K,"<K>") for l in out.splitlines() if K in l or (part and (K[:6] in l or K[-6:] in l))),"")
    return dict(i=i,script=sc,kind=kind,label=label.replace(K,"<K>").replace(TMP,"$TMP"),exit=rc,key="yes" if full else ("PARTIAL" if part else "no"),tb="Traceback" in out,line=line,head=(out.strip().splitlines() or [""])[-1][:110].replace(K,"<K>"))
if __name__=="__main__":
    print(len(cs),flush=True)
    with ThreadPoolExecutor(6) as ex: res=list(ex.map(run,range(len(cs))))
    json.dump(res,open(OUT+"/results2.json","w"),indent=0); print("DONE")
