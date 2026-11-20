# TRIAL-RERUN: our tests for other sessions' code, run again on the newest heads

Facts only. No verdicts. Run 2026-11-20 by the evidence runner of core-a. Nothing in the checkout was edited; our test files were copied unchanged into scratch folders next to an unpacked `git archive` of each branch (src, tests, tools, pyproject.toml).

## What was not run
- Nothing was skipped by us. No whole-suite run (not asked). Only the six files listed below were run.
- Skips inside the files are listed per file.

## Commit ids
- core-b: before d0cac9693, now dba4463a5 (origin/cloud/core-b)
- core-c: before 17f4534a4, now 49013c787 (origin/cloud/core-c)
- Titles since the old heads (src and tests): see `git log --oneline d0cac9693..origin/cloud/core-b -- src tests` and `17f4534a4..origin/cloud/core-c -- src tests`. core-b: 26bbb44d5 (F-store: spend day a plain date), fee3cb2db, 05d62ca32 (sender secret errors raised after the handler), 1fc346706, f40d28f0b (F-store fix round 3: ids and caps validated everywhere, memory store builds the row before booking, sender secret errors hide the name, lock timeout, binary document sizing), 37c8e9322 (provider mark fix round 1), 6cc472c0a (board), 3c033b209 (F-store fix round 2: reservation id validated in both stores), 449249728, c2bec4738 (A: outage rule). core-c: 4a17e89b3, d464e133c, 9faa8a6cf, 358759bae, a1c040a9a, 595878ec3 (all "work in progress of running agents, NOT verified"), ab6ff2f61 (G7 fix round 1, own-output rule), c11fafb99 (G7 hardening), 47af8e453 (B grants tests).

## Per file: before and after (logs: raw/RERUN-core-b.log, raw/RERUN-core-c.log)
core-b run (4 files together): 14 failed, 671 passed, 20 skipped.
| file | before (run2 log, d0cac9693) | after (dba4463a5) |
|---|---|---|
| tests/test_trigger_config.py | 232 passed, 20 skipped, 4 xfailed | 5 failed (4 strict XPASS, 1 error), rest passed; same 20 skips (field not built: triggers.senders limit 1, poll_s 6, port 7, allow_non_loopback 6) |
| tests/contracts/test_store_spend_reservations.py | 183 passed, 4 xfailed (4 xfailed = F1 x3, F2 x1) | 4 failed (all strict XPASS: F1 x3, F2 x1) |
| tests/contracts/test_t1_reserve_cap.py | not recorded separately | 11 passed, no failure, no skip |
| tests/contracts/test_meter.py | 259 passed, 3 xfailed (M1 x3) | 5 failed (3 strict XPASS M1, 2 errors), rest passed |
core-c run (2 files): 194 failed, 161 passed, 1 skipped, 8 xfailed.
| file | before | after (49013c787) |
|---|---|---|
| tests/contracts/test_model_gate_contract.py | 201 passed, 1 skipped (gate-contract-tests-on-core-c.log, 17f4534a4) | 165 failed, 36 passed, 1 skipped (same skip: point 10, no worst-case formula) |
| tests/test_redact_idempotence_property.py | run2: 37 failed (strict XPASS), 116 passed, 9 xfailed; run5 (final test file): 154 passed, 8 xfailed | 29 failed (strict XPASS), 125 passed, 8 xfailed |

## Table of changes
| test id | before | after | finding | commit that probably fixed it |
|---|---|---|---|---|
| test_trigger_config.py::test_env_kind_alias_of_a_secret_name_fails_the_start[action-secret-upper], [action-secret-dot], [two-senders], [one-sender-pair] | xfail | XPASS(strict) = failed | T1 | UNKNOWN (core-b secret-name validation since d0cac9693; f40d28f0b / 05d62ca32 touch secret_names) |
| test_store_spend_reservations.py::test_a_cap_that_is_a_finite_decimal_is_either_applied_or_a_value_error[postgres] | xfail | XPASS(strict) | F2 | f40d28f0b (caps validated everywhere) probably |
| test_store_spend_reservations.py::test_a_reserve_that_fails_for_any_reason_leaves_no_counter_change[memory-run-id-int], [memory-reservation-id-int], [memory-agent-none] | xfail | XPASS(strict) | F1 | f40d28f0b (memory store builds the row before booking) probably |
| test_meter.py::test_a_reserve_that_is_refused_for_any_reason_books_nothing[limits-memory-int], [limits-memory-float], [limits-memory-tuple] | xfail | XPASS(strict) | M1 | f40d28f0b probably |
| test_trigger_config.py::test_secret_name_characters_allowed_as_built[all] | pass | FAILED: the name `Key_one.v2:eu/primary-1` is refused (pattern now `^[A-Za-z0-9_.:-]{1,128}$`, the slash is no longer allowed) | NEW failure, no finding id | UNKNOWN (log -S of the pattern in src found only 6cc472c0a "board") |
| test_meter.py::test_settle_with_an_unknown_id_is_not_found_from_both_meters[limits-memory], [limits-postgres] | pass | FAILED: settle("") (empty id) raises ValueError "reservation id must be a str of 1 to 200 characters..." instead of NotFound | NEW failure, no finding id | 3c033b209 (reservation id validated in both stores) |
| test_model_gate_contract.py: 161 tests | pass | FAILED TypeError: ModelGate.bind() missing 1 required keyword-only argument: 'mapping' | NEW failure | core-c change to guard/model_gate.py bind (in the "work in progress" commits; not isolated) |
| test_model_gate_contract.py::test_hostile_an_empty_message_list_is_still_one_reserve_one_call_one_settle[store-style-no-map], [memory-style-no-map] | pass | FAILED TypeError: mapping must be a Mapping (the run's map) or NO_MAP | NEW failure | same |
| test_model_gate_contract.py::test_m1_the_whole_module_has_no_logger_no_print_and_no_exception_text | pass | FAILED: line 450: an exception built from a value | NEW failure | same |
| test_model_gate_contract.py::test_m1_the_module_keeps_no_state_between_calls | pass | FAILED: line 194: module-level call of compile | NEW failure | same |
| test_redact_idempotence_property.py::test_P7_I6_untrusted_text_a_second_pass_adds_no_map_entry_and_a_third_changes_nothing[29 ids: controls-around ... zero-width-in-values] | pass (marker `needs_own_output_rule` inactive because `_ESCAPED_LOOKALIKE` existed) | XPASS(strict): `_ESCAPED_LOOKALIKE` no longer exists in guard/redact.py, so the marker is active, and the test passes | none (not a finding; the marker condition flipped) | ab6ff2f61 removed `_ESCAPED_LOOKALIKE` |
| test_redact_idempotence_property.py: G7-F3 (4 P5 phone ids) and G7-F4 (P5 '. ' id, 3 P6 ids) | xfail | xfail unchanged (8 xfailed) | G7-F3, G7-F4 | not fixed |

Skips gone or new: none gone, none new (trigger config 20, gate 1).

## Markers to remove (the owner's next step; not edited by us)
- tests/test_trigger_config.py: the xfail on test_env_kind_alias_of_a_secret_name_fails_the_start (T1, 4 ids)
- tests/contracts/test_store_spend_reservations.py: xfail F2 (cap postgres id) and F1 (3 memory ids)
- tests/contracts/test_meter.py: xfail M1 (3 ids)
- tests/test_redact_idempotence_property.py: `needs_own_output_rule` condition on test_P7_I6 (the attribute `_ESCAPED_LOOKALIKE` is gone, so the marker now applies)
