"""INDEPENDENT hostile run against hand-off v20 (EVIDENCE RUNNER: records, never judges). Written by the runner; no spelling copied from the author's lists.
Usage (through run_pg_v20_tmp.sh, which starts a throwaway cluster under /tmp): python -I -B hostile_v20_indep.py <socket_dir> <src_dir> <held_dir_v20> <unused>
Part F: file spellings. Each is the REAL v20 held file text plus/with a hostile change. Columns: guard verdict (the v20 guard + allow_v20 pins, file name decides the pins),
  server behaviour (the mutated file is applied by the REAL migrate() on a fresh database; then the runtime login runs the probe), rows left (spend / spend_month / kill switch).
Part D: hostile data given to the GENUINE v20 DB-3 functions by the runtime login. Part R: things a runtime login tries on its own.
BYPASS CANDIDATE (mechanical rule): guard CLEAN and (probe changed data, or leaked the marker, or the structure differs from the genuine file's structure)."""
import sys, os, secrets, shutil, tempfile, atexit, json, unicodedata
from datetime import date
from pathlib import Path
sock, src, HELD = sys.argv[1], sys.argv[2], Path(sys.argv[3])
V = HELD.parent
sys.path.insert(0, str(V)); sys.path.insert(0, src)
import psycopg
from psycopg import sql
import hadavin_sdk.store.migrate as m
import secdef_guard_v20 as g20
import allow_v20 as A20
import secdef_audit_v20 as au

PW = {"postgres": os.environ["HV_ADMIN_PW"]}
def dsn(u, db): return f"host={sock} dbname={db} user={u} password={PW[u]}"
admin = psycopg.connect(dsn("postgres", "postgres"), autocommit=True)
for r in ("migr17", "rt17", "op17"):
    PW[r] = secrets.token_hex(16)
    admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(r), sql.Literal(PW[r])))
D = date(2026, 11, 16)
DB2N, DB3N = "spend_decrease_log.sql", "spend_guarded_writes.sql"
T2, T3 = (HELD / DB2N).read_text(), (HELD / DB3N).read_text()
SEL = {k: m.Grant("table", "SELECT") for k in ("spend", "spend_month", "kill_switch")}
ORIG = {k: m.GRANTS[k] for k in SEL}
SP = "SET search_path = pg_catalog, pg_temp"
MARK = "LEAKMARK-" + secrets.token_hex(3)
real_files = m._migration_files

def verdict(name, text):
    try:
        p = A20.check(g20, name, text)
        return ("CLEAN" if not p else f"FLAGGED({len(p)})"), p
    except Exception as e:  # a crash of the guard is itself a result
        return f"GUARD-CRASH({type(e).__name__})", [repr(e)[:120]]

def grant_fns(db):
    """what the start-up grant step does (author's prototype apply_function_grants), limited to the functions that exist in this database"""
    try:
        mgx = psycopg.connect(dsn("migr17", db), autocommit=True)
        have = {r[0] for r in mgx.execute("SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace")}
        pol = {k: v for k, v in au.FUNCTION_POLICY.items() if k.split("(")[0] in have}
        au.apply_function_grants(mgx, roles={"runtime": "rt17", "operator": "op17"}, policy=pol)
    except Exception as e:
        return f"APPLIED, but the function-grant step failed {type(e).__name__}: {str(e).splitlines()[0][:80]}"
    return None

def apply_files(db, db2_text, db3_text):
    """fresh database owned by the migration role; real 0001-0005, then DB-2 and DB-3 texts (None = not applied). Returns ('ok'|'REJECTED ...', tmp)."""
    admin.execute(sql.SQL("CREATE DATABASE {} OWNER migr17").format(sql.Identifier(db)))
    tmp = Path(tempfile.mkdtemp(prefix="hv20ind_")); atexit.register(shutil.rmtree, tmp, True)
    for p in real_files(m.MIGRATIONS): shutil.copy(p, tmp / p.name)
    if db2_text is not None: (tmp / "0006_dec.sql").write_text(db2_text)
    if db3_text is not None: (tmp / "0007_guard.sql").write_text(db3_text)
    for k in ("spend_decrease_log", "kill_switch_log"):
        (m.GRANTS.__setitem__(k, m.Grant("table", "")) if db2_text is not None else m.GRANTS.pop(k, None))
    m.GRANTS.update(ORIG)
    m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
    try:
        m.migrate(dsn("migr17", db), runtime_role="rt17")
    except psycopg.Error as e:
        return f"REJECTED by server {e.sqlstate}: {str(e).splitlines()[0][:70]}", tmp
    except Exception as e:
        return f"REJECTED by migrate() {type(e).__name__}: {str(e).splitlines()[0][:90]}", tmp
    m.GRANTS.update(SEL)
    try:
        for _ in range(2): m.migrate(dsn("migr17", db), runtime_role="rt17")
    except Exception as e:
        return f"APPLIED, but re-run of migrate() failed {type(e).__name__}: {str(e).splitlines()[0][:80]}", tmp
    r = grant_fns(db)
    if r: return r, tmp
    return "ok", tmp

def structure(c):
    q = lambda s: c.execute(s).fetchall()
    return {
     "triggers": q("SELECT tgrelid::regclass::text, tgname, tgenabled FROM pg_trigger WHERE NOT tgisinternal ORDER BY 1,2"),
     "functions": q("SELECT p.oid::regprocedure::text, p.prosecdef, p.proconfig, pg_get_userbyid(p.proowner), md5(pg_get_functiondef(p.oid)) FROM pg_proc p WHERE pronamespace='public'::regnamespace ORDER BY 1"),
     "constraints": q("SELECT conrelid::regclass::text, conname, convalidated, pg_get_constraintdef(oid) FROM pg_constraint WHERE connamespace='public'::regnamespace AND conrelid::regclass::text IN ('spend','spend_month','kill_switch') ORDER BY 1,2"),
     "rules_policies": q("SELECT 'rule', tablename, rulename FROM pg_rules WHERE schemaname='public' UNION ALL SELECT 'policy', tablename, policyname FROM pg_policies UNION ALL SELECT 'rls', relname, relrowsecurity::text FROM pg_class WHERE relname IN ('spend','spend_month','kill_switch') ORDER BY 1,2,3"),
     "relations": q("SELECT relname, relkind FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind IN ('r','v','m','f','p') ORDER BY 1"),
     "owner_acl": q("SELECT relname, pg_get_userbyid(relowner), relacl::text FROM pg_class WHERE relname IN ('spend','spend_month','kill_switch') ORDER BY 1"),
    }
def data(c):
    return (c.execute("SELECT agent_id, day, usd, 0 FROM spend ORDER BY 1,2").fetchall(), c.execute("SELECT agent_id, month, usd, 0 FROM spend_month ORDER BY 1,2").fetchall(),
            c.execute('SELECT "on" FROM kill_switch ORDER BY id').fetchall())
def seed(c):
    c.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('seed', %s, 100)", (D,))
    c.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('seed', %s, 100)", (date(2026, 11, 1),))
    c.execute('INSERT INTO kill_switch (id, schema_version, "on", "by", ts) VALUES (1, 1, true, \'seed\', now()) ON CONFLICT (id) DO UPDATE SET "on" = true')
    c.execute("CREATE TABLE IF NOT EXISTS secret_t (v text)"); c.execute("INSERT INTO secret_t VALUES (%s)", (MARK,))

