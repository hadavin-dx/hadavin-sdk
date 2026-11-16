"""Own stdlib load script (from ORDER 199), tidied for final_gate.sh: root, python and ports come from the environment.
No retries except in kill mode. Numbers only. usage: load.py scen MODE same|diff N   |   load.py kill MODE ROUND"""
import json, os, shutil, signal, subprocess, sys, threading, time, urllib.request, urllib.error
from collections import Counter
ROOT = os.environ["LOAD_ROOT"]; DATA = os.environ["LOAD_DATA"]; PY = os.environ["LOAD_PY"]
DP = os.environ["LOAD_DESK_PORT"]; FP = os.environ["LOAD_FAKES_PORT"]  # free ports picked by final_gate.sh per step
DESK = "http://127.0.0.1:" + DP; FAKES = "http://127.0.0.1:" + FP
ENV = {k: v for k, v in os.environ.items() if not k.startswith("DESK_")}
ENV.update(PYTHONPATH="src:.", DESK_DB_PATH=DATA + "/desk.sqlite3", DESK_PORT=DP, DESK_FAKES_PORT=FP, DESK_BIND="127.0.0.1")
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def get(url, t=30):
    with OP.open(url, timeout=t) as r: return json.loads(r.read())
def post(url, obj, t=60):
    req = urllib.request.Request(url, json.dumps(obj).encode(), {"Content-Type": "application/json"})
    try:
        with OP.open(req, timeout=t) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b"{}")
        except Exception: return e.code, {}
    except Exception as e: return type(e).__name__, {}

procs = {}
def start(mode):
    shutil.rmtree(DATA, ignore_errors=True); os.makedirs(DATA)
    procs["fakes"] = subprocess.Popen([PY, "-m", "demo_only.fakes_server", "--outbox", mode, "--port", FP], cwd=ROOT, env=ENV, stdout=open(DATA + "/fakes.log", "w"), stderr=subprocess.STDOUT)
    start_desk(); 
def start_desk():
    procs["desk"] = subprocess.Popen([PY, "-m", "lead_desk.server"], cwd=ROOT, env=ENV, stdout=open(DATA + "/desk.log", "a"), stderr=subprocess.STDOUT)
    for _ in range(100):
        try: get(DESK + "/counts", 2); return
        except Exception: time.sleep(0.1)
    raise SystemExit("desk did not start")
def stop():
    for p in procs.values():
        try: p.kill(); p.wait(5)
        except Exception: pass

def env_body(ref, email): return {"source": "form", "source_ref": ref, "payload": {"name": "Ada Example", "email": email, "phone": "555 0100", "message": "Please call me."}}

def burst(n, emails, tag, retry_refused=False):
    barrier = threading.Barrier(n); res = []; lock = threading.Lock(); acked = []
    def one(i):
        email = emails[i]; ref = f"{tag}-{i}"; body = env_body(ref, email); barrier.wait(); t0 = time.time(); tries = 0
        while True:
            st, js = post(DESK + "/leads", body); tries += 1
            if retry_refused and st in ("URLError", "ConnectionResetError", "RemoteDisconnected", "TimeoutError", "timeout", "BadStatusLine", 503) and tries < 60:
                time.sleep(0.25); continue
            break
        with lock: res.append((st, time.time() - t0, js.get("receipt_id"), ref, email, tries))
    th = [threading.Thread(target=one, args=(i,)) for i in range(n)]
    [t.start() for t in th]; return th, res

def report(label, n, res, expect_leads, wait=3.0):
    time.sleep(wait)
    cnt = get(DESK + "/counts"); crm = get(FAKES + "/fake/crm"); out = get(FAKES + "/fake/outbox")
    st = Counter(r[0] for r in res); lat = max((r[1] for r in res), default=0)
    crm_per = Counter(r["record"].get("email", r["lead_id"]) if isinstance(r["record"], dict) else r["lead_id"] for r in crm["rows"])
    mail_per = Counter(m["to"] for m in out["messages"])
    recv_sum = cnt["new"] + cnt["duplicate"] + cnt["review"] + cnt["rejected_envelopes"]
    fivexx = sum(v for k, v in st.items() if isinstance(k, int) and k >= 500)
    nonint = {k: v for k, v in st.items() if not isinstance(k, int)}
    print(f"{label}: n={n} status={dict(st)} 5xx={fivexx} client_errors={nonint} max_latency_s={lat:.2f}")
    print(f"   desk_counts={cnt}")
    try:
        import sqlite3 as _s; _c=_s.connect("file:"+DATA+"/desk.sqlite3?mode=ro",uri=True); print("   followup_states=",dict(_c.execute("select state,count(*) from followups group by state").fetchall()),"open_receipts=",_c.execute("select count(*) from receipts where outcome is null").fetchone()[0]); _c.close()
    except Exception as _e: print("   followup_states unreadable:",type(_e).__name__)
    print(f"   received={cnt['received']} vs new+dup+review+rejected={recv_sum} (failed/unknown shown in open/pending) lost_receipt={cnt['received']-recv_sum}")
    print(f"   crm_rows={crm['count']} distinct_leads_in_crm={len(crm_per)} max_rows_per_lead={max(crm_per.values(), default=0)}; emails={out['count']} distinct_recipients={len(mail_per)} max_emails_per_lead={max(mail_per.values(), default=0)}; expected_leads={expect_leads}")
    return cnt, crm, out

def scenario(mode, kind, n):
    start(mode)
    emails = ["same@example.test"] * n if kind == "same" else [f"lead{i}@example.test" for i in range(n)]
    th, res = burst(n, emails, f"{kind}{n}"); [t.join() for t in th]
    report(f"[{mode}] {kind} n={n}", n, res, 1 if kind == "same" else n); stop()

def killtest(mode, rnd, n=200):
    start(mode)
    emails = [f"k{rnd}x{i}@example.test" for i in range(n)]
    th, res = burst(n, emails, f"kill{rnd}", retry_refused=True)
    time.sleep(0.4); procs["desk"].send_signal(signal.SIGKILL); procs["desk"].wait(); time.sleep(0.5); start_desk()
    [t.join() for t in th]
    cnt, crm, out = report(f"[{mode}] kill-9 round {rnd} n={n}", n, res, n, wait=5.0)
    ok = sum(1 for r in res if r[0] in (200, 201, 202))
    print(f"   acked_2xx={ok} of {n}; acked_but_no_receipt_id={sum(1 for r in res if r[0] in (200,201,202) and not r[2])}; retries_total={sum(r[5]-1 for r in res)}")
    stop()

if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a[0] == "scen": scenario(a[1], a[2], int(a[3]))
        elif a[0] == "kill": killtest(a[1], int(a[2]))
    finally: stop()
