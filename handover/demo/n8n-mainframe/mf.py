"""D-N2 / D-N2a tests: Design A (n8n as the main frame, lease claim, create-or-update CRM, one CRM+mail sub-workflow) on the real n8n 2.46.6 with stand-ins (made-up data, loopback only, no spend).
Runs inside a prepared harness work folder (see README.md).   python mf.py M0 M1 K1 K2 K3 K3B K4 K5 T8 T9 T10 T11 T12 T13
  env MF_REPS = kills per point (default 20), MF_LEASE = lease seconds used by the TESTS (default 20; the design value is 120, see README).
COUNTS ARE TAKEN OUTSIDE THE FLOW: this driver reads the CRM stand-in, the mail stand-in's file and the model call log after each run; expected set (lead ids sent) against observed set; extras count as failures.
Prints REC (raw) and RESULT lines; writes mf_result_<tests>.json."""
import sys, os, json, time, subprocess, threading, uuid, collections, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "n8n-tests"))
from dn1_common import *
HERE_MF = os.path.dirname(os.path.abspath(__file__))
STAGEP, CRMP = 8770, 8771
ST_URL, CRM_URL = "http://127.0.0.1:%d" % STAGEP, "http://127.0.0.1:%d" % CRMP
JOURNAL, CRMLOG = os.path.join(S, "stage-journal.jsonl"), os.path.join(S, "crm.log.jsonl")
REPS = int(os.environ.get("MF_REPS", "20")); LEASE = int(os.environ.get("MF_LEASE", "20")); RESULTS = {}
MAIL_TO, ALERT_TO = "intake@example.test", "alerts@example.test"
EXTRA.update(MF_CRM_URL=CRM_URL, MF_STAGE_URL=ST_URL, MF_STAGE_TIMEOUT_MS="15000")
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
def ctl(url, **kw):
    r = urllib.request.Request(url + "/control", json.dumps(kw).encode(), {"Content-Type": "application/json"}, method="POST"); urllib.request.urlopen(r, timeout=5).read()
def crm_ctl(**kw): ctl(CRM_URL, **kw)
def stage_ctl(**kw): ctl(ST_URL, **kw)
def mf_stack(model_slow=None):
    for n in ("stage", "crm", "model", "catcher"): stop(n)
    wait_free([MODELP, STAGEP, CRMP, MAILP]); clean_state()
    for f in (JOURNAL, CRMLOG) + tuple(MAIL + s for s in (".delay", ".pre", ".drop", ".conn")):
        if os.path.exists(f): os.remove(f)
    e = denv()
    spawn("model", [sys.executable, "-m", "demo_only.fake_model_server", "--mode", "ok", "--port", str(MODELP), "--key-file", KEY, "--call-log", CALLS], e, "model.log")
    assert up(M + "/stats"), "model stand-in did not start"
    if model_slow: model_ctl(mode="slow", slow_seconds=model_slow)
    spawn("crm", [sys.executable, os.path.join(HERE_MF, "crm_stub.py"), str(CRMP), CRMLOG], os.environ.copy(), "crm.log", cwd=S)
    spawn("catcher", [sys.executable, os.path.join(HERE, "smtp_catcher.py"), str(MAILP), MAIL], os.environ.copy(), "catcher.log", cwd=S)
    start_stage(); time.sleep(1)
    psql("DROP TABLE IF EXISTS mf_leads;")
    psql("CREATE TABLE mf_leads(lead_key text PRIMARY KEY, email text, name text, state text NOT NULL DEFAULT 'new' CHECK (state IN ('new','processing','done','review','unknown','failed')), claimed_until timestamptz, claim_token text, "
         "attempts int NOT NULL DEFAULT 0, crm_id text, mail_sent boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());")