# genuine reference structure
ok, _ = apply_files("ref_genuine", T2, T3); assert ok == "ok", ok
_mgref = psycopg.connect(dsn("migr17", "ref_genuine"), autocommit=True); seed(_mgref); REF = structure(_mgref)
gv, gp = verdict(DB3N, T3); g2v, _ = verdict(DB2N, T2)
print(f"GENUINE-CHECK v20 DB-3 guard verdict {gv}; DB-2 guard verdict {g2v}; genuine DBs applied ok", flush=True)

rows = []   # (id, family, spelling, guard, server, effect, left)
def snapshot_diff(a, b): return [k for k in a if a[k] != b[k]]
def run_file_case(cid, fam, what, text, probes, target="db3", base_name=None):
    name = base_name or (DB3N if target == "db3" else DB2N)
    gvd, gprob = verdict(name, text)
    db = "f_" + cid.lower().replace("-", "")
    srv, tmp = apply_files(db, T2 if target == "db3" else text, text if target == "db3" else None)
    eff, left = "n/a (not applied)", "n/a"
    if srv == "ok":
        mg = psycopg.connect(dsn("migr17", db), autocommit=True)
        try: seed(mg)
        except Exception as e: seed_err = str(e)[:60]
        st0, d0 = structure(mg), data(mg)
        rt = psycopg.connect(dsn("rt17", db), autocommit=True)
        outs, leaked = [], False
        for p in probes:
            try:
                r = rt.execute(p)
                try: res = r.fetchall()
                except psycopg.ProgrammingError: res = None
                if res is not None and MARK in repr(res): leaked = True
                outs.append("ok")
            except psycopg.Error as e: outs.append(str(e.sqlstate))
        d1 = data(mg)
        sd = [k for k in snapshot_diff(REF, st0)]
        eff = f"probe {','.join(outs)}; data {'CHANGED' if d1 != d0 else 'unchanged'}; leak {'YES' if leaked else 'no'}; structure vs genuine: {','.join(sd) if sd else 'same'}"
        left = f"spend={[(a, str(u)) for a, _, u, _ in d1[0]]} month={[(a, str(u)) for a, _, u, _ in d1[1]]} killsw_on={[x[0] for x in d1[2]]}"
        cand = gvd == "CLEAN" and (d1 != d0 or leaked or sd)
    else:
        cand = False
    rows.append((cid, fam, what, gvd, srv, eff, left, "BYPASS-CANDIDATE" if cand else ""))
    print(f"{cid} | {gvd} | {srv[:60]} | {eff[:110]}" + ("  <<< BYPASS-CANDIDATE" if cand else ""), flush=True)

def pl(name, body, ret="void", hdr=f"LANGUAGE plpgsql SECURITY DEFINER {SP}", args=""):
    return f"CREATE OR REPLACE FUNCTION {name}({args}) RETURNS {ret} {hdr} AS $f$ BEGIN {body} END $f$;\n"
ZW, NB, GREEK_NU, CYR_A = "​", " ", "ν", "а"
CALL = lambda n: [f"SELECT {n}()"]
F = []  # (id, family, spelling, extra-or-full-text, probes, target)
def add(cid, fam, what, extra, probes, target="db3", replace=None):
    F.append((cid, fam, what, extra, probes, target, replace))

# ---- RETURN-expression bodies
add("H01", "RETURN body", "SQL-standard RETURN expr, definer, leaks a table the runtime cannot read via query_to_xml",
    f"CREATE OR REPLACE FUNCTION h01() RETURNS xml LANGUAGE sql SECURITY DEFINER {SP} RETURN query_to_xml('SELECT v FROM public.secret_t', true, false, '');\n", CALL("h01"))
add("H02", "RETURN body", "RETURN calls a second definer plpgsql helper that deletes spend",
    pl("h02_helper", "DELETE FROM public.spend; DELETE FROM public.spend_month;", "int").replace("RETURNS int", "RETURNS int") .replace("END $f$", "RETURN 1; END $f$") +
    f"CREATE OR REPLACE FUNCTION h02() RETURNS int LANGUAGE sql SECURITY DEFINER {SP} RETURN h02_helper();\n", CALL("h02"))
add("H03", "RETURN body", "RETURN set_config('session_replication_role','replica',true) in a definer",
    f"CREATE OR REPLACE FUNCTION h03() RETURNS text LANGUAGE sql SECURITY DEFINER {SP} RETURN pg_catalog.set_config('session_replication_role', 'replica', true);\n", CALL("h03") + ["SELECT current_setting('session_replication_role')"])
add("H04", "RETURN body", "RETURN (data-modifying CTE) is not legal SQL: server must refuse",
    f"CREATE OR REPLACE FUNCTION h04() RETURNS bigint LANGUAGE sql SECURITY DEFINER {SP} RETURN (WITH d AS (DELETE FROM spend RETURNING 1) SELECT count(*) FROM d);\n", CALL("h04"))
add("H05", "RETURN body", "invoker RETURN body with lower-case 'return' and quoted type, no attribute at all (control-like: plain function)",
    "create or replace function h05() returns \"text\" language sql return 'x';\n", CALL("h05"))
