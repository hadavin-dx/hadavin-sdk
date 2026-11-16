"""v16 Postgres checks on the REAL store and migration code of src/ (read only, never edited), against a throwaway
cluster. Usage: python pg_v16.py <socket_dir> <src_dir> (admin password in env HV_ADMIN_PW; every login uses a password, scram-sha-256). One line per check: PASS/FAIL/INFO. Made-up data only.
Roles: the MIGRATION role is a plain non-superuser LOGIN role that owns the database (printed below); the runtime,
portal and audit-reader roles are plain roles. Prototype code (`add_spend_v15`, `apply_audit_reader`) is a reference
for the builders, not product code."""
import sys, os, tempfile, shutil, time, re, secrets
from types import SimpleNamespace
from datetime import date
from decimal import Decimal
from pathlib import Path
sock, src = sys.argv[1], sys.argv[2]
sys.path.insert(0, src)
import psycopg
from psycopg import sql
from psycopg import errors as pgerr
import hadavin_sdk.store.migrate as m
from hadavin_sdk.store.postgres import PostgresStore, connect

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import secdef_guard_v16 as sg
PW = {}
HELD = HERE / "held-sql"
DAY, MONTH = date(2026, 11, 16), date(2026, 11, 1)
results = []
def check(name, ok, detail=""):
    results.append(ok); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
def info(msg): print("INFO " + msg)
def dsn(user, db): return f"host={sock} dbname={db} user={user} password={PW[user]}"
def sqlstate(fn):
    try: fn(); return None
    except psycopg.Error as e: return type(e).__name__ + "/" + str(e.sqlstate)
def exc_name(fn):
    try: fn(); return None
    except Exception as e: return type(e).__name__

PW["postgres"] = os.environ["HV_ADMIN_PW"]
admin = psycopg.connect(dsn("postgres", "postgres"), autocommit=True)
def mkrole(name, extra=""):
    PW[name] = secrets.token_hex(16)
    admin.execute(sql.SQL("CREATE ROLE {} LOGIN " + extra + " PASSWORD {}").format(sql.Identifier(name), sql.Literal(PW[name])))
info("server " + admin.execute("SELECT version()").fetchone()[0])
info("server_version_num " + str(admin.execute("SHOW server_version_num").fetchone()[0]) + " (CI uses 17.10: NOT run here)")
for r in ("migr_v16", "rtr_v16", "portal_v16", "auditrd_v16"):
    mkrole(r)
row = admin.execute("SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles WHERE rolname='migr_v16'").fetchone()
check("M3: the migration role is NOT a superuser (rolsuper, createrole, createdb, bypassrls all false)", row == (False, False, False, False), str(row))

def real_files_in(tmp):
    return lambda folder=tmp: sorted(Path(folder).glob("*.sql"))

def build_db(name, held=None, number="0006_spend_nonneg", roles=True):
    """A fresh database owned by the non-superuser migration role: real 0001-0005, then optionally one held file as 0006."""
    admin.execute(f"CREATE DATABASE {name} OWNER migr_v16")
    tmp = Path(tempfile.mkdtemp(prefix="v16mig_"))
    for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmp / p.name)
    if held: shutil.copy(HELD / held, tmp / f"{number}.sql")
    m._migration_files = real_files_in(tmp)
    applied = m.migrate(dsn("migr_v16", name), runtime_role="rtr_v16")
    return tmp, applied

real_files = m._migration_files

# ---------------------------------------------------------------- A. default held file = Q34 exact
tmpA, applied = build_db("exp_a", "spend_nonneg.sql")
check("A1 real migrate() as the NON-SUPERUSER migration role applies 0001-0005 and the DEFAULT held file (Q34-exact) as 0006", len(applied) == 6 and applied[-1] == "0006_spend_nonneg", str(applied))
who = psycopg.connect(dsn("migr_v16", "exp_a")).execute("SELECT session_user, current_user, (SELECT rolsuper FROM pg_roles WHERE rolname = session_user)").fetchone()
check("A2 the migration ran as a non-superuser (session_user, current_user, rolsuper)", who == ("migr_v16", "migr_v16", False), str(who))
mig = connect(dsn("migr_v16", "exp_a"))
src_def = mig.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'spend_usd_ok'").fetchone()[0]
check("A3 the default file carries exactly CHECK (usd >= 0), no Infinity clause", src_def == "CHECK ((usd >= (0)::numeric))", src_def)
rt = connect(dsn("rtr_v16", "exp_a"))
store = PostgresStore(connect(dsn("rtr_v16", "exp_a")))
for tbl, key in (("spend", "day"), ("spend_month", "month")):
    for v, want in (("-0.01", "CheckViolation/23514"), ("-Infinity", "CheckViolation/23514"), ("NaN", None), ("Infinity", None)):
        k = DAY if key == "day" else MONTH
        st = sqlstate(lambda: rt.execute(f"INSERT INTO {tbl} (agent_id, {key}, usd) VALUES (%s, %s, %s)", (f"h{v}", k, Decimal(v))))
        check(f"A4 DEFAULT file: runtime role INSERT {v} into {tbl} -> {want or 'ACCEPTED (expected: the default lets it in)'}", st == want, str(st))
mig.execute("DELETE FROM spend WHERE agent_id LIKE 'h%'"); mig.execute("DELETE FROM spend_month WHERE agent_id LIKE 'h%'")
info("A4 summary: under the default file NaN and Infinity are NOT refused by the database; only the store code (5.4) refuses them")

def add_spend_v15(store, agent, day, usd):
    """Reference shape for S-2a (same as v14's prototype): delta >= 0 upsert, delta < 0 UPDATE ... RETURNING."""
    if not usd.is_finite(): raise ValueError("amount not finite")
    month = day.replace(day=1)
    with store._lock, store._db.transaction():
        if usd >= 0:
            d = store._exec("INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd", (agent, day, usd)).fetchone()["usd"]
            mo = store._exec("INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd RETURNING usd", (agent, month, usd)).fetchone()["usd"]
        else:
            try:
                r = store._exec("UPDATE spend SET usd = usd + %s WHERE agent_id = %s AND day = %s RETURNING usd", (usd, agent, day)).fetchone()
                q = store._exec("UPDATE spend_month SET usd = usd + %s WHERE agent_id = %s AND month = %s RETURNING usd", (usd, agent, month)).fetchone()
            except pgerr.CheckViolation as e:
                raise ValueError("a spend total may not go below zero") from e
            if r is None or q is None: raise LookupError("negative change to a total that does not exist")
            d, mo = r["usd"], q["usd"]
    return Decimal(d), Decimal(mo)

