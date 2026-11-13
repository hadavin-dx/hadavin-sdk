# Fresh review (fourth reader): semgrep on main 61ded9e, v10 patch (sha256 7e944af3...0bfb, verified)
Read-only, offline, no y/yes answered, no pkill, no ruff/mypy/bandit/gitleaks-scan/hygiene/CodeQL/Sonar run (owner order 10:20Z). Scratch /tmp/work/sg10r (r = applied v10, git add -A only). Mutant tooling: /tmp/work/semgrep-v10/mine-fresh4.py (my mutants), /tmp/work/sg10r/run.sh (bounded, restores workflow and cmp after each). Final cmp of semgrep.yml against the patched original: identical.

VERDICT: CLEAN (0 Blocker, 0 Major, 4 Minor). Only Blocker/Major block.

## Checks
- git apply --check + apply on 61ded9e: OK, 9 files.
- Own tests (test_nosemgrep_form, test_gitleaks_semgrep_lock, test_workflow_files_parse, test_workflow_run_flags; gitleaks 8.30.1 on PATH, DPLD_REQUIRE_SCAN=1): 133 passed in 11.6 s. Matches body.
- Suppression grep on added lines: noqa, type: ignore, nosec, NOSONAR, pragma, pylint: disable, fmt: off/skip = 0. Word nosem in 64 added lines (matches body), all docs/test data/workflow message/comments; none a real suppression.
- Workflow read in full: triggers pull_request + push to [main] only (no pull_request_target); permissions contents: read; no secrets/token; fork PRs get a read-only token and no secrets; both actions pinned to the same 40-hex ids as lint.yml; persist-credentials: false; no github.* expression inside any run: (only github.ref / event_name in concurrency, which is not a shell); retry: only exit 2 retried, 3 tries, status kept and `exit "$status"`; exit 1 never retried; shell is GitHub's default bash -e, the `&& status=0 || status=$?` form is safe under -e. Install is hash-locked, wheels-only, --no-deps.
- docs/tests.md and the body checked sentence by sentence against the diff: no false sentence found (the ordering "fourth ... the third sonar.yml" is odd but true). Numbers I could not check offline (17 s install, 25 files/912/118 diff since 0841f36, lead's earlier clean run) are stated as the author's and not as measured here.
- (5) client-copy skip disclosure: in a copy without demo_only/ both new test files are skipped as a whole (2 skipped, measured by me on a tree without demo_only/). Body states it. True.
- (6) no-demo skip: same measurement; body wording correct.

## Mutants (workflow edited, tests run, restored, cmp identical after each)
Suite per mutant: test_nosemgrep_form.py + test_workflow_files_parse.py + test_workflow_run_flags.py + test_hygiene::test_workflows_are_pinned_and_limited.
Builder's (13 of 39 re-run), all KILLED: persist-credentials true, retry also on exit 1, GITHUB_TOKEN env, R1 step if, R3 extra action step, R4 --config=, R6 defaults shell, R7 step shell, R9 cache pip, R13 push dev, R15 install || true, R17 container, R18 workflow_dispatch.
Mine (30 run, 4 were no-ops and dropped): KILLED 24: yaml anchor/alias env; setup-python `token`; checkout `path`; checkout `token`; step env SEMGREP_RULES; step env SEMGREP_APP_TOKEN; pause 20 to 0; retry count 3 to 1; retry on any non-zero; exit status replaced by `exit 0`; scan line with backslash continuation; extra "semgrep scan" text in an echo; step name changes (install, setup-python); `message` branch edit; pip check removed; exit 1 hidden (`status=0` in the findings branch); flag order swapped; step `id:`; pull_request_target added; `|| true` after the scan; (S1-S7 below are the exceptions).
SURVIVED (8):
 S1 duplicate key `run: "true"` before the real `run:` in the scan step: PyYAML keeps the last, so the test sees the real one. GitHub's own parser rejects duplicate keys (not measured), so the job would fail, not silently skip. Minor.
 S2 `set -x` added to the scan run block: only more log output (the step has no secrets). Cosmetic, Minor.
 S3 `sleep "${RETRY_PAUSE_SECONDS}"` replaced by `sleep 0`: retries still happen, only the pause changes (the test sets the variable to 0 anyway). Cosmetic, Minor.
 S4 top-level `name: semgrep` changed: only the check name changes; matters only if a required-check rule names it (body says keep it not required). Minor.
 S5 extra lines in the scan run block that are not the scan line (an extra `echo >> $GITHUB_STEP_SUMMARY` before `exit`): the whitelist pins only the scan line and the env, not the rest of the block; the retry test runs the block but only with the stand-in. Cosmetic as tried.
 S6/S7 (the part that could matter) an early `if [[ ... ]]; then exit 0; fi` in the run block keyed on an environment variable. With a variable that the test shell does not have (my first try, `CI`) it survived locally, but with the value GitHub really sets (CI=true, GITHUB_ACTIONS=true, GITHUB_EVENT_NAME=pull_request) the retry test fails in lint.yml's test run (I re-ran those with the variable set: killed). So a skip keyed on a GitHub-set variable is caught by the lint job; one keyed on a variable absent from the test shell AND present only in the scan step is not possible any more (step env is whitelisted). Residual: only the exact-text of the run block is not whitelisted. Minor; the diff shows the block in review.
Net: nothing that makes the scan silently not run, opens a secret/write path, or changes the exit code, on a normal GitHub run, survived. The v9 Major (blacklist, 18 of 21 surviving) is fixed: all 21 of v9's reader mutants class are killed by the whitelist, and my 30 new ones leave only cosmetic survivors.

## Minor
m1 The run block text (other than the scan line, env, retry behaviour) is not pinned; consider asserting the whole block text or its hash. Optional.
m2 Duplicate YAML keys are not rejected by the test (PyYAML last-wins). Optional: a loader that raises on duplicate keys.
m3 `name:` of the workflow and of steps are not pinned (cosmetic).
m4 Whole-file skip of both new test files without demo_only/ is disclosed; it means the lock/gitleaks and workflow checks do not run in such a copy.

## Not done
No real Semgrep run, no GitHub run (nothing can show the registry result), full suite not run, hygiene/lint/type/secret scans not run by order. Mutants run the 4 workflow-related test sets above, not all 133 tests.
Preamble rules used: R5, R6, R12, R19 (no loop left running, no processes started).
