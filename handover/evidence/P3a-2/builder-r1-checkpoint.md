# builder-r1 checkpoint 1 (P3a-2 round 1 fixes)
Done in worktree /home/user/build/B-P3a-2 (not yet committed): one manifest tests/fixtures/migrations_released.json (src copy deleted, migrate no longer reads a list); trigger equality + definition/function compare; privileged-role refusal with named override; hash of texts[p]; SQLSTATE 57014; pg_db_role_setting and time limits in read-back; docstring/CHANGELOG wording; pglast hard-fail in CI.
Next: run the migration test files on PG16 (port 55432), mutation spot-check of new tests against old code, commit, push to core/P3a-2.
Blockers: PG17 cannot run here.
