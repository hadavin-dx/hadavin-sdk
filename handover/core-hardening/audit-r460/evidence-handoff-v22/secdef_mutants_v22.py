"""Mutants for the SECURITY DEFINER guards (v16 to v22; v22 is the guard under test (variables g22, A22, p22; gQ is the v21 guard, gP the v20 guard), the v21 column shows which new v22 mutants v21 misses). A mutant is a SQL text that Postgres accepts and that leaves a routine or right the guard must refuse.
Prints for each: whether v16, v17 and v18 flag it; a check PASSES when v18 flags it (controls: v18 must NOT flag). Needs TWO arguments:
  python secdef_mutants_v19.py <held-sql folder> <product migrations folder>      (a missing argument stops the run with exit 2, v17 silently ran 25 of 30)
Also runs the 25 + 2 spellings of the v17 independent evidence runner (spellings.json, spellings2.json) and the parser tests P1, P2."""
import sys, glob, os, json
if len(sys.argv) != 3 or not all(os.path.isdir(a) for a in sys.argv[1:]):
    print("usage: secdef_mutants_v19.py <held-sql folder> <product migrations folder> (both must be existing folders)"); sys.exit(2)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import secdef_guard_v16 as g16, secdef_guard_v17 as g17, secdef_guard_v18 as g18, secdef_guard_v19 as g19, secdef_guard_v22 as g22, secdef_guard_v20 as gP, secdef_guard_v21 as gQ
from secdef_guard_v22 import PIN_ANY
import allow_v22 as A22, allow_v20 as AP, allow_v21 as AQ
from allow_v22 import ALLOWED_BY_FILE, ATOMIC_TABLES_BY_FILE, EXTRA_BY_FILE
V17_ALLOWED = {"spend_log_decrease", "kill_switch_log_change", "spend_reserve", "spend_settle", "kill_switch_engage", "kill_switch_release"}
DB3 = "spend_guarded_writes.sql"; DB2 = "spend_decrease_log.sql"
RES = "spend_reserve(text,date,numeric)"; SET = "spend_settle(text,date,numeric,numeric)"; ENG = "kill_switch_engage()"; REL = "kill_switch_release()"
SP = "SET search_path = pg_catalog, pg_temp"
def rev(f, args=""): return f"REVOKE ALL ON FUNCTION {f}({args}) FROM PUBLIC;\n"
def fn(name="evil", args="", hdr=f"LANGUAGE sql SECURITY DEFINER {SP}", body="AS $f$ SELECT 1 $f$"): return f"CREATE OR REPLACE FUNCTION {name}({args}) RETURNS int {hdr} {body};\n"
RESERVE = f"CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE spend SET usd = usd + p_worst WHERE agent_id = p_agent; END;\n" + rev("spend_reserve", "text, date, numeric")
# (name, file, text, allowed-for-v18, expected: "flag" or "clean")
M = []
OPTS = {}
def add(n, text, allowed=None, file="x.sql", want="flag", opts=None):
    M.append((n, file, text, allowed if allowed is not None else {}, want))
    if opts: OPTS[n] = opts
# ---- the 20 mutants of v17 (S01-S20), kept
add("S01 attributes after the body", "CREATE OR REPLACE FUNCTION evil() RETURNS trigger AS $f$ BEGIN RETURN NULL; END $f$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog;\n" + rev("evil"))
add("S02 single-quoted body", f"CREATE OR REPLACE FUNCTION evil() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER {SP} AS 'BEGIN INSERT INTO t VALUES (1); RETURN NULL; END';\n" + rev("evil"))
add("S03 BEGIN ATOMIC body, function not on the list", f"CREATE OR REPLACE FUNCTION evil() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE t SET a = 1; END;\n" + rev("evil"))
add("S04 schema-qualified name not on the list", fn("public.evil") + rev("evil"))
add("S05 ALTER FUNCTION ... SECURITY DEFINER", "ALTER FUNCTION spend_keep_keys() SECURITY DEFINER;\n")
add("S06 CREATE PROCEDURE ... SECURITY DEFINER", "CREATE PROCEDURE evil() LANGUAGE sql SECURITY DEFINER AS $f$ SELECT 1 $f$;\n")
TRIG = lambda body="BEGIN EXECUTE format('INSERT INTO %I.t VALUES (1)', TG_TABLE_SCHEMA); RETURN NULL; END", hdr=f"LANGUAGE plpgsql SECURITY DEFINER {SP}", f="spend_log_decrease": f"CREATE OR REPLACE FUNCTION {f}() RETURNS trigger {hdr} AS $f$ {body} $f$;\n" + rev(f)
DB2A = {"spend_log_decrease()": "definer"}
add("S07 one %I. hides a bare table statement", TRIG("BEGIN EXECUTE format('INSERT INTO %I.a VALUES (1)', TG_TABLE_SCHEMA); INSERT INTO spend_decrease_log VALUES (1); RETURN NULL; END"), DB2A, DB2)
add("S08 a comment inside the token", TRIG(hdr=f"LANGUAGE plpgsql SECURITY /* c */ DEFINER {SP}", f="evil"))
add("S09 newline and tab inside the token", TRIG(hdr=f"LANGUAGE plpgsql SECURITY\n\tDEFINER {SP}", f="evil"))
add("S10 DO block that creates one", "DO $x$ BEGIN EXECUTE 'CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY DEFINER AS ''SELECT 1'''; END $x$;\n")
add("S11 search_path without pg_temp last", TRIG(hdr="LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_temp, pg_catalog"), DB2A, DB2)
add("S12 search_path names public", TRIG(hdr="LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_catalog, pg_temp"), DB2A, DB2)
add("S13 no search_path at all", TRIG(hdr="LANGUAGE plpgsql SECURITY DEFINER"), DB2A, DB2)
add("S14 no REVOKE from PUBLIC", f"CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER {SP} AS $f$ BEGIN RETURN NULL; END $f$;\n", DB2A, DB2)
add("S15 GRANT EXECUTE to PUBLIC after the REVOKE", TRIG() + "GRANT EXECUTE ON FUNCTION spend_log_decrease() TO PUBLIC;\n", DB2A, DB2)
add("S16 lower-case token, name in a quoted identifier", f"create or replace function \"evil\"() returns int language sql security definer {SP} as $f$ select 1 $f$;\nrevoke all on function evil() from public;\n")
add("S17 token in a function that is not OR REPLACE", f"CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY DEFINER {SP} AS $f$ SELECT 1 $f$;\n" + rev("evil"))
add("S18 EXECUTE of a concatenated string", TRIG("BEGIN EXECUTE 'DELETE FROM ' || TG_TABLE_NAME; RETURN NULL; END"), DB2A, DB2)
add("S19 bare UPDATE ONLY in a dollar body", TRIG("BEGIN UPDATE ONLY spend SET usd = 0; RETURN NULL; END"), DB2A, DB2)
add("S20 DB-3 style body without search_path", "CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS void LANGUAGE sql SECURITY DEFINER BEGIN ATOMIC UPDATE kill_switch SET \"on\" = true; END;\n" + rev("kill_switch_engage"), {ENG: "definer"}, DB3)
# ---- MA1 spelling A: double-quoted names that look like comments
add("A1 name \"a--b\" hides the token on the same line", "CREATE OR REPLACE FUNCTION \"a--b\"() RETURNS int LANGUAGE sql SECURITY DEFINER " + SP + " AS $f$ SELECT 1 $f$;\n")
add("A2 name \"t/*\" opens a comment that hides an ALTER FUNCTION", "CREATE TABLE \"t/*\" (a int);\nALTER FUNCTION spend_reserve(text,date,numeric) SECURITY DEFINER;\nSELECT 1; /* real comment */\n")
add("A3 E'..\\'..' string hides a statement boundary", "SELECT E'\\''; CREATE OR REPLACE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY DEFINER " + SP + " AS $f$ SELECT 1 $f$;\n")
# ---- B: ALTER FUNCTION with no SECURITY token
for n, tail in (("B1 ALTER FUNCTION ... SET search_path = public", "SET search_path = public"), ("B2 ALTER FUNCTION ... RESET search_path", "RESET search_path"), ("B3 ALTER FUNCTION ... OWNER TO the runtime role", "OWNER TO rt17"), ("B4 ALTER ROUTINE ... SET search_path", None)):
    add(n, f"ALTER {'ROUTINE' if tail is None else 'FUNCTION'} spend_reserve(text,date,numeric) {tail or 'SET search_path = public'};\n", {RES: "definer"}, DB3)
