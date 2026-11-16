"""EVIDENCE RUNNER second pass: the listed function kill_switch_release is REPLACED (not appended) by a hostile definition, so the 'created twice' rule cannot mask the body checks.
usage: hostile_guard2_v19.py <evidence-handoff-v19 folder>"""
import sys, os, re
H = sys.argv[1]; sys.path.insert(0, H)
import secdef_guard_v19 as g
from allow_v19 import ALLOWED_BY_FILE as A, ATOMIC_TABLES_BY_FILE as T, EXTRA_BY_FILE as X
N = "spend_guarded_writes.sql"; t = open(os.path.join(H, "held-sql", N), encoding="utf-8").read()
i = t.index("CREATE OR REPLACE FUNCTION kill_switch_release()"); j = t.index("REVOKE ALL ON FUNCTION spend_reserve")
orig = t[i:j]; SP = "SET search_path = pg_catalog, pg_temp"
run = lambda s: g.check_sql_text(N, s, A[N], extra_statements=X.get(N, ()), atomic_tables=T.get(N))
V = {
 "R00 control: unchanged": orig,
 "R01 body deletes spend": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC DELETE FROM spend; END;\n",
 "R02 body touches unlisted table runs": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC DELETE FROM runs; END;\n",
 "R03 no search_path": "CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER BEGIN ATOMIC UPDATE kill_switch SET \"on\" = false WHERE id = 1; END;\n",
 "R04 search_path = public": "CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = public BEGIN ATOMIC UPDATE kill_switch SET \"on\" = false WHERE id = 1; END;\n",
 "R05 calls pg_read_file": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC SELECT pg_read_file('/etc/hostname'); END;\n",
 "R06 calls set_config": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC SELECT set_config('role','x',true); END;\n",
 "R07 plpgsql EXECUTE string": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS $f$ BEGIN EXECUTE 'DELETE FROM spend'; END $f$;\n",
 "R08 plpgsql EXECUTE format %s": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE plpgsql SECURITY DEFINER {SP} AS $f$ BEGIN EXECUTE format('DELETE FROM %s', 'spend'); END $f$;\n",
 "R09 extra SET role attribute": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER SET role = postgres {SP} BEGIN ATOMIC SELECT 1; END;\n",
 "R10 attribute LEAKPROOF": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER LEAKPROOF {SP} BEGIN ATOMIC UPDATE kill_switch SET \"on\" = false WHERE id = 1; END;\n",
 "R11 SECURITY INVOKER (listed as definer)": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY INVOKER {SP} BEGIN ATOMIC UPDATE kill_switch SET \"on\" = false WHERE id = 1; END;\n",
 "R12 schema-qualified table in body": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE other.kill_switch SET \"on\" = false WHERE id = 1; END;\n",
 "R13 body with subselect of unlisted table": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE kill_switch SET \"on\" = false WHERE id = (SELECT max(id) FROM runs); END;\n",
 "R14 body with CTE delete": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC WITH d AS (DELETE FROM spend RETURNING 1) SELECT 1; END;\n",
 "R15 body with TRUNCATE": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC TRUNCATE spend; END;\n",
 "R16 body calls query_to_xml": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC SELECT query_to_xml('select * from runs', true, false, ''); END;\n",
 "R17 uppercase quoted table \"KILL_SWITCH\"": f"CREATE OR REPLACE FUNCTION kill_switch_release() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC UPDATE \"KILL_SWITCH\" SET \"on\" = false; END;\n",
 "R18 function owner changed in same file": orig + "ALTER FUNCTION kill_switch_release() OWNER TO postgres;\n",
 "R19 REVOKE moved before CREATE": "REVOKE ALL ON FUNCTION kill_switch_release() FROM PUBLIC;\n" + orig.replace("REVOKE ALL ON FUNCTION kill_switch_release() FROM PUBLIC;\n", ""),
 "R20 REVOKE for release removed (PUBLIC keeps execute)": orig,  # handled below by deleting the REVOKE line from the whole file
}
ok = 0
for k, v in V.items():
    full = t[:i] + v + t[j:]
    if k.startswith("R20"): full = t.replace("REVOKE ALL ON FUNCTION kill_switch_release() FROM PUBLIC;", "")
    if k.startswith("R19"): full = t.replace("REVOKE ALL ON FUNCTION kill_switch_release() FROM PUBLIC;", "") .replace(orig, v)
    p = run(full); print(f"{k}: flagged={'Y' if p else 'N'} | {(p[0] if p else '')[:170]}")
