"""Shared stack helpers for the n8n door tests (made-up data, loopback only, no spend, no real service). Imported by dn1.py.
Runs inside a prepared work folder of the evidence harness (see README.md): n8n 2.46.6 installed there, Postgres container, owner account (setup.py)."""
import os, sys, json, time, glob, shutil, socket, sqlite3, subprocess, signal, threading, urllib.request, urllib.error, uuid, collections
import api, lib
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ["N8N_EVD_WORK"]
ROOT = os.environ.get("DN1_DESK_REPO", "/tmp/rr/t3exp")          # clean export of the public desk repository
S = os.path.join(WORK, "dn1"); os.makedirs(S, exist_ok=True)
KEYTEXT = "FAKEKEY-planted-0123456789"                              # made-up model key (T7 greps for it)
KEY, LEDGER, CALLS, PXLOG, MAIL = (os.path.join(S, n) for n in ("key.txt", "ledger.jsonl", "calls.log", "proxy.log", "mail.jsonl"))
from runcfg import DESKP, FAKEP, MODELP, PROXYP, MAILP, N8NP   # defaults = the old literal values (8765, 8766, 48767, 8760, 8791, n8n 5679); env-configurable, see runcfg.py
D = "http://127.0.0.1:%d" % DESKP; F = "http://127.0.0.1:%d" % FAKEP; M = "http://127.0.0.1:%d" % MODELP
ALERT_TO = "alerts@example.test"
PLANT_EMAIL, PLANT_NAME = "planted.t7@example.test", "Planted Tester"
procs = {}
EXTRA = {"N8N_BLOCK_ENV_ACCESS_IN_NODE": "false", "DESK_URL": "http://127.0.0.1:%d" % PROXYP, "DESK_TIMEOUT_MS": "15000", "DESK_ALERT_TO": ALERT_TO}
_orig_env = lib.n8n_env
lib.n8n_env = lambda limit=None: dict(_orig_env(limit), **EXTRA)    # n8n gets the door settings from its environment
def bindable(p):
    s = socket.socket()
    try: s.bind(("127.0.0.1", p)); return True
    except OSError: return False
    finally: s.close()
def wait_free(ports, t=150):
    for _ in range(t):
        if all(bindable(p) for p in ports): return
        time.sleep(1)
    raise RuntimeError("ports did not free up: %s" % [p for p in ports if not bindable(p)])
def spawn(name, args, env, log, cwd=None):
    p = subprocess.Popen(args, cwd=cwd or ROOT, env=env, stdout=open(os.path.join(S, log), "ab"), stderr=subprocess.STDOUT, start_new_session=True); procs[name] = p; return p
def stop(name):
    p = procs.pop(name, None)
    if not p: return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try: os.killpg(p.pid, sig)
        except OSError: pass
        time.sleep(1 if sig == signal.SIGTERM else 0)
    try: p.wait(timeout=5)
    except Exception: pass
def stop_desk_side():
    for n in ("desk", "proxy", "fakes", "model", "catcher"): stop(n)
def get(u, t=3):
    try:
        with urllib.request.urlopen(u, timeout=t) as r: return r.status, r.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
    except Exception as e: return type(e).__name__, ""
def up(url, tries=60):
    for _ in range(tries):
        if get(url)[0] == 200: return True
        time.sleep(0.5)
    return False
def denv(extra=None):
    e = {k: os.environ[k] for k in ("PATH", "HOME") if k in os.environ}
    e.update(PYTHONPATH="src:.", DESK_LEADFLOW_FILE="off", DESK_QUALIFIER="live_claude", DESK_LIVE_MODEL="fake-model", DESK_LIVE_KEY_FILE=KEY,
             DESK_LIVE_PRICE_IN_PER_MTOK="1", DESK_LIVE_PRICE_OUT_PER_MTOK="1", DESK_LIVE_PRICE_DATE="2026-11-14", DESK_LIVE_CAP_RUN_USD="1", DESK_LIVE_CAP_TOTAL_USD="2",
             DESK_LIVE_LEDGER_PATH=LEDGER, DESK_LIVE_RUN_ID="dn1", DESK_LIVE_BASE_URL=M)
    e.update(extra or {}); return e
