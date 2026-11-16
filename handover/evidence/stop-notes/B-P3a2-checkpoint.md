# P3a-2 commit 3b checkpoint (builder, UTC 2026-11-11 21:32)
Done (uncommitted in /home/user/build/B-P3a2): migrate() eight steps in src/hadavin_sdk/store/migrate.py (ruff clean); schema-owner filter (_SCHEMA_OWNER_SQL, `schema_owner` in _state_problems) for the DBA-owned-schema recipe; tests/test_migration_wiring.py fake adapted (120 pass); test_k2 message re-pointed (55 pass).
Next: TPG triage (run queued behind heavy.sh, log /home/user/build/B-P3a2-c3b-tpg3.log), retire 10 TPG tests, re-point rest, 11 broken mutants (M61 M64 M67 M95 R2 PS1 GO2 FO5 PC1 PT1 SD3) + ~20 new, new wiring + real-server tests, test_every_runner_catalog_read_is_pinned, fail-before, gates, commit, push.
Deviations to report: missing_schema_usage judged at step 6 not step 2; _read_back pins only its catalog part; schema owner filter (plan O8 vs PLAIN_MIGRATION_ROLE_SQL).
Not 3c: dead code (effective_problems, _objects, _changed_since, _Changed, _SCHEMA_USAGE_SQL) left in place for 3c.
