"""Per-file pins of v22 (= v21 plus DDL_PINS_BY_FILE, HELD_FILES and the new spend_reserve pin; built by make_allow_v22.py); v21 text follows. Per-file pins of v21 (v19 plus TRIGGER_PINS_BY_FILE, FN_PINS_BY_FILE, KINDS_BY_FILE; the fingerprints were printed by the guard from the files as read by the builder in this session; a changed file needs a new pin in the same commit, and the reviewer reads the file text, not the hash). ALLOWED_BY_FILE: functions (name(types) -> definer|invoker). ATOMIC_TABLES_BY_FILE: relations a BEGIN ATOMIC body may use.
EXTRA_BY_FILE: fingerprints (secdef_guard_v21.fingerprint) of one-off statements that match no shape. A file name that is not a key here gets NOTHING allowed
(fails closed): the move PR that renames a held file must rename its key in the same commit (the guard test names the file in every problem)."""
ALLOWED_BY_FILE = {
 "spend_decrease_log.sql": {"spend_keep_keys()": "invoker", "spend_log_decrease()": "definer", "kill_switch_log_change()": "definer", "kill_switch_log_insert()": "definer", "audit_log_append_only()": "invoker"},
 "spend_guarded_writes.sql": {"spend_reserve(text,date,numeric)": "definer", "spend_settle(text,date,numeric,numeric)": "definer", "kill_switch_engage()": "definer", "kill_switch_release()": "definer"},
 "0002_audit_chain.sql": {"hadavin_audit_append_only()": "invoker"},
}
ATOMIC_TABLES_BY_FILE = {"spend_guarded_writes.sql": {"spend", "spend_month", "kill_switch"}}
EXTRA_BY_FILE = {
 "spend_nonneg_upgrade.sql": {"d5cbfe6dc4f2d178", "f48b9856bb955ca1"},   # the two ALTER TABLE ... DROP CONSTRAINT x, ADD CONSTRAINT x statements
 "0003_approvals_tick.sql": {"4c1fc9f8ae5bb872", "77c500a59151f7d7", "49600395601567ac"},  # the duplicate-decision DELETE, the month-row backfill INSERT, the kill-switch row INSERT
}