def n8n_prepare_mf(recovery_copies=1):
    api.login(); inst = json.load(open(os.path.join(WORK, ".run", "instance.json")))
    c = api.call("POST", "/credentials", {"name": "mf-mail-smtp", "type": "smtp", "projectId": inst["project_id"],
         "data": {"user": "stand-in", "password": "stand-in", "host": "127.0.0.1", "port": MAILP, "secure": False, "disableStartTls": True, "hostName": ""}})
    d = c.get("data", c); assert "id" in d, c
    out = os.path.join(S, "mfflows"); res = {}
    def build(subid): subprocess.run([sys.executable, os.path.join(HERE_MF, "build_mainframe.py"), out, inst["pg_credential_id"], d["id"], subid, str(LEASE)], check=True, capture_output=True)
    build("PLACEHOLDER"); res["sub"] = api.deploy(os.path.join(out, "mf-sub-crm-mail.json"), "mf-sub"); subid = res["sub"][0]; assert isinstance(subid, str), res
    build(subid)
    for fn, nm in (("mf-form.json", "mf-form"), ("mf-hook.json", "mf-hook"), ("mf-recovery.json", "mf-recovery")): res[nm] = api.deploy(os.path.join(out, fn), nm)
    for i in range(2, recovery_copies + 1): res["mf-recovery%d" % i] = api.deploy(os.path.join(out, "mf-recovery.json"), "mf-recovery%d" % i)
    return res
def restart_n8n(**env): return n8n_restart(paths=("mf-form", "mf-hook"), **env)
def kill_n8n_now(): return lib.kill_n8n_confirmed()
def req(path, body, t=75): return post(path, body, t=t)
def fbody(k, email=None): return form(k, email)
# ---- observation, taken OUTSIDE the flow
def crm_rows(k): return sum(1 for r in json.loads(get(CRM_URL + "/rows")[1] or "{}").get("rows", []) if r.get("lead_key") == k)
def mail_keys():
    c = collections.Counter()
    for m in mail_rows():
        s = m.get("subject", "")
        if s.startswith("[demo] lead "): c[s[len("[demo] lead "):]] += 1
    return c
def alerts(k): return sum(1 for m in mail_rows() if ALERT_TO in m.get("to", []) and k in m.get("subject", ""))
def mails(k): return mail_keys().get(k, 0)
def smtp_conns(): return len(jl(MAIL + ".conn"))
def model_calls(k): return sum(1 for c in jl(CALLS) if c.get("lead_id") == k)
def row(k):
    r = psql("SELECT state, mail_sent, '', attempts, coalesce(crm_id,'') FROM mf_leads WHERE lead_key='%s';" % k).split("|")
    return {"state": r[0], "mail_sent": r[1] == "t", "attempts": int(r[3]), "has_crm_id": bool(r[4])} if len(r) == 5 else {"state": None}
def outcome(k):
    r = row(k); o = {"row": r, "crm_rows": crm_rows(k), "mails": mails(k), "alerts": alerts(k), "model_calls": model_calls(k)}
    o["doubled"] = o["crm_rows"] > 1 or o["mails"] > 1 or o["model_calls"] > 1 or o["alerts"] > 1
    o["unknown"] = r["state"] == "unknown"
    o["lost"] = r["state"] not in ("done", "unknown", "failed") or (r["state"] == "done" and (o["crm_rows"] != 1 or o["mails"] != 1))
    return o
def wait_final(k, t0, timeout=200):
    while time.time() - t0 < timeout:
        try:
            if row(k).get("state") in ("done", "unknown", "failed", "review"): return round(time.time() - t0, 1)
        except Exception: pass
        time.sleep(1)
    return None
def watch(pred, timeout=40):
    t = time.time()
    while time.time() - t < timeout:
        try:
            if pred(): return True
        except Exception: pass
        time.sleep(0.02)
    return False
def crm_seen(k, op): return lambda: any(r.get("op") == op and r.get("lead_key") == k for r in jl(CRMLOG))
def sets_check(expected):
    """expected set (lead ids sent) against observed sets (mail stand-in, CRM stand-in, model log); extras count as failures"""
    mk = set(mail_keys()); crm = {r.get("lead_key") for r in json.loads(get(CRM_URL + "/rows")[1] or "{}").get("rows", [])}; mod = {c.get("lead_id") for c in jl(CALLS)}; ex = set(expected)
    return {"mail_extras": sorted(mk - ex), "crm_extras": sorted(crm - ex), "model_extras": sorted(mod - ex)}
