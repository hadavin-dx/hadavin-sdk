"""Run the REAL store and migration code of src/ (read only, never edited) against the throwaway cluster.
Usage: python pg_real_code_v14.py <socket_dir> <src_dir>. Prints one line per check: PASS/FAIL/INFO.
Prototype of the S-2a store shape lives here only as `add_spend_v14` (a reference for the builder, not product code)."""
import sys, tempfile, shutil, time
from datetime import date
from decimal import Decimal
from pathlib import Path
sock, src = sys.argv[1], sys.argv[2]
sys.path.insert(0, src)
import psycopg
from psycopg import errors as pgerr
import hadavin_sdk.store.migrate as m
from hadavin_sdk.store.postgres import PostgresStore, connect

HERE = Path(__file__).parent
DAY, MONTH = date(2026, 11, 16), date(2026, 11, 1)
results = []
def check(name, ok, detail=""):
    results.append(ok); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
def info(msg): print("INFO " + msg)
def dsn(user, db="exp2"): return f"host={sock} dbname={db} user={user}"

admin = psycopg.connect(f"host={sock} dbname=postgres user=postgres", autocommit=True)
for r in ("migr_v14", "rtr_v14", "portal_v14"):
    admin.execute(f"CREATE ROLE {r} LOGIN")
admin.execute("CREATE DATABASE exp2 OWNER migr_v14")

# 1. real migrations 0001-0005 and the real runtime grants
applied = m.migrate(dsn("migr_v14"), runtime_role="rtr_v14")
check("real migrate() applies 0001-0005 and the runtime grants on Postgres 16", len(applied) == 5, str(applied))
mig = connect(dsn("migr_v14"))
store = PostgresStore(connect(dsn("rtr_v14")))

# 2. old store code before the CHECK: reserve then give back works
store.add_spend("a", DAY, Decimal("5"))
tot = store.add_spend("a", DAY, Decimal("-3"))
check("old add_spend: reserve +5 then settle -3 works before the CHECK", tot == (Decimal(2), Decimal(2)), str(tot))

# 3. apply held file 1 as text, through the real guard (numbered 0006 in a temp copy of the folder)
tmp = Path(tempfile.mkdtemp(prefix="v14mig_"))
for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmp / p.name)
shutil.copy(HERE / "held-sql" / "spend_nonneg.sql", tmp / "0006_spend_nonneg.sql")
real_files = m._migration_files
m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
# v14 security minor 4: a run that holds the table makes held file 1 fail after its own lock_timeout and roll back
holder = connect(dsn("migr_v14"))
t0 = time.monotonic(); err = None
with holder.transaction():
    holder.execute("LOCK TABLE spend IN ROW SHARE MODE")
    try: m.migrate(dsn("migr_v14"), runtime_role="rtr_v14")
    except psycopg.Error as e: err = e
el = time.monotonic() - t0
check("v14 lock: with a session holding spend, held file 1 fails with 55P03 after about its 5 s lock_timeout", err is not None and err.sqlstate == "55P03" and 4.5 < el < 15, f"{getattr(err, 'sqlstate', None)} after {el:.1f}s")
check("v14 lock: the failed migration rolled back (no 0006 row in the ledger, no constraint)", mig.execute("SELECT count(*) FROM schema_migrations WHERE version LIKE '0006%%'").fetchone()[0] == 0 and mig.execute("SELECT count(*) FROM pg_constraint WHERE conname = 'spend_usd_ok'").fetchone()[0] == 0)
holder.close()
m._migration_files = real_files
m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
check("guard: check_ledger + check_grants accept held file 1 numbered 0006", (m.check_ledger(m._migration_files()) + m.check_grants(m._migration_files())) == [])
applied = m.migrate(dsn("migr_v14"), runtime_role="rtr_v14")
check("real migrate() applies held file 1 as 0006", applied == ["0006_spend_nonneg"], str(applied))

# 4. B1 on the real code: old shape breaks, v14 shape works
def sqlstate(fn):
    try: fn(); return None
    except psycopg.Error as e: return type(e).__name__ + "/" + str(e.sqlstate)
