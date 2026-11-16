"""Per-file pins of v20 (v19 plus TRIGGER_PINS_BY_FILE, FN_PINS_BY_FILE, KINDS_BY_FILE; the fingerprints were printed by the guard from the files as read by the builder in this session; a changed file needs a new pin in the same commit, and the reviewer reads the file text, not the hash). ALLOWED_BY_FILE: functions (name(types) -> definer|invoker). ATOMIC_TABLES_BY_FILE: relations a BEGIN ATOMIC body may use.
EXTRA_BY_FILE: fingerprints (secdef_guard_v20.fingerprint) of one-off statements that match no shape. A file name that is not a key here gets NOTHING allowed
(fails closed): the move PR that renames a held file must rename its key in the same commit (the guard test names the file in every problem)."""
ALLOWED_BY_FILE = {
 "spend_decrease_log.sql": {"spend_keep_keys()": "invoker", "spend_log_decrease()": "definer", "kill_switch_log_change()": "definer", "kill_switch_log_insert()": "definer", "audit_log_append_only()": "invoker"},
 "spend_guarded_writes.sql": {"spend_reserve(text,date,numeric)": "definer", "spend_settle(text,date,numeric,numeric)": "definer", "kill_switch_engage()": "definer", "kill_switch_release()": "definer"},
 "0002_audit_chain.sql": {"hadavin_audit_append_only()": "invoker"},
}
ATOMIC_TABLES_BY_FILE = {"spend_guarded_writes.sql": {"spend", "spend_month", "kill_switch"}}
EXTRA_BY_FILE = {
 "spend_nonneg_upgrade.sql": {"e6ac34b6078911b5", "546a359be721e79e"},   # the two ALTER TABLE ... DROP CONSTRAINT x, ADD CONSTRAINT x statements
 "0003_approvals_tick.sql": {"00159fbff1514eb2", "ef1e897d019d5128", "11e153216b3bd000"},  # the duplicate-decision DELETE, the month-row backfill INSERT, the kill-switch row INSERT
}

D2, D3 = "spend_decrease_log.sql", "spend_guarded_writes.sql"
TRIGGER_PINS_BY_FILE = {
 "0002_audit_chain.sql": {"audit_entries_append_only": "49ca8bc9a0bdf705", "audit_checkpoints_append_only": "6dd3e0175bd809ea", "audit_entries_no_truncate": "8db359d87e5a30bd", "audit_checkpoints_no_truncate": "203443c1e5a75393"},
 D2: {"spend_keep_keys": "838e3f094cdbb3b3", "spend_month_keep_keys": "7889de2345307f42", "spend_log_decrease": "0094f338b44898e1", "spend_month_log_decrease": "229c2ee37a492a12",
      "kill_switch_log_change": "e3b7d01729e27d0e", "kill_switch_log_insert": "4f245d287eb77632", "spend_decrease_log_append_only": "d5b941ccdc4c3fd3",
      "spend_decrease_log_no_truncate": "6f31277140ecc32f", "kill_switch_log_append_only": "f2f4994670185a57", "kill_switch_log_no_truncate": "3be02803615b2186"},
}
FN_PINS_BY_FILE = {
 D2: {"spend_keep_keys()": "7be874adcdb19a94", "spend_log_decrease()": "0d89c3b9627ba323", "kill_switch_log_change()": "2b50890fa0b797ed", "kill_switch_log_insert()": "c05e4dca6665ab45", "audit_log_append_only()": "c4362dfbf7d095bb"},
 D3: {"spend_reserve(text,date,numeric)": "9ae27603c1f1d7b3", "spend_settle(text,date,numeric,numeric)": "d97dfa884b064e37", "kill_switch_engage()": "e8ff2171b8e650c6", "kill_switch_release()": "168ff26df72043a0"},
 "0002_audit_chain.sql": {"hadavin_audit_append_only()": "757aaa32fd7f350b"},
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
