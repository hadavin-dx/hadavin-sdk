"""Independent spellings test of secdef_guard_v18 (EVIDENCE RUNNER, written by the runner, not the builder). 30 NEW spellings.
For each: (1) does the v18 guard flag it (problems list non-empty); (2) does Postgres 16 ACCEPT the text; (3) what is the effect
in the database (a SECURITY DEFINER routine exists / PUBLIC may run a new routine / a default privilege for PUBLIC exists / a routine
changed owner or search_path). A MISS = Postgres accepted it AND an effect appeared AND the guard said clean. Records, never judges.
Usage: python spell30_v18.py <socket_dir> <src_dir> <held18> <held16>   (HV_ADMIN_PW in the environment)"""
import sys, os, json
from pathlib import Path
sock = sys.argv[1]; HELD18 = Path(sys.argv[3])
sys.path.insert(0, str(HELD18.parent))
import psycopg
import secdef_guard_v18 as g
from allow_v18 import ALLOWED_BY_FILE as A
SP = "SET search_path = pg_catalog, pg_temp"
RV = lambda f: f"REVOKE ALL ON FUNCTION {f} FROM PUBLIC;\n"
DB3, DB2, X = "spend_guarded_writes.sql", "spend_decrease_log.sql", "x.sql"
C = []  # (id, file, text, what)
def add(i, what, text, file=X): C.append((i, file, text, what))
# --- dynamic SQL inside DO / procedures (Class A)
add("N01", "DO, token joined with ||", "DO $$ BEGIN EXECUTE 'CREATE FUNCTION n01() RETURNS int LANGUAGE sql SECURITY ' || 'DEFINER AS ''SELECT 1'''; END $$;")
add("N02", "DO, format with %s", "DO $$ BEGIN EXECUTE format('CREATE FUNCTION n02() RETURNS int LANGUAGE sql SECURITY %s AS $q$SELECT 1$q$', 'DEFINER'); END $$;")
add("N03", "DO, format with %I (lower-case word stays unquoted)", "DO $$ BEGIN EXECUTE format('CREATE FUNCTION n03() RETURNS int LANGUAGE sql SECURITY %I AS $q$SELECT 1$q$', 'definer'); END $$;")
add("N04", "DO, format with %L on ALTER (value 'x')", "DO $$ BEGIN EXECUTE format('ALTER FUNCTION base_f() SET search_path = %L', 'public'); END $$;")
add("N05", "DO, E-string with a hex escape for D", r"DO $$ BEGIN EXECUTE E'CREATE FUNCTION n05() RETURNS int LANGUAGE sql SECURITY \x44EFINER AS $q$SELECT 1$q$'; END $$;")
add("N06", "DO, chr() for D", "DO $$ BEGIN EXECUTE 'CREATE FUNCTION n06() RETURNS int LANGUAGE sql SECURITY ' || chr(68) || 'EFINER AS $q$SELECT 1$q$'; END $$;")
add("N07", "DO, nested dollar tags $a$ $b$ $c$", "DO $a$ BEGIN EXECUTE $b$CREATE FUNCTION n07() RETURNS int LANGUAGE sql SECURITY DEFINER AS $c$SELECT 1$c$$b$; END $a$;")
add("N08", "DO LANGUAGE plpgsql form (word order)", "DO LANGUAGE plpgsql $$ BEGIN EXECUTE 'CREATE FUNCTION n08() RETURNS int LANGUAGE sql SECURITY DEFINER AS $q$SELECT 1$q$'; END $$;")
add("N09", "procedure (invoker) that runs dynamic SQL, then CALL", "CREATE OR REPLACE PROCEDURE n09p() LANGUAGE plpgsql AS $$ BEGIN EXECUTE 'CREATE FUNCTION n09() RETURNS int LANGUAGE sql SECURITY DEFINER AS $q$SELECT 1$q$'; END $$;\nCALL n09p();")
add("N10", "function in an ALLOWED file: invoker list, body creates definer via format %s", "CREATE OR REPLACE FUNCTION spend_keep_keys() RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, pg_temp AS $f$ BEGIN EXECUTE format('CREATE FUNCTION n10() RETURNS int LANGUAGE sql SECURITY %s AS $q$SELECT 1$q$', 'DEFINER'); RETURN NEW; END $f$;", DB2)
# --- tokenizer (Class B)
add("N11", "double-quoted name containing --", 'CREATE OR REPLACE FUNCTION "n--11"() RETURNS int LANGUAGE sql SECURITY DEFINER ' + SP + " AS 'SELECT 1';\n" + RV('"n--11"()'))
add("N12", "double-quoted name containing /*", 'CREATE OR REPLACE FUNCTION "n/*12"() RETURNS int LANGUAGE sql SECURITY DEFINER ' + SP + " AS 'SELECT 1'; /* closes */\n" + RV('"n/*12"()'))
add("N13", "comment between SECURITY and DEFINER (block)", "CREATE OR REPLACE FUNCTION n13() RETURNS int LANGUAGE sql SECURITY/**/DEFINER " + SP + " AS 'SELECT 1';\n" + RV("n13()"))
add("N14", "line comment between tokens", "CREATE OR REPLACE FUNCTION n14() RETURNS int LANGUAGE sql SECURITY --x\n DEFINER " + SP + " AS 'SELECT 1';\n" + RV("n14()"))
add("N15", "nested block comment between tokens", "CREATE OR REPLACE FUNCTION n15() RETURNS int LANGUAGE sql SECURITY /* a /* b */ c */ DEFINER " + SP + " AS 'SELECT 1';\n" + RV("n15()"))
add("N16", "standard string ending in a backslash hides the next statement from a backslash-aware scanner", r"SELECT 'a\'; CREATE OR REPLACE FUNCTION n16() RETURNS int LANGUAGE sql SECURITY DEFINER " + SP + " AS 'SELECT 1'; SELECT 'b';" + "\n" + RV("n16()"))
add("N17", "form feed and vertical tab as whitespace inside SECURITY<FF>DEFINER", "CREATE OR REPLACE FUNCTION n17() RETURNS int LANGUAGE sql SECURITY\x0cDEFINER " + SP + " AS 'SELECT 1';\n" + RV("n17()"))
add("N18", "unicode-escape function name U&\"n\\0031\\0038\"", 'CREATE OR REPLACE FUNCTION U&"n\\0031\\0038"() RETURNS int LANGUAGE sql SECURITY DEFINER ' + SP + " AS 'SELECT 1';\n" + RV("n18()"))
add("N19", "mixed case SeCuRiTy DeFiNeR and quoted language", "CREATE OR REPLACE FUNCTION n19() RETURNS int LANGUAGE sql SeCuRiTy DeFiNeR " + SP + " AS 'SELECT 1';\n" + RV("n19()"))
add("N20", "name with a dollar sign n$20$ (looks like a dollar quote start)", "CREATE OR REPLACE FUNCTION n$20$() RETURNS int LANGUAGE sql SECURITY DEFINER " + SP + " AS 'SELECT 1';\n" + RV("n$20$()"))
# --- ALTER / grants / overloads (Class C)
add("N21", "ALTER FUNCTION ... SET search_path (public)", "ALTER FUNCTION spend_reserve(text, date, numeric) SET search_path = public;", DB3)
add("N22", "ALTER ROUTINE ... SECURITY DEFINER", "ALTER ROUTINE base_f() SECURITY DEFINER;")
add("N23", "ALTER FUNCTION ... OWNER TO", "ALTER FUNCTION base_f() OWNER TO CURRENT_USER;")
add("N24", "second overload, no REVOKE (int in place of numeric)", "CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst int) RETURNS void LANGUAGE sql SECURITY DEFINER " + SP + " AS 'SELECT 1';", DB3)
add("N25", "same signature written with a typmod numeric(10,2) and decimal alias (replaces the body of an allowed function)", "CREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst decimal(10,2)) RETURNS TABLE (day_usd numeric, month_usd numeric) LANGUAGE sql SECURITY DEFINER " + SP + " BEGIN ATOMIC SELECT 0::numeric, 0::numeric; END;\n" + RV("spend_reserve(text, date, numeric)"), DB3)
add("N26", "ALTER DEFAULT PRIVILEGES EXECUTE to PUBLIC", "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO PUBLIC;")
add("N27", "ALTER DEFAULT PRIVILEGES with comment between words", "ALTER/**/DEFAULT /**/PRIVILEGES GRANT EXECUTE ON FUNCTIONS TO PUBLIC;")
add("N28", "GRANT hidden after a comment-only line", "-- harmless\nGRANT EXECUTE ON FUNCTION spend_settle(text,date,numeric,numeric) TO PUBLIC;", DB3)
add("N29", "SET LOCAL ROLE before a CREATE (runs the rest as another role)", "SET LOCAL ROLE postgres;\nCREATE OR REPLACE FUNCTION n29() RETURNS int LANGUAGE sql SECURITY INVOKER AS 'SELECT 1';")
add("N30", "view (runs with owner rights, a definer-like object) over spend plus no grant", "CREATE VIEW n30v AS SELECT * FROM t;")
res = []
adm = psycopg.connect(f"host={sock} dbname=postgres user=postgres password={os.environ['HV_ADMIN_PW']}", autocommit=True)
adm.execute("CREATE DATABASE sp30")
SETUP = ("CREATE TABLE t(a int); CREATE FUNCTION base_f() RETURNS int LANGUAGE sql AS 'SELECT 1';"
         "CREATE FUNCTION spend_reserve(text,date,numeric) RETURNS void LANGUAGE sql AS 'SELECT 1'; CREATE FUNCTION spend_keep_keys() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN RETURN NEW; END $f$;"
         "CREATE FUNCTION spend_settle(text,date,numeric,numeric) RETURNS void LANGUAGE sql AS 'SELECT 1';")