before = store.spend_totals("a", DAY)
st = sqlstate(lambda: store.add_spend("a", DAY, Decimal("-1")))
check("B1: the REAL old add_spend with delta -1 on a row that holds 2 fails after file 1", st == "CheckViolation/23514", st)
check("B1: nothing changed after that failure (both rows rolled back)", store.spend_totals("a", DAY) == before, str(store.spend_totals("a", DAY)))

def add_spend_v14(store, agent, day, usd):
    """Reference shape for S-2a: positive or zero delta = upsert, negative delta = UPDATE ... RETURNING (a missing row is an error)."""
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
            except pgerr.CheckViolation as e:  # v14 security minor 1: one exception type with the memory store
                raise ValueError("a spend total may not go below zero") from e
            if r is None or q is None: raise LookupError("negative change to a total that does not exist")
            d, mo = r["usd"], q["usd"]
    return Decimal(d), Decimal(mo)

check("B1 fix: v14 shape, delta -1 on a row of 2 works", add_spend_v14(store, "a", DAY, Decimal("-1")) == (Decimal(1), Decimal(1)))
check("B1 fix: v14 shape, give back to exactly 0 works (positive control)", add_spend_v14(store, "a", DAY, Decimal("-1")) == (Decimal(0), Decimal(0)))
def exc_name(fn):
    try: fn(); return None
    except Exception as e: return type(e).__name__
st = exc_name(lambda: add_spend_v14(store, "a", DAY, Decimal("-0.01")))
check("B1 fix: v14 shape, a delta that would go below zero is refused by the database (23514) and surfaces as ValueError", st == "ValueError", str(st))
try: add_spend_v14(store, "nobody", DAY, Decimal("-1")); check("missing-row error raised", False)
except LookupError: check("missing-row error raised (LookupError)", True)
check("positive and zero deltas still upsert", add_spend_v14(store, "a", DAY, Decimal("2")) == (Decimal(2), Decimal(2)) and add_spend_v14(store, "z", DAY, Decimal("0")) == (Decimal(0), Decimal(0)))
for bad in ("NaN", "Infinity", "-Infinity"):
    try: add_spend_v14(store, "a", DAY, Decimal(bad)); check(f"non-finite {bad} refused in code", False)
    except ValueError: check(f"non-finite {bad} refused in code before any statement", True)
# E0-S2-2 rollback claim: day row and month row disagree; the month UPDATE fails, the day UPDATE must roll back
mig.execute("UPDATE spend_month SET usd = 1 WHERE agent_id = 'a'")  # month 1, day 2
before = store.spend_totals("a", DAY)
st = exc_name(lambda: add_spend_v14(store, "a", DAY, Decimal("-1.5")))  # day 0.5 ok, month -0.5 refused
check("rollback: when the month row refuses, the day row is unchanged too", st == "ValueError" and store.spend_totals("a", DAY) == before, f"{st} {store.spend_totals('a', DAY)}")
mig.execute("UPDATE spend_month SET usd = 2 WHERE agent_id = 'a'")

# 5. hostile direct writes as the runtime role (the E0-DB-1 list)
rt = connect(dsn("rtr_v14"))
for tbl, key in (("spend", "day"), ("spend_month", "month")):
    for v in ("-0.01", "NaN", "Infinity", "-Infinity"):
        st = sqlstate(lambda: rt.execute(f"INSERT INTO {tbl} (agent_id, {key}, usd) VALUES ('h', %s, %s)", (DAY if key == "day" else MONTH, Decimal(v))))
        check(f"runtime role INSERT {v} into {tbl} -> 23514", st == "CheckViolation/23514", st)
        st = sqlstate(lambda: rt.execute(f"UPDATE {tbl} SET usd = %s WHERE agent_id = 'a'", (Decimal(v),)))
        check(f"runtime role UPDATE {v} on {tbl} -> 23514", st == "CheckViolation/23514", st)

