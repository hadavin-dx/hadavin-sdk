"""v20 Postgres checks (v19 checks kept; the section "v20" before the SUMMARY adds the real-server proofs of the round-6 findings; the one v19 check that is now wrong, the NFC spelling, is rewritten) -- v19 Postgres checks (v18 checks kept, fixed or extended; new: real-server proofs of the MA1 and MA2 bypasses, m1 INSERT record, m2 settle without a day row, m6 separate counts, m7 statement_timeout) on the real migrate() code of src/ (read only), throwaway cluster, password logins only.
Usage: python pg_v18.py <socket_dir> <src_dir> <held_dir_v18> <held_dir_v16> (the v17 held files are read from ../evidence-handoff-v17/held-sql as the CONTROL) (admin password in HV_ADMIN_PW). One line per check: PASS/FAIL/INFO.
Prototype checks, made-up data. The v16 DB-2 file is run as a CONTROL: a new check must FAIL on it (line starts CONTROL)."""
import atexit, sys, os, tempfile, shutil, time, secrets, random
from datetime import date
from decimal import Decimal
from pathlib import Path
sock, src, H17, H16 = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
HOLD17 = Path(__file__).resolve().parent.parent / 'evidence-handoff-v17' / 'held-sql'
HOLD18 = Path(__file__).resolve().parent.parent / "evidence-handoff-v18" / "held-sql"
HOLD19 = Path(__file__).resolve().parent.parent / "evidence-handoff-v19" / "held-sql"  # the v18 files, only for controls of the v19 changes  # the v17 files, only for controls
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, src)
import psycopg
from psycopg import sql
import hadavin_sdk.store.migrate as m
PW, res, resc, ress = {}, [], [], []  # res: safety checks; resc: controls (old design shows the old behaviour); ress: exploits that are STATED and shown, not pass/fail of a safety property
D, MO = date(2026, 11, 16), date(2026, 11, 1)
def check(name, ok, detail=""):
    res.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)
def control(name, failed_as_expected, detail=""):
    resc.append(bool(failed_as_expected)); print(("CONTROL-OK (the old design or old check does not pass the new assertion; the text names which) " if failed_as_expected else "CONTROL-FAIL (the old design passed the new assertion, so the new check proves nothing) ") + name + (f"  [{detail}]" if detail else ""), flush=True)
def stated(name, shown, detail=""):
    ress.append(bool(shown)); print(("STATED-SHOWN (an exploit that is NOT closed works as described; this line is not a pass of a safety check) " if shown else "STATED-NOT-SHOWN (the exploit did not work: the text must change) ") + name + (f"  [{detail}]" if detail else ""), flush=True)
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
import secdef_audit_v20 as au
import secdef_guard_v18 as g18, secdef_guard_v19 as g19, secdef_guard_v20 as g20
import allow_v20 as A20
from allow_v19 import ALLOWED_BY_FILE, ATOMIC_TABLES_BY_FILE
import shutil
ROLES = {'runtime': 'rt17', 'operator': 'op17'}
def build(db, files, base=True):
    """files: list of (path, number-name). Fresh database owned by the non-superuser migration role; real 0001-0005 then the files."""
    if base: admin.execute(f"CREATE DATABASE {db} OWNER migr17")
    tmp = Path(tempfile.mkdtemp(prefix="v19mig_")); atexit.register(shutil.rmtree, tmp, True)
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
    ("DB-2 v19 spend_decrease_log", "spend_decrease_log.sql", "0006_a", None),
    ("DB-3 v19 spend_guarded_writes", "spend_guarded_writes.sql", "0006_a", None)):
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
for tag, folder in (("v19", H17), ("v16", H16)):
    db = "k_" + tag + secrets.token_hex(2)
    build(db, [(folder / "spend_decrease_log.sql", "0006_dec")])
    mg = psycopg.connect(dsn("migr17", db), autocommit=True)
    mg.execute("ALTER TABLE kill_switch_log RENAME TO kill_switch_log_x")  # the record cannot be written
    rt = psycopg.connect(dsn("rt17", db), autocommit=True)
    on_err = st(lambda: rt.execute("UPDATE kill_switch SET \"on\" = TRUE, \"by\" = 'x', ts = now() WHERE id = 1"))
    state_on = ks_state(db)[0]
    if tag == "v19":
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
for tag, folder in (("v19", H17), ("v17", HOLD17)):
    db = "q_" + tag + secrets.token_hex(2); build(db, [(folder / "spend_decrease_log.sql", "0006_dec")])
    rtq = psycopg.connect(dsn("rt17", db), autocommit=True)
    hold = psycopg.connect(dsn("migr17", db)); hold.execute("LOCK TABLE kill_switch_log IN ACCESS EXCLUSIVE MODE")
    rtq.execute("SET statement_timeout = 1500")
    on_err = st(lambda: rtq.execute("UPDATE kill_switch SET \"on\" = TRUE, \"by\" = 'x', ts = now() WHERE id = 1"))
    hold.rollback(); hold.close(); on_state = ks_state(db)[0]
    if tag == "v19":
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
for v in ("NaN", "Infinity"):
    check(f"G7 reserve of {v} refused 23514", st(lambda: rt.execute("SELECT * FROM spend_reserve('a', %s, %s)", (D, Decimal(v)))) == "23514")
