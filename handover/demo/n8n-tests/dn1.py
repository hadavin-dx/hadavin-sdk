"""n8n door tests S1 (step 1 proof), S1B (before: the repository's original two flows, imported unmodified) and T1-T7. Runs inside a prepared harness work folder.
  python dn1.py S1 T1 ...        (see README.md for the exact commands and pass criteria). Made-up data only. Prints REC lines (raw) and RESULT lines (PASS or FAIL)."""
import sys, json, os, time, glob, threading, subprocess, uuid, collections
from dn1_common import *
RESULTS = {}
def result(test, passed, why, **raw):
    RESULTS[test] = {"pass": passed, "why": why, **raw}; print("RESULT %s %s %s" % (test, "PASS" if passed else "FAIL", why), flush=True)
def uid(p): return "%s-%s" % (p, uuid.uuid4().hex[:6])
def paths_ok(): return n8n_restart() if False else True
# ------------------------------------------------------------------ S1B: before (original flows, unmodified)
def s1b():
    stack(); inst = api.login()
    orig = os.path.join(ROOT, "n8n", "desk-form.json"); w = json.load(open(orig)); 
    r = api.deploy(orig, "orig-form"); rec("S1B", deploy=str(r)[:80])
    EXTRA["DESK_URL"] = D; n8n_restart(paths=("desk-form",))
    lead = uid("b1"); st, rep = post("desk-form", form(lead)); rec("S1B", case="desk up, new lead", http=st, reply=rep)
    stop("desk"); lead2 = uid("b2"); st2, rep2 = post("desk-form", form(lead2)); rec("S1B", case="desk down", http=st2, reply=rep2)
    shows = isinstance(rep, dict) and "desk_status" in rep
    err = isinstance(rep2, dict) and rep2.get("n8n_error") is True
    result("S1B", not (shows and err), "FAIL expected before the change: reply carries desk_status=%s, n8n_error on desk down=%s (the original flows pass the desk body only and a bare error)" % (shows, err), http_up=st, http_down=st2)
# ------------------------------------------------------------------ S1: step 1 proof
def s1():
    stack(); print("prepare", n8n_prepare(), flush=True); n8n_restart()
    cases = []; ok = True; leads = 0
    def chk(name, cond, **kw):
        nonlocal ok; ok &= bool(cond); cases.append(dict(case=name, ok=bool(cond), **kw)); rec("S1", case=name, ok=bool(cond), **kw)
    for door, path, mk in (("form", "desk-form", form), ("webhook", "desk-webhook", hook)):
        a = uid(door + "a"); st, rep = post(path, mk(a)); leads += 1
        chk("%s: new lead 201" % door, st == 200 and rep.get("desk_status") == 201 and rep.get("verdict") == "new" and rep.get("n8n_error") is False, http=st, reply=rep)
        st, rep = post(path, mk(a)); chk("%s: same id again 201 replayed" % door, rep.get("desk_status") == 201 and rep.get("desk", {}).get("replayed") is True, http=st, reply=rep)
        st, rep = post(path, mk(uid(door + "b"), email="%s@example.test" % a)); chk("%s: same e-mail other id 200 duplicate" % door, rep.get("desk_status") == 200 and rep.get("verdict") == "duplicate", http=st, reply=rep)
        st, rep = post(path, mk(uid(door + "c"), email="not-an-email")); chk("%s: bad e-mail 202 review" % door, rep.get("desk_status") == 202 and rep.get("verdict") == "review", http=st, reply=rep)
    n_ok = len(px())
    stop("desk"); before = len(px()); down = uid("down"); t0 = time.time(); st, rep = post("desk-form", form(down)); dt = round(time.time() - t0, 1)
    tries = [p for p in px()[before:] if p.get("ref") == down]
    chk("desk down: n8n_error true, no verdict, HTTP 502, 3 tries", st == 502 and isinstance(rep, dict) and rep.get("n8n_error") is True and "verdict" not in rep and "desk_status" not in rep and len(tries) == 3, http=st, reply=rep, tries=len(tries), secs=dt)
    start_desk(); k = uid("kill"); open(ROOT + "/data/crash.flag", "w").write("A"); st, rep = post("desk-form", form(k)); time.sleep(2)
    tries = [p for p in px() if p.get("ref") == k]
    chk("desk killed mid-request (point A): no verdict, n8n_error true", isinstance(rep, dict) and rep.get("n8n_error") is True and "verdict" not in rep, http=st, reply=rep, proxy=tries[:4])
    if "desk" in procs and procs["desk"].poll() is None: pass
    kill_desk_now(); start_desk(); at = take("desk-form", form(k)); leads += 1
    chk("after restart the caller's resend gets a verdict", has_verdict(at[-1][1]) if isinstance(at[-1][1], dict) and at[-1][1].get("verdict") else False, attempts=at)
    time.sleep(8); m = money(None or leads)
    # leads: 2 doors x (new lead + review lead processed? review does not call the model) -> expected computed from desk
    calls = collections.Counter(c.get("lead_id") for c in jl(CALLS)); chk("money: every model lead id called exactly once", all(v == 1 for v in calls.values()), calls=dict(calls), ledger_reserves=len([r for r in jl(LEDGER) if r.get("op") == "reserve"]))
    chk("money: ledger reserve rows == model lead ids", len([r for r in jl(LEDGER) if r.get("op") == "reserve"]) == len(calls))
    result("S1", ok, "%d of %d checks passed" % (sum(c["ok"] for c in cases), len(cases)), cases=cases)
