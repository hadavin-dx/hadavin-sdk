"""Mutants for the v17 and v16 SECURITY DEFINER guards. Each MUTANT is a spelling the v16 guard missed (or a removed rule).
Prints, per mutant, whether v16 and v17 flag it; a check PASSES when v17 flags it. Real held files must give no problem (v17)."""
import sys, glob, os
sys.path.insert(0, os.path.dirname(__file__))
import secdef_guard_v16 as g16, secdef_guard_v17 as g17
ALLOWED = {"spend_log_decrease", "kill_switch_log_change", "spend_reserve", "spend_settle", "kill_switch_engage", "kill_switch_release"}
REV = "REVOKE ALL ON FUNCTION {f}() FROM PUBLIC;\n"
def trig(f="spend_log_decrease", hdr="LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp", body="BEGIN EXECUTE format('INSERT INTO %I.t VALUES (1)', TG_TABLE_SCHEMA); RETURN NULL; END", pre="CREATE OR REPLACE FUNCTION {f}() RETURNS trigger {hdr} AS $f$ {body} $f$;\n"):
    return pre.format(f=f, hdr=hdr, body=body) + REV.format(f=f)
SD, SP = "SECURITY DEFINER", "SET search_path = pg_catalog, pg_temp"
M = {
 "S01 attributes after the body": ("CREATE OR REPLACE FUNCTION evil() RETURNS trigger AS $f$ BEGIN RETURN NULL; END $f$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog;\n" + REV.format(f="evil"), ),
 "S02 single-quoted body": ("CREATE OR REPLACE FUNCTION evil() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS 'BEGIN INSERT INTO t VALUES (1); RETURN NULL; END';\n" + REV.format(f="evil"), ),
 "S03 BEGIN ATOMIC body, function not on the list": ("CREATE OR REPLACE FUNCTION evil() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp BEGIN ATOMIC UPDATE t SET a = 1; END;\n" + REV.format(f="evil"), ),
 "S04 schema-qualified name not on the list": ("CREATE OR REPLACE FUNCTION public.evil() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT 1 $f$;\n" + REV.format(f="evil"), ),
 "S05 ALTER FUNCTION ... SECURITY DEFINER": ("ALTER FUNCTION spend_keep_keys() SECURITY DEFINER;\n", ),
 "S06 CREATE PROCEDURE ... SECURITY DEFINER": ("CREATE PROCEDURE evil() LANGUAGE sql SECURITY DEFINER AS $f$ SELECT 1 $f$;\n", ),
 "S07 one %I. hides a bare table statement": (trig(body="BEGIN EXECUTE format('INSERT INTO %I.a VALUES (1)', TG_TABLE_SCHEMA); INSERT INTO spend_decrease_log VALUES (1); RETURN NULL; END"), ),
 "S08 a comment inside the token": (trig(hdr="LANGUAGE plpgsql SECURITY /* c */ DEFINER SET search_path = pg_catalog, pg_temp", f="evil"), ),
 "S09 newline and tab inside the token": (trig(hdr="LANGUAGE plpgsql SECURITY\n\tDEFINER SET search_path = pg_catalog, pg_temp", f="evil"), ),
 "S10 DO block that creates one": ("DO $x$ BEGIN EXECUTE 'CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY DEFINER AS ''SELECT 1'''; END $x$;\n", ),
 "S11 search_path without pg_temp last": (trig(hdr="LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_temp, pg_catalog"), ),
 "S12 search_path names public": (trig(hdr="LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_catalog, pg_temp"), ),
 "S13 no search_path at all": (trig(hdr="LANGUAGE plpgsql SECURITY DEFINER"), ),
 "S14 no REVOKE from PUBLIC": ("CREATE OR REPLACE FUNCTION spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ BEGIN RETURN NULL; END $f$;\n", ),
 "S15 GRANT EXECUTE to PUBLIC after the REVOKE": (trig() + "GRANT EXECUTE ON FUNCTION spend_log_decrease() TO PUBLIC;\n", ),
 "S16 lower-case token and name in a quoted identifier": ("create or replace function \"evil\"() returns int language sql security definer set search_path = pg_catalog, pg_temp as $f$ select 1 $f$;\nrevoke all on function evil() from public;\n", ),
 "S17 token in a function that is not OR REPLACE": ("CREATE FUNCTION evil() RETURNS int LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT 1 $f$;\n" + REV.format(f="evil"), ),
 "S18 EXECUTE of a concatenated string": (trig(body="BEGIN EXECUTE 'DELETE FROM ' || TG_TABLE_NAME; RETURN NULL; END"), ),
 "S19 bare UPDATE ONLY in a dollar body": (trig(body="BEGIN UPDATE ONLY spend SET usd = 0; RETURN NULL; END"), ),
 "S20 DB-3 style body without search_path": ("CREATE OR REPLACE FUNCTION kill_switch_engage() RETURNS void LANGUAGE sql SECURITY DEFINER BEGIN ATOMIC UPDATE kill_switch SET \"on\" = true; END;\n" + REV.format(f="kill_switch_engage"), ),
}
ok = bad = 0
for k, (txt,) in M.items():
    p16 = g16.check_sql_text("m.sql", txt, ALLOWED); p17 = g17.check_sql_text("m.sql", txt, ALLOWED)
    flag = "PASS" if p17 else "FAIL"; ok += bool(p17); bad += not p17
    print(f"{flag} {k}: v17 flags={len(p17)} ; v16 flags={len(p16)}" + ("  (v16 MISSES it)" if not p16 else ""))
folder = sys.argv[1] if len(sys.argv) > 1 else "held-sql"
real = []
for f in sorted(glob.glob(os.path.join(folder, "*.sql")) + glob.glob(os.path.join(sys.argv[2], "*.sql") if len(sys.argv) > 2 else "")):
    p = g17.check_sql_text(os.path.basename(f), open(f).read(), ALLOWED); real += p
    c = "PASS" if not p else "FAIL"; ok += not p; bad += bool(p)
    print(f"{c} real file {os.path.basename(f)}: {p}")
print(f"{ok} checks passed, {bad} failed")
sys.exit(1 if bad else 0)
