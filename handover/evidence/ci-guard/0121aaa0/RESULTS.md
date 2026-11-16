# CI guard round 4: evidence (EVIDENCE RUNNER: runs and records, does not judge)

Head under test: 0121aaa0aef494672375d3e249de72fc84acf4ae (origin/wip/cloud-ci-guard-wip), base origin/main a8b4d8e83f9fb29c09079417505682fd8b5464be.
Worktree /home/user/build/ER-ciguard-r4 (detached, `git rev-parse HEAD` equals the sha, `git status` clean before and after). Raw logs: /home/user/build/evidence-raw/ciguard-r4/ (outside the repo). Date 2026-11-12 UTC (about 22:00 to 22:40 UTC, 03:30 to 04:10 IST next day).

## Not run / deviations (first)
1. **The timing test FAILS when run alone**: `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` failed 3 of 3 runs alone at the head (logs 2c, 2d run1, 2d run2; "a quadratic function must be flagged") and also fails on origin/main (log 2e), so it is not caused by this diff (the diff touches only ci.yml, the golden and the new test file). It carries the `perf` mark, so the required full run (`-m "not live and not perf"`) deselects it and never ran it. Machine load average was about 4 (other agents' jobs share this machine), so the cause may be this machine; I did not investigate further and did not run the perf step.
2. Full suite: my first run (log 2-full-attempt1-pgenv-missing.log) had 1 failure, `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`, because I started my Postgres without PGHOST/PGPORT in the server's own environment (the test makes the server connect to itself). I restarted the server with PGHOST/PGPORT set, re-ran that file alone (253 passed, log 2b) and then re-ran the whole suite once more (10673 passed, log 2-full.log). So the suite ran twice; the numbers below are the second run.
3. Tool versions are not the CI pins: gitleaks 8.30.1 binary was a pre-existing local copy (/home/user/build/bin/gitleaks, version equals GITLEAKS_VERSION; its checksum was not compared with GITLEAKS_SHA256 because that pins the tarball, and github.com release download is blocked here with 403). zizmor 1.32.0 and bandit 1.9.4 were installed with `uv tool install` (latest, not the locked `scan` group); ruff 0.16.9 is from the project's locked environment. Semgrep, pip-audit, Trivy and the "System tools resolve" step were not run (not asked).
4. gitleaks was run over `origin/main..HEAD` and over `HEAD` (CI's own scope); not `--all`.
5. In item 5 the remote refs are the live remote (https://github.com/hadavin-dx/hadavin-sdk, 238 branches listed by ls-remote, 239 refs after fetch, not shallow), fetched into a fresh `git clone --no-hardlinks` of the main checkout. Head's `.gitleaksignore` is byte-identical to origin/main's, so "with origin/main's real .gitleaksignore" is the same file (checked out and `git status` stayed empty).
6. Slip: early on I ran `git fetch -q origin` inside the main checkout /home/user/hadavin-sdk (updates its remote-tracking refs only; no files, branches or config changed), against the instruction not to write to it. Adding the evidence worktree also wrote a normal admin record in its `.git/worktrees`. The base worktree and the live clone were removed afterwards.
7. Timing test in the required full run: not run (deselected by the perf mark), see 1.

## Results
| # | Item | Command (short) | Exit | Last line |
|---|------|-----------------|------|-----------|
| 1 | Guard tests | `heavy.sh uv run --no-sync pytest -q tests/test_ci_gitleaks_scope.py tests/test_ci_guard_wip_lanes.py` | 0 | 134 passed in 6.29s |
| 2a | Full suite, 1st run (PG env missing in server) | `pytest -q -m "not live and not perf" -rs` | 1 | 1 failed, 10672 passed, 1 skipped, 28 deselected in 283.48s |
| 2b | The one failing file alone, PG env fixed | `pytest -q tests/demo_askdata/test_validate_harm.py` | 0 | 253 passed in 24.99s |
| 2c | Full suite, final | same as 2a | 0 | 10673 passed, 1 skipped, 28 deselected in 312.88s (0:05:12) |
| 2d | Timing test alone at head (3 runs: 2c, 2d-1, 2d-2) | `pytest -k test_the_timing_harness_flags_a_quadratic_stand_in` | 1,1,1 | 1 failed, 132 deselected in 0.64s |
| 2e | Timing test alone on origin/main | same | 1 | 1 failed, 132 deselected in 0.73s |
| 3 | Fail-before: head's 2 test files + golden copied onto origin/main (old ci.yml) | `pytest -q <two files> -rf` | 1 | 32 failed, 102 passed in 5.55s |
| 4a | ruff check | `uv run --no-sync ruff check` | 0 | All checks passed! |
| 4b | ruff format | `ruff format --check` | 0 | 325 files already formatted |
| 4c | bandit | `bandit -ll -q -r src demos tools` | 0 | only 2 "nosec ... B102" warnings (src/hadavin_sdk/tools.py:389); no findings |
| 4d | zizmor | `zizmor --offline --format plain .github` | 0 | No findings to report. Good job! (3 suppressed) |
| 4e | gitleaks, new commits | `gitleaks git --redact --config .gitleaks.toml --log-opts=origin/main..HEAD .` | 0 | no leaks found (61.52 KB) |
| 4f | gitleaks, CI scope | same with `--log-opts=HEAD` | 0 | no leaks found (3.67 MB) |
| 5a | Guard step text from ci.yml, live remote refs, head | `env -i PATH=/usr/bin:/bin /bin/bash -e guard_step.sh` in clone at 0121aaa0 | 0 | no output |
| 5b | same, with origin/main's .gitleaksignore (identical file) | same | 0 | no output |
| 5c | same, checkout = origin/main (control) | same | 0 | no output |

Fail-before failed ids (32): test_ci_gitleaks_scope.py::test_real_ci_scan_is_limited_to_head_and_blocks, ::test_every_pinned_download_retries_and_keeps_its_checksum; and in test_ci_guard_wip_lanes.py: test_a_wip_cloud_lane_branch_with_a_handover_file_passes[3 params]; test_any_other_branch_with_a_handover_file_still_fails[9 params]; test_a_head_built_on_a_lane_commit_still_fails_even_if_a_lane_ref_has_it; test_a_lane_ref_pointing_at_another_branchs_commits_cannot_excuse_them_in_head; test_an_ignore_entry_for_a_sha_that_is_not_in_the_clone_is_stale_and_later_checks_run; test_the_path_checks_do_not_depend_on_what_the_pull_request_writes_into_gitleaks_toml[3 params]; test_a_tag_named_origin_main_does_not_weaken_the_main_history_check; test_a_tag_named_origin_core_cloud_handover_does_not_replace_the_deleted_branch; test_a_tag_named_origin_core_cloud_handover_does_not_replace_the_branch_in_the_range; test_a_merge_commit_that_adds_and_a_later_merge_that_removes_a_note_are_still_listed; test_a_merge_of_a_side_branch_with_a_handover_note_fails_even_if_the_merge_removes_it; test_an_entry_for_a_commit_in_the_pull_requests_own_history_is_refused_unless_main_has_the_line; test_an_entry_for_a_commit_in_the_own_history_is_accepted_when_main_has_the_identical_line; test_a_missing_origin_main_is_reported_even_if_a_tag_has_that_name; test_an_error_of_git_merge_base_fails_the_step_with_a_message; test_the_failure_message_names_the_refs_that_hold_the_notes; test_the_head_failure_message_names_the_refs_that_hold_the_notes; test_the_old_allowlist_wording_is_gone_and_the_new_rule_is_stated. (Full list: 3-failbefore.log.)

## Item 6: hostile probes (script probes.sh, log 6-probes.log)
Real step text from head's ci.yml, `env -i PATH=/usr/bin:/bin ... bash -e`, throwaway repos (main = config + empty ignore list with a future EXPIRES; origin/core/cloud-handover holds one note).
| Probe | Expected (my guess before running) | rc | First message |
|---|---|---|---|
| P0 clean checkout | 0 | 0 | none |
| P1a remote branch origin/feature/x (non-wip) holds a handover note | 1 | 1 | "handover notes exist in the history of HEAD or of a branch other than core/cloud-handover and the wip/cloud-* lane branches ... handover/reviews/x.md (on: origin/feature/x)" |
| P1b HEAD on non-wip branch feature-x holds the note | 1 | 1 | "handover notes are in this checkout's tree ..." plus the two history messages |
| P2a remote lane origin/wip/cloud-x holds the note | 0 | 0 | none |
| P2b HEAD on branch wip/cloud-x holds the note | 1 | 1 | "handover notes are in this checkout's tree ..." and "... in the history of HEAD itself (a lane branch does not excuse them ...)" |
| P3 ignore entry for a commit in the PR's own history, line not in main's file | 1 | 1 | "ignore entry hides a commit in this pull request's own history: c843301f..." |
| P3c control: entry commit only on core/cloud-handover, identical line already in origin/main, not in HEAD history | 0 | 0 | none |
| P4a ref refs/remotes/origin/pull/5/head holds a note | 1 | 1 | "... (on: origin/pull/5/head)" |
| P4b local ref refs/pull/5/head holds a note | 1 | 1 | "... (on: no remote branch)" |
| P5a path with a space, non-lane remote branch | 1 | 1 | "... handover/reviews/my note.md (on: origin/feature/sp)" |
| P5b path with a space, lane branch | 0 | 0 | none |
| P5c path with a space in HEAD | 1 | 1 | "handover notes are in this checkout's tree ..." |
| P6 same sha on lane origin/wip/cloud-x and as HEAD of the PR branch | 1 | 1 | "handover notes are in this checkout's tree ... (on: origin/wip/cloud-x)" and the HEAD-itself message |
| P6b same sha on lane origin/wip/cloud-x and on non-lane origin/feature/y, HEAD clean | 1 | **0** | none (the step passes) |

P6b differs from my guess: because the range subtracts everything reachable from any wip/cloud-* ref, a non-lane branch whose tip is a lane commit is not listed. The ci.yml comment calls that range "hygiene only, not the control"; the control is the check of HEAD's own history. Recorded without judgement; the reviewers decide whether it matters.

## Cleanup
Postgres cluster stopped (`pg_ctl stop`, "server stopped"); no helper processes of mine remain. Base worktree and live clone removed. Left in place: /home/user/build/ER-ciguard-r4 (the evidence worktree, clean at the head), its venv /home/user/build/ER-ciguard-r4-venv, the Postgres data dir /home/user/build/ER-ciguard-r4-pg, and the raw logs. Nothing was committed or added. Tokens: not measured.