# ------------------------------------------------------------------ T1 burst of 10, same lead id, production path
def t1():
    stack(); print("prepare", n8n_prepare(), flush=True); n8n_restart(); rows = []
    for b in range(1, 4):
        lead = uid("t1-%d" % b); email = lead + "@example.test"; res = [None] * 10; bar = threading.Barrier(10)
        def one(i):
            bar.wait(); res[i] = post("desk-form", form(lead))
        th = [threading.Thread(target=one, args=(i,)) for i in range(10)]; [t.start() for t in th]; [t.join() for t in th]
        late = []
        for i, (st, rep) in enumerate(res):
            if not has_verdict(rep): late.append(take("desk-form", form(lead)))
        time.sleep(10)
        dist = collections.Counter((st, rep.get("desk_status"), rep.get("verdict"), (rep.get("desk") or {}).get("replayed")) if isinstance(rep, dict) else (st, None, None, None) for st, rep in res)
        v = lead_view(email, lead); rows.append(rec("T1", burst=b, lead=lead, replies=[[list(k), n] for k, n in dist.items()], resend_attempts=late, desk=v, desk_requests=len([p for p in px() if p.get("ref") == lead])))
    m = money(3); rec("T1", money=m)
    good = all(r["desk"].get("leads") == 1 and r["desk"].get("crm_rows") == 1 and r["desk"].get("emails") == 1 and r["desk"].get("receipts") == 1 for r in rows) and m["ok"]
    result("T1", good, "3 bursts of 10 identical requests: each ended with 1 desk lead, 1 receipt, 1 CRM row, 1 e-mail; model calls 1 per lead id, ledger rows 1 per lead" if good else "see REC lines", rows=rows, money=m)
# ------------------------------------------------------------------ T2 n8n killed after it called the desk, before it answered
def t2():
    stack(slow=3); print("prepare", n8n_prepare(), flush=True); n8n_restart(); rows = []
    for i in range(1, 6):
        lead = uid("t2-%d" % i); email = lead + "@example.test"; box = {}
        th = threading.Thread(target=lambda: box.update(first=post("desk-form", form(lead), t=30))); th.start(); time.sleep(1.5)
        reqs_at_kill = len([p for p in px() if p.get("ref") == lead]) + 0
        killed = lib.kill_n8n_confirmed(); th.join(); ok = lib.start_n8n(None, paths=("desk-form", "desk-webhook")); time.sleep(2)
        at = take("desk-form", form(lead)); time.sleep(6)
        rows.append(rec("T2", i=i, lead=lead, killed_confirmed=killed, restarted=ok, first_call=[box["first"][0], None], resend_attempts=at, desk=lead_view(email, lead), desk_requests=len([p for p in px() if p.get("ref") == lead])))
    m = money(5); rec("T2", money=m)
    good = all(r["desk"].get("leads") == 1 and r["desk"].get("crm_rows") == 1 and r["desk"].get("emails") == 1 and has_verdict_attempt(r["resend_attempts"]) for r in rows) and m["ok"]
    result("T2", good, "5 of 5: n8n killed 1.5 s after the call (desk still working, model stand-in slow 3 s), restarted, the caller sent the same request again: 1 lead, 1 CRM row, 1 e-mail, a verdict in the reply; money 1 per lead" if good else "see REC lines", rows=rows, money=m)
