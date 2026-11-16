# Q8c-1 evidence at head be531371 (EVIDENCE RUNNER: recorded, nothing judged or fixed)

Branch `core/q8c-1-policy-vault-kubernetes`, head `be5313711305f417021a374465acc967b01f68e7` (clean tree checked), `origin/main` = `2a8c2aac`. Run 2026-11-11 19:40 to 20:50 UTC (01:10 to 02:20 IST on 11-12). Raw logs: `/home/user/build/evidence-raw/q8c1-be531371/`.

## Failed or not run (first)
1. **The 12 Vault engine tests were NOT run** (no Vault or OpenBao binary or server here; none downloaded). 12 skipped in `tests/test_policy_engine.py` (`engine-skips.txt`); with `HADAVIN_REQUIRE_VAULT_ENGINE=1` the same file gives `6 passed, 12 errors`. Nothing here shows a real Vault server refuses or allows anything. The same 12 are the only skips of the full suite besides one Bedrock test (13 skipped in total).
2. **My first two full-suite runs were bad runs, my own setup slips.** Run 1 (20 failed, 437 errors): my Postgres did not start (port already in use by another process; my first `select 1` reached that other server, read-only). Run 2 (1 failed, 10828 passed): Postgres up, but `PGHOST` and `PGPORT` were not in the server's own environment, so a `dblink_connect` test in `tests/demo_askdata/test_validate_harm.py` could not connect. Run 3 with the server environment set: exit 0. Logs of runs 1 and 2 are kept (`05-full-run1-no-postgres.log`, `05-full-run2-server-env-missing.log`).
3. `uv sync --locked --no-build` failed (`hadavin-sdk` editable has no binary); I ran `uv sync --locked --all-extras --group test` (builds only the project itself).
4. The timing test `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` was run alone 3 times per side: head failed 3 of 3, origin/main failed 2 of 3 and passed 1 (`flaky-timing-test.txt`). The full suite (run 3) passed it. Machine load was 4 to 8.
5. Not run: CodeQL, SonarCloud, CodeRabbit, CI service jobs, any Kubernetes cluster. Semgrep, zizmor, Trivy, pip-audit steps of ci.yml not run (not named by the package).

## Results
| Item | Command (after the `env -u ...` prefix) | Exit | Last line |
|---|---|---|---|
| 1 changed files | `git diff --name-only origin/main...HEAD` | 0 | 13 files (`diff-names.txt`) |
| 2 ruff | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 format | `ruff format --check src tests demos tools` | 0 | 323 files already formatted |
| 3 bandit | `bandit -q -r src demos tools -ll` | 0 | only warnings (nosec at tools.py:389) |
| 4 scan | `python tools/scan_repo.py` | 0 | no output |
| 4 stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4 gitleaks origin/main..HEAD | `gitleaks git --log-opts=origin/main..HEAD` | 0 | no leaks found |
| page | `python tools/policy_page.py --check` | 0 | no output |
| 5 full suite (run 3, own Postgres) | `heavy.sh ... pytest -p no:cacheprovider -q -m "not live and not perf" -rf` | 0 | 10829 passed, 13 skipped, 28 deselected in 255.81s |
| 6 policy mutants | `python tests/policy_mutants.py` (CI step "Declared-permission mutants") | 0 | 57 of 57 good; problems: [] (run took 483 s). It also prints: first-line check is weak (killer asserts through same()) for 36 of 57 mutants. |
| 6 ci.yml diff | adds `HADAVIN_REQUIRE_VAULT_ENGINE: "1"` in 3 places and the policy mutant step | - | CI step is the same command as run here |

## Item 7: new tests on old code (`failbefore-*-passed.txt`)
- On `6bdfadc1` src (head's tests, tools and fixture copied in; `PYTHONPATH` set to that tree's `src`, import path checked): 10 failed, 295 passed, 12 skipped. Failed: the 8 guard tests `every_unchecked_claim_has_a_dated_entry...`, `plant_an_unchecked_claim_with_no_pending_entry_is_caught`, `pr1_grants_are_all_named_in_a_source...`, `builder_only_claims_are_not_shown_as_checked...`, `plant_no_copy_ready_text_for_a_kind_with_an_unverified_grant_or_claim`, `the_committed_page_equals_what_the_data_gives`, `the_page_states_its_limits_and_offers_text...`, `every_note_of_a_kind_is_classed...`; the 2 docs tests `the_page_title_notes_and_engine_image_are_true`, `the_changelog_says_seven_rows_are_abbreviated...`.
- Of the 14 test functions added in batch 3, these PASS on the old src: `a_builder_only_source_is_marked_wherever_the_page_lists_it`, `a_never_path_over_a_grant_is_also_refused_by_the_check_command`, `no_never_list_line_of_the_three_kinds_covers_a_grant`, `plant_a_kubernetes_never_resource_that_a_grant_names_is_caught`, `plant_a_new_note_with_no_class_a_claim_that_is_not_listed_and_an_unknown_source_are_caught`, `plant_a_vault_never_path_over_a_grant_is_caught_and_a_capability_that_differs_is_not`, `plant_the_check_across_kinds_calls_the_cover_rule`, `the_page_and_the_fixture_agree_on_which_rows_are_abbreviated_and_what_is_unpinned` (8). These FAIL on old src: `every_note_of_a_kind_is_classed_and_every_claim...`, `every_unchecked_claim_has_a_dated_entry...`, `plant_an_unchecked_claim_with_no_pending_entry_is_caught`, `pr1_grants_are_all_named_in_a_source...`, `the_builder_only_claims_are_not_shown_as_checked...`, `the_changelog_says_seven_rows...` (6). (The new tests that pass on old src do so because the checks live in `tools/policy_page.py`, which was copied from head.)
- On `origin/main` src (all new test files, tools, fixture copied in): 198 failed, 107 passed, 12 skipped (guard 192 failed and 103 passed; docs 4 failed; engine 2 failed and 4 passed).

## Item 8: my own probes, not the builder's tests (`own-probes.txt`)
Run with `tools.policy_page` loaded from the head. Baseline: `cross_problems` and `data_problems` empty; page equals the committed file. `_checked_cell` marks V-ACL, V-PARSE and B-ACL "(builder only)" in all 4 id combinations I tried and leaves other ids unmarked. Never-vs-grant on the Vault secrets policy: a never path equal to the grant path with the same capability: 1 problem; with no capabilities: 1; with a different capability (`delete`): 0; `mount/data/+`: 1; `secret/*` and `sys/policies/acl/*`: 0 (my literals do not use the grant's `{mount}` token, so these two do not overlap in the check's own form). Kubernetes never resource equal to a grant's resource (`deployments`): 1; never `secrets`: 0. `copy_ready` is False for all three kinds (claims_unverified counts 1, 1, 3). Each builder-only id appears once on the page, each next to builder-only text.