def money_all(expected_ids):
    calls = collections.Counter(c.get("lead_id") for c in jl(CALLS)); led = [r for r in jl(LEDGER) if r.get("op") == "reserve"]; n = len(expected_ids)
    return {"expected_leads": n, "model_calls_total": sum(calls.values()), "model_lead_ids": len(calls), "max_calls_per_lead_id": max(calls.values()) if calls else 0, "ledger_reserve_rows": len(led),
            "ok": len(calls) == n and all(v == 1 for v in calls.values()) and len(led) == n}
def summarize(test, point, rows, ids, extra_ok=True, **kw):
    lost = sum(o["lost"] for o in rows); dbl = sum(o["doubled"] for o in rows); unk = sum(o["unknown"] for o in rows); fail = sum(o["row"]["state"] == "failed" for o in rows)
    ts = [o["seconds_kill_to_final"] for o in rows if o.get("seconds_kill_to_final")]; m = money_all(ids); se = sets_check(ids); rec(test, money=m, sets=se)
    extras = any(se.values()); hit = all(o.get("kill_point_reached", True) for o in rows)
    why = "%s: sample %d: lost %d, doubled %d, unknown %d (mail delivered in %d of them), failed %d; recovery reached a final state in %s s (min/median/max) after the kill; extras in the outside count: %s; money %s" % (
        point, len(rows), lost, dbl, unk, sum(1 for o in rows if o["unknown"] and o["mails"]), fail, "%s/%s/%s" % (min(ts), statistics.median(ts), max(ts)) if ts else "none", "NONE" if not extras else se, "ok" if m["ok"] else "NOT ok: %s" % m)
    result(test, lost == 0 and dbl == 0 and m["ok"] and not extras and hit and extra_ok, why, per_lead=rows, **kw)
# ---- tests
def m0():
    mf_stack(); print("prepare", n8n_prepare_mf(), flush=True); restart_n8n(); ok = True; ks = []
    for path, mk in (("mf-form", form), ("mf-hook", hook)):
        k = uid(path); ks.append(k); st, rep = req(path, mk(k)); st2, rep2 = req(path, mk(k)); time.sleep(1); o = outcome(k)
        good = st == 200 and rep.get("verdict") == "new" and rep2.get("verdict") == "done" and rep2.get("repeat") is True and o["crm_rows"] == 1 and o["mails"] == 1 and o["model_calls"] == 1 and o["row"]["state"] == "done"
        ok &= good; rec("M0", entry=path, lead=k, first=[st, rep], repeat=[st2, rep2], outcome=o, ok=good)
    k = uid("rev"); st, rep = req("mf-form", form(k, email="not-an-email")); o = outcome(k); good = rep.get("verdict") == "review" and o["row"]["state"] == "review" and o["mails"] == 0 and o["crm_rows"] == 0 and o["model_calls"] == 0
    ok &= good; rec("M0", case="invalid e-mail -> review, no CRM, no mail, no model call", lead=k, reply=[st, rep], outcome=o, ok=good)
    m = money_all(ks); se = sets_check(ks + [k]); ok &= m["ok"] and not se["mail_extras"]; rec("M0", money=m, sets=se)
    result("M0", ok, "both entries: new lead -> verdict new, state done; repeat -> verdict done without new work; invalid e-mail -> review with no CRM, mail or model call; 1 CRM row, 1 e-mail, 1 model call per lead; extras none")
def m1():
    mf_stack(); n8n_prepare_mf(); restart_n8n(); ids = []; rows = []
    for b in range(3):
        k = uid("m1-%d" % (b + 1)); ids.append(k); res = []; lk = threading.Lock()
        def one():
            st, rep = req("mf-form", fbody(k))
            with lk: res.append((st, rep.get("verdict") if isinstance(rep, dict) else None))
        th = [threading.Thread(target=one) for _ in range(10)]; [t.start() for t in th]; [t.join() for t in th]
        wait_final(k, time.time(), 60); o = outcome(k); o["replies"] = collections.Counter(map(str, res)).most_common(); o["lead"] = k; rows.append(o); rec("M1", burst=b + 1, **o)
    summarize("M1", "3 bursts of 10 identical requests (production path)", rows, ids)
