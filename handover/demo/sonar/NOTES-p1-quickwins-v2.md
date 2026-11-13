# P1 quick wins v2: NOTES (base db54e13, patch sonar-p1-quickwins-v2.patch, replaces sonar-p1-quickwins.patch)

Preamble points applied: 5, 6, 7, 20. EGM (13) NOT run by me: the lead runs it. Bible R-numbers not available in this shell, none cited.
Review of v1: /tmp/work/rv7-report.md (1 Major, 3 Minor, 3 Nit). All are handled below.

## What did not work or is uncertain (first)
- I cannot see the SonarCloud result. "Expected to clear" is a prediction. The rule texts for githubactions:S6506, S8541 and shell:S7688 are not served by the rules API here, so the accepted spelling is unverified (as in v1).
- The 3 changed v1 lines in lint.yml were checked by actionlint in v1 only. v2 changed 2 more lines of lint.yml (`[[`); actionlint was NOT rerun on v2. The runner default shell for `run:` on ubuntu is bash, so `[[` is valid; no `shell:` key was needed (the hygiene test now fails if any step or job sets a `shell:` other than bash).
- Not run: full suite, 8 playwright tests, 3 gitleaks tests, Windows, real CI. Windows: the new bash tests are skipped on Windows (skipif), mypy --platform win32 is clean; not executed there.
- The new start_all.sh tests use a stub `python`, so they prove what the shell `[[ ]]` lines decide (environment given to the desk process, pid-file refusal); they do not start a real server.
- Mutation of the old `[` form: the stub-based start_all tests PASS on the old single-bracket scripts too (the rewrite does not change behaviour; that is the point). They guard the new lines against a later wrong edit, not against the old code. See the table below for which tests fail on old code.

## Which new tests fail on the OLD code (evidence-p1v2-5, tests of v2 on db54e13 scripts and workflows, 6 failed / 219 passed / 3 skipped)
| test | fails on old code? | why |
|---|---|---|
| test_hygiene: double brackets in .sh files AND workflow run blocks | yes | single brackets in 2 scripts and in lint.yml |
| test_workflow_files_parse: curl flags, pip flags (2 tests) | yes (2) | flags missing in lint.yml |
| test_lead_step_route: demo launchers string (updated) | yes | script text had `[ ` |
| test_reset_scripts: scripts refuse to run under dash (reset.sh, start_all.sh) | yes (2) | old scripts had no guard |
| test_hygiene: no raw direction control | only if a raw char is present: with the OLD tests/test_followup_edge_cases.py it fails (lines 439, 445); in the 6 failures above the test file was already patched, so it passes | |
| test_hygiene: pattern probe (20 snippets) | no (tests the helper itself) | |
| test_reset_scripts: start_all.sh leadflow cases (8), pid-file (2), unknown mode | no, they pass on old code | behaviour is unchanged; they fail on MUTANTS of the new lines, below |
| test_smtp_provider: recipient stable across a second outbox object | no on old src (src is unchanged); fails on a per-instance-salt mutant (v1 evidence-p1-4) | does NOT catch a per-process salt such as hash(key); the comment now says so |

## Mutants of scripts/start_all.sh (evidence-p1v2-2), new tests kept
| mutant | result |
|---|---|
| line 12 `!= off` -> `!= of` | 2 failed (the `off` case and the `of` case) |
| line 12 `-n` -> `-z` | 5 failed |
| line 12 `&&` between the two tests -> `||` | 2 failed |
| line 16 first pid file name broken | 1 failed (fakes.pid case) |
| line 16 second pid file name broken | 1 failed (desk.pid case) |
Also: lint.yml line 77 back to `[ ]` -> hygiene test fails (`lint.yml run-block line 5`).
The old v1 test "unknown mode" was vacuous (a `case`, not a `[[`, and `assert not list(tmp_path.iterdir())` was always true). It is replaced by one that says so in its docstring and asserts the stub python was never called.

