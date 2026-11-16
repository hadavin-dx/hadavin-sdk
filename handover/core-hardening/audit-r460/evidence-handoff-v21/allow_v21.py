"""Per-file pins of v21 (v19 plus TRIGGER_PINS_BY_FILE, FN_PINS_BY_FILE, KINDS_BY_FILE; the fingerprints were printed by the guard from the files as read by the builder in this session; a changed file needs a new pin in the same commit, and the reviewer reads the file text, not the hash). ALLOWED_BY_FILE: functions (name(types) -> definer|invoker). ATOMIC_TABLES_BY_FILE: relations a BEGIN ATOMIC body may use.
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
 D3: {"spend_reserve(text,date,numeric)": "69a1b37ac27e7d27", "spend_settle(text,date,numeric,numeric)": "43e12400d7d87f70", "kill_switch_engage()": "663a59304dcf8b5a", "kill_switch_release()": "d263b5f4c7095b7d"},
 "0002_audit_chain.sql": {"hadavin_audit_append_only()": "f9085f6d3ce7477f"},
}
# statement kinds a DEFINER body may use (F1 of the independent run of v19): everything else, DELETE, TRUNCATE, MERGE, COPY and WITH included, is a problem
KINDS_BY_FILE = {
 D2: {"spend_log_decrease()": {"INSERT"}, "kill_switch_log_change()": {"INSERT"}, "kill_switch_log_insert()": {"INSERT"}},
 D3: {"spend_reserve(text,date,numeric)": {"INSERT", "UPDATE", "SELECT"}, "spend_settle(text,date,numeric,numeric)": {"UPDATE", "SELECT"},
      "kill_switch_engage()": {"INSERT", "UPDATE"}, "kill_switch_release()": {"UPDATE"}},
}
def check(g, name, text):
    """the one call every runner uses: the real file name picks every pin"""
    return g.check_sql_text(name, text, ALLOWED_BY_FILE.get(name, {}), extra_statements=EXTRA_BY_FILE.get(name, ()), atomic_tables=ATOMIC_TABLES_BY_FILE.get(name),
                            trigger_pins=TRIGGER_PINS_BY_FILE.get(name), fn_pins=FN_PINS_BY_FILE.get(name), kinds=KINDS_BY_FILE.get(name))