store.add_spend("a", DAY, Decimal("5"))
st = sqlstate(lambda: store.add_spend("a", DAY, Decimal("-3")))
check("A5 B1 with the DEFAULT file: the REAL old add_spend (INSERT ... ON CONFLICT) with delta -3 on a row of 5 fails 23514", st == "CheckViolation/23514", st)
check("A6 B1 fix with the default file: the UPDATE shape, delta -3 on a row of 5 works", add_spend_v15(store, "a", DAY, Decimal("-3")) == (Decimal(2), Decimal(2)))
check("A7 give-back to exactly 0 works", add_spend_v15(store, "a", DAY, Decimal("-2")) == (Decimal(0), Decimal(0)))
add_spend_v15(store, "a", DAY, Decimal("0.5"))
st = exc_name(lambda: add_spend_v15(store, "a", DAY, Decimal("-1")))
check("A8 WEDGE (security minor 3): a delta larger than the total (-1 on 0.5) is refused as ValueError and nothing changes; the agent-day keeps 0.5 and later positive deltas still work (fails closed, not a crash)", st == "ValueError" and store.spend_totals("a", DAY) == (Decimal("0.5"), Decimal("0.5")), f"{st} {store.spend_totals('a', DAY)}")
check("A8b the same agent-day still accepts a reserve after the refusal", add_spend_v15(store, "a", DAY, Decimal("1")) == (Decimal("1.5"), Decimal("1.5")))
st = exc_name(lambda: add_spend_v15(store, "nobody", DAY, Decimal("-1")))
check("A9 a negative change on a missing row raises LookupError", st == "LookupError", str(st))
for bad in ("NaN", "Infinity", "-Infinity"):
    check(f"A10 code-level finite check, independent of which held file is applied: {bad} refused before any statement", exc_name(lambda: add_spend_v15(store, "a", DAY, Decimal(bad))) == "ValueError")
mig.execute("UPDATE spend_month SET usd = 1 WHERE agent_id = 'a'")
before = store.spend_totals("a", DAY)
st = exc_name(lambda: add_spend_v15(store, "a", DAY, Decimal("-1.2")))
check("A11 rollback: when the month row refuses, the day row is unchanged too", st == "ValueError" and store.spend_totals("a", DAY) == before, f"{st} {store.spend_totals('a', DAY)}")
mig.execute("UPDATE spend_month SET usd = 1.5 WHERE agent_id = 'a'")

# ---------------------------------------------------------------- B. variant file (Infinity clause)
tmpB, applied = build_db("exp_b", "spend_nonneg_finite.sql")
check("B1 real migrate() applies the VARIANT file (separately pinned) as 0006", applied[-1] == "0006_spend_nonneg", str(applied))
rtb = connect(dsn("rtr_v16", "exp_b"))
for tbl, key in (("spend", "day"), ("spend_month", "month")):
    for v in ("-0.01", "NaN", "Infinity", "-Infinity"):
        k = DAY if key == "day" else MONTH
        st = sqlstate(lambda: rtb.execute(f"INSERT INTO {tbl} (agent_id, {key}, usd) VALUES ('h', %s, %s)", (k, Decimal(v))))
        check(f"B2 VARIANT: runtime role INSERT {v} into {tbl} -> 23514", st == "CheckViolation/23514", st)
    for v in ("-0.01", "NaN", "Infinity", "-Infinity"):
        rtb.execute(f"INSERT INTO {tbl} (agent_id, {key}, usd) VALUES ('u', %s, 1)", (DAY if key == "day" else MONTH,)) if v == "-0.01" else None
        st = sqlstate(lambda: rtb.execute(f"UPDATE {tbl} SET usd = %s WHERE agent_id = 'u'", (Decimal(v),)))
        check(f"B3 VARIANT: runtime role UPDATE to {v} on {tbl} -> 23514", st == "CheckViolation/23514", st)

# ---------------------------------------------------------------- C. pre-flight query (security minor 5)
admin.execute("CREATE DATABASE exp_c OWNER migr_v16")
tmpC = Path(tempfile.mkdtemp(prefix="v16mig_"))
for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmpC / p.name)
m._migration_files = real_files_in(tmpC)
m.migrate(dsn("migr_v16", "exp_c"), runtime_role="rtr_v16")
mc = connect(dsn("migr_v16", "exp_c"))
for i, v in enumerate(("-1", "NaN", "Infinity", "-Infinity", "3")):
    mc.execute("INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s)", (f"p{i}", DAY, Decimal(v)))
old_q = "SELECT agent_id FROM spend WHERE usd < 0 OR usd = 'NaN' ORDER BY 1"
new_q = "SELECT agent_id FROM spend WHERE usd < 0 OR usd::text IN ('NaN', 'Infinity', '-Infinity') ORDER BY 1"
old_rows = [r[0] for r in mc.execute(old_q).fetchall()]; new_rows = [r[0] for r in mc.execute(new_q).fetchall()]
check("C1 negative control: the v14 pre-flight query misses the +Infinity row (p2)", "p2" not in old_rows and old_rows == ["p0", "p1", "p3"], str(old_rows))
check("C2 the v15 pre-flight query lists all four bad rows (p0 -1, p1 NaN, p2 Infinity, p3 -Infinity) and not the good one (p4)", new_rows == ["p0", "p1", "p2", "p3"], str(new_rows))
st = sqlstate(lambda: mc.execute("ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric)"))
check("C3 applying the variant over bad rows fails (23514) before the repair", st == "CheckViolation/23514", st)
mc.execute("UPDATE spend SET usd = 0 WHERE agent_id IN ('p0','p1','p2','p3')")
check("C4 after the repair the pre-flight query lists nothing", mc.execute(new_q).fetchall() == [])

# ---------------------------------------------------------------- D. lock timeout of the default file (as in v14)
tmpD = Path(tempfile.mkdtemp(prefix="v16mig_"))
admin.execute("CREATE DATABASE exp_d OWNER migr_v16")
for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmpD / p.name)
m._migration_files = real_files_in(tmpD)
m.migrate(dsn("migr_v16", "exp_d"), runtime_role="rtr_v16")
shutil.copy(HELD / "spend_nonneg.sql", tmpD / "0006_spend_nonneg.sql")
holder = connect(dsn("migr_v16", "exp_d")); md = connect(dsn("migr_v16", "exp_d"))
t0 = time.monotonic(); err = None
with holder.transaction():
    holder.execute("LOCK TABLE spend IN ROW SHARE MODE")
    try: m.migrate(dsn("migr_v16", "exp_d"), runtime_role="rtr_v16")
    except psycopg.Error as e: err = e
el = time.monotonic() - t0
check("D1 with a session holding spend, the default held file fails 55P03 after about its 5 s lock_timeout (non-superuser migration role)", err is not None and err.sqlstate == "55P03" and 4.5 < el < 15, f"{getattr(err, 'sqlstate', None)} after {el:.1f}s")
check("D2 the failed migration rolled back (no 0006 row, no constraint)", md.execute("SELECT count(*) FROM schema_migrations WHERE version LIKE '0006%%'").fetchone()[0] == 0 and md.execute("SELECT count(*) FROM pg_constraint WHERE conname = 'spend_usd_ok'").fetchone()[0] == 0)
holder.close()

