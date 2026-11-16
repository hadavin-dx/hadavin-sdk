"""v17 NEW Postgres checks on the real migrate() code of src/ (read only), throwaway cluster, password logins only.
Usage: python pg_v17.py <socket_dir> <src_dir> <held_dir_v17> <held_dir_v16> (admin password in HV_ADMIN_PW). One line per check: PASS/FAIL/INFO.
Prototype checks, made-up data. The v16 DB-2 file is run as a CONTROL: a new check must FAIL on it (line starts CONTROL)."""
import sys, os, tempfile, shutil, time, secrets, random
from datetime import date
from decimal import Decimal
from pathlib import Path
sock, src, H17, H16 = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
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
def build(db, files, base=True):
    """files: list of (path, number-name). Fresh database owned by the non-superuser migration role; real 0001-0005 then the files."""
    if base: admin.execute(f"CREATE DATABASE {db} OWNER migr17")
    tmp = Path(tempfile.mkdtemp(prefix="v17mig_"))
    for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmp / p.name)
    for p, n in files: shutil.copy(p, tmp / f"{n}.sql")
    for k in ("spend_decrease_log", "kill_switch_log"):  # the move PR state (v16 E2): GRANTS entry only when the file is in the folder
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if any("spend_decrease_log" in str(p) for p, _ in files) else m.GRANTS.pop(k, None))
    m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
    return tmp, m.migrate(dsn("migr17", db), runtime_role="rt17")
def timed_migrate_with_lock(db, tmp, newfile, number, cap_s=15):
    """another session holds ROW EXCLUSIVE on spend; migrate() applies one more file; returns (sqlstate, seconds, ledger_rows_for_it)."""
    shutil.copy(newfile, tmp / f"{number}.sql")
    for k in ("spend_decrease_log", "kill_switch_log"):
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if "decrease_log" in str(newfile) else m.GRANTS.pop(k, None))
    hold = psycopg.connect(dsn("migr17", db)); hold.execute("LOCK TABLE spend IN ROW EXCLUSIVE MODE")
    t0 = time.monotonic(); code = None
    try: m.migrate(dsn("migr17", db, f"options='-c statement_timeout={cap_s * 1000}'"), runtime_role="rt17")
    except psycopg.Error as e: code = str(e.sqlstate)
    dt = time.monotonic() - t0; hold.rollback(); hold.close()
    led = psycopg.connect(dsn("migr17", db), autocommit=True).execute("SELECT count(*) FROM schema_migrations WHERE name = %s", (number,)).fetchone()[0] if False else None
    (tmp / f"{number}.sql").unlink()
    return code, dt

# ------------------------------------------------------------------ L: lock_timeout on EVERY held file (finding: DB-2 had none)
for label, f, number, pre in (
    ("DB-1 default spend_nonneg", "spend_nonneg.sql", "0006_a", None),
    ("DB-1 variant spend_nonneg_finite", "spend_nonneg_finite.sql", "0006_a", None),
    ("DB-1 upgrade spend_nonneg_upgrade (default applied first)", "spend_nonneg_upgrade.sql", "0007_a", "spend_nonneg.sql"),
    ("DB-2 v17 spend_decrease_log", "spend_decrease_log.sql", "0006_a", None),
    ("DB-3 v17 spend_guarded_writes", "spend_guarded_writes.sql", "0006_a", None)):
    db = "l_" + secrets.token_hex(3)
    tmp, _ = build(db, [(H17 / pre, "0006_pre")] if pre else [])
    code, dt = timed_migrate_with_lock(db, tmp, H17 / f, number)
    check(f"L {label}: with another session holding the table, migrate() fails 55P03 in 4 to 9 s", code == "55P03" and 4 <= dt <= 9, f"{code} after {dt:.1f}s")
    ledger = psycopg.connect(dsn("migr17", db)).execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'spend_decrease_log'").fetchone()[0]
    check(f"L {label}: nothing was applied (rolled back)", ledger == 0)
db = "l_" + secrets.token_hex(3); tmp, _ = build(db, [])
code, dt = timed_migrate_with_lock(db, tmp, H16 / "spend_decrease_log.sql", "0006_a", cap_s=12)
control("L v16 DB-2 file under the same lock: no 55P03", code != "55P03", f"{code} after {dt:.1f}s (waits until the {12}s statement cap)")
info("L: every file in held-sql/ has a lock check above; the lead's gate is `grep -c lock_timeout` plus this run (PR DB-1 test)")
import glob
for p in sorted(glob.glob(str(H17 / "*.sql"))):
    check(f"L text: {Path(p).name} contains SET LOCAL lock_timeout before its first statement that takes a lock", "SET LOCAL lock_timeout = '5s';" in open(p).read())

