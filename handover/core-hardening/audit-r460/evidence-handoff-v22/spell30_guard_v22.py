"""Runs the 30 spellings of the v18 independent runner (copy: spell30_runner_v18_copy.py, text of the cases taken unchanged from its lines 1-50) through the v18 and v22 guards.
Guard only, no Postgres. A case PASSES when v22 flags it. Usage: python spell30_guard_v22.py"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = ["x", "/nonexistent", os.path.join(HERE, "held-sql"), ""]
src = open(os.path.join(HERE, "spell30_runner_v18_copy.py")).read().split("res = []\nadm = psycopg.connect")[0]
src = src.replace("sys.path.insert(0, str(HELD18.parent))", "sys.path.insert(0, %r)" % HERE).replace("import secdef_guard_v18 as g\nfrom allow_v18 import ALLOWED_BY_FILE as A", "import secdef_guard_v18 as g\nfrom allow_v18 import ALLOWED_BY_FILE as A")
import types; sys.modules.setdefault("psycopg", types.ModuleType("psycopg"))  # the runner file imports it; this guard-only run never connects
ns = {"__name__": "x"}; exec(compile(src, "runner", "exec"), ns)
import secdef_guard_v22 as g19
from allow_v22 import ALLOWED_BY_FILE as A19, ATOMIC_TABLES_BY_FILE as T19, EXTRA_BY_FILE as X19
ok = bad = 0; v18miss = 0
for cid, file, text, what in ns["C"]:
    p19 = g19.check_sql_text(file, text, A19.get(file, {}), extra_statements=X19.get(file, ()), atomic_tables=T19.get(file))
    p18 = ns["g"].check_sql_text(file, text, ns["A"].get(file, {}))
    good = bool(p19); ok += good; bad += not good; v18miss += not p18
    print(("PASS " if good else "FAIL ") + f"{cid} {what}: v22 flags={len(p19)} v18 flags={len(p18)}" + ("  (v18 MISSES it)" if not p18 else ""))
print(f"SUMMARY {ok} of {ok + bad} spellings flagged by v22; the v18 guard misses {v18miss}")
sys.exit(1 if bad else 0)