add("B5 ALTER FUNCTION ... SECURITY INVOKER (drops the guard on a definer)", "ALTER FUNCTION spend_reserve(text,date,numeric) SECURITY INVOKER;\n", {RES: "definer"}, DB3)
# ---- C: overloads
add("C1 second overload of a listed name, only the real signature revoked", RESERVE + fn("spend_reserve", "p text", body="BEGIN ATOMIC UPDATE spend SET usd = 0; SELECT 1; END").replace("RETURNS int", "RETURNS int"), {RES: "definer"}, DB3)
add("C2 two listed signatures, only one REVOKE", fn("f", "a text") + fn("f", "a int") + rev("f", "text"), {"f(text)": "definer", "f(integer)": "definer"})
add("C3 overload with an alias type (int4 for integer): REVOKE for int does cover it", fn("f", "a int4") + rev("f", "integer"), {"f(integer)": "definer"}, want="clean")
# ---- D: grants
add("D1 GRANT of a second function in a list", RESERVE + "GRANT EXECUTE ON FUNCTION spend_reserve(text,date,numeric), kill_switch_release() TO rt17;\n", {RES: "definer"}, DB3)
add("D2 GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA", "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO rt17;\n")
add("D3 ALTER DEFAULT PRIVILEGES ... GRANT EXECUTE ON FUNCTIONS (survives the later REVOKE)", "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO rt17;\n")
add("D4 release granted to a non-operator role", "GRANT EXECUTE ON FUNCTION kill_switch_release() TO rt17;\n", {REL: "definer"}, DB3)
add("D5 role membership: GRANT operator_role TO rt17", "GRANT operator_role TO rt17;\n")
# ---- E: owner / identity
add("E1 SET ROLE before the CREATE", "SET ROLE postgres;\n" + RESERVE, {RES: "definer"}, DB3)
add("E2 SET SESSION AUTHORIZATION", "SET SESSION AUTHORIZATION postgres;\n")
add("E3 SET LOCAL ROLE", "SET LOCAL ROLE postgres;\n")
add("E4 RESET ROLE / RESET ALL", "RESET ALL;\n")
add("E5 ALTER TABLE ... OWNER TO", "ALTER TABLE spend OWNER TO rt17;\n")
add("E6 function attribute SET role = postgres", fn("spend_log_decrease", hdr=f"LANGUAGE sql SECURITY DEFINER {SP} SET role = postgres") + rev("spend_log_decrease"), DB2A, DB2)
# ---- F: allow-list, search_path, EXECUTE, bare statements, CASE
add("F1 the DB-2 file defines a DB-3 function name", RESERVE, {RES: "definer"} if False else ALLOWED_BY_FILE[DB2], DB2)
add("F2 search_path names a schema the runtime can write", TRIG(hdr="LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, app, pg_temp"), DB2A, DB2)
add("F3 EXECUTE format with %L from a caller value", TRIG("BEGIN EXECUTE format('INSERT INTO %I.t VALUES (%L)', TG_TABLE_SCHEMA, NEW.agent_id); RETURN NULL; END"), DB2A, DB2)
add("F4 EXECUTE format with %s", TRIG("BEGIN EXECUTE format('INSERT INTO %I.t VALUES (%s)', TG_TABLE_SCHEMA, 1); RETURN NULL; END"), DB2A, DB2)
add("F5 EXECUTE format whose schema argument is a caller value", TRIG("BEGIN EXECUTE format('INSERT INTO %I.t VALUES (1)', NEW.agent_id); RETURN NULL; END"), DB2A, DB2)
add("F6 bare SELECT ... FROM in a body", TRIG("BEGIN PERFORM 1 FROM spend; RETURN NULL; END"), DB2A, DB2)
add("F7 bare LOCK TABLE in a body", TRIG("BEGIN LOCK TABLE spend; RETURN NULL; END"), DB2A, DB2)
add("F8 bare DROP in a body", TRIG("BEGIN DROP TABLE spend_decrease_log; RETURN NULL; END"), DB2A, DB2)
add("F9 EXECUTE of ALTER through format", TRIG("BEGIN EXECUTE format('ALTER FUNCTION %I.f() SECURITY INVOKER', TG_TABLE_SCHEMA); RETURN NULL; END"), DB2A, DB2)
add("F10 LANGUAGE c", "CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE c SECURITY DEFINER " + SP + " AS 'x', 'y';\n" + rev("spend_log_decrease"), DB2A, DB2)
add("F11 DO block with a computed token (independent runner cases 12 to 15 in one)", "DO $$ BEGIN EXECUTE 'CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY ' || chr(32) || 'DEFINER AS $x$ SELECT 1 $x$'; END $$;\n")
# controls: must be clean
OKD = "CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER " + SP + " AS $f$ BEGIN EXECUTE format('INSERT INTO %I.spend_decrease_log VALUES (1)', TG_TABLE_SCHEMA) USING OLD.usd; RETURN NULL; END $f$;\n" + rev("spend_log_decrease")
add("K1 control: a correct listed function", OKD, DB2A, DB2, "clean")
add("K2 control: token only in a comment and in a string (v19: a COMMENT ON, because a bare SELECT is now refused)", "-- SECURITY DEFINER in a comment\nCOMMENT ON TABLE t IS 'SECURITY DEFINER';\n", {}, "x.sql", "clean")
add("K3 control: an atomic body with CASE ... END and a second statement", f"CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE kill_switch SET \"on\" = CASE WHEN true THEN true ELSE false END; UPDATE kill_switch SET ts = now(); END;\n" + rev("kill_switch_engage"), {ENG: "definer"}, DB3, "clean")
add("K4 control: a listed invoker function (the DB-2 audit trigger)", "CREATE OR REPLACE FUNCTION audit_log_append_only() RETURNS trigger LANGUAGE plpgsql " + SP + " AS $f$ BEGIN RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = '42501'; END $f$;\n", ALLOWED_BY_FILE[DB2], DB2, "clean")