def has_verdict_attempt(at): return bool(at) and isinstance(at[-1][1], dict) and bool(at[-1][1].get("verdict"))
# ------------------------------------------------------------------ T3 desk killed at A, C0, D2 keyed, D2 blind, D1b blind (through n8n)
def t3():
    rows = []; allok = True
    for point, kind in (("A", "keyed"), ("C0", "keyed"), ("D2", "keyed"), ("D2", "blind"), ("D1b", "blind")):
        stack(kind=kind); 
        if not rows: print("prepare", n8n_prepare(), flush=True); n8n_restart()
        series = []
        for i in range(1, 6):
            lead = uid("t3-%s%s-%d" % (point.lower(), kind[0], i)); email = lead + "@example.test"
            open(ROOT + "/data/crash.flag", "w").write(point); box = {}
            th = threading.Thread(target=lambda: box.update(first=post("desk-form", form(lead), t=45))); th.start()
            for _ in range(80):
                if procs["desk"].poll() is not None: break
                time.sleep(0.25)
            exit_code = procs["desk"].poll(); start_desk_after_exit()
            th.join(); first = box.get("first"); at = take("desk-form", form(lead)) if not has_verdict(first[1]) else []
            st2, rep2 = post("desk-form", form(lead)); time.sleep(12)
            series.append(rec("T3", point=point, kind=kind, i=i, desk_exit=exit_code, first=[first[0], {k: first[1].get(k) for k in ("n8n_error", "desk_status", "verdict")} if isinstance(first[1], dict) else None], resends=at, repeat=[st2, {k: rep2.get(k) for k in ("n8n_error", "desk_status", "verdict")} if isinstance(rep2, dict) else None], desk=lead_view(email, lead)))
        m = money(5); rec("T3", point=point, kind=kind, money=m)
        lost = sum(1 for r in series if r["desk"].get("leads") != 1 or r["desk"].get("receipts") != 1); dbl = sum(1 for r in series if r["desk"].get("crm_rows", 0) > 1 or r["desk"].get("emails", 0) > 1)
        ok = lost == 0 and dbl == 0 and m["ok"] and all(r["desk_exit"] == 137 for r in series)
        if point == "D1b": ok = ok and all(r["desk"].get("emails") == 0 and r["desk"].get("fu") == ["unknown"] for r in series)
        if kind == "blind" and point == "D2": ok = ok and all(r["desk"].get("emails") == 1 and r["desk"].get("fu") == ["unknown"] for r in series)
        rows.append({"point": point, "kind": kind, "lost": lost, "doubled": dbl, "money": m, "ok": ok}); allok &= ok
    result("T3", allok, "; ".join("%s %s: lost %d doubled %d money %s" % (r["point"], r["kind"], r["lost"], r["doubled"], "ok" if r["money"]["ok"] else "NOT ok") for r in rows), series=rows)
def start_desk_after_exit():
    procs.pop("desk", None); start_desk()
