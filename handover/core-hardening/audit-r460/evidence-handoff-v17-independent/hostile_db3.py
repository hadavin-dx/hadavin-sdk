"""Independent hostile tests for the v17 DB-3 file (spend_guarded_writes.sql). Written by the evidence runner, not the builder.
Usage: python hostile_db3.py <socket_dir> <src_dir> <held_v17> <held_v16>   (admin password in HV_ADMIN_PW). Prints OBS lines (what happened) and
EXPECT lines (PASS/FAIL against the stated safety property). Made-up data only. It never judges beyond the stated property."""
import sys, os, time, shutil, tempfile, secrets, threading
from datetime import date
from decimal import Decimal
from pathlib import Path
sock, src, H17, H16 = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, src)
import psycopg
from psycopg import sql
import hadavin_sdk.store.migrate as m
D, MO = date(2026, 11, 16), date(2026, 11, 1)
PW = {"postgres": os.environ["HV_ADMIN_PW"]}
admin = psycopg.connect(f"host={sock} dbname=postgres user=postgres password={PW['postgres']}", autocommit=True)
for r in ("migr17", "rt17", "op17"):
    PW[r] = secrets.token_hex(16)
    admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(r), sql.Literal(PW[r])))
def dsn(u, db, extra=""): return f"host={sock} dbname={db} user={u} password={PW[u]} {extra}"
res = []
def expect(name, ok, detail=""):
    res.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)
def obs(s): print("OBS " + s, flush=True)
def code(fn):
    try: fn(); return None
    except psycopg.Error as e: return str(e.sqlstate)
def build(db, names, with_log=True):
    admin.execute(f"CREATE DATABASE {db} OWNER migr17")
    tmp = Path(tempfile.mkdtemp(prefix="hv17ind_"))
    for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmp / p.name)
    for f, n in names: shutil.copy(H17 / f, tmp / f"{n}.sql")
    for k in ("spend_decrease_log", "kill_switch_log"):
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if any("decrease_log" in f for f, _ in names) else m.GRANTS.pop(k, None))
    m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
    m.migrate(dsn("migr17", db), runtime_role="rt17")
    mg = psycopg.connect(dsn("migr17", db), autocommit=True)
    obs("grants before DB-3 hardening for rt17: " + str(mg.execute("SELECT table_name, string_agg(privilege_type, ',' ORDER BY privilege_type) FROM information_schema.role_table_grants WHERE grantee='rt17' AND table_name IN ('spend','spend_month','kill_switch') GROUP BY 1 ORDER BY 1").fetchall()))
    mg.execute("REVOKE INSERT, UPDATE ON spend, spend_month, kill_switch FROM rt17")
    mg.execute("GRANT EXECUTE ON FUNCTION spend_reserve(text, date, date, numeric), spend_settle(text, date, date, numeric, numeric), kill_switch_engage() TO rt17")
    mg.execute("GRANT EXECUTE ON FUNCTION kill_switch_engage(), kill_switch_release() TO op17")
    return mg, tmp
mg, tmp = build("h1", [("spend_decrease_log.sql", "0006_dec"), ("spend_guarded_writes.sql", "0007_guard")])
rt = psycopg.connect(dsn("rt17", "h1"), autocommit=True)
op = psycopg.connect(dsn("op17", "h1"), autocommit=True)
obs("rt17 remaining table privileges on spend/spend_month/kill_switch: " + str(mg.execute("SELECT table_name, string_agg(privilege_type, ',' ORDER BY privilege_type) FROM information_schema.role_table_grants WHERE grantee='rt17' AND table_name IN ('spend','spend_month','kill_switch','spend_decrease_log','kill_switch_log') GROUP BY 1 ORDER BY 1").fetchall()))
def tot(ag="a"):
    return mg.execute("SELECT usd, open_usd FROM spend WHERE agent_id=%s AND day=%s", (ag, D)).fetchone()
