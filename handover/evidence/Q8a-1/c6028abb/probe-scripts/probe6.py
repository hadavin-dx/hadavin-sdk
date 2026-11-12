"""EVIDENCE probe (item 6): the 11 f-string hits of the previous evidence, each with a made-up marker planted as the configured value.
Records where the marker is seen: in a message / exception / cause / traceback / log line (SEEN-IN-TEXT) or only in a returned value."""
import json, logging, sys, traceback, collections, os
import hadavin_sdk
LEGAL = "zq" + "-probe-" + "mk4417"; UNDER = "zq_probe_mk4417"
def seen(exc):
    out=[]; st=[exc]; ids=set()
    while st:
        x=st.pop()
        if x is None or id(x) in ids: continue
        ids.add(id(x)); out+=[str(x),repr(x),str(x.args)]
        st+=[x.__cause__]+([] if x.__suppress_context__ else [x.__context__])
    out.append("".join(traceback.format_exception(exc))); return "\n".join(out)
class H(logging.Handler):
    def __init__(s): super().__init__(); s.b=[]
    def emit(s,r): s.b.append(r.getMessage()+" "+str(r.args)+(r.exc_text or ""))
rows=[]
def run(hit, label, fn, marker=LEGAL):
    h=H(); lg=logging.getLogger(); lg.addHandler(h); lg.setLevel(logging.DEBUG)
    ret=None; exc=None; text=""; rv=""
    try: ret=fn()
    except BaseException as e: exc=type(e).__name__; text=seen(e)
    lg.removeHandler(h)
    log="\n".join(h.b)
    rv=json.dumps(ret,default=str) if ret is not None else ""
    rows.append(dict(hit=hit,label=label,outcome=("raised "+exc) if exc else "returned",in_message_exc_traceback=marker in text,in_log=marker in log,in_returned_value=marker in rv))
# hits 1 (gcp:39), 2-3 (anthropic:32,33): see probe5 (same marker, same method); also here quickly
from types import SimpleNamespace
from hadavin_sdk.errors import ConfigError
import hadavin_sdk.actions.secrets_gcp as g
class C:
    def access_secret_version(s,name,retry=None,timeout=None): raise RuntimeError(f"denied {name}")
run("1 gcp:39", "project_id=marker, client error quotes path", lambda: g.GcpSecretManagerProvider(C(), project_id=LEGAL).get("a_secret"))
from google.api_core.exceptions import NotFound
class C2:
    def access_secret_version(s,name,retry=None,timeout=None): raise NotFound(f"missing {name}")
run("1 gcp:39", "project_id=marker, NotFound quotes path", lambda: g.GcpSecretManagerProvider(C2(), project_id=LEGAL).get("a_secret"))
import anthropic
from hadavin_sdk.llm import anthropic as wire
class V:
    def __init__(s,**kw): raise ValueError(f"bad {kw['base_url']}")
o=anthropic.AnthropicVertex; anthropic.AnthropicVertex=V
run("2 anthropic:32", "vertex region=marker (global/us/eu/other)", lambda: wire.client(SimpleNamespace(platform="vertex",region=LEGAL,project_id=LEGAL,call_timeout_s=5,resource=None),None))
for reg in ("global","us","eu"):
    run("2 anthropic:32", f"vertex region={reg}, project=marker", lambda reg=reg: wire.client(SimpleNamespace(platform="vertex",region=reg,project_id=LEGAL,call_timeout_s=5,resource=None),None))
anthropic.AnthropicVertex=o
class F:
    def __init__(s,**kw): raise ValueError(f"bad {kw['base_url']}")
o=anthropic.AnthropicFoundry; anthropic.AnthropicFoundry=F
run("3 anthropic:33", "foundry resource=marker", lambda: wire.client(SimpleNamespace(platform="foundry",resource=LEGAL,region=None,project_id=None,call_timeout_s=5),"k"))
anthropic.AnthropicFoundry=o
# hits 4,5 kubernetes
from hadavin_sdk.sources.kubernetes import KubernetesSettings, KubernetesSource
st=KubernetesSettings(api_url="https://k8s.example.invalid",namespaces=(LEGAL,))
def fetch_with(kind):
    def f(method,url,*,operation,body=None,headers=None,max_bytes=None,**kw):
        if kind=="raise": raise OSError(f"{method} {url} refused")
        if kind=="json": return "{ not json "+url
        if kind=="items_str": return json.dumps({"items":["x"],"metadata":{}})
        if kind=="items_none_meta": return json.dumps({"items":[{"metadata":None}],"metadata":{}})
        if kind=="error_status": return json.dumps({"kind":"Status","status":"Failure","message":f"namespaces \"{LEGAL}\" is forbidden"})
        if kind=="ok_empty": return json.dumps({"items":[],"metadata":{}})
        if kind=="ok_one":
            if "events" in url: return json.dumps({"items":[{"metadata":{"name":"ev1"},"lastTimestamp":"2026-01-01T12:00:00Z","reason":"x","message":"m"}],"metadata":{}})
            return json.dumps({"items":[{"metadata":{"name":"dep1","annotations":{}},"spec":{"template":{"spec":{"containers":[]}}}}],"metadata":{}})
        if kind=="pod_log": return "line1\nline2\n"
    return f