# ================= v19: NEW mutants. The run prints "v18 MISSES it" when the v18 guard passes the mutant; a new mutant the v18 guard already flags is listed honestly (no mark).
NEWMUT = set()
def addn(n, *a, **k): add(n, *a, **k); NEWMUT.add(n)
RES_NOREV = RESERVE.split("REVOKE ALL")[0]
# ---- MA1a: DROP then re-create, REVOKE ordering
addn("N01 REVOKE; DROP FUNCTION; CREATE OR REPLACE (re-created function has PUBLIC execute)", rev("spend_reserve", "text, date, numeric") + "DROP FUNCTION spend_reserve(text, date, numeric);\n" + RES_NOREV, {RES: "definer"}, DB3)
addn("N02 CREATE; REVOKE; CREATE OR REPLACE again (second create, no REVOKE after it)", RESERVE + RES_NOREV, {RES: "definer"}, DB3)
addn("N03 REVOKE before the CREATE", rev("spend_reserve", "text, date, numeric") + RES_NOREV, {RES: "definer"}, DB3)
addn("N04 DROP FUNCTION alone", "DROP FUNCTION kill_switch_engage();\n", {ENG: "definer"}, DB3)
# ---- MA1b: role and session switches, quoted and underscore spellings, set_config
addn("N05 SELECT set_config('role', 'postgres', false) at top level", "SELECT set_config('role', 'postgres', false);\n")
addn('N06 SET "role" TO postgres (quoted name)', 'SET "role" TO postgres;\n')
addn("N07 SET session_authorization TO postgres (one underscore word)", "SET session_authorization TO postgres;\n")
addn('N08 RESET "role"', 'RESET "role";\n')
addn('N09 SET LOCAL "role" = postgres', 'SET LOCAL "role" = postgres;\n')
addn("N10 SET SESSION_AUTHORIZATION TO postgres", "SET SESSION_AUTHORIZATION TO postgres;\n")
# ---- MA1c: other statements
addn("N11 file-level SET search_path = public", "SET search_path = public;\n" + RESERVE, {RES: "definer"}, DB3)
addn("N12 file-level SET LOCAL search_path = public", "SET LOCAL search_path = public;\n")
addn("N13 CALL a procedure", "CALL some_proc();\n")
addn("N14 PREPARE", "PREPARE p AS SELECT 1;\n")
addn("N15 REASSIGN OWNED", "REASSIGN OWNED BY migr17 TO rt17;\n")
addn("N16 CREATE VIEW", "CREATE VIEW v AS SELECT * FROM spend;\n")
addn("N17 CREATE POLICY", "CREATE POLICY p ON spend USING (true);\n")
addn("N18 ALTER TABLE ... DISABLE TRIGGER", "ALTER TABLE spend DISABLE TRIGGER spend_keep_keys;\n")
addn("N19 ALTER TABLE ... DROP CONSTRAINT", "ALTER TABLE spend DROP CONSTRAINT spend_usd_ok;\n")
addn("N20 ALTER TABLE ... ADD COLUMN, DISABLE TRIGGER ALL (second action)", "ALTER TABLE spend ADD COLUMN x int, DISABLE TRIGGER ALL;\n")
addn("N21 bare SELECT at top level", "SELECT 1;\n")
addn("N22 DROP TABLE at top level", "DROP TABLE spend_decrease_log;\n")
addn("N23 LOCK TABLE at top level", "LOCK TABLE spend;\n")
addn("N24 INSERT at top level", "INSERT INTO spend VALUES ('x', now(), 0);\n")
addn("N25 UPDATE at top level", "UPDATE spend SET usd = 0;\n")
addn("N26 DELETE at top level", "DELETE FROM spend_decrease_log;\n")
addn("N27 COPY ... TO PROGRAM", "COPY spend TO PROGRAM 'id';\n")
addn("N28 COMMIT (ends the transaction, so SET LOCAL stops holding)", "COMMIT;\n")
addn("N29 CREATE TRIGGER executing a function that is not listed", "CREATE TRIGGER t BEFORE UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION evil();\n", DB2A, DB2)
addn("N30 DROP TRIGGER without IF EXISTS", "DROP TRIGGER spend_keep_keys ON spend;\n")
addn("N31 CREATE TABLE ... AS SELECT", "CREATE TABLE t AS SELECT * FROM spend;\n")
addn("N32 CREATE TEMP TABLE", "CREATE TEMP TABLE spend (a int);\n")
addn("N33 REVOKE ... FROM a role (not the PUBLIC shape)", "REVOKE ALL ON FUNCTION kill_switch_engage() FROM rt17;\n", {ENG: "definer"}, DB3)
addn("N34 REVOKE of a function that is not listed for the file", "REVOKE ALL ON FUNCTION other() FROM PUBLIC;\n", {ENG: "definer"}, DB3)
addn("N35 file name not in the allow-list gets nothing (fails closed)", RESERVE, {}, "renamed_by_the_move_pr.sql")
# ---- MA1d: bodies
ATOM = lambda body, f="kill_switch_engage": f"CREATE OR REPLACE FUNCTION {f}() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC {body} END;\n" + rev(f)
addn("N36 definer atomic body calls query_to_xml on a caller text", ATOM("SELECT query_to_xml('select 1', true, false, '');"), {ENG: "definer"}, DB3)
addn("N37 definer atomic body calls set_config", ATOM("SELECT set_config('role', 'postgres', true);"), {ENG: "definer"}, DB3)
addn("N38 definer plpgsql body calls pg_read_file", TRIG("BEGIN PERFORM pg_read_file('x'); RETURN NULL; END"), DB2A, DB2)
addn('N39 definer body calls a quoted function name "query_to_xml"(..)', ATOM('SELECT "query_to_xml"(\'select 1\', true, false, \'\');'), {ENG: "definer"}, DB3)
addn("N40 definer body calls pg_catalog.set_config (schema-qualified call)", ATOM("SELECT pg_catalog.set_config('role', 'x', true);"), {ENG: "definer"}, DB3)
addn("N41 EXECUTE string holds a query_to_xml call", TRIG("BEGIN EXECUTE format('INSERT INTO %I.t VALUES (query_to_xml($1, true, false, $2))', TG_TABLE_SCHEMA); RETURN NULL; END"), DB2A, DB2)
addn("N42 definer atomic body updates a table that is not pinned for the file", ATOM("UPDATE audit_entries SET a = 1;"), {ENG: "definer"}, DB3)
addn("N43 definer atomic body names a schema-qualified relation", ATOM("UPDATE public.kill_switch SET \"on\" = true;"), {ENG: "definer"}, DB3)
addn("N44 definer atomic body with SET ROLE inside", ATOM("SET ROLE postgres;"), {ENG: "definer"}, DB3)
addn("N45 definer atomic body with a join to an unpinned table", ATOM("UPDATE kill_switch SET \"on\" = true FROM audit_entries WHERE true;"), {ENG: "definer"}, DB3)
# ---- MA2: schema and quoted-case aliasing of listed names
addn("N46 other_schema.spend_reserve(...) stands for the listed name (body unscanned in v18)", "CREATE OR REPLACE FUNCTION other_schema.spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS void LANGUAGE sql SECURITY DEFINER " + SP + " BEGIN ATOMIC SELECT 1; END;\n" + rev("spend_reserve", "text, date, numeric"), {RES: "definer"}, DB3)
addn("N47 quoted case \"Spend_Reserve\" stands for the listed name", "CREATE OR REPLACE FUNCTION \"Spend_Reserve\"(p_agent text, p_day date, p_worst numeric) RETURNS void LANGUAGE sql SECURITY DEFINER " + SP + " BEGIN ATOMIC SELECT 1; END;\n" + rev("spend_reserve", "text, date, numeric"), {RES: "definer"}, DB3)
addn("N48 quoted type \"Date\" stands for date", "CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day \"Date\", p_worst numeric) RETURNS void LANGUAGE sql SECURITY DEFINER " + SP + " BEGIN ATOMIC SELECT 1; END;\n" + rev("spend_reserve", "text, date, numeric"), {RES: "definer"}, DB3)
addn("N49 type with another schema (evil.date) stands for date", "CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day evil.date, p_worst numeric) RETURNS void LANGUAGE sql SECURITY DEFINER " + SP + " BEGIN ATOMIC SELECT 1; END;\n" + rev("spend_reserve", "text, date, numeric"), {RES: "definer"}, DB3)
addn("N50 public.spend_reserve(...) (any qualification is refused)", RESERVE.replace("FUNCTION spend_reserve(p_agent", "FUNCTION public.spend_reserve(p_agent"), {RES: "definer"}, DB3)
addn("N51 REVOKE names another schema's function, the real one stays open", RESERVE.split("REVOKE ALL")[0] + "REVOKE ALL ON FUNCTION other_schema.spend_reserve(text, date, numeric) FROM PUBLIC;\n", {RES: "definer"}, DB3)
# controls added in v19 (must be clean)
addn("K5 control: the quoted lower-case name \"spend_reserve\" is the listed name", RESERVE.replace("FUNCTION spend_reserve(p_agent", "FUNCTION \"spend_reserve\"(p_agent"), {RES: "definer"}, DB3, "clean")
addn("K6 control: pg_catalog.date for date is the same type", RESERVE.replace("p_day date", "p_day pg_catalog.date"), {RES: "definer"}, DB3, "clean")
addn("K7 control: ALTER TABLE with two ADD actions, SET LOCAL statement_timeout, DROP TRIGGER IF EXISTS, COMMENT ON", "SET LOCAL lock_timeout = '5s';\nSET LOCAL statement_timeout = '60s';\nALTER TABLE spend ADD COLUMN x int, ADD CONSTRAINT c CHECK (x >= 0);\nDROP TRIGGER IF EXISTS t ON spend;\nCOMMENT ON TABLE spend IS 'x';\n", {}, "x.sql", "clean")
addn("K8 control: CREATE TRIGGER executing a listed function", "CREATE TRIGGER t BEFORE UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();\n", ALLOWED_BY_FILE[DB2], DB2, "clean")
addn("K9 control: an atomic body that reads and writes only the pinned relations, with a join and an alias", ATOM("UPDATE kill_switch k SET \"on\" = true FROM spend s WHERE k.id = 1 AND s.usd >= 0;"), {ENG: "definer"}, DB3, "clean")