def kill_case(test, point, setup, trigger, after_kill, model_slow=None, label=None):
    mf_stack(model_slow); n8n_prepare_mf(); restart_n8n(); rows = []; ids = []
    for i in range(REPS):
        k = uid("%s-%d" % (test.lower(), i + 1)); ids.append(k); setup(k)
        th = threading.Thread(target=lambda: req("mf-form", fbody(k))); th.start()
        hit = watch(trigger(k), 40); t0 = time.time()
        if hit: after_kill(k)
        th.join(timeout=80)
        st, rep = req("mf-form", fbody(k)); tdone = wait_final(k, t0); o = outcome(k)             # the caller sends the same request again once n8n is back (take rule); the lease then lapses and recovery takes the rest
        st3, rep3 = req("mf-form", fbody(k)); o["caller_resend_after_restart"] = [st, rep.get("verdict") if isinstance(rep, dict) else rep]; o["resend_after_final"] = [st3, rep3.get("verdict") if isinstance(rep3, dict) else rep3]
        o.update(lead=k, kill_point_reached=hit, seconds_kill_to_final=tdone); rows.append(o); rec(test, i=i + 1, **o)
    summarize(test, point, rows, ids)
def k1(): kill_case("K1", "n8n killed after the claim insert, before the CRM write (CRM request held 6 s before it is stored)", lambda k: crm_ctl(upsert_delay_ms=6000), lambda k: crm_seen(k, "upsert_start"), lambda k: (kill_n8n_now(), restart_n8n()))
def k2(): kill_case("K2", "n8n killed after the CRM write, before the mail step (CRM answer held 6 s after the row was stored)", lambda k: crm_ctl(upsert_ack_delay_ms=6000), lambda k: crm_seen(k, "upsert"), lambda k: (kill_n8n_now(), restart_n8n()))
def k3b():
    def setup(k): open(MAIL + ".pre", "w").write("6")
    def after(k):
        if os.path.exists(MAIL + ".pre"): os.remove(MAIL + ".pre")
        kill_n8n_now(); restart_n8n()
    kill_case("K3B", "n8n killed after mail_sent was set, while the SMTP node was connecting (stand-in holds the greeting 6 s), mail NOT yet delivered", setup, lambda k: (lambda: smtp_conns() >= 1 and psql("SELECT mail_sent FROM mf_leads WHERE lead_key='%s';" % k) == "t"), after)
def k3():
    def setup(k): open(MAIL + ".delay", "w").write("6")
    def after(k):
        if os.path.exists(MAIL + ".delay"): os.remove(MAIL + ".delay")
        kill_n8n_now(); restart_n8n()
    kill_case("K3", "n8n killed after the mail was delivered (stored by the stand-in), before the table update (acknowledgement held 6 s)", setup, lambda k: (lambda: mails(k) >= 1), after)
def kill_stage_now():
    p = procs.pop("stage", None)
    if p:
        try: os.killpg(p.pid, signal.SIGKILL)
        except OSError: pass
        p.wait(timeout=5)
def k4(): kill_case("K4", "desk stage killed mid-call (model stand-in slow 4 s; the stage is back 5 s after the kill)", lambda k: None, lambda k: (lambda: model_calls(k) >= 1), lambda k: (kill_stage_now(), time.sleep(5), start_stage()), model_slow=4)
def k5():
    def after(k):
        subprocess.run(["docker", "kill", lib.PG], capture_output=True); time.sleep(2); subprocess.run(["docker", "start", lib.PG], capture_output=True); assert pg_ready(), "postgres did not come back"
    kill_case("K5", "Postgres killed once while n8n waited for the CRM answer (stopped without clean shutdown, started 2 s later)", lambda k: crm_ctl(upsert_ack_delay_ms=5000), lambda k: crm_seen(k, "upsert"), after)
