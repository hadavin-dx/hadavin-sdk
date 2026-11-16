"""Independent hostile tests of the v18 DB-3 / DB-2 files and migrations (EVIDENCE RUNNER; written by the runner, not the builder).
Sections: B runtime role (reserve/settle/kill switch/direct DML), O operator role rights, C migrate four times + fingerprints,
D lock_timeout 55P03 on all held files, T trigger cost 5 runs. Lines: EXPECT PASS/FAIL against a stated property, OBS what happened.
Usage: python hostile_v18.py <socket_dir> <src_dir> <held18> <held16>   (HV_ADMIN_PW in the environment). Made-up data only."""
import sys, os, time, shutil, tempfile, secrets, subprocess, hashlib, statistics, unicodedata
from datetime import date
from decimal import Decimal
from pathlib import Path
sock, src, H18, H16 = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, src); sys.path.insert(0, str(H18.parent))
import psycopg
from psycopg import sql
import hadavin_sdk.store.migrate as m
import secdef_audit_v18 as au
D, MO = date(2026, 11, 16), date(2026, 11, 1)
PW = {"postgres": os.environ["HV_ADMIN_PW"]}
admin = psycopg.connect(f"host={sock} dbname=postgres user=postgres password={PW['postgres']}", autocommit=True)
for r in ("migr_i", "rt_i", "op_i"):
    PW[r] = secrets.token_hex(16)
    admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(r), sql.Literal(PW[r])))
ROLES = {"runtime": "rt_i", "operator": "op_i"}
def dsn(u, db, extra=""): return f"host={sock} dbname={db} user={u} password={PW[u]} {extra}"
res = []
def expect(name, ok, detail=""):
    res.append(bool(ok)); print(("EXPECT PASS " if ok else "EXPECT FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)
def obs(s): print("OBS " + s, flush=True)
def code(fn):
    try: fn(); return None
    except psycopg.Error as e: return str(e.sqlstate)
SEL = {k: m.Grant("table", "SELECT") for k in ("spend", "spend_month", "kill_switch")}
ORIG = {k: m.GRANTS[k] for k in SEL}
real_files = m._migration_files
def build(db, files, hard=True):
    admin.execute(f"CREATE DATABASE {db} OWNER migr_i")
    tmp = Path(tempfile.mkdtemp(prefix="hv18ind_"))
    for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmp / p.name)
    for p, n in files: shutil.copy(p, tmp / f"{n}.sql")
    for k in ("spend_decrease_log", "kill_switch_log"):
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if any("decrease_log" in str(p) for p, _ in files) else m.GRANTS.pop(k, None))
    m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
    m.GRANTS.update(SEL if hard else ORIG)
    m.migrate(dsn("migr_i", db), runtime_role="rt_i")
    mg = psycopg.connect(dsn("migr_i", db), autocommit=True)
    if hard: au.apply_function_grants(mg, roles=ROLES)
    return mg, tmp
FILES = [(H18 / "spend_decrease_log.sql", "0006_dec"), (H18 / "spend_guarded_writes.sql", "0007_guard")]
mg, tmp = build("h1", FILES)
rt = psycopg.connect(dsn("rt_i", "h1"), autocommit=True); op = psycopg.connect(dsn("op_i", "h1"), autocommit=True)
obs("postgres " + mg.execute("SHOW server_version").fetchone()[0])
R = lambda ag, w, c=None, day=D: (c or rt).execute("SELECT * FROM spend_reserve(%s,%s,%s)", (ag, day, w)).fetchone()
S = lambda ag, w, a, c=None, day=D: (c or rt).execute("SELECT * FROM spend_settle(%s,%s,%s,%s)", (ag, day, w, a)).fetchone()
def tot(ag, day=D): return mg.execute("SELECT usd, open_usd FROM spend WHERE agent_id=%s AND day=%s", (ag, day)).fetchone()
def mtot(ag, mo=MO): return mg.execute("SELECT usd, open_usd FROM spend_month WHERE agent_id=%s AND month=%s", (ag, mo)).fetchone()
def bad_rows(): return mg.execute("SELECT (SELECT count(*) FROM spend WHERE usd<0 OR open_usd<0 OR usd<open_usd OR usd='NaN' OR open_usd='NaN') + (SELECT count(*) FROM spend_month WHERE usd<0 OR open_usd<0 OR usd<open_usd OR usd='NaN' OR open_usd='NaN')").fetchone()[0]

