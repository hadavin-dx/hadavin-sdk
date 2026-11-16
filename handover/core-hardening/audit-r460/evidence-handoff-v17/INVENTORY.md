# Inventory, evidence-handoff-v17
Held SQL (`held-sql/`): spend_nonneg.sql, spend_nonneg_finite.sql, spend_nonneg_upgrade.sql (unchanged from v16); spend_decrease_log.sql (changed: lock_timeout line, m5 rule); spend_guarded_writes.sql (new, DB-3, owner-open L22). All five contain `lock_timeout` (L text check).
Programs: run_pg_v17.sh, pg_v17.py (49 checks), pg_v16_regress.py (175 v16 checks on v17 files), secdef_guard_v16.py, secdef_guard_v17.py, secdef_mutants_v17.py (20 mutants), run_secrets_v17.sh, agent_probe_v17.py, patch_v17_main.py (builds the v17 main file from v16), gate4_v17.sh (NOT run in v17).
Raw: raw/ (pg new run1/run2 49 of 49; v16 checks run1/run2 175 of 175; secdef mutants 20 flagged, 30 checks 0 failed; secrets 0 failures; banned-string count 0 hits; PG version lines).
sha256-v17.txt lists every file above except this one. Not run: PG 14 and 17.10, gate4, product tests.
