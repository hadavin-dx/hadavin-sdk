import os, subprocess, sys, json, re, shutil
from concurrent.futures import ThreadPoolExecutor
RR="/home/user/build/rr6"; T=RR+"/tree-C11"; OUT=RR+"/out/C11"; TMP=RR+"/tmp-C11"
PY=RR+"/venv312/bin/python"
K="".join(["Hq","7Zk","Wp","3Xv","9Nd"])   # fake key built from parts
os.makedirs(TMP,exist_ok=True)
keyfile=TMP+"/fake.key"; open(keyfile,"w").write("fake-"+K+"\n")
def sdir(n):
    d=f"{TMP}/c{n}"; os.makedirs(d,exist_ok=True); return d
S={ # script -> (command prefix, base args dict(opt->val or None for flag), value options, flag options)
 "feed":(["scripts/feed.py"],{"--source":"form","--index":"1"},["--source","--index"],["--all"]),
 "hubspot_probe":(["scripts/hubspot_probe.py"],{},["--yes-spend-calls","--token-env","--dry-run"],["--plan"]),
 "run_live_check":(["scripts/run_live_check.py"],{"--key-file":keyfile,"--base-url":"http://127.0.0.1:9","--ledger":TMP+"/led.json","--cap-run":"1","--cap-total":"2","--price-date":"2026-11-01","--model":"m1=1,2"},
   ["--key-file","--base-url","--ledger","--cap-run","--cap-total","--price-date","--model","--max-tokens","--effort","--timeout","--leads","--runs"],[]),
 "run_real_check":(["scripts/run_real_check.py"],{},["--config","--dry-port-base","--dry-smtp-script"],["--dry-fakes","--live-model","--cleanup","--assume-yes","--keep"]),
 "catcher":(["-m","load_tools.catcher"],{"--out":TMP+"/c.jsonl","--port":"0"},["--out","--host","--port","--control"],[]),
 "check_invariants":(["-m","load_tools.check_invariants"],{"--requests":TMP+"/r","--book":TMP+"/b","--catcher":TMP+"/ca","--crm":TMP+"/cr","--model-log":TMP+"/ml","--ledger":TMP+"/l"},
   ["--requests","--book","--catcher","--crm","--model-log","--ledger","--drain","--model-bound","--max-failed","--max-unknown","--facts","--max-review","--max-503-rate","--max-drain-seconds","--json"],["--model-required","--no-model-required","--require-comparable","--no-require-comparable"]),
 "load_driver":(["-m","load_tools.load_driver"],{"--base-url":"http://127.0.0.1:9","--scenario":"burst:1","--log":TMP+"/lg"},
   ["--base-url","--scenario","--log","--facts","--workers","--threads","--seed","--id-prefix"],[]),
 "n8n_api":(["scripts/n8n_api.py"],{},[],[]),
 "scrub":(["-m","tools.scrub_n8n_export"],{},[],[]),
 "check_schema":(["scripts/check_schema.py"],{},[],[]),
 "reset_check":(["scripts/reset_check.py"],{},[],[]),
 "crash_desk":(["scripts/crash_desk.py"],{},[],[]),
 "server":(["-m","lead_desk.server"],{},[],[]),
}
for f in open(TMP+"/../out/C11/touch","a") if False else []: pass
for f in ["r","b","ca","cr","ml","l","lg"]: open(f"{TMP}/{f}","w").write("")
cases=[]
def add(sc,kind,args,env=None,label=None): cases.append((sc,kind,args,env or {},label or " ".join(args)))
for sc,(pre,base,vopts,fopts) in S.items():
    def others(skip): 
        r=[]
        for o,v in base.items():
            if o in skip: continue
            r+= [o] if v is None else [o,v]
        return r
    add(sc,"positional",[K]); add(sc,"positional",[K,K])
    add(sc,"optname",["--"+K]); add(sc,"optname",["-"+K]); add(sc,"optname",["--"+K+"="+K])
    add(sc,"subcommand",[K,"list"]); add(sc,"subcommand",["list",K]); 
    add(sc,"dashdash",["--",K]); add(sc,"dashdash",others([])+["--",K])
    add(sc,"stray+base",others([])+[K])
    add(sc,"optname+base",others([])+["--"+K])
    for o in vopts:
        add(sc,"value",others([o])+[o,K]); add(sc,"value=",others([o])+[o+"="+K])
        add(sc,"value+stray",others([o])+[o,"1",K])
        add(sc,"missing-value",others([o])+[o,K and "--"+K])
        ab=o[:max(5,len(o)-3)]
        add(sc,"prefix",others([o])+[ab,K]); add(sc,"prefix=",others([o])+[ab+"="+K]); add(sc,"dashdash",others([o])+[o,"--",K])
    for o in fopts:
        add(sc,"flag+stray",others([])+[o,K]); add(sc,"flag=",others([])+[o+"="+K])
        ab=o[:max(5,len(o)-3)]
        add(sc,"prefix",others([])+[ab]); add(sc,"prefix=",others([])+[ab+"="+K])
# sub-command forms for n8n_api / scrub
for cmd in ["import","activate","deactivate"]:
    add("n8n_api","subcommand",[cmd,K]); add("n8n_api","subcommand",[cmd,K,K])
    add("n8n_api","subcommand",[cmd,"--"+K])
