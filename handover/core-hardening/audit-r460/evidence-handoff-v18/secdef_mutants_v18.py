"""Mutants for the SECURITY DEFINER guards (v16, v17, v18). A mutant is a SQL text that Postgres accepts and that leaves a routine or right the guard must refuse.
Prints for each: whether v16, v17 and v18 flag it; a check PASSES when v18 flags it (controls: v18 must NOT flag). Needs TWO arguments:
  python secdef_mutants_v18.py <held-sql folder> <product migrations folder>      (a missing argument stops the run with exit 2, v17 silently ran 25 of 30)
Also runs the 25 + 2 spellings of the v17 independent evidence runner (spellings.json, spellings2.json) and the parser tests P1, P2."""
import sys, glob, os, json
if len(sys.argv) != 3 or not all(os.path.isdir(a) for a in sys.argv[1:]):
    print("usage: secdef_mutants_v18.py <held-sql folder> <product migrations folder> (both must be existing folders)"); sys.exit(2)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import secdef_guard_v16 as g16, secdef_guard_v17 as g17, secdef_guard_v18 as g18
from allow_v18 import ALLOWED_BY_FILE
V17_ALLOWED = {"spend_log_decrease", "kill_switch_log_change", "spend_reserve", "spend_settle", "kill_switch_engage", "kill_switch_release"}
DB3 = "spend_guarded_writes.sql"; DB2 = "spend_decrease_log.sql"
RES = "spend_reserve(text,date,numeric)"; SET = "spend_settle(text,date,numeric,numeric)"; ENG = "kill_switch_engage()"; REL = "kill_switch_release()"
SP = "SET search_path = pg_catalog, pg_temp"
def rev(f, args=""): return f"REVOKE ALL ON FUNCTION {f}({args}) FROM PUBLIC;\n"
def fn(name="evil", args="", hdr=f"LANGUAGE sql SECURITY DEFINER {SP}", body="AS $f$ SELECT 1 $f$"): return f"CREATE OR REPLACE FUNCTION {name}({args}) RETURNS int {hdr} {body};\n"
RESERVE = f"CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE spend SET usd = usd + p_worst WHERE agent_id = p_agent; END;\n" + rev("spend_reserve", "text, date, numeric")
# (name, file, text, allowed-for-v18, expected: "flag" or "clean")
M = []
def add(n, text, allowed=None, file="x.sql", want="flag"): M.append((n, file, text, allowed if allowed is not None else {}, want))
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
add("K2 control: token only in a comment and in a string", "-- SECURITY DEFINER in a comment\nSELECT 'SECURITY DEFINER';\n", {}, "x.sql", "clean")
add("K3 control: an atomic body with CASE ... END and a second statement", f"CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE kill_switch SET \"on\" = CASE WHEN true THEN true ELSE false END; UPDATE kill_switch SET ts = now(); END;\n" + rev("kill_switch_engage"), {ENG: "definer"}, DB3, "clean")
add("K4 control: a listed invoker function (the DB-2 audit trigger)", "CREATE OR REPLACE FUNCTION audit_log_append_only() RETURNS trigger LANGUAGE plpgsql " + SP + " AS $f$ BEGIN RAISE EXCEPTION '% is append-only', TG_TABLE_NAME USING ERRCODE = '42501'; END $f$;\n", ALLOWED_BY_FILE[DB2], DB2, "clean")
# the independent runner's spellings
for fname in ("spellings.json", "spellings2.json"):
    for k, txt in json.load(open(os.path.join(HERE, fname))).items():
        if k.startswith("C1") or k.startswith("C2"): continue
        add("R" + k, txt, {RES: "definer"} if k.startswith("25") else {}, DB3 if k.startswith("25") else "x.sql", "flag")
ok = bad = 0; v17_miss = 0; v16_miss = 0
for n, file, text, allowed, want in M:
    p18 = g18.check_sql_text(file, text, allowed)
    try: p17 = g17.check_sql_text(file, text, V17_ALLOWED)
    except Exception as e: p17 = ["crash " + type(e).__name__]
    try: p16 = g16.check_sql_text(file, text, V17_ALLOWED)
    except Exception as e: p16 = ["crash " + type(e).__name__]
    good = bool(p18) if want == "flag" else not p18
    ok += good; bad += not good
    miss17 = want == "flag" and not p17; v17_miss += miss17; v16_miss += want == "flag" and not p16
    print(("PASS " if good else "FAIL ") + f"{n}: v18 flags={len(p18)} ; v17 flags={len(p17)} ; v16 flags={len(p16)}" + ("  (v17 MISSES it)" if miss17 else "") + (f"  [{p18[0][:90]}]" if p18 and not good else ""))
# parser tests (a statement count that v17 gets wrong)
T = f"CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE k SET a = CASE WHEN true THEN 1 ELSE 2 END; UPDATE k SET b = 1; END;\nSELECT 1;\n"
n17 = len(g17.statements(g17.strip_comments(T))); n18 = len(g18.split_statements(g18.tokenize(T)))
for name, ok_, d in (("P1 BEGIN ATOMIC with CASE ... END is ONE statement (plus the SELECT: 2 in all)", n18 == 2, f"v18={n18} v17={n17}"), ("P2 a quoted name with -- and /* leaves the next statement visible", len(g18.split_statements(g18.tokenize('CREATE TABLE "a--b" (x int);\nCREATE TABLE "c/*" (y int);\nSELECT 1;\n'))) == 3, "v18 sees 3 statements")):
    ok += ok_; bad += not ok_; print(("PASS " if ok_ else "FAIL ") + name + f" [{d}]")
folder1, folder2 = sys.argv[1], sys.argv[2]
for f in sorted(glob.glob(os.path.join(folder1, "*.sql")) + glob.glob(os.path.join(folder2, "*.sql"))):
    b = os.path.basename(f); p = g18.check_sql_text(b, open(f).read(), ALLOWED_BY_FILE.get(b, {}))
    ok += not p; bad += bool(p); print(("PASS " if not p else "FAIL ") + f"real file {b}: {p}")
print(f"{ok} checks passed, {bad} failed; mutants the v17 guard misses: {v17_miss}; the v16 guard misses: {v16_miss}")
sys.exit(1 if bad else 0)
