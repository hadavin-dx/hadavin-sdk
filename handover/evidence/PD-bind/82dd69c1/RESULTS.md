# PD Part 2 bind guard, round 11: evidence (records only, no judgement)

Head under test: `82dd69c12f506b9484de7e9ec59593fa943b86e7` (origin/wip/cloud-pd-bind). Older heads: `304c3bd3` (batch 10), `83cdb7a2` (batch 9). Raw logs: `/home/user/build/evidence-raw/pdbind-82dd69c1/`; copies of the key ones sit next to this file. Nothing was committed or pushed by the runner.

## 0. Not run, deviations, things to know first
- NOT RUN (lead order): full pytest, Playwright, the full 263-row bind mutant table (94 rows run: 34 listed + 60 sampled), Python 3.14.
- Item 7: "replace a toolbox member" and "replace an existing tool in hooks.tools" are NOT applicable in the fixture app: `hooks.toolbox` is None and `hooks.tools` is empty, so I could only add a tool to `hooks.tools` and put a new object into `hooks.toolbox`. I did not build a fixture with a real toolbox, so toolbox-member replacement was not run.
- Item 7, one hostile input was SERVED, not refused: replacing the `hooks.tools` field with an equal copy (an empty dict `dict(old_tools)`) is believed (control line 1c). Raw result only; no judgement.
- Item 6 label error in my probe: the line "seal compare alone (_runtime_ok, no scan of rows)" is mislabelled. `_runtime_ok(rt)` with no scan object still checks the store as a stand-in, so it reads the rows (its 40.9 / 101.3 ms equals the whole `real_now` time). I did NOT measure the seal compare separately from the row scan; there is no separate figure.
- Item 4 note: counts include string-literal mutant source in `tests/bind_mutants.py` (lines inside quoted mutant code), counted as the grep sees them.
- Focused runs used pytest `-x` (stop at first failure); both finished with 0 failures, so it changed nothing.
- Python 3.12 = system 3.12.3 (venv `ER-pdbanner11-venv312`, pytest only, hadavin_sdk via PYTHONPATH); 3.13 = 3.13.18 (`q8c1-b17fix/.venv`). `hadavin_sdk.__file__` printed under `/home/user/build/ER-pdbind11/src/` at the top of every log (also in the old-tree logs: under ER-pdbind11-old0 / old1).
- Env names unset for all runs: AWS_*, ANTHROPIC_*, GH_TOKEN, GITHUB_TOKEN. No script prompt appeared; no network, no spend, no model call.
- bandit: installed `/root/.local/bin/bandit` 1.9.4 (not in the venv).
- 3 mutant rows are verdict CRASH (the runner counts them good): B22, B123, B153. 91 KILLED.

## Table
| # | item | exit | result line |
|---|---|---|---|
| 1a | focused tests py3.12 (test_bindguard, test_netguard, test_p7_tick, test_s5_runtime, test_s6_approvals) | 0 | 385 passed, 1 skipped in 47.66s |
| 1b | same py3.13 | 0 | 385 passed, 1 skipped in 45.12s |
| 2 | mutants, 34 listed rows + 60-row sample (seed 11) | 0 (12 slices) | 94 rows: 91 KILLED, 3 CRASH, 0 SURVIVED, 0 BAD |
| 3a | head's test_bindguard.py on 304c3bd3 src | 1 | 9 failed, 301 passed, 1 skipped in 33.30s |
| 3b | head's test_bindguard.py on 83cdb7a2 src | 1 | 22 failed, 288 passed, 1 skipped in 34.32s |
| 4 | suppression markers added | n/a | noqa 31, type-ignore 212, pragma-no-cover 1, fmt-skip 0 (see section 4) |
| 5 | ruff check / ruff format --check / bandit -ll | 0 / 0 / 0 | All checks passed; 326 files already formatted; bandit no findings |
| 6 | per-request cost | 0 | 1000 rows 40.7-52.1 ms; 2400 rows 103.1-109.6 ms |
| 7 | hostile inputs | 0 | see section 7 |

## 1. Focused tests
Skip is the same one as before (no IPv6 loopback). Logs: focused-py312.log, focused-py313.log.

