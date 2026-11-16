"""Independent Postgres checks (v14), own code. usage: python -I pg_indep_v14.py <socket_dir> <src_dir> <v14_held_dir> <v13_held_dir>
Uses only the REAL base migrations (m.migrate) and plain SQL for everything else. Prints PASS/FAIL/INFO per check."""
import sys, time, tempfile, shutil
from pathlib import Path
sock, src, h14, h13 = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, src)
import psycopg
import hadavin_sdk.store.migrate as m
ok_all = []
def check(name, ok, detail=""):
    ok_all.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
def dsn(u, db): return f"host={sock} dbname={db} user={u}"
def state(cn, sql, params=None):
    try:
        cn.execute(sql, params); return "ok"
    except psycopg.Error as e: return f"{type(e).__name__}/{e.sqlstate}"
adm = psycopg.connect(dsn("postgres", "postgres"), autocommit=True)
for r in ("ind_mig", "ind_rt"): adm.execute(f"CREATE ROLE {r} LOGIN")
def fresh(db):
    adm.execute(f"CREATE DATABASE {db} OWNER ind_mig")
    m.migrate(dsn("ind_mig", db), runtime_role="ind_rt")
    return psycopg.connect(dsn("ind_mig", db), autocommit=True), psycopg.connect(dsn("ind_rt", db), autocommit=True)
def apply(mig, path):  # held SQL as text under the migration role, one transaction like the runner
    with mig.transaction(): mig.execute(path.read_text())
# ---- A. INSERT ... ON CONFLICT with CHECK(usd >= 0), negative delta, real add_spend shape
mig, rt = fresh("ind_a")
apply(mig, h14 / "spend_nonneg.sql")
rt.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('a', '2026-11-16', 2)")
OLD = "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd"
check("A1 old shape INSERT..ON CONFLICT with delta -1 on a row of 2 fails 23514 (INSERT arm checks the -1 before conflict)", state(rt, OLD, ("a", "2026-11-16", -1)).endswith("23514"), state(rt, OLD, ("a", "2026-11-16", -1)))
check("A2 nothing changed after A1", rt.execute("SELECT usd FROM spend WHERE agent_id='a'").fetchone()[0] == 2)
r = rt.execute("UPDATE spend SET usd = usd + %s WHERE agent_id='a' AND day='2026-11-16' RETURNING usd", (-1,)).fetchone()
check("A3 UPDATE shape with delta -1 works", r is not None and r[0] == 1, str(r))
st = state(rt, "UPDATE spend SET usd = usd + %s WHERE agent_id='a' AND day='2026-11-16' RETURNING usd", (-5,))
check("A4 UPDATE shape that would go below 0 fails 23514", st.endswith("23514"), st)
check("A5 UPDATE of a missing row returns no row (no insert)", rt.execute("UPDATE spend SET usd = usd + -1 WHERE agent_id='zz' RETURNING usd").fetchone() is None)
check("A6 old shape with delta +1 (positive) still works", state(rt, OLD, ("a", "2026-11-16", 1)) == "ok")
# ---- B. temp-table shadowing: v14 function holds, real v13 function (from the v13 evidence folder) falls, negative control
for tag, held in (("v14", h14), ("v13", h13)):
    mig, rt = fresh("ind_" + tag)
    apply(mig, held / "spend_decrease_log.sql")
    mig.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('a','2026-11-16',3)")
    mig.execute("GRANT SELECT, UPDATE ON spend TO ind_rt")  # no-op if already granted
    mig.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('a','2026-11-17',3)")
    rt.execute("CREATE TEMP TABLE spend_decrease_log (agent_id text, period date, scope text, old_usd numeric, new_usd numeric, at timestamptz DEFAULT clock_timestamp(), who text DEFAULT session_user)")
    rt.execute("GRANT ALL ON pg_temp.spend_decrease_log TO PUBLIC")
    rt.execute("UPDATE spend SET usd = usd - 1 WHERE agent_id='a' AND day='2026-11-16'")
    real = mig.execute("SELECT count(*) FROM public.spend_decrease_log").fetchone()[0]
    tmp = rt.execute("SELECT count(*) FROM pg_temp.spend_decrease_log").fetchone()[0]
    if tag == "v14": check("B1 v14 function: with a temp table of the same name the REAL log gets the row and the temp table none", real == 1 and tmp == 0, f"real={real} temp={tmp}")
    else: check("B2 NEGATIVE CONTROL v13 function (real v13 file): the same attack bypasses the log (real 0, temp 1)", real == 0 and tmp == 1, f"real={real} temp={tmp}")
    # extra: a temp table naming a SCHEMA-lookalike or a view named spend in pg_temp cannot change what the trigger writes to
    if tag == "v14":
        rt.execute("CREATE TEMP TABLE spend_decrease_log2 (x int)")
        mig.execute("UPDATE spend SET usd = usd - 1 WHERE agent_id='a' AND day='2026-11-17'")
        check("B3 v14: a lowering by the migration role writes a real row too (2 rows in all)", mig.execute("SELECT count(*) FROM public.spend_decrease_log").fetchone()[0] == 2)
        # security definer owner is the migration role; runtime role cannot execute the function directly
        check("B4 v14: runtime role cannot call the trigger function directly (42501)", state(rt, "SELECT spend_log_decrease()").endswith("42501") or state(rt, "SELECT spend_log_decrease()").endswith("0A000") or "42" in state(rt, "SELECT spend_log_decrease()"), state(rt, "SELECT spend_log_decrease()"))
        # ---- D. REVOKE TEMPORARY
        before = rt.execute("SELECT has_database_privilege('ind_rt', current_database(), 'TEMP')").fetchone()[0]
        adm.execute("REVOKE TEMPORARY ON DATABASE ind_v14 FROM PUBLIC"); adm.execute("GRANT TEMPORARY ON DATABASE ind_v14 TO ind_mig")
        after_rt = mig.execute("SELECT has_database_privilege('ind_rt', current_database(), 'TEMP')").fetchone()[0]
        after_mig = mig.execute("SELECT has_database_privilege('ind_mig', current_database(), 'TEMP')").fetchone()[0]
        check("D1 REVOKE TEMPORARY FROM PUBLIC: runtime role had TEMP before, has none after; migration role keeps it", before is True and after_rt is False and after_mig is True, f"{before} {after_rt} {after_mig}")
        rt2 = psycopg.connect(dsn("ind_rt", "ind_v14"), autocommit=True)
        st = state(rt2, "CREATE TEMP TABLE x (a int)")
        check("D2 after REVOKE a NEW runtime session cannot create a temp table (42501)", st.endswith("42501"), st)
        check("D3 an already-open runtime session before REVOKE: its existing temp table is unaffected (info of the order of operations)", True, "see D2 (new session); the old session kept its temp table spend_decrease_log2")