# ---- EXECUTE strings, %I/%L/format()
add("H06", "EXECUTE format", "EXECUTE format('DELETE FROM %I.spend', 'public') in a plpgsql definer", pl("h06", "EXECUTE format('DELETE FROM %I.spend', 'public');"), CALL("h06"))
add("H07", "EXECUTE format", "EXECUTE format('UPDATE %s SET usd = %L', 'public.spend', 0)", pl("h07", "EXECUTE format('UPDATE %s SET usd = %L', 'public.spend', 0);"), CALL("h07"))
add("H08", "EXECUTE format", "EXECUTE 'DELETE FROM ' || quote_ident('public') || '.' || quote_ident('spend')", pl("h08", "EXECUTE 'DELETE FROM ' || quote_ident('public') || '.' || quote_ident('spend');"), CALL("h08"))
add("H09", "EXECUTE format", "positional %1$I.%2$I with USING-free format", pl("h09", "EXECUTE format('DELETE FROM %1$I.%2$I', 'public', 'spend');"), CALL("h09"))
add("H10", "EXECUTE format", "EXECUTE of an E-string with escaped quote", pl("h10", "EXECUTE E'DELETE FROM public.spend WHERE agent_id <> \\'\\'';"), CALL("h10"))
add("H11", "EXECUTE format", "EXECUTE of a U&'' unicode-escape string", pl("h11", "EXECUTE U&'DELETE FROM public.spend';"), CALL("h11"))
add("H12", "EXECUTE format", "PERFORM + EXECUTE built by array_to_string (no literal SQL word in the text)", pl("h12", "EXECUTE array_to_string(ARRAY['DELETE','FROM','public.spend'], ' ');"), CALL("h12"))
add("H13", "EXECUTE format", "EXECUTE via chr() codes only (no keyword in text): TRUNCATE", pl("h13", "EXECUTE chr(84)||chr(82)||chr(85)||chr(78)||chr(67)||chr(65)||chr(84)||chr(69)||' public.spend';"), CALL("h13"))
# ---- dollar-quote and nested quote tricks
add("H14", "dollar quote", "body inside $a$ with an inner $b$ string holding the DELETE", f"CREATE OR REPLACE FUNCTION h14() RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS $a$ BEGIN EXECUTE $b$DELETE FROM public.spend$b$; END $a$;\n", CALL("h14"))
add("H15", "dollar quote", "DO block builds a definer function from doubled quotes", "DO $x$ BEGIN EXECUTE 'CREATE FUNCTION h15() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS ''DELETE FROM public.spend'''; END $x$;\n", CALL("h15"))
add("H16", "dollar quote", "tag with a digit-free unicode tag $é$", f"CREATE OR REPLACE FUNCTION h16() RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS $é$ BEGIN DELETE FROM public.spend; END $é$;\n", CALL("h16"))
add("H17", "dollar quote", "single-quoted body with a '' inside a string that contains the word DELETE", f"CREATE OR REPLACE FUNCTION h17() RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS 'BEGIN PERFORM ''x''; DELETE FROM public.spend; END';\n", CALL("h17"))
add("H18", "dollar quote", "comment-looking text inside a quoted identifier hides the attribute", "CREATE OR REPLACE FUNCTION \"h/*18\"() RETURNS void LANGUAGE sql SECURITY DEFINER " + SP + " AS $f$ DELETE FROM public.spend $f$;\nSELECT 1 AS \"*/\";\n", ['SELECT "h/*18"()'])
add("H19", "dollar quote", "nested block comment around the keyword that the server also skips, then a live statement", "/* a /* nested */ still comment */ CREATE OR REPLACE FUNCTION h19() RETURNS void LANGUAGE sql SECURITY /* c */ DEFINER " + SP + " AS $f$ DELETE FROM public.spend $f$;\n", CALL("h19"))
# ---- case and quoted identifiers
add("H20", "case/quoted", "mixed-case keywords sEcUrItY dEfInEr", "CrEaTe Or RePlAcE fUnCtIoN h20() rEtUrNs VoId LaNgUaGe SqL sEcUrItY dEfInEr " + SP + " AS $f$ DELETE FROM public.spend $f$;\n", CALL("h20"))
add("H21", "case/quoted", "quoted upper-case twin \"Spend_Reserve\" of a pinned name, evil body", f"CREATE OR REPLACE FUNCTION \"Spend_Reserve\"(p_agent text, p_day date, p_worst numeric) RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS $f$ BEGIN DELETE FROM public.spend; END $f$;\n", ["SELECT \"Spend_Reserve\"('a', '2026-11-16', 1)"])
add("H22", "case/quoted", "overload spend_reserve(varchar,date,numeric) with evil body (an overload picked by a typed call)", f"CREATE OR REPLACE FUNCTION spend_reserve(p_agent varchar, p_day date, p_worst numeric) RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS $f$ BEGIN DELETE FROM public.spend; END $f$;\n", ["SELECT spend_reserve('a'::varchar, '2026-11-16'::date, 1::numeric)"])
add("H23", "case/quoted", "pinned function re-created with the same signature and an added DELETE in the body (fingerprint pin)", None, ["SELECT * FROM spend_reserve('a', '2026-11-16', 1)"], replace=("BEGIN ATOMIC\n  INSERT INTO spend (agent_id, day, usd, open_usd) SELECT p_agent", "BEGIN ATOMIC\n  DELETE FROM spend WHERE agent_id <> p_agent;\n  INSERT INTO spend (agent_id, day, usd, open_usd) SELECT p_agent"))
add("H24", "case/quoted", "pinned spend_settle with the month guard EXISTS removed (semantic weakening, same statement kinds and tables)", None, ["SELECT * FROM spend_settle('seed', '2026-11-16', 0, 0)"], replace=("      AND EXISTS (SELECT 1 FROM spend_month y WHERE y.agent_id = p_agent AND y.month = date_trunc('month', p_day)::date);", "      AND true;"))
add("H25", "case/quoted", "pinned kill_switch_release without the `AND \"on\" = true` and without session_user (changed by-column)", None, ["SELECT kill_switch_release()"], replace=("WHERE id = 1 AND \"on\" = true;", "WHERE id = 1;"))
# ---- schema-qualified / search_path
add("H26", "schema/search_path", "definer function in schema public, qualified name public.h26", f"CREATE OR REPLACE FUNCTION public.h26() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} AS $f$ DELETE FROM public.spend $f$;\n", CALL("h26"))
add("H27", "schema/search_path", "search_path lists public AFTER pg_temp", "CREATE OR REPLACE FUNCTION h27() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp, public AS $f$ DELETE FROM spend $f$;\n", CALL("h27"))
add("H28", "schema/search_path", "search_path TO form, correct value, but a function not on the list", "CREATE OR REPLACE FUNCTION h28() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path TO pg_catalog, pg_temp AS $f$ DELETE FROM public.spend $f$;\n", CALL("h28"))
add("H29", "schema/search_path", "ALTER FUNCTION of a pinned function to search_path public", "ALTER FUNCTION spend_reserve(text, date, numeric) SET search_path = public;\n", ["SELECT * FROM spend_reserve('a', '2026-11-16', 1)"])
add("H30", "schema/search_path", "ALTER ROUTINE ... SECURITY INVOKER-> DEFINER on a DB-1 style helper (ALTER ROUTINE spelling)", "ALTER ROUTINE spend_settle(text, date, numeric, numeric) OWNER TO op17;\n", ["SELECT 1"])
add("H31", "schema/search_path", "CREATE SCHEMA + shadow function + ALTER ROLE rt17 SET search_path", "CREATE SCHEMA ev31; CREATE FUNCTION ev31.spend_reserve(text, date, numeric) RETURNS void LANGUAGE sql AS $f$ SELECT 1 $f$; ALTER ROLE rt17 SET search_path = ev31, public;\n", ["SELECT spend_reserve('a', '2026-11-16', 1)"])
add("H32", "schema/search_path", "SET search_path at file level (session setting, not LOCAL)", "SET search_path = pg_temp, public;\n", ["SELECT 1"])
# ---- DML on spend via CTE / USING / RETURNING / MERGE / TRUNCATE
add("H33", "DML on spend", "BEGIN ATOMIC with a data-modifying CTE that deletes spend", f"CREATE OR REPLACE FUNCTION h33() RETURNS bigint LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC WITH d AS (DELETE FROM spend RETURNING 1) SELECT count(*) FROM d; END;\n", CALL("h33"))
add("H34", "DML on spend", "BEGIN ATOMIC DELETE ... USING spend_month", f"CREATE OR REPLACE FUNCTION h34() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC DELETE FROM spend USING spend_month m WHERE m.agent_id = spend.agent_id; END;\n", CALL("h34"))
add("H35", "DML on spend", "BEGIN ATOMIC UPDATE ... FROM ... RETURNING (lowers usd)", f"CREATE OR REPLACE FUNCTION h35() RETURNS TABLE (u numeric) LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE spend SET usd = 0 FROM spend_month m WHERE m.agent_id = spend.agent_id RETURNING spend.usd; END;\n", CALL("h35"))
add("H36", "DML on spend", "BEGIN ATOMIC INSERT ... ON CONFLICT DO UPDATE SET usd = 0", f"CREATE OR REPLACE FUNCTION h36() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC INSERT INTO spend (agent_id, day, usd) VALUES ('seed', DATE '2026-11-16', 0) ON CONFLICT (agent_id, day) DO UPDATE SET usd = 0; END;\n", CALL("h36"))
add("H37", "DML on spend", "MERGE ... WHEN MATCHED THEN DELETE in plpgsql definer", pl("h37", "MERGE INTO public.spend s USING public.spend_month m ON m.agent_id = s.agent_id WHEN MATCHED THEN DELETE;"), CALL("h37"))
add("H38", "DML on spend", "TRUNCATE ONLY in plpgsql definer", pl("h38", "TRUNCATE ONLY public.spend;"), CALL("h38"))
add("H39", "DML on spend", "TRUNCATE TABLE ... spend_month, spend CASCADE in BEGIN ATOMIC is illegal; plpgsql form", pl("h39", "TRUNCATE TABLE public.spend_month, public.spend CASCADE;"), CALL("h39"))
add("H40", "DML on spend", "WITH u AS (UPDATE ... RETURNING) inside EXECUTE in plpgsql definer", pl("h40", "EXECUTE 'WITH u AS (UPDATE public.spend SET usd = 0 RETURNING 1) SELECT count(*) FROM u';"), CALL("h40"))
# ---- DROP/ALTER/DISABLE TRIGGER
add("H41", "trigger", "ALTER TABLE spend DISABLE TRIGGER spend_keep_keys", "ALTER TABLE spend DISABLE TRIGGER spend_keep_keys;\n", ["SELECT 1"])
add("H42", "trigger", "ALTER TABLE spend DISABLE TRIGGER USER / ALL", "ALTER TABLE spend_month DISABLE TRIGGER USER;\n", ["SELECT 1"])
add("H43", "trigger", "DROP TRIGGER without IF EXISTS", "DROP TRIGGER spend_log_decrease ON spend;\n", ["SELECT 1"])
add("H44", "trigger", "DROP TRIGGER IF EXISTS of a pinned trigger, never re-created", "DROP TRIGGER IF EXISTS spend_log_decrease ON spend;\n", ["SELECT 1"])
add("H45", "trigger", "ALTER TABLE ... ENABLE REPLICA TRIGGER spend_keep_keys (it then does not fire in a normal session)", "ALTER TABLE spend ENABLE REPLICA TRIGGER spend_keep_keys;\n", ["SELECT 1"])
add("H46", "trigger", "compound ALTER: ADD CONSTRAINT then DISABLE TRIGGER in one statement", "ALTER TABLE spend ADD CONSTRAINT h46_ok CHECK (usd >= 0), DISABLE TRIGGER ALL;\n", ["SELECT 1"])
add("H47", "trigger", "ALTER TABLE spend ADD COLUMN, ALTER COLUMN usd SET DEFAULT / DROP NOT NULL", "ALTER TABLE spend ADD COLUMN h47 int, ALTER COLUMN usd DROP NOT NULL;\n", ["SELECT 1"])
add("H48", "trigger", "ALTER TABLE ONLY public.spend (qualified) DROP CONSTRAINT", "ALTER TABLE ONLY public.spend DROP CONSTRAINT spend_guarded_ok;\n", ["SELECT 1"])
add("H49", "trigger", "new trigger on spend that runs a definer function (AFTER UPDATE) set up as a pinned-name trigger lookalike", pl("h49_t", "RETURN NULL;", "trigger") + "CREATE TRIGGER spend_keep_keys_x AFTER UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION h49_t();\n", ["SELECT 1"])
# ---- CREATE VIEW / POLICY / RULE
add("H50", "view/policy/rule", "CREATE RULE ... DO INSTEAD NOTHING on spend UPDATE", "CREATE RULE h50 AS ON UPDATE TO spend DO INSTEAD NOTHING;\n", ["SELECT * FROM spend_settle('seed', '2026-11-16', 0, 0)"])
add("H51", "view/policy/rule", "CREATE RULE ... DO ALSO UPDATE spend_month SET usd = 0", "CREATE RULE h51 AS ON INSERT TO spend DO ALSO UPDATE spend_month SET usd = 0;\n", ["SELECT * FROM spend_reserve('seed', '2026-11-16', 1)"])
add("H52", "view/policy/rule", "CREATE VIEW over a table the runtime cannot read, then GRANT SELECT to rt17", "CREATE VIEW h52 AS SELECT v FROM secret_t; GRANT SELECT ON h52 TO rt17;\n", ["SELECT * FROM h52"])
add("H53", "view/policy/rule", "ENABLE ROW LEVEL SECURITY + CREATE POLICY USING (false) on spend", "ALTER TABLE spend ENABLE ROW LEVEL SECURITY; CREATE POLICY h53 ON spend USING (false);\n", ["SELECT * FROM spend_settle('seed', '2026-11-16', 0, 0)"])
add("H54", "view/policy/rule", "CREATE MATERIALIZED VIEW / CREATE TABLE AS shadow of spend", "CREATE TABLE spend_shadow AS SELECT * FROM spend;\n", ["SELECT 1"])
# ---- SET ROLE / set_config / authorization
add("H55", "role/set_config", "top-level SET ROLE rt17 (file continues as another role)", "SET ROLE rt17;\n", ["SELECT 1"])
add("H56", "role/set_config", "SET SESSION AUTHORIZATION rt17 / RESET ROLE", "SET SESSION AUTHORIZATION rt17;\nRESET ROLE;\n", ["SELECT 1"])
add("H57", "role/set_config", "SELECT set_config('role','op17',false) at file level", "SELECT set_config('role', 'rt17', false);\n", ["SELECT 1"])
add("H58", "role/set_config", "SET LOCAL \"ROLE\" quoted upper", "SET LOCAL \"ROLE\" = rt17;\n", ["SELECT 1"])
add("H59", "role/set_config", "GRANT migr17-owned function EXECUTE with grant option to rt17", "GRANT EXECUTE ON FUNCTION kill_switch_release() TO rt17 WITH GRANT OPTION;\n", ["SELECT kill_switch_release()"])
add("H60", "role/set_config", "GRANT op17 TO rt17 (role membership)", "GRANT op17 TO rt17;\n", ["SELECT kill_switch_release()"])
# ---- unicode look-alikes / zero width in names
add("H61", "unicode", "function name spend_reserve with Greek nu (U+03BD) in place of v, evil body", f"CREATE OR REPLACE FUNCTION \"spend_reser{GREEK_NU}e\"(p_agent text, p_day date, p_worst numeric) RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS $f$ BEGIN DELETE FROM public.spend; END $f$;\n", [f"SELECT \"spend_reser{GREEK_NU}e\"('a', '2026-11-16', 1)"])
add("H62", "unicode", "unquoted function name with a zero-width space inside (spend_res<ZWSP>erve)", f"CREATE OR REPLACE FUNCTION spend_res{ZW}erve(p_agent text, p_day date, p_worst numeric) RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS $f$ BEGIN DELETE FROM public.spend; END $f$;\n", [f"SELECT spend_res{ZW}erve('a', '2026-11-16', 1)"])
add("H63", "unicode", "NBSP (U+00A0) between SECURITY and DEFINER", f"CREATE OR REPLACE FUNCTION h63() RETURNS void LANGUAGE sql SECURITY{NB}DEFINER {SP} AS $f$ DELETE FROM public.spend $f$;\n", CALL("h63"))
add("H64", "unicode", "zero-width joiner inside the word DEFINER (DEF<ZWJ>INER)", f"CREATE OR REPLACE FUNCTION h64() RETURNS void LANGUAGE sql SECURITY DEF‍INER {SP} AS $f$ DELETE FROM public.spend $f$;\n", CALL("h64"))
add("H65", "unicode", "full-width quotation / semicolon characters around a statement", "CREATE OR REPLACE FUNCTION h65() RETURNS void LANGUAGE sql SECURITY DEFINER " + SP + " AS $f$ DELETE FROM public.spend $f$；\n", CALL("h65"))
add("H66", "unicode", "table name lookalike: Cyrillic a in spend_month (spend_month with U+0430) used as a shadow target", f"CREATE TABLE \"spend_month{CYR_A}\" (x int);\n", ["SELECT 1"])
# ---- the guard does not pin CHECK text: weakened constraints, and a CHECK function call
add("H67", "weakened check", "agent-id CHECK replaced by CHECK (true) (same constraint name, ADD form)", None, ["SELECT * FROM spend_reserve('a b', '2026-11-16', 1)"], replace=("CHECK (agent_id ~ '^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$');\nALTER TABLE spend ADD CONSTRAINT spend_day_window", "CHECK (true);\nALTER TABLE spend ADD CONSTRAINT spend_day_window"))
add("H68", "weakened check", "ceiling 1e12 changed to 1e30 in spend_guarded_ok", None, ["SELECT * FROM spend_reserve('big', '2026-11-16', 1e20)"], replace=("CHECK (usd >= 0 AND usd < 1000000000000::numeric);\nALTER TABLE spend ADD CONSTRAINT spend_agent_len", "CHECK (usd < 1e30::numeric);\nALTER TABLE spend ADD CONSTRAINT spend_agent_len"))
add("H69", "weakened check", "CHECK that calls a user function (volatile helper) in the expression", "CREATE FUNCTION h69_f(numeric) RETURNS boolean LANGUAGE sql AS $f$ SELECT true $f$; ALTER TABLE spend ADD CONSTRAINT h69 CHECK (h69_f(usd));\n", ["SELECT 1"])
# ---- DB-2 file mutations (target db2)
add("H70", "DB-2 file", "spend_log_decrease body gets an extra DELETE of the log through EXECUTE", None, ["SELECT 1"], target="db2", replace=("  IF TG_TABLE_NAME = 'spend' THEN\n    EXECUTE format('INSERT INTO %I.spend_decrease_log", "  EXECUTE 'DELETE FROM public.spend_decrease_log';\n  IF TG_TABLE_NAME = 'spend' THEN\n    EXECUTE format('INSERT INTO %I.spend_decrease_log"))
add("H71", "DB-2 file", "kill_switch_log_change handler swallows errors also when the switch goes OFF (no RAISE)", None, ["SELECT 1"], target="db2", replace=("    IF NEW.\"on\" THEN\n      RAISE WARNING 'kill_switch_log not written (%): the switch ON is kept', SQLSTATE;\n    ELSE\n      RAISE;\n    END IF;\n  END;\n  RETURN NULL;\nEND $f$;\nREVOKE ALL ON FUNCTION kill_switch_log_change()", "    NULL;\n  END;\n  RETURN NULL;\nEND $f$;\nREVOKE ALL ON FUNCTION kill_switch_log_change()"))
add("H72", "DB-2 file", "the append-only trigger on the log is disabled inside the file", "ALTER TABLE spend_decrease_log DISABLE TRIGGER spend_decrease_log_append_only;\n", ["SELECT 1"], target="db2", replace=("__APPEND__", ""))
add("H73", "DB-2 file", "WHEN condition of the decrease trigger widened to never fire (NEW.usd < OLD.usd removed)", None, ["SELECT 1"], target="db2", replace=("WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd < OLD.usd OR NEW.usd >= 'Infinity'::numeric))\n  EXECUTE FUNCTION spend_log_decrease();\nCREATE TRIGGER spend_month_log_decrease", "WHEN (false)\n  EXECUTE FUNCTION spend_log_decrease();\nCREATE TRIGGER spend_month_log_decrease"))
add("H74", "DB-2 file", "spend_log_decrease made SECURITY INVOKER-looking: attribute order moved after the body (plpgsql, search_path first)", None, ["SELECT 1"], target="db2", replace=("RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER\nSET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF TG_TABLE_NAME = 'spend' THEN\n    EXECUTE format('INSERT INTO %I.spend_decrease_log", "RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER\nSET search_path = pg_catalog, pg_temp, public AS $f$\nBEGIN\n  IF TG_TABLE_NAME = 'spend' THEN\n    EXECUTE format('INSERT INTO %I.spend_decrease_log"))