def mtot(ag="a"):
    return mg.execute("SELECT usd, open_usd FROM spend_month WHERE agent_id=%s AND month=%s", (ag, MO)).fetchone()
R = lambda ag, w, c=rt: c.execute("SELECT * FROM spend_reserve(%s,%s,%s,%s)", (ag, D, MO, w)).fetchone()
S = lambda ag, w, a, c=rt: c.execute("SELECT * FROM spend_settle(%s,%s,%s,%s,%s)", (ag, D, MO, w, a)).fetchone()

# ---- A. lower a settled total
R("a", Decimal("10")); S("a", Decimal("10"), Decimal("4"))      # settled 4, open 0
expect("A0 baseline: reserve 10, settle with actual 4 -> usd 4 open 0", tot() == (Decimal("4"), Decimal("0")), str(tot()))
for label, fn in (
    ("direct UPDATE spend SET usd=0", lambda: rt.execute("UPDATE spend SET usd = 0")),
    ("direct UPDATE spend_month SET usd=0", lambda: rt.execute("UPDATE spend_month SET usd = 0")),
    ("direct DELETE FROM spend", lambda: rt.execute("DELETE FROM spend")),
    ("TRUNCATE spend", lambda: rt.execute("TRUNCATE spend")),
    ("TRUNCATE spend_month, kill_switch", lambda: rt.execute("TRUNCATE spend_month, kill_switch")),
    ("direct INSERT of a row", lambda: rt.execute("INSERT INTO spend(agent_id, day, usd) VALUES ('z', %s, 1)", (D,))),
    ("SELECT ... FOR UPDATE (row lock needs UPDATE privilege)", lambda: rt.execute("SELECT * FROM spend FOR UPDATE")),
    ("ALTER TABLE spend DROP CONSTRAINT", lambda: rt.execute("ALTER TABLE spend DROP CONSTRAINT spend_guarded_ok")),
    ("ALTER TABLE spend DISABLE TRIGGER ALL", lambda: rt.execute("ALTER TABLE spend DISABLE TRIGGER ALL")),
    ("DROP TRIGGER on spend", lambda: rt.execute("DROP TRIGGER spend_keep_keys ON spend")),
    ("CREATE OR REPLACE FUNCTION spend_settle (own body)", lambda: rt.execute("CREATE OR REPLACE FUNCTION public.spend_settle(text,date,date,numeric,numeric) RETURNS TABLE(day_usd numeric, month_usd numeric) LANGUAGE sql AS 'SELECT 0::numeric, 0::numeric'")),
    ("ALTER FUNCTION spend_settle SECURITY INVOKER", lambda: rt.execute("ALTER FUNCTION spend_settle(text,date,date,numeric,numeric) SECURITY INVOKER")),
    ("ALTER FUNCTION spend_settle OWNER TO rt17", lambda: rt.execute("ALTER FUNCTION spend_settle(text,date,date,numeric,numeric) OWNER TO rt17")),
    ("SET ROLE migr17", lambda: rt.execute("SET ROLE migr17")),
    ("SET SESSION AUTHORIZATION op17", lambda: rt.execute("SET SESSION AUTHORIZATION op17")),
    ("call kill_switch_release", lambda: rt.execute("SELECT kill_switch_release()")),
    ("CREATE FUNCTION in schema public", lambda: rt.execute("CREATE FUNCTION public.evil() RETURNS int LANGUAGE sql AS 'SELECT 1'")),
    ("ALTER TABLE spend DISABLE TRIGGER USER", lambda: rt.execute("ALTER TABLE spend DISABLE TRIGGER USER")),
    ("DELETE FROM spend_decrease_log", lambda: rt.execute("DELETE FROM spend_decrease_log")),
    ("UPDATE kill_switch_log", lambda: rt.execute("UPDATE kill_switch_log SET new_on = true")),
):
    c = code(fn); expect(f"A1 runtime role: {label} is refused", c in ("42501", "42P01"), f"sqlstate={c}")