# ================= v20: NEW mutants (round 6 of the security review and the independent runner of v19). The run shows `v19 MISSES it` for each one the v19 guard passes.
NEWMUT20 = set()
def add20(n, *a, **k): add(n, *a, **k); NEWMUT20.add(n)
REAL = {"trigger_pins": "real", "fn_pins": "real", "kinds": "real"}
REAL_V22 = {"trigger_pins": "real", "fn_pins": "real", "kinds": "real", "add_pins": "real"}      # use the pins of allow_v20 for this file
DB2TXT = open(os.path.join(sys.argv[1], DB2)).read(); DB3TXT = open(os.path.join(sys.argv[1], DB3)).read()
KIND_REL = {"kinds": "real"}
RELF = lambda body: f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC {body} END;\n" + rev("kill_switch_release")
# ---- B1: bodies that are never scanned
add20("V01 definer RETURN expression calls query_to_xml (security B1)", f"CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS xml LANGUAGE sql SECURITY DEFINER {SP} RETURN query_to_xml(p_agent, true, false, '');\n" + rev("spend_reserve", "text, date, numeric"), {RES: "definer"}, DB3)
add20("V02 definer RETURN expression calls set_config", f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS text LANGUAGE sql SECURITY DEFINER {SP} RETURN set_config('role', 'postgres', true);\n" + rev("kill_switch_release"), {REL: "definer"}, DB3)
add20("V03 definer RETURN expression reads an unpinned table", f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS text LANGUAGE sql SECURITY DEFINER {SP} RETURN (SELECT rolpassword FROM pg_authid LIMIT 1);\n" + rev("kill_switch_release"), {REL: "definer"}, DB3)
add20("V04 definer with no body at all (neither ATOMIC, RETURN nor one string)", f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP};\n" + rev("kill_switch_release"), {REL: "definer"}, DB3)
add20("V05 definer with two string bodies", f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} AS 'select 1', 'select 2';\n" + rev("kill_switch_release"), {REL: "definer"}, DB3)
add20("V06 definer with a string body AND a RETURN", f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS int LANGUAGE sql SECURITY DEFINER {SP} AS 'select 1' RETURN 1;\n" + rev("kill_switch_release"), {REL: "definer"}, DB3)
# ---- M1: %I.name( hides a call
add20("V07 EXECUTE format('SELECT %I.evil_fn($1)') (security M1)", TRIG("BEGIN EXECUTE format('SELECT %I.evil_fn($1)', TG_TABLE_SCHEMA) USING NEW.usd; RETURN NULL; END"), DB2A, DB2)
add20("V08 EXECUTE format('INSERT INTO %I.t SELECT %I.evil_fn(1)')", TRIG("BEGIN EXECUTE format('INSERT INTO %I.t SELECT %I.evil_fn(1)', TG_TABLE_SCHEMA, TG_TABLE_SCHEMA); RETURN NULL; END"), DB2A, DB2)
add20("V09 EXECUTE string with FROM %I.evil_srf(...) (a set-returning function in FROM)", TRIG("BEGIN EXECUTE format('INSERT INTO %I.t SELECT * FROM %I.evil_srf($1)', TG_TABLE_SCHEMA, TG_TABLE_SCHEMA) USING NEW.usd; RETURN NULL; END"), DB2A, DB2)
# ---- M2: triggers
add20("V10 DB-2 text with a DROP TRIGGER IF EXISTS of a pinned audit trigger at the end (security M2)", DB2TXT + "\nDROP TRIGGER IF EXISTS spend_log_decrease ON spend;\n", ALLOWED_BY_FILE[DB2], DB2, opts=REAL)
add20("V11 DB-2 text with a WHEN (false) on the kill-switch trigger", DB2TXT.replace('WHEN (NEW."on" IS DISTINCT FROM OLD."on")', "WHEN (false)"), ALLOWED_BY_FILE[DB2], DB2, opts=REAL)
add20("V12 DB-2 text plus CREATE OR REPLACE TRIGGER spend_log_decrease ... WHEN (false)", DB2TXT + "\nCREATE OR REPLACE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW WHEN (false) EXECUTE FUNCTION spend_log_decrease();\n", ALLOWED_BY_FILE[DB2], DB2, opts=REAL)
add20("V13 DROP TRIGGER IF EXISTS of a name that is not pinned", DB2TXT + "\nDROP TRIGGER IF EXISTS some_other ON spend;\n", ALLOWED_BY_FILE[DB2], DB2, opts=REAL)
add20("V14 DB-2 text without the append-only trigger of the record (a pinned trigger the file no longer creates)", DB2TXT.replace("CREATE TRIGGER kill_switch_log_append_only BEFORE UPDATE OR DELETE ON kill_switch_log FOR EACH ROW\n  EXECUTE FUNCTION audit_log_append_only();\n", ""), ALLOWED_BY_FILE[DB2], DB2, opts=REAL)
add20("V15 control: DB-2 text with a DROP TRIGGER IF EXISTS of a pinned name BEFORE its CREATE", "DROP TRIGGER IF EXISTS spend_keep_keys ON spend;\n" + DB2TXT, ALLOWED_BY_FILE[DB2], DB2, "clean", opts=REAL)
add20("V16 control: the real DB-2 file with every pin", DB2TXT, ALLOWED_BY_FILE[DB2], DB2, "clean", opts=REAL)
# ---- M3: relations introduced by MERGE, USING, TABLE, SELECT INTO
add20("V17 atomic body MERGE INTO an unpinned table (security M3)", ATOM("MERGE INTO audit_entries a USING kill_switch k ON true WHEN MATCHED THEN DELETE;"), {ENG: "definer"}, DB3)
add20("V18 atomic body DELETE ... USING pg_authid", ATOM("DELETE FROM kill_switch USING pg_authid WHERE true;"), {ENG: "definer"}, DB3)
add20("V19 atomic body TABLE pg_authid", ATOM("TABLE pg_authid;"), {ENG: "definer"}, DB3)
add20("V20 atomic body SELECT ... INTO a new table", ATOM("SELECT id INTO newt FROM kill_switch;"), {ENG: "definer"}, DB3)
add20("V21 atomic body COPY / TRUNCATE of an unpinned table", ATOM("TRUNCATE audit_entries;"), {ENG: "definer"}, DB3)
add20("V22 EXECUTE string with USING pg_authid", TRIG("BEGIN EXECUTE format('DELETE FROM %I.t USING pg_authid', TG_TABLE_SCHEMA); RETURN NULL; END"), DB2A, DB2)
# ---- M4: head and body fingerprint
add20("V23 release without its `AND \"on\" = true` (same tables, other behaviour) (security M4)", DB3TXT.replace('WHERE id = 1 AND "on" = true;', "WHERE id = 1;"), ALLOWED_BY_FILE[DB3], DB3, opts=REAL)
add20("V24 release and engage swapped bodies", DB3TXT.replace("UPDATE kill_switch SET \"on\" = false, \"by\" = session_user, ts = clock_timestamp() WHERE id = 1 AND \"on\" = true;", "UPDATE kill_switch SET \"on\" = true;"), ALLOWED_BY_FILE[DB3], DB3, opts=REAL)
add20("V25 reserve with another return type", DB3TXT.replace("RETURNS TABLE (day_usd numeric, month_usd numeric)\nLANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp\nBEGIN ATOMIC\n  INSERT INTO spend (agent_id", "RETURNS TABLE (day_usd numeric, month_usd numeric)\nLANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp\nBEGIN ATOMIC\n  INSERT INTO spend (agent_id", 1).replace("p_worst > 0\n    ON CONFLICT (agent_id, day)", "p_worst > -1\n    ON CONFLICT (agent_id, day)"), ALLOWED_BY_FILE[DB3], DB3, opts=REAL)
add20("V26 control: the real DB-3 file with every pin", DB3TXT, ALLOWED_BY_FILE[DB3], DB3, "clean", opts=REAL)
# ---- F1 (independent runner of v19): statement kinds
add20("V27 release body DELETE FROM spend (runner R01; Postgres accepted it)", RELF("DELETE FROM spend;"), {REL: "definer"}, DB3, opts=KIND_REL)
add20("V28 release body WITH d AS (DELETE FROM spend RETURNING 1) SELECT 1 (runner R14)", RELF("WITH d AS (DELETE FROM spend RETURNING 1) SELECT 1;"), {REL: "definer"}, DB3, opts=KIND_REL)
add20("V29 release body TRUNCATE spend (runner R15; the server refuses it)", RELF("TRUNCATE spend;"), {REL: "definer"}, DB3, opts=KIND_REL)
add20("V30 release with the LEAKPROOF attribute (runner R10; the server refuses it)", f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER LEAKPROOF {SP} BEGIN ATOMIC UPDATE kill_switch SET \"on\" = false; END;\n" + rev("kill_switch_release"), {REL: "definer"}, DB3, opts=KIND_REL)
add20("V31 control: release body UPDATE only", RELF("UPDATE kill_switch SET \"on\" = false WHERE id = 1;"), {REL: "definer"}, DB3, "clean", opts=KIND_REL)
add20("V32 DB-2 definer body with a DELETE inside the EXECUTE string", TRIG("BEGIN EXECUTE format('DELETE FROM %I.spend_decrease_log', TG_TABLE_SCHEMA); RETURN NULL; END"), DB2A, DB2, opts={"kinds": "real"})
# ---- m1 / F2: expressions inside allowed shapes
add20("V33 ADD CONSTRAINT CHECK (pg_read_file(..)) (runner H42)", "ALTER TABLE spend ADD CONSTRAINT c CHECK (pg_read_file('x') = 'y');\n")
add20("V34 ADD COLUMN DEFAULT current_setting(..) (runner H43)", "ALTER TABLE spend ADD COLUMN x text DEFAULT current_setting('server_version');\n")
add20("V35 ADD COLUMN GENERATED ALWAYS AS (evil()) STORED (runner H44)", "ALTER TABLE spend ADD COLUMN g text GENERATED ALWAYS AS (evil(agent_id)) STORED;\n")
add20("V36 CREATE INDEX on an expression calling evil() (runner H90)", "CREATE INDEX i ON spend (evil(agent_id));\n")
add20("V37 CREATE INDEX ... WHERE evil() (runner H91)", "CREATE INDEX i ON spend (agent_id) WHERE evil();\n")
add20("V38 CREATE TABLE with DEFAULT evil()", "CREATE TABLE t (a int DEFAULT evil());\n")
add20("V39 CREATE TRIGGER WHEN (evil())", "CREATE TRIGGER t BEFORE UPDATE ON spend FOR EACH ROW WHEN (evil()) EXECUTE FUNCTION spend_keep_keys();\n", ALLOWED_BY_FILE[DB2], DB2)
add20("V40 CHECK with OPERATOR(...)", "ALTER TABLE spend ADD CONSTRAINT c CHECK (usd OPERATOR(public.+) 1 > 0);\n")
add20("V41 control: CHECK with length, regex, date_trunc, extract, REFERENCES t (id), numeric(10,2)", "ALTER TABLE spend ADD CONSTRAINT c CHECK (length(agent_id) BETWEEN 1 AND 200 AND agent_id ~ '^a$' AND extract(day FROM day) >= 1);\nCREATE INDEX i2 ON spend (date_trunc('day', ts));\nCREATE TABLE t2 (a numeric(10,2) REFERENCES t (id), b timestamptz DEFAULT clock_timestamp());\n", {}, "x.sql", "clean")
# ---- m2: positional SET
add20("V42 atomic body: SELECT ... FOR UPDATE; SET search_path = public (the UPDATE within 4 tokens exempted the SET in v19)", ATOM("SELECT 1 FROM kill_switch FOR UPDATE; SET search_path = public;"), {ENG: "definer"}, DB3)
add20("V43 control: UPDATE name AS alias SET and DO UPDATE SET are legal", ATOM("INSERT INTO kill_switch (id) VALUES (1) ON CONFLICT (id) DO UPDATE SET ts = now(); UPDATE kill_switch AS k SET ts = now();"), {ENG: "definer"}, DB3, "clean")
# ---- m3: tokenizer follows the server
add20("V44 SECURITY<NBSP>DEFINER is ONE identifier for the server, not the two words (tokenizer, v19 split it)", RESERVE.replace("SECURITY DEFINER", "SECURITY DEFINER"), {RES: "definer"}, DB3)
add20("V45 control: a name made of an astral character is one word", "COMMENT ON TABLE t IS 'x';\nALTER TABLE spend ADD COLUMN \U0001F600x int;\n", {}, "x.sql", "clean")

# ================= v21: NEW mutants (round 7 of the security review). The run shows `v20 MISSES it` for each one the v20 guard passes.
NEWMUT21 = set()
def add21(n, *a, **k): add(n, *a, **k); NEWMUT21.add(n)
ATOMX = lambda body, fnn="kill_switch_engage": f"CREATE OR REPLACE FUNCTION {fnn}() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC {body} END;\n" + rev(fnn)
add21("W01 settle without the guard in its final SELECT (security M2 of v20): the pin differs", DB3TXT.replace("\n      AND p_worst >= 0 AND p_actual >= 0;\nEND;", ";\nEND;"), ALLOWED_BY_FILE[DB3], DB3, opts=REAL)
add21("W02 alias column list hides a second relation (security m4)", ATOMX("SELECT 1 FROM spend AS d (a, b), pg_authid;"), {ENG: "definer"}, DB3)
add21("W03 TABLESAMPLE hides a second relation (security m4)", ATOMX("SELECT 1 FROM spend TABLESAMPLE SYSTEM (50), pg_authid;"), {ENG: "definer"}, DB3)
add21("W04 TABLESAMPLE ... REPEATABLE hides a second relation", ATOMX("SELECT 1 FROM spend d TABLESAMPLE BERNOULLI (50) REPEATABLE (1), pg_authid;"), {ENG: "definer"}, DB3)
add21("W05 call of cloc<Kelvin sign>_timestamp() read as clock_timestamp() (security m5)", ATOMX("UPDATE kill_switch SET ts = clocK_timestamp();"), {ENG: "definer"}, DB3)
add21("W06 <long s>elect(1) read as the syntax word SELECT before a bracket (security m5)", ATOMX("UPDATE kill_switch SET ts = ſelect(1);"), {ENG: "definer"}, DB3)
add21("W07 relation <Kelvin sign>ill_switch read as the pinned kill_switch (security m5)", ATOMX("SELECT 1 FROM Kill_switch;"), {ENG: "definer"}, DB3)
add21('W08 search_path = "PG_CATALOG", pg_temp (a different schema for the server; security m6)', TRIG(hdr='LANGUAGE plpgsql SECURITY DEFINER SET search_path = "PG_CATALOG", pg_temp'), DB2A, DB2)
add21("W09 a -- comment that ends at a carriage return hides DROP TABLE (security m7)", "SET LOCAL lock_timeout = '5s'; -- c\rDROP TABLE spend;\n")
add21("W10 SET LOCAL lock_timeout = 0 (no timeout at all; security m11)", "SET LOCAL lock_timeout = 0;\n")
add21("W11 SET LOCAL statement_timeout = '0' (security m11)", "SET LOCAL statement_timeout = '0';\n")
add21("W12 CREATE TABLE ... INHERITS (spend) (security m11)", "CREATE TABLE child (x int) INHERITS (spend);\n")
add21("W13 a function called key() is not the syntax word KEY (security m11)", ATOMX("UPDATE kill_switch SET ts = key(1);"), {ENG: "definer"}, DB3)
add21("W14 a function called over() is not the syntax word OVER", ATOMX("UPDATE kill_switch SET ts = over(1);"), {ENG: "definer"}, DB3)
add21("W15 a function called filter() is not the syntax word FILTER", ATOMX("UPDATE kill_switch SET ts = filter(1);"), {ENG: "definer"}, DB3)
add21("W16 DROP TRIGGER of a pinned name ON another table (security m11)", "DROP TRIGGER IF EXISTS spend_keep_keys ON audit_entries;\n" + DB2TXT, ALLOWED_BY_FILE[DB2], DB2, opts=REAL)
add21("W17 control: ON CONFLICT (..) and PRIMARY KEY (..) are still syntax", ATOMX("INSERT INTO kill_switch (id) VALUES (1) ON CONFLICT (id) DO NOTHING;"), {ENG: "definer"}, DB3, "clean")
add21("W18 control: alias column list over a pinned relation only", ATOMX("SELECT 1 FROM spend AS d (a, b);"), {ENG: "definer"}, DB3, "clean")
add21("W19 control: SET LOCAL lock_timeout = '5s' and statement_timeout = '60s'", "SET LOCAL lock_timeout = '5s';\nSET LOCAL statement_timeout = '60s';\n", {}, "x.sql", "clean")
add21("W20 control: DB-3 file with the new pins", DB3TXT, ALLOWED_BY_FILE[DB3], DB3, "clean", opts=REAL)

# ---- B1 of the independent runner of v20 (H67, H68, H75, H76): the text of ALTER TABLE ... ADD must be the pinned text
ADDP = {"add_pins": "real"}
DB1F = "spend_nonneg.sql"; DB1TXT = open(os.path.join(HERE, "held-sql", DB1F)).read()
ID_RE = "CHECK (agent_id ~ '^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$')"
assert DB3TXT.count(ID_RE) == 2 and DB3TXT.count("1000000000000::numeric") == 4
add21("W21 (H75) CHECK (true) in place of the agent-id rule on both tables", DB3TXT.replace(ID_RE, "CHECK (true)"), ALLOWED_BY_FILE[DB3], DB3, opts=ADDP)
add21("W22 (H76) ceiling 1e30 on both tables", DB3TXT.replace("1000000000000::numeric", "1000000000000000000000000000000::numeric"), ALLOWED_BY_FILE[DB3], DB3, opts=ADDP)
add21("W23 (H67) the ceiling of spend.usd dropped (spend only)", DB3TXT.replace("CHECK (usd >= 0 AND usd < 1000000000000::numeric);\nALTER TABLE spend ADD CONSTRAINT spend_agent_len", "CHECK (usd >= 0);\nALTER TABLE spend ADD CONSTRAINT spend_agent_len", 1), ALLOWED_BY_FILE[DB3], DB3, opts=ADDP)
add21("W24 (H68) open_usd check weakened by OR true (spend only)", DB3TXT.replace("CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric);\nALTER TABLE spend ADD CONSTRAINT spend_guarded_ok", "CHECK (open_usd >= 0 OR true);\nALTER TABLE spend ADD CONSTRAINT spend_guarded_ok", 1), ALLOWED_BY_FILE[DB3], DB3, opts=ADDP)
add21("W25 day window widened to year 9999", DB3TXT.replace("day < DATE '2100-01-01'", "day < DATE '9999-01-01'", 1), ALLOWED_BY_FILE[DB3], DB3, opts=ADDP)
add21("W26 open_usd column default changed to 5", DB3TXT.replace("ALTER TABLE spend ADD COLUMN open_usd numeric NOT NULL DEFAULT 0;", "ALTER TABLE spend ADD COLUMN open_usd numeric NOT NULL DEFAULT 5;", 1), ALLOWED_BY_FILE[DB3], DB3, opts=ADDP)
add21("W27 DB-1 default file with CHECK (usd >= 0 OR true)", DB1TXT.replace("usd >= 0", "usd >= 0 OR true"), ALLOWED_BY_FILE.get(DB1F, {}), DB1F, opts=ADDP)
add21("W28 control: the real DB-3 file with the ADD pins", DB3TXT, ALLOWED_BY_FILE[DB3], DB3, "clean", opts=ADDP)
add21("W29 control: the real DB-1 default file with the ADD pins", DB1TXT, ALLOWED_BY_FILE.get(DB1F, {}), DB1F, "clean", opts=ADDP)


# ---- v22 (round 9): reserve guard (security MJ1), renamed file (MJ2), timeouts (m2), DDL pins (m6), timeouts first (m6)
NEWMUT22 = set()
def add22(n, *a, **k): add(n, *a, **k); NEWMUT22.add(n)
RSV_OLD = "m.month = date_trunc('month', p_day)::date\n      AND p_worst > 0;\nEND;"
assert DB3TXT.count(RSV_OLD) == 1
add22("X01 (MJ1) reserve without the guard in its final SELECT (the v21 text: a rejected reserve returns the unchanged totals); the v21 pin accepts it, the v22 pin does not", DB3TXT.replace(RSV_OLD, "m.month = date_trunc('month', p_day)::date;\nEND;"), ALLOWED_BY_FILE[DB3], DB3, opts={**REAL_V22, "qfn": 1})
add22("X02 (MJ1) reserve whose final SELECT has the guard on the wrong sign (p_worst >= 0 lets 0 through)", DB3TXT.replace(RSV_OLD, "m.month = date_trunc('month', p_day)::date\n      AND p_worst >= 0;\nEND;"), ALLOWED_BY_FILE[DB3], DB3, opts=REAL_V22)
add22("X03 control: the real v22 DB-3 file with every pin and both timeout requirements", DB3TXT, ALLOWED_BY_FILE[DB3], DB3, "clean", opts=REAL_V22)
CHK_TRUE = "SET LOCAL lock_timeout = '5s';\nALTER TABLE spend ADD CONSTRAINT spend_x CHECK (true);\n"
add22("X04 (MJ2) a renamed or new held file with ADD CONSTRAINT ... CHECK (true): no pin table for the name, so every ADD is a problem", CHK_TRUE, {}, "spend_guarded_writes_renamed.sql", opts={"add_pins": "none"})
add22("X05 (MJ2) the real DB-3 text under another file name: nothing is pinned for the name, so every ADD (ten) and every function is a problem", DB3TXT, ALLOWED_BY_FILE[DB3], "spend_guarded_writes2.sql", opts={"add_pins": "none"})
add22("X06 (MJ2) a renamed copy of the DB-1 default file", DB1TXT, {}, "spend_nonneg_renamed.sql", opts={"add_pins": "none"})
for k, v in (("X07", "0x0"), ("X08", "'0_0'"), ("X09", "'0e0'"), ("X10", "'0.0'"), ("X11", "'0'"), ("X12", "'999999h'"), ("X13", "'3601s'"), ("X14", "'-5s'"), ("X15", "'1d'"), ("X16", "'5us'"), ("X17", "0")):
    add22(f"{k} (m2) SET LOCAL lock_timeout = {v} (zero spelling or above one hour)", f"SET LOCAL lock_timeout = {v};\n")
add22("X18 control (m2): the longest allowed value 1h, and 3600s, and 3600000 (milliseconds)", "SET LOCAL lock_timeout = '1h';\nSET LOCAL statement_timeout = '3600s';\nSET LOCAL lock_timeout = 3600000;\n", {}, "x.sql", "clean")
add22("X19 (m6) COMMENT ON TABLE with an unpinned text in a pinned file", "SET LOCAL lock_timeout = '5s';\nCOMMENT ON TABLE spend IS 'harmless';\n", {}, "spend_nonneg.sql", opts={"add_pins": "real"})
add22("X20 (m6) CREATE INDEX with an unpinned text in a pinned file", "SET LOCAL lock_timeout = '5s';\nCREATE INDEX evil_idx ON spend (usd);\n", {}, "spend_nonneg.sql", opts={"add_pins": "real"})
add22("X21 (m6) CREATE TABLE with an unpinned text in a pinned file", "SET LOCAL lock_timeout = '5s';\nCREATE TABLE spend_shadow (agent_id text, usd numeric);\n", {}, "spend_nonneg.sql", opts={"add_pins": "real"})
add22("X22 (m6) CREATE TABLE in a file that has no pin table", "CREATE TABLE spend_shadow (agent_id text, usd numeric);\n", {}, "nopins.sql", opts={"add_pins": "none"})
add22("X23 (m6) the DB-3 file without its statement_timeout line (both timeouts required)", DB3TXT.replace("SET LOCAL statement_timeout = '60s';\n", ""), ALLOWED_BY_FILE[DB3], DB3, opts={**REAL_V22, "req": 1, "req2": 1})
add22("X24 (m6) the DB-3 file with the timeouts AFTER the first ALTER TABLE", DB3TXT.replace("SET LOCAL lock_timeout = '5s';\nSET LOCAL statement_timeout = '60s';\n", "", 1).replace("ALTER TABLE spend_month ADD COLUMN", "SET LOCAL lock_timeout = '5s';\nSET LOCAL statement_timeout = '60s';\nALTER TABLE spend_month ADD COLUMN", 1), ALLOWED_BY_FILE[DB3], DB3, opts={**REAL_V22, "req": 1, "req2": 1})
add22("X25 (m6) a held file with no lock_timeout at all before its CREATE TABLE", "CREATE TABLE spend_shadow (agent_id text);\n", {}, "x.sql", opts={"req": 1})
add22("X26 control: the v22 DB-3 file with both timeout requirements and every pin is clean (same as X03, written out)", DB3TXT, ALLOWED_BY_FILE[DB3], DB3, "clean", opts={**REAL_V22, "req": 1, "req2": 1})
add22("X27 control: a pinned DB-1 file with lock_timeout required is clean", DB1TXT, ALLOWED_BY_FILE.get(DB1F, {}), DB1F, "clean", opts={"add_pins": "real", "req": 1})

# the independent runner's spellings
for fname in ("spellings.json", "spellings2.json"):
    for k, txt in json.load(open(os.path.join(HERE, fname))).items():
        if k.startswith("C1") or k.startswith("C2"): continue
        add("R" + k, txt, {RES: "definer"} if k.startswith("25") else {}, DB3 if k.startswith("25") else "x.sql", "flag")
def realpinsP(file, o):
    r = {"trigger_pins": gP.PIN_ANY, "fn_pins": gP.PIN_ANY, "kinds": gP.PIN_ANY}
    if not o: return r
    if o.get("trigger_pins") == "real": r["trigger_pins"] = AP.TRIGGER_PINS_BY_FILE.get(file)
    if o.get("fn_pins") == "real": r["fn_pins"] = AP.FN_PINS_BY_FILE.get(file)
    if o.get("kinds") == "real": r["kinds"] = AP.KINDS_BY_FILE.get(file)
    return r
def realpinsQ(file, o):
    r = {"trigger_pins": gQ.PIN_ANY, "fn_pins": gQ.PIN_ANY, "kinds": gQ.PIN_ANY}
    if not o: return r
    if o.get("add_pins") == "real": r["add_pins"] = set(AQ.ADD_PINS_BY_FILE[file]) if file in AQ.ADD_PINS_BY_FILE else None
    if o.get("add_pins") == "none": r["add_pins"] = None
    if o.get("qfn"): r["fn_pins"] = AQ.FN_PINS_BY_FILE.get(file)   # only X01: shows that the v21 pin of spend_reserve accepts the unguarded text
    return r
def realpins(file, o):
    r = {"trigger_pins": PIN_ANY, "fn_pins": PIN_ANY, "kinds": PIN_ANY, "add_pins": PIN_ANY}
    if not o: return r
    if o.get("add_pins") == "none": r["add_pins"] = None
    if o.get("req"): r["require_lock_timeout"] = True; r["require_stmt_timeout"] = bool(o.get("req2"))
    if o.get("add_pins") == "real": r["add_pins"] = set(A22.DDL_PINS_BY_FILE[file])
    if o.get("trigger_pins") == "real": r["trigger_pins"] = A22.TRIGGER_PINS_BY_FILE.get(file)
    if o.get("fn_pins") == "real": r["fn_pins"] = A22.FN_PINS_BY_FILE.get(file)
    if o.get("kinds") == "real": r["kinds"] = A22.KINDS_BY_FILE.get(file)
    return r
ok = bad = 0; v17_miss = 0; v16_miss = 0; v18_miss = 0; v19_miss = 0; new_total = 0; new_miss18 = 0; new20_total = 0; new20_miss19 = 0; new21_total = 0; new21_missP = 0; new22_total = 0; new22_missQ = 0
import allow_v19 as A19
for n, file, text, allowed, want in M:
    p22 = g22.check_sql_text(file, text, allowed, extra_statements=EXTRA_BY_FILE.get(file, ()), atomic_tables=ATOMIC_TABLES_BY_FILE.get(file), **realpins(file, OPTS.get(n)))
    try: p19 = g19.check_sql_text(file, text, allowed, extra_statements=A19.EXTRA_BY_FILE.get(file, ()), atomic_tables=A19.ATOMIC_TABLES_BY_FILE.get(file))
    except Exception as e: p19 = ["crash " + type(e).__name__]
    try: p18 = g18.check_sql_text(file, text, allowed)
    except Exception as e: p18 = ["crash " + type(e).__name__]
    try: p17 = g17.check_sql_text(file, text, V17_ALLOWED)
    except Exception as e: p17 = ["crash " + type(e).__name__]
    try: p16 = g16.check_sql_text(file, text, V17_ALLOWED)
    except Exception as e: p16 = ["crash " + type(e).__name__]
    try: pQ = gQ.check_sql_text(file, text, allowed, extra_statements=AQ.EXTRA_BY_FILE.get(file, ()), atomic_tables=AQ.ATOMIC_TABLES_BY_FILE.get(file), **realpinsQ(file, OPTS.get(n)))
    except Exception as e: pQ = ["crash " + type(e).__name__]
    missQ = want == "flag" and not pQ
    if n in NEWMUT22 and want == "flag": new22_total += 1; new22_missQ += missQ
    good = bool(p22) if want == "flag" else not p22
    ok += good; bad += not good
    miss17 = want == "flag" and not p17; v17_miss += miss17; v16_miss += want == "flag" and not p16
    miss18 = want == "flag" and not p18; v18_miss += miss18
    miss19 = want == "flag" and not p19; v19_miss += miss19
    if n in NEWMUT and want == "flag": new_total += 1; new_miss18 += miss18
    if n in NEWMUT20 and want == "flag": new20_total += 1; new20_miss19 += miss19
    try: pP = gP.check_sql_text(file, text, allowed, extra_statements=AP.EXTRA_BY_FILE.get(file, ()), atomic_tables=AP.ATOMIC_TABLES_BY_FILE.get(file), **realpinsP(file, OPTS.get(n)))
    except Exception as e: pP = ['crash ' + type(e).__name__]
    missP = want == 'flag' and not pP
    if n in NEWMUT21 and want == 'flag': new21_total += 1; new21_missP += missP
    print(("PASS " if good else "FAIL ") + f"{n}: v22 flags={len(p22)} ; v21 flags={len(pQ)}" + ("  (v21 MISSES it)" if missQ and n in NEWMUT22 else "") + f" ; v20 flags={len(pP)}" + ("  (v20 MISSES it)" if missP and n in NEWMUT21 else "") + f" ; v19 flags={len(p19)} ; v18 flags={len(p18)} ; v17 flags={len(p17)} ; v16 flags={len(p16)}" + ("  (v19 MISSES it)" if miss19 and n in NEWMUT20 else "") + ("  (v18 MISSES it)" if miss18 else "") + (f"  [{p22[0][:100]}]" if p22 and not good else ""))
T = f"CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE k SET a = CASE WHEN true THEN 1 ELSE 2 END; UPDATE k SET b = 1; END;\nSELECT 1;\n"
n20 = len(g22.split_statements(g22.tokenize(T)))
for name, ok_, d in (("P1 BEGIN ATOMIC with CASE ... END is ONE statement (plus the SELECT: 2 in all)", n20 == 2, f"v20={n20}"), ("P2 a quoted name with -- and /* leaves the next statement visible", len(g22.split_statements(g22.tokenize('CREATE TABLE "a--b" (x int);\nCREATE TABLE "c/*" (y int);\nSELECT 1;\n'))) == 3, "v20")):
    ok += ok_; bad += not ok_; print(("PASS " if ok_ else "FAIL ") + name + f" [{d}]")
def fpn(g, t): return g.fingerprint(g.split_statements(g.tokenize(t))[0])
for name, ok_, d in (
    ("P3 `@-` and `@ -` have different fingerprints in v21 (v20 equal)", fpn(g22, "SELECT @- 1;") != fpn(g22, "SELECT @ - 1;") and fpn(gP, "SELECT @- 1;") == fpn(gP, "SELECT @ - 1;"), "server: operator @- does not exist, `@ - 1` is 1"),
    ("P4 E'x' and E 'x' have different fingerprints in v21 (v20 equal)", fpn(g22, "SELECT E'x';") != fpn(g22, "SELECT E 'x';") and fpn(gP, "SELECT E'x';") == fpn(gP, "SELECT E 'x';"), "server: the second is a syntax error"),
    ("P5 comments and the amount of white space do not change a fingerprint", fpn(g22, "SELECT 1 /* c */ + 2;") == fpn(g22, "SELECT   1\n+ -- x\n 2;"), ""),
    ("P6 a -- comment ends at a carriage return: the tokens after it are read", [t[1] for t in g22.tokenize("SELECT 1 -- c\r, 2")] == ["SELECT", "1", ",", "2"], "server: two columns"),
    ("P8 the relation scan itself (not the call rule) names pg_authid after an alias column list, after TABLESAMPLE, and after TABLESAMPLE ... REPEATABLE (v20 flagged the first two for a wrong reason: it read `d (` as a call)",
     all(any("relation pg_authid" in x for x in g22._atomic_problems(g22.tokenize(q), "f", {"spend", "spend_month", "kill_switch"})) for q in ("SELECT 1 FROM spend AS d (a, b), pg_authid;", "SELECT 1 FROM spend TABLESAMPLE SYSTEM (50), pg_authid;", "SELECT 1 FROM spend d TABLESAMPLE BERNOULLI (50) REPEATABLE (1), pg_authid;")) and
     not any("relation pg_authid" in x for x in gP._atomic_problems(gP.tokenize("SELECT 1 FROM spend AS d (a, b), pg_authid;"), "f", {"spend", "spend_month", "kill_switch"})), "v20 relation scan did not name it"),
    ("P9 (security m8) a forbidden statement AFTER a ';' inside an EXECUTE string is flagged by v21; the v20 guard flags only a string that STARTS with it; the control string with one statement is clean in both",
     bool(g22._body_problems("BEGIN EXECUTE format('UPDATE %I.spend SET usd = usd; GRANT ALL ON spend TO PUBLIC', TG_TABLE_SCHEMA); RETURN NEW; END", "f")) and not gP._body_problems("BEGIN EXECUTE format('UPDATE %I.spend SET usd = usd; GRANT ALL ON spend TO PUBLIC', TG_TABLE_SCHEMA); RETURN NEW; END", "f") and bool(g22._body_problems("BEGIN EXECUTE format('GRANT ALL ON spend TO PUBLIC', TG_TABLE_SCHEMA); RETURN NEW; END", "f")) and not g22._body_problems("BEGIN EXECUTE format('UPDATE %I.spend SET usd = usd', TG_TABLE_SCHEMA); RETURN NEW; END", "f"), ""),
    ("P10 (security m11) `AS end` and `AS case` inside a BEGIN ATOMIC body are column labels: the body is still ONE statement in v21 (v20 ended it at `AS end`)",
     len(g22.split_statements(g22.tokenize("CREATE FUNCTION f() RETURNS int LANGUAGE sql BEGIN ATOMIC SELECT 1 AS end; SELECT 2 AS case; SELECT 3; END; SELECT 4;"))) == 2 and len(gP.split_statements(gP.tokenize("CREATE FUNCTION f() RETURNS int LANGUAGE sql BEGIN ATOMIC SELECT 1 AS end; SELECT 2 AS case; SELECT 3; END; SELECT 4;"))) > 2, ""),
    ("P11 (security m11) an INVOKER function body that calls set_config('role', ...) is flagged by v21; v20 checked calls only in definer bodies and the pin alone stood in the way",
     bool(g22._body_problems_v19("BEGIN PERFORM set_config('role', 'x', false); RETURN NEW; END", "f", False)) and not gP._body_problems_v19("BEGIN PERFORM set_config('role', 'x', false); RETURN NEW; END", "f", False) and not g22._body_problems_v19("BEGIN RETURN NEW; END", "f", False), ""),
    ("P7 ASCII-only folding: Kelvin sign and long s keep their identity", str(g22.tokenize("cloc\u212a")[0][1].lower()) == "cloc\u212a" and str(g22.tokenize("\u017felect")[0][1].upper()) == "\u017fELECT", "")):
    ok += ok_; bad += not ok_; print(("PASS " if ok_ else "FAIL ") + name + f" [{d}]")
folder1, folder2 = sys.argv[1], sys.argv[2]
for f in sorted(glob.glob(os.path.join(folder1, "*.sql")) + glob.glob(os.path.join(folder2, "*.sql"))):
    b = os.path.basename(f); p = A22.check(g22, b, open(f).read())
    ok += not p; bad += bool(p); print(("PASS " if not p else "FAIL ") + f"real file {b}: {p}")
print(f"{ok} checks passed, {bad} failed; mutants the v19 guard misses: {v19_miss}; the v18 guard misses: {v18_miss}; the v17 guard misses: {v17_miss}; the v16 guard misses: {v16_miss}; of the {new20_total} NEW v20 mutants that must be flagged the v19 guard misses {new20_miss19} and flags {new20_total - new20_miss19} (the others are listed above without the 'v19 MISSES' mark); of the {new21_total} NEW v21 mutants that must be flagged the v20 guard misses {new21_missP} and flags {new21_total - new21_missP}; of the {new22_total} NEW v22 mutants that must be flagged the v21 guard misses {new22_missQ} and flags {new22_total - new22_missQ}")
sys.exit(1 if bad else 0)
