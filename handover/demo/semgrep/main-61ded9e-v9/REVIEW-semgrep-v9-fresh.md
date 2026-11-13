# Fresh review (third reviewer): semgrep on main 61ded9e, v9 patch (sha256 b59f5bd9...9d73, verified)
Reviewer: fresh, read-only, offline (no curl; no real Semgrep run; no y/yes answered; no pkill). Scratch: /tmp/claude-0/-home-user/b34836a1-affe-5ae5-ba66-3c71b6499c1e/scratchpad/v9 (r = applied + one commit on detached 61ded9e, gc = fresh clone for gitleaks, nd = no-demo copy, mine.py/runm.sh = my mutant tools). Preamble rules used: R3, R5, R6, R7, R8, R19, R20.

VERDICT: NOT CLEAN (0 Blocker, 1 Major, 5 Minor). v8's three Majors are fixed (checked, below). The one Major is the same class as v8's M-3: the workflow-hazard test is a blacklist, and 18 of my 21 new mutants of the workflow pass every test.

## Major
M-1 (workflow guard is a blacklist). `_workflow_problems` in tests/test_nosemgrep_form.py names known hazards one by one; anything else passes. My mutants (workflow restored and `cmp` identical after each; no loop left running), run against the workflow tests (test_nosemgrep_form no-known-hazard + retry + concurrency, test_workflow_run_flags, test_workflow_files_parse, test_hygiene::test_workflows_are_pinned_and_limited). SURVIVED (26 passed each): 
 1 scan step `if: github.event_name != 'pull_request'` (scan never runs on a PR);
 2 job `if: false`;
 3 a second step `- uses: actions/cache@<40 zeros>` (any extra action/step);
 4 `--config=https://rules.invalid/r.yml` (the `--config=` form is not in the pack list);
 5 `--exclude=src` (the `=` form is not in the folder list; `--exclude src` is caught by accident as a folder);
 6 top-level `defaults: run: shell: sh`;
 7 scan step `shell: sh` (the retry test runs `bash -e -c` itself, so the step's shell is never tested);
 8 `strategy: matrix`;
 9 setup-python `cache: pip`;
10 python-version "3.9" (lock is for 3.12);
11 scan step `working-directory: tools`;
12 job `env: SEMGREP_RULES: p/ci` (literal, no secret);
13 `push: branches: [dev]` (no push scan on main);
14 `pull_request: branches: [nothing]`;
15 install `... || true` (broken install hidden; the later pip check step may still catch);
16 scan step `timeout-minutes: 1`;
17 job `container: evilcorp/img:latest`;
18 added trigger `workflow_dispatch:`.
KILLED: `-c <url>` (as an extra "folder"), a second job with `needs`, `--exclude-rule x` (as a folder).
Confirmed against ALL 8 focused files (333 passed, nothing failed) for 1, 3 and (all 8 files) 4 was killed only incidentally by the hardcoded-URL scan in test_hygiene_scan_public (a non-URL value such as `--config=./evil.yml` has no such guard). The other survivors I ran only against the workflow-related tests above, not all 8 files: say so; treat 1, 3, 6, 7, 11, 17 as the ones that matter.
Builder's 18 mutants (mutate.py): all 18 KILLED by me, restored and cmp-identical after each. So the 8 v8 survivors are fixed; the class is not.
Fix (cheap, ends the tail): compare the parsed workflow to a whitelist instead of a blacklist: exact top-level keys {name, on, permissions, concurrency, jobs}; `on` exactly {pull_request: {branches: [main]}, push: {branches: [main]}}; exactly one job whose keys are exactly {runs-on, timeout-minutes, steps}; exactly 5 steps with exact `uses` values (the two pinned SHAs) and exact key sets (no `if`, `shell`, `working-directory`, `env` except the one RETRY_PAUSE_SECONDS, `continue-on-error`); `with` exactly as now; reject any scan word that starts with `-` and is not in a fixed allowed list (this also covers `--config=`, `--exclude=`, `-c`). About 25 lines; add my 18 as mutants.
(Per the round cap: this is the same Major class v8 had; if the owner prefers speed, the alternative is to word the body's "does NOT prove" bullet and the test docstring as "18 + 21 listed changes are caught, nothing else is" - it already says "a sample, not a proof", so the honesty part is present. I still rate it Major because the scan silently not running (survivor 1, 13, 14) is the one thing this workflow exists to prevent.)

## Suppression grep (first task)
git diff --cached 61ded9e, added lines only: noqa = 0, nosec = 0, NOSONAR = 0, type: ignore = 0, pragma = 0, pylint: disable = 0, fmt: off/skip = 0. The WORD nosem/nosemgrep: 64 added lines (docs/tests.md 2, the workflow's echo message 1, tests/test_nosemgrep_form.py docstring/comments/test data, the .py file name line). The comment-shaped hits (`# nosemgrep:`, `// nosem`) are all inside Python string literals of test data or inside comments of tests/ (not scanned by Semgrep; the new test excludes docs/, itself and the workflow). No new real suppression. Pre-existing on 61ded9e: noqa S603 at tests/test_hygiene.py:48, 200, 209 (+S607) and tools/hygiene.py:114-115, unchanged by the patch. grep -c noqa in the two new test files = 0. => no Major from suppressions.

## v8 Majors, checked
M-1 (noqa/run_cmd): tests/run_cmd.py gone; both new files `from test_hygiene import _run`; ruff check "All checks passed" with 0 new noqa. OK. (Side effect: new files import a test module and `support`; disclosed.)
M-2 (no shell sentence): body line 5 now says bash -e -c of the scan step's run: block read from semgrep.yml, other two are fixed git/gitleaks words. Matches the test code (`_run(tmp_path, "bash", "-e", "-c", _scan_run_block(...))`). OK.
M-3: 8 survivors now killed (see above) but the class remains (M-1 of this report).

## (1) Workflow semgrep.yml (read in full)
Triggers: pull_request and push, branches [main]; no pull_request_target; no workflow_run. Fork PR: read-only token, no secrets, nothing needs one. permissions: contents: read top level, no job block. Actions pinned to full SHAs, same two as lint.yml lines 26/31 (compared). persist-credentials: false. Expression injection: no ${{ }} in any run:; only the concurrency group uses github.ref (not a run: step; safe) and cancel-in-progress uses event_name. Install: --require-hashes --only-binary=:all: --no-deps. Retry: only exit 2 retried (stand-in test, 8 cases pass, retry-on-1 mutant killed); `exit "$status"` preserved; echo before loop cannot change the code; `[[ ]]` with `bash -e`: `cmd && status=0 || status=$?` keeps -e from aborting. Secrets: none. Note (not a defect): exit 2 also covers a bad --config, so a typo is retried 3x (workflow comment says so). Rules fetched live (disclosed).

## (3) Claim rows: 29 of 87 re-measured
OK by my own measurement: 4 (9 files, +1807/-1), 5 (src 0), 9, 10 (sha256), 13 (1130 lines, 67 pins, 919 hashes), 21 ([[ at lines 70,72,74,76), 24 (3 JSON), 34, 38, 40 (SHAs; checkout/setup-python lines 28/32), 41, 46 (.codeant line 20), 47, 49 (dependabot github-actions only), 51/52 (per-file counts 24, 93, 4, 44, 5, 10, 146, 7 = 333; ran 333 passed in 80 s with DPLD_REQUIRE_SCAN=1), 54 (18 builder mutants all killed), 57/72 (git apply --check OK; 9 files), 58 (gitleaks dir + git on a fresh clone with one ref and 5 commits: no leaks), 59 (ruff, format 158 files, mypy linux+win32 28 files, bandit rc 0), 65 (47 files), 69, 70 (cwd=target line 200), 74 (lint.yml lines 13-14, 18, 26, 31), 75 (lint.yml 47-48), 76 (no-demo copy: 15 passed, 6 skipped, ruff clean; matches body; evidence-4 itself shows the 5-file run), 78 (0 and 64 reproduced; plus pragma/pylint/fmt 0), 79 (grep noqa 0 in both files), 80 (`_git_text` hardcodes git, check=True: true), 81 (exceptions.txt line 34 = the otel line), 87 (head_ref/base_ref/ref_name/actor in the regex, mutants killed), 86.
Not re-measured: 6, 25-27 (lead's docker run), 37, 39, 42, 43, 55, 56, 62, 66-68, 71, 85 (earlier-tree files), 7/8/28/29/65-diff (needs db54e13/3598120, not in my clone: `bad revision db54e13`; I checked 61ded9e tree 4aa3ea0c3e... and its message "head 3598120" only).
Row 84 text ("18 workflow changes ... NOT a claim that the workflow is guarded") is honest and consistent with M-1.
False/loose sentences in the body: none false. Loose: body "Eighteen made-up changes were tried and all are caught" vs the test file holding 21 mutant cases (the 18 are the builder's mutate.py set; 3 more are in the test only); say "21 in the test, 18 re-run with mutate.py".

## (4) docs/tests.md numbers
25 files / 912 / 118, 47 files each appear once in the added text; consistent with row 29/64 (the 25/912/118 diff needs 0841f36, not in my clone: not re-measured), 3 JSON, 20 s, 3 tries, 20 min match the workflow. No stale number found.

## (5) Gates on the applied tree (61ded9e + patch, gitleaks 8.30.1 on PATH, DPLD_REQUIRE_SCAN=1, gpgsign off via GIT_CONFIG_COUNT)
ruff check: All checks passed. ruff format --check: 158 files already formatted. mypy --platform linux and win32: no issues in 28 source files each. bandit -ll -r src tools scripts -c pyproject.toml: rc 0. 8 focused files: 333 passed in 80.27 s (one pytest at a time; full suite NOT run). Committed-state gitleaks dir and git on a fresh clone: no leaks. git apply --check: OK.

## (6) Client-copy skip disclosure
Present under "What this PR does NOT prove" (bullet "In a client copy ... both new test files are skipped as a whole"). Measured here: 15 passed, 6 skipped (whole files), ruff clean. OK.

## Minor
m-1 body "Eighteen" vs 21 cases (above).
m-2 `--config=`/`--exclude=` glued forms are invisible to the pack and folder checks (part of M-1).
m-3 retry test never uses the step's `shell:`; a `shell: sh` step would break `[[ ]]` on the runner and no test sees it (part of M-1, survivor 7).
m-4 body "Tests run" line mixes v8/v9 counts ("the v9 run of 5 of the files skipped 3") - correct but hard to read for a non-technical reader (preamble R14).
m-5 the two new test files import `test_hygiene` (a test module) and `support`; any failure of test_hygiene's import breaks them too (disclosed in row 79).

Slips: none beyond a backgrounded loop: my 3-mutant full-suite loop ran longer than 120 s and moved to the background; I did not start another until it finished, then confirmed the workflow `cmp` identical to the original (and no process of mine is running). Tokens: not metered.
