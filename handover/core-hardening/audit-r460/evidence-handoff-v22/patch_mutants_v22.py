"""Builds secdef_mutants_v22.py from secdef_mutants_v21.py: renames the variables that held the guard under test (g20, A20, p20 -> g22, A22, p22; v21 security minor m4), adds the v21 guard as gQ
(the column 'v21 flags'), keeps v20 as gP, and adds the v22 mutants V01 to V31. Every replacement is asserted."""
import re
s = open("secdef_mutants_v21.py").read()
def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80]); s = s.replace(old, new)
s = re.sub(r"\bg20\b", "g22", s); s = re.sub(r"\bA20\b", "A22", s); s = re.sub(r"\bp20\b", "p22", s)
rep("secdef_guard_v21 as g22, secdef_guard_v20 as gP", "secdef_guard_v22 as g22, secdef_guard_v20 as gP, secdef_guard_v21 as gQ")
rep("from secdef_guard_v21 import PIN_ANY", "from secdef_guard_v22 import PIN_ANY")
rep("import allow_v21 as A22, allow_v20 as AP", "import allow_v22 as A22, allow_v20 as AP, allow_v21 as AQ")
rep("from allow_v21 import ALLOWED_BY_FILE", "from allow_v22 import ALLOWED_BY_FILE")
rep('"""Mutants for the SECURITY DEFINER guards (v16 to v21; v21 is the guard under test (the variable names g22, A22, p22 still say 20: they now hold the v21 modules), the v20 column shows which new v21 mutants v20 misses).',
    '"""Mutants for the SECURITY DEFINER guards (v16 to v22; v22 is the guard under test (variables g22, A22, p22; gQ is the v21 guard, gP the v20 guard), the v21 column shows which new v22 mutants v21 misses).')
# default add_pins = PIN_ANY for unit mutants; "none" = None (the real caller for a file that is not a key); "req" = the timeout requirements
rep('''def realpins(file, o):
    if not o: return {"trigger_pins": PIN_ANY, "fn_pins": PIN_ANY, "kinds": PIN_ANY}
    r = {"trigger_pins": PIN_ANY, "fn_pins": PIN_ANY, "kinds": PIN_ANY}
    if o.get("add_pins") == "real": r["add_pins"] = set(A22.ADD_PINS_BY_FILE[file])''',
'''def realpinsQ(file, o):
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
    if o.get("add_pins") == "real": r["add_pins"] = set(A22.DDL_PINS_BY_FILE[file])''')
rep("new21_total = 0; new21_missP = 0", "new21_total = 0; new21_missP = 0; new22_total = 0; new22_missQ = 0")
rep('''    good = bool(p22) if want == "flag" else not p22''', '''    try: pQ = gQ.check_sql_text(file, text, allowed, extra_statements=AQ.EXTRA_BY_FILE.get(file, ()), atomic_tables=AQ.ATOMIC_TABLES_BY_FILE.get(file), **realpinsQ(file, OPTS.get(n)))
    except Exception as e: pQ = ["crash " + type(e).__name__]
    missQ = want == "flag" and not pQ
    if n in NEWMUT22 and want == "flag": new22_total += 1; new22_missQ += missQ
    good = bool(p22) if want == "flag" else not p22''')
rep('''f"{n}: v21 flags={len(p22)} ; v20 flags={len(pP)}"''', '''f"{n}: v22 flags={len(p22)} ; v21 flags={len(pQ)}" + ("  (v21 MISSES it)" if missQ and n in NEWMUT22 else "") + f" ; v20 flags={len(pP)}"''')
rep('''; of the {new21_total} NEW v21 mutants that must be flagged the v20 guard misses {new21_missP} and flags {new21_total - new21_missP}")''',
    '''; of the {new21_total} NEW v21 mutants that must be flagged the v20 guard misses {new21_missP} and flags {new21_total - new21_missP}; of the {new22_total} NEW v22 mutants that must be flagged the v21 guard misses {new22_missQ} and flags {new22_total - new22_missQ}")''')
NEW = r'''
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
'''
rep("# the independent runner's spellings\n", NEW + "\n# the independent runner's spellings\n")
rep('REAL = {"trigger_pins": "real", "fn_pins": "real", "kinds": "real"}', 'REAL = {"trigger_pins": "real", "fn_pins": "real", "kinds": "real"}\nREAL_V22 = {"trigger_pins": "real", "fn_pins": "real", "kinds": "real", "add_pins": "real"}')
open("secdef_mutants_v22.py", "w").write(s)
print("written")