def clear_log():
    """Test housekeeping only: the owner switches the append-only trigger off, empties the log, switches it on."""
    with mig.transaction():
        mig.execute("ALTER TABLE spend_decrease_log DISABLE TRIGGER spend_decrease_log_append_only")
        mig.execute("DELETE FROM spend_decrease_log")
        mig.execute("ALTER TABLE spend_decrease_log ENABLE TRIGGER spend_decrease_log_append_only")

# ---------------------------------------------------------------- E. DB-2 (v16 file) on the default database exp_a (file as 0007)
m._migration_files = real_files_in(tmpA)
shutil.copy(HELD / "spend_decrease_log.sql", tmpA / "0007_spend_decrease_log.sql")
files = m._migration_files()
p = m.check_grants(files)
check("E1 DB-2 PR state (file numbered, no GRANTS entry): guard says created but not in GRANTS, for BOTH new tables", any("spend_decrease_log (table) is created by a migration but is not in GRANTS" in x for x in p) and any("kill_switch_log (table) is created by a migration but is not in GRANTS" in x for x in p), "; ".join(p)[:140])
m.GRANTS["spend_decrease_log"] = m.Grant("table", ""); m.GRANTS["kill_switch_log"] = m.Grant("table", "")
check("E2 move PR state (numbered file + GRANTS entry with an EMPTY runtime list): check_ledger and check_grants empty", m.check_ledger(files) + m.check_grants(files) == [], str(m.check_grants(files)))
only = [x for x in files if "0007" not in x.name]
p2 = m.check_grants(only)
check("E3 v12 state (GRANTS entry merged, SQL held elsewhere): the guard fails with 'which no migration creates'", any("GRANTS names spend_decrease_log, which no migration creates" in x for x in p2))
applied = m.migrate(dsn("migr_v16", "exp_a"), runtime_role="rtr_v16")
check("E4 real migrate() as the non-superuser migration role applies DB-2 as 0007", applied == ["0007_spend_decrease_log"], str(applied))
fo = mig.execute("SELECT pg_get_userbyid(proowner), prosecdef, proconfig FROM pg_proc WHERE proname = 'spend_log_decrease'").fetchone()
check("E5 the SECURITY DEFINER function is owned by the NON-superuser migration role and has search_path = pg_catalog, pg_temp", fo[0] == "migr_v16" and fo[1] is True and fo[2] == ["search_path=pg_catalog, pg_temp"], str(fo))
bad = tmpA / "0008_plain_function.sql"; bad.write_text("CREATE FUNCTION f() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;\n")
p3 = m.check_grants(m._migration_files()); bad.unlink()
check("E6 the guard refuses a plain CREATE FUNCTION (only CREATE OR REPLACE FUNCTION is read)", any("statement the guard does not read" in x and "CREATE FUNCTION" in x for x in p3))
st = sqlstate(lambda: rt.execute("UPDATE spend SET day = day - 3650 WHERE agent_id = 'a'"))
check("E7 key guard: runtime role key rewrite on spend -> 42501", st == "InsufficientPrivilege/42501", st)
st = sqlstate(lambda: rt.execute("UPDATE spend_month SET agent_id = 'b' WHERE agent_id = 'a'"))
check("E8 key guard: runtime role key rewrite on spend_month -> 42501", st == "InsufficientPrivilege/42501", st)
add_spend_v15(store, "a", DAY, Decimal("-0.5"))
rows = mig.execute("SELECT scope, old_usd, new_usd, who FROM spend_decrease_log ORDER BY at").fetchall()
check("E9 one lowering through the store writes two rows (day and month); who is the runtime login role", len(rows) == 2 and {r[0] for r in rows} == {"spend", "spend_month"} and all(r[3] == "rtr_v16" for r in rows), str(rows))
add_spend_v15(store, "a", DAY, Decimal("0.5"))
check("E10 a raising write adds no row", mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0] == 2)
for stmt in ("SELECT * FROM spend_decrease_log", "INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES ('f', now(), 's', 1, 0)", "UPDATE spend_decrease_log SET new_usd = 9", "DELETE FROM spend_decrease_log", "TRUNCATE spend_decrease_log"):
    st = sqlstate(lambda: rt.execute(stmt))
    check(f"E11 runtime role denied on the log: {stmt.split()[0]} -> 42501", st == "InsufficientPrivilege/42501", st)
# trigger condition (T6 of v14, re-run): lower, raise, NaN, Infinity, NaN->NaN. Needs the DEFAULT file (NaN accepted by it).
clear_log()
mig.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('t6', %s, 5)", (DAY,))
def nlog(): return mig.execute("SELECT count(*) FROM spend_decrease_log WHERE agent_id = 't6'").fetchone()[0]
mig.execute("UPDATE spend SET usd = 4 WHERE agent_id = 't6'"); a = nlog()
mig.execute("UPDATE spend SET usd = 6 WHERE agent_id = 't6'"); b = nlog()
mig.execute("UPDATE spend SET usd = 'NaN' WHERE agent_id = 't6'"); c = nlog()
mig.execute("UPDATE spend SET usd = 'NaN' WHERE agent_id = 't6'"); d = nlog()
mig.execute("UPDATE spend SET usd = 7 WHERE agent_id = 't6'"); e_ = nlog()
mig.execute("UPDATE spend SET usd = 'Infinity' WHERE agent_id = 't6'"); f = nlog()
check("E12 trigger condition: lower logs (1), raise does not (1), becoming NaN logs (2), NaN to NaN does not (2), NaN to 7 logs? see next, Infinity logs", (a, b, c, d) == (1, 1, 2, 2) and f == e_ + 1, f"counts after each step {a},{b},{c},{d},{e_},{f}")
mig.execute("DELETE FROM spend WHERE agent_id = 't6'"); clear_log()