print("==== B. runtime role: amounts")
VALS = [("negative -1", Decimal("-1")), ("zero", Decimal("0")), ("1e12 (the ceiling itself)", Decimal("1e12")), ("999999999999.99 (just under)", Decimal("999999999999.99")),
        ("NaN", Decimal("NaN")), ("Infinity", Decimal("Infinity")), ("-Infinity", Decimal("-Infinity")), ("1e30", Decimal("1e30")), ("1e131072 (numeric overflow)", Decimal("1e131072")), ("NULL", None), ("0.0000000001", Decimal("0.0000000001"))]
for i, (nm, v) in enumerate(VALS):
    ag = f"amt{i}"; before = bad_rows()
    c1 = code(lambda: R(ag, v)); t1, m1 = tot(ag), mtot(ag)
    obs(f"B1 reserve {nm}: sqlstate={c1} day={t1} month={m1}")
    expect(f"B1 reserve {nm}: no row ends negative, NaN, or with open above total", bad_rows() == before == 0, f"bad rows {before}->{bad_rows()}")
    if nm in ("negative -1", "NaN", "Infinity", "-Infinity", "1e30", "1e12 (the ceiling itself)", "NULL"):
        expect(f"B1 reserve {nm}: refused or inert (no money recorded)", c1 is not None or t1 in (None, (Decimal(0), Decimal(0))), f"sqlstate={c1} day={t1}")
    # settle (after a 10 reservation) with the same value as worst and as actual
    R("s%d" % i, Decimal("10"))
    for lab, w, a in (("worst", v, Decimal("0")), ("actual", Decimal("10"), v)):
        b4 = tot("s%d" % i)
        c2 = code(lambda: S("s%d" % i, w, a)); aft = tot("s%d" % i)
        obs(f"B2 settle({lab}={nm}) after reserve 10: sqlstate={c2} before={b4} after={aft}")
        expect(f"B2 settle {lab}={nm}: settled money (total - open) never falls", aft is not None and (aft[0] - aft[1]) >= (b4[0] - b4[1]), f"{b4}->{aft}")
        if aft != b4: break
expect("B2 after the amount tests no row is negative, NaN or open>total", bad_rows() == 0, str(bad_rows()))
print("==== B. runtime role: agent names")
NAMES = [("empty string", ""), ("1 char", "a"), ("200 chars", "x" * 200), ("201 chars", "x" * 201), ("200 unicode (é, 2 bytes each)", "é" * 200), ("201 unicode", "é" * 201),
         ("200 emoji (4 bytes each)", "\U0001F600" * 200), ("201 emoji", "\U0001F600" * 201), ("NULL", None), ("whitespace only", "   "), ("newline and quote", "a\n'\";--"),
         ("NFC é", unicodedata.normalize("NFC", "café")), ("NFD é (looks identical)", unicodedata.normalize("NFD", "café")), ("UPPER vs lower: A", "A"), ("lower a (separate from 'a'?)", "a")]
for nm, v in NAMES:
    c1 = code(lambda: R(v, Decimal("1"))); n = mg.execute("SELECT count(*) FROM spend WHERE agent_id IS NOT DISTINCT FROM %s AND day=%s", (v, D)).fetchone()[0] if v is not None else 0
    obs(f"B3 reserve with agent name {nm}: sqlstate={c1} rows={n}")
    if nm in ("empty string", "201 chars", "201 unicode", "201 emoji", "NULL"): expect(f"B3 agent name {nm} refused", c1 is not None and n == 0, f"sqlstate={c1}")
    if nm in ("1 char", "200 chars", "200 unicode (é, 2 bytes each)", "200 emoji (4 bytes each)"): expect(f"B3 agent name {nm} accepted", c1 is None and n == 1, f"sqlstate={c1}")