# 6. M3: the held file 2 and the GRANTS timing, on the real guard
shutil.copy(HERE / "held-sql" / "spend_decrease_log.sql", tmp / "0007_spend_decrease_log.sql")
files = m._migration_files()
p = m.check_grants(files)
check("M3 (v14 DB-2 PR state, no GRANTS entry yet): guard says the table is created but not in GRANTS", any("spend_decrease_log (table) is created by a migration but is not in GRANTS" in x for x in p), "; ".join(p)[:120])
m.GRANTS["spend_decrease_log"] = m.Grant("table", "")
check("M3 move PR state (file numbered + GRANTS entry with an EMPTY runtime list): check_grants == []", m.check_grants(files) == [], str(m.check_grants(files)))
saved = files
m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
only_grants = [p for p in files if "0007" not in p.name]
p2 = m.check_grants(only_grants)
check("M3 v12 state (GRANTS entry merged, SQL held elsewhere): migrate()'s guard fails with 'which no migration creates'", any("GRANTS names spend_decrease_log, which no migration creates" in x for x in p2), "; ".join(p2)[:140])
applied = m.migrate(dsn("migr_v14"), runtime_role="rtr_v14")
check("real migrate() applies held file 2 as 0007 and effective_problems(runtime role) is empty (an empty Grant is accepted)", applied == ["0007_spend_decrease_log"], str(applied))
# plain CREATE FUNCTION is refused by the guard (so 'use OR REPLACE' is a real rule)
bad = tmp / "0008_plain_function.sql"; bad.write_text("CREATE FUNCTION f() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;\n")
p3 = m.check_grants(m._migration_files()); bad.unlink()
check("guard refuses a plain CREATE FUNCTION (only CREATE OR REPLACE FUNCTION is read)", any("statement the guard does not read" in x and "CREATE FUNCTION" in x for x in p3), "; ".join(p3)[:100])

# 7. M1 and the log on the real store code
st = sqlstate(lambda: rt.execute("UPDATE spend SET day = day - 3650 WHERE agent_id = 'a'"))
check("M1: runtime role key rewrite on spend -> 42501", st == "InsufficientPrivilege/42501", st)
st = sqlstate(lambda: rt.execute("UPDATE spend_month SET agent_id = 'b' WHERE agent_id = 'a'"))
check("M1: runtime role key rewrite on spend_month -> 42501", st == "InsufficientPrivilege/42501", st)
add_spend_v14(store, "a", DAY, Decimal("-0.5"))
rows = mig.execute("SELECT scope, old_usd, new_usd FROM spend_decrease_log ORDER BY at").fetchall()
check("log: one lowering through the v14 store writes two rows (day and month) and a raise writes none", len(rows) == 2 and {r[0] for r in rows} == {"spend", "spend_month"}, str(rows))
add_spend_v14(store, "a", DAY, Decimal("0.5"))
check("log: a raising write added no row", mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0] == 2)
for stmt in ("SELECT * FROM spend_decrease_log", "INSERT INTO spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES ('f', now(), 's', 1, 0)", "UPDATE spend_decrease_log SET new_usd = 9", "DELETE FROM spend_decrease_log", "TRUNCATE spend_decrease_log"):
    st = sqlstate(lambda: rt.execute(stmt))
    check(f"runtime role denied on the log: {stmt.split()[0]} -> 42501", st == "InsufficientPrivilege/42501", st)