## Changes (v2 on top of v1, all in one patch against db54e13)
| file | change |
|---|---|
| .github/workflows/lint.yml | v1 changes (curl `--proto '=https' --proto-redir '=https' --tlsv1.2`, pip `--only-binary :all:`) plus the 2 remaining `[ ]` tests (status, literals-left) now `[[ ]]` |
| scripts/reset.sh, scripts/start_all.sh | every test `[[ ]]` (v1); NEW: right after `set -eu` a POSIX `case "${BASH_VERSION:-}"` guard exits 2 with a message when run by a non-bash shell; header comment says bash is required |
| README.md | one sentence under the Linux commands: run both scripts with `bash`; `sh scripts/...` fails in dash with `[[: not found` |
| tests/test_hygiene.py | quote- and comment-aware scan, tighter regex (catches `do [ ..`, `) [ ..`, `[` + tab, `else [`, `$( [`), 20 probe snippets (11 must be caught, 9 must not: `[[`, `]]`, arrays, `[ ]` in grep/sed/awk regexes, in comments and strings), the test covers .sh files and every workflow `run:` block |
| tests/test_reset_scripts.py | `_run` takes `*args`, `first_on_path`, `shell`; stub-python tests of start_all.sh (8 leadflow/nudge cases, 2 pid-file cases, unknown mode); dash guard tests |
| tests/test_smtp_provider.py | v1 test, comment fixed: same process, a restart is not proven |
| other test files, followup edge cases, workflow parse, lead step route | as in v1 |

Found while testing (important): under dash, `[[ x ]]` prints `[[: not found` and counts as FALSE. In reset.sh that silently skipped the "database not inside ./data" refusal (line 15), so a bare `sh scripts/reset.sh` on v1 was not just broken, it bypassed a safety check. Before the patch (single brackets) dash worked correctly. The guard fixes this; evidence-p1v2-6.

## Behaviour change to put in the PR text
`sh scripts/reset.sh` and `sh scripts/start_all.sh` (dash) worked before this series; now they stop at once with exit 2 and "run this script with bash". The shebang says bash and the README says `bash scripts/...`. The README now says so in one sentence.

## Per-rule count (issues of issues-pr4-0253.json fixed here): 15
githubactions:S6506 1, githubactions:S8541 1, shell:S7688 10 (reset.sh 6, start_all.sh 4), text:S6389 2, python:S5863 1. Extra, not flagged by Sonar: 2 `[ ]` in lint.yml run blocks.

## Rung table
| component | need | rung tried | verdict |
|---|---|---|---|
| curl/pip flags, `[[`, escape instead of raw char | 15 findings | standard tool options | CUT-TO-CONFIG, no new code |
| BASH_VERSION guard (3 lines each script) | `[[` silently false in dash skipped a deletion safety check | no standard option (shellcheck cannot stop a run); POSIX `case` is the smallest | KEEP-CODE (safety guarantee) |
| new tests | stop findings returning, prove the changed lines | existing test files extended, stub python in bash, no new tool | KEEP |

## Rungs run (files in /tmp/demo-push/handover/demo/sonar/)
| what | result | file |
|---|---|---|
| 6 affected test files with v2 (fresh clone, db54e13 + patch) | 225 passed, 3 skipped, 0 failed | evidence-p1v2-1 |
| mutants of start_all.sh, lint.yml | table above | evidence-p1v2-2 |
| ruff check, ruff format --check, mypy linux and win32, bandit -ll | all clean, bandit exit 0 (9 Low items hidden by -ll) | evidence-p1v2-3 |
| git apply --check: db54e13 alone; P3 and P2 each before and after v2 (in a clean tree each time) | all OK | evidence-p1v2-4 |
| v2 tests on old code | 6 failed, table above | evidence-p1v2-5 |
| dash guard and why it exists | evidence-p1v2-6 | |
| NOT run | full suite, playwright, gitleaks tests, actionlint on v2, Windows, CI, SonarCloud | |

## Series overlap
Touches lint.yml, README.md, scripts/*.sh and 6 test files (adds yaml import to test_hygiene.py, a `_run` signature change in test_reset_scripts.py). No conflict with P2 or P3 in either order (apply --check). Only the apply was tested, not the tests of the combined series.

## Expected to clear on SonarCloud
Same 15 as v1: S6506 (flags on the only curl), S8541, S7688 x10, S6389 x2, S5863. Risk: S7688 might flag the guard `case` (it is not a test command; I do not expect it); S6506 may want different flags (unknown).