# ------------------------------------------------------------------ T4 slow desk, n8n timeout below the delay
def t4():
    rows = []
    stack(); print("prepare", n8n_prepare(), flush=True); n8n_restart(DESK_TIMEOUT_MS="2000")
    for delay in (1, 3, 8):
        model_ctl(mode="slow", slow_seconds=delay)
        for i in range(1, 4):
            lead = uid("t4-%ds-%d" % (delay, i)); email = lead + "@example.test"; t0 = time.time(); st, rep = post("desk-form", form(lead), t=60); dt = round(time.time() - t0, 1)
            tries = len([p for p in px() if p.get("ref") == lead]); time.sleep(delay + 2)
            at = [] if has_verdict(rep) else take("desk-form", form(lead))
            rows.append(rec("T4", delay=delay, i=i, first=[st, {k: rep.get(k) for k in ("n8n_error", "desk_status", "verdict")} if isinstance(rep, dict) else None], secs=dt, desk_requests_from_n8n=tries, resends=at, desk=lead_view(email, lead)))
    m = money(9); rec("T4", money=m)
    retry_fired = all(r["desk_requests_from_n8n"] >= 2 for r in rows if r["delay"] >= 3) and all(r["desk_requests_from_n8n"] == 1 for r in rows if r["delay"] == 1)
    one = all(r["desk"].get("leads") == 1 and r["desk"].get("crm_rows") == 1 and r["desk"].get("emails") == 1 for r in rows)
    result("T4", retry_fired and one and m["ok"], "retry fired for delays 3 and 8 (desk requests per lead >= 2: %s), 1 request at delay 1; every lead 1 desk lead/CRM row/e-mail: %s; money ok: %s" % (retry_fired, one, m["ok"]), rows=rows, money=m)
    EXTRA["DESK_TIMEOUT_MS"] = "15000"
# ------------------------------------------------------------------ T5 forced desk failure fires the error workflow exactly once
def t5():
    stack(); print("prepare", n8n_prepare(), flush=True); n8n_restart(); rows = []
    good = uid("t5ok"); post("desk-form", form(good)); time.sleep(4); m0 = len(mail_rows())
    stop("desk"); lead = uid("t5-fail"); st, rep = post("desk-form", form(lead, email=lead + "@example.test", name="Fail Person")); time.sleep(8)
    ms = mail_rows(); start_desk()
    rec("T5", ok_run_mails=m0, fail_reply=[st, rep], mails=ms)
    body = ms[0]["body"] if ms else ""
    checks = {"exactly one notification": len(ms) == 1, "fixed recipient only": all(m["to"] == [ALERT_TO] for m in ms), "no lead data (address, name) in the body": lead + "@example.test" not in body and "Fail Person" not in body,
              "lead id in the body": lead in body, "no n8n attribution": "n8n" not in body.lower().replace("lead desk door", ""), "ok run sent no notification": m0 == 0,
              "nothing sent to the lead's own address (desk e-mail stand-in)": per(lead + "@example.test")["emails"] == 0, "reply has no verdict, n8n_error true": isinstance(rep, dict) and rep.get("n8n_error") is True and "verdict" not in rep}
    m = money(1); rec("T5", checks=checks, money=m)
    result("T5", all(checks.values()) and m["ok"], "; ".join("%s=%s" % (k, v) for k, v in checks.items()) + "; money ok=%s" % m["ok"], checks=checks, mails=ms, money=m)
