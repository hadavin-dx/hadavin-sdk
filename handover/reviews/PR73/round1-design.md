# PR 73 (P3a-2) round 1, egm-design, head 2b0941b (condensed). Money/state path, no round cap.
Limits: ticket lines 1-51 only, no SQL files, nothing run. Evidence: 66/66 mutants (reconstructed runner), 1 env failure (dblink socket, also on base), PG16 only, PG17 and CI not run.
- M1 migrate.py:435 trigger check is a blacklist: tgenabled A->O passes. Fix: refuse any tgenabled change for pre-existing triggers; compare pg_get_triggerdef and prosrc/prosecdef (same-name recreate, V-g). Add wiring stubs.
- M2 migration role not superuser: stated, not enforced. Read rolsuper/createrole/createdb/bypassrls of current_user, refuse; named logged override for tests.
- M3 additive-only / layer 1 not enforced here (P3a-3 comparer not built); make P3a-3 a hard merge-order condition, state in PR.
- M4 manifest hash reads read_bytes separately from executed text (universal newlines): hash texts[p].encode.
- N5 persistent settings (pg_db_role_setting) missing from read-back (nit-to-major).
- N6 pg_auth_members cluster-wide gives false refusals: say so in message.
- N7 COMMIT backstop detects, cannot undo: reword, keep test.
- N8 "statement timeout" string match depends on lc_messages: use SQLSTATE 57014.
- N9 stale docstrings in migration_numbers.py:5-14; pglast importorskip skips silently: hard-fail in CI.
- N10 lock_timeout/statement_timeout not in read-back; RECIPE_TIMEOUTS after advisory lock.
- N11 dblink_exec runs outside the transaction: state in trust-limit text.
Recommendation: items 1-4 fixed or accepted by lead before merge; add killers A->O and superuser role; attach PG17 + CI runs.