for k in ("raise","json","items_str","items_none_meta","error_status","ok_empty","ok_one"):
    run("4 kubernetes:237", f"recent_changes ns=marker fetch={k}", lambda k=k: KubernetesSource(fetch_with(k),st).recent_changes(LEGAL,"2026-01-01T00:00:00Z","2026-01-02T00:00:00Z"))
    run("5 kubernetes:251", f"query_logs ns=marker fetch={k}", lambda k=k: KubernetesSource(fetch_with(k),st).query_logs(LEGAL+"/pod","2026-01-01T00:00:00Z","2026-01-02T00:00:00Z",5))
run("5 kubernetes:251", "query_logs pod log lines", lambda: KubernetesSource(fetch_with("pod_log"),st).query_logs(LEGAL+"/pod","2026-01-01T00:00:00Z","2026-01-02T00:00:00Z",5))
# hit 6 migration_numbers:251
from pathlib import Path
from hadavin_sdk.store.migration_numbers import hand_recipe, order_problems
late=Path("0001_first.sql")
run("6 migration_numbers:251","hand_recipe schema=plain marker (underscores)",lambda: hand_recipe([("0001_x","SELECT 1;")],UNDER),UNDER)
run("6 migration_numbers:251","hand_recipe schema=marker with dash",lambda: hand_recipe([("0001_x","SELECT 1;")],LEGAL))
run("6 migration_numbers:251","order_problems schema=plain marker",lambda: order_problems(["0002_second"],[late],{late:"SELECT 1;"},UNDER),UNDER)
run("6 migration_numbers:251","order_problems schema=marker with dash",lambda: order_problems(["0002_second"],[late],{late:"SELECT 1;"},LEGAL))
# hits 7,8 migrate.py:212 on the real Postgres
dsn=os.environ["HADAVIN_TEST_PG_DSN"]
import psycopg
from hadavin_sdk.store import migrate as mg
with psycopg.connect(dsn, autocommit=True) as c:
    c.execute(f'DROP SCHEMA IF EXISTS {UNDER} CASCADE'); c.execute(f'DROP ROLE IF EXISTS {UNDER}')
    c.execute(f'CREATE ROLE {UNDER}'); c.execute(f'CREATE SCHEMA {UNDER}'); c.execute(f'GRANT CREATE ON SCHEMA {UNDER} TO {UNDER}')
    c.execute(f'CREATE TABLE {UNDER}.t1 (a int)'); c.execute(f'ALTER TABLE {UNDER}.t1 OWNER TO {UNDER}')
with psycopg.connect(dsn) as c:
    c.execute(f'SET search_path TO {UNDER}')
    def eff():
        return mg.effective_problems(c, UNDER, lambda g: "", None)
    run("7+8 migrate.py:212","effective_problems role=schema=marker (CREATE granted, owns table)",eff,UNDER)
    run("7+8 migrate.py:212","effective_problems role missing",lambda: mg.effective_problems(c, UNDER+"_x", lambda g: "", None),UNDER)
with psycopg.connect(dsn, autocommit=True) as c:
    c.execute(f'DROP SCHEMA {UNDER} CASCADE'); c.execute(f'DROP ROLE {UNDER}')
# hits 9-11 backends/table.py hosts
from hadavin_sdk.backends.table import AnthropicSettings, S3ObjectLockSettings
from hadavin_sdk.backends.factory import hosts as hostlist
for plat in ("vertex",):
    s=AnthropicSettings(kind="anthropic",platform="vertex",region=LEGAL,project_id=LEGAL)
    run("9+10 table:367,379", "hosts() vertex region=marker",lambda s=s: hostlist([("llm",s)]))
s=AnthropicSettings(kind="anthropic",platform="foundry",resource=LEGAL,api_key_secret_name="k")
run("11a table:380", "hosts() foundry resource=marker",lambda s=s: hostlist([("llm",s)]))
s=S3ObjectLockSettings(kind="s3_object_lock",bucket=LEGAL,region="eu-west-1",retention_ack=True)
run("11b table:394", "hosts() s3 bucket=marker",lambda s=s: hostlist([("anchor",s)]))
s=S3ObjectLockSettings(kind="s3_object_lock",bucket="b",region=LEGAL,retention_ack=True)
run("11b table:394", "hosts() s3 region=marker",lambda s=s: hostlist([("anchor",s)]))
print("module:",hadavin_sdk.__file__)
for r in rows: print(f"{r['hit']:22s} {r['label'][:68]:68s} {r['outcome']:20s} msg/exc/tb={r['in_message_exc_traceback']!s:5s} log={r['in_log']!s:5s} returned={r['in_returned_value']}")
json.dump(rows,open(sys.argv[1],"w"),indent=0)