SMOKE = bool(os.environ.get('HV_SMOKE'))
if SMOKE: F = F[:6] + [x for x in F if x[0] in ('H23', 'H72')]
_rep67 = ("CHECK (agent_id ~ '^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$');\nALTER TABLE spend ADD CONSTRAINT spend_day_window", "CHECK (true);\nALTER TABLE spend ADD CONSTRAINT spend_day_window")
def both_tables(t):
    t = t.replace(_rep67[0], _rep67[1], 1)
    return t.replace("ADD CONSTRAINT spend_month_agent_len CHECK (agent_id ~ '^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$');", "ADD CONSTRAINT spend_month_agent_len CHECK (true);", 1)
add("H75", "weakened check", "agent-id CHECK replaced by CHECK (true) on BOTH spend and spend_month (so a reserve with a space in the id works)", None, ["SELECT * FROM spend_reserve('a b', '2026-11-16', 1)", "SELECT * FROM spend_reserve(E'a\\nb', '2026-11-16', 1)"], replace=("__BOTH_AGENT__", ""))
add("H76", "weakened check", "ceiling 1e12 raised to 1e30 on BOTH tables (a reserve of 1e20 is accepted)", None, ["SELECT * FROM spend_reserve('big', '2026-11-16', 1e20)"], replace=("__BOTH_CEIL__", ""))
add("H77", "DB-2 file", "audit_log_append_only made a no-op (RETURN NULL) so the logs can be edited", None, ["SELECT 1"], target="db2", replace=("  RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = '42501';\nEND $f$;", "  RETURN OLD;\nEND $f$;"))
add("H78", "pinned semantic", "kill_switch_engage turned around: sets \"on\" = false (same kinds, same table, same signature)", None, ["SELECT kill_switch_engage()"], replace=("ON CONFLICT (id) DO UPDATE SET \"on\" = true,", "ON CONFLICT (id) DO UPDATE SET \"on\" = false,"))
for cid, fam, what, extra, probes, target, rep in F:
    base = T3 if target == "db3" else T2
    if rep is not None:
        old, new = rep
        if old == "__APPEND__": text = base + "\n" + extra
        elif old == "__BOTH_AGENT__": text = both_tables(base)
        elif old == "__BOTH_CEIL__": text = base.replace("usd < 1000000000000::numeric", "usd < 1e30::numeric")
        else:
            assert old in base, f"{cid}: replace anchor not found"
            text = base.replace(old, new, 1)
    else:
        text = base + "\n" + extra
    try: run_file_case(cid, fam, what, text, probes, target)
    except Exception as e:
        rows.append((cid, fam, what, "?", f"HARNESS ERROR {type(e).__name__}", str(e)[:100], "", "")); print(cid, "HARNESS ERROR", type(e).__name__, str(e)[:100], flush=True)