rt.execute("GRANT UPDATE ON spend TO rt17")  # Postgres only warns (no error) when the grantor lacks the right; check the effect
expect("A1 runtime role: GRANT UPDATE ON spend TO rt17 has no effect (the privilege is still absent)", not mg.execute("SELECT has_table_privilege('rt17','spend','UPDATE')").fetchone()[0])
expect("A1 after all refused attempts the totals are unchanged", tot() == (Decimal("4"), Decimal("0")) and mtot() == (Decimal("4"), Decimal("0")), f"{tot()} {mtot()}")
# via the function
c = code(lambda: S("a", Decimal("1"), Decimal("0"))); expect("A2 settle (worst 1, nothing open) refused 23514", c == "23514", f"sqlstate={c}  total={tot()}")
c = code(lambda: S("a", Decimal("0.0000000001"), Decimal("0"))); expect("A2b settle with a tiny worst 1e-10, nothing open: refused 23514", c == "23514", f"sqlstate={c}")
r = S("a", Decimal("0"), Decimal("0")); expect("A3 settle worst 0 actual 0 changes nothing", tot() == (Decimal("4"), Decimal("0")), str(r))
r = S("a", Decimal("0"), Decimal("-0.1")); expect("A3b settle actual negative changes nothing", tot() == (Decimal("4"), Decimal("0")), str(r))
r = S("a", Decimal("-5"), Decimal("0")); expect("A3c settle worst negative changes nothing", tot() == (Decimal("4"), Decimal("0")), str(r))
r = S("a", Decimal("-5"), Decimal("-5")); expect("A3d settle both negative changes nothing", tot() == (Decimal("4"), Decimal("0")), str(r))
# reservation held by ANOTHER agent id: can the runtime settle B's open reservation (shared runtime identity)?
R("b", Decimal("7"))
r = S("b", Decimal("7"), Decimal("0"))
obs(f"A4 runtime with ONE login can settle ANY agent_id's open reservation (agent id is a plain argument, not bound to a login): settle('b',7,0) -> {r}; b now {tot('b')}")
expect("A4 settled money of agent a untouched by settling b", tot() == (Decimal("4"), Decimal("0")))
# settled money cannot be erased even with many agents/days: sum invariant
# reserve with day/month crossing
R("c", Decimal("5"))
d2 = date(2026, 11, 17)
rt.execute("SELECT * FROM spend_reserve('c', %s, %s, %s)", (d2, MO, Decimal("3")))
rt.execute("SELECT * FROM spend_settle('c', %s, %s, %s, %s)", (D, MO, Decimal("5"), Decimal("0")))
mt = mtot("c"); obs(f"A5 month row for c after reserve 5 (day1) + reserve 3 (day2) + settle day1 5->0: usd/open = {mt}")
# settle day1 again but with month worst bigger than day's open? month open is 3 now
c = code(lambda: rt.execute("SELECT * FROM spend_settle('c', %s, %s, %s, %s)", (D, MO, Decimal("3"), Decimal("0"))))
obs(f"A5b settle day1 (open 0) worst 3 against month with open 3 -> sqlstate={c}; day1 total={tot('c')} month={mtot('c')}")
expect("A5b a settle that does not fit the DAY row is refused even if the month row could absorb it", c == "23514", f"sqlstate={c}")
bad = mg.execute("SELECT count(*) FROM spend WHERE usd<0 OR open_usd<0 OR usd<open_usd").fetchone()[0] + mg.execute("SELECT count(*) FROM spend_month WHERE usd<0 OR open_usd<0 OR usd<open_usd").fetchone()[0]
expect("A5c no row anywhere has usd<0, open<0, or open>usd", bad == 0, str(bad))

