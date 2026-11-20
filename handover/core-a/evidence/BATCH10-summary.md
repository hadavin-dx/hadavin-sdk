# BATCH10 summary

Fri Nov 20 11:22:03 UTC 2026
Python 3.13.18
6e61005db871ed0c648435da646c7e2bb4cd8564
8ff23e60491745b59f2840d04d516179300edbc8eecca18d619812ce8a2131cf  src/hadavin_sdk/triggers/__init__.py
fdd9ae116d6add8229daefdae674975d80582fa9528bf693c3d65b86a804651f  src/hadavin_sdk/triggers/endpoint.py
5f1e8134ba72fb070b393059b38cec2630165b1f7a969060462ce7f2bee4f41d  src/hadavin_sdk/triggers/server.py
ae2ad99697fa85c0d9ad8448c3b43e396013ff40fc00ae617971409510ec4a1f  src/hadavin_sdk/triggers/worker.py
ebf79b05cc0bd9131b7121c494155e6934cdd812c5fbdc8a5322861b982551df  src/hadavin_sdk/testing/crash.py
1e95dc262c92566c466069528bdea0bee0b1b649ac26cd981be033ecf3d2d5b9  tests/triggers/crash_launcher.py

## 1 lint
ruff check: All checks passed (exit 0); ruff format: 458 files already formatted (exit 0); bandit -ll: High 0, Medium 0, Low 7, exit 0

## 2 whole suite
12 failed, 12366 passed, 458 skipped, 75 xfailed, 9 warnings in 345.43s (0:05:45)
xfailed: 75
FAILED (a) strict-mode by design:
FAILED tests/triggers/test_worker.py::test_main_without_a_triggers_block_exits_2
FAILED tests/triggers/test_worker.py::test_the_defaults_constants_of_core_b_equal_the_literals_of_the_worker
FAILED tests/triggers/test_t5_main_start.py::test_1_starts_answers_a_signed_request_and_stops_on_sigterm_with_exit_0
FAILED tests/triggers/test_t5_main_start.py::test_2a_a_secret_shorter_than_32_characters_is_refused
FAILED tests/triggers/test_t5_main_start.py::test_2b_two_senders_with_one_secret_value_are_refused
FAILED tests/triggers/test_t5_main_start.py::test_2c_a_sender_whose_agent_is_not_qualified_is_refused
FAILED tests/triggers/test_t5_main_start.py::test_2d_a_host_that_is_not_loopback_needs_the_command_line_switch
FAILED tests/triggers/test_t5_main_start.py::test_2e_a_port_already_in_use_is_a_config_error
FAILED tests/triggers/test_t5_main_start.py::test_3_the_worker_asks_only_for_the_names_the_senders_list
FAILED tests/triggers/test_t5_process.py::test_d1_main_refuses_to_start_without_a_triggers_block
FAILED (b) other:
FAILED tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]
FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
(b) causes: dblink-connect: psycopg could not connect to socket /var/run/postgresql/.s.PGSQL.5432; no_vendor_brand: handover/BRIEF-PREAMBLE.md contains the brand

skip table (count reason)
264	core-b meter not on this branch yet
187	core-b step F not landed: Store.reserve_spend missing
2	an empty body is refused at Content-Length (own test)
1	the model gate (step F) is not on this branch yet: hadavin_sdk.guard.model_gate is missing
1	tests/fixtures/textnorm_corpus.json is not on this branch: that corpus is not run here
1	k1b Budget has no reserve/settle on this tree: the in-memory meter arrives with step F-install (ii-meter.md header); its cases are written from tickets/F-install.md and have never run
1	core-b trigger config not on this branch yet
1	Stubber refuses a malformed Converse shape before the kind sees it

## 3 combined tree (core-b head 1e579134559862c6c735e63973f8c6d1fa2f7c73)
1437 passed, 4 skipped, 9 warnings in 189.14s (0:03:09)
SKIPPED [1] tests/triggers/test_endpoint.py:847: an empty body is refused at Content-Length (own test)
SKIPPED [1] tests/triggers/test_endpoint.py:864: an empty body is refused at Content-Length (own test)
SKIPPED [1] tests/triggers/test_t5_strict_mode.py:45: this tree has core-b's trigger config: the module runs for real
SKIPPED [1] tests/triggers/test_t5_strict_mode.py:56: this tree has core-b's trigger config: the module runs for real

Not run: endpoint_mutants script (blocked item)