STATE = ("SELECT (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND prosecdef),"
         "(SELECT count(*) FROM pg_proc p WHERE pronamespace='public'::regnamespace AND EXISTS (SELECT 1 FROM aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE') AND p.prosecdef),"
         "(SELECT count(*) FROM pg_default_acl),"
         "(SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proconfig IS NOT NULL AND proconfig::text LIKE '%public%'),"
         "(SELECT count(*) FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner WHERE pronamespace='public'::regnamespace AND r.rolname<>'postgres'),"
         "(SELECT count(*) FROM pg_class WHERE relkind='v' AND relnamespace='public'::regnamespace),"
         "(SELECT count(*) FROM pg_proc p WHERE pronamespace='public'::regnamespace AND p.proname<>'base_f' AND EXISTS (SELECT 1 FROM aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE'))")
NAMES = ("secdef routines", "of those PUBLIC may run", "default-ACL rows", "routines with search_path naming public", "routines owned by a non-postgres role", "views", "routines PUBLIC may run (all)")
for cid, file, text, what in C:
    allowed = A.get(file, {})
    problems = g.check_sql_text(file, text, allowed)
    c = psycopg.connect(f"host={sock} dbname=sp30 user=postgres password={os.environ['HV_ADMIN_PW']}", autocommit=True)
    c.execute("BEGIN"); c.execute(SETUP)
    # unlisted baseline: SETUP functions have PUBLIC exec; effect is measured as DELTA
    b = c.execute(STATE).fetchone()
    err = None
    try: c.execute(text)
    except psycopg.Error as e: err = f"{e.sqlstate} {str(e).splitlines()[0][:70]}"
    a = None if err else c.execute(STATE).fetchone()
    c.execute("ROLLBACK"); c.close()
    delta = {} if a is None else {NAMES[i]: f"{b[i]}->{a[i]}" for i in range(len(b)) if a[i] != b[i]}
    # a "secdef effect" = the count of secdef routines grew, or a routine's search_path now names public, or a default ACL appeared, or a view exists
    eff = a is not None and (a[0] > b[0] or a[3] > b[3] or a[2] > b[2] or a[5] > b[5] or a[1] > b[1])
    miss = (a is not None) and eff and not problems
    res.append((cid, miss))
    print(f"{cid} | {what} | guard_flagged={bool(problems)} | postgres={'REJECTED ' + err if err else 'accepted'} | effect={delta or 'none'} | {'MISS' if miss else ('flagged' if problems else ('clean-no-effect' if not eff else '??'))}", flush=True)
    if problems: print("      guard: " + problems[0][:140])
print(f"SUMMARY 30 spellings: guard flagged {sum(1 for c,*_ in C if g.check_sql_text(c and next(f for i,f,_,_ in C if i==c), next(t for i,_,t,_ in C if i==c), A.get(next(f for i,f,_,_ in C if i==c), {})))}; MISSES (accepted by Postgres, effect present, guard clean): {[c for c, m in res if m]}")