# ---- B. kill switch
before = mg.execute('SELECT "on","by" FROM kill_switch').fetchone()
for label, fn in (
    ("engage with an argument (forged by)", lambda: rt.execute("SELECT kill_switch_engage('forged')")),
    ("direct UPDATE of by", lambda: rt.execute("UPDATE kill_switch SET \"by\" = 'forged'")),
    ("direct UPDATE on=false", lambda: rt.execute("UPDATE kill_switch SET \"on\" = false")),
    ("SET session_authorization via set_config", lambda: rt.execute("SELECT set_config('session_authorization','op17',false)")),
):
    c = code(fn); expect(f"B1 runtime: {label} refused", c in ("42501", "42883", "22023", "55P02"), f"sqlstate={c}")
rt.execute("SELECT kill_switch_engage()")
s = mg.execute('SELECT "on","by" FROM kill_switch').fetchone(); expect("B2 engage records by=rt17", s == (True, "rt17"), str(s))
# SET ROLE inside session: can runtime make session_user differ? try SET ROLE to a role it is not a member of
c = code(lambda: rt.execute("SET ROLE op17")); expect("B3 SET ROLE op17 refused", c == "42501", str(c))
# a role member case: grant rt17 membership in op17 -> by stays session_user (rt17) after SET ROLE
admin.execute("GRANT op17 TO rt17"); rt.execute("SET ROLE op17")
rt.execute("SELECT kill_switch_release()"); s = mg.execute('SELECT "on","by" FROM kill_switch').fetchone()
obs(f"B4 (only if an operator privilege is granted by membership) release after SET ROLE op17 records by={s[1]} (session_user, the login, not the SET ROLE role)")
expect("B4 `by` is the login (session_user), not the SET ROLE role", s == (False, "rt17"), str(s))
rt.execute("RESET ROLE"); admin.execute("REVOKE op17 FROM rt17")
# engage twice / release on missing row
mg.execute("DELETE FROM kill_switch") ; rt.execute("SELECT kill_switch_engage()")
obs(f"B5 migration role deleted the kill_switch row; runtime engage silently succeeds, rows now={mg.execute('SELECT count(*) FROM kill_switch').fetchone()[0]} (engage = UPDATE ... WHERE id=1: no row, no error)")
mg.execute("INSERT INTO kill_switch(id, schema_version, \"on\", \"by\", ts) VALUES (1, 1, false, 'restore', now())")

# ---- C. hostile values
VALS = {"NaN": Decimal("NaN"), "Infinity": Decimal("Infinity"), "-Infinity": Decimal("-Infinity"), "negative": Decimal("-1"),
        "bigint+1 (2^63)": Decimal(2**63), "bigint max 2^63-1": Decimal(2**63 - 1), "1e131072 numeric overflow": Decimal("1e131072"),
        "1e30": Decimal("1e30"), "NULL": None}
for nm, v in VALS.items():
    b4 = (tot("v"), mtot("v"))
    c = code(lambda: R("v", v))
    after = (tot("v"), mtot("v"))
    ok_state = (after[0] is None or after[0][0] >= 0)
    if nm in ("NaN", "Infinity", "-Infinity", "negative"):
        expect(f"C1 reserve {nm}: refused or inert, state unchanged", (c is not None or after == b4) and ok_state, f"sqlstate={c} before={b4[0]} after={after[0]}")
    elif nm == "NULL":
        expect(f"C1 reserve {nm}: refused or inert, state unchanged", (c is not None or after == b4) and ok_state, f"sqlstate={c} before={b4[0]} after={after[0]}")
    else:
        obs(f"C1 reserve {nm}: sqlstate={c} before={b4[0]} after={after[0]}")
    if nm.startswith("bigint") and c is None:  # clear it by settling the same amount
        c2 = code(lambda: S("v", v, Decimal("0"))); obs(f"C1b settle back {nm}: sqlstate={c2} after={tot('v')}")
    if nm == "1e30" and c is None:
        S("v", v, Decimal("0"))
