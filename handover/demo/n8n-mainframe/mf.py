"""D-N2 tests: the n8n main-frame design on the real n8n 2.46.6 with stand-ins (made-up data, loopback only, no spend). Runs inside a prepared harness work folder (see ../n8n-tests/README.md).
  python mf.py M0 M1 K1 K2 K3 K4 K5      env MF_REPS (default 5) = kills per point.  Prints REC (raw) and RESULT lines; writes mf_result_<tests>.json
M0 smoke (both entries, repeat), M1 burst of 10 same lead id, K1 kill n8n after the table insert before the CRM write, K2 after the CRM write before the mail, K3 after the mail was delivered before the table update,
K4 kill the desk stage mid-call, K5 kill Postgres once. Each reports lost / doubled / unknown per lead id and whether the recovery flow fixed it, and how long it took; the money check is in every test."""
import sys, os, json, time, subprocess, threading, uuid, collections, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "n8n-tests"))
from dn1_common import *
HERE_MF = os.path.dirname(os.path.abspath(__file__))
STAGEP, CRMP = 8770, 8771
ST_URL, CRM_URL = "http://127.0.0.1:%d" % STAGEP, "http://127.0.0.1:%d" % CRMP
JOURNAL, CRMLOG = os.path.join(S, "stage-journal.jsonl"), os.path.join(S, "crm.log.jsonl")
REPS = int(os.environ.get("MF_REPS", "5")); RESULTS = {}
EXTRA.update(MF_CRM_URL=CRM_URL, MF_STAGE_URL=ST_URL)
def uid(p): return "%s-%s" % (p, uuid.uuid4().hex[:6])
def result(test, passed, why, **raw):
    RESULTS[test] = {"pass": passed, "why": why, **raw}; print("RESULT %s %s %s" % (test, "PASS" if passed else "FAIL", why), flush=True)
def psql(sql):
    return subprocess.run(["docker", "exec", lib.PG, "psql", "-U", "postgres", "-At", "-F", "|", "-c", sql], capture_output=True, text=True).stdout.strip()
def pg_ready(t=60):
    for _ in range(t):
        if subprocess.run(["docker", "exec", lib.PG, "pg_isready", "-h", "127.0.0.1", "-U", "postgres"], capture_output=True).returncode == 0: return True
        time.sleep(1)
    return False
def start_stage():
    wait_free([STAGEP]); spawn("stage", [sys.executable, os.path.join(HERE_MF, "stage_server.py"), str(STAGEP), JOURNAL, MAIL], denv(), "stage.log"); assert up(ST_URL + "/mail_count?key=x"), "stage did not start"
def mf_stack(model_slow=None):
    for n in ("stage", "crm", "model", "catcher"): stop(n)
    wait_free([MODELP, STAGEP, CRMP, MAILP]); clean_state()
    for f in (JOURNAL, CRMLOG, MAIL + ".delay"):
        if os.path.exists(f): os.remove(f)
    e = denv()
    spawn("model", [sys.executable, "-m", "demo_only.fake_model_server", "--mode", "ok", "--port", str(MODELP), "--key-file", KEY, "--call-log", CALLS], e, "model.log")
    assert up(M + "/stats"), "model stand-in did not start"
    if model_slow: model_ctl(mode="slow", slow_seconds=model_slow)
    spawn("crm", [sys.executable, os.path.join(HERE_MF, "crm_stub.py"), str(CRMP), CRMLOG], os.environ.copy(), "crm.log", cwd=S)
    spawn("catcher", [sys.executable, os.path.join(HERE, "smtp_catcher.py"), str(MAILP), MAIL], os.environ.copy(), "catcher.log", cwd=S)
    start_stage(); time.sleep(1)
    psql("DROP TABLE IF EXISTS mf_leads;")
    psql("CREATE TABLE mf_leads(lead_key text PRIMARY KEY, email text, name text, state text NOT NULL DEFAULT 'new', mail_sent boolean NOT NULL DEFAULT false, label text, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());")
def crm_ctl(**kw):
    r = urllib.request.Request(CRM_URL + "/control", json.dumps(kw).encode(), {"Content-Type": "application/json"}, method="POST"); urllib.request.urlopen(r, timeout=5).read()
def n8n_prepare_mf():
    api.login(); inst = json.load(open(os.path.join(WORK, ".run", "instance.json")))
    c = api.call("POST", "/credentials", {"name": "mf-mail-smtp", "type": "smtp", "projectId": inst["project_id"],
         "data": {"user": "stand-in", "password": "stand-in", "host": "127.0.0.1", "port": MAILP, "secure": False, "disableStartTls": True, "hostName": ""}})
    d = c.get("data", c); assert "id" in d, c
    out = os.path.join(S, "mfflows"); subprocess.run([sys.executable, os.path.join(HERE_MF, "build_mainframe.py"), out, inst["pg_credential_id"], d["id"]], check=True, capture_output=True)
    res = {}
    for fn, nm in (("mf-form.json", "mf-form"), ("mf-hook.json", "mf-hook"), ("mf-recovery.json", "mf-recovery")): res[nm] = api.deploy(os.path.join(out, fn), nm)
    return res
