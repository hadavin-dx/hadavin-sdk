# Q8a-1 batch 16 pr notes (builder)

Status lines are filled in at the end of this file (section "Gates"). Evidence folder: /home/user/build/B-Q8a1-b16-evidence/.

## Fail-before on c098aacf
Method: detached worktree of c098aacf (src unchanged), only the changed test files of the head copied in (tests/_guard_allowances.py, _text_guard.py, stage_mutants.py, test_changelog_claims.py, test_guard_reasons.py, test_q8a1_b15_fixes.py, test_q8a1_b16_fixes.py, test_stage_names.py). Command: pytest on test_changelog_claims, test_guard_reasons, test_q8a1_b15_fixes, test_q8a1_b16_fixes, test_stage_names. Result: 27 failed, 591 passed in 19.79s. Log: failbefore.log. Failed ids (27):
- `tests/test_changelog_claims.py::test_the_counts_of_the_batch_16_entry_are_the_counts_of_this_head`
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[FILENAME]`
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[MIGNAMES]`
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[NUMFIELD]`
- `tests/test_q8a1_b15_fixes.py::test_check_config_accepts_a_good_configuration_and_exits_0`
- `tests/test_q8a1_b15_fixes.py::test_check_config_refuses_a_key_shaped_model_id_by_field_and_rule_never_the_value`
- `tests/test_q8a1_b16_fixes.py::test_check_config_does_not_run_a_tool_module`
- `tests/test_q8a1_b16_fixes.py::test_check_config_says_what_it_did_not_check`
- `tests/test_q8a1_b16_fixes.py::test_check_config_still_refuses_a_tool_with_no_module_in_tool_modules`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[../x]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[..\\x]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[/etc/x]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[a/b]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[.hidden]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[a b]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[a:b]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[ABC]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[nul]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[com1]`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_bad_event_id_does_not_quote_the_id[abc\n]`
- `tests/test_q8a1_b16_fixes.py::test_an_event_id_with_a_colon_a_capital_or_a_device_name_is_refused_and_a_generated_id_is_not`
- `tests/test_q8a1_b16_fixes.py::test_the_local_audit_folder_never_makes_a_file_from_an_event_that_skipped_the_model_check`
- `tests/test_q8a1_b16_fixes.py::test_shown_id_shows_only_ids_of_the_prefixes_the_code_makes`
- `tests/test_q8a1_b16_fixes.py::test_every_prefix_given_to_new_id_in_the_package_is_in_the_shown_list`
- `tests/test_q8a1_b16_fixes.py::test_the_refusal_of_a_ledger_row_without_a_file_shows_only_names_shaped_like_ours`
- `tests/test_q8a1_b16_fixes.py::test_the_outbox_never_makes_a_file_from_an_event_id_that_is_not_a_plain_name`
- `tests/test_stage_names.py::test_no_config_derived_name_is_put_in_a_message_outside_the_one_filter`

The guard tables (planted and clean forms) are test tooling copied with the tests, so on the old src they cannot fail. The real fail-before of the guard is the OLD guard file (c098aacf) run on the new tables (oldguard.py, result oldguard.txt): it MISSES 14 of the 17 new planted shapes (R16a to R16h, R16j to R16n, R16p; R16d finds one of two) and finds R16 (function parameter), R16i and R16o (controls, the behaviour held). It passes all 12 new clean forms (controls: they guard the widened guard against over-flagging).

## Pass-on-old-code table (by script: table.py; per test id and parameter; the 25 ids of the independent evidence file plus the new ids that pass on c098aacf)
- `tests/test_changelog_claims.py::test_every_path_under_tests_src_or_tools_in_the_changelog_exists`: no mutant (it checks a document, not code); reason: control for the old paths (every path the old CHANGELOG named existed); the new test is shown failing with a planted missing path (docs/no_such_file_b16.md) in the old tree, see the fail-before section
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[CLOSED]`: killed by Z131
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[OWNERROR]`: killed by Z185
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[URL]`: killed by Z125,Z140
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15a an error object built outside a raise]`: killed by Z100
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15b a keyword made from the text of an error]`: killed by Z101
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15c an attribute set to the text of an error]`: killed by Z102
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15d an out-parameter list filled by a helper and joined by the caller]`: killed by Z103
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15e a raise inside an except with no from]`: killed by Z104
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15f traceback.print_exc]`: killed by Z105
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15g a log call with exc_info]`: killed by Z106
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15h sys.exit with a name]`: killed by Z107
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15i a path join handed to an error]`: killed by Z108
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15j a parameter that is called shown_name]`: killed by Z109
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15k a status_text imported from a library]`: killed by Z110
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15l an UPPER_CASE table filled at run time]`: killed by Z111
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15m an UPPER_CASE name bound to a call]`: killed by Z112
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R15n int() of an unproven value in a message]`: killed by Z123
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R15 a class tuple handed to a function]`: killed by Z113
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R15 a context manager that is not an error]`: killed by Z114
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R15 a raise after the except block]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R15 a raise from None inside an except]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R15 a table of written words that nothing changes]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R15 int() of a value that is a written number]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R15 the package's own shown_name]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_changelog_claims.py::test_every_repository_path_in_the_changelog_exists`: no mutant (it checks a document, not code); reason: control for the old paths (every path the old CHANGELOG named existed); the new test is shown failing with a planted missing path (docs/no_such_file_b16.md) in the old tree, see the fail-before section
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[CARD]`: killed by Z165,Z166,Z167
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[FILTER]`: killed by Z184
- `tests/test_guard_reasons.py::test_the_claim_of_each_reason_holds_in_the_code[HANDOFF]`: killed by Z183
- `tests/test_q8a1_b16_fixes.py::test_a_refused_port_is_shown_by_its_digits_never_by_the_text_of_the_value`: killed by Z181
- `tests/test_q8a1_b16_fixes.py::test_check_config_exit_codes_are_those_of_main_and_tick`: killed by Z182
- `tests/test_q8a1_b16_fixes.py::test_execute_reports_an_error_status_as_its_digits_and_never_through_the_text_of_the_status[404-failed]`: killed by Z180
- `tests/test_q8a1_b16_fixes.py::test_execute_reports_an_error_status_as_its_digits_and_never_through_the_text_of_the_status[408-unknown]`: control: this status (503 or 408 -> unknown) already printed digits on c098aacf; the 404 case is killed by Z180
- `tests/test_q8a1_b16_fixes.py::test_execute_reports_an_error_status_as_its_digits_and_never_through_the_text_of_the_status[503-unknown]`: control: this status (503 or 408 -> unknown) already printed digits on c098aacf; the 404 case is killed by Z180
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16a a local text of an error set on an attribute]`: killed by Z150
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16b a positional argument of a class]`: killed by Z151
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16c a dict value made from an error]`: killed by Z152
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16d a helper returns the text of an error]`: killed by Z153
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16e repr of an unproven value]`: killed by Z154
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16f a helper that raises, called in an except]`: killed by Z155
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16g format_exception_only]`: killed by Z156
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16h TracebackException.from_exception]`: killed by Z157
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16i an error class derived from ValueError]`: killed by Z158
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16j a derived error built outside a raise]`: old guard (c098aacf) misses this shape (script run); killed by Z100 too (same site as R15a; the mutated guard finds 0 of 1 here, script run, not pinned in the runner)
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16k an attribute of a library result]`: killed by Z159
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16l a set difference in a message]`: killed by Z160
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16m a text filter that returns its argument]`: killed by Z161
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16n a number annotation on a text]`: killed by Z162
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16o a log call with a text directive]`: control: the old guard (c098aacf) already finds this shape (script run), so the row pins behaviour that held; no mutant
- `tests/test_stage_names.py::test_the_guard_finds_each_planted_fault_alone[R16p a self attribute that only another class writes]`: killed by Z164
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16a a written text set on an attribute]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16b a class given a written text]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16c a dict value that is the class name of an error]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16d a helper returns the class name of an error]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16e repr of a counter]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16f a helper that raises, called outside an except]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16i a derived error class given a written text]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16k an attribute of an object of the package]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16l the size of a set difference]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16n a number annotation on a number]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16o a log call with a number directive]`: killed by Z163
- `tests/test_stage_names.py::test_the_guard_passes_the_filtered_and_code_owned_forms[R16p a self attribute that the class writes]`: control: a clean form that must NOT be flagged; the old guard (c098aacf) passes it too (script run), so it passes on old code by design; it guards the widened guard against over-flagging; no mutant is pinned to this form, the function is killed by the over-flag mutants Z1 and others