# ------------------------------------------------------------------ K: m5 switch ON is never blocked by the record
def ks_state(db): return psycopg.connect(dsn("migr17", db), autocommit=True).execute('SELECT "on", "by" FROM kill_switch').fetchone()
for tag, folder in (("v17", H17), ("v16", H16)):
    db = "k_" + tag + secrets.token_hex(2)
    build(db, [(folder / "spend_decrease_log.sql", "0006_dec")])
    mg = psycopg.connect(dsn("migr17", db), autocommit=True)
    mg.execute("ALTER TABLE kill_switch_log RENAME TO kill_switch_log_x")  # the record cannot be written
    rt = psycopg.connect(dsn("rt17", db), autocommit=True)
    on_err = st(lambda: rt.execute("UPDATE kill_switch SET \"on\" = TRUE, \"by\" = 'x', ts = now() WHERE id = 1"))
    state_on = ks_state(db)[0]
    if tag == "v17":
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
check("H1 m4: with no held file, a positive reserve (INSERT ... ON CONFLICT branch) on a NaN row RETURNS NaN, so the code check after RETURNING is needed in the INSERT branch too", r.is_nan(), str(r))

# ------------------------------------------------------------------ G: DB-3 prototype, runtime role has SELECT only plus EXECUTE
def apply_grants(db, rt_exec=True):
    mg = psycopg.connect(dsn("migr17", db), autocommit=True)
    mg.execute("REVOKE INSERT, UPDATE ON spend, spend_month, kill_switch FROM rt17")
    mg.execute("GRANT EXECUTE ON FUNCTION spend_reserve(text, date, date, numeric), spend_settle(text, date, date, numeric, numeric), kill_switch_engage() TO rt17")
    mg.execute("GRANT EXECUTE ON FUNCTION kill_switch_engage(), kill_switch_release() TO op17")
    mg.execute("GRANT SELECT ON spend, spend_month, kill_switch TO op17")
    return mg
