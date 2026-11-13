# crlf-guard-v6.patch (builder b13; base db54e13 and 2db3926; 2 files: tests/test_hygiene.py +135, docs/tests.md +1/-1)

sha256 of the patch file: 2d032787d57326e72c5f648090df0c3e879a0ab47963b96a9920511481c193c7 (168 lines of patch text). Companion patch: `sonar/sonar-p1-quickwins-v3.2.2-delta.patch` (sha256 b9c941027ac7238cc5f151107b299453baf2abb35c23b96a4455d86ff89a26f3, test-only, +22/-1 in tests/test_workflow_run_flags.py).
Built from the reviewer's `crlf-guard-min-reviewer.patch` (+110/-1). No push, no network write, made-up data only. EGM not run by me (builder; the lead runs the EGM step). No bible folder on this machine: no R-numbers cited.

## What failed, was wrong or is not proven (first)
1. **My own slip, caught by the real run:** my first version of the new helper was called `_gitleaks_sees_the_cr_only_in_the_crlf_copy` (44 characters). The repository's own literal scan (pattern 9, 40 or more unbroken letters) reported it, and `test_hygiene_scan_public` failed on it ("hardcoded literals found"). The five-test selection I used for mutants did not include that test; the whole-file run found it. Renamed `_check_gitleaks_premise`. Then my v3.2.2 test text (`"jobs:\n  call:..."`) hit the same scan (`s:\n` looks like a drive letter path); rewritten with `chr(10).join([...])`. Both were found by running the whole stack with `DPLD_REQUIRE_SCAN=1`, not by my selected tests.
2. **Size.** v6 is +135 lines of test code and +1/-1 docs = **+136/-1** (min patch +110/-1, v5 +253/-4). That is under the "about 140" of this order and over the older "about 120". I did NOT drop the lone-CR mutant class (it is cheap here: one parametrized case). If the lead wants 120: delete `test_a_gitleaks_that_crashes_on_the_clean_copy_is_not_taken_for_clean` (14 lines, the E13 kill) and the 2 nested-file lines (E6 kill); then E13 and E6 are alive again (measured below).
3. **Not run:** real Windows, macOS, PowerShell, cmd (the `py -3` hint and the cures were not run there; reasoned only, as in the review). The 12-patch stack was run only on the affected 16 test files plus `tests/test_gitleaks_exceptions.py`, not the full suite (the lead runs it). No CI, no SonarCloud.
4. **Two new `# noqa: S603` comments** (the two `subprocess.run` calls in the new tests, same form as the 7 already in this file). The studio's no-suppression rule is about Sonar findings; this is the file's existing ruff convention for a constant argv list. I removed the 3 I could (the planted-tree git calls now go through the existing `_git` helper). Your call if you want zero.
5. Survivors of my mutants (11 of 53, all classified below). None is a mutant of the cure text, the hint, the file list, the exit codes or the measured scope.