obs("B3 observation: names 'café' (NFC) and 'café' (NFD) are separate agent ids and so separate budgets: " + str(mg.execute("SELECT count(*) FROM spend WHERE agent_id LIKE 'caf%'").fetchone()[0]) + " rows")
print("==== B. runtime role: another agent's reservation, days and months")
R("owner_a", Decimal("7")); R("victim", Decimal("9"))
r = S("victim", Decimal("9"), Decimal("0"), c=rt)
obs(f"B4 the runtime login settles another agent's open reservation (agent id is only an argument): settle('victim',9,0) -> {r}; victim now {tot('victim')}")
expect("B4 settled money of the other agent is untouched", tot("owner_a") == (Decimal(7), Decimal(7)), str(tot("owner_a")))
c = code(lambda: S("victim", Decimal("9"), Decimal("0"))); expect("B4b second settle of the same reservation refused 23514", c == "23514", f"sqlstate={c}")
c = code(lambda: S("owner_a", Decimal("8"), Decimal("0"))); expect("B4c settle with worst larger than open refused 23514", c == "23514", f"sqlstate={c}")
r = S("never_seen", Decimal("1"), Decimal("1")); obs(f"B5 settle for an agent with no row: returns {r}, rows created={mg.execute('SELECT count(*) FROM spend WHERE agent_id=%s',("never_seen",)).fetchone()[0]}")
r = S("owner_a", Decimal("0"), Decimal("5")); obs(f"B5b settle worst 0 actual 5 (cost added without a reservation): {r} -> raises total, safe direction")
for nm, day in (("1999-01-01", date(1999, 1, 1)), ("9999-12-31 (Python date.max; NOT the Postgres infinity)", date.max), ("0001-01-01", date.min), ("2026-02-30 n/a, leap day 2024-02-29", date(2024, 2, 29))):
    c = code(lambda: R("days", Decimal("1"), day=day)); obs(f"B6 reserve for day {nm}: sqlstate={c}; month rows for agent: {mg.execute('SELECT month::text FROM spend_month WHERE agent_id=%s ORDER BY 1', ('days',)).fetchall()}")
for lit in ("infinity", "-infinity"):
    c = code(lambda: rt.execute(f"SELECT * FROM spend_reserve('inf', '{lit}'::date, 1)")); obs(f"B6 reserve for the Postgres date '{lit}': sqlstate={c}; month rows: {mg.execute('SELECT month::text FROM spend_month WHERE agent_id=%s', ('inf',)).fetchall()}")
c = code(lambda: rt.execute("SELECT * FROM spend_reserve('d', NULL, 1)")); expect("B6 NULL day refused", c is not None, f"sqlstate={c}")
c = code(lambda: rt.execute("SELECT * FROM spend_reserve('d', %s, 1, 1)", (D,))); expect("B6b the v17 four-argument call (a caller-chosen month) no longer exists", c == "42883", f"sqlstate={c}")
c = code(lambda: rt.execute("SELECT * FROM spend_reserve('d', %s, 1::numeric, 99)", (D,))); obs(f"B6c extra argument -> {c}")
expect("B7 invariants after all of B", bad_rows() == 0, str(bad_rows()))
print("==== B. runtime role: kill switch")
st0 = mg.execute('SELECT "on","by" FROM kill_switch').fetchone(); obs(f"B8 start state {st0}")
for label, fn in (("engage with an argument (forged by)", lambda: rt.execute("SELECT kill_switch_engage('forged')")), ("release by runtime", lambda: rt.execute("SELECT kill_switch_release()")),
                  ("direct UPDATE on=false", lambda: rt.execute('UPDATE kill_switch SET "on"=false')), ("direct INSERT", lambda: rt.execute("INSERT INTO kill_switch(id,schema_version,\"on\",\"by\",ts) VALUES (2,1,true,'x',now())")),
                  ("DELETE", lambda: rt.execute("DELETE FROM kill_switch")), ("TRUNCATE", lambda: rt.execute("TRUNCATE kill_switch")),
                  ("set_config session_authorization", lambda: rt.execute("SELECT set_config('session_authorization','op_i',false)")), ("SET ROLE op_i", lambda: rt.execute("SET ROLE op_i")),
                  ("SET SESSION AUTHORIZATION op_i", lambda: rt.execute("SET SESSION AUTHORIZATION op_i"))):
    c = code(fn); expect(f"B8 runtime role: {label} refused", c in ("42501", "42883", "22023", "55P02"), f"sqlstate={c}")
