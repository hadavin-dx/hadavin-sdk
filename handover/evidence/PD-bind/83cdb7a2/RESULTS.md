# EVIDENCE RUNNER results: PD part 2 batch 9, head 83cdb7a293b7d5ba7d79bedaf3c8990fe99c4ee4 (previous 3db352f5)

Records only; no judgement. Not committed or pushed. Raw logs: /home/user/build/evidence-raw/pdbind9-runner/. Worktree: /home/user/build/wt/ER-pdbind9 (HEAD equals the sha, status clean at start and at end). Python 3.13, venv ER-pdbind8-venv, cloud AWS_* variables unset for every run.

## What failed or deviated (first)
1. **bind_mutants row B153 is BAD at 83cdb7a2: SURVIVED** ("a hostile text key is shown again in its own handler"; allow_crash row, killer test_a_hostile_text_key_gets_a_fixed_label_and_nothing_is_called_on_it_again). Same row on 3db352f5 (its own tests): good, CRASH. Rerun alone at head: SURVIVED again (b153-head.log). Row text is unchanged in the delta; src/bindguard.py changed. 120 of 121 rows run were good.
2. **Probe finding (not a test failure):** a core Runtime held in the make_on_decided holder with an INSTANCE-level function (e.g. rt.execute = lambda, rt.handle = lambda, or an extra function attribute) is NOT counted: serve() on 0.0.0.0 is served (control, unchanged runtime: also served). Replacing rt.llm or rt.store is refused. A Runtime SUBCLASS and a patched Runtime class are refused. Probe: probe3.py.
3. Venv deviation: the venv's .pth points at /home/user/build/ER-pdbind8/src (stale). I set PYTHONPATH=<worktree>/src for every run and checked hadavin_sdk.__file__ resolves to the worktree (and to the old tree for fail-before). No new venv, no pyproject/uv.lock change.
4. Own slips: (a) first mutation driver ran the baseline once per row (slow); stopped my own task and rewrote it to batches of 10; (b) one early check of the 3 "pass on old code" tests ran against the NEW src by mistake (a cd inside env.sh) and was redone correctly; (c) my first probe set used an invented attribute name (on_approval) and a wrong module for is_stand_in_object; fixed and rerun; (d) my first plain gitleaks run scanned all 362 branches of the shared repo (1,958 findings from other branches); rerun restricted to history reachable from the head.
5. stage_mutants first sat in the heavy-slot queue about 7 minutes behind other jobs; it finished.

## (1) Focused tests
- tests/test_bindguard.py + tests/test_repo_rules.py: exit 0, 325 passed, 1 skipped (tests/test_bindguard.py:479 "this machine has no IPv6 loopback") in 30.11 s.
- git diff 3db352f5 83cdb7a2 --name-only touches only tests/test_bindguard.py and tests/bind_mutants.py (not a pytest file); src files: approvals/receiver.py, approvals/requests.py, bindguard.py, runtime/agent_loop.py, standins.py; CHANGELOG.md. No other test file touched.

## (2) Fail-before (new tests/test_bindguard.py against src of 3db352f5)
Tree: git archive 3db352f5 + new test file. Result: **25 failed, 260 passed, 1 skipped (286 collected)**, exit 1. Matches the builder's 25. (Builder says 285 tests; 285 passed+failed plus 1 skipped.)
Failing by name (25):
- test_the_eight_pinned_plain_classes_hold_no_class_level_mutable_value
- test_the_classes_are_pinned_when_the_receiver_is_imported_not_at_the_first_question
- test_the_lists_of_trusted_classes_are_exactly_these_literals
- test_a_container_referenced_many_times_is_charged_each_time_it_is_entered
- test_the_walk_of_a_detector_list_is_charged_for_every_visit
- test_a_stand_in_is_charged_twenty_values_and_a_few_thousand_references_are_fine
- test_the_class_level_attributes_of_the_pinned_classes_are_functions_or_builtin_descriptors
- test_a_fixed_clock_with_a_foreign_tzinfo_is_counted_and_never_runs_it
- test_a_clock_swapped_in_after_the_start_is_answered_503_and_never_runs
- test_the_clock_of_build_is_judged_like_the_clock_set_later
- test_models_now_with_its_code_replaced_is_counted
- test_a_stand_in_holding_a_datetime_with_a_foreign_tzinfo_reads_as_real
- test_a_path_with_a_real_object_in_a_slot_reads_as_real
- test_a_class_patched_before_the_first_question_reads_as_real
- test_a_hand_built_runtime_in_a_holder_is_counted_and_a_hand_built_approvals_gets_no_belief
- test_a_serve_of_an_approvals_class_with_a_replaced_method_is_refused_before_anything_else
- test_a_thousand_row_store_is_a_stand_in_and_answers_401_not_503
- test_a_store_over_the_budget_is_named_over_budget_and_a_real_object_is_named_real
- test_a_thousand_rows_use_at_most_half_the_budget
- test_a_refusal_text_cannot_imitate_a_line_of_its_own
- test_the_changelog_states_the_pin_moment_the_budget_row_count_and_the_boundary
- test_the_depth_is_eight_levels_below_the_own_dictionary_and_the_texts_say_so
- test_a_core_runtime_whose_class_was_patched_is_counted
- test_a_card_with_a_slot_reads_as_real
- test_a_holder_key_that_is_a_text_subclass_runs_no_code_of_its_own
The three named tests: test_a_text_or_number_subclass_is_not_a_plain_atom PASSED on old src; test_every_build_argument_is_either_recorded_as_an_override_or_named_as_not_a_service PASSED on old src; test_the_changelog_states_the_pin_moment_the_budget_row_count_and_the_boundary: FAILED when the old CHANGELOG.md is used (that is the 25 above), PASSED when the new CHANGELOG.md is copied in (then test_changelog_numbers_and_lists_are_the_ones_in_the_code fails instead; count still 25: failbefore2.log). The builder's claim holds only with the new CHANGELOG ("copy src files only").

