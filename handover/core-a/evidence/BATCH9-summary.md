# BATCH9 evidence (core-a), run only, no judgement

Head: 32eae7c1717e568b8acdb9d9056d190f1c99fc18 ; 2026-11-20 10:41 UTC ; Python 3.13.18. sha256 values: BATCH9-env.log
(triggers/__init__ 8ff23e60, endpoint e426.. see log, crash.py ebf79b05, tests/endpoint_mutants.py b050c662).

1. Lint (BATCH9-lint.log): ruff check "All checks passed!"; ruff format --check "452 files already formatted"; bandit -ll: Low 7, Medium 0, High 0 (rc 0).
2. Whole suite (BATCH9-suite.log): `13 failed, 12305 passed, 458 skipped, 75 xfailed, 9 warnings in 346.22s`
   (a) strict-mode by design (10):
   - tests/triggers/test_t5_main_start.py::test_1_starts_answers_a_signed_request_and_stops_on_sigterm_with_exit_0
   - ...::test_2a_a_secret_shorter_than_32_characters_is_refused
   - ...::test_2b_two_senders_with_one_secret_value_are_refused
   - ...::test_2c_a_sender_whose_agent_is_not_qualified_is_refused
   - ...::test_2d_a_host_that_is_not_loopback_needs_the_command_line_switch
   - ...::test_2e_a_port_already_in_use_is_a_config_error
   - ...::test_3_the_worker_asks_only_for_the_names_the_senders_list
   - tests/triggers/test_worker.py::test_main_without_a_triggers_block_exits_2
   - tests/triggers/test_t5_process.py::test_d1_main_refuses_to_start_without_a_triggers_block
     (all 9 above: "HADAVIN_REQUIRE_PG=1: core-b trigger config (TriggerSettings, Config.triggers) not on this tree; ...")
   - tests/triggers/test_worker.py::test_the_defaults_constants_of_core_b_equal_the_literals_of_the_worker
     (message: "Failed: the strict switch is on: defaults.TRIGGER_MAX_RUNNING_CEILING is not on this tree")
   (b) other (3):
   - tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]
     (psycopg SqlclientUnableToEstablishSqlconnection: dblink connects to socket /var/run/postgresql/.s.PGSQL.5432, no such file)
   - tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
     (handover/BRIEF-PREAMBLE.md contains the forbidden string '[vendor-brand]')
   - tests/triggers/test_t5_crash_matrix_paths.py::test_pg_kill_at_point[read31-audit.write_outcome-4-after]
     (json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0))
   Skips (458) reason -> count: core-b meter not on this branch yet 264; core-b step F not landed: Store.reserve_spend missing 187;
   empty body refused at Content-Length (own test) 2; model gate (step F) missing 1; textnorm_corpus.json not on branch 1;
   k1b Budget no reserve/settle on this tree 1; core-b trigger config not on this branch yet 1; Stubber refuses malformed Converse shape 1.
   xfailed: 75.
3. Combined tree (BATCH9-combined.log), core-b head d2920f5520b428e28c47a91c3c79f4227c25e9d0; hadavin_sdk.__file__ = scratch ev9-b/src/hadavin_sdk/__init__.py:
   `1377 passed, 4 skipped, 9 warnings in 207.90s`; no FAILED. Skips: 2 "this tree has core-b's trigger config: the module runs for real", 2 "empty body refused at Content-Length (own test)".
4. Mutants (BATCH9-mutants.log): 98 mutant lines (ok/KILLED/CRASH), 0 BAD, 0 SURV. The log ends after G32e; the script's own
   final lines ("N killed ..." / "N of N run are as expected; problems: []") are NOT in the log. rc=0 (appended by the shell after `timeout 590`). Not rerun.

Could not run: nothing skipped by me. Forbidden string replaced by [vendor-brand] in the logs.