_ua = mg.execute("SELECT usd, open_usd FROM spend WHERE agent_id='a'").fetchone()
check("G7 reserve of -1: v19 refuses it by writing nothing (the function returns the unchanged totals, v18 raised 23514): total and open amount of the agent unchanged", rt.execute("SELECT * FROM spend_reserve('a', %s, %s)", (D, Decimal("-1"))).fetchall() == [(_ua[0], mg.execute("SELECT usd FROM spend_month WHERE agent_id='a'").fetchone()[0])] and mg.execute("SELECT usd, open_usd FROM spend WHERE agent_id='a'").fetchone() == _ua)
check("G7 a settle with actual NaN refused 23514 and the total is unchanged", st(lambda: rt.execute("SELECT * FROM spend_settle('a', %s, %s, %s)", (D, Decimal("1"), Decimal("NaN")))) == "23514" and rt.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0] == Decimal("2.4"))
# unbounded inputs (coordinator item 4)
check("G12 a reserve of 1000000000000 (the ceiling) refused 23514, 999999999999 accepted", st(lambda: rt.execute("SELECT * FROM spend_reserve('big', %s, %s)", (D, Decimal("1000000000000")))) == "23514" and st(lambda: rt.execute("SELECT * FROM spend_reserve('big', %s, %s)", (D, Decimal("999999999999")))) is None)
check("G12 an agent_id of length 0 or 201 refused 23514", st(lambda: rt.execute("SELECT * FROM spend_reserve('', %s, %s)", (D, Decimal("1")))) == "23514" and st(lambda: rt.execute("SELECT * FROM spend_reserve(%s, %s, %s)", ("x" * 201, D, Decimal("1")))) == "23514")
r_nob = rt.execute("SELECT * FROM spend_settle('nobody', %s, %s, %s)", (D, Decimal("1"), Decimal("0"))).fetchall()
check("G12 a settle for an agent that has no row returns no row and writes no row in spend or spend_month (v18 passed this check through an `or True` for a no-op; v19 checks the rows)", r_nob == [] and mg.execute("SELECT (SELECT count(*) FROM spend WHERE agent_id='nobody'), (SELECT count(*) FROM spend_month WHERE agent_id='nobody')").fetchone() == (0, 0), str(r_nob))
a_before = mg.execute("SELECT usd, open_usd FROM spend WHERE agent_id='a'").fetchone(); rt.execute("SELECT * FROM spend_reserve('victim', %s, %s)", (D, Decimal("5")))
rt.execute("SELECT * FROM spend_settle('victim', %s, %s, %s)", (D, Decimal("5"), Decimal("0")))
stated("G12 the runtime login can settle (give back) a reservation it made under ANY agent_id name, e.g. 'victim' (the control is per-agent logins, L-4, and the invoice comparison)", mg.execute("SELECT usd FROM spend WHERE agent_id='victim'").fetchone()[0] == 0)

# ---- v19 m2: a settle for a DAY that has no row must not change the MONTH row
rt.execute("SELECT * FROM spend_reserve('m2a', %s, %s)", (D, Decimal("5"))); D2 = date(2026, 11, 20)
mb = mg.execute("SELECT usd, open_usd FROM spend_month WHERE agent_id='m2a'").fetchone()
r2 = rt.execute("SELECT * FROM spend_settle('m2a', %s, %s, %s)", (D2, Decimal("5"), Decimal("0"))).fetchall()
ma = mg.execute("SELECT usd, open_usd FROM spend_month WHERE agent_id='m2a'").fetchone()
check("G12 m2 a settle for another day of the same month that has no day row returns no row and leaves the month row (usd and open) unchanged", r2 == [] and ma == mb == (Decimal("5"), Decimal("5")), f"before {mb} after {ma}")
rt.execute("SELECT * FROM spend_settle('m2a', %s, %s, %s)", (D, Decimal("5"), Decimal("0")))
check("G12 m2 the honest settle of the real day still works afterwards (month back to 0 and open 0)", mg.execute("SELECT usd, open_usd FROM spend_month WHERE agent_id='m2a'").fetchone() == (Decimal("0"), Decimal("0")))
# ---- v19 independent-runner observations: day window, amount 0, agent id spellings
for lbl, dv in (("infinity", "infinity"), ("-infinity", "-infinity"), ("1999-01-01", "1999-01-01"), ("0001-01-01", "0001-01-01"), ("2100-01-01", "2100-01-01")):
    check(f"G12 a reserve for the day {lbl} is refused 23514", st(lambda: rt.execute("SELECT * FROM spend_reserve('dw', %s::date, %s)", (dv, Decimal("1")))) == "23514")
check("G12 a reserve of 0 writes no row and returns no row", rt.execute("SELECT * FROM spend_reserve('zero0', %s, %s)", (D, Decimal("0"))).fetchall() == [] and mg.execute("SELECT count(*) FROM spend WHERE agent_id='zero0'").fetchone()[0] == 0)
import unicodedata
for lbl, nm in (("NFD cafe + combining accent", unicodedata.normalize("NFD", "caf\u00e9")), ("whitespace only", "   "), ("leading blank", " a1"), ("newline", "a\nb"), ("tab and quote", "a\t\"b")):
    check(f"G12 the agent id {lbl} is refused 23514", st(lambda: rt.execute("SELECT * FROM spend_reserve(%s, %s, %s)", (nm, D, Decimal("1")))) == "23514")
for lbl, nm in (("NFC cafe (non-ASCII)", unicodedata.normalize("NFC", "caf\u00e9")), ("fullwidth A", "\uff21b"), ("zero-width space", "a\u200bb"), ("NBSP at the start", "\u00a0a"), ("right-to-left override", "a\u202eb"), ("NEL control U+0085", "a\u0085b"), ("a space inside", "a b"), ("DEL", "a\x7fb"), ("201 characters", "a" * 201), ("empty", "")):
    check(f"G12 v20 the agent id {lbl} is refused 23514 (ASCII allow-list; v19 accepted the first six as separate budgets)", st(lambda: rt.execute("SELECT * FROM spend_reserve(%s, %s, %s)", (nm, D, Decimal("1")))) == "23514")
for nm in ("a", "Agent_1.x:y@z/q+w-1", "a" * 200):
    check(f"G12 v20 the agent id {nm[:20]!r} ({len(nm)} characters) is accepted", st(lambda: rt.execute("SELECT * FROM spend_reserve(%s, %s, %s)", (nm, D, Decimal("1")))) is None)
rt.execute("SELECT * FROM spend_reserve('Case', %s, %s)", (D, Decimal("1"))); rt.execute("SELECT * FROM spend_reserve('case', %s, %s)", (D, Decimal("1")))
stated("G12 agent ids that differ only in letter case ('Case' and 'case') are two budgets (names come from configuration in our code; a hostile login can pick any name anyway)", mg.execute("SELECT count(*) FROM spend WHERE lower(agent_id)='case'").fetchone()[0] == 2)
tb = mg.execute("SELECT usd FROM spend WHERE agent_id='victim'").fetchone()
rt.execute("SELECT * FROM spend_settle('victim', %s, %s, %s)", (D, Decimal("0"), Decimal("5")))
stated("G12 a settle with worst 0 and actual 5 RAISES a total with no reservation (it can only over-report spend, never hide it; ceiling 1e12 still holds)", mg.execute("SELECT usd FROM spend WHERE agent_id='victim'").fetchone()[0] == tb[0] + 5)
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