def clean_state():
    for f in glob.glob(ROOT + "/data/*"): (shutil.rmtree if os.path.isdir(f) else os.remove)(f)
    for f in (LEDGER, CALLS, PXLOG, MAIL):
        if os.path.exists(f): os.remove(f)
    open(KEY, "w").write(KEYTEXT + "\n"); os.chmod(KEY, 0o600)
def start_desk():
    wait_free([DESKP]); spawn("desk", [sys.executable, "scripts/crash_desk.py"], denv(), "desk.log")
    assert up(D + "/counts"), "desk did not start"
def kill_desk_now():
    p = procs.pop("desk", None)
    if p:
        try: os.killpg(p.pid, signal.SIGKILL)
        except OSError: pass
        try: p.wait(timeout=5)
        except Exception: pass
def stack(kind="keyed", model_mode="ok", slow=None, catcher=True, fresh=True):
    """fresh desk side: model stand-in (call log), CRM/mail stand-in (keyed or blind), desk (live-model qualifier against the stand-in, spend ledger), counting proxy, mail catcher"""
    stop_desk_side(); wait_free([DESKP, FAKEP, MODELP, PROXYP, MAILP])
    if fresh: clean_state()
    e = denv()
    spawn("model", [sys.executable, "-m", "demo_only.fake_model_server", "--mode", model_mode, "--port", str(MODELP), "--key-file", KEY, "--call-log", CALLS], e, "model.log")
    spawn("fakes", [sys.executable, "-m", "demo_only.fakes_server", "--outbox", kind, "--port", str(FAKEP)], e, "fakes.log")
    assert up(F + "/fake/info") and up(M + "/stats"), "stand-ins did not start"
    assert json.loads(get(F + "/fake/info")[1]).get("mode") == kind, "stand-in mode is not " + kind
    if slow: model_ctl(mode="slow", slow_seconds=slow)
    start_desk()
    spawn("proxy", [sys.executable, os.path.join(HERE, "desk_proxy.py"), str(PROXYP), str(DESKP), PXLOG], os.environ.copy(), "proxy.log", cwd=S)
    if catcher: spawn("catcher", [sys.executable, os.path.join(HERE, "smtp_catcher.py"), str(MAILP), MAIL], os.environ.copy(), "catcher.log", cwd=S)
    time.sleep(1)
def model_ctl(**kw):
    r = urllib.request.Request(M + "/control", json.dumps(kw).encode(), {"Content-Type": "application/json"}, method="POST"); urllib.request.urlopen(r, timeout=5).read()
# ---- n8n side
CRED_ID = None
def n8n_prepare(deploy_doors=True):
    global CRED_ID
    api.login(); inst = json.load(open(os.path.join(WORK, ".run", "instance.json")))
    c = api.call("POST", "/credentials", {"name": "desk-alert-smtp", "type": "smtp", "projectId": inst["project_id"],
         "data": {"user": "stand-in", "password": "stand-in", "host": "127.0.0.1", "port": MAILP, "secure": False, "disableStartTls": True, "hostName": ""}})
    d = c.get("data", c); assert "id" in d, c; CRED_ID = d["id"]
    out = os.path.join(S, "flows"); subprocess.run([sys.executable, os.path.join(HERE, "build_flows.py"), out], check=True, capture_output=True)
    n = json.load(open(os.path.join(out, "desk-error-notifier.json"))); n["nodes"][1]["credentials"]["smtp"]["id"] = CRED_ID
    json.dump(n, open(os.path.join(out, "desk-error-notifier.json"), "w"))
    w = api.call("POST", "/workflows", n); wd = w.get("data", w); assert "id" in wd, w; err_id = wd["id"]
    act = api.call("POST", "/workflows/%s/activate" % err_id, {"versionId": wd["versionId"]})   # n8n 2.46.6: an error workflow must be active ("is not active and cannot be executed" otherwise)
    assert "HTTPError" not in act, act
    subprocess.run([sys.executable, os.path.join(HERE, "build_flows.py"), out, err_id], check=True, capture_output=True)
    json.dump(n, open(os.path.join(out, "desk-error-notifier.json"), "w"))
    res = {"error_workflow": err_id}
    if deploy_doors:
        for fn, nm in (("desk-form-door.json", "door-form"), ("desk-webhook-door.json", "door-hook")): res[nm] = api.deploy(os.path.join(out, fn), nm)
    return res