# ---------------------------------------------------------------- F. temporary-table attack, as v14 (B1 of v13), and REVOKE TEMPORARY
rtc = connect(dsn("rtr_v16", "exp_a"))
add_spend_v15(store, "a", DAY, Decimal("2"))
rtc.execute("CREATE TEMP TABLE spend_decrease_log (agent_id text, period date, scope text, old_usd numeric, new_usd numeric, at timestamptz DEFAULT clock_timestamp(), who text DEFAULT session_user)")
rtc.execute("GRANT ALL ON pg_temp.spend_decrease_log TO PUBLIC")
store_rt = PostgresStore(rtc)
add_spend_v15(store_rt, "a", DAY, Decimal("-0.5"))
n_temp = rtc.execute("SELECT count(*) FROM pg_temp.spend_decrease_log").fetchone()[0]
n_real = mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
check("F1 B1 fix: with a temporary table of the log's name present, the REAL log still gets both rows and the temporary table none", n_real == 2 and n_temp == 0, f"real={n_real} temp={n_temp}")
v14_fn = re.search(r"CREATE OR REPLACE FUNCTION spend_log_decrease\(\).*?END \$f\$;", (HELD / "spend_decrease_log.sql").read_text(), re.S).group(0)
v13_fn = """CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public AS $f$
BEGIN
  IF TG_TABLE_NAME = 'spend' THEN
    INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES (OLD.agent_id, OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd);
  ELSE
    INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES (OLD.agent_id, OLD.month, TG_TABLE_NAME, OLD.usd, NEW.usd);
  END IF;
  RETURN NULL;
END $f$;"""
mig.execute(v13_fn); clear_log()
add_spend_v15(store_rt, "a", DAY, Decimal("-0.25"))
n_temp_old = rtc.execute("SELECT count(*) FROM pg_temp.spend_decrease_log").fetchone()[0]
n_real_old = mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
check("F2 negative control: on the v13 function the same test FAILS (real log 0 rows, temporary table 2 rows)", n_real_old == 0 and n_temp_old == 2, f"real={n_real_old} temp={n_temp_old}")
mig.execute(v14_fn); clear_log(); rtc.execute("DELETE FROM pg_temp.spend_decrease_log")
add_spend_v15(store_rt, "a", DAY, Decimal("-0.25"))
check("F3 restored: the v15 function is back and the real log gets the rows again", mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0] == 2)
rtc.close()
def can_temp(role): return mig.execute("SELECT has_database_privilege(%s, current_database(), 'TEMP')", (role,)).fetchone()[0]
check("F4 before the REVOKE the runtime role can create temporary tables", can_temp("rtr_v16") is True)
admin.execute("REVOKE TEMPORARY ON DATABASE exp_a FROM PUBLIC"); admin.execute("GRANT TEMPORARY ON DATABASE exp_a TO migr_v16")
check("F5 after REVOKE ... FROM PUBLIC the runtime role has no TEMP and the migration role keeps it", can_temp("rtr_v16") is False and can_temp("migr_v16") is True)
rtc = connect(dsn("rtr_v16", "exp_a"))
st = sqlstate(lambda: rtc.execute("CREATE TEMP TABLE spend_decrease_log (agent_id text)"))
check("F6 the runtime role creating the temporary table is refused (42501)", st == "InsufficientPrivilege/42501", st)
rtc.close()

# ---------------------------------------------------------------- G. the AUDIT READER role (security M2; NEW role, prototype of the DB-2 move PR code)
def apply_audit_reader(db, role):
    """Prototype of `migrate(..., audit_reader_role=)`: SELECT only on relations whose Grant has audit_read; then the
    same effective_problems check the runtime and purge roles get. `audit_read` is modelled by identity here."""
    logs = (m.GRANTS["spend_decrease_log"], m.GRANTS["kill_switch_log"])
    pick = lambda g: "SELECT" if any(g is x for x in logs) else ""
    m._apply_grants(db, role, pick)
    return m.effective_problems(db, role, pick)
with mig.transaction():
    prob = apply_audit_reader(mig, "auditrd_v16")
check("G1 effective_problems for the audit-reader role is empty (it can SELECT the log and nothing else, whatever way it got it)", prob == [], "; ".join(prob)[:200])
ar = connect(dsn("auditrd_v16", "exp_a"))
n = ar.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
check("G2 the audit reader can read both logs", n >= 2 and ar.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] >= 0, str(n))
check("G3 the audit reader can read the log's size and the catalogue entry (status line figures)", ar.execute("SELECT pg_total_relation_size('spend_decrease_log'), to_regclass('spend_decrease_log') IS NOT NULL").fetchone()[1] is True)
for stmt in ("INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES ('f', now(), 's', 1, 0)", "UPDATE spend_decrease_log SET new_usd = 9", "DELETE FROM spend_decrease_log", "TRUNCATE spend_decrease_log", "SELECT * FROM spend", "SELECT * FROM spend_month", "UPDATE spend SET usd = 0", "SELECT * FROM kill_switch", "SELECT * FROM audit_entries", "SELECT * FROM runs", "CREATE TEMP TABLE x (a int)", "CREATE TABLE public.x (a int)", "INSERT INTO kill_switch_log (old_on, new_on) VALUES (false, true)", "UPDATE kill_switch_log SET new_on = false", "DELETE FROM kill_switch_log", "TRUNCATE kill_switch_log"):
    st = sqlstate(lambda: ar.execute(stmt))
    check(f"G4 NEGATIVE TEST audit reader denied: {stmt[:48]} -> 42501", st == "InsufficientPrivilege/42501", str(st))
st = sqlstate(lambda: ar.execute("SET ROLE rtr_v16"))
check("G5 the audit reader cannot become the runtime role (SET ROLE refused 42501)", st == "InsufficientPrivilege/42501", str(st))
# the portal role does NOT get the log (the earlier v14 design gave it)
with mig.transaction():
    m._apply_grants(mig, "portal_v16", lambda g: "SELECT" if g.portal else "")
pt = connect(dsn("portal_v16", "exp_a"))
st = sqlstate(lambda: pt.execute("SELECT 1 FROM spend_decrease_log"))
check("G6 the portal role cannot read the log (it is NOT portal-readable any more)", st == "InsufficientPrivilege/42501", str(st))
# the runtime role cannot read it
st = sqlstate(lambda: connect(dsn("rtr_v16", "exp_a")).execute("SELECT 1 FROM spend_decrease_log"))
check("G7 the runtime role still cannot read the log", st == "InsufficientPrivilege/42501", str(st))
# a role that is a MEMBER of another named role would inherit: the prototype's effective_problems catches it
mkrole("evil_v16"); admin.execute("GRANT rtr_v16 TO evil_v16")
with mig.transaction():
    m._apply_grants(mig, "evil_v16", lambda g: "SELECT" if g is m.GRANTS["spend_decrease_log"] else "")
    prob2 = m.effective_problems(mig, "evil_v16", lambda g: "SELECT" if g is m.GRANTS["spend_decrease_log"] else "")
check("G8 negative: a would-be audit reader that is also a member of the runtime role is reported by effective_problems (it could UPDATE spend)", any("can UPDATE spend" in x for x in prob2), "; ".join(prob2)[:140])

# ---------------------------------------------------------------- H. append-only logs (security minor 4); replaces v15's retention delete
mig.execute("INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd, at) VALUES ('old', %s, 'spend', 2, 1, now() - interval '500 days')", (DAY,))
n_before = mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
for who_, c_ in (("audit reader", ar), ("runtime role", connect(dsn("rtr_v16", "exp_a")))):
    st = sqlstate(lambda: c_.execute("DELETE FROM spend_decrease_log WHERE at < now() - interval '400 days'"))
    check(f"H1 the {who_} cannot delete log rows (42501)", st == "InsufficientPrivilege/42501", str(st))
for stmt in ("DELETE FROM spend_decrease_log", "UPDATE spend_decrease_log SET new_usd = 9", "TRUNCATE spend_decrease_log", "DELETE FROM kill_switch_log", "UPDATE kill_switch_log SET new_on = false", "TRUNCATE kill_switch_log"):
    st = sqlstate(lambda: mig.execute(stmt))
    check(f"H2 the OWNER (migration role) is also refused by the append-only trigger: {stmt[:40]} -> 42501", st == "InsufficientPrivilege/42501", str(st))