lr = mg.execute("SELECT old_on, new_on, old_by, new_by, who FROM kill_switch_log ORDER BY at DESC LIMIT 1").fetchone()
check("G9 m1 the INSERT of a missing switch row is recorded (old state read as ON, new ON, who = rt17)", lr == (True, True, None, "rt17", "rt17"), str(lr))
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
tmp7 = Path(tempfile.mkdtemp(prefix="v19mig_")); atexit.register(shutil.rmtree, tmp7, True)
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

# ------------------------------------------------------------------ controls on the v18 files (each v19 change must FAIL on the v18 file)
db8 = "c8_" + secrets.token_hex(3); build(db8, [(HOLD18 / "spend_decrease_log.sql", "0006_dec"), (HOLD18 / "spend_guarded_writes.sql", "0007_guard")])
mg8 = psycopg.connect(dsn("migr17", db8), autocommit=True); mg8.execute("GRANT EXECUTE ON FUNCTION spend_reserve(text,date,numeric), spend_settle(text,date,numeric,numeric), kill_switch_engage() TO rt17"); rt8 = psycopg.connect(dsn("rt17", db8), autocommit=True)
rt8.execute("SELECT * FROM spend_reserve('m2a', %s, %s)", (D, Decimal("5"))); rt8.execute("SELECT * FROM spend_settle('m2a', %s, %s, %s)", (D2, Decimal("5"), Decimal("0")))
control("G12 m2 v18 DB-3 file: a settle for a day without a row LOWERS the month row (usd 5 -> 0) while the day row stays 5", mg8.execute("SELECT usd FROM spend_month WHERE agent_id='m2a'").fetchone()[0] == 0 and mg8.execute("SELECT usd FROM spend WHERE agent_id='m2a'").fetchone()[0] == 5)
control("G12 v18 DB-3 file: a reserve for the day 'infinity' is accepted", st(lambda: rt8.execute("SELECT * FROM spend_reserve('dw', 'infinity'::date, %s)", (Decimal("1"),))) is None)
control("G12 v18 DB-3 file: a reserve of 0 creates a row", (rt8.execute("SELECT * FROM spend_reserve('zero0', %s, %s)", (D, Decimal("0"))).fetchall() or True) and mg8.execute("SELECT count(*) FROM spend WHERE agent_id='zero0'").fetchone()[0] == 1)
control("G12 v18 DB-3 file: an NFD agent id and a newline agent id are accepted", st(lambda: rt8.execute("SELECT * FROM spend_reserve(%s, %s, %s)", (unicodedata.normalize("NFD", "caf\u00e9"), D, Decimal("1")))) is None and st(lambda: rt8.execute("SELECT * FROM spend_reserve(%s, %s, %s)", ("a\nb", D, Decimal("1")))) is None)
n0 = mg8.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0]; mg8.execute("DELETE FROM kill_switch"); rt8.execute("SELECT kill_switch_engage()")
control("G9 m1 v18 DB-2 file: the INSERT of a missing switch row writes no record", mg8.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] == n0)
# K-insert: the record never stops a switch ON that arrives by INSERT; a switch OFF by INSERT is refused when the record cannot be written
dbi = "ki_" + secrets.token_hex(3); build(dbi, [(H17 / "spend_decrease_log.sql", "0006_dec")])
mgi = psycopg.connect(dsn("migr17", dbi), autocommit=True); rti = psycopg.connect(dsn("rt17", dbi), autocommit=True)
mgi.execute("DELETE FROM kill_switch"); mgi.execute("ALTER TABLE kill_switch_log RENAME TO kill_switch_log_x")
e_on = st(lambda: rti.execute("INSERT INTO kill_switch (id, schema_version, \"on\", \"by\", ts) VALUES (1, 1, true, 'x', now())"))
check("K m1 with the record unwritable, an INSERT of a switch row that is ON still works", e_on is None and mgi.execute('SELECT "on" FROM kill_switch').fetchone()[0] is True, f"err={e_on}")
mgi.execute("DELETE FROM kill_switch")
e_off = st(lambda: rti.execute("INSERT INTO kill_switch (id, schema_version, \"on\", \"by\", ts) VALUES (1, 1, false, 'x', now())"))
check("K m1 with the record unwritable, an INSERT of a switch row that is OFF is refused (fail closed) and no row exists", e_off is not None and mgi.execute("SELECT count(*) FROM kill_switch").fetchone()[0] == 0, f"err={e_off}")
mgi.execute("ALTER TABLE kill_switch_log_x RENAME TO kill_switch_log")
rti.execute("INSERT INTO kill_switch (id, schema_version, \"on\", \"by\", ts) VALUES (1, 1, false, 'x', now())")
check("K m1 with the record writable, an INSERT of a switch row that is OFF is recorded as old ON, new OFF", mgi.execute("SELECT old_on, new_on, who FROM kill_switch_log ORDER BY at DESC LIMIT 1").fetchone() == (True, False, "rt17"))
# m7: SET LOCAL statement_timeout lasts for the migration transaction only
cx = psycopg.connect(dsn("migr17", dbi)); cx.execute("SET LOCAL statement_timeout = '60s'"); in_tx = cx.execute("SHOW statement_timeout").fetchone()[0]; cx.commit(); after_tx = cx.execute("SHOW statement_timeout").fetchone()[0]
check("L m7 SET LOCAL statement_timeout = '60s' holds inside the transaction and is gone after it (so it cannot leak to the next file or the runtime)", in_tx == "1min" and after_tx == "0", f"{in_tx} then {after_tx}")
check("L m7 text: the DB-3 file has SET LOCAL statement_timeout as its second statement, after the lock_timeout line", [l for l in open(H17 / "spend_guarded_writes.sql").read().splitlines() if l.strip() and not l.lstrip().startswith("--")][1].strip() == "SET LOCAL statement_timeout = '60s';")

# ------------------------------------------------------------------ MA1 and MA2 of the v18 review: the bypasses are REAL on this server (16.15), the v18 guard passes them, the v19 guard flags them
dbp = "ma_" + secrets.token_hex(3); build(dbp, []); mgp = psycopg.connect(dsn("migr17", dbp), autocommit=True)
def both(text, allowed, file="x.sql"):
    return (bool(g18.check_sql_text(file, text, allowed)), bool(g19.check_sql_text(file, text, allowed, atomic_tables=ATOMIC_TABLES_BY_FILE.get(file))))
