"""v18 Postgres checks (v17 checks kept, fixed or extended; new ones for MA1-MA4, m1-m8) on the real migrate() code of src/ (read only), throwaway cluster, password logins only.
Usage: python pg_v18.py <socket_dir> <src_dir> <held_dir_v18> <held_dir_v16> (the v17 held files are read from ../evidence-handoff-v17/held-sql as the CONTROL) (admin password in HV_ADMIN_PW). One line per check: PASS/FAIL/INFO.
Prototype checks, made-up data. The v16 DB-2 file is run as a CONTROL: a new check must FAIL on it (line starts CONTROL)."""
import atexit, sys, os, tempfile, shutil, time, secrets, random
from datetime import date
from decimal import Decimal
from pathlib import Path
sock, src, H17, H16 = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
HOLD17 = Path(__file__).resolve().parent.parent / 'evidence-handoff-v17' / 'held-sql'  # the v17 files, only for controls
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, src)
import psycopg
from psycopg import sql
import hadavin_sdk.store.migrate as m
PW, res = {}, []
D, MO = date(2026, 11, 16), date(2026, 11, 1)
def check(name, ok, detail=""):
    res.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)
def control(name, failed_as_expected, detail=""):
    res.append(bool(failed_as_expected)); print(("CONTROL-OK (the new check fails on v16) " if failed_as_expected else "CONTROL-FAIL (the new check does NOT fail on v16) ") + name + (f"  [{detail}]" if detail else ""), flush=True)
def info(s): print("INFO " + s, flush=True)
def dsn(u, db, extra=""): return f"host={sock} dbname={db} user={u} password={PW[u]} {extra}"
def st(fn):
    try: fn(); return None
    except psycopg.Error as e: return str(e.sqlstate)
PW["postgres"] = os.environ["HV_ADMIN_PW"]
admin = psycopg.connect(dsn("postgres", "postgres"), autocommit=True)
for r in ("migr17", "rt17", "op17", "ar17"):
    PW[r] = secrets.token_hex(16)
    admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(r), sql.Literal(PW[r])))
info("server " + admin.execute("SELECT version()").fetchone()[0])
real_files = m._migration_files
SEL = {k: m.Grant('table', 'SELECT') for k in ('spend', 'spend_month', 'kill_switch')}
ORIG = {k: m.GRANTS[k] for k in SEL}
def grants_select_only(): m.GRANTS.update(SEL)
def grants_original(): m.GRANTS.update(ORIG)
import secdef_audit_v18 as au
ROLES = {'runtime': 'rt17', 'operator': 'op17'}
def build(db, files, base=True):
    """files: list of (path, number-name). Fresh database owned by the non-superuser migration role; real 0001-0005 then the files."""
    if base: admin.execute(f"CREATE DATABASE {db} OWNER migr17")
    tmp = Path(tempfile.mkdtemp(prefix="v18mig_")); atexit.register(shutil.rmtree, tmp, True)
    for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmp / p.name)
    for p, n in files: shutil.copy(p, tmp / f"{n}.sql")
    for k in ("spend_decrease_log", "kill_switch_log"):  # the move PR state (v16 E2): GRANTS entry only when the file is in the folder
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if any("spend_decrease_log" in str(p) for p, _ in files) else m.GRANTS.pop(k, None))
    m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
    return tmp, m.migrate(dsn("migr17", db), runtime_role="rt17")
def set_log_grants(newfile):
    for k in ("spend_decrease_log", "kill_switch_log"):
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if "decrease_log" in str(newfile) else m.GRANTS.pop(k, None))
def fingerprint(db):
    """what a migration file changes: constraints, functions, triggers, columns, ledger rows of the public schema (m3: the old 'nothing applied' check looked at one table name and was vacuous for 4 of 5 files)."""
    c = psycopg.connect(dsn("migr17", db), autocommit=True)
    return c.execute("SELECT (SELECT count(*) FROM pg_constraint WHERE connamespace='public'::regnamespace), (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace), (SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal), (SELECT count(*) FROM pg_attribute a JOIN pg_class k ON k.oid=a.attrelid WHERE k.relnamespace='public'::regnamespace AND k.relkind='r' AND a.attnum>0 AND NOT a.attisdropped), (SELECT count(*) FROM schema_migrations)").fetchone()