## 2. Mutants (tests/bind_mutants.py, run as `python tests/bind_mutants.py "B257 " ...`; names end in a space so "B25 " cannot match "B250")
Listed rows run (34 of 34 asked; none missing): B257-B272 (16), B221, B230, B231, B244-B248, B31, B98, B210, B211, B214, B219, B239-B242. All KILLED. B98 KILLED by test_a_base_swapped_for_a_copy_with_the_same_attributes_read (it SURVIVED on 304c3bd3 in the previous evidence). (B253 does not exist; it is not in the asked list.)
Sample (60 rows, `random.Random(11).sample` of the 229 rows not listed, sorted): B2 B4 B8 B10 B11 B16 B17 B22 B24 B25 B38 B43 B50 B51 B53 B62 B64 B81 B83 B90 B109 B121 B123 B124 B126 B127 B128 B130 B136 B139 B140 B141 B144 B146 B153 B160 B161 B162 B163 B167 B169 B171 B172 B173 B176 B177 B179 B187 B199 B209 B216 B218 B228 B235 B236 B237 B238 B243 B249 B256. 57 KILLED + 3 CRASH (B22, B123, B153). Per-row lines: mutant-verdicts.txt (94 lines); slice logs raw dir mut-00..11.log (each ends "N of N good; problems: []").
Leftover mutation check: `git status --short` and `git diff --stat` in the worktree after all 12 slices: both empty (runner works on temp copies).

## 3. Fail-before (head's tests/test_bindguard.py and tests/bind_mutants.py copied onto detached worktrees; PYTHONPATH on each)
304c3bd3: `9 failed, 301 passed, 1 skipped in 33.30s`. Failing: test_changelog_numbers_and_lists_are_the_ones_in_the_code, test_a_tool_put_into_the_hooks_of_a_sealed_runtime_is_counted, test_the_toolbox_and_the_executor_of_a_sealed_runtime_cannot_be_changed_unseen, test_the_code_and_the_closure_cells_of_a_hook_function_cannot_be_rewritten_unseen, test_the_judged_names_of_a_runtime_are_all_its_keys, test_a_kinds_or_evidence_put_on_the_core_runtime_is_counted, test_a_sealed_runtime_that_is_dropped_is_freed, test_the_seal_is_private, test_an_object_read_after_the_budget_ran_out_is_not_blamed_for_it.
83cdb7a2: `22 failed, 288 passed, 1 skipped in 34.32s`. Failing (22): the 9 above plus test_the_classes_are_pinned_when_the_receiver_is_imported_not_at_the_first_question, test_the_lists_of_trusted_classes_are_exactly_these_literals, test_every_build_argument_is_either_recorded_as_an_override_or_named_as_not_a_service, test_the_last_level_judges_an_atom_like_every_other_level, test_a_function_or_a_name_put_on_the_core_runtime_instance_is_counted, test_a_member_of_the_core_runtime_that_is_not_the_one_build_made_is_counted, test_hold_run_ids_put_into_the_hooks_of_a_real_runtime_is_refused_on_a_public_bind, test_a_runtime_made_by_hand_with_stand_ins_only_is_not_believed, test_a_request_scans_the_store_the_runtime_holds_once_and_stays_within_one_budget, test_one_request_is_bounded_by_one_budget_when_every_object_is_big, test_models_now_with_a_replaced_module_name_is_counted, test_the_changelog_pin_counts_and_the_row_figure_are_the_code_s, test_the_pin_count_check_notices_a_count_off_by_one.
The head's mutant runner on each old tree (row "B98 "): raises `RuntimeError: the unmutated copy does not pass its tests` (rc=1) on both, because the copied tests fail on old code. So no mutant verdict exists for the old trees. Logs: fb-old1-304c3bd3.log, fb-old0-83cdb7a2.log; failing names: fb-old*-names.txt.
Total test functions in head test_bindguard.py: 223 (grep "def test_"). Not computed: which of the new tests are labelled PIN or pass on old code (only the failing lists above were recorded).

