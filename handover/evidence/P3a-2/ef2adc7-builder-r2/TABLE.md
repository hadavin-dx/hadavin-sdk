# Mutant table, head ef2adc75c1a8086c0cd3fd0f389c0676f10d5cdd (builder fix round, PR branch core/P3a-2)

| Runner | Ids | Killed | Not killed |
|---|---|---|---|
| tests/migrate_mutants.py (checked in; raw output: migrate_mutants.log) | 100 (the 89 earlier ones, M65 re-added, T14-T17, R7, B1-B3, O1, O2 and the re-pointed M88 and R4) | 100 | none |
| tests/migration_numbers_mutants.py (raw output: migration_numbers_mutants.log) | 40 | 40 | none |
| handover/tools/p3a2_mutants.py | superseded; not run again (header line added) | - | - |

Dropped on purpose: M88b (the code shape it planted no longer exists; its behaviour is covered by M88 and T1) and P9 (the `_SET_ALLOWED` rule it planted no longer exists).
Re-pointed: M88 now runs `test_a_trigger_created_disabled_is_refused_and_one_created_enabled_is_not`; R4 now has three killers (the wiring test, the new real-server test of a changed grant option, and the text pin).
Command: `HADAVIN_TEST_PG_DSN=<scratch PostgreSQL 16.15> uv run python -m tests.migrate_mutants` (through /home/user/build/heavy.sh). Not run on PostgreSQL 17.