def final_rows(ids, timeout=230):
    t0 = time.time(); rows = []
    for k in ids:
        wait_final(k, t0, timeout); o = outcome(k); o["lead"] = k; o["seconds_kill_to_final"] = round(time.time() - t0, 1); rows.append(o)
    return rows
def t8():
    mf_stack(); n8n_prepare_mf(); restart_n8n(); ids = []; rows = []; conn0 = smtp_conns()
    for mode in ("refuse", "error", "timeout"):
        stage_ctl(mode=mode, sleep=40); k = uid("t8-" + mode); ids.append(k); t0 = time.time(); st, rep = req("mf-form", fbody(k), t=120)
        rec("T8", mode=mode, lead=k, reply=[st, rep], seconds=round(time.time() - t0, 1))
    stage_ctl(mode="ok"); rows = final_rows(ids); [rec("T8", **o) for o in rows]
    ok = all(o["row"]["state"] == "failed" and o["mails"] == 0 and o["crm_rows"] == 0 and o["alerts"] == 1 and o["model_calls"] == 0 for o in rows) and smtp_conns() - conn0 == len(ids)   # only the alert mails connect: 1 per lead
    rec("T8", smtp_connections_total=smtp_conns(), alert_mails=len(ids))
    result("T8", ok, "cap stage refuses / errors / times out (also through the recovery retries, 3 tries): 0 mails to the intake recipient, 0 CRM writes, 0 model calls, state failed, exactly 1 alert per lead; SMTP connections = alerts only (%d)" % (smtp_conns() - conn0), per_lead=rows)
def t9():
    mf_stack(); n8n_prepare_mf(); restart_n8n(); ids = []; bad = []
    cases = [("evil1", {"email": "attacker@example.test\r\nBcc: evil@example.test", "name": "x"}), ("evil2", {"email": "a@example.test", "name": "to: evil@example.test"}), ("evil3", {"email": "a@example.test", "name": "x", "to": "evil@example.test", "recipient": "evil@example.test"})]
    for nm, f in cases:
        k = uid("t9-" + nm); ids.append(k); b = form(k, email=f["email"], name=f["name"]); b.update({x: f[x] for x in ("to", "recipient") if x in f}); st, rep = req("mf-form", b); rec("T9", case=nm, reply=[st, rep])
    k = uid("t9-subj"); st, rep = req("mf-form", form(k + "\r\nBcc: evil@example.test", email="ok@example.test")); rec("T9", case="lead id with a line break and a header", reply=[st, rep])
    time.sleep(3); rcpts = [r for m in mail_rows() for r in m.get("to", [])]; hdrs = [h for m in mail_rows() for h in m.get("headers", [])]
    ok = all(r == MAIL_TO for r in rcpts) and "Bcc" not in hdrs and len(rcpts) >= 1
    rec("T9", recipients_seen=sorted(set(rcpts)), headers_seen=sorted(set(hdrs)), mails=len(mail_rows()))
    result("T9", ok, "no input field changed the recipient: every mail went to the constant recipient only (%s); no injected header (Bcc) in any mail" % sorted(set(rcpts)))
def t10():
    rows = []; ids = []; mf_stack(); n8n_prepare_mf(); restart_n8n()
    for i in range(max(3, min(REPS, 5))):
        for kind in ("crm", "smtp"):
            k = uid("t10%s-%d" % (kind, i + 1)); ids.append(k)
            if kind == "crm": crm_ctl(upsert_ack_delay_ms=40000)
            else: open(MAIL + ".delay", "w").write("40")
            th = threading.Thread(target=lambda: req("mf-form", fbody(k), t=120)); th.start(); t0 = time.time()
            watch(crm_seen(k, "upsert") if kind == "crm" else (lambda: mails(k) >= 1), 60)
            if os.path.exists(MAIL + ".delay"): os.remove(MAIL + ".delay")
            th.join(timeout=100); tf = wait_final(k, t0, 120); time.sleep(3); o = outcome(k); o.update(lead=k, held=kind, seconds_kill_to_final=tf); rows.append(o); rec("T10", **o)
    ok = all(o["crm_rows"] == 1 and o["model_calls"] == 1 and o["mails"] == 1 and not o["doubled"] for o in rows)
    summarize("T10", "main run held 40 s (CRM answer, then SMTP acknowledgement) with a %d s lease while recovery fires (no kill)" % LEASE, rows, ids, extra_ok=ok)