# ---------------------------------------------------------------- Part D: hostile data against the GENUINE v20 functions
dbd = "d_genuine"; ok, _ = apply_files(dbd, T2, T3); assert ok == "ok", ok
mgd = psycopg.connect(dsn("migr17", dbd), autocommit=True); rtd = psycopg.connect(dsn("rt17", dbd), autocommit=True)
def left(agent):
    if agent is not None and '\x00' in agent: return 'no row can exist (NUL cannot be stored in text)'
    a = mgd.execute("SELECT count(*), coalesce(sum(usd),0), coalesce(sum(open_usd),0) FROM spend WHERE agent_id = %s", (agent,)).fetchone()
    b = mgd.execute("SELECT count(*), coalesce(sum(usd),0), coalesce(sum(open_usd),0) FROM spend_month WHERE agent_id = %s", (agent,)).fetchone()
    return f"day rows={a[0]} usd={a[1]} open={a[2]}; month rows={b[0]} usd={b[1]} open={b[2]}"
def call(q, args):
    try:
        r = rtd.execute(q, args)
        try: res = r.fetchall()
        except psycopg.ProgrammingError: res = None
        return "ok " + (repr([[str(x) for x in row] for row in res])[:60] if res is not None else "")
    except psycopg.Error as e: return f"error {e.sqlstate}"
    except (ValueError, UnicodeError) as e: return f"CLIENT-REFUSED {type(e).__name__} (never reached the server)"
