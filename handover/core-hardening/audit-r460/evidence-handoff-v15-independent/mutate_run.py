"""Plant mutations on scratch copies of the held SQL and run suite_indep.sh on each. Usage: python3 -B -I mutate_run.py <out_file>"""
import os, shutil, subprocess, sys, tempfile, re
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "orig-sql")
N, V, L = "spend_nonneg.sql", "spend_nonneg_finite.sql", "spend_decrease_log.sql"
# (id, file, old, new, count_expected)
M = [
 ("M01 default: drop spend CHECK line", N, "ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0);\n", "", 1),
 ("M02 default: drop spend_month CHECK line", N, "ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0);\n", "", 1),
 ("M03 default: >= 0 becomes > 0 (spend)", N, "spend_usd_ok CHECK (usd >= 0)", "spend_usd_ok CHECK (usd > 0)", 1),
 ("M04 default: >= 0 becomes >= -1 (month)", N, "spend_month_usd_ok CHECK (usd >= 0)", "spend_month_usd_ok CHECK (usd >= -1)", 1),
 ("M05 default: flip sign >= to <= (spend)", N, "spend_usd_ok CHECK (usd >= 0)", "spend_usd_ok CHECK (usd <= 0)", 1),
 ("M06 default: drop SET LOCAL lock_timeout", N, "SET LOCAL lock_timeout = '5s';\n", "", 1),
 ("M07 default: lock_timeout 5s becomes 60s", N, "lock_timeout = '5s'", "lock_timeout = '60s'", 1),
 ("M08 default: CHECK made vacuous (OR true, month)", N, "spend_month_usd_ok CHECK (usd >= 0)", "spend_month_usd_ok CHECK (usd >= 0 OR true)", 1),
 ("M09 variant: drop < Infinity (spend)", V, "spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric)", "spend_usd_ok CHECK (usd >= 0)", 1),
 ("M10 variant: < Infinity becomes <= Infinity (month)", V, "spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric)", "spend_month_usd_ok CHECK (usd >= 0 AND usd <= 'Infinity'::numeric)", 1),
 ("M11 variant: drop usd >= 0 part (spend)", V, "spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric)", "spend_usd_ok CHECK (usd < 'Infinity'::numeric)", 1),
 ("M12 variant: AND becomes OR (month)", V, "spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric)", "spend_month_usd_ok CHECK (usd >= 0 OR usd < 'Infinity'::numeric)", 1),
 ("M13 variant: drop month constraint", V, "ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);\n", "", 1),
 ("M14 variant: drop lock_timeout", V, "SET LOCAL lock_timeout = '5s';\n", "", 1),
 ("M15 log: drop REVOKE ALL ON FUNCTION FROM PUBLIC", L, "REVOKE ALL ON FUNCTION spend_log_decrease() FROM PUBLIC;\n", "", 1),
 ("M16 log: REVOKE replaced by GRANT ALL TO PUBLIC", L, "REVOKE ALL ON FUNCTION spend_log_decrease() FROM PUBLIC;", "GRANT ALL ON FUNCTION spend_log_decrease() TO PUBLIC;", 1),
 ("M17 log: search_path pg_temp first (log function)", L, "SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF TG_TABLE_NAME = 'spend' THEN\n    EXECUTE", "SET search_path = pg_temp, pg_catalog AS $f$\nBEGIN\n  IF TG_TABLE_NAME = 'spend' THEN\n    EXECUTE", 1),
 ("M18 log: drop pg_temp from path (implicit temp-first)", L, "SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF TG_TABLE_NAME = 'spend' THEN\n    EXECUTE", "SET search_path = pg_catalog AS $f$\nBEGIN\n  IF TG_TABLE_NAME = 'spend' THEN\n    EXECUTE", 1),
 ("M19 log: drop SET search_path of log function (v13 shape)", L, "LANGUAGE plpgsql SECURITY DEFINER\nSET search_path = pg_catalog, pg_temp AS $f$", "LANGUAGE plpgsql SECURITY DEFINER AS $f$", 1),
 ("M20 log: drop SECURITY DEFINER", L, "LANGUAGE plpgsql SECURITY DEFINER", "LANGUAGE plpgsql", 1),
 ("M21 log: trigger condition NEW < OLD becomes NEW > OLD (spend)", L, "CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW\n  WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd < OLD.usd", "CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW\n  WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd > OLD.usd", 1),
 ("M22 log: drop >= Infinity clause (month)", L, "CREATE TRIGGER spend_month_log_decrease AFTER UPDATE ON spend_month FOR EACH ROW\n  WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd < OLD.usd OR NEW.usd >= 'Infinity'::numeric))", "CREATE TRIGGER spend_month_log_decrease AFTER UPDATE ON spend_month FOR EACH ROW\n  WHEN (NEW.usd IS DISTINCT FROM OLD.usd AND (NEW.usd < OLD.usd))", 1),
 ("M23 log: drop spend key-guard trigger", L, "CREATE TRIGGER spend_keep_keys BEFORE UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();\n", "", 1),
 ("M24 log: drop month key-guard trigger", L, "CREATE TRIGGER spend_month_keep_keys BEFORE UPDATE ON spend_month FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();\n", "", 1),
 ("M25 log: add GRANT ALL on the log TO PUBLIC", L, "CREATE INDEX spend_decrease_log_by_agent", "GRANT ALL ON spend_decrease_log TO PUBLIC;\nCREATE INDEX spend_decrease_log_by_agent", 1),
 ("M26 log: old/new swapped in the spend insert", L, "USING OLD.agent_id, OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd;", "USING OLD.agent_id, OLD.day, TG_TABLE_NAME, NEW.usd, OLD.usd;", 1),
 ("M27 log: who default session_user becomes current_user", L, "DEFAULT session_user", "DEFAULT current_user", 1),
 ("M28 log: key guard ignores day change", L, "OR NEW.day IS DISTINCT FROM OLD.day THEN", "THEN", 1),
 ("M29 log: key guard ERRCODE 42501 becomes P0001", L, "'spend key columns may not change' USING ERRCODE = '42501';\n    END IF;\n  ELSE", "'spend key columns may not change' USING ERRCODE = 'P0001';\n    END IF;\n  ELSE", 1),
 ("M30 log: drop the index", L, "CREATE INDEX spend_decrease_log_by_agent ON spend_decrease_log (agent_id, period, at);\n", "", 1),
 ("M31 log: key guard function gets search_path pg_temp first", L, "RETURNS trigger LANGUAGE plpgsql\nSET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF TG_TABLE_NAME = 'spend' THEN\n    IF NEW.agent_id", "RETURNS trigger LANGUAGE plpgsql\nSET search_path = pg_temp, pg_catalog AS $f$\nBEGIN\n  IF TG_TABLE_NAME = 'spend' THEN\n    IF NEW.agent_id", 1),
 ("M32 log: month scope row stores NEW as old (month insert)", L, "USING OLD.agent_id, OLD.month, TG_TABLE_NAME, OLD.usd, NEW.usd;", "USING OLD.agent_id, OLD.month, TG_TABLE_NAME, NEW.usd, NEW.usd;", 1),
 ("M33 log: audit-relevant: log column scope stores wrong period (day for month)", L, "USING OLD.agent_id, OLD.month, TG_TABLE_NAME", "USING OLD.agent_id, OLD.month + 1, TG_TABLE_NAME", 1),
]
out = open(sys.argv[1], "w"); caught = 0
for mid, fn, old, new, cnt in M:
    d = tempfile.mkdtemp(prefix="mut_"); 
    for f in os.listdir(SRC): shutil.copy(os.path.join(SRC, f), d)
    p = os.path.join(d, fn); t = open(p).read()
    assert t.count(old) == cnt, (mid, t.count(old))
    open(p, "w").write(t.replace(old, new))
    os.chmod(d, 0o755)
    for f in os.listdir(d): os.chmod(os.path.join(d, f), 0o644)
    lab = "m" + re.match(r"M(\d+)", mid).group(1)
    r = subprocess.run(["bash", os.path.join(HERE, "suite_indep.sh"), d, lab], capture_output=True, text=True)
    lines = r.stdout.splitlines(); fails = [l for l in lines if l.startswith("FAIL")]
    summ = [l for l in lines if l.startswith("SUMMARY")]
    is_caught = bool(fails) or r.returncode != 0
    caught += is_caught
    out.write(f"{mid}: {'CAUGHT' if is_caught else 'NOT CAUGHT'} ({summ[-1] if summ else 'no summary'}) failing_checks: {' ; '.join(l[5:].split('  [')[0][:60] for l in fails[:6])}{' ...' if len(fails)>6 else ''}\n"); out.flush()
    shutil.rmtree(d)
out.write(f"TOTAL mutations={len(M)} caught={caught}\n"); out.close()