D2, D3 = "spend_decrease_log.sql", "spend_guarded_writes.sql"
TRIGGER_PINS_BY_FILE = {
 "0002_audit_chain.sql": {"audit_entries_append_only": "d86c341917b5cfc1", "audit_checkpoints_append_only": "cba3e114832c94ad", "audit_entries_no_truncate": "f300d8388c969d01", "audit_checkpoints_no_truncate": "b33267f50db496d4"},
 D2: {"spend_keep_keys": "a6f7d6f9ba917964", "spend_month_keep_keys": "8c486769d333048a", "spend_log_decrease": "e8cf4bd012603eb4", "spend_month_log_decrease": "136a55e6536a7af5",
      "kill_switch_log_change": "948f8128dc48ba5d", "kill_switch_log_insert": "8b03d1ffda7cff94", "spend_decrease_log_append_only": "ec417102067f880c",
      "spend_decrease_log_no_truncate": "49dbf667e197105c", "kill_switch_log_append_only": "10aafa0f136357b0", "kill_switch_log_no_truncate": "23ff1591586b6622"},
}
FN_PINS_BY_FILE = {
 D2: {"spend_keep_keys()": "97f17e2a9c0e6dff", "spend_log_decrease()": "43b113a40cdc3fc4", "kill_switch_log_change()": "d244c7a3c273d5d0", "kill_switch_log_insert()": "77f061c184a4634c", "audit_log_append_only()": "d8a8c41428712207"},
 D3: {"spend_reserve(text,date,numeric)": "807cc71c5cb2fbbe", "spend_settle(text,date,numeric,numeric)": "43e12400d7d87f70", "kill_switch_engage()": "663a59304dcf8b5a", "kill_switch_release()": "d263b5f4c7095b7d"},
 "0002_audit_chain.sql": {"hadavin_audit_append_only()": "f9085f6d3ce7477f"},
}
# statement kinds a DEFINER body may use (F1 of the independent run of v19): everything else, DELETE, TRUNCATE, MERGE, COPY and WITH included, is a problem
KINDS_BY_FILE = {
 D2: {"spend_log_decrease()": {"INSERT"}, "kill_switch_log_change()": {"INSERT"}, "kill_switch_log_insert()": {"INSERT"}},
 D3: {"spend_reserve(text,date,numeric)": {"INSERT", "UPDATE", "SELECT"}, "spend_settle(text,date,numeric,numeric)": {"UPDATE", "SELECT"},
      "kill_switch_engage()": {"INSERT", "UPDATE"}, "kill_switch_release()": {"UPDATE"}},
}
DDL_PINS_BY_FILE = {'spend_decrease_log.sql': ['2b17b76970b59b6f', 'a66ca870762f3594', 'adbcef933462c06e', 'f8fb1c3f08c3f0e8'], 'spend_guarded_writes.sql': ['143a98d95ee24daa', '156b2404645796e7', '2fb7d7520586cce1', '40282382be811a4c', '6657c5c86c8d7780', 'a85f18eea448552f', 'cc245308140cd057', 'e73eefd80fa153a4', 'f4bf6b54018ba5d4', 'ffc11090e7a5b422'], 'spend_nonneg.sql': ['218ca1805b82c990', '7c7f8e948a3d2ef2'], 'spend_nonneg_finite.sql': ['8029775c7249384d', 'd1acc8678c0e682d'], 'spend_nonneg_upgrade.sql': ['d5cbfe6dc4f2d178', 'f48b9856bb955ca1'], '0001_core.sql': ['08a4343775dca98d', '0ab347830e546b18', '0d13901451103311', '0dcba9ae546ac56f', '36abc8b54fff979e', '3d2739dc24f08674', '68f2ce921bcf939c', '8e85c436c3b0dbef', 'b883c19ada0e6898', 'cca48d79090ec2ed', 'cf6f35d6d7431c8c', 'f47d3b590be9da2a'], '0002_audit_chain.sql': ['23a5c7ffeb72792f', '42b496e2d249b6e6', '8340a389dbcce0fd', 'e6281bb0341d384a'], '0003_approvals_tick.sql': ['17518c60fa57cd55', '8f3b2aa88299afe8', 'aee58e14db999b66', 'b5ebf4270255744a', 'fd65e2dd0979b426'], '0004_audit_checkpoint_meta.sql': ['657eb87e277910fa', '99ad3d47854ede25'], '0005_evidence.sql': ['19e1ae983716759f', '8af748d999c432d1', 'd6fd181d7f2c8b16']}   # v22 m6: fingerprints of every ALTER TABLE ... ADD, CREATE TABLE, CREATE INDEX and COMMENT ON statement of a file (v21 pinned only ALTER TABLE ... ADD of the held files)
HELD_FILES = {"spend_nonneg.sql", "spend_nonneg_finite.sql", "spend_nonneg_upgrade.sql", "spend_decrease_log.sql", "spend_guarded_writes.sql"}

def check(g, name, text):
    """the one call every runner uses: the real file name picks every pin"""
    return g.check_sql_text(name, text, ALLOWED_BY_FILE.get(name, {}), extra_statements=EXTRA_BY_FILE.get(name, ()), atomic_tables=ATOMIC_TABLES_BY_FILE.get(name),
                            trigger_pins=TRIGGER_PINS_BY_FILE.get(name), fn_pins=FN_PINS_BY_FILE.get(name), kinds=KINDS_BY_FILE.get(name),
                            add_pins=(set(DDL_PINS_BY_FILE[name]) if name in DDL_PINS_BY_FILE else None),
                            require_lock_timeout=name in HELD_FILES, require_stmt_timeout=(name == D3))   # v22: a file name that is not a key gets NO pinned DDL (None = every one is a problem)