# ------------------------------------------------------------------ T6 n8n-only P1a / P1b (kill after the n8n insert, before the desk)
def t6():
    stack(); inst = json.load(open(os.path.join(WORK, ".run", "instance.json"))); api.login(); CRED = (inst["pg_credential_id"], "n8n-publish-pg")
    def psql(sql):
        p = subprocess.run(["docker", "exec", lib.PG, "psql", "-U", "postgres", "-At", "-c", sql], capture_output=True, text=True); return p.stdout.strip() + p.stderr.strip()
    psql("CREATE TABLE IF NOT EXISTS leads_skip (id serial PRIMARY KEY, lead_id text, note text); CREATE UNIQUE INDEX IF NOT EXISTS leads_skip_lead_id_uq ON leads_skip (lead_id);")
    import mkwf2
    def desk_http(pos): return {"parameters": {"method": "POST", "url": D + "/leads", "sendBody": True, "specifyBody": "json", "jsonBody": "={{ JSON.stringify($('Webhook').item.json.body) }}", "options": {}}, "name": "ToDesk", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": pos}
    WAIT = lambda: {"parameters": {"resume": "timeInterval", "amount": 4, "unit": "seconds"}, "name": "Wait4s", "type": "n8n-nodes-base.wait", "typeVersion": 1.1, "position": [440, 0], "webhookId": "t6-" + uuid.uuid4().hex[:8]}
    pg = {"parameters": {"operation": "insert", "schema": {"__rl": True, "mode": "list", "value": "public"}, "table": {"__rl": True, "mode": "name", "value": "leads_skip"}, "columns": {"mappingMode": "defineBelow", "value": {"lead_id": "={{ $json.body.source_ref }}", "note": "synthetic"}, "matchingColumns": [], "schema": []}, "options": {"skipOnConflict": True}}, "name": "PgInsert", "type": "n8n-nodes-base.postgres", "typeVersion": 2.5, "position": [220, 0], "credentials": {"postgres": {"id": CRED[0], "name": CRED[1]}}}
    IF = {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"}, "conditions": [{"id": "c1", "leftValue": "={{ $json.lead_id }}", "rightValue": "", "operator": {"type": "string", "operation": "notEmpty", "singleValue": True}}], "combinator": "and"}, "options": {}}, "name": "IsNew", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [660, 0]}
    DUP = {"parameters": {"mode": "runOnceForAllItems", "jsCode": "return [{json: {branch: 'duplicate'}}];"}, "name": "DupReply", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [880, 100]}
    wa = {"name": "t6-a", "nodes": [mkwf2.hook("t6-a", "t6a"), pg, WAIT(), IF, desk_http([880, -100]), DUP], "connections": {"Webhook": {"main": [[{"node": "PgInsert", "type": "main", "index": 0}]]}, "PgInsert": {"main": [[{"node": "Wait4s", "type": "main", "index": 0}]]}, "Wait4s": {"main": [[{"node": "IsNew", "type": "main", "index": 0}]]}, "IsNew": {"main": [[{"node": "ToDesk", "type": "main", "index": 0}], [{"node": "DupReply", "type": "main", "index": 0}]]}}, "settings": {}}
    wb = {"name": "t6-b", "nodes": [mkwf2.hook("t6-b", "t6b"), WAIT(), desk_http([660, 0])], "connections": {"Webhook": {"main": [[{"node": "Wait4s", "type": "main", "index": 0}]]}, "Wait4s": {"main": [[{"node": "ToDesk", "type": "main", "index": 0}]]}}, "settings": {}}
    for w in (wa, wb): json.dump(w, open(os.path.join(S, w["name"] + ".json"), "w")); print("deployed", w["name"], api.deploy(os.path.join(S, w["name"] + ".json"), w["name"]), flush=True)
    n8n_restart(paths=("t6-a", "t6-b")); rows = []
    for flavor, path in (("P1a n8n insert first", "t6-a"), ("P1b desk first", "t6-b")):
        for i in range(1, 6):
            sid = uid(path + "-%d" % i); email = sid + "@example.test"; env = {"source": "form", "source_ref": sid, "payload": {"name": "Test Person", "email": email, "company": "Example Ltd", "message": "made-up"}}
            box = {}; th = threading.Thread(target=lambda: box.update(first=post(path, env, t=25))); th.start(); time.sleep(1.5)
            killed = lib.kill_n8n_confirmed(); th.join(); ok = lib.start_n8n(None, paths=("t6-a", "t6-b")); time.sleep(2)
            at = take(path, env); time.sleep(10)
            rows.append(rec("T6", flavor=flavor, i=i, n8n_table_rows=psql("SELECT count(*) FROM leads_skip WHERE lead_id='%s'" % sid) if path == "t6-a" else "n/a", killed=killed, restarted=ok, first=[box["first"][0], None], resend_attempts=[[a[0], a[1]] for a in at], desk=lead_view(email, sid)))
    leads = sum(1 for r in rows if r["desk"].get("leads") == 1); m = money(leads); rec("T6", money=m)
    lost_a = sum(1 for r in rows if r["flavor"].startswith("P1a") and r["desk"].get("leads") == 0); ok_b = sum(1 for r in rows if r["flavor"].startswith("P1b") and r["desk"].get("leads") == 1 and r["desk"].get("emails") == 1)
    result("T6", lost_a == 5 and ok_b == 5 and m["ok"], "P1a lost %d of 5 (expected 5: the n8n insert made the resend a 'duplicate'); P1b %d of 5 got the lead through the caller's resend; money for the %d leads that reached the desk ok=%s" % (lost_a, ok_b, leads, m["ok"]), rows=rows, money=m)
# ------------------------------------------------------------------ T7 grep for planted address, name and fake key
def t7():
    stack(); print("prepare", n8n_prepare(), flush=True)
    keep = os.path.join(S, "flows", "desk-form-keep.json"); w = json.load(open(os.path.join(S, "flows", "desk-form-door.json"))); w["name"] = "door-form-keep (control: default execution saving)"; w["nodes"][0]["parameters"]["path"] = "desk-form-keep"; w["nodes"][0]["webhookId"] = "door-keep-wh"
    w["settings"] = {k: v for k, v in w["settings"].items() if not k.startswith("save")}; json.dump(w, open(keep, "w")); print("control deployed", api.deploy(keep, "door-keep"), flush=True)
    n8n_restart(paths=("desk-form", "desk-webhook", "desk-form-keep")); lead = uid("t7")
    st1, r1 = post("desk-form", form(lead, email=PLANT_EMAIL, name=PLANT_NAME)); st2, r2 = post("desk-form-keep", form(lead + "k", email="k." + PLANT_EMAIL, name=PLANT_NAME))
    stop("desk"); st3, r3 = post("desk-form", form(lead + "f", email="f." + PLANT_EMAIL, name=PLANT_NAME)); time.sleep(6); start_desk()
    time.sleep(2); lib.kill_n8n_confirmed()                                      # stop n8n so its database file is complete on disk
    needles = {"address": "planted.t7@example.test", "name": PLANT_NAME, "key": KEYTEXT}; places = {}
    def scan(label, paths):
        found = {n: 0 for n in needles}
        for p in paths:
            try: data = open(p, "rb").read()
            except OSError: continue
            for n, v in needles.items(): found[n] += data.count(v.encode())
        places[label] = found
    scan("n8n database file(s)", glob.glob(os.path.join(WORK, "n8nhome", "**", "database.sqlite*"), recursive=True))
    scan("n8n log", [os.path.join(WORK, "n8n2.log")]); scan("exported flow JSON (door and notifier)", [p for p in glob.glob(os.path.join(S, "flows", "*.json")) if "keep" not in p])
    scan("n8n user folder, every other file", [p for p in glob.glob(os.path.join(WORK, "n8nhome", "**", "*"), recursive=True) if os.path.isfile(p) and "database.sqlite" not in p])
    scan("notifier mail file", [MAIL])
    # control: the execution of the keep flow stores the lead in the database; the door flows (saving off) must not
    rec("T7", replies=[[st1, r1], [st2, r2], [st3, r3]], places=places)
    bad = [(l, n) for l, f in places.items() for n, c in f.items() if c and l != "n8n database file(s)"] + [("n8n database file(s)", "key")] * bool(places["n8n database file(s)"]["key"])
    db_addr = places["n8n database file(s)"]["address"]
    result("T7", not bad and True, "planted address/name/fake key found: %s. n8n database: address %d, name %d, key %d (the control flow with default saving is one execution; the door flows save no execution data). NOTE: the database count includes the control flow's execution, see raw." % (bad or "nowhere outside the database", db_addr, places["n8n database file(s)"]["name"], places["n8n database file(s)"]["key"]), places=places)
if __name__ == "__main__":
    api.login() if False else None
    fn = {"S1B": s1b, "S1": s1, "T1": t1, "T2": t2, "T3": t3, "T4": t4, "T5": t5, "T6": t6, "T7": t7}
    try:
        for name in sys.argv[1:]:
            print(">> %s %s" % (name, time.strftime("%H:%M:%SZ", time.gmtime())), flush=True)
            try: fn[name]()
            except Exception as e:
                import traceback; traceback.print_exc(); result(name, False, "test crashed: %s: %s" % (type(e).__name__, str(e)[:200]))
    finally:
        stop_desk_side(); json.dump(RESULTS, open("dn1_result_%s.json" % "_".join(sys.argv[1:]), "w"), indent=1, default=str); print("dn1 done", flush=True)