rt.execute("SELECT kill_switch_engage()"); s1 = mg.execute('SELECT "on","by",ts FROM kill_switch').fetchone()
expect("B9 runtime engage works and records by=session login", s1[0] is True and s1[1] == "rt_i", str(s1[:2]))
time.sleep(0.05); rt.execute("SELECT kill_switch_engage()"); s2 = mg.execute('SELECT "on","by",ts FROM kill_switch').fetchone()
expect("B9b engage again on an ON switch leaves by and ts alone", s1 == s2, f"{s1} vs {s2}")
op.execute("SELECT kill_switch_release()"); s3 = mg.execute('SELECT "on","by" FROM kill_switch').fetchone(); expect("B10 operator release works, by=op_i", s3 == (False, "op_i"), str(s3))
s3a = mg.execute('SELECT ts FROM kill_switch').fetchone()[0]; op.execute("SELECT kill_switch_release()"); expect("B10b release on an OFF switch changes nothing", mg.execute('SELECT ts FROM kill_switch').fetchone()[0] == s3a)
mg.execute("DELETE FROM kill_switch"); rt.execute("SELECT kill_switch_engage()"); expect("B11 row missing: engage creates it ON", mg.execute('SELECT "on" FROM kill_switch').fetchone() == (True,))
op.execute("SELECT kill_switch_release()"); rt.execute("SELECT kill_switch_engage()")
expect("B12 the kill-switch log recorded changes (rows in kill_switch_log)", mg.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] >= 3, str(mg.execute("SELECT count(*) FROM kill_switch_log").fetchone()))
print("==== B. runtime role: direct DML on the three tables")
for tb in ("spend", "spend_month", "kill_switch"):
    for verb, q in (("INSERT", None), ("UPDATE", f"UPDATE {tb} SET usd = 0" if tb != "kill_switch" else 'UPDATE kill_switch SET "on" = false'), ("DELETE", f"DELETE FROM {tb}"), ("TRUNCATE", f"TRUNCATE {tb}"),
                    ("SELECT FOR UPDATE", f"SELECT * FROM {tb} FOR UPDATE"), ("COPY FROM", None), ("ALTER TABLE", f"ALTER TABLE {tb} DISABLE TRIGGER ALL"), ("DROP TRIGGER", None)):
        if verb == "INSERT": q = {"spend": "INSERT INTO spend(agent_id,day,usd) VALUES ('z',%s,1)", "spend_month": "INSERT INTO spend_month(agent_id,month,usd) VALUES ('z',%s,1)", "kill_switch": "INSERT INTO kill_switch(id,schema_version,\"on\",\"by\",ts) VALUES (9,1,true,'x',now())"}[tb]
        if verb in ("COPY FROM", "DROP TRIGGER"): continue
        c = code(lambda: rt.execute(q, (D,)) if "%s" in q else rt.execute(q)); expect(f"B13 runtime {verb} on {tb} refused (42501)", c == "42501", f"sqlstate={c}")
for q in ("DELETE FROM spend_decrease_log", "UPDATE kill_switch_log SET new_on = true", "TRUNCATE spend_decrease_log", "INSERT INTO spend_decrease_log(agent_id,period,scope,old_usd,new_usd) VALUES ('x',now(),'s',1,0)"):
    c = code(lambda: rt.execute(q)); expect(f"B14 runtime: {q[:45]} refused", c in ("42501", "42P01"), f"sqlstate={c}")
c = code(lambda: rt.execute("CREATE FUNCTION public.evil() RETURNS int LANGUAGE sql AS 'SELECT 1'")); obs(f"B15 runtime CREATE FUNCTION in public: sqlstate={c}")
c = code(lambda: rt.execute("CREATE TEMP TABLE spend(agent_id text, day date, usd numeric)")); obs(f"B15b runtime CREATE TEMP TABLE spend (shadow): sqlstate={c}")
if c is None:
    r = R("shadowtest", Decimal("1")); real = tot("shadowtest"); expect("B15c a temp table named spend does not capture the function's write (BEGIN ATOMIC binds objects)", real == (Decimal(1), Decimal(1)), f"{r} real={real}")
    rt.execute("DROP TABLE pg_temp.spend")
for sch in ("pg_temp",):
    pass
c = code(lambda: rt.execute("SET search_path = pg_temp, public")); r2 = None
if c is None:
    R("sp_path", Decimal("1")); expect("B15d with search_path = pg_temp,public the function still writes the real table", tot("sp_path") == (Decimal(1), Decimal(1)), str(tot("sp_path")))
    rt.execute("RESET search_path")
expect("B16 invariants after kill switch and DML tests", bad_rows() == 0, str(bad_rows()))