def dcase(cid, fam, what, agent, q, args, note=""):
    r = call(q, args); l = left(agent) if agent is not None else ""
    rows.append((cid, fam, what, "n/a (genuine file: " + gv + ")", r, "", l, note)); print(f"{cid} | {what[:70]} | {r[:50]} | {l[:70]}", flush=True)
RES, SET = "SELECT * FROM spend_reserve(%s, %s, %s)", "SELECT * FROM spend_settle(%s, %s, %s, %s)"
n = 0
def aid_case(label, a, expect):
    global n
    if SMOKE and n >= 4: return
    n += 1; cid = f"D{n:02d}"
    dcase(cid, "agent id", f"{label} (expected by the file's rule: {expect})", a, RES, (a, D, 1))
aid_case("0 characters ''", "", "refuse")
aid_case("1 character 'a'", "a", "accept")
aid_case("200 characters", "a" * 200, "accept")
aid_case("201 characters", "a" * 201, "refuse")
aid_case("first char '.'", ".abc", "refuse"); aid_case("first char '_'", "_abc", "refuse"); aid_case("first char '-'", "-abc", "refuse")
aid_case("inner space 'a b'", "a b", "refuse"); aid_case("leading space", " ab", "refuse"); aid_case("trailing space", "ab ", "refuse")
aid_case("trailing newline", "ab\n", "refuse"); aid_case("inner tab", "a\tb", "refuse"); aid_case("carriage return", "a\rb", "refuse")
aid_case("single quote", "a'b", "refuse"); aid_case("double quote", 'a"b', "refuse"); aid_case("backslash", "a\\b", "refuse"); aid_case("percent", "a%b", "refuse")
aid_case("dollar", "a$b", "refuse"); aid_case("semicolon", "a;b", "refuse"); aid_case("star", "a*b", "refuse"); aid_case("equals", "a=b", "refuse"); aid_case("DEL 0x7f", "a\x7fb", "refuse")
aid_case("zero-width space inside", "a​b", "refuse"); aid_case("RTL override U+202E", "a‮b", "refuse"); aid_case("BOM U+FEFF at end", "ab﻿", "refuse")
aid_case("Cyrillic a (U+0430) first", "аbc", "refuse"); aid_case("full-width a (U+FF41)", "ａbc", "refuse"); aid_case("NFD e + combining acute", "café", "refuse"); aid_case("NFC e-acute", "café", "refuse")
aid_case("emoji", "a\U0001F600", "refuse"); aid_case("NUL byte (client side)", "a\x00b", "refuse")
aid_case("allowed set all together", "aZ09._:@/+-x", "accept"); aid_case("case twin 'A' vs 'a' (stated: separate budgets)", "A", "accept")
aid_case("NULL agent id", None, "no row")
n0 = n
# amounts
def amt(label, v, expect, agent=None):
    global n
    if SMOKE and n >= 6: return
    n += 1; a = agent or f"amt{n}"
    dcase(f"D{n:02d}", "amount", f"reserve {label} (expected: {expect})", a, RES, (a, D, v))
amt("0", 0, "no row"); amt("-1", -1, "no row"); amt("NULL", None, "no row"); amt("0.0000001", "0.0000001", "accept"); amt("999999999999.99", "999999999999.99", "accept")
amt("1e12 exactly", "1000000000000", "23514"); amt("1e12 - 0.0000001 (boundary under)", "999999999999.9999999", "accept"); amt("1e20", "100000000000000000000", "23514"); amt("NaN", "NaN", "refuse"); amt("Infinity", "Infinity", "refuse")
amt("-Infinity", "-Infinity", "no row"); amt("1e131072 (numeric max digits)", "1" + "0" * 131000, "23514 or 22003")
# day boundaries
for label, dv in (("2019-12-31", "2019-12-31"), ("2020-01-01", "2020-01-01"), ("2099-12-31", "2099-12-31"), ("2100-01-01", "2100-01-01"), ("infinity", "infinity"), ("NULL", None)):
    n += 1; a = f"day{n}"; dcase(f"D{n:02d}", "day", f"reserve with day {label}", a, RES, (a, dv, 1))