Notes on the table: BUILT no longer appears (no BUILT reason exists). For the planted rows R15a to R15n the killers are Z100 to Z112 and Z123, pinned per row. R16j is also killed by Z100 (script run with the Z100 text applied: 0 of 1 found), not pinned in the runner.

## Reason checks (what they prove) and mutants
New mutants Z150-Z167 (guard shapes and CARD), Z168-Z187 (fixes and reason checks). Killer messages named: Z115, Z116, Z118, Z126-Z130, Z136, Z138 now name their own claim (tests edited; Z120 was already specific). Mutants run: Z165-Z167 (mut2), Z168-Z175 (mut3), Z176-Z181 (mut4), Z183-Z187 (mut6), all KILLED with the pinned test and message. Z188 was tried and dropped (its mutation changed the row key, so it was killed for the wrong reason). Full run: see Gates.


## Found late by the full mutation run (fixed in commit 20581c80)
The first full mutation run on head 9310ff77 ended with 342 of 363 good. The 21 others were mutants that had gone stale or equivalent because I widened the guard (Round 16) and formatted it, and I had run only the new mutants after that. All 21 were repaired and re-run (27 of 27 good in the targeted run; the full run on the final head is listed under Gates):
- Format: `tests/_text_guard.py` now carries `# fmt: off` (the mutants quote its lines; a formatter broke 10 quotes). The file is still linted.
- Equivalent after the widening, so retargeted: Z2 (now the `/` join read in `bare_unsafe`), Z37 (now the import check of the filter module), Z79 (now a problem sentence made from `str(...)`, a real LISTED claim).
- Planted faults that were found by a second rule, so they proved nothing on their own: R15b, R15c, R15d, R15j, R15k, R16b, R16d, R16i/R16j (base `KeyboardInterrupt`, because `Exception` is itself an error suffix), R16o clean form. Each now isolates the one rule its mutant removes.
- A real checker gap found: the NUM check trusted any call whose name starts with `purge_`, and any method name that some class declares as a number. It now reads the number from the store contract (`-> int` in store/protocol.py) for `purge_` calls (Z65 retargeted to that file).
- Message fixes so each killer names its own claim: Z121 (test records the connect call instead of raising inside a command that catches everything), Z127 (pattern moved to `EVENT_ID_PATTERN`), Z128.

