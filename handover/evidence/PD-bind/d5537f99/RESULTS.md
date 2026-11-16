# EVIDENCE RUNNER results: PD-bind round 5, head d5537f99852b39c12721cfe053bd284c73bc1a81

Runner only records. Raw logs: /home/user/build/evidence-raw/pdbind-r5/ ; probes: /home/user/build/pdbind-r5-probes/ ; worktree /home/user/build/ER-pdbind-r5 (detached, HEAD = head above, status clean).

## Deviations (first)
1. Fail-before: **19 failed, 158 passed, 1 skipped** (builder reported 29). I ran only tests/test_bindguard.py (the only changed test file) with the head's tools/server_scan.py and tests/bind_mutants.py copied onto ddf930f8, src from ddf930f8 (import path checked). test_a_forged_class_with_the_same_module_and_name_is_not_a_stand_in is not in the failed list (passes on old code, as expected). The gap of 10 to the builder's 29 is not explained by me.
2. A first report of mine was handed back before the suite finished (instruction); this file completes it.
3. DIFF on probes (see probes logs): (a) del a._config works (no __delattr__ guard); (b) real channel put in then slot deleted: real_now raises AttributeError, stdlib server prints a traceback and the client sees RemoteDisconnected (no 503); (c) object.__setattr__(a,"_config",None) then POST on public bind, stand-ins only: 401, still served; (d) patching a method before the first question is not seen (True; stated "not promised"); (e) a list of exactly 100000 ints reads as real (other dict values count toward the budget); (f) Approvals.__setattr__ replaced at class level lets a._channel = x through (outside the guard by the docstring). Scan does not see _socket.socket().bind, socket.socket().bind, getattr(socketserver, ...).
4. heavy.sh priority is derived from the folder name (pdbind gives 2); I could not make it low, used nice 19. IPv6 loopback test skipped (no IPv6 here).
5. bandit -ll -r src: Medium 0, High 0. CI form (src demos tools): exit 0.

## Results
| # | Item | Exit | Last line |
|---|---|---|---|
| 1 | full suite, not live and not perf (heavy.sh) | 0 | 10778 passed, 2 skipped, 28 deselected in 277.59s |
| 2a | tests/bind_mutants.py | 0 | 130 of 130 good; problems: [] |
| 2b | tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] (git status empty after) |
| 3 | fail-before test_bindguard.py on ddf930f8 src | 1 | 19 failed, 158 passed, 1 skipped |
| 4a | ruff check | 0 | All checks passed! |
| 4b | ruff format --check src tests demos tools | 0 | 326 files already formatted |
| 4c | bandit -ll -r src / CI form | 0 / 0 | Medium 0, High 0 |
| 4d | tools/scan_repo.py | 0 | no output |
| 4e | gitleaks origin/main..HEAD (10 commits) | 0 | no leaks found |
| 4f | check-no-handover-files.sh wip/cloud-pd-bind <sha> | 0 | no output |

Failed ids before the change (raw: fail-before-ids.txt):
tests/test_bindguard.py::test_the_listener_reaches_the_approvals_only_through_the_signature_check
tests/test_bindguard.py::test_held_is_required_everywhere_it_decides
tests/test_bindguard.py::test_no_registration_door_exists_and_the_five_are_a_literal_of_pairs
tests/test_bindguard.py::test_a_method_replaced_on_a_base_class_or_changed_bases_read_as_real
tests/test_bindguard.py::test_changed_bases_of_a_stand_in_read_as_real
tests/test_bindguard.py::test_a_base_swapped_for_a_copy_with_the_same_attributes_reads_as_real
tests/test_bindguard.py::test_a_module_that_is_not_imported_or_whose_name_was_rebound_gives_real
tests/test_bindguard.py::test_the_class_is_looked_up_in_the_module_dictionary_not_with_getattr
tests/test_bindguard.py::test_a_cleared_pin_of_a_class_that_was_seen_fails_closed
tests/test_bindguard.py::test_a_subclass_of_a_listed_class_is_not_that_class
tests/test_bindguard.py::test_a_module_that_is_not_a_plain_module_gives_real
tests/test_bindguard.py::test_an_instance_with_more_values_than_the_budget_reads_as_real
tests/test_bindguard.py::test_a_detector_list_with_a_function_a_patched_method_or_a_foreign_container_reads_as_real
tests/test_bindguard.py::test_a_detector_list_nested_or_cyclic_is_read_without_recursion_errors
tests/test_bindguard.py::test_a_function_hidden_inside_a_stand_in_reads_as_real_up_to_the_depth_limit
tests/test_bindguard.py::test_an_approvals_refuses_plain_writes_a_class_swap_and_weak_references
tests/test_bindguard.py::test_a_class_swapped_with_the_object_level_write_is_answered_503
tests/test_bindguard.py::test_a_hostile_key_or_mapping_makes_the_answer_real_and_never_raises
tests/test_bindguard.py::test_a_refused_request_is_logged_once_a_minute_per_set_of_services

## Probes
Full outcome lines in probes-standins.log, probes-approvals.log, probes-scan.log, probes-importbind.log (import-time bind: 108 modules, 0 errors, no bind or listen calls). Refusal log: two refused requests back to back give 1 line; a different service set within 60 s gives a second; same set after 61 s (clock patched) gives a third.

## Cleanup
Postgres stopped; extra worktree ER-pdbind-r5-old removed; ER-pdbind-r5 kept. Nothing committed or added to git.

## Lead note (added when saved)
This is the COMPLETE runner result for d5537f99 (full suite 10778 passed 2 skipped exit 0; bind mutants 130/130; stage 37/37; lint, bandit, scan, gitleaks and handover check exit 0). Open discrepancy: fail-before gave 19 failed where the builder reported 29; unexplained, to be re-checked on the batch 6 head. The head is STALE for decisions: round 5 found 5 Majors and batch 6 (builder a0347669) replaces it.