for nm, v in VALS.items():
    for pos in ("worst", "actual"):
        R("w", Decimal("5")); b4 = (tot("w"), mtot("w"))
        args = (v, Decimal("0")) if pos == "worst" else (Decimal("1"), v)
        c = code(lambda: S("w", *args)); after = (tot("w"), mtot("w"))
        if nm in ("NaN", "Infinity", "-Infinity", "negative", "NULL"):
            expect(f"C2 settle {pos}={nm}: refused or inert, settled money (usd-open) not lowered", (c is not None or after == b4) and after[0][0] - after[0][1] >= b4[0][0] - b4[0][1], f"sqlstate={c} before={b4[0]} after={after[0]}")
        else:
            obs(f"C2 settle {pos}={nm}: sqlstate={c} before={b4[0]} after={after[0]}")
        mg.execute("DELETE FROM spend WHERE agent_id='w'; DELETE FROM spend_month WHERE agent_id='w'") if False else None
        # reset for next case: bring open back to 0 through the migration role
        mg.execute("UPDATE spend SET usd=0, open_usd=0 WHERE agent_id='w'"); mg.execute("UPDATE spend_month SET usd=0, open_usd=0 WHERE agent_id='w'")
# NULL for other args
for label, fn in (
    ("reserve NULL agent", lambda: rt.execute("SELECT * FROM spend_reserve(NULL,%s,%s,1)", (D, MO))),
    ("reserve NULL day", lambda: rt.execute("SELECT * FROM spend_reserve('n',NULL,%s,1)", (MO,))),
    ("reserve NULL month", lambda: rt.execute("SELECT * FROM spend_reserve('n',%s,NULL,1)", (D,))),
    ("settle NULL agent", lambda: rt.execute("SELECT * FROM spend_settle(NULL,%s,%s,1,0)", (D, MO))),
    ("reserve float8 NaN argument", lambda: rt.execute("SELECT * FROM spend_reserve('n',%s,%s,'NaN'::float8)", (D, MO))),
    ("reserve text '1' argument", lambda: rt.execute("SELECT * FROM spend_reserve('n',%s,%s,'1'::text)", (D, MO))),
    ("reserve date 'infinity'", lambda: rt.execute("SELECT * FROM spend_reserve('n','infinity'::date,%s,1)", (MO,))),
    ("reserve empty-string agent", lambda: rt.execute("SELECT * FROM spend_reserve('',%s,%s,1)", (D, MO))),
    ("reserve 100KB agent id", lambda: rt.execute("SELECT * FROM spend_reserve(%s,%s,%s,1)", ("x" * 100000, D, MO))),
):
    obs(f"C3 {label}: sqlstate={code(fn)}")
obs(f"C3 rows now in spend with agent 'n': {mg.execute(chr(83)+'ELECT count(*) FROM spend WHERE agent_id = %s', ('n',)).fetchone()[0]}, empty agent id: {mg.execute('SELECT count(*) FROM spend WHERE agent_id = %s', ('',)).fetchone()[0]}")
# month row mismatch: reserve with an arbitrary month label that is not day's month
rt.execute("SELECT * FROM spend_reserve('mm', %s, %s, 1)", (D, date(1999, 1, 1)))
obs(f"C4 reserve accepts a month that is not the day's month and not a first-of-month date: spend_month rows for mm = {mg.execute(chr(83)+'ELECT month FROM spend_month WHERE agent_id = %s', ('mm',)).fetchall()}")

# ---- D. races (threads, separate connections)
def worker_conns(n): return [psycopg.connect(dsn("rt17", "h1"), autocommit=True) for _ in range(n)]
# D1: 40 concurrent reserves of 1 -> total 40
cs = worker_conns(20); errs = []
def go_reserve(c):
    try:
        for _ in range(5): c.execute("SELECT * FROM spend_reserve('race1', %s, %s, 1)", (D, MO))
    except Exception as e: errs.append(str(e)[:80])