## (3) bind_mutants (chunked, checkpoint file ckpt-sel.jsonl, each chunk under 8 min, no full run)
Table: **227 rows** on Python 3.13 (old head: 198 rows; 29 added, 0 removed, 24 changed by comparing Mutant records; 11 allow_crash rows). Selected 121 = 29 added + 24 changed + 11 crash + 60 sample (seed 9, from the rest). Result: **120 good, 1 BAD (B153)**; verdicts KILLED 110, CRASH 10, SURVIVED 1.
By set: added 29/29 good; changed 24/24 good; sample 60/60 good; crash rows 10/11 good (B153 the one). B197 (ran in a batch, not alone; no memory problem seen) KILLED/CRASH good: see table.
**B57**: KILLED by test_serve_refuses_a_subclass_and_a_look_alike_of_the_approvals, good. **B196**: KILLED by test_the_walk_of_a_detector_list_is_charged_for_every_visit, good.
Per-row table: /home/user/build/evidence-raw/pdbind9-runner/mut-table.md. NOT RUN: the other 106 rows (full run left for the laptop). Python 3.14 row count (226) not checked (only 3.13 here).

## (4) stage_mutants: **37 of 37 good; problems: []** (stage.log).

## (5) Lint and scans
- ruff check: exit 0, "All checks passed!"
- ruff format --check: exit 0, "330 files already formatted"
- bandit -q -r src demos tools -ll (as ci.yml): exit 0, 0 issues (warnings only: comment text read as test names, one nosec B102 with no finding at src/hadavin_sdk/tools.py:389).
- tools/scan_repo.py: exit 0.
- gitleaks (--log-opts head sha, 90 commits): exit 0, no leaks. Delta 3db352f5..83cdb7a2 (1 commit): exit 0. Unrestricted run (all 362 branches, 6,134 commits): exit 1, 1,958 findings; not the head's history.
- check-no-handover-files.sh wip/cloud-pd-bind 83cdb7a2: exit 0.

## (6) Hostile probes (made-up data; probes.py, probe2.py, probe3.py, probes.log)
- Approvals subclass instance to serve(): REFUSED ("serve needs an Approvals made by the core (not a subclass or a look-alike)").
- Approvals class method patched (receive): REFUSED ("the Approvals class was changed after it was pinned").
- Approvals instance with replaced held_services: cannot be set (AttributeError "an Approvals is set once"), so nothing to serve; unchanged object served (control).
- Runtime subclass in holder: REFUSED (held on_decided). Runtime.__init__ patched: REFUSED. Runtime instance with instance-level execute/handle/extra function: SERVED (see failure 2).
- Clock with foreign tzinfo (recording tzinfo): clock counted in held_services, tzinfo code ran 0 times, serve REFUSED (held clock); fixed-offset timezone also counted.
- 2,000 shared detectors: is_stand_in_object True (pass); 7,500: False (refused).
- 1,000-row store: verdict stand-in; unsigned POST answered HTTP 401 (not 503).
- Refusal text: newline, ANSI escape, CR LF imitation of a line, NUL, bidi override all shown as "(unreadable)"; reasons with ANSI or a newline are rejected.

## Processes
Started and ended: pytest runs, chunk.py batches, stage_mutants, probes, gitleaks. One background task I stopped with TaskStop (first slow mutation driver). No pkill. Nothing of mine left running; git status of the worktree clean. Other agents' processes (pdbanner, q8c1) were running and untouched. Own token use not measurable here.

RUN ON LAPTOP: hadavin-sdk 83cdb7a293b7d5ba7d79bedaf3c8990fe99c4ee4 pytest -q full + bind_mutants complete