for lbl, stmt, probe in (('SET "role" TO rt17 (quoted name)', 'SET "role" TO rt17', None), ("SET session_authorization TO rt17 (one underscore word)", "SET session_authorization TO rt17", None), ("SELECT set_config('role','rt17',false)", "SELECT set_config('role','rt17',false)", None)):
    admin.execute("RESET ALL"); admin.execute(stmt); cu = admin.execute("SELECT current_user, session_user").fetchone(); admin.execute("RESET ALL")
    f18, f19 = both(stmt + ";\n", {})
    check(f"MA1 real server: {lbl} changes the session identity on 16.15 (current_user, session_user = {cu}); v18 guard flags it = {f18}; v19 guard flags it = {f19}", (cu[0] == "rt17" or cu[1] == "rt17") and f19)
    if f18: info(f"MA1 note: the v18 guard already flagged: {lbl}")
mgp.execute("CREATE TABLE public.secret_t (v text)"); mgp.execute("INSERT INTO public.secret_t VALUES ('made-up-secret')")
LEAK = "CREATE OR REPLACE FUNCTION leak(q text) RETURNS xml LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT query_to_xml(q, true, false, '') $f$;\nREVOKE ALL ON FUNCTION leak(text) FROM PUBLIC;\nGRANT EXECUTE ON FUNCTION leak(text) TO rt17;\n"
mgp.execute(LEAK.split("\n")[0]); mgp.execute("REVOKE ALL ON FUNCTION leak(text) FROM PUBLIC"); mgp.execute("GRANT EXECUTE ON FUNCTION leak(text) TO rt17")
rtp = psycopg.connect(dsn("rt17", dbp), autocommit=True)
direct = st(lambda: rtp.execute("SELECT * FROM public.secret_t")); via = rtp.execute("SELECT leak('select * from public.secret_t')").fetchone()[0]
f18, f19 = both(LEAK.replace("\nGRANT EXECUTE ON FUNCTION leak(text) TO rt17;\n", "\n"), {"leak(text)": "definer"})
check(f"MA1d real server: the runtime role cannot read secret_t directly ({direct}) but a definer function calling query_to_xml hands it the row; v18 guard flags the function = {f18}; v19 guard flags it = {f19}", direct == "42501" and "made-up-secret" in str(via) and f19 and not f18)
mgp.execute("CREATE OR REPLACE FUNCTION pf() RETURNS int LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT 1 $f$"); mgp.execute("REVOKE ALL ON FUNCTION pf() FROM PUBLIC")
before = rtp.execute("SELECT has_function_privilege('rt17', 'pf()', 'EXECUTE')").fetchone()[0]
mgp.execute("DROP FUNCTION pf()"); mgp.execute("CREATE OR REPLACE FUNCTION pf() RETURNS int LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT 1 $f$")
after = rtp.execute("SELECT has_function_privilege('rt17', 'pf()', 'EXECUTE')").fetchone()[0]
DR = "REVOKE ALL ON FUNCTION pf() FROM PUBLIC;\nDROP FUNCTION pf();\nCREATE OR REPLACE FUNCTION pf() RETURNS int LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT 1 $f$;\n"
f18, f19 = both(DR, {"pf()": "definer"})
check(f"MA1a real server: after REVOKE, DROP, CREATE OR REPLACE the runtime role may run the function (before {before}, after {after}); v18 guard flags the text = {f18}; v19 guard flags it = {f19}", before is False and after is True and f19 and not f18)
mgp.execute("CREATE SCHEMA other_schema"); mgp.execute("CREATE OR REPLACE FUNCTION other_schema.spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS int LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT 1 $f$")
mgp.execute("GRANT USAGE ON SCHEMA other_schema TO rt17"); runs = rtp.execute("SELECT other_schema.spend_reserve('a', '2026-11-16', 1)").fetchone()[0]
SP2 = "CREATE OR REPLACE FUNCTION other_schema.spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp BEGIN ATOMIC SELECT 1; END;\nREVOKE ALL ON FUNCTION spend_reserve(text, date, numeric) FROM PUBLIC;\n"
f18, f19 = both(SP2, {"spend_reserve(text,date,numeric)": "definer"}, "spend_guarded_writes.sql")
check(f"MA2 real server: a definer function in another schema with the listed name has default PUBLIC execute and the runtime role runs it ({runs}); v18 guard flags the text = {f18}; v19 guard flags it = {f19}", runs == 1 and f19 and not f18)

# ================================================================== v20 (round 6): real-server proofs. Each "v19 guard clean" claim is computed here with the v19 guard module; each fix is computed with the v20 guard.
import warnings
def g20f(text, allowed, file="x.sql", **kw): return bool(g20.check_sql_text(file, text, allowed, atomic_tables=ATOMIC_TABLES_BY_FILE.get(file), **kw))
def g19f(text, allowed, file="x.sql"): return bool(g19.check_sql_text(file, text, allowed, atomic_tables=ATOMIC_TABLES_BY_FILE.get(file)))
PIN = g20.PIN_ANY
SPX = "SET search_path = pg_catalog, pg_temp"
def section(name):
    info("---- " + name)
def fresh_g(tag, files=None):
    db = tag + "_" + secrets.token_hex(3)
    files = files or [(H17 / "spend_decrease_log.sql", "0006_dec"), (H17 / "spend_guarded_writes.sql", "0007_guard")]
    t, mgx, _, _ = new_g(db, files)
    return db, mgx, psycopg.connect(dsn("rt17", db), autocommit=True), psycopg.connect(dsn("op17", db), autocommit=True)