th = [threading.Thread(target=go_reserve, args=(c,)) for c in cs]; [t.start() for t in th]; [t.join() for t in th]
expect("D1 20 connections x 5 reserves of 1 racing on one agent-day: total exactly 100, open 100, no errors", tot("race1") == (Decimal("100"), Decimal("100")) and mtot("race1") == (Decimal("100"), Decimal("100")) and not errs, f"{tot('race1')} {mtot('race1')} errs={errs[:2]}")
# D2: two connections settle the SAME single reservation of 10 to 0: exactly one wins
for trial in range(10):
    ag = f"race2_{trial}"; R(ag, Decimal("10")); a, b = worker_conns(2); out = []; bar = threading.Barrier(2)
    def go(c):
        bar.wait(); out.append(code(lambda: c.execute("SELECT * FROM spend_settle(%s,%s,%s,10,0)", (ag, D, MO))))
    t = [threading.Thread(target=go, args=(c,)) for c in (a, b)]; [x.start() for x in t]; [x.join() for x in t]
    ok = sorted(map(str, out)) == ["23514", "None"] and tot(ag) == (Decimal("0"), Decimal("0"))
    if not ok: expect(f"D2 trial {trial}: exactly one of two racing full settles wins", False, f"{out} {tot(ag)}")
    a.close(); b.close()
else:
    expect("D2 10 trials: two connections racing to settle the same reservation of 10: exactly one succeeds, the other 23514, total 0", True)
# D3: reserve 10 + settle(10,actual 3) racing with settle(10, actual 0) -> settled money never below 3 if the first wins, else 0, never negative
viol = 0
for trial in range(20):
    ag = f"race3_{trial}"; R(ag, Decimal("10")); a, b = worker_conns(2); bar = threading.Barrier(2); out = []
    def g1(c): bar.wait(); out.append(code(lambda: c.execute("SELECT * FROM spend_settle(%s,%s,%s,10,3)", (ag, D, MO))))
    def g2(c): bar.wait(); out.append(code(lambda: c.execute("SELECT * FROM spend_settle(%s,%s,%s,10,0)", (ag, D, MO))))
    t = [threading.Thread(target=g1, args=(a,)), threading.Thread(target=g2, args=(b,))]; [x.start() for x in t]; [x.join() for x in t]
    u, o = tot(ag)
    if not (o == 0 and u in (Decimal("3"), Decimal("0")) and sorted(map(str, out)) == ["23514", "None"]): viol += 1
    a.close(); b.close()
expect("D3 20 trials: racing settle(10,actual 3) vs settle(10,actual 0): one wins, one 23514, open 0, total is 3 or 0", viol == 0, f"violations={viol}")
# D4: reserve racing with settle on same row: invariant usd - open >= 0 and equals sum of actuals
ag = "race4"; R(ag, Decimal("1")); cs = worker_conns(8); errs = []
def mix(c, i):
    try:
        for k in range(30):
            if (i + k) % 2: c.execute("SELECT * FROM spend_reserve('race4', %s, %s, 2)", (D, MO))
            else: code(lambda: c.execute("SELECT * FROM spend_settle('race4', %s, %s, 2, 1)", (D, MO)))
    except Exception as e: errs.append(str(e)[:80])
th = [threading.Thread(target=mix, args=(c, i)) for i, c in enumerate(cs)]; [t.start() for t in th]; [t.join() for t in th]
u, o = tot(ag); mu, mo = mtot(ag)
obs(f"D4 mixed 8x30 calls: day usd={u} open={o}; month usd={mu} open={mo}; errors={errs[:2]}")
expect("D4 mixed race: usd>=open>=0, day and month rows agree (usd and open), settled = usd-open is a non-negative integer count of settles", u >= o >= 0 and (u, o) == (mu, mo) and (u - o) == (u - o).to_integral_value(), f"settled={u-o}")
# deadlock check: opposite order of agent rows in one connection? functions take day then month row; test two agents crossing
dl = []
def cross(c, a1, a2):
    try:
        for _ in range(30): c.execute("SELECT * FROM spend_reserve(%s,%s,%s,1)", (a1, D, MO)); c.execute("SELECT * FROM spend_reserve(%s,%s,%s,1)", (a2, D, MO))
    except Exception as e: dl.append(str(e)[:60])