# settle variations
def seedres(a, v=10): rtd.execute(RES, (a, D, v)).fetchall()
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle worst=10 actual=0 after reserve 10 (give back)", a, SET, (a, D, 10, 0))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle worst=11 (more than open 10)", a, SET, (a, D, 11, 0))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle actual NULL", a, SET, (a, D, 10, None))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle worst NULL", a, SET, (a, D, None, 5))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle worst negative -5, actual 0 (try to raise open)", a, SET, (a, D, -5, 0))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle actual negative -1", a, SET, (a, D, 10, -1))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle actual 1e12 (above ceiling)", a, SET, (a, D, 10, "1000000000000"))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle actual NaN", a, SET, (a, D, 10, "NaN"))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle actual 50 above worst 10 (stated safe direction)", a, SET, (a, D, 10, 50))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle day NULL", a, SET, (a, None, 10, 0))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle for another day (no row for that day)", a, SET, (a, date(2026, 11, 17), 10, 0))
n += 1; a = f"st{n}"; seedres(a); dcase(f"D{n:02d}", "settle", "settle twice: second give-back of the same 10", a, SET, (a, D, 10, 0)); r2 = call(SET, (a, D, 10, 0)); rows.append((f"D{n:02d}b", "settle", "(second call of the line above)", "n/a", r2, "", left(a), "")); print(f"D{n:02d}b second give-back {r2} {left(a)}", flush=True)
n += 1; a = f"nomonth{n}"; mgd.execute("INSERT INTO spend (agent_id, day, usd, open_usd) VALUES (%s, %s, 7, 7)", (a, D)); dcase(f"D{n:02d}", "settle", "settle where the month row is MISSING (day row only, open 7)", a, SET, (a, D, 7, 0))
n += 1; a = f"noday{n}"; mgd.execute("INSERT INTO spend_month (agent_id, month, usd, open_usd) VALUES (%s, %s, 7, 7)", (a, date(2026, 11, 1))); dcase(f"D{n:02d}", "settle", "settle where the DAY row is MISSING (month row only, open 7)", a, SET, (a, D, 7, 0))
n += 1; a = f"nomonth_reserve{n}"; mgd.execute("INSERT INTO spend (agent_id, day, usd, open_usd) VALUES (%s, %s, 3, 3)", (a, D)); dcase(f"D{n:02d}", "reserve", "reserve 1 when only the day row exists (month row created?)", a, RES, (a, D, 1))
# open reservation at cutover (separate database: DB-2 only, an old-style row, then DB-3 applied)
dbc = "d_cutover"; ok2, tmpc = apply_files(dbc, T2, None); assert ok2 == "ok", ok2
mgc = psycopg.connect(dsn("migr17", dbc), autocommit=True)
mgc.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('cut', %s, 5)", (D,)); mgc.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('cut', %s, 5)", (date(2026, 11, 1),))
(tmpc / "0007_guard.sql").write_text(T3); m.GRANTS.update(ORIG); m.migrate(dsn("migr17", dbc), runtime_role="rt17"); m.GRANTS.update(SEL); m.migrate(dsn("migr17", dbc), runtime_role="rt17")
grant_fns(dbc); rtc = psycopg.connect(dsn("rt17", dbc), autocommit=True)
try: r = rtc.execute(SET, ("cut", D, 5, 0)).fetchall(); res = "ok " + repr([[str(x) for x in row] for row in r])
except psycopg.Error as e: res = f"error {e.sqlstate}"
lc = mgc.execute("SELECT usd, open_usd FROM spend WHERE agent_id='cut'").fetchone(); lm = mgc.execute("SELECT usd, open_usd FROM spend_month WHERE agent_id='cut'").fetchone()
n += 1; rows.append((f"D{n:02d}", "cutover", "reservation of 5 open at the moment DB-3 is applied (old-style row), then give-back 5 -> 0", "n/a", res, "", f"day usd/open={tuple(map(str, lc))} month usd/open={tuple(map(str, lm))}", "")); print(f"D{n:02d} cutover settle {res} day={lc} month={lm}", flush=True)
# apply DB-3 over a row that BREAKS the agent rule (pre-check says the file must refuse at apply time)
dbc2 = "d_cutover2"; ok3, tmpc2 = apply_files(dbc2, T2, None); mgc2 = psycopg.connect(dsn("migr17", dbc2), autocommit=True)
mgc2.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('bad agent', %s, 5)", (D,)); (tmpc2 / "0007_guard.sql").write_text(T3); m.GRANTS.update(ORIG)
try: m.migrate(dsn("migr17", dbc2), runtime_role="rt17"); res = "APPLIED (file did not refuse an old bad row)"
except psycopg.Error as e: res = f"refused {e.sqlstate}"
n += 1; rows.append((f"D{n:02d}", "cutover", "DB-3 applied over an old row whose agent id has a space", "n/a", res, "", f"spend rows={mgc2.execute('SELECT count(*) FROM spend').fetchone()[0]}; functions installed={mgc2.execute(chr(83)+'ELECT count(*) FROM pg_proc WHERE proname = '+chr(39)+'spend_reserve'+chr(39)).fetchone()[0]}", "")); print(f"D{n:02d} cutover bad row {res}", flush=True)
# hostile ledger of the amounts: the totals must equal the sum of what was reserved minus what was given back (conservation check on the genuine DB)
cons = mgd.execute("SELECT count(*) FROM spend WHERE usd < 0 OR open_usd < 0 OR open_usd > usd").fetchone()[0]
n += 1; rows.append((f"D{n:02d}", "invariant", "after every case above: rows with usd<0 or open<0 or open>usd in spend (day) table", "n/a", f"{cons} rows", "", "", "")); print(f"D{n:02d} invariant violations {cons}", flush=True)
cons2 = mgd.execute("SELECT count(*) FROM spend_month WHERE usd < 0 OR open_usd < 0 OR open_usd > usd").fetchone()[0]
rows.append((f"D{n:02d}b", "invariant", "same for spend_month", "n/a", f"{cons2} rows", "", "", "")); print(f"invariant month {cons2}", flush=True)

# ---------------------------------------------------------------- Part R: things a runtime login tries on its own (genuine v20 DB)
dbr = "r_genuine"; ok, _ = apply_files(dbr, T2, T3); assert ok == "ok", ok
mgr = psycopg.connect(dsn("migr17", dbr), autocommit=True); seed(mgr)
def rcase(cid, what, stmts, check_sql=None):
    if SMOKE and cid > 'R03': return
    c = psycopg.connect(dsn("rt17", dbr), autocommit=True); outs = []
    for s in stmts:
        try:
            r = c.execute(s)
            try: res = r.fetchall()
            except psycopg.ProgrammingError: res = None
            outs.append("ok" + (":" + repr(res)[:50] if res is not None else ""))
        except psycopg.Error as e: outs.append(str(e.sqlstate))
    extra = ""
    if check_sql: extra = repr(mgr.execute(check_sql).fetchall())[:120]
    d = data(mgr)
    rows.append((cid, "runtime login", what, "n/a", " ; ".join(outs)[:150], extra, f"spend={[(a, str(u)) for a, _, u, _ in d[0]]} killsw_on={[x[0] for x in d[2]]}", "")); print(f"{cid} | {what[:70]} | {' ; '.join(outs)[:90]}", flush=True); c.close()