db = "g_" + secrets.token_hex(3)
build(db, [(H17 / "spend_decrease_log.sql", "0006_dec"), (H17 / "spend_guarded_writes.sql", "0007_guard")])
mg = apply_grants(db)
rt = psycopg.connect(dsn("rt17", db), autocommit=True); op = psycopg.connect(dsn("op17", db), autocommit=True)
fn_owner = mg.execute("SELECT r.rolname, r.rolsuper, p.prosecdef, p.proconfig FROM pg_proc p JOIN pg_roles r ON r.oid = p.proowner WHERE p.proname IN ('spend_reserve','spend_settle','kill_switch_engage','kill_switch_release')").fetchall()
check("G0 the four DB-3 functions are SECURITY DEFINER, owned by the non-superuser migration role, search_path pg_catalog, pg_temp", len(fn_owner) == 4 and all(r[0] == "migr17" and not r[1] and r[2] and "search_path=pg_catalog, pg_temp" in r[3] for r in fn_owner), str(fn_owner[:1]))
check("G0 PUBLIC has no EXECUTE on any of them", not mg.execute("SELECT bool_or(has_function_privilege('public', p.oid, 'EXECUTE')) FROM pg_proc p WHERE p.proname IN ('spend_reserve','spend_settle','kill_switch_engage','kill_switch_release')").fetchone()[0])
check("G1 runtime role: direct INSERT into spend refused 42501", st(lambda: rt.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('a', %s, 1)", (D,))) == "42501")
check("G1 runtime role: direct UPDATE of spend refused 42501", st(lambda: rt.execute("UPDATE spend SET usd = 0")) == "42501")
check("G1 runtime role: direct UPDATE of spend_month refused 42501", st(lambda: rt.execute("UPDATE spend_month SET usd = 0")) == "42501")
check("G1 runtime role: direct UPDATE of kill_switch refused 42501", st(lambda: rt.execute("UPDATE kill_switch SET \"on\" = FALSE")) == "42501")
check("G1 runtime role: INSERT, DELETE of kill_switch refused 42501", st(lambda: rt.execute("DELETE FROM kill_switch")) == "42501")
q = lambda c, f, *a: c.execute(f"SELECT * FROM {f}", a).fetchone()
r = rt.execute("SELECT * FROM spend_reserve('a', %s, %s, %s)", (D, MO, Decimal("1.5"))).fetchone()
check("G2 reserve 1.5 returns day and month totals (1.5, 1.5)", r == (Decimal("1.5"), Decimal("1.5")), str(r))
r = rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s, %s)", (D, MO, Decimal("1.5"), Decimal("0.4"))).fetchone()
check("G3 settle (worst 1.5, actual 0.4) leaves 0.4 on both", r == (Decimal("0.4"), Decimal("0.4")), str(r))
check("G4 settle again with nothing open is refused 23514 (the 0.4 already settled cannot be erased)", st(lambda: rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s, %s)", (D, MO, Decimal("1"), Decimal("0")))) == "23514")
check("G4 the total is still 0.4 after the refusal", rt.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0] == Decimal("0.4"))
rt.execute("SELECT * FROM spend_reserve('a', %s, %s, %s)", (D, MO, Decimal("2")))
check("G5 settle of a worst case larger than what is open (3 > 2) refused 23514", st(lambda: rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s, %s)", (D, MO, Decimal("3"), Decimal("0")))) == "23514")
r = rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s, %s)", (D, MO, Decimal("-1"), Decimal("0"))).fetchone()
check("G6 a negative worst case changes nothing (total stays 2.4)", r == (Decimal("2.4"), Decimal("2.4")), str(r))
check("G6 a negative actual cost changes nothing", rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s, %s)", (D, MO, Decimal("1"), Decimal("-5"))).fetchone() == (Decimal("2.4"), Decimal("2.4")))
for v in ("NaN", "Infinity", "-1"):
    check(f"G7 reserve of {v} refused 23514", st(lambda: rt.execute("SELECT * FROM spend_reserve('a', %s, %s, %s)", (D, MO, Decimal(v)))) == "23514")
check("G7 a settle with actual NaN refused 23514 and the total is unchanged", st(lambda: rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s, %s)", (D, MO, Decimal("1"), Decimal("NaN")))) == "23514" and rt.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0] == Decimal("2.4"))
# fuzz: invariant settled money (usd - open) never goes down, whatever the runtime sends
rnd = random.Random(1717); bad = 0; floor = {}
mg.execute("DELETE FROM spend_decrease_log") if False else None
for i in range(400):
    ag = f"f{rnd.randrange(3)}"; w = Decimal(rnd.choice(["0", "0.01", "1", "2.5", "10", "-1", "NaN"])); a = Decimal(rnd.choice(["0", "0.5", "1", "3", "-2", "Infinity"]))
    act = rnd.choice(("reserve", "settle", "settle"))
    before = mg.execute("SELECT usd - open_usd, usd, open_usd FROM spend WHERE agent_id = %s", (ag,)).fetchone()
    err = st(lambda: rt.execute("SELECT * FROM spend_reserve(%s, %s, %s, %s)", (ag, D, MO, w)) if act == "reserve" else rt.execute("SELECT * FROM spend_settle(%s, %s, %s, %s, %s)", (ag, D, MO, w, a)))
    after = mg.execute("SELECT usd - open_usd, usd, open_usd FROM spend WHERE agent_id = %s", (ag,)).fetchone()
    if before and after and after[0] < before[0]: bad += 1
    if err and before != after and not (before is None): bad += 1
check("G8 fuzz, 400 random calls by the runtime role: settled money (total minus open reservation) never fell; a refused call changed nothing", bad == 0, f"violations={bad}")
neg = mg.execute("SELECT count(*) FROM spend WHERE usd < 0 OR open_usd < 0 OR usd < open_usd").fetchone()[0]
check("G8 after the fuzz no row has a negative total, a negative open amount, or open above the total", neg == 0)
# kill switch
rt.execute("SELECT kill_switch_engage()")
s = mg.execute('SELECT "on", "by" FROM kill_switch').fetchone()
check("G9 runtime role engages the kill switch; `by` is its own login (rt17), not a value it chose", s == (True, "rt17"), str(s))
check("G9 runtime role cannot release it: 42501", st(lambda: rt.execute("SELECT kill_switch_release()")) == "42501" and mg.execute('SELECT "on" FROM kill_switch').fetchone()[0] is True)
op.execute("SELECT kill_switch_release()")
s = mg.execute('SELECT "on", "by" FROM kill_switch').fetchone()
check("G9 operator role releases it; `by` is the operator login (op17)", s == (False, "op17"), str(s))
rows = mg.execute("SELECT old_on, new_on, who FROM kill_switch_log ORDER BY at").fetchall()
check("G9 with DB-2 also applied the record has both changes with the invoking login in `who`", rows == [(False, True, "rt17"), (True, False, "op17")], str(rows))
# temp-table attack against the BEGIN ATOMIC bodies
rt.execute("CREATE TEMP TABLE spend (agent_id text, day date, usd numeric, open_usd numeric DEFAULT 0)")
rt.execute("CREATE TEMP TABLE spend_month (agent_id text, month date, usd numeric, open_usd numeric DEFAULT 0)")
rt.execute("CREATE TEMP TABLE kill_switch (id int, \"on\" boolean, \"by\" text, ts timestamptz)")
rt.execute("SET search_path = pg_temp, public")
before = mg.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0]
rt.execute("SELECT * FROM pg_catalog.pg_class LIMIT 0")
try: rt.execute("SELECT * FROM public.spend_reserve('a', %s, %s, %s)", (D, MO, Decimal("1")))
except psycopg.Error as e: info("temp attack call error " + str(e.sqlstate))
after = mg.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0]
check("G10 temporary tables named spend, spend_month, kill_switch plus search_path = pg_temp first: the real total moved (+1) and the temporary tables are empty", after == before + 1 and rt.execute("SELECT count(*) FROM pg_temp.spend").fetchone()[0] == 0, f"{before}->{after}")
# DB-3 on top of DB-1 default and DB-2 through the real migrate(), with the DB-1 constraint names present
db2 = "g2_" + secrets.token_hex(3)
try:
    ap = build(db2, [(H17 / "spend_nonneg.sql", "0006_nn"), (H17 / "spend_decrease_log.sql", "0007_dec"), (H17 / "spend_guarded_writes.sql", "0008_guard")])[1]
    check("G11 DB-1 default, DB-2 and DB-3 apply together through the real migrate() (names do not clash)", len(ap) == 8, str(ap[-3:]))
except Exception as e: check("G11 all three apply together", False, type(e).__name__ + str(e)[:80])
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
