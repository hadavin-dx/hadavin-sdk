# PD bind guard batch 10: builder notes (BUILDER, worktree pdbind-b8, base 83cdb7a2)

## What failed or is uncertain (first)
- Python 3.14 NOT verified (no interpreter). Row B158 is skipped there by design; the CHANGELOG says 243 of 244.
- The full 244-row mutant table was NOT re-run. Only the new and re-pointed rows were run (below). No 60-row sample was run (time box).
- Slip found and fixed in my own work: my first "scan once" test used approvals whose holder was EMPTY, so the runtime was never read and the test passed on old code (and row B249 survived). Rebuilt with the runtime in the holder: it now fails on 83cdb7a2 (store scanned 2 times), so the reviewers' claim of two scans is true for that shape.
- A new finding in my own change: `copy.copy(hooks)` wrote `__slotnames__` into the pinned `Hooks` class and made every later question read as real. Fixed in the pin (touches it, like `__annotations__`); test + row B256. `__slotnames__` is a list on the class (allowed in the "no mutable class value" test; it is only read to restore a copy).
- Row B253 (CHANGELOG pin count) cannot run in the mutation runner (the temp copy has no CHANGELOG, the test skips). Removed; proved by hand instead: dropping HOOKS from `_PINNED_KEYS` makes `test_the_changelog_pin_counts_and_the_row_figure_are_the_code_s` fail with "the CHANGELOG says 23 pinned classes".
- B153 result is CRASH (killed by a crash, an allowed kind for that row), not a plain test failure.

## Fail-before (tests/test_bindguard.py of the new head run on 83cdb7a2 source; 12 failed, 289 passed)
Fail on old: test_the_classes_are_pinned_when_the_receiver_is_imported_not_at_the_first_question, test_the_lists_of_trusted_classes_are_exactly_these_literals, test_every_build_argument_is_either_recorded_as_an_override_or_named_as_not_a_service, test_the_last_level_judges_an_atom_like_every_other_level, test_a_function_or_a_name_put_on_the_core_runtime_instance_is_counted, test_a_member_of_the_core_runtime_that_is_not_the_one_build_made_is_counted, test_hold_run_ids_replaced_on_a_real_runtime_cannot_be_reached_from_a_post, test_a_runtime_made_by_hand_with_stand_ins_only_is_not_believed, test_a_request_scans_the_store_the_runtime_holds_once_and_stays_within_one_budget, test_one_request_is_bounded_by_one_budget_when_every_object_is_big, test_models_now_with_a_replaced_module_name_is_counted, test_the_changelog_pin_counts_and_the_row_figure_are_the_code_s.
New tests that PASS on old source, each labelled PIN in its docstring: the_search_of_the_approvals_folder_is_not_vacuous, a_service_of_the_core_runtime_that_is_not_a_stand_in_is_counted, the_runtime_stays_believed_after_a_run_and_a_tick, a_class_name_whose_value_pretends_to_be_a_type_is_not_a_class (old already used issubclass(type(cls), type); row B251 kills the isinstance form), all_thirteen_data_classes_stay_as_pinned_after_use_in_a_fresh_interpreter (row B252), a_model_row_visited_is_charged_the_stand_in_weight_each_time (row B219), copying_an_object_of_a_pinned_class_does_not_change_the_answer (row B256).

## Rows run alone (tests/bind_mutants.py "<id> ")
KILLED by their named test with the stated reason: B236-B248, B250, B251, B252, B254, B255, B256, B249, B215, B239, B57, B165, B137, B146, B161, B182, B209, B210, B211, B212, B213, B214, B218, B219, B232, B31. B153: CRASH (accepted kind). B249, B250, B215, B239, B57, B165, B256 were first BAD (survived / wrong reason / snippet moved) and were fixed (test re-pointed or row text corrected), then re-run and killed. Rows B221, B230, B231 merged into B31/B210 (comment in the table). Table now 244 rows.

## Runs
- Python 3.13: tests/test_bindguard.py + test_netguard + test_p7_tick + test_s5_runtime + test_s6_approvals: 376 passed, 1 skipped. Python 3.12: tests/test_bindguard.py 301 passed, 1 skipped. Python 3.14: not run.
- ruff check, ruff format --check, bandit -ll on changed files: clean.
- Measured per request, before authentication (CHANGELOG): 1,000 mixed rows ~40 ms; 2,400 rows ~95 ms; worst case (store, channel, runtime llm each 150,000 values) ~61 ms.

## Per class
A last-level atom judge (`_atom_plain`, B236-B238). B instance shadow: seal_runtime, instance keys, sealed members, hooks fields (B239-B248), hold_run_ids recorded (B247). C vacuous test fixed. D one `Scan` per request (B249, B250). E mutant rows (B232, B219, B57, B212-B214, B210/B231 merge, B31/B221 merge, B224 note, pin labels). F CHANGELOG/text + parsing test. G fresh-interpreter test, live_class spoof pin (B251, B252). H `models.datetime` and `models.UTC` pinned (B254, B255).