def restart_n8n(): return n8n_restart(paths=("mf-form", "mf-hook"))
def kill_n8n_now(): return lib.kill_n8n_confirmed()
def req(path, body): return post(path, body, t=60)
def fbody(k): return form(k)             # submission_id = k, email = k@example.test
# ---- per-lead observation
def crm_rows(k): return sum(1 for r in json.loads(get(CRM_URL + "/rows")[1] or "{}").get("rows", []) if r.get("lead_key") == k)
def mails(k): return sum(1 for m in mail_rows() if k in m.get("subject", ""))
def model_calls(k): return sum(1 for c in jl(CALLS) if c.get("lead_id") == k)
def row(k):
    r = psql("SELECT state, mail_sent, coalesce(label,'') FROM mf_leads WHERE lead_key='%s';" % k).split("|")
    return {"state": r[0], "mail_sent": r[1] == "t", "label": r[2]} if len(r) == 3 else {"state": None}
def second_mail_count(k):
    try: return json.loads(get(ST_URL + "/mail_count?key=" + k)[1] or "{}").get("count")
    except Exception: return None
def outcome(k):
    r = row(k); o = {"row": r, "crm_rows": crm_rows(k), "mails": mails(k), "mails_second_count": second_mail_count(k), "model_calls": model_calls(k)}
    o["doubled"] = o["crm_rows"] > 1 or o["mails"] > 1 or o["model_calls"] > 1
    o["unknown"] = r["state"] == "unknown"
    o["lost"] = r["state"] is None or o["crm_rows"] == 0 or (o["mails"] == 0 and not o["unknown"]) or r["state"] not in ("done", "unknown")
    return o
def wait_final(k, t0, timeout=170):
    while time.time() - t0 < timeout:
        try:
            if row(k).get("state") in ("done", "unknown"): return round(time.time() - t0, 1)
        except Exception: pass
        time.sleep(1)
    return None
def watch(pred, timeout=40):
    t = time.time()
    while time.time() - t < timeout:
        if pred(): return True
        time.sleep(0.02)
    return False
def seen_in(path, k, key="lead_key"): return lambda: any(r.get(key) == k for r in jl(path))
def money_all(expected):
    calls = collections.Counter(c.get("lead_id") for c in jl(CALLS)); led = [r for r in jl(LEDGER) if r.get("op") == "reserve"]
    return {"expected_leads": expected, "model_calls_total": sum(calls.values()), "model_lead_ids": len(calls), "max_calls_per_lead_id": max(calls.values()) if calls else 0, "ledger_reserve_rows": len(led),
            "ok": len(calls) == expected and all(v == 1 for v in calls.values()) and len(led) == expected}
# ---- tests
def m0():
    mf_stack(); print("prepare", n8n_prepare_mf(), flush=True); restart_n8n(); ok = True; ks = []
    for path, mk in (("mf-form", form), ("mf-hook", hook)):
        k = uid(path); ks.append(k); st, rep = req(path, mk(k)); st2, rep2 = req(path, mk(k)); time.sleep(1); o = outcome(k)
        good = st == 200 and rep.get("verdict") == "new" and rep.get("repeat") is False and rep2.get("repeat") is True and rep2.get("verdict") == "new" and o["crm_rows"] == 1 and o["mails"] == 1 and o["model_calls"] == 1 and o["row"]["state"] == "done" and o["mails_second_count"] == 1
        ok &= good; rec("M0", entry=path, lead=k, first=[st, rep], repeat=[st2, rep2], outcome=o, ok=good)
    m = money_all(len(ks)); ok &= m["ok"]; rec("M0", money=m)
    result("M0", ok, "both entries: new lead -> done with a verdict; the repeat returns the stored state; 1 CRM row, 1 e-mail (both counts), 1 model call; money 1 per lead id")
def m1():
    mf_stack(); n8n_prepare_mf(); restart_n8n(); bursts = []; ok = True
    for b in range(3):
        k = uid("m1-%d" % (b + 1)); res = []; lk = threading.Lock()
        def one():
            st, rep = req("mf-form", fbody(k))
            with lk: res.append((st, rep.get("verdict") if isinstance(rep, dict) else None, rep.get("repeat") if isinstance(rep, dict) else None))
        th = [threading.Thread(target=one) for _ in range(10)]; [t.start() for t in th]; [t.join() for t in th]
        t0 = time.time(); wait_final(k, t0, 60); o = outcome(k); good = o["crm_rows"] == 1 and o["mails"] == 1 and o["model_calls"] == 1 and o["row"]["state"] == "done"; ok &= good
        rec("M1", burst=b + 1, lead=k, replies=collections.Counter(map(str, res)).most_common(), outcome=o, ok=good); bursts.append(k)
    m = money_all(3); ok &= m["ok"]; rec("M1", money=m)
    result("M1", ok, "3 bursts of 10 identical requests (production path): each 1 table row, 1 CRM row, 1 e-mail, 1 model call; money 1 per lead id")