rcase("R01", "CREATE TEMP TABLE spend, then spend_reserve (does the definer write the real table?)", ["CREATE TEMP TABLE spend (agent_id text, day date, usd numeric, open_usd numeric)", "SELECT * FROM spend_reserve('tmpa', '2026-11-16', 1)", "SELECT count(*) FROM pg_temp.spend"], "SELECT count(*) FROM public.spend WHERE agent_id = 'tmpa'")
rcase("R02", "CREATE TEMP TABLE spend_month + kill_switch, then kill_switch_engage", ["CREATE TEMP TABLE spend_month (x int)", "CREATE TEMP TABLE kill_switch (x int)", "SELECT kill_switch_engage()"], "SELECT count(*) FROM public.kill_switch")
rcase("R03", "CREATE TEMP TABLE spend with a trigger (own temp table) and call spend_reserve", ["CREATE TEMP TABLE spend (agent_id text)", "CREATE FUNCTION pg_temp.tf() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN RETURN NEW; END $f$", "CREATE TRIGGER tt BEFORE INSERT ON pg_temp.spend FOR EACH ROW EXECUTE FUNCTION pg_temp.tf()", "SELECT * FROM spend_reserve('tmpb', '2026-11-16', 1)"], "SELECT count(*) FROM public.spend WHERE agent_id = 'tmpb'")
rcase("R04", "CREATE TRIGGER on the real spend table", ["CREATE FUNCTION pg_temp.tf() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN RETURN NEW; END $f$", "CREATE TRIGGER evil AFTER INSERT ON public.spend FOR EACH ROW EXECUTE FUNCTION pg_temp.tf()"])
rcase("R05", "SET search_path = pg_temp, public then call the functions", ["SET search_path = pg_temp, public", "SELECT * FROM spend_reserve('sp1', '2026-11-16', 1)"], "SELECT count(*) FROM public.spend WHERE agent_id = 'sp1'")
rcase("R06", "CREATE TEMP VIEW spend then reserve", ["CREATE TEMP VIEW spend AS SELECT 1 AS x", "SELECT * FROM spend_reserve('vw1', '2026-11-16', 1)"], "SELECT count(*) FROM public.spend WHERE agent_id = 'vw1'")
rcase("R07", "CREATE FUNCTION in public (shadow spend_reserve)", ["CREATE FUNCTION public.spend_reserve(text, date, numeric) RETURNS void LANGUAGE sql AS 'SELECT 1'"])
rcase("R08", "CREATE FUNCTION pg_temp.spend_reserve then call unqualified", ["CREATE FUNCTION pg_temp.spend_reserve(text, date, numeric) RETURNS void LANGUAGE sql AS 'SELECT 1'", "SELECT * FROM spend_reserve('tf1', '2026-11-16', 1)"], "SELECT count(*) FROM public.spend WHERE agent_id = 'tf1'")
rcase("R09", "SET ROLE migr17 / set_config role / SET SESSION AUTHORIZATION", ["SET ROLE migr17", "SELECT set_config('role', 'migr17', false)", "SET SESSION AUTHORIZATION migr17"])
rcase("R10", "COPY spend TO PROGRAM / COPY FROM PROGRAM", ["COPY spend TO PROGRAM 'cat'", "COPY spend FROM PROGRAM 'echo x'"])
rcase("R11", "ALTER TABLE spend DISABLE TRIGGER ALL; TRUNCATE spend; DROP TABLE spend", ["ALTER TABLE spend DISABLE TRIGGER ALL", "TRUNCATE spend", "DROP TABLE spend"])
rcase("R12", "DROP FUNCTION spend_settle; CREATE OR REPLACE spend_reserve; ALTER FUNCTION ... SET search_path", ["DROP FUNCTION spend_settle(text,date,numeric,numeric)", "CREATE OR REPLACE FUNCTION spend_reserve(text,date,numeric) RETURNS void LANGUAGE sql AS 'SELECT 1'", "ALTER FUNCTION spend_reserve(text,date,numeric) SET search_path = public"])
rcase("R13", "set_config('session_replication_role','replica'); LOCK TABLE spend ACCESS EXCLUSIVE", ["SELECT set_config('session_replication_role', 'replica', false)", "LOCK TABLE spend IN ACCESS EXCLUSIVE MODE"])
rcase("R14", "CREATE RULE / POLICY / VIEW on spend", ["CREATE RULE r1 AS ON UPDATE TO spend DO INSTEAD NOTHING", "CREATE POLICY p1 ON spend USING (true)", "CREATE VIEW public.v1 AS SELECT * FROM spend"])
rcase("R15", "kill_switch_release as runtime; direct UPDATE kill_switch; direct UPDATE/DELETE spend", ["SELECT kill_switch_release()", "UPDATE kill_switch SET \"on\" = false", "UPDATE spend SET usd = 0", "DELETE FROM spend"], 'SELECT "on" FROM kill_switch')
rcase("R16", "settle ANOTHER agent's open reservation (stated limit (b) of the file)", ["SELECT * FROM spend_reserve('victim', '2026-11-16', 40)", "SELECT * FROM spend_settle('victim', '2026-11-16', 40, 0)"], "SELECT usd, open_usd FROM spend WHERE agent_id = 'victim'")
rcase("R17", "reserve to the ceiling then settle at 0 (stated limit (a) of the file)", ["SELECT * FROM spend_reserve('gamer', '2026-11-16', 999999999999)", "SELECT * FROM spend_settle('gamer', '2026-11-16', 999999999999, 0)"], "SELECT usd, open_usd FROM spend WHERE agent_id = 'gamer'")
rcase("R18", "create a temp table named spend_decrease_log / audit_entries then lower a total (settle) ", ["CREATE TEMP TABLE spend_decrease_log (x int)", "SELECT * FROM spend_reserve('lg', '2026-11-16', 5)", "SELECT * FROM spend_settle('lg', '2026-11-16', 5, 0)"], "SELECT count(*) FROM public.spend_decrease_log WHERE agent_id = 'lg'")
rcase("R19", "SET LOCAL statement_timeout / lock_timeout then reserve inside a transaction block, ROLLBACK after reserve", ["BEGIN", "SELECT * FROM spend_reserve('rb', '2026-11-16', 9)", "ROLLBACK"], "SELECT count(*) FROM public.spend WHERE agent_id = 'rb'")
rcase("R20", "CREATE TABLE in public, CREATE SCHEMA, CREATE EXTENSION", ["CREATE TABLE public.t_rt (x int)", "CREATE SCHEMA s_rt", "CREATE EXTENSION IF NOT EXISTS dblink"])

rcase("R21", "LOCK TABLE spend ACCESS EXCLUSIVE inside a transaction (R13 hit 25P01 before any privilege check)", ["BEGIN", "LOCK TABLE spend IN ACCESS EXCLUSIVE MODE", "ROLLBACK"])
rcase("R22", "SELECT ... FOR UPDATE on spend; LOCK ROW EXCLUSIVE; inside a transaction", ["BEGIN", "SELECT * FROM spend FOR UPDATE", "ROLLBACK", "BEGIN", "LOCK TABLE spend IN ROW EXCLUSIVE MODE", "ROLLBACK"])
# ---------------------------------------------------------------- output
cand = [r for r in rows if r[7] == "BYPASS-CANDIDATE"]
json.dump(rows, open(os.environ.get("HV_ROWS_JSON", "/dev/null"), "w"))
nF = sum(1 for r in rows if r[0].startswith("H")); nD = sum(1 for r in rows if r[0].startswith("D")); nR = sum(1 for r in rows if r[0].startswith("R"))
print(f"SUMMARY file spellings={nF} data cases={nD} runtime-login cases={nR} bypass candidates={len(cand)}: {[r[0] for r in cand]}")
