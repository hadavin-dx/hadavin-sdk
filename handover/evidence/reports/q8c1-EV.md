EVIDENCE RUNNER report, Q8c-1 head be5313711305f417021a374465acc967b01f68e7 (tree clean). I recorded results only; nothing was fixed or judged. Summary file: /home/user/hadavin-sdk/handover/evidence/Q8c-1/be531371/RESULTS.md (gitleaks on that folder: no leaks). Raw logs: /home/user/build/evidence-raw/q8c1-be531371/. Not pushed or committed. I did not read builder reports.

FAILED OR NOT RUN (first)
1. The 12 Vault engine tests were NOT RUN. There is no vault/bao binary here and I downloaded none. All 12 in tests/test_policy_engine.py skipped. With HADAVIN_REQUIRE_VAULT_ENGINE=1 the file gives 6 passed, 12 errors. The full suite has 13 skips: those 12 plus the Bedrock Stubber test. Nothing here shows a real Vault refuses or allows anything, and the five R17 sources and three hashes were not re-read by me.
2. My first two full-suite runs were bad, both my own setup slips, and the logs are kept.
   - Run 1: 20 failed, 437 errors. My Postgres did not start because the port was already in use by another agent's server. My first "select 1" reached that server (read-only).
   - Run 2: 1 failed, 10828 passed. PGHOST and PGPORT were not in the server's environment, so the dblink test in tests/demo_askdata/test_validate_harm.py could not connect.
   - Run 3 had the server environment set and gave exit 0 (see table).
3. `uv sync --locked --no-build` failed (the hadavin-sdk editable has no binary distribution). I used `uv sync --locked --all-extras --group test` instead.
4. The flaky timing test test_the_timing_harness_flags_a_quadratic_stand_in, run alone 3 times per side through the three slot locks. Head: failed 3 of 3. origin/main: failed 2, passed 1. It passed in full-suite run 3.
5. Not run: CodeQL, SonarCloud, CodeRabbit, CI service jobs, any Kubernetes cluster, and the Semgrep, zizmor, Trivy and pip-audit steps of ci.yml (the package does not name them).

RESULTS (env -u cloud and token variables on every command)
| Item | Exit | Last line |
|---|---|---|
| ruff check and ruff format --check over src tests demos tools | 0 and 0 | All checks passed; 323 files formatted |
| bandit -ll over src demos tools | 0 | warnings only (nosec at tools.py:389) |
| tools/scan_repo.py | 0 | no output |
| tools/policy_page.py --check | 0 | no output |
| tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| tests/policy_mutants.py (CI step) | 0 | 57 of 57 good; problems: []. It also prints "first-line check is weak (killer asserts through same()) for 36 of 57 mutants". |
| gitleaks origin/main..HEAD | 0 | no leaks found |
| Full pytest, run 3, own Postgres 16, through heavy.sh | 0 | 10829 passed, 13 skipped, 28 deselected in 255.81s |
| Changed files vs origin/main | - | 13 files (ci.yml, CHANGELOG, README, docs/declared-permissions.md, 3 src modules: secrets_vault, signer_vault, kubernetes; fixture; policy_mutants; 3 test files; tools/policy_page.py) |

FAIL-BEFORE (item 7). The src path was forced with PYTHONPATH, and the import path was checked.
- On 6bdfadc1 src, with head's tests, tools and fixture copied in: 10 failed, 295 passed, 12 skipped. The 10 failures are 8 guard tests and 2 docs tests. They include the page-equals-data test and the changelog "seven abbreviated rows" test.
- Of the 14 test functions added in batch 3, 6 FAIL on the old src: note_classed_and_claims_have_source_or_entry, unchecked_claim_has_dated_entry_and_goes_red_when_overdue, plant_an_unchecked_claim_with_no_pending_entry, pr1_grants_named_in_a_source, builder_only_claims_not_shown_as_checked, changelog_says_seven_rows_abbreviated.
- The other 8 PASS on the old src: builder_only_source_marked_wherever_listed, never_path_over_a_grant_refused_by_check_command, no_never_list_line_covers_a_grant, plant_a_kubernetes_never_resource, plant_a_new_note_with_no_class, plant_a_vault_never_path_over_a_grant, plant_the_check_across_kinds, page_and_fixture_agree_on_abbreviated_rows. The tools/policy_page.py copied from head holds those checks. The pass lists are in failbefore-6bdfadc1-passed.txt.
- On origin/main src, with all new test files, tools and fixture copied in: 198 failed, 107 passed, 12 skipped.

PER BATCH-3 ITEM, MY OWN PROBES (own-probes.txt, my script, not the builder's tests)
- Builder-only marks: _checked_cell marks V-ACL, V-PARSE and B-ACL "(builder only)" in all 4 id combinations tried. Each id appears once on the page, next to builder-only text. The committed page equals the generated page.
- Never vs grant on Vault secrets:
  - never path equal to the grant path, same capability: 1 problem
  - no capabilities: 1
  - different capability (delete): 0
  - mount/data/+: 1
  - secret/* and sys/policies/acl/*: 0 (my literals did not use the grant's {mount} token, so they do not overlap in the check's own form)
- Kubernetes never resource equal to a grant's resource: 1 problem. never secrets: 0.
- Dated claim entries and unchecked claims: copy_ready is False for all three kinds (unchecked claim counts 1, 1, 3). The dated-entry and overdue behaviour is covered only by the batch-3 tests, which pass in the full run.
- Baseline cross_problems and data_problems are empty.

Cleanup: my worktrees, Postgres (stopped, folder deleted) and watcher shells are all stopped. Process check: 0 left. Tokens: moderate, no sub-agents. Real clock about 70 min, of which about 55 min was waiting in the heavy.sh queue. R-numbers: per the preamble (R17 and R18 are the ticket's claim ids, not bible numbers).