check("H3 the refused statements changed nothing", mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0] == n_before)
# honest limit: the owner can still switch the trigger off (visible in the catalogue) and a superuser bypasses triggers
with mig.transaction():
    mig.execute("ALTER TABLE spend_decrease_log DISABLE TRIGGER spend_decrease_log_append_only")
    mig.execute("DELETE FROM spend_decrease_log WHERE agent_id = 'old'")
    dis = mig.execute("SELECT tgenabled FROM pg_trigger WHERE tgname = 'spend_decrease_log_append_only'").fetchone()[0]
    mig.execute("ALTER TABLE spend_decrease_log ENABLE TRIGGER spend_decrease_log_append_only")
check("H4 LIMIT STATED, not hidden: the database owner can DISABLE the trigger (tgenabled = D while off) and delete; an append-only trigger shows edits, it does not stop the owner", dis == "D")
check("H5 the trigger is back on afterwards", mig.execute("SELECT tgenabled FROM pg_trigger WHERE tgname = 'spend_decrease_log_append_only'").fetchone()[0] == "O")

# ---------------------------------------------------------------- I. cost of the trigger, run by the RUNTIME role on a non-superuser database (security M3)
def timing(dbname, with_trigger):
    admin.execute(f"CREATE DATABASE {dbname} OWNER migr_v16")
    t = Path(tempfile.mkdtemp(prefix="v16mig_"))
    for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, t / p.name)
    shutil.copy(HELD / "spend_nonneg.sql", t / "0006_spend_nonneg.sql")
    if with_trigger: shutil.copy(HELD / "spend_decrease_log.sql", t / "0007_spend_decrease_log.sql")
    m._migration_files = real_files_in(t)
    m.GRANTS["spend_decrease_log"] = m.Grant("table", ""); m.GRANTS["kill_switch_log"] = m.Grant("table", "")
    if not with_trigger: m.GRANTS.pop("spend_decrease_log"); m.GRANTS.pop("kill_switch_log")
    m.migrate(dsn("migr_v16", dbname), runtime_role="rtr_v16")
    c = connect(dsn("rtr_v16", dbname))
    c.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('t', %s, 1000000)", (DAY,))
    t0 = time.perf_counter()
    for _ in range(20000): c.execute("UPDATE spend SET usd = usd - 0.0001 WHERE agent_id = 't' AND day = %s", (DAY,))
    ms = (time.perf_counter() - t0) * 1000
    size = None
    if with_trigger:
        mm = connect(dsn("migr_v16", dbname))
        size = mm.execute("SELECT pg_total_relation_size('spend_decrease_log'), count(*), min(who), max(who) FROM spend_decrease_log").fetchone()
    shutil.rmtree(t)
    return ms, size
ms0, _ = timing("exp_t0", False)
ms1, sz = timing("exp_t1", True)
info(f"I timing (runtime role, 20000 lowering UPDATEs, migration role = non-superuser, indicative, one run per script run; the script is run twice): without trigger {ms0:.0f} ms, with trigger {ms1:.0f} ms, +{(ms1-ms0)/20000:.3f} ms per lowering")
info(f"I size: log {sz[0]} bytes, {sz[1]} rows, {sz[0]/max(sz[1],1):.1f} bytes per row, who = {sz[2]}/{sz[3]}")
check("I1 the timing run's log rows record the RUNTIME login role, not postgres", sz[2] == "rtr_v16" and sz[3] == "rtr_v16", f"{sz[2]},{sz[3]}")
check("I2 the log has one row per lowering (20000 rows)", sz[1] == 20000, str(sz[1]))

# ---------------------------------------------------------------- J. S-2b detection of the log through the audit reader (to_regclass) and absence
mkrole("ar2_v16")
a2 = connect(dsn("ar2_v16", "exp_c"))
check("J1 S-2b detection: where DB-2 is NOT applied (database exp_c) to_regclass('spend_decrease_log') is NULL for a reader that has no privilege", a2.execute("SELECT to_regclass('spend_decrease_log') IS NULL").fetchone()[0] is True)
check("J2 S-2b detection: where DB-2 is applied (database exp_a) the audit reader sees it", ar.execute("SELECT to_regclass('spend_decrease_log') IS NOT NULL").fetchone()[0] is True)


# ================================================================= v16 NEW SECTIONS
from decimal import InvalidOperation
from hadavin_sdk.models import KillSwitch, now as sdk_now
from hadavin_sdk.limits import Limits

def build_multi(name, helds):
    """Fresh database owned by the non-superuser migration role: real 0001-0005 then each (file number, held file)."""
    admin.execute(f"CREATE DATABASE {name} OWNER migr_v16")
    t = Path(tempfile.mkdtemp(prefix="v16mig_"))
    for p in real_files_dir.glob("*.sql"): shutil.copy(p, t / p.name)
    for number, f in helds: shutil.copy(HELD / f, t / f"{number}.sql")
    m._migration_files = real_files_in(t)
    m.GRANTS["spend_decrease_log"] = m.Grant("table", ""); m.GRANTS["kill_switch_log"] = m.Grant("table", "")
    if not any("decrease_log" in f for _, f in helds):
        m.GRANTS.pop("spend_decrease_log"); m.GRANTS.pop("kill_switch_log")
    applied = m.migrate(dsn("migr_v16", name), runtime_role="rtr_v16")
    return t, applied
real_files_dir = m.MIGRATIONS

# ---------------------------------------------------------------- Q. password authentication really exercised (security major 3)
rows = admin.execute("SELECT auth_method, count(*) FROM pg_hba_file_rules WHERE type <> 'host' OR true GROUP BY 1").fetchall()
check("Q1 every pg_hba rule of the throwaway cluster uses scram-sha-256 (no trust)", rows and all(r[0] == "scram-sha-256" for r in rows), str(rows))
check("Q2 password_encryption is scram-sha-256 and the stored role passwords are SCRAM verifiers", admin.execute("SHOW password_encryption").fetchone()[0] == "scram-sha-256" and admin.execute("SELECT bool_and(rolpassword LIKE 'SCRAM-SHA-256$%%') FROM pg_authid WHERE rolname LIKE '%%_v16'").fetchone()[0] is True)
def login_state(user, pw):
    try:
        c = psycopg.connect(f"host={sock} dbname=exp_a user={user}" + (f" password={pw}" if pw is not None else "")); c.close(); return "OK"
    except psycopg.Error as e:
        return (e.sqlstate or "none") + "/" + ("no-password-message" if "no password" in str(e).lower() or "password" in str(e).lower() else "other")
check("Q3 a right password logs in", login_state("rtr_v16", PW["rtr_v16"]) == "OK")
st = login_state("rtr_v16", "wrong" + secrets.token_hex(4))
check("Q4 a wrong password is refused (28P01)", st.startswith("28P01"), st)
st = login_state("rtr_v16", None)
check("Q5 no password is refused (the server asks for one; libpq reports it)", st != "OK", st)
check("Q6 the earlier v15 runs used trust (security review m3): this run proves the migration, store and grants code works with password logins", True)