## Group 4, 6, 7, others
- Restore of `test_a_failing_detector_is_logged_by_class_only`: it already exists at c098aacf in tests/test_q8a1_b14_fixes.py together with the Bedrock-shaped bare-id test `test_the_bedrock_detector_logs_the_class_of_a_cloud_error_never_its_text`; both pass at the head. Nothing was dropped; I did not change them.
- Group 10 closed by evidence; E1 and E2 are owner questions (nothing built).
- CARD demo-fixture half: ticket Q8a1-card-demo-fixture (due 2026-11-19), file /home/user/hadavin-sdk/handover/tickets/Q8a1-card-demo-fixture.md (outside the code branch).
- Decision not as the review wrote it: shown_id uses a closed prefix list, not a "20+ hex refusal" (a real id has 32 hex digits). Stated in the CHANGELOG.
- Exception: tests/test_changelog_claims.py does not check paths under `handover/` (that folder is not in the code branches); two older handover paths in the CHANGELOG are therefore unchecked.

## `noqa: BLE001` handlers (54 in src, per site; script handlers.py)
"no name bound" means the handler binds no error variable, so it cannot print its text. "class only" means every use of the error variable is a class name. "USES" lists the other uses; none prints the text of the error. `agent_loop.py:312` and `tools.py:1231` hand the error to `error_reason`, whose text goes to the model, the open REDACTED owner question. No handler prints `{exc}`, so none was changed.
- `src/hadavin_sdk/app.py:277` class only (1 use)
- `src/hadavin_sdk/approvals/requests.py:118` class only (1 use)
- `src/hadavin_sdk/approvals/requests.py:190` class only (1 use)
- `src/hadavin_sdk/approvals/requests.py:233` class only (1 use)
- `src/hadavin_sdk/approvals/slack_channel.py:176` class only (1 use)
- `src/hadavin_sdk/audit/anchor_azure.py:86` class only (1 use)
- `src/hadavin_sdk/audit/anchor_gcs.py:72` class only (1 use)
- `src/hadavin_sdk/audit/chain.py:221` no name bound; prints nothing of the error
- `src/hadavin_sdk/audit/chain.py:228` no name bound; prints nothing of the error
- `src/hadavin_sdk/audit/chain.py:240` no name bound; prints nothing of the error
- `src/hadavin_sdk/audit/chain.py:253` no name bound; prints nothing of the error
- `src/hadavin_sdk/audit/chain.py:315` class only (1 use)
- `src/hadavin_sdk/audit/chain.py:330` class only (1 use)
- `src/hadavin_sdk/audit/chain.py:354` class only (1 use)
- `src/hadavin_sdk/audit/chain.py:532` USES ['is_connectivity_error(exc)', 'type(exc)']
- `src/hadavin_sdk/audit/local_dir.py:126` no name bound; prints nothing of the error
- `src/hadavin_sdk/audit/local_dir.py:136` no name bound; prints nothing of the error
- `src/hadavin_sdk/audit/local_dir.py:149` no name bound; prints nothing of the error
- `src/hadavin_sdk/audit/local_dir.py:166` no name bound; prints nothing of the error
- `src/hadavin_sdk/backends/platform_secrets.py:93` class only (1 use)
- `src/hadavin_sdk/cli.py:350` class only (1 use)
- `src/hadavin_sdk/cli.py:438` USES ["_kill_switch_store_down('set', exc)"]
- `src/hadavin_sdk/cli.py:451` USES ["_kill_switch_store_down('reset', exc)"]
- `src/hadavin_sdk/cli.py:98` USES ['_print_frames(exc)', 'type(exc)']
- `src/hadavin_sdk/guard/http.py:131` USES ["box['error'] = exc"]
- `src/hadavin_sdk/guard/injection.py:88` class only (1 use)
- `src/hadavin_sdk/guard/runmap.py:257` no name bound; prints nothing of the error
- `src/hadavin_sdk/guard/runmap.py:522` class only (1 use)
- `src/hadavin_sdk/k1b/audit_sink.py:55` no name bound; prints nothing of the error
- `src/hadavin_sdk/k1b/loop.py:95` USES ["box['exc'] = exc", 'type(exc)']
- `src/hadavin_sdk/runtime/agent_loop.py:252` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:298` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:312` USES ['error_reason(exc)']
- `src/hadavin_sdk/runtime/agent_loop.py:414` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:426` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:430` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:521` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:528` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:550` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:616` class only (1 use)
- `src/hadavin_sdk/runtime/agent_loop.py:629` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:658` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:702` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:722` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:733` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:858` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:892` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:907` no name bound; prints nothing of the error
- `src/hadavin_sdk/runtime/agent_loop.py:915` no name bound; prints nothing of the error
- `src/hadavin_sdk/sources/__init__.py:74` class only (1 use)
- `src/hadavin_sdk/sources/kubernetes.py:205` USES ["getattr(exc, 'too_large', False)", 'type(exc)']
- `src/hadavin_sdk/tools.py:1153` USES ["box['error'] = exc"]
- `src/hadavin_sdk/tools.py:1231` USES ['error_reason(exc, ctx.secrets_handed_out(), self._scrub)']
- `src/hadavin_sdk/tools.py:424` class only (1 use)