row = mig.execute("SELECT who FROM spend_decrease_log LIMIT 1").fetchone()
check("log: the who column holds the login role (session_user) of the runtime connection", row[0] == "rtr_v14", str(row))
# v14 security blocker B1: the runtime role creates a temporary table of the log's name, then lowers a total
rtc = connect(dsn("rtr_v14"))
mig.execute("DELETE FROM spend_decrease_log")
rtc.execute("CREATE TEMP TABLE spend_decrease_log (agent_id text, period date, scope text, old_usd numeric, new_usd numeric, at timestamptz DEFAULT clock_timestamp(), who text DEFAULT session_user)")
rtc.execute("GRANT ALL ON pg_temp.spend_decrease_log TO PUBLIC")
check("B1 attack set-up: the runtime role CAN create a temporary table (PUBLIC default) and grant on it before the REVOKE", True)
store_rt = PostgresStore(rtc)
add_spend_v14(store_rt, "a", DAY, Decimal("-0.5"))
n_temp = rtc.execute("SELECT count(*) FROM pg_temp.spend_decrease_log").fetchone()[0]
n_real = mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
check("B1 fix: with the temporary table present, the REAL log still gets both rows (day and month) and the temporary table none", n_real == 2 and n_temp == 0, f"real={n_real} temp={n_temp}")
# negative control (the test must FAIL on the v13 function): put the v13 function back, repeat, then restore v14
import re
v14_fn = re.search(r"CREATE OR REPLACE FUNCTION spend_log_decrease\(\).*?END \$f\$;", (HERE / "held-sql" / "spend_decrease_log.sql").read_text(), re.S).group(0)
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
mig.execute(v13_fn)
mig.execute("DELETE FROM spend_decrease_log")
add_spend_v14(store_rt, "a", DAY, Decimal("-0.25"))
n_temp_old = rtc.execute("SELECT count(*) FROM pg_temp.spend_decrease_log").fetchone()[0]
n_real_old = mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
check("B1 negative control: on the v13 function the same test FAILS (real log 0 rows, temporary table 2 rows: the bypass works)", n_real_old == 0 and n_temp_old == 2, f"real={n_real_old} temp={n_temp_old}")
mig.execute(v14_fn)
rtc.execute("DELETE FROM pg_temp.spend_decrease_log")
add_spend_v14(store_rt, "a", DAY, Decimal("-0.25"))
check("B1 restored: the v14 function is back and the real log gets the rows again", mig.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0] == 2 and rtc.execute("SELECT count(*) FROM pg_temp.spend_decrease_log").fetchone()[0] == 0)
rtc.close()
# REVOKE TEMP FROM PUBLIC as the operator would; the check proposed for effective_problems
def can_temp(role): return mig.execute("SELECT has_database_privilege(%s, current_database(), 'TEMP')", (role,)).fetchone()[0]
check("TEMP check (prototype of the DB-2 check): the runtime role can create temporary tables before the REVOKE", can_temp("rtr_v14") is True)
admin.execute("REVOKE TEMPORARY ON DATABASE exp2 FROM PUBLIC")
admin.execute("GRANT TEMPORARY ON DATABASE exp2 TO migr_v14")
check("TEMP check: after REVOKE ... FROM PUBLIC the runtime role has no TEMP and the migration role keeps it", can_temp("rtr_v14") is False and can_temp("migr_v14") is True)
rtc = connect(dsn("rtr_v14"))
st = sqlstate(lambda: rtc.execute("CREATE TEMP TABLE spend_decrease_log (agent_id text)"))
check("B1 defence in depth: the runtime role creating the temporary table is now refused (42501)", st == "InsufficientPrivilege/42501", st)
rtc.close()
# portal read role (question L10): SELECT on the log for the portal role only
m.GRANTS["spend_decrease_log"] = m.Grant("table", "", portal=True)
applied = m.migrate(dsn("migr_v14"), runtime_role="rtr_v14", portal_role="portal_v14")
check("portal role: migrate(runtime, portal) accepts Grant('table', '', portal=True) for the log", applied == [], str(applied))
pt = connect(dsn("portal_v14"))
rows = pt.execute("SELECT count(*), COALESCE(sum(old_usd - new_usd), 0) FROM spend_decrease_log").fetchall()
check("portal role can read the log (the status line's figures)", rows[0][0] == 2, str(rows))
sz = pt.execute("SELECT pg_total_relation_size('spend_decrease_log')").fetchone()[0]
check("portal role can read the size of the log (alarm figure)", sz > 0, str(sz))
st = sqlstate(lambda: pt.execute("DELETE FROM spend_decrease_log"))
check("portal role cannot delete from the log (42501)", st == "InsufficientPrivilege/42501", st)
st = sqlstate(lambda: connect(dsn("rtr_v14")).execute("SELECT 1 FROM spend_decrease_log"))
check("runtime role still cannot read the log (42501)", st == "InsufficientPrivilege/42501", st)
pt.close()
# the same migration run twice applies nothing (ledger) and the guard still accepts
check("second migrate() applies nothing", m.migrate(dsn("migr_v14"), runtime_role="rtr_v14") == [])
m._migration_files = real_files
shutil.rmtree(tmp)
info(f"{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
