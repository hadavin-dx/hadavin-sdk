"""Per-file allow-lists of v18 (class F fix: one union list let the DB-2 file define a DB-3 name). Key = name(types); value = definer or invoker."""
ALLOWED_BY_FILE = {
 "spend_decrease_log.sql": {"spend_keep_keys()": "invoker", "spend_log_decrease()": "definer", "kill_switch_log_change()": "definer", "audit_log_append_only()": "invoker"},
 "spend_guarded_writes.sql": {"spend_reserve(text,date,date,numeric)": "definer", "spend_settle(text,date,date,numeric,numeric)": "definer", "kill_switch_engage()": "definer", "kill_switch_release()": "definer"},
 "0002_audit_chain.sql": {"hadavin_audit_append_only()": "invoker"},
}