add("n8n_api","subcommand",["import",TMP+"/"+K+".json"]) 
add("scrub","positional",[K,K]); add("scrub","positional",[K,K,K]); add("scrub","positional",[TMP+"/x/"+K,TMP+"/y/"+K])
add("scrub","positional",["/etc/passwd",K])
# env cases
DESKV="DESK_ADAPTERS DESK_ALLOWED_HOSTS DESK_APPROVERS_FILE DESK_BIND DESK_CRM DESK_DB_PATH DESK_FAKES_HOST DESK_FAKES_PORT DESK_FAKES_URL DESK_LATER_MODE DESK_LEADFLOW_FILE DESK_NUDGE_TO DESK_OUTBOX DESK_PORT DESK_QUALIFIER DESK_REPLIES_PATH DESK_SEND_TIMEOUT_SECONDS DESK_SIZE_CAP_BYTES DESK_STALL_SECONDS DESK_START_SECONDS".split()
LIVE="MODEL KEY_FILE LEDGER_PATH RUN_ID PRICE_DATE PRICE_IN_PER_MTOK PRICE_OUT_PER_MTOK CAP_RUN_USD CAP_TOTAL_USD BASE_URL API_VERSION TIMEOUT_SECONDS MAX_TOKENS EFFORT ALLOW_ANY_BASE_URL".split()
HS="KEY_FILE MAX_CALLS BASE_URL ALLOW_ANY_BASE_URL MAX_429_RETRIES STATS_FILE TIMEOUT_SECONDS".split()
SM="HOST PORT FROM MESSAGE_ID_DOMAIN TIMEOUT_SECONDS".split()
SP="HOST PORT SECURITY USER PASSWORD_FILE CA_FILE FROM MESSAGE_ID_DOMAIN MAX_SENDS RECIPIENTS STATS_FILE TIMEOUT_SECONDS".split()
envsets=[({v:K},v) for v in DESKV]
envsets+=[({"DESK_QUALIFIER":"live_claude","DESK_LIVE_"+v:K},"DESK_LIVE_"+v) for v in LIVE]
envsets+=[({"DESK_CRM":"hubspot","DESK_HUBSPOT_"+v:K},"DESK_HUBSPOT_"+v) for v in HS]
envsets+=[({"DESK_OUTBOX":"smtp","DESK_SMTP_"+v:K},"DESK_SMTP_"+v) for v in SM]
envsets+=[({"DESK_OUTBOX":"smtp_provider","DESK_SMTPP_"+v:K},"DESK_SMTPP_"+v) for v in SP]
for e,name in envsets:
    for sc,args in [("server",[]),("feed",["--source","form","--index","1"]),("reset_check",[]),("run_real_check",["--dry-fakes"]),("load_driver",None),("check_invariants",None)]:
        if args is None:
            if not name.startswith("DESK_QUALIFIER"): continue
            args=None
        add(sc,"env",args if args is not None else (["--base-url","http://127.0.0.1:9","--scenario","burst:1","--log",TMP+"/lg"] if sc=="load_driver" else ["--requests",TMP+"/r","--book",TMP+"/b","--catcher",TMP+"/ca","--crm",TMP+"/cr","--model-log",TMP+"/ml","--ledger",TMP+"/l"]),env=e,label="ENV "+name)
for v,sc,args in [("N8N_URL","n8n_api",["list"]),("N8N_API_KEY_FILE","n8n_api",["list"]),("LEAD_DESK_PATH_ROOTS","scrub",[TMP+"/a.json",TMP+"/o.json"]),("LEAD_DESK_PATH_ROOTS","n8n_api",["import",TMP+"/a.json"])]:
    add(sc,"env",args,env={v:K},label="ENV "+v)
add("hubspot_probe","env",["--plan"],env={"HUBSPOT_TOKEN":K},label="ENV default token var")
add("hubspot_probe","env",["--yes-spend-calls","7","--dry-run","http://127.0.0.1:9"],env={"HUBSPOT_TOKEN":K},label="ENV default token var, dry-run")
for v in ["HTTP_PROXY","HTTPS_PROXY","no_proxy","PYTHONPATH","DESK_QUALIFIER"]:
    add("n8n_api","env",["list"],env={v:"http://"+K+"@127.0.0.1:9"},label="ENV "+v+" (userinfo)")
# unique dirs
def run(i):
    sc,kind,args,env,label=cases[i]
    pre=S[sc][0]; d=sdir(i)
    e={"PATH":os.environ["PATH"],"PYTHONPATH":T+"/src","TMPDIR":d,"HOME":d,"DESK_DB_PATH":d+"/d.sqlite3","DESK_PORT":"0","DESK_FAKES_PORT":"1"}
    e.update(env)
    if "DESK_DB_PATH" in env and env["DESK_DB_PATH"]==K: pass
    cmd=["unshare","-n","timeout","20",PY]+pre+args
    try:
        p=subprocess.run(cmd,cwd=T,env=e,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=40,errors="replace")
        rc=p.returncode; out=p.stdout+p.stderr
    except Exception as x: rc="ERR"; out=str(x)
    shutil.rmtree(d,ignore_errors=True)
    full=K in out; part=(not full) and (K[:6] in out or K[-6:] in out)
    line=""
    for l in out.splitlines():
        if K in l or (part and (K[:6] in l or K[-6:] in l)): line=l.strip()[:160].replace(K,"<K>").replace(K[:6],"<K1>"); break
    tb="Traceback" in out
    return dict(i=i,script=sc,kind=kind,label=label.replace(K,"<K>").replace(TMP,"$TMP"),exit=rc,key="yes" if full else ("PARTIAL" if part else "no"),tb=tb,line=line,
                head=(out.strip().splitlines() or [""])[-1][:100].replace(K,"<K>"))
if __name__=="__main__":
    print(len(cases),"cases",flush=True)
    with ThreadPoolExecutor(6) as ex: res=list(ex.map(run,range(len(cases))))
    json.dump(res,open(OUT+"/results.json","w"),indent=0)
    print("DONE",flush=True)
