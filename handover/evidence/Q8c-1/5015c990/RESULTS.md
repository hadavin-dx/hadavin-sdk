# Evidence Q8c-1, head 5015c99057c8aa7d0968150e640afe0c4b735005 (previous fbc837b4, base origin/main 2a8c2aac)
Evidence runner. Records only; no judgment, no fix. Raw logs: /home/user/build/evidence-raw/q8c1-5015c990/.
HEAD confirmed equal to the sha above; the worktree was clean before and after the runs.

## Failed or not run (first)
1. NOT RUN: the flaky timing test (`test_the_timing_harness_flags_a_quadratic_stand_in`), 3 times on head and 3 on main. It needs all three heavy slots at once; other agents held them and my first attempt gave up after 100 s in the queue (rc 124). The ticket names no perf item.
2. EXPECTED ERRORS (recorded): the 12 Vault engine tests with HADAVIN_REQUIRE_VAULT_ENGINE=1 end as 12 errors ("HADAVIN_TEST_VAULT_ADDR is not set"), 8 other tests of the file pass. No Vault/OpenBao binary was downloaded.
3. Fail-before as asked (new test files and fixtures only, the base's own tools/ and src/): COLLECTION ERRORS on both bases, so no test of the three policy files ran. On fbc837b4: `tools.policy_page` has no attribute `note_problems`. On origin/main: `policy_page` cannot be imported from `tools` (the file does not exist there). See table below for the second variant.
4. `uv sync --locked --no-build` (the command of the brief) fails here: "hadavin-sdk editable can't be installed because it is marked as --no-build". I ran `uv sync --locked --all-extras --group test` instead (local build of the project itself; lockfile respected).
5. My first mutant run was cut by my own 110 s timeout (rc 124, tree stayed clean: `git status` empty); rerun with no timeout, result below.
6. CI's own steps were not run as CI runs them: the pytest step there sets HADAVIN_REQUIRE_VAULT_ENGINE=1 and a Vault service (not available here); the full run below had no Vault server, so 11 engine tests skipped as shown.

## Table (head)
| item | command | exit | last line |
|---|---|---|---|
| files changed vs origin/main | git diff --name-only origin/main...HEAD | 0 | 13 files: CHANGELOG.md, README.md, ci.yml, docs/declared-permissions.md, secrets_vault.py, signer_vault.py, sources/kubernetes.py, the sources fixture, tests/policy_mutants.py, test_policy_docs.py, test_policy_engine.py, test_policy_guard.py, tools/policy_page.py |
| files changed vs fbc837b4 | git diff --name-only fbc837b4 5015c990 | 0 | CHANGELOG.md, docs/declared-permissions.md, src/hadavin_sdk/actions/secrets_vault.py, tests/fixtures/policy_sources_2026-11-11.txt, tests/policy_mutants.py, tests/test_policy_guard.py, tools/policy_page.py |
| ruff check src tests demos tools | uv run --no-sync ruff check | 0 | All checks passed! |
| ruff format --check | same | 0 | 323 files already formatted |
| bandit -ll | uv run --with bandit bandit -q -r src demos tools -ll | 0 | only a "nosec B102 ... tools.py:389" warning line |
| scan_repo | python tools/scan_repo.py | 0 | (no output) |
| policy_page --check | python tools/policy_page.py --check | 0 | (no output) |
| stage_mutants | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| gitleaks origin/main..HEAD | gitleaks git --log-opts origin/main..HEAD | 0 | no leaks found |
| full pytest (own Postgres 16.15, port set in server and test env; via heavy.sh, no queue wait) | pytest -p no:cacheprovider -q -m "not live and not perf" -rs | 0 | 10857 passed, 13 skipped, 28 deselected in 281.20s |
| skips in the full run | -rs | | 1 in tests/contracts/test_llm.py:95 (Stubber), 12 in tests/test_policy_engine.py (needs a real Vault server; env not set) |
| policy_mutants alone after pytest | python tests/policy_mutants.py (all 3 slot locks held) | 0 | 89 of 89 good; problems: [] (builder said 89 of 89: same). It also prints: "first-line check is weak (killer asserts through same()) for 41 of 89 mutants" and a killer shared by more than one mutant (print only, exit 0) |
| Vault engine tests | HADAVIN_REQUIRE_VAULT_ENGINE=1 pytest tests/test_policy_engine.py | 1 | 8 passed, 12 errors (no Vault address) |

## Fail-before, variant 2 (new tests + fixture + head's tools/policy_page.py, base's own src/)
Needed because variant 1 only gave collection errors. Whole three files: fbc837b4 tree: 13 failed, 320 passed, 12 skipped. origin/main tree: 218 failed, 115 passed, 12 skipped.
New test functions (name not in fbc837b4's three files): 12. Result per id (fbc837b4 src | origin/main src):
- test_policy_guard.py::test_a_claim_with_no_mark_two_marks_or_a_stale_start_is_a_problem_and_a_missing_line_is_refused | PASSED | FAILED
- test_policy_guard.py::test_a_free_note_class_that_lists_a_source_its_entry_does_not_name_is_a_problem_of_the_check | PASSED | FAILED
- test_policy_guard.py::test_a_free_or_never_row_with_a_claim_marks_its_partly_read_sources | PASSED | FAILED
- test_policy_guard.py::test_a_free_reason_that_says_it_creates_nothing_or_changes_nothing_has_no_class_and_is_refused | FAILED | FAILED
- test_policy_guard.py::test_a_grant_or_never_reason_with_no_class_is_refused_and_a_wrong_class_is_caught | PASSED | FAILED
- test_policy_guard.py::test_a_never_path_deeper_than_the_prefix_grant_is_not_reported_as_covering_it | PASSED | FAILED
- test_policy_guard.py::test_a_note_class_with_an_unknown_source_id_is_a_problem_of_the_check_and_the_page_raises_policy_error | PASSED | FAILED
- test_policy_guard.py::test_every_claim_has_one_of_two_marks_taken_from_the_head_of_the_sources_file | FAILED | FAILED
- test_policy_guard.py::test_the_check_command_reports_a_claim_with_no_mark_in_the_sources_file | PASSED | FAILED
- test_policy_guard.py::test_the_page_head_and_the_r17_cell_and_reason_state_the_same_scope | FAILED | FAILED
- test_policy_guard.py::test_the_page_shows_the_builder_mark_on_the_plus_claim_of_r17_and_the_nobody_mark_on_every_other_claim | FAILED | FAILED
- test_policy_guard.py::test_the_path_overlap_with_a_prefix_setting_agrees_with_a_brute_force_search_over_its_values | PASSED | PASSED
Other failures on the fbc837b4 variant (old test ids, 9): test_pr1_grants_are_all_named_in_a_source..., test_the_builder_only_claims_are_not_shown_as_checked..., test_vault_text_in_page_mode_and_with_values, test_the_committed_page_equals_what_the_data_gives, test_plant_a_page_that_differs..., test_the_data_of_this_repository_breaks_no_rule_the_command_line_checks, test_plant_m10_check_reports_each_data_problem..., test_m10_write_makes_a_missing_docs_folder..., test_every_note_of_a_kind_is_classed_and_every_claim_has_a_source_or_an_unchecked_entry. (8 of the 12 new tests pass against the old src.)

## Probes (own scripts: probes-head.log, probes-p5b.log; script at /home/user/build/EV-q8c1-5015c990/probes/)
1. Claim marks: baseline problems []. Claim with no mark (nobody list replaced): 0-marks problems for R17's second claim and R18's claim. Two marks (R18 start also under builder): one "has 2 marks" problem. Mark swapped between R17 and R18: `claim_mark_problems` returns [] (each claim has exactly one mark); the generated page then shows R17 with the nobody mark and R18 with the builder mark (the repo test that pins "builder mark only on R17" is the thing that would notice).
2. Reason with no class: removing the class key of any grant, free or never reason gives at least one "has 0 classes in NOTE_CLASSES, needs one" problem, for all 45 reason entries of the three kinds (none printed "NO key"). (Never rows that share one reason text give 2 to 6 problems.)
3. K-NOPE: `note_problems` and `data_problems` both report it ("not in the sources file" and "not in `verified` of the same entry"); `pp.page()` raises PolicyError ("the page names source K-NOPE ..."), not KeyError.
4. `{mount}/data/{path_prefix}+/deeper/+` against R17 `{mount}/data/{path_prefix}+`: vault_paths_overlap False in both argument orders; `never_covers_grant_problems` with that never line returns []. Controls: `{path_prefix}*` and `{mount}/data/*` overlap True; `{path_prefix}+/*` overlaps False (it needs a slash after the name; my expectation label in the log, "expect True", was wrong for that one).
5. Hostile sources file (claim_readers | builder_marks | source_ids): duplicated CLAIM-READ-BY-BUILDER or -NOBODY line: claim_readers PolicyError, others ok. Fullwidth colon tag or leading-space tag: PolicyError. Blank/whitespace-only lines, CRLF, unicode (NBSP separator, RTL mark, zero-width space) in a claim line: all three ok. UTF-8 BOM: claim_readers ok, builder_marks and source_ids PolicyError (row 1 has not five columns). Invalid UTF-8 byte: PolicyError (cannot be read). Empty file: claim_readers and builder_marks PolicyError, source_ids ok. Empty start (`;; ` with trailing space, or an empty tag value): PolicyError; a trailing ` ;;` with no space is accepted as a start text (`...;;`). A zero-width character inside a start: claim_mark_problems reports 0 marks for R18's claim and a stale start. A start repeated under both marks: accepted by claim_readers.

Cleanup: own Postgres stopped, worktrees under /home/user/build/EV-q8c1-5015c990 kept for the lead (wt, wt-prev, wt-main; the two base trees hold copied test files, uncommitted).