## What v6 changes against the reviewer's min patch
| item | min patch (measured) | v6 (measured) | how |
|---|---|---|---|
| E10 safety assert weakened to `assert names` | already KILLED in min (F9; the empty tree holds exceptions.txt) | KILLED | nothing to change; kept |
| E13 only exit code 1 counts: a gitleaks that crashes (exit 2) on the clean copy | SURVIVES (fake program that exits 1 on a CR copy and 2 on the LF copy: test passes) | KILLED by 2 tests | the premise test now demands exit 0 on the LF copy and exit 1 on the CRLF copy (was `(rc == 1) is found`); `test_a_gitleaks_that_crashes_on_the_clean_copy_is_not_taken_for_clean` runs the same check with a fake `subprocess.run` returning 2 (git still runs for real) and expects the failure. Real fake programs: `evidence-b13-2-fake-gitleaks-rc.txt` |
| E16 hint drops "or a lone CR" | SURVIVES | KILLED | "a lone CR" added to HINT_PHRASES |
| E6 guard matches the base name only | SURVIVES | KILLED | the bad-file test plants a CRLF `sub/exceptions.txt`; only root files are named |
| F25 (not asked): the REPO patch leaking out of `_guard_message` again | SURVIVES in min | KILLED | one line: `assert REPO != tree` after the `with monkeypatch.context()` block (the Major 1 fix is now pinned, not only present) |
Note on the scan code: v6, like the min patch, does not touch `test_hygiene_scan_public` (its `assert p.returncode == 0` already fails on any non-zero exit, so a crashed scan fails there; the E13 mutant `== 1` existed only in v5's rewrite). The premise test is the only place where an exit code can hide.

## (1) Re-verification (evidence-b13-1*)
- Apply: `git apply --check` of v6 on db54e13 and on 2db3926: OK (also staged on both).
- Whole `tests/test_hygiene.py`: **21 passed** (15 old + 6 new) with `GIT_CONFIG_GLOBAL` core.autocrlf=false and =true, on db54e13 and on 2db3926, gitleaks 8.30.1, `DPLD_REQUIRE_SCAN=1`, `--strict-markers`; and in a real `git clone -c core.autocrlf=true --no-checkout` + `checkout db54e13` + v6: 21 passed (repo config autocrlf=true, global config empty).
- Real clone, plant CRLF and lone CR in each guarded file: guard fails with the cure text (4 of 4); `git checkout -- file` and the Python one-liner both give 0 CR and bytes identical to the LF original (8 of 8) (evidence-b13-1b).
- No gitleaks on PATH, `DPLD_REQUIRE_SCAN` unset: 5 passed, 1 skipped (the skip names the variable); with `DPLD_REQUIRE_SCAN=1`: the premise test fails (evidence-b13-1c).

## (3) Scope claim, measured (evidence-b13-3-scope.txt)
Clean clone of db54e13, ONE file kind turned to CRLF at a time, gitleaks 8.30.1:
| file turned to CRLF | `gitleaks dir . --exit-code 1` | `hygiene.pipeline` (the tests) | `lint.yml` literal-scan step (`git grep -f patterns.txt` minus `grep -v -E -f exceptions.txt`) | tests/test_hygiene.py + tests/test_gitleaks_exceptions.py (59) |
|---|---|---|---|---|
| none (baseline) | 0 | 0 findings | 2636 lines found, 0 left | 59 passed |
| .gitleaks.toml | 0 | 0 | 2636 / 0 left | 59 passed |
| patterns.txt | 0 | 0 | 2636 / 0 left (same 2636) | 59 passed |
| exceptions.txt | 0 | 0 | 2636 / **2636 left** (the CI step would fail, and print 2636 lines that say nothing about line endings) | 59 passed (the tests read the file with Python) |
| requirements-*.txt and the three `.in` files (8 files) | 0 | 0 | 2636 / 0 left | 59 passed |
| sonar-project.properties | **1 (finding)** | 0 | 2636 / 0 left | **1 failed** (`test_hygiene_scan_public`: "gitleaks dir reported findings") |
So the reviewer's v5 comment ("a CR in any of the 5 kinds makes gitleaks report the key line") was an overclaim: only sonar-project.properties does. exceptions.txt stays in the guard because the measured effect is real (the `lint.yml` step), but the effect is in CI's shell step, not in the Python tests. The comment in the code and the paragraph in docs/tests.md now say exactly this table. Not measured: `pip install --require-hashes` on a CRLF lock file (pip not run); a CR in other files (only the five kinds named in the v5 comment were tried, plus .gitleaks.toml).

## (4) Mutants (evidence-b13-4-*; one table: evidence-b13-4-mutant-table.md)
53 mutants of v6 run against the 6 new tests under autocrlf false AND true (killed = killed in both unless said): reviewer's F1-F30 (his rv25 mutants of the min patch), my G1-G23 (the reviewer's E-list items that still exist, the builders' items that still exist, and new ones).
**41 killed, 1 killed only with autocrlf=true (F13: .gitattributes dropped from the planted tree), 11 survived.** Survivors:
- F15 `--config` dropped from the premise run: equivalent (gitleaks finds ./.gitleaks.toml in the cwd); G20 (the copy of the toml not made) is killed.
- F24 `ls-files -o -c`: adds untracked files only; no test plants an untracked file; equivalent for the tracked-file check.
- F30, G12: variants of how the planted tree is set up (index not LF; only one file written): equivalent for these tests.
- G13 LF_ONLY_FILES also lists `.gitleaks.toml` (scope wider than measured): not pinned by a test; a wider list is not wrong, only unmeasured.
- F26, F27, G14, G15, G16, G19: deleting a parameter or an assertion of the tests themselves (lone-CR case, byte compare of the cured file, second cure, guard re-check, hint phrases). They are removals of test lines, not code mutants; the code mutants these lines exist for (F2, F3, G11, G18, F28, F29, F1..F22) are all killed.
Builders' 58-row table and the reviewer's 26 E-mutants are mapped onto v6 in the same table file: rows about code v6 does not have (the scan-failure message, report-row reading, .editorconfig, the pyproject marker, the .ps1 exemption, the five-glob list) are marked "n/a: code not in v6" with the reason. Rows with a v6 counterpart are all killed except where listed above (E17/F30, E18/F24, E26/G12 are the equivalent ones).
The min patch, same mutants (evidence-b13-4b): F9 (E10) killed, F25, G1 (E6), G2 (E16) survived; v6 kills all four.

## (5) Apply matrix on db54e13 (evidence-b13-5-apply-matrix.txt)
12 items: C = crlf-guard-v6, P1 = sonar-p1-quickwins-v3.2, P1d = v3.2.1-delta, P1dd = v3.2.2-delta (mine), P2 = sonar-p2-regex-http-bug-v2.1, P3 = sonar-p3-path-helper-v3, N1 nodemo-ci-job-v3, N2 nodemo-fix-v3, N3 nodemo-optional-hygiene-repo-v4, N4 nodemo-ruff-isort, G = semgrep-on-db54e13-v5.1, T = sonar-yaml-test-trimmed-v2 (files taken from /tmp/demo-lead/handover/demo/, the demo-push copy of sonar/ does not hold the nodemo-v3/v4, P2 v2.1 and semgrep v5.1 files).
- Each alone on db54e13: all OK except P1d and P1dd (they need P1: expected).
- All 132 ordered pairs: 92 OK, 40 FAIL; every one of the 40 is a delta before its base (P1d or P1dd first, or P1d/P1dd after a patch other than P1): 0 unexpected. `P1, P1dd` (without P1d) applies.
- 3000 random full orders of all 12 (2000 seed 13 + 1000 seed 99; P1 < P1d < P1dd enforced, the rest free): **0 failures**. v6 alone on 2db3926: OK.
- The stack of all 12 applied in one order on db54e13 (46 files changed, 4327 insertions, 98 deletions): ruff check, ruff format --check (156 files), mypy --platform linux and win32 (28 source files), bandit -ll exit 0 (same 9 Low as db54e13 alone): clean (evidence-b13-7). The 16 test files the stack changes or adds plus tests/test_gitleaks_exceptions.py: **716 passed** with autocrlf=false and 716 passed with autocrlf=true, gitleaks 8.30.1, `DPLD_REQUIRE_SCAN=1` (evidence-b13-8). The earlier failing run (item 1 above) is why the evidence is the second one.

## (6) Reusable-workflow job and P1 (evidence-b13-6-*)
- Does v3.2.1 already handle a job with `uses:` and no `steps`? **No for `tests/test_workflow_run_flags.py`**: v3.2.1 fixed the null-steps problem in `tests/test_shell_single_bracket.py` (`_step_groups`), but `_run_commands` in test_workflow_run_flags.py still reads `job["steps"]`. Measured on db54e13 + v3.2 + v3.2.1 + a workflow `.github/workflows/call.yml` whose only job is `uses: octo/repo/.github/workflows/x.yml@<40 hex>`: `KeyError: 'steps'`, 2 failed (the curl test and the pip test, `[call.yml]`), 154 passed; `test_shell_single_bracket.py` and `test_workflows_are_pinned_and_limited` pass.
- The reviewer's second failure (`test_workflows_are_pinned_and_limited`) is a different thing: it fails for a `uses: ./.github/workflows/lint.yml` job because the pin test accepts only `owner/repo/...@<40 hex>`. Measured on plain db54e13 without any patch: the same failure. So it is the existing pin policy, not P1.
- `sonar-p1-quickwins-v3.2.2-delta.patch`: `for step in job.get("steps") or []:` (a missing key and an empty `steps:` both mean no steps) plus `test_a_job_without_steps_has_no_commands_and_the_next_job_is_still_read` (a `uses:` job, an empty `steps:` job and a real job with `run: echo hi`; expects `["echo hi"]`). With the call.yml tree: 157 passed. Mutants on the new test: `job["steps"]` killed, `job.get("steps", [])` killed (empty `steps:` is None), stop-reading-at-the-first-job-without-steps killed, `or [{}]` survives (equivalent: a step `{}` has no `run`). It applies after v3.2 (with or without v3.2.1); alone on db54e13 it fails because the file does not exist there.

## Rung table (preamble 20)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| CR guard in tests/test_hygiene.py | say "line endings" before two scans fail without saying it | `.gitattributes eol=lf` already in the repo (stops Git from writing CRLF, not an editor that saves it); `git ls-files --eol` in CI, pre-commit `mixed-line-ending`: NOT tried, UNVERIFIED | scope table above | a message that names the file and two cures that a test runs | KEEP-CODE (small), lead may cut to a CI `git ls-files --eol` step once someone measures it |
| cure commands in the message | a reader can fix it without GNU sed | `git checkout -- file`; one Python line | both run by the tests and in a real clone (8 of 8) | nothing | KEEP |

## Files
skips/crlf-guard-v6.patch, sonar/sonar-p1-quickwins-v3.2.2-delta.patch, this file, skips/evidence-b13-1-verify.txt, -1b-real-clone-cures, -1c-no-gitleaks, -2-fake-gitleaks-rc, -3-scope, -4-mutants-v6.txt, -4-mutant-table.md, -4b-min-patch-before, -5-apply-matrix, -6-reusable-before / -after / -mutants, -7-gates-stack, -8-stack-tests. (The v3.2.2 delta is in the skips/ evidence set because it was built for this order; it was written to sonar/ as ordered.) Scratch: /tmp/work/b13-14803.