def kill_case(test, point, setup, trigger, after_kill, model_slow=None, kill="n8n"):
    mf_stack(model_slow); n8n_prepare_mf(); restart_n8n(); rows = []; ks = []
    for i in range(REPS):
        k = uid("%s-%d" % (test.lower(), i + 1)); ks.append(k); setup(k)
        th = threading.Thread(target=lambda: req("mf-form", fbody(k))); th.start()
        hit = watch(trigger(k), 40); t0 = time.time()
        if hit: after_kill(k)
        th.join(timeout=70)
        # the caller sends the same request again right after the restart (take rule, first resend), then the recovery flow has its time
        st, rep = req("mf-form", fbody(k)); tdone = wait_final(k, t0); o = outcome(k)
        st3, rep3 = req("mf-form", fbody(k)); o["caller_resend_after_restart"] = [st, {x: rep.get(x) for x in ("n8n_error", "state", "verdict", "repeat")} if isinstance(rep, dict) else rep]
        o["resend_after_final"] = [st3, {x: rep3.get(x) for x in ("state", "verdict", "repeat")} if isinstance(rep3, dict) else rep3]
        o.update(lead=k, kill_point_reached=hit, seconds_kill_to_final=tdone); rows.append(o); rec(test, i=i + 1, **o)
    lost = sum(o["lost"] for o in rows); dbl = sum(o["doubled"] for o in rows); unk = sum(o["unknown"] for o in rows); ts = [o["seconds_kill_to_final"] for o in rows if o["seconds_kill_to_final"]]
    m = money_all(len(ks)); rec(test, money=m)
    why = "%s: %d kills: lost %d, doubled %d, unknown %d; recovery flow reached a final state in %s s (min/median/max) after the kill; mails delivered per lead %s; money %s" % (
        point, REPS, lost, dbl, unk, "%s/%s/%s" % (min(ts), statistics.median(ts), max(ts)) if ts else "none", [o["mails"] for o in rows], "ok" if m["ok"] else "NOT ok: %s" % m)
    result(test, lost == 0 and dbl == 0 and m["ok"] and all(o["kill_point_reached"] for o in rows), why, per_lead=rows)
def k1(): kill_case("K1", "n8n killed after the table insert, before the CRM write (CRM search held 6 s)", lambda k: crm_ctl(search_delay_ms=6000), lambda k: seen_in(CRMLOG, k), lambda k: (kill_n8n_now(), restart_n8n()))
def k2(): kill_case("K2", "n8n killed after the CRM write, before the mail step (CRM answer held 6 s after the row was stored)", lambda k: crm_ctl(create_ack_delay_ms=6000), lambda k: (lambda: any(r.get("op") == "create" and r.get("lead_key") == k for r in jl(CRMLOG))), lambda k: (kill_n8n_now(), restart_n8n()))
def k3():
    def setup(k): open(MAIL + ".delay", "w").write("6")
    def after(k):
        if os.path.exists(MAIL + ".delay"): os.remove(MAIL + ".delay")
        kill_n8n_now(); restart_n8n()
    kill_case("K3", "n8n killed after the mail was delivered (stored by the stand-in), before the table update (acknowledgement held 6 s)", setup, lambda k: (lambda: mails(k) >= 1), after)
def k4():
    def after(k):
        p = procs.pop("stage", None)
        if p:
            try: os.killpg(p.pid, signal.SIGKILL)
            except OSError: pass
            p.wait(timeout=5)
        time.sleep(5); start_stage()
    kill_case("K4", "desk stage killed mid-call (model stand-in slow 4 s; the stage is back 5 s after the kill)", lambda k: None, lambda k: (lambda: model_calls(k) >= 1), after, model_slow=4)
def k5():
    def setup(k): crm_ctl(create_ack_delay_ms=5000)
    def after(k):
        subprocess.run(["docker", "kill", lib.PG], capture_output=True); time.sleep(2); subprocess.run(["docker", "start", lib.PG], capture_output=True); assert pg_ready(), "postgres did not come back"
    kill_case("K5", "Postgres killed once while n8n waited for the CRM answer (container killed, started 2 s later)", setup, lambda k: (lambda: any(r.get("op") == "create" and r.get("lead_key") == k for r in jl(CRMLOG))), after)
TESTS = {"M0": m0, "M1": m1, "K1": k1, "K2": k2, "K3": k3, "K4": k4, "K5": k5}
if __name__ == "__main__":
    for t in sys.argv[1:]:
        try: TESTS[t]()
        except Exception as e: import traceback; traceback.print_exc(); result(t, False, "driver error: %s: %s" % (type(e).__name__, str(e)[:200]))
        finally: json.dump(RESULTS, open(os.path.join(WORK, "mf_result_%s.json" % "_".join(sys.argv[1:])), "w"), indent=1, default=str)
