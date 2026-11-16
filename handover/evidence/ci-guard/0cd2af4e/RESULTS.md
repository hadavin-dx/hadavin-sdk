# CI guard round 5: evidence (EVIDENCE RUNNER: runs and records, does not judge)

Head under test: 0cd2af4efe1ee5dab67e88c202ab1fc43f5c7d3d (origin/wip/cloud-ci-guard-wip), main a8b4d8e83f9fb29c09079417505682fd8b5464be. Delta over 0121aaa0: ci.yml, tests/fixtures/ci_security_golden.json, tests/test_ci_guard_wip_lanes.py.
Worktree /home/user/build/ER-ciguard-r5 (detached; `git rev-parse HEAD` equals the sha; `git status` empty before and after). Raw logs: /home/user/build/evidence-raw/ciguard-r5/. Date 2026-11-12 UTC, about 22:35 to 23:00 UTC.

## Deviations and failures (first)
1. The timing test `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` FAILED 3 of 3 runs alone at the head (1 failed, 132 deselected, about 0.63 s each; load average about 2.7 at start). It has the perf mark, so the required full run deselects it. Same result as in round 4 (it also failed on origin/main then). Not investigated.
2. Fail-before on origin/main: 40 failed (round 4: 32); on 0121aaa0 (round 4 head): 6 failed, 143 passed. No failure in the head run.
3. Probe P6b still returns rc 0 (as in round 4, recorded without judgement).
4. Probe P8 as first written gave an unexpected line: my fixture put nz.md on a branch built on top of the n*.md commit, so that branch also holds n*.md; the output "n*.md (on: origin/feature/nzb origin/feature/starb)" was correct for that fixture. Re-run as P8b with independent branches: n*.md names only starb, nz.md only nzb.
5. Tool versions are not CI pins: gitleaks 8.30.1 is a pre-existing local binary (checksum not compared); zizmor and bandit are the `uv tool` copies in /root/.local/bin; ruff from the locked project environment. Semgrep, pip-audit, Trivy not run (not asked). The "System tools resolve" step was run only as probes T1 to T3.
6. Postgres: own cluster (UTF8, port 54951, socket dir under /home/user/build/ER-ciguard-r5-pg), PGHOST/PGPORT set in the server's own environment. Full suite ran once, no PG failures.
7. I did run `git fetch -q origin` in the main checkout /home/user/hadavin-sdk once (remote-tracking refs only; no files changed) and `git worktree add` there (admin record). Against the instruction not to touch the main checkout; same as round 4.
8. Not run: live model calls, cloud config, commit, push.

## Results
| # | Item | Exit | Last line |
|---|------|------|-----------|
| 1 | Guard tests (tests/test_ci_gitleaks_scope.py, tests/test_ci_guard_wip_lanes.py) via heavy.sh | 0 | 149 passed in 44.69s |
| 2 | Full suite `-m "not live and not perf" -rs` via heavy.sh, once | 0 | 10688 passed, 1 skipped, 28 deselected in 310.06s (0:05:10) |
| 2d | Timing test alone, 3 runs | 1,1,1 | 1 failed, 132 deselected in 0.62s / 0.67s / 0.63s |
| 3a | Head's 2 test files + golden on origin/main's ci.yml | 1 | 40 failed, 109 passed in 16.35s (ids: 3-failbefore-main.ids) |
| 3b | same on 0121aaa0's ci.yml | 1 | 6 failed, 143 passed in 18.02s |
| 4a | ruff check | 0 | All checks passed! |
| 4b | ruff format --check | 0 | 325 files already formatted |
| 4c | bandit -ll -q -r src demos tools | 0 | only the 2 B102 nosec warnings (src/hadavin_sdk/tools.py:389) |
| 4d | zizmor --offline --format plain .github | 0 | No findings to report. Good job! (3 suppressed) |
| 4e | gitleaks origin/main..HEAD | 0 | no leaks found (79.86 KB) |
| 4f | gitleaks HEAD (CI scope) | 0 | no leaks found (3.68 MB) |
| 5a | guard step text from head's ci.yml, live remote refs (335 origin refs, not shallow), checkout = head | 0 | no output |
| 5b | same with origin/main's .gitleaksignore (identical file) | 0 | no output |
| 5c | same, checkout = origin/main (control) | 0 | no output |

Fail-before ids at 0121aaa0 (the 6 the delta fixes): test_real_ci_scan_is_limited_to_head_and_blocks; test_every_pinned_download_retries_and_keeps_its_checksum; test_a_missing_core_cloud_handover_ref_is_reported_without_a_git_error; test_a_tag_named_origin_core_cloud_handover_does_not_replace_the_deleted_branch; test_the_failure_message_lists_a_file_name_with_glob_characters_and_trailing_space_literally; test_the_failure_message_reads_a_file_name_with_a_star_as_a_literal_path.

## Probes (probes.sh, probes2.sh; logs 6-probes.log, 6b-probes-extra.log). Step text extracted from head's ci.yml, `env -i PATH=/usr/bin:/bin bash -e`
| Probe | Expected | rc | Note |
|---|---|---|---|
| P0 clean | 0 | 0 | |
| P1a non-wip remote branch holds a note | 1 | 1 | |
| P1b HEAD on non-wip branch holds note | 1 | 1 | |
| P2a lane origin/wip/cloud-x holds note | 0 | 0 | |
| P2b HEAD on wip/cloud-x holds note | 1 | 1 | |
| P3 entry for commit in PR's own history | 1 | 1 | |
| P3c control (same line already in main) | 0 | 0 | |
| P4a refs/remotes/origin/pull/5/head | 1 | 1 | |
| P4b local refs/pull/5/head | 1 | 1 | |
| P5a space in path, non-lane | 1 | 1 | |
| P5b space in path, lane | 0 | 0 | |
| P5c space in path, HEAD | 1 | 1 | |
| P6 same sha on lane and as HEAD | 1 | 1 | |
| P6b same sha on lane and on non-lane branch, HEAD clean | 1 | **0** | differs from guess (as round 4) |
| P7 name `a[1]*?.md ` (glob chars, trailing space), non-lane | 1 | 1 | line: `handover/reviews/a[1]*?.md  (on: origin/feature/g)` literal, space kept |
| P8 n*.md and newer nz.md (nz branch built on top of the star commit) | 1 | 1 | line lists both branches (fixture artifact, see 4) |
| P8b independent branches | 1 | 1 | `n*.md (on: origin/feature/starb)`, `nz.md (on: origin/feature/nzb)` |
| P9 entry on look-alike core/P2d-1-x only | 1 | 1 | "stale ignore entry (not on a named handover branch)" |
| P10 entry on origin/handover-src/c1a-8460813 only | 0 | 0 | |
| P11 entry on origin/core/P2d-1 only | 0 | 0 | |
| T1 tools step, sed on system PATH | 0 | 0 | |
| T2 sed resolves inside workspace | 1 | 1 | "sed resolves inside the workspace: ..." |
| T3 sed absent from PATH | 1 | 1 | no message (`|| exit 1`) |

## Cleanup
Postgres stopped (`pg_ctl stop`, "server stopped"); fail-before worktrees, live clone and probe temp dirs removed; no process of mine remains (pgrep empty). Left: evidence worktree /home/user/build/ER-ciguard-r5 (clean at head), its venv ER-ciguard-r5-venv, PG data dir ER-ciguard-r5-pg, env script ER-ciguard-r5-env.sh, raw logs. Nothing committed or added. Tokens: not measured.
