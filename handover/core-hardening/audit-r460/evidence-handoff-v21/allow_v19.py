"""Per-file pins of v19. ALLOWED_BY_FILE: functions (name(types) -> definer|invoker). ATOMIC_TABLES_BY_FILE: relations a BEGIN ATOMIC body may use.
EXTRA_BY_FILE: fingerprints (secdef_guard_v19.fingerprint) of one-off statements that match no shape. A file name that is not a key here gets NOTHING allowed
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
