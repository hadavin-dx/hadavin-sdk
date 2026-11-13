# PD Part 2 bind guard, round 10: evidence (records only, no judgement)

Head under test: `304c3bd34c50d740385003cf9b87168345c9d48d` (origin/wip/cloud-pd-bind). Old code: `83cdb7a2`. Raw logs: `/home/user/build/evidence-raw/pdbind-304c3bd3/`.

## 0. Not run, deviations, things to know first
- NOT RUN (lead order): full pytest, Playwright, the complete 244-row bind mutant table, Python 3.14 run.
- Mutants: only the listed rows plus a 60-row sample (seed 10); 98 rows run of 244 (3.13 list). **B224 does not exist** in the table (its own docstring says it was merged away in batch 9), so it was not run. Listed rows run: 38 of 39 asked (B224 missing); sample: 60.
- Focused tests: the five files named. The grep for other files importing bindguard/standins/receiver found none beyond those five (focused-files.txt).
- Python 3.12 used is the system 3.12.3 (not a newer 3.12); 3.13 is 3.13.18. Two separate venvs, `PYTHONPATH` on the worktree `src`; `hadavin_sdk.__file__` printed inside the worktree each time (build tree, old tree, probes).
- Environment names present and unset for every run: GH_TOKEN, GITHUB_TOKEN, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_CA_BUNDLE, ANTHROPIC_BASE_URL (values never read or printed). ANTHROPIC_API_KEY not present.
- `uv sync --locked` was run with `--all-extras --group test`.
- bandit: not in the venv; ran the installed `/root/.local/bin/bandit` 1.9.4 (python 3.13). It printed warnings "nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389" (recorded, exit 0).
- **FAILED row (item 3): B98 "the mro is not compared" SURVIVED on 304c3bd3** (twice, also alone: B98-rerun.out). On 83cdb7a2 the same row is KILLED by `test_a_base_swapped_for_a_copy_with_the_same_attributes_read...` (B98-on-old.out). So the row stopped being killed between 83cdb7a2 and 304c3bd3.
- Item 4 counts match the builder claim: 12 failed, 289 passed, 1 skipped on 83cdb7a2. But of the 8 tests with PIN in their docstring, 7 pass on old (as a pin should) and 1 (`test_every_build_argument_is_either_recorded_...`) fails on old.

## Table
| # | item | command (short) | exit | last line |
|---|---|---|---|---|
| 1a | focused tests py3.12 | pytest tests/test_bindguard.py test_netguard test_p7_tick test_s5_runtime test_s6_approvals | 0 | 376 passed, 1 skipped in 50.31s (skip: no IPv6 loopback, test_bindguard.py:479) |
| 1b | focused tests py3.13 | same | 0 | 376 passed, 1 skipped in 48.30s (same skip) |
| 2a | ruff check src tests demos tools | ruff check | 0 | All checks passed! |
| 2b | ruff format --check | ruff format --check | 0 | 326 files already formatted |
| 2c | bandit -q -r src demos tools -ll | bandit | 0 | only nosec warnings, no findings printed |
| 2d | gitleaks origin/main..HEAD (26 commits) | gitleaks git --redact | 0 | no leaks found |
| 3a | new/re-pointed rows (38 rows) | tests/bind_mutants.py <rows> | 0 | all 38 KILLED or CRASH, all "good" |
| 3b | 60-row sample, seed 10 | same, 6 slices of 10 | 1 (slice 09) | 59 of 60 good; BAD: B98 SURVIVED |
| 3c | leftover mutation | git status, git diff | 0 | status empty, diff empty |
| 4 | new test file on 83cdb7a2 | pytest tests/test_bindguard.py (old src) | 1 | 12 failed, 289 passed, 1 skipped |
| 5 | probes | probes.py | 0 | see section 5 |

Item 3 verdict counts over all 98 rows: 93 KILLED, 4 CRASH (counted good by the runner; includes B153), 1 SURVIVED. Per-row verdicts: `mutant-verdicts.txt`; names list: `mutant-names.txt` (N = new/re-pointed, S = sample).