def timed_migrate_with_lock(db, tmp, newfile, number, cap_s=15):
    """another session holds ROW EXCLUSIVE on spend; migrate() applies one more file; returns (sqlstate, seconds)."""
    shutil.copy(newfile, tmp / f"{number}.sql")
    set_log_grants(newfile)
    hold = psycopg.connect(dsn("migr17", db)); hold.execute("LOCK TABLE spend IN ROW EXCLUSIVE MODE")
    t0 = time.monotonic(); code = None
    try: m.migrate(dsn("migr17", db, f"options='-c statement_timeout={cap_s * 1000}'"), runtime_role="rt17")
    except psycopg.Error as e: code = str(e.sqlstate)
    dt = time.monotonic() - t0; hold.rollback(); hold.close()
    (tmp / f"{number}.sql").unlink()
    return code, dt

# ------------------------------------------------------------------ L: lock_timeout on EVERY held file (finding: DB-2 had none)
for label, f, number, pre in (
    ("DB-1 default spend_nonneg", "spend_nonneg.sql", "0006_a", None),
    ("DB-1 variant spend_nonneg_finite", "spend_nonneg_finite.sql", "0006_a", None),
    ("DB-1 upgrade spend_nonneg_upgrade (default applied first)", "spend_nonneg_upgrade.sql", "0007_a", "spend_nonneg.sql"),
    ("DB-2 v18 spend_decrease_log", "spend_decrease_log.sql", "0006_a", None),
    ("DB-3 v18 spend_guarded_writes", "spend_guarded_writes.sql", "0006_a", None)):
    db = "l_" + secrets.token_hex(3)
    tmp, _ = build(db, [(H17 / pre, "0006_pre")] if pre else [])
    fp0 = fingerprint(db)
    code, dt = timed_migrate_with_lock(db, tmp, H17 / f, number)
    check(f"L {label}: with another session holding the table, migrate() fails 55P03 in 4 to 9 s", code == "55P03" and 4 <= dt <= 9, f"{code} after {dt:.1f}s")
    fp1 = fingerprint(db)
    check(f"L {label}: nothing was applied (constraints, functions, triggers, columns and ledger rows all unchanged)", fp1 == fp0, f"{fp0} -> {fp1}")
    shutil.copy(H17 / f, tmp / f"{number}.sql"); set_log_grants(H17 / f); m.migrate(dsn("migr17", db), runtime_role="rt17"); fp2 = fingerprint(db)
    check(f"L {label}: the same file without the lock DOES change that fingerprint (so the check above is not vacuous)", fp2 != fp0, f"{fp0} -> {fp2}")
db = "l_" + secrets.token_hex(3); tmp, _ = build(db, [])
code, dt = timed_migrate_with_lock(db, tmp, H16 / "spend_decrease_log.sql", "0006_a", cap_s=12)
control("L v16 DB-2 file under the same lock: no 55P03", code != "55P03", f"{code} after {dt:.1f}s (waits until the {12}s statement cap)")
info("L: every file in held-sql/ has a lock check above; the lead's gate is `grep -c lock_timeout` plus this run (PR DB-1 test)")
import glob
for p in sorted(glob.glob(str(H17 / "*.sql"))):
    first = [l for l in open(p).read().splitlines() if l.strip() and not l.lstrip().startswith("--")][0].strip()
    check(f"L text: the FIRST statement of {Path(p).name} is SET LOCAL lock_timeout (position, not only presence)", first == "SET LOCAL lock_timeout = '5s';", first[:60])
_bad = "ALTER TABLE spend ADD COLUMN x int;\nSET LOCAL lock_timeout = '5s';\n"
check("L text: the position check itself refuses a file that sets the timeout AFTER an ALTER", [l for l in _bad.splitlines() if l.strip()][0] != "SET LOCAL lock_timeout = '5s';")

# ------------------------------------------------------------------ K: m5 switch ON is never blocked by the record
def ks_state(db): return psycopg.connect(dsn("migr17", db), autocommit=True).execute('SELECT "on", "by" FROM kill_switch').fetchone()
for tag, folder in (("v18", H17), ("v16", H16)):
    db = "k_" + tag + secrets.token_hex(2)
    build(db, [(folder / "spend_decrease_log.sql", "0006_dec")])
    mg = psycopg.connect(dsn("migr17", db), autocommit=True)
    mg.execute("ALTER TABLE kill_switch_log RENAME TO kill_switch_log_x")  # the record cannot be written
    rt = psycopg.connect(dsn("rt17", db), autocommit=True)
    on_err = st(lambda: rt.execute("UPDATE kill_switch SET \"on\" = TRUE, \"by\" = 'x', ts = now() WHERE id = 1"))
    state_on = ks_state(db)[0]
    if tag == "v18":
        check("K m5: with the record unwritable, switching ON still works", on_err is None and state_on is True, f"err={on_err}")
        off_err = st(lambda: rt.execute("UPDATE kill_switch SET \"on\" = FALSE, \"by\" = 'x', ts = now() WHERE id = 1"))
        check("K m5: with the record unwritable, switching OFF is refused (fail closed) and the switch stays ON", off_err is not None and ks_state(db)[0] is True, f"err={off_err}")
        mg.execute("ALTER TABLE kill_switch_log_x RENAME TO kill_switch_log")
        rt.execute("UPDATE kill_switch SET \"on\" = FALSE, \"by\" = 'x', ts = now() WHERE id = 1")
        rows = mg.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0]
        check("K m5: with the record writable again a switch OFF is recorded (1 row)", rows == 1, str(rows))
    else:
        control("K m5: v16 file: switching ON with the record unwritable", on_err is not None, f"err={on_err}")


