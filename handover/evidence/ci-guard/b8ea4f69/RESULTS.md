# Evidence for ci-guard head b8ea4f69 (EVIDENCE RUNNER; records only, no judgement)

## Not run / deviations (first)
- HEAD SUPERSEDED: the coordinator stopped this run because b8ea4f69 is superseded by 0121aaa0. Nothing here covers 0121aaa0.
- Standalone timing test (3x on head, 3x on origin/main): NOT run (stopped before it started; it was queued behind the full run). The same test ran once inside the full suite on the head and passed (no failure seen). Flake on main: not confirmed or refuted.
- Semgrep, Trivy, pip-audit, Vault tests: IMPOSSIBLE-NOW (per brief).
- `uv sync --no-build` failed (editable project has no binary distribution); synced without --no-build, rc=0. Python 3.13.18.
- stage_mutants.py ran before the full suite started (not overlapping); tree clean after.
- Item 6(l) and the step were run on the head worktree; refs fetched with `git fetch --all --prune`.
- A stray postgres of EV-ciguard2-a001174b (pid 2520) was found, not mine, not touched.
- Worktrees and my Postgres removed at the end. Raw logs: /home/user/build/evidence-raw/ciguard3/

## Table
| item | command | exit | last line |
|---|---|---|---|
| 1 full pytest | `-m "not live and not perf" -rs` via heavy.sh, own PG16 | 0 | 10664 passed, 1 skipped, 28 deselected in 269.14s (skip: tests/contracts/test_llm.py:95) |
| 2 ruff check | src tests demos tools | 0 | All checks passed! |
| 2 ruff format --check | same | 0 | 321 files already formatted |
| 2 bandit -ll | uv --with bandit | 0 | only nosec warnings |
| 2 zizmor --offline | .github | 0 | No findings to report (3 suppressed) |
| 2 scan_repo.py | | 0 | (empty) |
| 2 stage_mutants.py | | 0 | 37 of 37 good |
| 2 gitleaks origin/main..HEAD | | 0 | no leaks found |
| 3 fail-before, origin/main (a8b4d8e8) ci.yml | the head's 2 test files (125 tests) | 1 | 14 failed, 111 passed |
| 3 fail-before, a001174b ci.yml | same | 1 | 12 failed, 113 passed |
| 3 on head | same | 0 | 125 passed |
| 6 step scenarios | own scripts, step text parsed from head ci.yml, bash -e | see below | raw: 6/SUMMARY |
| 6(l) live refs | file count under handover/(reviews|tickets|evidence) | | new range 0 files; old range (HEAD --all --not origin/core/cloud-handover) 611 files; HEAD alone 0; 142 lane refs; step on live repo rc=0 |

Item 3 failing on main: lane pass cases (3), head-on-lane-commit, other-branch lane ref, unknown sha, 3 toml variants, 2 tag cases... (14 total); on a001174b: 5 lane-only entry cases, unknown sha, 3 toml, 3 tag cases (12). Full lists in 3-wtmain.log / 3-wtold.log.

Item 6 results (rc, expected): a 1 fail; b 0 pass; c nested wip/cloud-a/b rc=1 (not excused); d wip/cloudx, wip/other, feature/wip/cloud-x all rc=1; e rc=1; f_outside rc=1 (stale entry message only), f_note rc=1 (stale plus handover messages); g1 tag origin/main rc=1 ("in main history" message); g2 tag origin/core/cloud-handover without branch rc=1; g3 branch present, tag elsewhere rc=0; h(i) no allowlist rc=1, h(ii) paths-only rc=1; i1 merge in rc=1, i2 merge removes rc=1, i3 later merge removes rc=1; j stale message then handover checks still ran, rc=1; k1 rename out rc=1, k2 rc=1, k3 lane-only rename rc=0, k4 rename into handover rc=1. No result differed from the brief's expectation.