def n8n_restart(paths=("desk-form", "desk-webhook"), **env):
    lib.kill_n8n_confirmed(); EXTRA.update(env); return lib.start_n8n(None, paths=paths)
# ---- calls
def post(path, body, t=45):
    r = urllib.request.Request("http://127.0.0.1:%d/webhook/%s" % (N8NP, path), json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=t) as x: st, txt = x.status, x.read().decode()
    except urllib.error.HTTPError as e: st, txt = e.code, e.read().decode()
    except Exception as e: return type(e).__name__, None
    try: return st, json.loads(txt)
    except ValueError: return st, txt[:200]
def form(lead, email=None, name="Test Person"):
    return {"submission_id": lead, "name": name, "email": email or ("%s@example.test" % lead), "phone": "", "company": "Example Ltd", "message": "made-up"}
def hook(lead, email=None, name="Test Person"):
    return {"message_id": lead, "from_name": name, "from_email": email or ("%s@example.test" % lead), "body": "made-up"}
def has_verdict(rep): return isinstance(rep, dict) and bool(rep.get("verdict")) and not rep.get("n8n_error")
def take(path, body, gap=5, resends=3):
    """the take rule: no verdict in the reply = send again with the same lead id, up to 3 times, 5 s apart"""
    out = []
    for i in range(resends + 1):
        st, rep = post(path, body); out.append([st, rep if not isinstance(rep, dict) else {k: rep.get(k) for k in ("n8n_error", "desk_status", "verdict") }])
        if has_verdict(rep): break
        if i < resends: time.sleep(gap)
    return out
# ---- counting
def jl(path):
    try: return [json.loads(l) for l in open(path) if l.strip()]
    except OSError: return []
def desk_db(email=None, ref=None):
    for f in [x for x in glob.glob(ROOT + "/data/*") if os.path.isfile(x) and open(x, "rb").read(15) == b"SQLite format 3"]:
        c = sqlite3.connect("file:%s?mode=ro" % f, uri=True)
        try:
            o = {}
            if email is not None:
                o["leads"] = c.execute("select count(*) from leads where lower(email)=?", (email.lower(),)).fetchone()[0]
                o["fu"] = [r[0] for r in c.execute("select f.state from followups f join leads l on l.lead_id=f.lead_id where lower(l.email)=?", (email.lower(),)).fetchall()]
            if ref is not None: o["receipts"] = c.execute("select count(*) from receipts where source_ref=?", (ref,)).fetchone()[0]
            return o
        except Exception as e: return {"err": str(e)[:80]}
        finally: c.close()
    return {"err": "no-db"}
def per(email):
    crm = json.loads(get(F + "/fake/crm")[1] or "{}"); ob = json.loads(get(F + "/fake/outbox")[1] or "{}")
    return {"crm_rows": sum(1 for r in crm.get("rows", []) if r.get("record", {}).get("email") == email), "emails": sum(1 for m in ob.get("messages", []) if m.get("to") == email)}
def lead_view(email, ref):
    return {**desk_db(email, ref), **per(email)}
def money(expected):
    """money check: model stand-in calls per desk lead id all equal 1 and their number equals `expected`; spend ledger reserve rows equal `expected`"""
    calls = collections.Counter(c.get("lead_id") for c in jl(CALLS)); led = [r for r in jl(LEDGER) if r.get("op") == "reserve"]
    ok = len(calls) == expected and all(v == 1 for v in calls.values()) and len(led) == expected
    return {"expected_leads": expected, "model_calls_total": sum(calls.values()), "model_lead_ids": len(calls), "max_calls_per_lead_id": max(calls.values()) if calls else 0, "ledger_reserve_rows": len(led), "ok": ok}
def mail_rows(): return jl(MAIL)
def px(): return jl(PXLOG)
def rec(test, **kw): print("REC", json.dumps(dict(test=test, **kw), default=str), flush=True); return kw