# ------------------------------------------------------------------ H: security minor m4 (the INSERT branch can return a bad total too)
db = "h_" + secrets.token_hex(3); build(db, [])
mgh = psycopg.connect(dsn("migr17", db), autocommit=True)
mgh.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('n', %s, 'NaN')", (D,))
r = mgh.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('n', %s, 1) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd", (D,)).fetchone()[0]
check("H1 (a fact about Postgres, NOT a test of the code fix; that is a Python PR test): with no held file, a positive reserve (INSERT ... ON CONFLICT branch) on a NaN row RETURNS NaN, so the code check after RETURNING is needed in the INSERT branch too", r.is_nan(), str(r))


# ------------------------------------------------------------------ K2: m4 the DB-2 handler and a cancelled statement (57014)
for tag, folder in (("v18", H17), ("v17", HOLD17)):
    db = "q_" + tag + secrets.token_hex(2); build(db, [(folder / "spend_decrease_log.sql", "0006_dec")])
    rtq = psycopg.connect(dsn("rt17", db), autocommit=True)
    hold = psycopg.connect(dsn("migr17", db)); hold.execute("LOCK TABLE kill_switch_log IN ACCESS EXCLUSIVE MODE")
    rtq.execute("SET statement_timeout = 1500")
    on_err = st(lambda: rtq.execute("UPDATE kill_switch SET \"on\" = TRUE, \"by\" = 'x', ts = now() WHERE id = 1"))
    hold.rollback(); hold.close(); on_state = ks_state(db)[0]
    if tag == "v18":
        check("K2 m4: record table locked by another session and a 1.5 s statement_timeout: switching ON still works", on_err is None and on_state is True, f"err={on_err}")
        hold = psycopg.connect(dsn("migr17", db)); hold.execute("LOCK TABLE kill_switch_log IN ACCESS EXCLUSIVE MODE")
        off_err = st(lambda: rtq.execute("UPDATE kill_switch SET \"on\" = FALSE, \"by\" = 'x', ts = now() WHERE id = 1")); hold.rollback(); hold.close()
        check("K2 m4: the same lock and timeout while switching OFF: refused (fail closed) and the switch stays ON", off_err is not None and ks_state(db)[0] is True, f"err={off_err}")
    else:
        control("K2 m4: the v17 file (`WHEN OTHERS` only) with the same lock and timeout: switching ON is cancelled with 57014", on_err == "57014", f"err={on_err} state_on={on_state}")