## 4. Suppressions (git diff origin/main...82dd69c1, added lines only; also in suppression-table.txt)
Added: noqa 31 (codes: BLE001 23, S603 4, F401 3, S311 1), `type: ignore` 212, `pragma: no cover` 1, `fmt: skip` 0, nosec 0.
By file: src/bindguard.py noqa 2 + type-ignore 2; src/standins.py noqa 2 + type-ignore 9; src/approvals/receiver.py noqa 3; src/approvals/requests.py noqa 2; tools/server_scan.py type-ignore 2; tests/test_bindguard.py noqa 9 + type-ignore 190 + pragma 1; tests/bind_mutants.py noqa 12 + type-ignore 9 (inside quoted mutant source); tests/test_netguard.py noqa 1.
Raw counts of the same markers in the same 23 changed files (files that exist on that revision): origin/main noqa 36, type-ignore 1, pragma 0, fmt-skip 0, nosec 2; head noqa 67, type-ignore 213, pragma 1, fmt-skip 0, nosec 2.

## 5. Lint
`ruff check src tests demos tools`: All checks passed! (ruff 0.17.1, rc 0). `ruff format --check src tests demos tools`: 326 files already formatted (rc 0). `bandit -q -ll` on the changed src and tools files: rc 0, only "Test in comment ... not a test name" warnings; on `-r src demos tools`: rc 0, only the "nosec encountered (B102) ... tools.py:389" warning, no findings.

## 6. Cost per request (`Approvals.real_now()`, three runs each; cloud container, one other process running at times, not isolated)
- 1000 mixed rows: 43.0, 52.1, 40.7 ms; store scanned 1x; 101,710 values charged (budget 250,000); result ().
- 2400 mixed rows: 109.6, 104.7, 103.1 ms; store scanned 1x; 243,810 values charged; result ().
- store + channel + runtime.llm with 150,000 values each: 122.0, 124.9, 119.9 ms; store scanned 1x; 249,666 charged; answer: held channel "not read in full ... MemoryStore used most of the budget", held on_decided function.
- `_runtime_ok(rt)` x1000 on 1000 rows: 40.856 s total (40.9 ms each); on 2400 rows 101.289 s (101.3 ms each). Mislabelled in the log as "no scan of rows": see section 0. The seal compare alone was not separated out.
Compare 304c3bd3: 1000 rows 43.6/44.6 ms, 101,710 values; 2400 rows 105.1/104.0 ms, 243,810 values.

## 7. Hostile inputs (serve on 0.0.0.0, runtime in the on_decided holder; REFUSED/SERVED; probes.py `hostile`; raw: probe-hostile.log)
- control: SERVED. Hooks fields: execute, hold_run_ids, level_override, post_card, request_approval, restored_key, rollback, toolbox, tools, validate_proposal, verify; hooks.tools empty; toolbox None.
- Assign into hooks.tools (`hooks.tools['probe-tool']=fn`): REFUSED; after removing it: SERVED. hooks.tools field replaced by an equal empty copy dict: SERVED. hooks.toolbox = object(): REFUSED. Replacing an existing tool / a toolbox member: not run (none exist in the fixture).
- Closure cells rewritten (one at a time, restored after): hooks.post_card cell 0: REFUSED; hooks.request_approval cells 0, 1, 2: REFUSED each. execute/verify/rollback are methods with no cells; hold_run_ids/level_override None. After restoring: SERVED.
- `_kinds`: own['_kinds'] replaced by another frozenset: REFUSED; the same plus one name: REFUSED; a plain set with the same names: REFUSED; a frozenset subclass with the same names and its own __contains__: REFUSED; restored: SERVED. `Runtime._kinds` put on the class: REFUSED; deleted again: SERVED. Hand-built `object.__new__(Runtime)` with the same dict incl. _kinds: REFUSED.
- Drop a sealed runtime, then gc: seals 1 -> 2 after a second app -> 3 after a third; after dropping the third app's runtime and gc x3: runtime alive False, seals 2 (weak, freed). A hand-built runtime made after the collection: REFUSED. Real runtime control: SERVED.

## Cleanup
Worktrees ER-pdbind11, ER-pdbind11-old0, ER-pdbind11-old1 removed; no process of mine left running; no commit, no push; nothing written under handover/ except this evidence folder (uncommitted, for the lead).