# ---------------------------------------------------------------- K. security majors 1 and 2: NO held file applied at all
tmpK, applied = build_multi("exp_k", [])
check("K0 database with ONLY the real 0001-0005 (no held file, no CHECK on the spend tables)", len(applied) == 5, str(applied))
mk = connect(dsn("migr_v16", "exp_k")); rk = connect(dsn("rtr_v16", "exp_k")); sk = PostgresStore(connect(dsn("rtr_v16", "exp_k")))
check("K0b no constraint spend_usd_ok exists here", mk.execute("SELECT count(*) FROM pg_constraint WHERE conname IN ('spend_usd_ok', 'spend_month_usd_ok')").fetchone()[0] == 0)
def add_spend_v16(store, agent, day, usd):
    """Reference for S-2a: code-level rule, independent of every held file. Positive delta: upsert. Negative delta:
    UPDATE ... RETURNING. After BOTH writes, a total that is NaN, Infinity or below 0 raises ValueError inside the
    transaction, so both rows roll back."""
    if not usd.is_finite(): raise ValueError("amount not finite")
    month = day.replace(day=1)
    with store._lock, store._db.transaction():
        if usd >= 0:
            d = store._exec("INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd", (agent, day, usd)).fetchone()["usd"]
            mo = store._exec("INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd RETURNING usd", (agent, month, usd)).fetchone()["usd"]
        else:
            r = store._exec("UPDATE spend SET usd = usd + %s WHERE agent_id = %s AND day = %s RETURNING usd", (usd, agent, day)).fetchone()
            q = store._exec("UPDATE spend_month SET usd = usd + %s WHERE agent_id = %s AND month = %s RETURNING usd", (usd, agent, month)).fetchone()
            if r is None or q is None: raise LookupError("negative change to a total that does not exist")
            d, mo = r["usd"], q["usd"]
        for v in (d, mo):
            v = Decimal(v)
            if not v.is_finite() or v < 0: raise ValueError("a spend total must be finite and not below zero")
    return Decimal(d), Decimal(mo)
def spend_totals_v16(store, agent, day):
    d, mo = store.spend_totals(agent, day)
    for v in (d, mo):
        if not v.is_finite() or v < 0: raise ValueError("bad_amount")
    return d, mo
sk.add_spend("k1", DAY, Decimal("2"))
r_old = None
try: r_old = sk.add_spend("k1", DAY, Decimal("-3"))
except Exception as e: r_old = type(e).__name__
check("K1 NEGATIVE CONTROL (old shape, no held file): the REAL add_spend with delta -3 on a total of 2 is ACCEPTED and leaves -1 (the bug the code-level rule must stop)", r_old == (Decimal(-1), Decimal(-1)), str(r_old))
mk.execute("UPDATE spend SET usd = 2 WHERE agent_id = 'k1'"); mk.execute("UPDATE spend_month SET usd = 2 WHERE agent_id = 'k1'")
st = exc_name(lambda: add_spend_v16(sk, "k1", DAY, Decimal("-3")))
check("K2 v16 rule, NO held file: delta -3 on a total of 2 raises ValueError and BOTH rows roll back (still 2 and 2)", st == "ValueError" and sk.spend_totals("k1", DAY) == (Decimal(2), Decimal(2)), f"{st} {sk.spend_totals('k1', DAY)}")
check("K3 v16 rule: a legal give-back (-1.5 on 2) works", add_spend_v16(sk, "k1", DAY, Decimal("-1.5")) == (Decimal("0.5"), Decimal("0.5")))
for bad in ("NaN", "Infinity", "-Infinity"):
    mk.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('kn', %s, %s) ON CONFLICT (agent_id, day) DO UPDATE SET usd = EXCLUDED.usd", (DAY, Decimal(bad)))
    mk.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('kn', %s, %s) ON CONFLICT (agent_id, month) DO UPDATE SET usd = EXCLUDED.usd", (MONTH, Decimal(bad)))
    for delta in ("1", "-1"):
        st = exc_name(lambda: add_spend_v16(sk, "kn", DAY, Decimal(delta)))
        check(f"K4 NO held file, a stored {bad} total plus delta {delta}: refused with ValueError (a NaN stays NaN under addition, so it would be accepted without the result check)", st == "ValueError", str(st))
    still = mk.execute("SELECT usd::text FROM spend WHERE agent_id = 'kn'").fetchone()[0]
    check(f"K5 the refused write rolled back: the stored {bad} total is unchanged", still == bad, still)
    st = exc_name(lambda: spend_totals_v16(sk, "kn", DAY))
    check(f"K6 v16 spend_totals refuses a stored {bad} total (ValueError, mapped to limits_unavailable / bad_amount)", st == "ValueError", str(st))
# a stored negative total (a repair-needed state): fails closed, never silently accepted
mk.execute("UPDATE spend SET usd = -5 WHERE agent_id = 'kn'"); mk.execute("UPDATE spend_month SET usd = -5 WHERE agent_id = 'kn'")
st = exc_name(lambda: add_spend_v16(sk, "kn", DAY, Decimal("1")))
check("K8 WEDGE by design: a stored negative total (-5) plus +1 = -4 is still refused; the agent-day fails closed until an operator repairs the row (stated in 5.4)", st == "ValueError" and mk.execute("SELECT usd FROM spend WHERE agent_id = 'kn'").fetchone()[0] == Decimal(-5), str(st))
check("K9 v16 add_spend with delta NaN/Infinity/-Infinity is refused before any statement", all(exc_name(lambda b=b: add_spend_v16(sk, "k1", DAY, Decimal(b))) == "ValueError" for b in ("NaN", "Infinity", "-Infinity")))

# ---------------------------------------------------------------- L. Limits.blocked and the NaN row (security major 2, the second half)
reg = SimpleNamespace(agents={"kn": SimpleNamespace(budget_usd=SimpleNamespace(daily=Decimal(10), monthly=Decimal(100)))})
lim = Limits(sk, None, reg)
today = sdk_now().date()
mk.execute("DELETE FROM spend WHERE agent_id = 'kn'"); mk.execute("DELETE FROM spend_month WHERE agent_id = 'kn'")
mk.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('kn', %s, 'NaN')", (today,)); mk.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('kn', %s, 'NaN')", (today.replace(day=1),))
st = exc_name(lambda: lim.blocked("kn"))
check("L1 NEGATIVE CONTROL: the REAL Limits.blocked on a NaN total raises InvalidOperation (an unhandled crash, not a stop)", st == "InvalidOperation", str(st))
def blocked_v16(lim_, agent):
    reasons = ["kill_switch"] if lim_.store.get_kill_switch().on else []
    try: day, month = spend_totals_v16(lim_.store, agent, sdk_now().date())
    except ValueError: return reasons + ["bad_amount"]
    budget = lim_.registry.agents[agent].budget_usd
    if day >= budget.daily: reasons.append("daily_budget")
    if month >= budget.monthly: reasons.append("monthly_budget")
    return reasons