cs = worker_conns(4); th = [threading.Thread(target=cross, args=(cs[i], "x1" if i % 2 else "x2", "x2" if i % 2 else "x1")) for i in range(4)]
[t.start() for t in th]; [t.join() for t in th]
expect("D5 crossing agent order from 4 connections: no deadlock or error (month row is shared by both agents? no, per agent)", not dl, str(dl[:2]))

# ---- E. lock_timeout 55P03 on each held file, own method: hold a lock on each table separately, apply the file through the real migrate()
def lock_case(label, files_pre, newfile, number, hold_sql):
    db = "e_" + secrets.token_hex(3)
    admin.execute(f"CREATE DATABASE {db} OWNER migr17")
    tm = Path(tempfile.mkdtemp(prefix="hv17e_"))
    for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tm / p.name)
    for f, n in files_pre: shutil.copy(H17 / f, tm / f"{n}.sql")
    for k in ("spend_decrease_log", "kill_switch_log"):
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if any("decrease_log" in f for f, _ in files_pre) else m.GRANTS.pop(k, None))
    m._migration_files = lambda folder=tm: sorted(Path(folder).glob("*.sql"))
    m.migrate(dsn("migr17", db), runtime_role="rt17")
    shutil.copy(H17 / newfile, tm / f"{number}.sql")
    for k in ("spend_decrease_log", "kill_switch_log"):
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if "decrease_log" in newfile else m.GRANTS.pop(k, None))
    hold = psycopg.connect(dsn("migr17", db)); hold.execute(hold_sql)
    t0 = time.monotonic(); c = None
    try: m.migrate(dsn("migr17", db, "options='-c statement_timeout=20000'"), runtime_role="rt17")
    except psycopg.Error as e: c = str(e.sqlstate)
    dt = time.monotonic() - t0; hold.rollback(); hold.close()
    applied = psycopg.connect(dsn("migr17", db), autocommit=True).execute("SELECT count(*) FROM schema_migrations WHERE version LIKE %s", (number + "%",)).fetchone()[0]
    expect(f"E {label} | hold: {hold_sql}", c == "55P03" and 4.5 <= dt <= 7 and applied == 0, f"sqlstate={c} after {dt:.2f}s, ledger rows for it={applied}")
    admin.execute(f"DROP DATABASE {db} WITH (FORCE)")
for f, number, pre in (("spend_nonneg.sql", "0006_x", []), ("spend_nonneg_finite.sql", "0006_x", []),
                       ("spend_nonneg_upgrade.sql", "0007_x", [("spend_nonneg.sql", "0006_pre")]),
                       ("spend_decrease_log.sql", "0006_x", []), ("spend_guarded_writes.sql", "0006_x", [])):
    for hold in ("LOCK TABLE spend IN ROW EXCLUSIVE MODE", "LOCK TABLE spend_month IN ROW EXCLUSIVE MODE", "LOCK TABLE kill_switch IN ROW EXCLUSIVE MODE", "LOCK TABLE spend IN ACCESS SHARE MODE"):
        if f in ("spend_nonneg.sql", "spend_nonneg_finite.sql", "spend_nonneg_upgrade.sql", "spend_guarded_writes.sql") and "kill_switch" in hold: continue
        lock_case(f, pre, f, number, hold)
print(f"SUMMARY {sum(res)} of {len(res)} EXPECT checks passed")
sys.exit(0 if all(res) else 1)