try:
    section("B1 RETURN-form definer (security B1): the v19 guard passes it, the server runs it as the owner")
    dbb, mgb, rtb, opb = fresh_g("b1")
    mgb.execute("CREATE TABLE public.secret_t (v text)"); mgb.execute("INSERT INTO public.secret_t VALUES ('made-up-secret')")
    B1 = f"CREATE OR REPLACE FUNCTION leak2(q text) RETURNS xml LANGUAGE sql SECURITY DEFINER {SPX} RETURN query_to_xml(q, true, false, '');\nREVOKE ALL ON FUNCTION leak2(text) FROM PUBLIC;\n"
    mgb.execute(B1.split("\n")[0]); mgb.execute("REVOKE ALL ON FUNCTION leak2(text) FROM PUBLIC"); mgb.execute("GRANT EXECUTE ON FUNCTION leak2(text) TO rt17")
    direct = st(lambda: rtb.execute("SELECT * FROM public.secret_t")); via = str(rtb.execute("SELECT leak2('select * from public.secret_t')").fetchone()[0])
    f19, f20 = g19f(B1, {"leak2(text)": "definer"}), g20f(B1, {"leak2(text)": "definer"}, fn_pins=PIN, kinds=PIN, trigger_pins=PIN)
    check(f"B1 real server: a RETURN-form definer hands the runtime role a row it cannot read ({direct} direct); v19 guard flags it = {f19}; v20 guard flags it = {f20}", direct == "42501" and "made-up-secret" in via and not f19 and f20)
    RESB = f"CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS xml LANGUAGE sql SECURITY DEFINER {SPX} RETURN query_to_xml(p_agent, true, false, '');\nREVOKE ALL ON FUNCTION spend_reserve(text, date, numeric) FROM PUBLIC;\n"
    f19, f20 = g19f(RESB, {"spend_reserve(text,date,numeric)": "definer"}, "spend_guarded_writes.sql"), g20f(RESB, {"spend_reserve(text,date,numeric)": "definer"}, "spend_guarded_writes.sql", fn_pins=PIN, kinds=PIN, trigger_pins=PIN)
    check(f"B1 the reviewer's exact case (RETURN query_to_xml(p_agent, ...) as spend_reserve in the DB-3 file): v19 guard flags it = {f19}; v20 guard flags it = {f20}", not f19 and f20)

    section("M1 %I.name( in an EXECUTE string (security M1)")
    mgb.execute("CREATE TABLE public.tt (a int, b int)"); mgb.execute("INSERT INTO public.tt VALUES (1, 1)"); mgb.execute("GRANT SELECT, UPDATE ON public.tt TO rt17")
    mgb.execute("CREATE FUNCTION public.evil_fn(int) RETURNS int LANGUAGE sql AS $f$ INSERT INTO public.secret_t VALUES ('written-by-definer') RETURNING 1 $f$")
    M1F = f"CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER {SPX} AS $f$ BEGIN EXECUTE format('SELECT %I.evil_fn($1)', TG_TABLE_SCHEMA) USING NEW.a; RETURN NULL; END $f$;\nREVOKE ALL ON FUNCTION spend_log_decrease() FROM PUBLIC;\n"
    mgb.execute(M1F.split("\nREVOKE")[0].replace("spend_log_decrease", "m1_trig")); mgb.execute("CREATE TRIGGER m1_t AFTER UPDATE ON public.tt FOR EACH ROW EXECUTE FUNCTION m1_trig()")
    d_before = st(lambda: rtb.execute("INSERT INTO public.secret_t VALUES ('x')")); rtb.execute("UPDATE public.tt SET b = 2")
    wrote = mgb.execute("SELECT count(*) FROM public.secret_t WHERE v = 'written-by-definer'").fetchone()[0]
    f19, f20 = g19f(M1F, {"spend_log_decrease()": "definer"}, "spend_decrease_log.sql"), g20f(M1F, {"spend_log_decrease()": "definer"}, "spend_decrease_log.sql", fn_pins=PIN, kinds=PIN, trigger_pins=PIN)
    check(f"M1 real server: a definer trigger runs the hidden call `%I.evil_fn` with the owner's rights (the runtime role cannot insert into secret_t: {d_before}; one row written by the trigger: {wrote}); v19 guard flags it = {f19}; v20 guard flags it = {f20}", d_before == "42501" and wrote == 1 and not f19 and f20)

    section("M2 trigger drop and neutering (security M2)")
    dbm, mgm, rtm, opm = fresh_g("m2")
    mgm.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('t1', %s, 10)", (D,)); mgm.execute("UPDATE spend SET usd = 7 WHERE agent_id = 't1'")
    n1 = mgm.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
    DT = "DROP TRIGGER IF EXISTS spend_log_decrease ON spend;\n"; txt2 = open(H17 / "spend_decrease_log.sql").read()
    f19 = bool(g19.check_sql_text("spend_decrease_log.sql", txt2 + DT, ALLOWED_BY_FILE["spend_decrease_log.sql"], atomic_tables=None)); f20 = bool(A20.check(g20, "spend_decrease_log.sql", txt2 + DT))
    mgm.execute(DT); mgm.execute("UPDATE spend SET usd = 3 WHERE agent_id = 't1'")
    n2 = mgm.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
    check(f"M2 real server: before the DROP a lowering writes a record row ({n1}); after `DROP TRIGGER IF EXISTS` (clean in v19) the next lowering writes none ({n2}); v19 guard flags the file = {f19}; v20 guard flags it = {f20}", n1 == 1 and n2 == 1 and not f19 and f20)
    NEU = txt2 + "\nCREATE OR REPLACE TRIGGER spend_month_log_decrease AFTER UPDATE ON spend_month FOR EACH ROW WHEN (false) EXECUTE FUNCTION spend_log_decrease();\n"
    f19 = bool(g19.check_sql_text("spend_decrease_log.sql", NEU, ALLOWED_BY_FILE["spend_decrease_log.sql"], atomic_tables=None)); f20 = bool(A20.check(g20, "spend_decrease_log.sql", NEU))
    mgm.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('t1', %s, 10)", (MO,)); mgm.execute("CREATE OR REPLACE TRIGGER spend_month_log_decrease AFTER UPDATE ON spend_month FOR EACH ROW WHEN (false) EXECUTE FUNCTION spend_log_decrease()")
    k1 = mgm.execute("SELECT count(*) FROM spend_decrease_log WHERE scope='spend_month'").fetchone()[0]; mgm.execute("UPDATE spend_month SET usd = 1"); k2 = mgm.execute("SELECT count(*) FROM spend_decrease_log WHERE scope='spend_month'").fetchone()[0]
    check(f"M2 real server: CREATE OR REPLACE TRIGGER ... WHEN (false) neuters the month record (rows {k1} then {k2} after a lowering); v19 guard flags the file = {f19}; v20 guard flags it = {f20}", k1 == k2 and not f19 and f20)

    section("M3 MERGE INTO / DELETE USING / TABLE in an atomic body (security M3)")
    for lbl, body in (("MERGE INTO secret_t USING kill_switch", "MERGE INTO secret_t s USING kill_switch k ON true WHEN MATCHED THEN DELETE;"), ("DELETE FROM kill_switch USING secret_t", "DELETE FROM kill_switch USING secret_t WHERE true;"), ("TABLE secret_t", "TABLE secret_t;")):
        T = f"CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS {'void' if 'TABLE' not in lbl else 'text'} LANGUAGE sql SECURITY DEFINER {SPX} BEGIN ATOMIC {body} END;\nREVOKE ALL ON FUNCTION kill_switch_engage() FROM PUBLIC;\n"
        err = st(lambda: mgb.execute(T.split("\nREVOKE")[0].replace("kill_switch_engage", "m3f")))
        f19, f20 = g19f(T, {"kill_switch_engage()": "definer"}, "spend_guarded_writes.sql"), g20f(T, {"kill_switch_engage()": "definer"}, "spend_guarded_writes.sql", fn_pins=PIN, kinds=PIN, trigger_pins=PIN)
        info(f"M3 {lbl}: the server {'accepts it' if err is None else 'refuses it with ' + str(err)}; v19 guard flags it = {f19}; v20 guard flags it = {f20}")
        check(f"M3 {lbl}: v20 guard flags it, and the v19 guard did not (server verdict above)", f20 and not f19)
        if err is None: mgb.execute("DROP FUNCTION m3f()")

    section("M4 / F1 a replacement body of a listed definer (independent runner of v19)")
    txt3 = open(H17 / "spend_guarded_writes.sql").read()
    REPL = {"R01 DELETE FROM spend": 'DELETE FROM spend;', "R14 WITH d AS (DELETE ...) SELECT 1": "WITH d AS (DELETE FROM spend RETURNING 1) SELECT 1;"}
    dbf, mgf, rtf, opf = fresh_g("f1")
    rtf.execute("SELECT * FROM spend_reserve('victim', %s, %s)", (D, Decimal("4")))
    for lbl, body in REPL.items():
        T = txt3.replace('UPDATE kill_switch SET "on" = false, "by" = session_user, ts = clock_timestamp() WHERE id = 1 AND "on" = true;', body)
        f19 = bool(g19.check_sql_text("spend_guarded_writes.sql", T, ALLOWED_BY_FILE["spend_guarded_writes.sql"], atomic_tables=ATOMIC_TABLES_BY_FILE["spend_guarded_writes.sql"])); f20 = bool(A20.check(g20, "spend_guarded_writes.sql", T))
        body_sql = body
        mgf.execute(f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SPX} BEGIN ATOMIC {body_sql} END")
        opf.execute("SELECT kill_switch_release()"); left = mgf.execute("SELECT count(*) FROM spend").fetchone()[0]
        check(f"F1 real server: {lbl} as the body of kill_switch_release is accepted and the OPERATOR role's call leaves {left} rows in spend; v19 guard flags it = {f19}; v20 guard flags it = {f20}", left == 0 and not f19 and f20)
        rtf.execute("SELECT * FROM spend_reserve('victim', %s, %s)", (D, Decimal("4")))
    T = txt3.replace('WHERE id = 1 AND "on" = true;', "WHERE id = 1;")
    f19 = bool(g19.check_sql_text("spend_guarded_writes.sql", T, ALLOWED_BY_FILE["spend_guarded_writes.sql"], atomic_tables=ATOMIC_TABLES_BY_FILE["spend_guarded_writes.sql"])); f20 = bool(A20.check(g20, "spend_guarded_writes.sql", T))
    check(f"M4 a release without its `AND on = true` (same tables, other behaviour): v19 guard flags it = {f19}; v20 guard flags it (head/body fingerprint) = {f20}", not f19 and f20)

    section("m1 / F2 expressions inside allowed shapes")
    mgb.execute("ALTER TABLE public.tt ADD COLUMN x text DEFAULT current_setting('server_version')"); xv = mgb.execute("SELECT x FROM public.tt LIMIT 1").fetchone()[0]
    for lbl, T in (("DEFAULT current_setting(..)", "ALTER TABLE tt ADD COLUMN y text DEFAULT current_setting('server_version');\n"), ("CHECK (pg_read_file(..))", "ALTER TABLE tt ADD CONSTRAINT c CHECK (pg_read_file('x') = 'y');\n"), ("index on evil(a)", "CREATE INDEX i ON tt (evil(a));\n"), ("GENERATED ALWAYS AS (evil())", "ALTER TABLE tt ADD COLUMN g int GENERATED ALWAYS AS (evil(a)) STORED;\n")):
        check(f"m1 {lbl}: v19 guard flags it = {g19f(T, {})}; v20 guard flags it = {g20f(T, {}, fn_pins=PIN, kinds=PIN, trigger_pins=PIN)}", not g19f(T, {}) and g20f(T, {}, fn_pins=PIN, kinds=PIN, trigger_pins=PIN))
    info(f"m1 the server accepted DEFAULT current_setting('server_version') as the migration role and stored {xv!r}")

    section("m3 tokenizer against the server")
    cases = [("NBSP inside a word", "SELECT 1 AS x", "colname"), ("U+3000 inside a word", "SELECT 1 AS　x", "colname"), ("U+0085 inside a word", "SELECT 1 AS\u0085x", "colname"), ("U+2028 inside a word", "SELECT 1 AS x", "colname"),
             ("astral character starts a word", "SELECT 1 AS \U0001F600y", "colname"), ("astral dollar tag", "SELECT $\U0001F600$a;b$\U0001F600$", "value")]
    for lbl, q, how in cases:
        try:
            cur = admin.execute(q); sv = cur.description[0].name if how == "colname" else cur.fetchone()[0]
        except psycopg.Error as e: sv = "ERR " + str(e.sqlstate)
        toks = g20.tokenize(q); t19 = g19.tokenize(q)
        if how == "colname": mine = [t[1] for t in toks if t[0] == "word"][-1]; old = [t[1] for t in t19 if t[0] == "word"][-1]
        else: mine = (g20._body_source(toks[1]) if len(toks) > 1 and toks[1][0] == "dollar" else None); old = (g19._body_source(t19[1]) if len(t19) > 1 and t19[1][0] == "dollar" else None)
        check(f"m3 {lbl}: the server reads {sv!r}; v20 tokenizer reads {mine!r}; v19 tokenizer read {old!r}", sv == mine and sv != old)
    for lbl, q in (("form feed", "SELECT\f1"), ("vertical tab", "SELECT\v1")):
        try: admin.execute(q).fetchone(); sv = "accepted"
        except psycopg.Error as e: sv = "ERR " + str(e.sqlstate)
        check(f"m3 {lbl} is a separator for the server ({sv}) and for the v20 tokenizer ({len(g20.tokenize(q))} tokens)", sv == "accepted" and len(g20.tokenize(q)) == 2)

    section("m4 agent-id rule: locale and encoding")
    for enc, extra in (("SQL_ASCII", "LC_COLLATE 'C' LC_CTYPE 'C'"), ("LATIN1", "LC_COLLATE 'C' LC_CTYPE 'C'"), ("UTF8", "LC_COLLATE 'C.utf8' LC_CTYPE 'C.utf8'"), ("UTF8", "LC_COLLATE 'C' LC_CTYPE 'C'")):
        for tag, hold in (("v19", HOLD19), ("v20", H17)):
            dbn = "e_" + secrets.token_hex(3); admin.execute(f"CREATE DATABASE {dbn} TEMPLATE template0 ENCODING '{enc}' {extra} OWNER migr17")
            try:
                tmpn, _ = build(dbn, [(hold / "spend_decrease_log.sql", "0006_dec"), (hold / "spend_guarded_writes.sql", "0007_guard")], base=False)
                mgn = psycopg.connect(dsn("migr17", dbn), autocommit=True); grants_select_only(); m.migrate(dsn("migr17", dbn), runtime_role="rt17"); au.apply_function_grants(mgn, roles=ROLES)
                rtn = psycopg.connect(dsn("rt17", dbn), autocommit=True)
                good = st(lambda: rtn.execute("SELECT * FROM spend_reserve('plain1', %s, %s)", (D, Decimal("1"))))
                nel = st(lambda: rtn.execute("SELECT * FROM spend_reserve(%s, %s, %s)", ("a\u0085b" if enc == "UTF8" else "a", D, Decimal("1"))))
                info(f"m4 {tag} database {enc} / {extra}: ordinary id 'plain1' -> {good}; id with U+0085 (or 'a' in a one-byte database) -> {nel}")
                if tag == "v19" and enc in ("SQL_ASCII", "LATIN1"): control(f"m4 v19 file in a {enc} database: even a plain agent id fails ({good})", good is not None)
                if tag == "v20": check(f"m4 v20 file in a {enc} / {extra} database: a plain id works and the U+0085 id is refused", good is None and (nel == "23514" if enc == "UTF8" else nel is None))
                if tag == "v19" and enc == "UTF8": info(f"m4 v19 U+0085 result in {extra}: {nel} (locale dependence shows when the two UTF8 lines differ)")
            except Exception as e: check(f"m4 {tag} {enc} test ran", False, type(e).__name__ + " " + str(e)[:150])
            m.migrate  # noqa

    section("m6 cutover: open reservations, apply-time refusal, rollback, month row, timeouts")
    # (1) rows before DB-3: open_usd = 0 afterwards, a settle of a reservation made before the cutover is refused
    dbc = "cut_" + secrets.token_hex(3); tmpc, _ = build(dbc, []); mgc = psycopg.connect(dsn("migr17", dbc), autocommit=True)
    mgc.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('old1', %s, 5)", (D,)); mgc.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('old1', %s, 5)", (MO,))
    for p, n in ((H17 / "spend_decrease_log.sql", "0006_dec"), (H17 / "spend_guarded_writes.sql", "0007_guard")): shutil.copy(p, tmpc / f"{n}.sql")
    set_log_grants(H17 / "spend_decrease_log.sql"); grants_select_only(); m.migrate(dsn("migr17", dbc), runtime_role="rt17"); au.apply_function_grants(mgc, roles=ROLES); rtc = psycopg.connect(dsn("rt17", dbc), autocommit=True)
    o = mgc.execute("SELECT open_usd FROM spend WHERE agent_id='old1'").fetchone()[0]
    e = st(lambda: rtc.execute("SELECT * FROM spend_settle('old1', %s, %s, %s)", (D, Decimal("5"), Decimal("1"))))
    check(f"m6 cutover: a row that held a reservation of 5 before the file gets open_usd = {o}; the later settle of that reservation is refused ({e}) and the total stays 5 (safe direction)", o == 0 and e == "23514" and mgc.execute("SELECT usd FROM spend WHERE agent_id='old1'").fetchone()[0] == 5)
    rtc.execute("SELECT * FROM spend_reserve('old1', %s, %s)", (D, Decimal("3"))); rtc.execute("SELECT * FROM spend_settle('old1', %s, %s, %s)", (D, Decimal("3"), Decimal("1")))
    check("m6 cutover with nothing in flight (the drain procedure): a NEW reserve and settle on the old row work and the total is 5 + 1 = 6", mgc.execute("SELECT usd, open_usd FROM spend WHERE agent_id='old1'").fetchone() == (Decimal("6"), Decimal("0")))
    # (2) an old row that breaks the agent rule: v19 applies the file (NOT VALID) and the settle is stuck; v20 refuses at apply time and rolls back
    for tag, hold in (("v19", HOLD19), ("v20", H17)):
        dbx = "bad_" + secrets.token_hex(3); tmpx, _ = build(dbx, []); mgx = psycopg.connect(dsn("migr17", dbx), autocommit=True)
        mgx.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('bad name', %s, 5)", (D,)); mgx.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('bad name', %s, 5)", (MO,))
        for p, n in ((hold / "spend_decrease_log.sql", "0006_dec"), (hold / "spend_guarded_writes.sql", "0007_guard")): shutil.copy(p, tmpx / f"{n}.sql")
        set_log_grants(hold / "spend_decrease_log.sql"); grants_select_only()
        err = st(lambda: m.migrate(dsn("migr17", dbx), runtime_role="rt17"))
        has_col = mgx.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='spend' AND column_name='open_usd'").fetchone()[0]
        has_fn = mgx.execute("SELECT count(*) FROM pg_proc WHERE proname='spend_reserve'").fetchone()[0]
        ledger = mgx.execute("SELECT count(*) FROM schema_migrations WHERE version LIKE '0007%'").fetchone()[0]
        if tag == "v19":
            au19 = None
            stuck = None
            try:
                mgx.execute("UPDATE spend SET open_usd = 5 WHERE agent_id='bad name'"); mgx.execute("UPDATE spend_month SET open_usd = 5 WHERE agent_id='bad name'")
            except psycopg.Error as e2: stuck = e2.sqlstate
            control(f"m6 v19 file with an old row 'bad name': the file APPLIES (error {err}); the row can no longer be changed at all (settling it fails {stuck}) because NOT VALID checks every new row version", err is None and stuck == "23514")
        else:
            check(f"m6 v20 file with an old row 'bad name': migrate refuses at apply time ({err}), nothing is applied (open_usd column {has_col}, function {has_fn}, ledger rows {ledger}): the whole transaction rolled back", err == "23514" and has_col == 0 and has_fn == 0 and ledger == 0)
    # (3) day row without a month row
    for tag, hold in (("v19", HOLD19), ("v20", H17)):
        dby, mgy, rty, opy = fresh_g("dm", [(hold / "spend_decrease_log.sql", "0006_dec"), (hold / "spend_guarded_writes.sql", "0007_guard")])
        mgy.execute("INSERT INTO spend (agent_id, day, usd, open_usd) VALUES ('dm', %s, 5, 5)", (D,))
        r = rty.execute("SELECT * FROM spend_settle('dm', %s, %s, %s)", (D, Decimal("5"), Decimal("0"))).fetchall(); u = mgy.execute("SELECT usd, open_usd FROM spend WHERE agent_id='dm'").fetchone()
        if tag == "v19": control(f"m6 v19 file: a settle for a day row WITHOUT a month row changes the day row ({u}) and returns no row ({r}) and commits", u == (Decimal("0"), Decimal("0")) and r == [])
        else: check(f"m6 v20 file: the same settle changes neither table (day row {u}) and returns no row", u == (Decimal("5"), Decimal("5")) and r == [])
    # (4) SET LOCAL outside a transaction
    with warnings.catch_warnings():
        cz = psycopg.connect(dsn("migr17", dbc), autocommit=True); msgs = []; cz.add_notice_handler(lambda d: msgs.append(d.message_primary))
        cz.execute("SET LOCAL lock_timeout = '5s'"); lt = cz.execute("SHOW lock_timeout").fetchone()[0]
    check(f"m6 SET LOCAL outside a transaction does nothing (lock_timeout stays {lt!r}; server notice {msgs[:1]}): the runner MUST run each file in one transaction; migrate() does (db.transaction())", lt == "0" and msgs)
    holder = psycopg.connect(dsn("migr17", dbc)); holder.execute("LOCK TABLE spend_month IN ACCESS EXCLUSIVE MODE")
    dbl = "lk_" + secrets.token_hex(3); tmpl, _ = build(dbl, [])
    holder2 = psycopg.connect(dsn("migr17", dbl)); holder2.execute("LOCK TABLE spend IN ACCESS EXCLUSIVE MODE")
    for p, n in ((H17 / "spend_decrease_log.sql", "0006_dec"), (H17 / "spend_guarded_writes.sql", "0007_guard")): shutil.copy(p, tmpl / f"{n}.sql")
    set_log_grants(H17 / "spend_decrease_log.sql"); t0 = time.time(); errl = st(lambda: m.migrate(dsn("migr17", dbl), runtime_role="rt17")); dt = time.time() - t0
    check(f"m6 inside migrate() the 5 s lock_timeout of the file works: a held lock makes the apply fail with {errl} after {dt:.1f} s and nothing is applied", errl == "55P03" and 4 < dt < 12)
    holder.rollback(); holder2.rollback()

    section("m5 volume of the decrease record")
    dbv, mgv, rtv, opv = fresh_g("vol")
    t0 = time.time()
    for i in range(1000): rtv.execute("SELECT * FROM spend_reserve('vol', %s, %s)", (D, Decimal("2"))); rtv.execute("SELECT * FROM spend_settle('vol', %s, %s, %s)", (D, Decimal("2"), Decimal("1")))
    nrows = mgv.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]; sz = mgv.execute("SELECT pg_total_relation_size('spend_decrease_log')").fetchone()[0]
    info(f"m5 1000 reserve+settle pairs with actual below worst wrote {nrows} rows to spend_decrease_log ({sz} bytes, {sz / max(nrows, 1):.0f} bytes per row, {time.time() - t0:.1f} s)")
    check("m5 every ordinary settle below its reservation writes one row per table (2 per settle): the record is NOT a signal of tampering any more once DB-3 is applied; it is volume, STATED in the text with this number", nrows == 2000)

    section("F4 / F5 observations of the independent runner of v19, as checks")
    dbo, mgo, rto, opo = fresh_g("obs")
    for lbl, amt in (("0", "0"), ("-0.01", "-0.01"), ("-1e30", "-1e30"), ("-Infinity", "-Infinity"), ("NULL", None)):
        try: rr = rto.execute("SELECT * FROM spend_reserve('obs', %s, %s::numeric)", (D, amt)).fetchall(); e5 = None
        except psycopg.Error as e2: rr, e5 = None, e2.sqlstate
        check(f"F5 a reserve of {lbl} returns no row and no error (the store code must treat an empty result as an error): rows={rr} error={e5}", rr == [] and e5 is None)
    for lbl, w, a in (("worst -1", "-1", "0"), ("actual -1", "1", "-1"), ("worst -Infinity", "-Infinity", "0"), ("worst NULL", None, "0"), ("actual NULL", "1", None)):
        try: rr = rto.execute("SELECT * FROM spend_settle('obs', %s, %s::numeric, %s::numeric)", (D, w, a)).fetchall(); e5 = None
        except psycopg.Error as e2: rr, e5 = None, e2.sqlstate
        check(f"F5 a settle with {lbl} returns no row and no error: rows={rr} error={e5}", rr == [] and e5 is None)
    rto.execute("CREATE TEMP TABLE spend (agent_id text, day date, usd numeric, open_usd numeric)"); rto.execute("SELECT * FROM spend_reserve('tmpcase', %s, %s)", (D, Decimal("2")))
    check("F4 a runtime login can create a TEMP table named spend (and, in the same session, a trigger on it), but the DB-3 function still writes the real table (pg_catalog first, pg_temp last in its search_path)", mgo.execute("SELECT usd FROM spend WHERE agent_id='tmpcase'").fetchone()[0] == 2 and rto.execute("SELECT count(*) FROM pg_temp.spend").fetchone()[0] == 0)
except Exception as e:
    import traceback; traceback.print_exc(); check("v20 section ran to its end", False, type(e).__name__ + " " + str(e)[:200])

print(f"SUMMARY safety checks {sum(res)} of {len(res)} passed; controls {sum(resc)} of {len(resc)} showed the old behaviour; stated exploits shown {sum(ress)} of {len(ress)}")
sys.exit(0 if all(res) and all(resc) and all(ress) else 1)
