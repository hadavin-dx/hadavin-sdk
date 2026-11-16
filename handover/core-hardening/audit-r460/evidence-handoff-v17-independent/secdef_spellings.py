"""Independent spellings test for the v17 SECURITY DEFINER guard. Each case is a SQL text that Postgres would accept and that creates a
SECURITY DEFINER routine NOT on the declared list; the guard should flag it. Prints FLAGGED / MISSED per case plus the guard's message.
Controls: a text with SECURITY INVOKER must not be flagged. Postgres validity of each spelling is checked separately (pg_validate.py)."""
import sys
sys.path.insert(0, sys.argv[1])
import secdef_guard_v17 as g
ALLOWED = {"spend_log_decrease", "kill_switch_log_change", "spend_reserve", "spend_settle", "kill_switch_engage", "kill_switch_release"}
REV = "REVOKE ALL ON FUNCTION {n}() FROM PUBLIC;\n"
SP = "SET search_path = pg_catalog, pg_temp"
def fn(name="evil", tok="SECURITY DEFINER", pre="CREATE OR REPLACE FUNCTION", rev=None, body="AS 'SELECT 1'"):
    return f"{pre} {name}() RETURNS int LANGUAGE sql {tok} {SP} {body};\n" + (REV.format(n=rev or name.strip('"').split('.')[-1]))
C = {
 "01 quoted mixed-case name \"Evil\"": fn('"Evil"'),
 "02 schema-qualified public.evil": fn("public.evil"),
 "03 CREATE FUNCTION (no OR REPLACE)": fn(pre="CREATE FUNCTION"),
 "04 ALTER FUNCTION evil() SECURITY DEFINER": "ALTER FUNCTION evil() SECURITY DEFINER;\n",
 "05 mixed case SeCuRiTy dEfInEr": fn(tok="SeCuRiTy dEfInEr"),
 "06 block comment between words": fn(tok="SECURITY /* x */ DEFINER"),
 "07 line comment between words": fn(tok="SECURITY -- x\n DEFINER"),
 "08 nested block comment between words": fn(tok="SECURITY /* a /* b */ c */ DEFINER"),
 "09 unicode-escaped identifier U&\"ev\\0069l\"": fn('U&"ev\\0069l"'),
 "10 odd dollar tag $a_1$ body": "CREATE OR REPLACE FUNCTION evil() RETURNS int LANGUAGE plpgsql SECURITY DEFINER " + SP + " AS $a_1$ BEGIN RETURN 1; END $a_1$;\n" + REV.format(n="evil"),
 "11 token only in a DO block string (CREATE FUNCTION via EXECUTE)": "DO $$ BEGIN EXECUTE 'CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY DEFINER AS $x$ SELECT 1 $x$'; END $$;\n",
 "12 token built by concatenation in a DO block": "DO $$ BEGIN EXECUTE 'CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY ' || 'DEF' || 'INER AS $x$ SELECT 1 $x$'; END $$;\n",
 "13 token built with format('%s') in a DO block": "DO $$ BEGIN EXECUTE format('CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY %s AS $x$ SELECT 1 $x$', 'DEFINER'); END $$;\n",
 "14 token via E'' unicode escape in a DO block": "DO $$ BEGIN EXECUTE E'CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY\\u0020DEFINER AS $x$ SELECT 1 $x$'; END $$;\n",
 "15 token via chr(32) in a DO block": "DO $$ BEGIN EXECUTE 'CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY' || chr(32) || 'DEFINER AS $x$ SELECT 1 $x$'; END $$;\n",
 "16 CREATE PROCEDURE": fn(pre="CREATE PROCEDURE").replace("RETURNS int ", ""),
 "17 ALTER ROUTINE evil() SECURITY DEFINER": "ALTER ROUTINE evil() SECURITY DEFINER;\n",
 "18 tab and newlines inside the token": fn(tok="SECURITY\t\n\r DEFINER"),
 "19 double-quoted name containing '--' (guard comment-strip is not quote-aware?)": "CREATE OR REPLACE FUNCTION \"x--y\"() RETURNS int LANGUAGE sql SECURITY DEFINER " + SP + " AS 'SELECT 1';\n" + REV.format(n="\"x--y\"").replace('"x--y"', '"x--y"'),
 "20 double-quoted name containing '/*' (opens guard block comment)": "CREATE OR REPLACE FUNCTION \"x/*y\"() RETURNS int LANGUAGE sql SECURITY DEFINER " + SP + " AS 'SELECT 1';\nSELECT 1; -- */\n",
 "21 double-quoted name with -- , token AFTER it on the same line": "CREATE OR REPLACE FUNCTION \"a--\"() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1';\n",
 "22 unquoted name with $tag$ shape: evil$q$": "CREATE OR REPLACE FUNCTION evil$q$() RETURNS int LANGUAGE sql SECURITY DEFINER " + SP + " AS 'SELECT 1';\nSELECT $q$ x $q$;\n",
 "23 E'' string with \\' hiding a statement boundary": "SELECT E'\\'';\nCREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1';\nSELECT 'x';\n",
 "24 token in statement preceded by a legit declared function (same statement via BEGIN ATOMIC mimic)": "CREATE OR REPLACE FUNCTION spend_reserve() RETURNS void LANGUAGE sql SECURITY DEFINER " + SP + " BEGIN ATOMIC SELECT 1; END;\nCREATE FUNCTION evil() RETURNS void LANGUAGE sql SECURITY DEFINER BEGIN ATOMIC SELECT 1; END;\n" + REV.format(n="spend_reserve"),
 "25 SECURITY DEFINER declared-name function but a 2nd same-named overload with other args": "CREATE OR REPLACE FUNCTION spend_reserve(int) RETURNS int LANGUAGE sql SECURITY DEFINER " + SP + " AS 'SELECT 1';\nREVOKE ALL ON FUNCTION spend_reserve(text) FROM PUBLIC;\n",
}
CONTROLS = {
 "C1 SECURITY INVOKER function": fn(tok="SECURITY INVOKER"),
 "C2 token only in a comment": "-- SECURITY DEFINER\nSELECT 1;\n",
}
ALLOWED_NAMES = ALLOWED
flagged = missed = 0
for k, t in C.items():
    p = g.check_sql_text("x.sql", t, ALLOWED)
    if p: flagged += 1
    else: missed += 1
    print(("FLAGGED " if p else "MISSED  ") + k + ("  -> " + p[0][:110] if p else ""))
for k, t in CONTROLS.items():
    p = g.check_sql_text("x.sql", t, ALLOWED); print(("CONTROL-OK " if not p else "CONTROL-FALSE-POSITIVE ") + k + str(p[:1]))
print(f"SUMMARY spellings={len(C)} flagged={flagged} missed={missed}")
import json; json.dump(C, open(sys.argv[2], "w"))
