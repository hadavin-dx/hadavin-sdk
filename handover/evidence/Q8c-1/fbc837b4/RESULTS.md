# Q8c-1 evidence, head fbc837b4 (previous head be531371, base origin/main 2a8c2aac)
EVIDENCE RUNNER: results recorded, nothing judged, nothing fixed. Raw logs: `/home/user/build/evidence-raw/Q8c1-fbc837b4/` (outside the repo; names below).
Detached worktree at fbc837b4, `git status` clean at start and end. Own venv; own Postgres 16.15 (port 56911, PGHOST/PGPORT set in the server's environment; stopped and folder deleted at the end).

## Failed, not run, or different from the brief (first)
- Vault engine tests (item 6): NOT RUN against a server. No `vault` or `bao` binary on this machine; brief forbids downloading or running an external binary (docker exists; not used). 12 skipped without the switch; 12 errors with `HADAVIN_REQUIRE_VAULT_ENGINE=1`.
- `uv sync --locked --no-build` fails here ("hadavin-sdk editable ... has no binary distribution"); I used `uv sync --locked --all-extras --group test` (same deviation as earlier runs). Logs: sync.log, sync2.log.
- Item 5 on old src: 124 of 333 tests in the three policy test files FAIL (and 207 on origin/main src). Mostly tests of data that only exists in the head src. Counts below.
- Surprises in item 7 (probes P1a, P1b, P1c): the check reports 0 problems when the Kubernetes `rules_review` free reason is changed to "...creates nothing in the cluster" and the page then shows that sentence beside "Checked: ... K-SSRR". See item 7.
- Not run (not in the brief): CI steps other than ones listed, perf tests, flaky timing test, Python 3.12 job, semgrep, zizmor. gitleaks ran on the commit range, plus on this folder (see end).

## Table
| # | item | command | exit | last line |
|---|---|---|---|---|
| 1 | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 1 | ruff format | `ruff format --check src tests demos tools` | 0 | 323 files already formatted |
| 1 | bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only 2 nosec WARNING lines (src/hadavin_sdk/tools.py:389), no issues |
| 1 | page check | `python tools/policy_page.py --check` | 0 | no output |
| 1 | scan_repo | `python tools/scan_repo.py` | 0 | no output |
| 1 | gitleaks | `gitleaks git --redact --log-opts="origin/main..HEAD"` | 0 | no leaks found |
| 2 | full pytest | via heavy.sh, `-p no:cacheprovider -q -m "not live and not perf" -rs`, own PG | 0 | 10845 passed, 13 skipped, 28 deselected in 333.34s |
| 3 | policy mutants | `python tests/policy_mutants.py` via heavy.sh | 0 | 70 of 70 good; problems: [] (log also says: first-line check weak for 36 of 70; some killers shared) |
| 4 | stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 6 | engine tests, no switch | `pytest -rs tests/test_policy_engine.py` | 0 | 8 passed, 12 skipped |
| 6 | engine tests, `HADAVIN_REQUIRE_VAULT_ENGINE=1` | same | 1 | 8 passed, 12 errors |
| 8 | diff vs be531371 | `git diff --stat be531371 HEAD` | - | 9 files changed, 912 insertions(+), 170 deletions(-) |

Skips in the full run: 12 are tests/test_policy_engine.py ("needs a real Vault server (HADAVIN_TEST_VAULT_ADDR is not set) ... CI runs these against its Vault service and requires them"); 1 is tests/contracts/test_llm.py:95 ("Stubber refuses a malformed Converse shape before the kind sees it"). Log: full.log.
Item 6 error text with the switch: "Failed: HADAVIN_REQUIRE_VAULT_ENGINE=1 but HADAVIN_TEST_VAULT_ADDR is not set: the Vault engine tests must run here". Logs: engine-without.log, engine-with.log.

## 5 Fail-before
Head's tests/test_policy_*.py, tests/policy_mutants.py, tests/fixtures/policy_sources_2026-11-11.txt and tools/ copied into a detached worktree of the old tree; src from that tree; env without the Vault switch. Run: `pytest -rA tests/test_policy_guard.py tests/test_policy_docs.py tests/test_policy_engine.py`. Logs: fb-old.log, fb-main.log, fb-old-with-page.log (the same with head's docs/declared-permissions.md also copied; identical counts).
| src from | passed | failed | skipped |
|---|---|---|---|
| be531371 | 197 | 124 | 12 |
| origin/main | 114 | 207 | 12 |
Per file on be531371 src: guard 188 pass / 121 fail; docs 2 / 2; engine 7 / 1. On origin/main src: guard 108 / 201; docs 0 / 4; engine 6 / 2.
The 16 test functions that are new in head vs be531371 (none of the existing test functions changed text; found by comparing function source; helpers and parametrised ids not separately compared):
| new test | be531371 src | origin/main src |
|---|---|---|
| a_free_or_never_reason_that_says_it_is_unchecked_must_list_the_claim | FAILED | FAILED |
| the_self_review_create_is_an_unchecked_claim_on_the_page_not_a_checked_fact | FAILED | FAILED |
| the_pending_claims_of_a_free_and_a_never_entry_are_watched_like_a_grant_claim | FAILED | FAILED |
| a_never_path_of_two_or_more_parts_over_the_one_prefix_grant_is_caught | FAILED | FAILED |
| the_path_overlap_automaton_agrees_with_a_brute_force_search_on_every_small_pattern_pair | PASSED | PASSED |
| the_path_prefix_setting_is_read_as_one_or_more_parts_each_ending_in_a_slash | PASSED | PASSED |
| a_never_type_that_does_not_fit_the_platform_is_refused | FAILED | FAILED |
| every_note_with_a_sources_class_shows_its_source_ids_after_the_note_and_in_the_source_list | FAILED | FAILED |
| a_sources_note_whose_free_entry_does_not_list_the_id_is_caught | FAILED | FAILED |
| the_builder_only_marks_are_read_from_the_head_of_the_sources_file_and_match_its_list | PASSED | PASSED |
| the_builder_marks_refuse_a_missing_line_an_unknown_id_and_a_second_line | PASSED | PASSED |
| a_source_of_which_only_a_passage_was_read_is_marked_on_a_row_with_a_claim_only | FAILED | FAILED |
| the_grants_broader_than_their_reason_say_so_in_the_cell_a_reader_checks | FAILED | FAILED |
| the_limit_of_a_dated_entry_is_one_number_in_the_tool | PASSED | PASSED |
| the_hash_path_control_also_accepts_400_but_never_403_or_404_and_no_other_request_accepts_400 | PASSED | PASSED |
| the_longer_sign_path_is_sent_for_the_signing_key_and_listed_on_the_page | PASSED | PASSED |
7 of 16 new tests pass on old src (the tools are copied from head, so tool-side guards are present). The full per-test list is in fb-old.log and fb-main.log (-rA).