def t11():
    mf_stack(); n8n_prepare_mf(recovery_copies=2); restart_n8n(); ids = []
    crm_ctl(upsert_ack_delay_ms=8000)
    for i in range(8):
        k = uid("t11-%d" % (i + 1)); ids.append(k); threading.Thread(target=lambda k=k: req("mf-form", fbody(k), t=100)).start(); time.sleep(0.2)
    time.sleep(3); kill_n8n_now(); restart_n8n(); t0 = time.time(); rows = final_rows(ids); [rec("T11", **o) for o in rows]
    summarize("T11", "8 leads in flight, n8n killed, restarted; TWO recovery workflows run at the same time (same schedule)", rows, ids)
def t12():
    mf_stack(); n8n_prepare_mf(); restart_n8n(); ids = []; rows = []
    for i in range(max(3, min(REPS, 5))):
        open(MAIL + ".drop", "w").write("1"); k = uid("t12-%d" % (i + 1)); ids.append(k); st, rep = req("mf-form", fbody(k)); t0 = time.time(); tf = wait_final(k, t0, 120); time.sleep(5); o = outcome(k); o.update(lead=k, reply=[st, rep.get("verdict") if isinstance(rep, dict) else rep], seconds_kill_to_final=tf); rows.append(o); rec("T12", **o)
    ok = all(o["mails"] == 1 and o["row"]["state"] == "unknown" and o["alerts"] == 1 and o["crm_rows"] == 1 for o in rows)
    summarize("T12", "SMTP stand-in accepts the mail then drops the connection (fault mode): expected 1 mail, state unknown, 1 alert, no resend", rows, ids, extra_ok=ok)
def t13():
    mf_stack(); n8n_prepare_mf(); restart_n8n(); ids = []
    # (a) duplicate webhook delivery of one lead id (two at once, then a third later); (b) Postgres killed mid-burst of 12 leads; (c) n8n restarted with half-done runs
    dup = uid("t13dup"); ids.append(dup); out = []; th = [threading.Thread(target=lambda: out.append(req("mf-form", fbody(dup)))) for _ in range(3)]; [t.start() for t in th]; [t.join() for t in th]
    crm_ctl(upsert_ack_delay_ms=6000)
    for i in range(12):
        k = uid("t13b-%d" % (i + 1)); ids.append(k); threading.Thread(target=lambda k=k: req("mf-form", fbody(k), t=100)).start(); time.sleep(0.15)
    time.sleep(3); subprocess.run(["docker", "kill", lib.PG], capture_output=True); time.sleep(3); subprocess.run(["docker", "start", lib.PG], capture_output=True); pg_ready()
    time.sleep(5); kill_n8n_now(); restart_n8n(); rows = final_rows(ids); [rec("T13", **o) for o in rows]
    summarize("T13", "duplicate delivery of one lead id (3 at once), Postgres killed mid-burst of 12 leads, then n8n killed and restarted with half-done runs", rows, ids)
TESTS = {"M0": m0, "M1": m1, "K1": k1, "K2": k2, "K3": k3, "K3B": k3b, "K4": k4, "K5": k5, "T8": t8, "T9": t9, "T10": t10, "T11": t11, "T12": t12, "T13": t13}
if __name__ == "__main__":
    for t in sys.argv[1:]:
        try: TESTS[t]()
        except Exception as e: import traceback; traceback.print_exc(); result(t, False, "driver error: %s: %s" % (type(e).__name__, str(e)[:200]))
        finally:
            for n in list(procs): stop(n)           # stop every stand-in this run started (the next run needs the ports)
            json.dump(RESULTS, open(os.path.join(WORK, "mf_result_%s.json" % "_".join(sys.argv[1:])), "w"), indent=1, default=str)