check("L2 v16 blocked: the same NaN row gives ['bad_amount'] (the loop maps it to the existing stop card; no crash)", blocked_v16(lim, "kn") == ["bad_amount"], str(blocked_v16(lim, "kn")))
mk.execute("UPDATE spend SET usd = 'Infinity' WHERE agent_id = 'kn'")
check("L3 v16 blocked on an Infinity row gives ['bad_amount']", blocked_v16(lim, "kn") == ["bad_amount"])
mk.execute("UPDATE spend SET usd = 1 WHERE agent_id = 'kn'"); mk.execute("UPDATE spend_month SET usd = 1 WHERE agent_id = 'kn'")
check("L4 v16 blocked on a good row gives []", blocked_v16(lim, "kn") == [])
# the `limits status` read of the same rows
def status_line(store, agent):
    try: d, mo = spend_totals_v16(store, agent, today); return f"ok {d} {mo}"
    except ValueError: return "bad_amount"
mk.execute("UPDATE spend SET usd = 'NaN' WHERE agent_id = 'kn'")
check("L5 `limits status` line for a NaN row prints bad_amount (and `--check` would exit non-zero)", status_line(sk, "kn") == "bad_amount")

# ---------------------------------------------------------------- M. kill-switch log (security major 5), DB-2 v16 file
tmpM, applied = build_multi("exp_m", [("0006_spend_nonneg", "spend_nonneg.sql"), ("0007_spend_decrease_log", "spend_decrease_log.sql")])
check("M0 real migrate() applies the v16 DB-2 file as 0007 on top of the default file (non-superuser migration role)", applied[-1] == "0007_spend_decrease_log", str(applied))
mm_ = connect(dsn("migr_v16", "exp_m")); rm_ = connect(dsn("rtr_v16", "exp_m")); sm_ = PostgresStore(connect(dsn("rtr_v16", "exp_m")))
fo = mm_.execute("SELECT pg_get_userbyid(proowner), prosecdef, proconfig FROM pg_proc WHERE proname = 'kill_switch_log_change'").fetchone()
check("M1 kill_switch_log_change is SECURITY DEFINER, owned by the non-superuser migration role, search_path = pg_catalog, pg_temp", fo[0] == "migr_v16" and fo[1] is True and fo[2] == ["search_path=pg_catalog, pg_temp"], str(fo))
sm_.set_kill_switch(KillSwitch(on=True, by="op:tester"))
sm_.set_kill_switch(KillSwitch(on=True, by="op:tester2"))
sm_.set_kill_switch(KillSwitch(on=False, by="op:tester3"))
rows = mm_.execute("SELECT old_on, new_on, old_by, new_by, who FROM kill_switch_log ORDER BY at").fetchall()
check("M2 REAL store.set_kill_switch: on, on again, off write exactly two rows (the unchanged on->on write is not logged), by the runtime login role", len(rows) == 2 and rows[0][:2] == (False, True) and rows[1][:2] == (True, False) and all(r[4] == "rtr_v16" for r in rows), str(rows))
for stmt in ("SELECT * FROM kill_switch_log", "INSERT INTO kill_switch_log (old_on, new_on) VALUES (false, true)", "UPDATE kill_switch_log SET new_on = false", "DELETE FROM kill_switch_log", "TRUNCATE kill_switch_log"):
    st = sqlstate(lambda: rm_.execute(stmt))
    check(f"M3 NEGATIVE TEST runtime role denied on the kill-switch log: {stmt.split()[0]} -> 42501", st == "InsufficientPrivilege/42501", str(st))
st = sqlstate(lambda: rm_.execute("DELETE FROM kill_switch"))
info(f"M4 INFO runtime role DELETE FROM kill_switch -> {st} (if allowed, a delete-and-reinsert is a state change the update trigger does not see)")
rtm = connect(dsn("rtr_v16", "exp_m"))
temp_ok = sqlstate(lambda: rtm.execute("CREATE TEMP TABLE kill_switch_log (old_on boolean, new_on boolean, old_by text, new_by text, at timestamptz, who text)"))
check("M5 (TEMP still granted in this database) runtime role created a temporary table named like the log", temp_ok is None, str(temp_ok))
sm2 = PostgresStore(rtm)
sm2.set_kill_switch(KillSwitch(on=True, by="op:t4"))
n_real = mm_.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0]; n_tmp = rtm.execute("SELECT count(*) FROM pg_temp.kill_switch_log").fetchone()[0]
check("M6 temporary-table attack on the kill-switch log: the REAL log gets the 3rd row, the temporary table none", n_real == 3 and n_tmp == 0, f"real={n_real} temp={n_tmp}")
v_old = re.search(r"CREATE OR REPLACE FUNCTION kill_switch_log_change\(\).*?END \$f\$;", (HELD / "spend_decrease_log.sql").read_text(), re.S).group(0)
v_bad = v_old.replace("SET search_path = pg_catalog, pg_temp", "SET search_path = pg_catalog, public").replace("EXECUTE format('INSERT INTO %I.kill_switch_log (old_on, new_on, old_by, new_by) VALUES ($1, $2, $3, $4)', TG_TABLE_SCHEMA)\n    USING", "INSERT INTO kill_switch_log (old_on, new_on, old_by, new_by) VALUES (").replace("OLD.\"on\", NEW.\"on\", OLD.\"by\", NEW.\"by\";", "OLD.\"on\", NEW.\"on\", OLD.\"by\", NEW.\"by\");")
mm_.execute(v_bad)
sm2.set_kill_switch(KillSwitch(on=False, by="op:t5"))
check("M7 NEGATIVE CONTROL: with the unsafe function shape (public in the path, bare table name) the same attack DIVERTS the row to the temporary table (real log stays 3, temporary table 1)", mm_.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] == 3 and rtm.execute("SELECT count(*) FROM pg_temp.kill_switch_log").fetchone()[0] == 1)
mm_.execute(v_old)
sm2.set_kill_switch(KillSwitch(on=True, by="op:t6"))
check("M8 the safe function restored: the REAL log gets the 4th row", mm_.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] == 4)
with mm_.transaction():
    prob = (lambda pick: (m._apply_grants(mm_, "auditrd_v16", pick), m.effective_problems(mm_, "auditrd_v16", pick))[1])(lambda g: "SELECT" if (g is m.GRANTS["spend_decrease_log"] or g is m.GRANTS["kill_switch_log"]) else "")
arm = connect(dsn("auditrd_v16", "exp_m"))
check("M9 audit reader can read the kill-switch log and effective_problems is empty", arm.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] == 4 and prob == [], str(prob))