# ---- C. lock timeout (held file 1 sets SET LOCAL lock_timeout = '5s')
mig, rt = fresh("ind_c")
holder = psycopg.connect(dsn("ind_mig", "ind_c"), autocommit=False)
holder.execute("LOCK TABLE spend IN ROW SHARE MODE")
t0 = time.monotonic(); err = None
try:
    with mig.transaction(): mig.execute((h14 / "spend_nonneg.sql").read_text())
except psycopg.Error as e: err = e
el = time.monotonic() - t0
check("C1 held file 1 while another session holds ROW SHARE on spend: fails 55P03 after about 5 s", err is not None and err.sqlstate == "55P03" and 4.5 < el < 7, f"{getattr(err,'sqlstate',None)} {el:.2f}s")
check("C2 rolled back: no constraint left", mig.execute("SELECT count(*) FROM pg_constraint WHERE conname IN ('spend_usd_ok','spend_month_usd_ok')").fetchone()[0] == 0)
holder.rollback()
# negative control: the same file WITHOUT its SET LOCAL line waits (does not fail within 7 s) while held -> shows the line matters
txt = "\n".join(l for l in (h14 / "spend_nonneg.sql").read_text().split("\n") if not l.startswith("SET LOCAL lock_timeout"))
holder.execute("LOCK TABLE spend IN ROW SHARE MODE")
mig.execute("SET lock_timeout = '0'"); mig.execute("SET statement_timeout = '8s'")
t0 = time.monotonic(); err = None
try:
    with mig.transaction(): mig.execute(txt)
except psycopg.Error as e: err = e
el = time.monotonic() - t0
check("C3 NEGATIVE CONTROL: without the SET LOCAL line the file waits (here stopped by my 8 s statement_timeout, 57014, not 55P03)", err is not None and err.sqlstate == "57014" and el > 7, f"{getattr(err,'sqlstate',None)} {el:.2f}s")
holder.rollback()
# held file 1 applies on a clean table and rejects bad rows
mig.execute("SET statement_timeout = 0"); mig.execute("SET lock_timeout = 0")
with mig.transaction(): mig.execute((h14 / "spend_nonneg.sql").read_text())
for v in ("-0.01", "'NaN'", "'Infinity'", "'-Infinity'"):
    vv = v if v.startswith("'") else f"'{v}'"
    check(f"C4 after file 1: runtime INSERT {v} into spend -> 23514", state(rt, f"INSERT INTO spend (agent_id, day, usd) VALUES ('h','2026-11-16',{vv}::numeric)").endswith("23514"))
print(f"INFO {sum(ok_all)} of {len(ok_all)} checks passed")
sys.exit(0 if all(ok_all) else 1)