# ------------------------------------------------------------------ G: DB-3, the REAL migrate(runtime_role=) with the grant map as the move PR must set it
def new_g(db, files):
    """MA3: build with the grant map UNCHANGED (_RW), show what migrate() hands the runtime role (control), then set select-only and run migrate twice more."""
    grants_original(); tmp, _ = build(db, files)
    mgx = psycopg.connect(dsn("migr17", db), autocommit=True); rtx = psycopg.connect(dsn("rt17", db), autocommit=True)
    ctl = st(lambda: rtx.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('ctl', %s, 1)", (D,)))
    ctl2 = st(lambda: rtx.execute("UPDATE kill_switch SET \"on\" = FALSE"))
    mgx.execute("DELETE FROM spend WHERE agent_id = 'ctl'")
    grants_select_only()
    for _ in range(2): m.migrate(dsn("migr17", db), runtime_role="rt17")
    au.apply_function_grants(mgx, roles=ROLES)
    for _ in range(2): m.migrate(dsn("migr17", db), runtime_role="rt17")
    return tmp, mgx, ctl, ctl2
db = "g_" + secrets.token_hex(3)
tmp, mg, ctl, ctl2 = new_g(db, [(H17 / "spend_decrease_log.sql", "0006_dec"), (H17 / "spend_guarded_writes.sql", "0007_guard")])
control("MA3 grant map unchanged (_RW): migrate(runtime_role=) leaves the runtime role able to INSERT into spend and UPDATE kill_switch directly (so G1 holds only in a hand-granted test)", ctl is None and ctl2 is None, f"insert err={ctl}, update err={ctl2}")
rt = psycopg.connect(dsn("rt17", db), autocommit=True); op = psycopg.connect(dsn("op17", db), autocommit=True)
check("MA3 after DB-3 and migrate(runtime_role=) run FOUR times (twice with _RW, twice select-only) the function grants are still exactly as set", au.secdef_problems(mg, roles=ROLES, owner="migr17") == [], str(au.secdef_problems(mg, roles=ROLES, owner="migr17")[:2]))
fn = ("spend_reserve(text,date,numeric)", "spend_settle(text,date,numeric,numeric)", "kill_switch_engage()", "kill_switch_release()")
perm = lambda who: [bool(mg.execute(f"SELECT has_function_privilege(%s, '{f}', 'EXECUTE')", (who,)).fetchone()[0]) for f in fn]
check("MA4 runtime role: EXECUTE on spend_reserve, spend_settle, kill_switch_engage and NOT on kill_switch_release", perm("rt17") == [True, True, True, False], str(perm("rt17")))
check("MA4 operator role: EXECUTE on kill_switch_release only", perm("op17") == [False, False, False, True], str(perm("op17")))
check("MA4 audit-reader and migration-unrelated login (ar17) and PUBLIC hold no EXECUTE", perm("ar17") == [False] * 4 and not any(mg.execute(f"SELECT has_function_privilege('public', '{f}', 'EXECUTE')").fetchone()[0] for f in fn))
tb = lambda who: [mg.execute("SELECT has_table_privilege(%s, %s, 'SELECT')", (who, t)).fetchone()[0] for t in ("spend", "spend_month", "kill_switch")]
check("MA4 runtime role: SELECT on the three tables; operator role: SELECT on none of them (m6: it only runs the release function)", tb("rt17") == [True] * 3 and tb("op17") == [False] * 3, f"{tb('rt17')} {tb('op17')}")
check("G1 runtime role: direct INSERT into spend refused 42501", st(lambda: rt.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('a', %s, 1)", (D,))) == "42501")
check("G1 runtime role: direct UPDATE of spend refused 42501", st(lambda: rt.execute("UPDATE spend SET usd = 0")) == "42501")
check("G1 runtime role: direct UPDATE of spend_month refused 42501", st(lambda: rt.execute("UPDATE spend_month SET usd = 0")) == "42501")
check("G1 runtime role: direct UPDATE of kill_switch refused 42501", st(lambda: rt.execute("UPDATE kill_switch SET \"on\" = FALSE")) == "42501")
check("G1 runtime role: DELETE of kill_switch refused 42501", st(lambda: rt.execute("DELETE FROM kill_switch")) == "42501")
for t in ("spend", "spend_month", "kill_switch"):
    check(f"G1 runtime role: DELETE FROM {t} refused 42501", st(lambda: rt.execute(f"DELETE FROM {t}")) == "42501")
    check(f"G1 runtime role: TRUNCATE {t} refused 42501", st(lambda: rt.execute(f"TRUNCATE {t}")) == "42501")
r = rt.execute("SELECT * FROM spend_reserve('a', %s, %s)", (D, Decimal("1.5"))).fetchone()
check("G2 reserve 1.5 returns day and month totals (1.5, 1.5)", r == (Decimal("1.5"), Decimal("1.5")), str(r))
check("G2 the month row is derived from the day (2026-11-01), the caller passes no month", mg.execute("SELECT month FROM spend_month WHERE agent_id='a'").fetchone()[0] == MO)
r = rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s)", (D, Decimal("1.5"), Decimal("0.4"))).fetchone()
check("G3 settle (worst 1.5, actual 0.4) leaves 0.4 on both", r == (Decimal("0.4"), Decimal("0.4")), str(r))
check("G4 settle again with nothing open is refused 23514 (the 0.4 already settled cannot be erased)", st(lambda: rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s)", (D, Decimal("1"), Decimal("0")))) == "23514")
check("G4 the total is still 0.4 after the refusal", rt.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0] == Decimal("0.4"))
rt.execute("SELECT * FROM spend_reserve('a', %s, %s)", (D, Decimal("2")))
check("G5 settle of a worst case larger than what is open (3 > 2) refused 23514", st(lambda: rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s)", (D, Decimal("3"), Decimal("0")))) == "23514")
r = rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s)", (D, Decimal("-1"), Decimal("0"))).fetchone()
check("G6 a negative worst case changes nothing (total stays 2.4)", r == (Decimal("2.4"), Decimal("2.4")), str(r))
check("G6 a negative actual cost changes nothing", rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s)", (D, Decimal("1"), Decimal("-5"))).fetchone() == (Decimal("2.4"), Decimal("2.4")))
for v in ("NaN", "Infinity", "-1"):
    check(f"G7 reserve of {v} refused 23514", st(lambda: rt.execute("SELECT * FROM spend_reserve('a', %s, %s)", (D, Decimal(v)))) == "23514")
check("G7 a settle with actual NaN refused 23514 and the total is unchanged", st(lambda: rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s)", (D, Decimal("1"), Decimal("NaN")))) == "23514" and rt.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0] == Decimal("2.4"))
# unbounded inputs (coordinator item 4)
check("G12 a reserve of 1000000000000 (the ceiling) refused 23514, 999999999999 accepted", st(lambda: rt.execute("SELECT * FROM spend_reserve('big', %s, %s)", (D, Decimal("1000000000000")))) == "23514" and st(lambda: rt.execute("SELECT * FROM spend_reserve('big', %s, %s)", (D, Decimal("999999999999")))) is None)
check("G12 an agent_id of length 0 or 201 refused 23514", st(lambda: rt.execute("SELECT * FROM spend_reserve('', %s, %s)", (D, Decimal("1")))) == "23514" and st(lambda: rt.execute("SELECT * FROM spend_reserve(%s, %s, %s)", ("x" * 201, D, Decimal("1")))) == "23514")
check("G12 a settle for an agent that has no row changes nothing and writes no row", st(lambda: rt.execute("SELECT * FROM spend_settle('nobody', %s, %s, %s)", (D, Decimal("1"), Decimal("0")))) is not None or mg.execute("SELECT count(*) FROM spend WHERE agent_id='nobody'").fetchone()[0] == 0)
a_before = mg.execute("SELECT usd, open_usd FROM spend WHERE agent_id='a'").fetchone(); rt.execute("SELECT * FROM spend_reserve('victim', %s, %s)", (D, Decimal("5")))
rt.execute("SELECT * FROM spend_settle('victim', %s, %s, %s)", (D, Decimal("5"), Decimal("0")))
check("G12 STATED, not closed: the runtime login can settle (give back) a reservation it made under ANY agent_id name, e.g. 'victim' (the control is per-agent logins, L-4, and the invoice comparison)", mg.execute("SELECT usd FROM spend WHERE agent_id='victim'").fetchone()[0] == 0)
# fuzz
rnd = random.Random(1717); bad = 0
for i in range(400):
    ag = f"f{rnd.randrange(3)}"; w = Decimal(rnd.choice(["0", "0.01", "1", "2.5", "10", "-1", "NaN", "999999999999"])); a = Decimal(rnd.choice(["0", "0.5", "1", "3", "-2", "Infinity"]))
    act = rnd.choice(("reserve", "settle", "settle"))
    before = mg.execute("SELECT usd - open_usd, usd, open_usd FROM spend WHERE agent_id = %s", (ag,)).fetchone()
    err = st(lambda: rt.execute("SELECT * FROM spend_reserve(%s, %s, %s)", (ag, D, w)) if act == "reserve" else rt.execute("SELECT * FROM spend_settle(%s, %s, %s, %s)", (ag, D, w, a)))
    after = mg.execute("SELECT usd - open_usd, usd, open_usd FROM spend WHERE agent_id = %s", (ag,)).fetchone()
    if before and after and after[0] < before[0]: bad += 1
    if err and before != after and not (before is None): bad += 1
check("G8 fuzz, 400 random calls by the runtime role: settled money (total minus open reservation) never fell; a refused call changed nothing", bad == 0, f"violations={bad}")
neg = mg.execute("SELECT count(*) FROM spend WHERE usd < 0 OR open_usd < 0 OR usd < open_usd OR usd >= 1000000000000").fetchone()[0]
check("G8 after the fuzz no row has a negative total, a negative open amount, open above the total, or a total at the ceiling", neg == 0)
# kill switch
ts_state = lambda: mg.execute('SELECT "on", "by", ts FROM kill_switch').fetchone()
rt.execute("SELECT kill_switch_engage()"); s = ts_state()
check("G9 runtime role engages the kill switch; `by` is its own login (rt17), not a value it chose", s[:2] == (True, "rt17"), str(s[:2]))
mg.execute("UPDATE kill_switch SET \"by\" = 'first-person'"); s0 = ts_state(); rt.execute("SELECT kill_switch_engage()")
check("G9 m2 engage when already ON changes nothing (`by` and `ts` of the first engage stay)", ts_state() == s0, f"{s0[1]}")
check("G9 runtime role cannot release it: 42501", st(lambda: rt.execute("SELECT kill_switch_release()")) == "42501" and mg.execute('SELECT "on" FROM kill_switch').fetchone()[0] is True)
op.execute("SELECT kill_switch_release()"); s = ts_state()
check("G9 operator role releases it; `by` is the operator login (op17)", s[:2] == (False, "op17"), str(s[:2]))
op.execute("SELECT kill_switch_release()")
check("G9 m2 release when already OFF changes nothing (`by` and `ts` stay)", ts_state() == s)
rows = mg.execute("SELECT old_on, new_on, who FROM kill_switch_log ORDER BY at").fetchall()
check("G9 with DB-2 also applied the record has the changes with the invoking login in `who`", rows[:2] == [(False, True, "rt17"), (True, False, "op17")], str(rows))
mg.execute("DELETE FROM kill_switch"); rt.execute("SELECT kill_switch_engage()")
check("G9 m2 engage with the row missing creates it and switches ON (a missing row was a silent no-op)", mg.execute('SELECT "on", "by" FROM kill_switch').fetchone() == (True, "rt17"))
# temp-table attack against the BEGIN ATOMIC bodies
rt.execute("CREATE TEMP TABLE spend (agent_id text, day date, usd numeric, open_usd numeric DEFAULT 0)")
rt.execute("CREATE TEMP TABLE spend_month (agent_id text, month date, usd numeric, open_usd numeric DEFAULT 0)")
rt.execute("CREATE TEMP TABLE kill_switch (id int, \"on\" boolean, \"by\" text, ts timestamptz)")
rt.execute("SET search_path = pg_temp, public")
before = mg.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0]
try: rt.execute("SELECT * FROM public.spend_reserve('a', %s, %s)", (D, Decimal("1")))
except psycopg.Error as e: info("temp attack call error " + str(e.sqlstate))
after = mg.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0]
check("G10 temporary tables named spend, spend_month, kill_switch plus search_path = pg_temp first: the real total moved (+1) and the temporary tables are empty", after == before + 1 and rt.execute("SELECT count(*) FROM pg_temp.spend").fetchone()[0] == 0, f"{before}->{after}")
# DB-3 on top of DB-1 default and DB-2 through the real migrate()
db2 = "g2_" + secrets.token_hex(3)
try:
    ap = build(db2, [(H17 / "spend_nonneg.sql", "0006_nn"), (H17 / "spend_decrease_log.sql", "0007_dec"), (H17 / "spend_guarded_writes.sql", "0008_guard")])[1]
    check("G11 DB-1 default, DB-2 and DB-3 apply together through the real migrate() (names do not clash)", len(ap) == 8, str(ap[-3:]))
except Exception as e: check("G11 all three apply together", False, type(e).__name__ + str(e)[:80])

# ------------------------------------------------------------------ MA2: the start-up query finds hand-made and mis-granted functions
db = "s_" + secrets.token_hex(3); grants_select_only()
_, mgs, _, _ = new_g(db, [(H17 / "spend_decrease_log.sql", "0006_dec"), (H17 / "spend_guarded_writes.sql", "0007_guard")])
rts = psycopg.connect(dsn("rt17", db), autocommit=True)
check("MA2 clean database: the query run on the RUNTIME login (no table rights needed) finds no problem", au.secdef_problems(rts, roles=ROLES, owner="migr17") == [])
sup = psycopg.connect(dsn("postgres", db), autocommit=True)  # a superuser makes the hostile changes (ALTER OWNER needs it)
mk = lambda body: sup.execute(body)
EVIL = "CREATE FUNCTION {n}() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS 'SELECT 1'"
cases = [
 ("a hand-made SECURITY DEFINER function that is on no list", EVIL.format(n="evil"), "DROP FUNCTION evil()", "unexpected SECURITY DEFINER function public.evil"),
 ("EXECUTE on spend_reserve granted to PUBLIC", "GRANT EXECUTE ON FUNCTION spend_reserve(text,date,numeric) TO PUBLIC", "REVOKE EXECUTE ON FUNCTION spend_reserve(text,date,numeric) FROM PUBLIC", "PUBLIC"),
 ("kill_switch_release granted to the runtime role", "GRANT EXECUTE ON FUNCTION kill_switch_release() TO rt17", "REVOKE EXECUTE ON FUNCTION kill_switch_release() FROM rt17", "rt17"),
 ("kill_switch_engage granted to the operator role", "GRANT EXECUTE ON FUNCTION kill_switch_engage() TO op17", "REVOKE EXECUTE ON FUNCTION kill_switch_engage() FROM op17", "op17"),
 ("a second overload of a listed name, created with the default (PUBLIC) EXECUTE", "CREATE FUNCTION spend_reserve(p text, p2 date, p3 numeric, p4 numeric) RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS 'SELECT 1'", "DROP FUNCTION spend_reserve(text,date,numeric,numeric)", "unexpected SECURITY DEFINER function public.spend_reserve(text,date,numeric,numeric)"),
 ("kill_switch_release owner changed to another role", "ALTER FUNCTION kill_switch_release() OWNER TO op17", "ALTER FUNCTION kill_switch_release() OWNER TO migr17; GRANT EXECUTE ON FUNCTION kill_switch_release() TO op17", "owned by op17"),
 ("search_path of spend_settle reset (ALTER FUNCTION ... RESET)", "ALTER FUNCTION spend_settle(text,date,numeric,numeric) RESET search_path", "ALTER FUNCTION spend_settle(text,date,numeric,numeric) SET search_path = pg_catalog, pg_temp", "not exactly search_path"),
 ("search_path of spend_settle set to public by ALTER FUNCTION SET", "ALTER FUNCTION spend_settle(text,date,numeric,numeric) SET search_path = public", "ALTER FUNCTION spend_settle(text,date,numeric,numeric) SET search_path = pg_catalog, pg_temp", "not exactly search_path"),
 ("a SECURITY DEFINER function with a listed name in another schema", "CREATE SCHEMA other17; CREATE FUNCTION other17.kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS 'SELECT 1'", "DROP SCHEMA other17 CASCADE", "unexpected SECURITY DEFINER function other17.kill_switch_release"),
 ("the runtime role made a member of the operator role", "GRANT op17 TO rt17", "REVOKE op17 FROM rt17", "member of op17"),
]
exp_tables = lambda g: g.runtime if g else ""
for name, bad, fix, want in cases:
    mk(bad); pr = au.secdef_problems(rts, roles=ROLES, owner="migr17")
    old = m.effective_problems(mgs, "rt17", exp_tables) if "member" not in name else None
    mk(fix); pr_after = au.secdef_problems(rts, roles=ROLES, owner="migr17")
    check(f"MA2 {name}: the start-up query reports it", any(want in p for p in pr), str(pr[:1]))
    check(f"MA2 {name}: after the repair the query is clean again", pr_after == [], str(pr_after[:1]))
    if old is not None: control(f"MA2 {name}: the v17-era audit (migrate.effective_problems: tables and columns only) reports nothing", old == [], str(old[:1]))
mk("DROP FUNCTION kill_switch_engage()")
check("MA2 a listed function that was dropped is reported", any("listed but not installed" in p for p in au.secdef_problems(rts, roles=ROLES, owner="migr17")))
mgs.execute("SELECT 1"); au.apply_function_grants  # (the dropped function is recreated only in a new database)
# m7: a non-default schema, and a binding to a lookalike in another schema
db7 = "n_" + secrets.token_hex(3); admin.execute(f"CREATE DATABASE {db7} OWNER migr17")
mg7 = psycopg.connect(dsn("migr17", db7), autocommit=True); mg7.execute("CREATE SCHEMA app17")
opt = "options='-c search_path=app17'"
tmp7 = Path(tempfile.mkdtemp(prefix="v18mig_")); atexit.register(shutil.rmtree, tmp7, True)
for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmp7 / p.name)
for p, n in ((H17 / "spend_decrease_log.sql", "0006_dec"), (H17 / "spend_guarded_writes.sql", "0007_guard")): shutil.copy(p, tmp7 / f"{n}.sql")
set_log_grants(H17 / "spend_decrease_log.sql"); grants_select_only(); m._migration_files = lambda folder=tmp7: sorted(Path(folder).glob("*.sql"))
mg7.execute("GRANT USAGE ON SCHEMA app17 TO rt17, op17")
try:
    m.migrate(dsn("migr17", db7, opt), runtime_role="rt17"); mg7a = psycopg.connect(dsn("migr17", db7, opt), autocommit=True)
    mg7a.execute("GRANT USAGE ON SCHEMA app17 TO rt17, op17"); au.apply_function_grants(mg7a, roles=ROLES)
    rt7 = psycopg.connect(dsn("rt17", db7, opt), autocommit=True)
    check("m7 a non-default schema (app17): the functions are created there, bound only to app17 tables, and the query is clean", au.secdef_problems(rt7, roles=ROLES, owner="migr17") == [], str(au.secdef_problems(rt7, roles=ROLES, owner="migr17")[:2]))
    check("m7 the runtime role can reserve through the function in app17", rt7.execute("SELECT * FROM spend_reserve('z', %s, %s)", (D, Decimal("1"))).fetchone() == (Decimal("1"), Decimal("1")))
    mg7a.execute("CREATE TABLE public.spend (agent_id text, day date, usd numeric, open_usd numeric DEFAULT 0)")  # a lookalike earlier in the creating session's path
    mg7a.execute("CREATE TABLE public.spend_month (agent_id text, month date, usd numeric, open_usd numeric DEFAULT 0, PRIMARY KEY (agent_id, month))")
    mg7a.execute("SET search_path = public, app17")
    mg7a.execute("CREATE OR REPLACE FUNCTION app17.spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS TABLE (day_usd numeric, month_usd numeric) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp BEGIN ATOMIC INSERT INTO spend (agent_id, day, usd, open_usd) VALUES (p_agent, p_day, p_worst, p_worst); SELECT 0::numeric, 0::numeric; END")
    pr = au.secdef_problems(rt7, roles=ROLES, owner="migr17")
    check("m7 a function bound (by the creating session's search_path) to a lookalike table in schema public is reported", len(pr) == 1 and "bound to relations in schema ['public']" in pr[0], str(pr[:2]))
    control("m7 every OTHER check of the query (owner, settings, grants, name list) passes for that function, so only the binding check catches it (the v17 text had no query at all)", len(pr) == 1, f"{len(pr)} problem(s)")