# ---------------------------------------------------------------- N. upgrade path default -> variant (minor 2)
tmpN, applied = build_multi("exp_n", [("0006_spend_nonneg", "spend_nonneg.sql")])
mn = connect(dsn("migr_v16", "exp_n")); rn = connect(dsn("rtr_v16", "exp_n"))
mn.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('nan', %s, 'NaN')", (DAY,))
shutil.copy(HELD / "spend_nonneg_upgrade.sql", tmpN / "0007_spend_nonneg_upgrade.sql")
st = sqlstate(lambda: m.migrate(dsn("migr_v16", "exp_n"), runtime_role="rtr_v16"))
check("N1 the upgrade over a stored NaN row fails (23514) and rolls back: the old rule stays", st == "CheckViolation/23514" and mn.execute("SELECT count(*) FROM schema_migrations WHERE version LIKE '0007%%'").fetchone()[0] == 0 and mn.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'spend_usd_ok'").fetchone()[0] == "CHECK ((usd >= (0)::numeric))", str(st))
mn.execute("DELETE FROM spend WHERE agent_id = 'nan'")
applied = m.migrate(dsn("migr_v16", "exp_n"), runtime_role="rtr_v16")
check("N2 after the repair, real migrate() applies the upgrade file as 0007", applied == ["0007_spend_nonneg_upgrade"], str(applied))
defs = [mn.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = %s", (c,)).fetchone()[0] for c in ("spend_usd_ok", "spend_month_usd_ok")]
check("N3 both constraints now carry the Infinity clause, same names, no second constraint", all("Infinity" in d for d in defs) and mn.execute("SELECT count(*) FROM pg_constraint WHERE conname LIKE 'spend%%usd_ok'").fetchone()[0] == 2, str(defs))
check("N4 the runtime role is now refused NaN (23514)", sqlstate(lambda: rn.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('z', %s, 'NaN')", (DAY,))) == "CheckViolation/23514")

# ---------------------------------------------------------------- O. class-level guard over SECURITY DEFINER (security major 6)
ALLOWED = {"spend_log_decrease", "kill_switch_log_change"}
real_sql = sorted(m.MIGRATIONS.glob("*.sql")); held_sql = sorted(HELD.glob("*.sql"))
probs = [p for f in real_sql + held_sql for p in sg.check_sql_text(f.name, f.read_text(), ALLOWED)]
check(f"O1 the guard finds no problem in the {len(real_sql)} real migrations and the {len(held_sql)} held files", probs == [], "; ".join(probs)[:200])
base = (HELD / "spend_decrease_log.sql").read_text()
mutants = {
    "pg_temp not last": base.replace("SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF", "SET search_path = pg_temp, pg_catalog AS $f$\nBEGIN\n  IF", 1),
    "public in path": base.replace("SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF", "SET search_path = pg_catalog, public, pg_temp AS $f$\nBEGIN\n  IF", 1),
    "no pg_temp": base.replace("SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF", "SET search_path = pg_catalog AS $f$\nBEGIN\n  IF", 1),
    "no SET search_path": base.replace("SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF", "AS $f$\nBEGIN\n  IF", 1),
    "bare table (no %I)": base.replace("%I.kill_switch_log", "kill_switch_log"),
    "no REVOKE": base.replace("REVOKE ALL ON FUNCTION kill_switch_log_change() FROM PUBLIC;", ""),
    "undeclared SECURITY DEFINER": base + "\nCREATE OR REPLACE FUNCTION sneaky() RETURNS int LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT 1 $f$;\nREVOKE ALL ON FUNCTION sneaky() FROM PUBLIC;\n",
}
for label, text in mutants.items():
    differs = text != base
    found = sg.check_sql_text("mutant.sql", text, ALLOWED)
    check(f"O2 mutant '{label}' differs from the file and the guard reports it", differs and len(found) >= 1, "; ".join(found)[:120])
check("O3 the held-file head spend_log_decrease search_path text is what the guard read (sanity)", "pg_catalog, pg_temp" in base)

# ---------------------------------------------------------------- P. audit reader role checks (security major 4)
admin.execute("CREATE DATABASE exp_p OWNER migr_v16")
mp = connect(dsn("migr_v16", "exp_p"))
mkrole("reader_v16", "VALID UNTIL 'infinity'")
def reader_problems(db, role):
    """Prototype of DB-2's reader_problems: the reader must not be able to create temporary tables or objects, must not be a
    member of any role, must not be superuser/createrole/createdb/bypassrls/replication, must have an expiry (VALID UNTIL) in the future."""
    p = []
    if db.execute("SELECT has_database_privilege(%s, current_database(), 'TEMP')", (role,)).fetchone()[0]: p.append("can create temporary tables")
    if db.execute("SELECT has_database_privilege(%s, current_database(), 'CREATE')", (role,)).fetchone()[0]: p.append("can create schemas")
    if db.execute("SELECT has_schema_privilege(%s, 'public', 'CREATE')", (role,)).fetchone()[0]: p.append("can create in public")
    if db.execute("SELECT count(*) FROM pg_auth_members am JOIN pg_roles r ON r.oid = am.member WHERE r.rolname = %s", (role,)).fetchone()[0]: p.append("is a member of another role")
    f = db.execute("SELECT rolsuper OR rolcreaterole OR rolcreatedb OR rolbypassrls OR rolreplication, rolvaliduntil FROM pg_roles WHERE rolname = %s", (role,)).fetchone()
    if f[0]: p.append("has a powerful role flag")
    if f[1] is None: p.append("has no VALID UNTIL")
    return p
pr = reader_problems(mp, "reader_v16")
check("P1 NEGATIVE TEST BEFORE the REVOKE: on a fresh database the reader CAN create temporary tables (PUBLIC has TEMP) and reader_problems reports exactly that", "can create temporary tables" in pr, str(pr))
admin.execute("REVOKE TEMPORARY ON DATABASE exp_p FROM PUBLIC")
pr = reader_problems(mp, "reader_v16")
check("P2 after REVOKE TEMPORARY ... FROM PUBLIC (operator step, question L19) reader_problems is empty", pr == [], str(pr))
rr = connect(dsn("reader_v16", "exp_p"))
check("P3 the reader is refused CREATE TEMP TABLE (42501)", sqlstate(lambda: rr.execute("CREATE TEMP TABLE x (a int)")) == "InsufficientPrivilege/42501")
admin.execute("GRANT rtr_v16 TO reader_v16")
check("P4 NEGATIVE: a reader that is a member of the runtime role is reported", "is a member of another role" in reader_problems(mp, "reader_v16"))
admin.execute("REVOKE rtr_v16 FROM reader_v16")
mkrole("expired_v16", "VALID UNTIL '2020-01-01'")
st = login_state("expired_v16", PW["expired_v16"])
check("P5 a role whose VALID UNTIL is in the past cannot log in (28P01)", st.startswith("28P01"), st)
mkrole("nolimit_v16")
check("P6 NEGATIVE: a reader role created without VALID UNTIL is reported ('has no VALID UNTIL')", "has no VALID UNTIL" in reader_problems(mp, "nolimit_v16"))
admin.execute("ALTER ROLE reader_v16 NOLOGIN")
check("P7 revoking by NOLOGIN stops new logins (SQLSTATE 28000 or 28P01)", login_state("reader_v16", PW["reader_v16"])[:5] in ("28000", "28P01"), login_state("reader_v16", PW["reader_v16"]))

m._migration_files = real_files
for t in (tmpA, tmpB, tmpC, tmpD, tmpK, tmpM, tmpN): shutil.rmtree(t, ignore_errors=True)
info(f"{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