print("==== O. operator role: rights")
def priv_matrix(role):
    rows = mg.execute("SELECT c.relname, c.relkind, " + ", ".join(f"has_table_privilege(%s, c.oid, '{p}')" for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")) + " FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','p','v','m','S') ORDER BY 1", (role,) * 7).fetchall()
    return rows
for role in ("rt_i", "op_i"):
    for r in priv_matrix(role):
        got = [p for p, v in zip(("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"), r[2:]) if v]
        if got: obs(f"O1 {role} on {r[0]} ({r[1]}): {','.join(got)}")
    fns = mg.execute("SELECT p.oid::regprocedure::text FROM pg_proc p WHERE pronamespace='public'::regnamespace AND has_function_privilege(%s, p.oid, 'EXECUTE') ORDER BY 1", (role,)).fetchall()
    obs(f"O2 {role} can EXECUTE: {[f[0] for f in fns]}")
    obs(f"O3 {role}: schema public CREATE={mg.execute('SELECT has_schema_privilege(%s,%s,%s)', (role,'public','CREATE')).fetchone()[0]}, database TEMP={mg.execute('SELECT has_database_privilege(%s,current_database(),%s)', (role,'TEMP')).fetchone()[0]}, CREATE={mg.execute('SELECT has_database_privilege(%s,current_database(),%s)', (role,'CREATE')).fetchone()[0]}; member of: {mg.execute('SELECT r.rolname FROM pg_auth_members a JOIN pg_roles r ON r.oid=a.roleid JOIN pg_roles u ON u.oid=a.member WHERE u.rolname=%s', (role,)).fetchall()}; superuser/createrole/createdb: {mg.execute('SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls FROM pg_roles WHERE rolname=%s', (role,)).fetchone()}")
opm = {r[0]: r[2:] for r in priv_matrix("op_i")}
expect("O4 the operator role holds no INSERT/UPDATE/DELETE/TRUNCATE on any of the three tables", all(not any(opm[t][1:5]) for t in ("spend", "spend_month", "kill_switch")), str({t: opm[t] for t in ("spend", "spend_month", "kill_switch")}))
for tb, q in (("spend", "UPDATE spend SET usd=0"), ("kill_switch", 'UPDATE kill_switch SET "on"=false'), ("spend", "DELETE FROM spend"), ("kill_switch", "TRUNCATE kill_switch")):
    c = code(lambda: op.execute(q)); expect(f"O5 operator: {q} refused (42501)", c == "42501", f"sqlstate={c}")
for q in ("SELECT * FROM spend", "SELECT * FROM kill_switch", "SELECT * FROM spend_decrease_log", "SELECT * FROM kill_switch_log", "SELECT count(*) FROM runs"):
    c = code(lambda: op.execute(q)); obs(f"O6 operator {q}: sqlstate={c} ({'allowed' if c is None else 'refused'})")
c = code(lambda: op.execute("SELECT * FROM spend_reserve('opx', %s, 1)", (D,))); obs(f"O7 operator calls spend_reserve: sqlstate={c}")
c = code(lambda: op.execute("SELECT kill_switch_engage()")); obs(f"O7b operator calls kill_switch_engage: sqlstate={c}")
c = code(lambda: op.execute("SELECT * FROM spend_settle('opx', %s, 1, 0)", (D,))); obs(f"O7c operator calls spend_settle: sqlstate={c}")
print("==== O. the start-up audit query")
pr = au.secdef_problems(mg, roles=ROLES, owner="migr_i"); expect("O8 secdef_problems (builder's start-up query) is empty on the fresh state", pr == [], str(pr[:3]))

print("==== C. migrate four times, table fingerprints")
DUMPS = []
def fp(db):
    c = psycopg.connect(dsn("migr_i", db), autocommit=True)
    parts = []
    parts.append(c.execute("SELECT string_agg(pg_get_functiondef(p.oid) || coalesce(p.proacl::text,'') || p.proowner::regrole::text, E'\\n' ORDER BY p.oid::regprocedure::text) FROM pg_proc p WHERE pronamespace='public'::regnamespace").fetchone()[0])
    parts.append(c.execute("SELECT string_agg(conrelid::regclass || conname || pg_get_constraintdef(oid) || convalidated::text, E'\\n' ORDER BY conrelid::regclass::text, conname) FROM pg_constraint WHERE connamespace='public'::regnamespace").fetchone()[0])
    parts.append(c.execute("SELECT string_agg(pg_get_triggerdef(oid), E'\\n' ORDER BY pg_get_triggerdef(oid)) FROM pg_trigger WHERE NOT tgisinternal").fetchone()[0])
    parts.append(c.execute("SELECT string_agg(attrelid::regclass || attname || format_type(atttypid, atttypmod) || attnotnull::text || coalesce(pg_get_expr(d.adbin,d.adrelid),''), E'\\n' ORDER BY attrelid::regclass::text, attname) FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum WHERE a.attrelid IN (SELECT oid FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r') AND attnum>0 AND NOT attisdropped").fetchone()[0])
    parts.append(c.execute("SELECT string_agg(relname || coalesce(relacl::text,'') || relowner::regrole::text, E'\\n' ORDER BY relname) FROM pg_class WHERE relnamespace='public'::regnamespace").fetchone()[0])
    parts.append(c.execute("SELECT string_agg(indexdef, E'\\n' ORDER BY indexdef) FROM pg_indexes WHERE schemaname='public'").fetchone()[0])
    env = dict(os.environ, PGPASSWORD=PW["migr_i"]); dump = subprocess.run(["/usr/lib/postgresql/16/bin/pg_dump", "-h", sock, "-U", "migr_i", "-s", "-d", db], env=env, capture_output=True, text=True).stdout
    dump = "\n".join(l for l in dump.splitlines() if not l.startswith("--") and not l.startswith("\\restrict") and not l.startswith("\\unrestrict"))
    led = [r for r in c.execute("SELECT * FROM schema_migrations ORDER BY 1").fetchall()] if c.execute("SELECT to_regclass('schema_migrations')").fetchone()[0] else None
    DUMPS.append(dump)
    return [hashlib.sha256((p or "").encode()).hexdigest()[:12] for p in parts] + [hashlib.sha256(dump.encode()).hexdigest()[:12], len(dump)], led
tables = mg.execute("SELECT relname FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r' ORDER BY 1").fetchall()
obs("C0 tables: " + ",".join(t[0] for t in tables))
ledtab = mg.execute("SELECT relname FROM pg_class WHERE relnamespace='public'::regnamespace AND relname = 'schema_migrations'").fetchall(); obs(f"C0 ledger tables: {ledtab}")
f0, l0 = fp("h1")
fps = [f0]
for i in range(4):
    m.GRANTS.update(SEL); m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
    applied = m.migrate(dsn("migr_i", "h1"), runtime_role="rt_i"); au.apply_function_grants(mg, roles=ROLES); fps.append(fp("h1")[0]); obs(f"C{i+1} migrate() run {i+1}: returned {applied!r}; fingerprint {fps[-1]}")
import difflib
if any(f != fps[0] for f in fps):
    for k in (1, 2, 3, 4):
        dl = [l for l in difflib.unified_diff(DUMPS[0].splitlines(), DUMPS[k].splitlines(), lineterm='', n=0) if not l.startswith(('---','+++','@@'))]
        obs(f'C-diff run0 vs dump of run {k}: {len(dl)} differing lines: ' + ' || '.join(dl[:8])[:900])
expect("C5 the fingerprint (functions+ACL+owner, constraints, triggers, columns, table ACL+owner, indexes, pg_dump -s) is identical after run 0 and runs 1 to 4", all(f == fps[0] for f in fps), str(fps[0]) + " vs " + str(set(map(tuple, fps))))
# fresh database with the same files migrated four times from empty vs once: same fingerprint
mgb, tmpb = build("h2", FILES)
for _ in range(3): m.migrate(dsn("migr_i", "h2"), runtime_role="rt_i"); au.apply_function_grants(mgb, roles=ROLES)
expect("C6 a second fresh database migrated four times has the same fingerprint as the first (deterministic)", fp("h2")[0][:6] == fps[0][:6], str(fp("h2")[0]) + " vs " + str(fps[0]))
print("==== D. lock_timeout (55P03) on all held files")
def hold_and_migrate(db, tmpd, newfile, number, table, mode, cap_s=15):
    shutil.copy(newfile, tmpd / f"{number}.sql")
    for k in ("spend_decrease_log", "kill_switch_log"): (m.GRANTS.__setitem__(k, m.Grant("table", "")) if "decrease_log" in str(newfile) else m.GRANTS.pop(k, None))
    hold = psycopg.connect(dsn("migr_i", db)); hold.execute(f"LOCK TABLE {table} IN {mode} MODE")
    t0 = time.monotonic(); cd = None
    try: m.migrate(dsn("migr_i", db, f"options='-c statement_timeout={cap_s*1000}'"), runtime_role="rt_i")
    except psycopg.Error as e: cd = str(e.sqlstate)
    dt = time.monotonic() - t0; hold.rollback(); hold.close(); (tmpd / f"{number}.sql").unlink()
    return cd, dt
HF = [("spend_nonneg.sql", None), ("spend_nonneg_finite.sql", None), ("spend_nonneg_upgrade.sql", "spend_nonneg.sql"), ("spend_decrease_log.sql", None), ("spend_guarded_writes.sql", None)]
for f, pre in HF:
    for table, mode in (("spend", "ROW EXCLUSIVE"), ("spend_month", "ROW EXCLUSIVE"), ("kill_switch", "ROW EXCLUSIVE"), ("spend", "ACCESS SHARE")):
        db = "d_" + secrets.token_hex(3); m.GRANTS.update(ORIG); m.GRANTS.pop('spend_decrease_log', None); m.GRANTS.pop('kill_switch_log', None)
        tmpd = None
        admin.execute(f"CREATE DATABASE {db} OWNER migr_i"); tmpd = Path(tempfile.mkdtemp(prefix="hv18indd_"))
        for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmpd / p.name)
        if pre: shutil.copy(H18 / pre, tmpd / "0006_pre.sql")
        m._migration_files = lambda folder=tmpd: sorted(Path(folder).glob("*.sql")); m.migrate(dsn("migr_i", db), runtime_role="rt_i")
        fa = fp(db)[0]; num = "0007_x" if pre else "0006_x"
        cd, dt = hold_and_migrate(db, tmpd, H18 / f, num, table, mode); fb = fp(db)[0]
        obs(f"D {f} with {mode} held on {table}: sqlstate={cd} after {dt:.2f}s; schema unchanged={fa == fb}; ledger rows now={psycopg.connect(dsn('migr_i', db)).execute('SELECT count(*) FROM schema_migrations').fetchone()[0] if ledtab else '?'}")
        if mode == "ROW EXCLUSIVE":
            conflict = table in ("spend", "spend_month") or (table == "kill_switch" and f == "spend_decrease_log.sql")
            if conflict: expect(f"D {f} ROW EXCLUSIVE on {table}: 55P03 within 4 to 9 s and nothing applied", cd == "55P03" and 4 <= dt <= 9 and fa == fb, f"{cd} {dt:.2f}s unchanged={fa == fb}")
            else: obs(f"D (no lock conflict expected: the file does not touch {table}) {f}: sqlstate={cd}")
print("==== T. DB-2 trigger cost per lowering, 5 runs (runtime role, 20000 lowering UPDATEs, grants as migrate() gives them)")
def timing(db, with_trigger):
    files = [(H18 / "spend_decrease_log.sql", "0006_dec")] if with_trigger else []
    mgx, _ = build(db, files, hard=False)
    c = psycopg.connect(dsn("rt_i", db), autocommit=True); c.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('t', %s, 1000000)", (D,))
    t0 = time.perf_counter()
    for _ in range(20000): c.execute("UPDATE spend SET usd = usd - 0.0001 WHERE agent_id = 't' AND day = %s", (D,))
    ms = (time.perf_counter() - t0) * 1000
    size = mgx.execute("SELECT pg_total_relation_size('spend_decrease_log'), count(*) FROM spend_decrease_log").fetchone() if with_trigger else None
    return ms, size
per = []
for i in range(5):
    order = (False, True) if i % 2 == 0 else (True, False)
    r = {}
    for wt in order: r[wt] = timing(f"t{i}{'w' if wt else 'n'}", wt)
    p = (r[True][0] - r[False][0]) / 20000; per.append(p)
    obs(f"T run {i+1} (order {'without,with' if not order[0] else 'with,without'}): without {r[False][0]:.0f} ms, with {r[True][0]:.0f} ms, +{p:.3f} ms per lowering, log rows {r[True][1][1]}, relation size {r[True][1][0]} bytes ({r[True][1][0]/r[True][1][1]:.1f} per row)")
obs(f"T per-lowering cost over 5 runs: min {min(per):.3f}, median {statistics.median(per):.3f}, max {max(per):.3f} ms")
print(f"SUMMARY expect lines: {sum(res)} passed of {len(res)}")
