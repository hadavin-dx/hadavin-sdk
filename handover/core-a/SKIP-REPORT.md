# Skip report, core-a (read-only, BATCH-4)

Source: raw/BATCH4-own-files-pg16.log (PostgreSQL 16.15). Summary: 1567 passed, 455 skipped, 75 xfailed, 0 failed.
Tags: [L] from the log, [G] from grep of tests/ (not in the log), [E] estimate.

| Reason (log text) | Count | Files | Class | Follows REQUIRE_PG=1? |
|---|---|---|---|---|
| core-b meter not on this branch yet | 261 [L] | tests/contracts/test_meter.py | another session's branch (expected) | no, not a DB skip |
| k1b Budget has no reserve/settle on this tree | 1 [L] | tests/contracts/test_meter.py | another session's branch (expected) | no |
| core-b step F not landed: Store.reserve_spend missing | 1 [L] | tests/contracts/test_t1_reserve_cap.py | another session's branch (expected) | no |
| textnorm_corpus.json not on this branch | 1 [L] | tests/test_redact_idempotence_property.py | fixture not on branch (expected) | no |
| (no reason in the log) | 191 [L: 455 minus 264] | not in the log | unknown, not in the log | unknown |

- The -rs lines sum to 264 [L], not 455 [L]. The 191 gap has no reason in this log.
- The BATCH-4 board row lists only the 264 reasons above; its "all skips are another session's branch" claim covers 264, not 455.
- Zero database skips appear in this log [L], so REQUIRE_PG=1 converted nothing in this batch.

Skips not in the BATCH-4 log ([G] unless noted):
- Database, does NOT follow the switch (conftest covers only tests/triggers): tests/contracts/kinds/store_postgres.py:24 (HADAVIN_TEST_PG_DSN), tests/test_k5_round8_postgres.py:23, tests/test_k5_round10_postgres.py:14 (module skipif), tests/test_p2_postgres.py:26, tests/test_p7_store.py:11,106, tests/test_p7_tick.py:378, tests/test_k5_fixes2.py:285, tests/test_migrate_regex_linear.py:7 (psycopg). Counts [E] unknown.
- Database, follows the switch: tests/triggers/* skips whose reason names HADAVIN_TEST_PG_DSN or psycopg become failures under HADAVIN_REQUIRE_PG=1. 0 in BATCH-4 [L].
- Another session's branch (expected): tests/triggers/test_trigger_config.py:37,92,158 and tests/triggers/test_t5_main_start.py:31 ("core-b trigger config not on this branch yet"). BATCH-3 board row counts them; BATCH-4 log has no line for them [L], so whether they ran or skipped is unknown.
- Windows/POSIX only, do not skip on Linux: win32 guards in tests/test_mutation_runner.py (about 12 sites), tests/test_p4b_secrets.py:251,281, tests/triggers/test_worker.py:764, tests/triggers/test_t5_process.py:173, tests/triggers/test_t5_main_start.py:47, tests/test_mutation_runner_helpers.py:151. Linux-only guard: tests/test_migration_numbers.py:81,119,127,137 (runs here on Linux).
- Other, environment capability: symlink or privilege guards (tests/test_k1b_causelist_containment.py:30,48,57; tests/test_k1b_bundle.py:290; tests/test_p4b_secrets.py:306; tests/test_no_pglast_in_runtime.py:622; tests/test_mutation_runner.py:199; tests/test_http_metadata.py:160,406). Missing optional extras, not DB (importorskip anthropic, boto3, google.auth, pglast): tests/test_p5_llm.py, test_p6_detectors.py, test_p5p6_followups.py, tests/warden_port/*, tests/contracts/kinds/llm_wire.py, detectors.py, tests/test_migration_numbers_guards.py.
- Code-level: tests/triggers/test_endpoint.py:807,824 ("empty body refused at Content-Length"), 2 rows per BATCH-3 board row, absent from BATCH-4 log [L].
- Total [G]: about 90 skip-marker lines in tests/ (grep count, not run counts) [E].
