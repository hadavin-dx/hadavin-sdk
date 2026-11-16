"""Builds allow_v22.py from allow_v21.py (round 9). (1) the spend_reserve pin of the DB-3 file is replaced by the fingerprint the author READ in the v22 text (printed below; the final SELECT has the added guard `AND p_worst > 0`); every other pin is unchanged
(the tokenizer is the same, so the pins of v21 are the pins of v22: shown by the check at the end). (2) ADD_PINS_BY_FILE becomes DDL_PINS_BY_FILE: the fingerprints of every ALTER TABLE ... ADD, CREATE TABLE, CREATE INDEX and COMMENT ON statement of EVERY file
(the five held files and the product migrations 0001 to 0005). (3) check() passes the timeout requirements: both timeouts for the DB-3 file, lock_timeout for every held file. Prints the numbers."""
import re, os, sys, glob
sys.path.insert(0, ".")
import secdef_guard_v22 as g
t = open("allow_v21.py").read()
MIG = "/home/user/hadavin-sdk/src/hadavin_sdk/store/migrations"
files = {os.path.basename(f): f for f in sorted(glob.glob("held-sql/*.sql")) + sorted(glob.glob(MIG + "/*.sql"))}
# (1) the reserve pin
txt3 = open("held-sql/spend_guarded_writes.sql").read()
new_res = [g.fingerprint(s) for s in g.split_statements(g.tokenize(txt3)) if g._lead(s)[:4] == ["CREATE", "OR", "REPLACE", "FUNCTION"] and "spend_reserve" in g._flat(s)[:60]]
assert len(new_res) == 1
old_res = re.search(r'"spend_reserve\(text,date,numeric\)": "([0-9a-f]{16})"', t.split("FN_PINS_BY_FILE = ")[1]).group(1)
print("spend_reserve pin", old_res, "->", new_res[0])
assert t.count(old_res) == 1
t = t.replace(old_res, new_res[0])
# (2) DDL pins
pins = {}
for b, f in files.items():
    fp = set()
    for st in g.split_statements(g.tokenize(open(f).read())):
        L = g._lead(st)
        if (L[:2] == ["ALTER", "TABLE"] and any(g._is(x, "ADD") for x in st)) or (L[:1] == ["COMMENT"]) or (L[:1] == ["CREATE"] and ("INDEX" in L[:4] or (("TABLE" in L[:4]) and "FUNCTION" not in L[:4] and "TRIGGER" not in L[:4]))):
            fp.add(g.fingerprint(st))
    if fp: pins[b] = sorted(fp)
i = t.index("ADD_PINS_BY_FILE = ")
j = t.index("\ndef check(g, name, text):")
t = t[:i] + "DDL_PINS_BY_FILE = " + repr(pins) + "   # v22 m6: fingerprints of every ALTER TABLE ... ADD, CREATE TABLE, CREATE INDEX and COMMENT ON statement of a file (v21 pinned only ALTER TABLE ... ADD of the held files)\nHELD_FILES = {\"spend_nonneg.sql\", \"spend_nonneg_finite.sql\", \"spend_nonneg_upgrade.sql\", \"spend_decrease_log.sql\", \"spend_guarded_writes.sql\"}\n" + t[j:]
t = t.replace("add_pins=(set(ADD_PINS_BY_FILE[name]) if name in ADD_PINS_BY_FILE else None))",
              "add_pins=(set(DDL_PINS_BY_FILE[name]) if name in DDL_PINS_BY_FILE else None),\n                            require_lock_timeout=name in HELD_FILES, require_stmt_timeout=(name == D3))   # v22: a file name that is not a key gets NO pinned DDL (None = every one is a problem)")
assert "DDL_PINS_BY_FILE[name]" in t
t = t.replace('"""Per-file pins of v21', '"""Per-file pins of v22 (= v21 plus DDL_PINS_BY_FILE, HELD_FILES and the new spend_reserve pin; built by make_allow_v22.py); v21 text follows. Per-file pins of v21', 1)
open("allow_v22.py", "w").write(t)
print("DDL pins", {k: len(v) for k, v in pins.items()}, "total", sum(len(v) for v in pins.values()))