## 4. Fail-before (new test_bindguard.py from 304c3bd3 run on 83cdb7a2 src)
By AST: old file 198 test functions, new 214; 16 new, 11 changed, 0 removed (ast-count.txt). 8 carry PIN in the docstring.
FAIL on old (12) with first failing line:
1. test_the_classes_are_pinned_when_the_receiver_is_imported_not_at_the_first_question: the pins were not all taken at import
2. test_the_lists_of_trusted_classes_are_exactly_these_literals: module has no attribute HOOKS
3. test_every_build_argument_is_either_recorded_as_an_override_or_named_as_not_a_service: names recorded in build() are [channel, detector, llm, secrets, sources, tools]
4. test_the_last_level_judges_an_atom_like_every_other_level: a datetime with a foreign tzinfo at the last level was trusted
5. test_a_function_or_a_name_put_on_the_core_runtime_instance_is_counted: an instance-level on_decided was not counted
6. test_a_member_of_the_core_runtime_that_is_not_the_one_build_made_is_counted: a replaced registry was not counted
7. test_hold_run_ids_replaced_on_a_real_runtime_cannot_be_reached_from_a_post: a hold_run_ids put into the hooks was believed
8. test_a_runtime_made_by_hand_with_stand_ins_only_is_not_believed: an unsealed copy of the runtime was believed
9. test_a_request_scans_the_store_the_runtime_holds_once_and_stays_within_one_budget: the store was scanned 2 times in one request
10. test_one_request_is_bounded_by_one_budget_when_every_object_is_big: control: three 150,000-value objects were not over one budget together
11. test_models_now_with_a_replaced_module_name_is_counted: models.now with a replaced datetime was not counted
12. test_the_changelog_pin_counts_and_the_row_figure_are_the_code_s: module has no attribute HOOKS
PASS on old, new or changed tests (15): test_the_search_of_the_approvals_folder_is_not_vacuous, test_a_service_of_the_core_runtime_that_is_not_a_stand_in_is_counted, test_the_runtime_stays_believed_after_a_run_and_a_tick, test_a_class_name_whose_value_pretends_to_be_a_type_is_not_a_class, test_all_thirteen_data_classes_stay_as_pinned_after_use_in_a_fresh_interpreter, test_a_model_row_visited_is_charged_the_stand_in_weight_each_time, test_copying_an_object_of_a_pinned_class_does_not_change_the_answer, test_serve_refuses_a_subclass_and_a_look_alike_of_the_approvals, test_the_eight_pinned_plain_classes_hold_no_class_level_mutable_value, test_serve_refuses_with_bind_refused_when_any_slot_is_deleted, test_models_now_with_its_code_replaced_is_counted, test_a_serve_of_an_approvals_class_with_a_replaced_method_is_refused_before_anything_else, test_a_thousand_row_store_is_a_stand_in_and_answers_401_not_503, test_a_thousand_rows_use_at_most_half_the_budget, test_the_changelog_states_the_pin_moment_the_budget_row_count_and_the_boundary.
The 7 PIN-labelled ones that pass on old: the first seven names in that list that are PIN-labelled (search_of_approvals_folder, service_of_core_runtime, runtime_stays_believed, class_name_pretends, all_thirteen_data_classes, model_row_visited, copying_an_object).
(Only tests/test_bindguard.py and tests/bind_mutants.py changed in tests/; bind_mutants.py was not run against the old tree except row B98.)

## 5. Hostile probes (probes.py, probes.out, probes-b2.out; hadavin_sdk file inside the worktree)
(a) Serve on 0.0.0.0 with a real-service-free config, runtime in the on_decided holder. Untouched runtime: SERVED (control). REFUSED: instance attribute execute, handle, tick, on_decided, extra (callable and 1); swapped agents, limits, audit, registry, hooks (copy.copy); hooks.hold_run_ids, hooks.execute, hooks.post_card replaced; object.__new__(Runtime) with copied dict (with and without extra). After restore: SERVED.
(b) Value at the last level, store.extra wrapped k times in a list (k = 5..11): datetime with hostile tzinfo: real at every k; Path with a real object in a slot: real at every k; real object: real at every k. Controls: plain datetime, str, int, plain Path: stand-in k<=8, real k>=9. Empty list: stand-in k<=7, real k>=8. So at k=9 and k=10 even plain values read as real.
(c) copy.copy(hooks) is a pinned instance of Hooks, but a runtime holding it is REFUSED; deepcopy(hooks) held: REFUSED. copy/deepcopy of the pinned classes (Hooks, Runtime, Approvals, MemoryStore, FakeLLM) return the same class object; asking again afterwards: SERVED (control answer, nothing changed). copy.copy(runtime) as holder: REFUSED. deepcopy(runtime): TypeError (cannot pickle a lock). deepcopy(approvals): TypeError.
(d) real_now() per request: 1000 mixed rows 43.6 and 44.6 ms, store scanned 1x, 101,710 values charged; 2400 rows 105.1 and 104.0 ms, 1x, 243,810 values (budget 250,000); store+channel+runtime.llm with 150,000 values each: 115.6 and 118.5 ms, store scanned 1x, 249,666 charged, answer: held channel over budget, held on_decided function. Machine: cloud container, one run at a time, no other load measured.
(e) allow_public_bind_reason: non-ASCII, \n, NUL, tab, DEL, bidi, zero-width, 201 chars: refused "must be one printable ASCII line of at most 200 characters"; 9 chars, empty, spaces only: refused "at least 10 characters"; 10 and 200 chars: allowed (the log line printed the reason in full, 200 'a' chars). Hosts shown in the refusal: non-ASCII, newline, ESC, NUL, bidi, bytes, None all shown as `'(unreadable)'`; a 5000-character host shown cut to 80 characters plus `...`.

## Cleanup
Detached worktrees removed, venvs and tmp removed (see end of run); no process left; no commit, no push.
