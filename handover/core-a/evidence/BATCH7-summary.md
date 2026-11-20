# BATCH7 summary
head 3f26300256d520f8e2356ff8fdf1f08407391a8f; 2026-11-20 09:06 UTC; Python 3.13.18; core-b head 2bdbba391ad96c8ae825eaedb869ca946d1934af
Logs: BATCH7-env.log, BATCH7-lint.log, BATCH7-suite.log, BATCH7-combined.log, BATCH7-mutants.log

## 1 lint
- ruff check: Found 2 errors (rc=1), both in handover/core-a/tools/board.py (S603 at :23, RUF100 unused noqa S603 at :25)
- ruff format --check: 439 files already formatted (rc=0)
- bandit -ll -r src: No issues identified (rc=0)

## 2 whole suite
Last line: 12 failed, 12256 passed, 458 skipped, 75 xfailed, 9 warnings in 290.73s (0:04:50)
xfail count: 75

### FAILED (a) strict-mode by design (core-b trigger config not on this tree)
- tests/triggers/test_worker.py::test_main_without_a_triggers_block_exits_2
- tests/triggers/test_worker.py::test_the_defaults_constants_of_core_b_equal_the_literals_of_the_worker
- tests/triggers/test_t5_main_start.py::test_1_starts_answers_a_signed_request_and_stops_on_sigterm_with_exit_0
- tests/triggers/test_t5_main_start.py::test_2a_a_secret_shorter_than_32_characters_is_refused
- tests/triggers/test_t5_main_start.py::test_2b_two_senders_with_one_secret_value_are_refused
- tests/triggers/test_t5_main_start.py::test_2c_a_sender_whose_agent_is_not_qualified_is_refused
- tests/triggers/test_t5_main_start.py::test_2d_a_host_that_is_not_loopback_needs_the_command_line_switch
- tests/triggers/test_t5_main_start.py::test_2e_a_port_already_in_use_is_a_config_error
- tests/triggers/test_t5_main_start.py::test_3_the_worker_asks_only_for_the_names_the_senders_list
- tests/triggers/test_t5_process.py::test_d1_main_refuses_to_start_without_a_triggers_block

### FAILED (b) other
- tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]
  E psycopg.errors.SqlclientUnableToEstablishSqlconnection: could not establish connection; DETAIL: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: No such file or directory
- tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
  E vendor brand strings in the repo: handover/BRIEF-PREAMBLE.md: 'Port.io'; handover/core-a/board-state.json: 'Port.io'; handover/core-a/STATUS-BOARD.md: 'Port.io'

### Skip table (reason -> count; top 8 of the SKIPPED lines)
264	 core-b meter not on this branch yet
187	 core-b step F not landed: Store.reserve_spend missing
2	 an empty body is refused at Content-Length (own test)
1	 the model gate (step F) is not on this branch yet: hadavin_sdk.guard.model_gate is missing
1	 tests/fixtures/textnorm_corpus.json is not on this branch: that corpus is not run here
1	 k1b Budget has no reserve/settle on this tree: the in-memory meter arrives with step F-install (ii-meter.md header); its cases are written from tickets/F-install.md and have never run
1	 core-b trigger config not on this branch yet
1	 Stubber refuses a malformed Converse shape before the kind sees it

## 3 combined tree (core-b + this checkout's triggers/crash/tests/n8n)
hadavin_sdk.__file__ = scratch ev7-b/src/hadavin_sdk/__init__.py (confirmed)
Last line: 1327 passed, 4 skipped, 9 warnings in 156.86s (0:02:36)
Skips: 2 'this tree has core-b's trigger config: the module runs for real'; 2 'an empty body is refused at Content-Length (own test)'; FAILED: none

## 4 mutants
Last line: 90 of 90 run are as expected; problems: [] (89 killed, 1 crash-accepted G20j, 0 survivors; rc=0)