## 7 Hostile probes (my own script, `probe.py`-style, run on scratch copies of the two kind modules plus the sources file; calls `data_problems(root)` and `page(root)` of the head tool). Output: probes.log (copied here).
| probe | result |
|---|---|
| P0 baseline | 0 problems; page(scratch) equals docs/declared-permissions.md: True; real page equals the tool's output: True (bytes 29023) |
| P1a Kubernetes free reason for `k8s.rules_review` set to "asks the cluster ... and creates nothing in the cluster", `claims_unverified` and K-SSRR in `verified` kept | 0 problems. Page line: "... creates nothing in the cluster. Note: ... (sources: K-RBAC, K-SRC, K-SSRR). Checked: 2026-11-11, sources K-RBAC, K-SRC, K-SSRR. Claims not checked: a `create` on `selfsubjectrulesreviews` changes nothing in the cluster (the one source ... K-SSRR, does not say so)." So the page shows "creates nothing" beside "Checked" and also beside the "Claims not checked" sentence (because the claim entry was left in). |
| P1b same reason, `claims_unverified` emptied | 0 problems. Page line shows "creates nothing in the cluster" and "Checked: 2026-11-11, sources K-RBAC, K-SRC, K-SSRR." with no "Claims not checked" sentence. |
| P1c reason reworded "it is read-only and changes nothing", claim kept | 0 problems |
| P2a Vault never entry typed `resource`, name `{mount}/data/secret-x` | 1 problem: "never type 'resource' does not fit platform 'vault' (allowed: role, path)" |
| P2b typed `prose`, name holds a path | 1 problem, same text |
| P2c typed `action`, name a path | 1 problem, same text |
| P2d typed `path`, name is prose ("any secret under the data mount") | 0 problems |
| P3a never path `{mount}/data/+/+` over R17 | 1 problem: covers R17 |
| P3b never path `{mount}/data/{path_prefix}+/+` | 1 problem: covers R17 |
| P3c never path `{mount}/data/+` (one part, no prefix) | 0 problems |
| P3d never path `{mount}/data/{path_prefix}+` (same as R17) | 1 problem: covers R17 |
| P3e never path `{mount}/data/{path_prefix}+/deeper/+` | 1 problem: covers R17 (surprise to me: a path with a literal `deeper` part is reported as covering R17) |
| P4a (tool constant NOTE_CLASSES patched) sources class lists unknown id K-NOPE | `data_problems` 0 problems; `page()` raises KeyError 'K-NOPE' |
| P4b free entry `verified` drops K-SSRR while the note class still lists it | 0 problems |
| P4c note class lists V-TOK (a real id of another kind) | 0 problems |
| P5 page equals data | True |
Not tried: a note whose class is edited inside the kind module (the class table lives in tests/test_policy_guard.py, which I did not edit); P4 probes used the tool-side constant of the same name.

## 8 Diff
vs be531371: 9 files, 912 insertions, 170 deletions: CHANGELOG.md, docs/declared-permissions.md, src/hadavin_sdk/actions/secrets_vault.py, src/hadavin_sdk/sources/kubernetes.py, tests/fixtures/policy_sources_2026-11-11.txt, tests/policy_mutants.py, tests/test_policy_engine.py, tests/test_policy_guard.py, tools/policy_page.py. (diffstat.txt)
vs origin/main (merge-base 2a8c2aac): 13 files, 7078 insertions: the nine above plus .github/workflows/ci.yml, README.md, src/hadavin_sdk/audit/signer_vault.py, tests/test_policy_docs.py.