except Exception as e: check("m7 non-default schema test ran", False, type(e).__name__ + " " + str(e)[:120])

# ------------------------------------------------------------------ controls on the v17 DB-3 file for the new rules (each must behave the old way)
grants_original()
db4 = "c4_" + secrets.token_hex(3); build(db4, [(HOLD17 / "spend_decrease_log.sql", "0006_dec"), (HOLD17 / "spend_guarded_writes.sql", "0007_guard")])
mg4 = psycopg.connect(dsn("migr17", db4), autocommit=True); mg4.execute("GRANT EXECUTE ON FUNCTION spend_reserve(text,date,date,numeric), kill_switch_engage(), kill_switch_release() TO rt17"); rt4 = psycopg.connect(dsn("rt17", db4), autocommit=True)
e1 = st(lambda: rt4.execute("SELECT * FROM spend_reserve('c', %s, %s, %s)", (D, date(2020, 1, 1), Decimal("1000000000000"))))
control("G12 v17 DB-3 file: a reserve of 1000000000000 with a month that is not the month of the day is accepted (no ceiling, caller-chosen month)", e1 is None and mg4.execute("SELECT count(*) FROM spend_month WHERE month = '2020-01-01'").fetchone()[0] == 1, f"err={e1}")
mg4.execute("DELETE FROM kill_switch"); rt4.execute("SELECT kill_switch_engage()")
control("G9 m2 v17 DB-3 file: engage with the row missing does nothing and says nothing", mg4.execute("SELECT count(*) FROM kill_switch").fetchone()[0] == 0)
mg4.execute("INSERT INTO kill_switch (id, schema_version, \"on\", \"by\", ts) VALUES (1, 1, true, 'first', now())"); rt4.execute("SELECT kill_switch_engage()")
control("G9 m2 v17 DB-3 file: engage when already ON rewrites `by`", mg4.execute('SELECT "by" FROM kill_switch').fetchone()[0] == "rt17")
# control: the v16 design (no DB-3) lets the runtime role do both things G1 and G9 refuse
db3 = "c_" + secrets.token_hex(3); build(db3, [(H16 / "spend_decrease_log.sql", "0006_dec")])
rt3 = psycopg.connect(dsn("rt17", db3), autocommit=True); mg3 = psycopg.connect(dsn("migr17", db3), autocommit=True)
rt3.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('a', %s, 10)", (D,)); rt3.execute("UPDATE spend SET usd = 0")
control("G1/G4 v16 design: the runtime role zeroes a settled total of 10 by direct UPDATE", mg3.execute("SELECT usd FROM spend").fetchone()[0] == Decimal("0"), "total is 0 (the exposure of security major M1)")
mg3.execute('UPDATE kill_switch SET "on" = TRUE'); rt3.execute('UPDATE kill_switch SET "on" = FALSE, "by" = \'chosen-by-caller\'')
s3 = mg3.execute('SELECT "on", "by" FROM kill_switch').fetchone()
control("G9 v16 design: the runtime role switches the kill switch OFF and picks the `by` text", s3 == (False, "chosen-by-caller"), str(s3))
print(f"SUMMARY {sum(res)} of {len(res)} checks passed")
sys.exit(0 if all(res) else 1)
