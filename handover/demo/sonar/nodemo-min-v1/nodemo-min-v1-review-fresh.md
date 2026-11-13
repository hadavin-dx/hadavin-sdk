# Fresh review: nodemo-min-v1.patch (round 1 of 2)

Verdict: NOT CLEAN, for the stack with PR #12 (Major 1). The patch on main 61ded9e is CLEAN: no Blocker, no Major in the patch itself.
Reviewer: fresh reader, Python 3.12.3 venv (/tmp/work/rv37-main/venv312), job run with NORUFF=1 through /tmp/work/rv37-main/drv/runjob.py (executes the workflow's own run: blocks, install steps skipped: no network). One pytest at a time; full suite not run outside the job's chunks; no ruff/mypy/bandit/gitleaks scan/hygiene scan/Sonar run by me (the job's own gitleaks binary is used only by the tests that need it).
Patch sha256 verified 4f4de258...c67a. Applies (git apply --check) on 61ded9e and on PR #12 head 8d65577.

## Major
1. The job goes RED on PR #12 head 8d65577 (patch applied). Measured: step "Tests", collect-only fails with exit 2:
   `ERROR tests/test_followup_b.py ... ModuleNotFoundError: No module named 'demo_only'`.
   Cause: PR #12's tests/test_followup_b.py (line 9) has `from tests.support import start_proc, stop_proc`. conftest's `_NEEDS_DEMO` regex matches `from support`/`import support` but not `from tests.support`, so the file is not turned into a placeholder and fails at collection in a client copy. This is a true positive (the file really does not work in a client copy), not a flaw of the job. But the lead must know: merging nodemo before PR #12 is fixed makes PR #12 red; PR #12 needs `from support import ...` (as the other tests do) or the regex widened. Not measured: whether PR #12 is otherwise green after that change (I did not re-run it). NOTES-nodemo-min.md says only "applies on PR #12 head"; it does not say the job is RED there. Add one sentence.

## Checked and OK (evidence)
(1) Feed skip. `from conftest import DEMO_PRESENT` is conftest.py's own exported name (line 21, same module-level helper conftest itself uses for the placeholder rule). Style note: no other test file imports DEMO_PRESENT; the only other `from conftest import` is test_portal_demo.py (`Env`); test_except_clause_hierarchy computes its own DEMO_GONE and test_portal_demo uses module-level pytest.skip. So "existing helper" is true for the name, not for a prior user of it; it adds no new mechanism and no noqa. Reason text names demo_only, so the gate counts it as expected. With the demo present and DPLD_REQUIRE_DEMO=1: `tests/test_sonar_p2_feed_optional.py` 3 passed (no behaviour change). The file stays real in the client copy (no `support`/`env`/`test_*` import: it runs 2 tests and skips 1).
(2) Workflow read in full. Triggers pull_request (main) + push (main), not pull_request_target; fork PRs get a read-only token and no secrets; `permissions: contents: read`; timeout-minutes 60; checkout and setup-python SHAs identical to lint.yml (3d3c42e5..., 6d4fd22b...), persist-credentials false; no secrets; the only `${{ }}` is `runner.temp` in an env: block, none in a run:; gitleaks download and checksum identical to lint.yml; install uses --require-hashes on requirements-dev.txt as lint.yml does. Gate logic: junit based, per-chunk exit code, tests/cases/skip counts cross-checked, passed+skipped+xfailed minus module skips equals collect-only, floor 85 percent, unexpected skips cap 3, env skips cap 6.
(3) Fails-before / after, own run, main 61ded9e:
   - WITHOUT the skip (workflow only): RED, "chunk 7: pytest exit code 1"; chunk 7 log: `FAILED tests/test_sonar_p2_feed_optional.py::test_feed_calls_the_configured_desk_address`.
   - WITH the patch: GREEN, passed 888, skipped 86, xfailed 0, collected 974, 0 environment skips, 0 unexplained skips, floor 828, share 91.2 percent; 73 `needs-demo-only` placeholder items counted from the junit files (matches the comment's "73 placeholder files").
(5) Suppressions: grep of added lines for noqa, type: ignore, nosec, NOSONAR, nosemgrep, pragma, pylint: disable, fmt: off/skip finds 0.
(6) Semgrep v10 stack (main + nodemo + semgrep-on-main-61ded9e-v10.patch): GREEN, passed 891, skipped 88, collected 979, unexplained skips 0 of 3 (the two new files that `from support import REPO` become placeholders whose reason names demo_only: counted as expected). PR #12: see Major 1.

## Own cases on the real job (patch applied on main, each a full job run)
| case | result |
|---|---|
| a failing test in a chunk | RED (chunk 8 exit code 1) |
| the failing test while pytest's exit status is forced to 0 by a conftest hook (swallowed exit code) | RED "tests failed" (junit shows it) |
| addopts `-p no:junitxml` (pyproject) | RED (no valid junit file for chunk 0) |
| conftest os._exit(0) at session finish (all runs) | RED (no "N tests collected" line) |
| same, only in the real runs, not collect-only | RED ("tests failed in the no-demo copy": a test of this repo also trips, not junit-clean) |
| conftest sys.exit(0) at import | RED (no "N tests collected" line) |
| xfail strict that xpasses | RED (chunk 8 exit 1) |
| python_files extended by check_*.py with a failing file | RED |
| conftest drops one file's tests only in the real runs | RED "973 tests reported but 974 collected" |
| conftest drops them only in collect-only | GREEN, but a no-op: pytest's "N tests collected" counts before modifyitems, so nothing real was lost (the id list shrank, the count line did not) |
| conftest drops them in both modes | RED "973 reported but 974 collected" (the count line ignores the drop, so the gate sees it) |
| deleted junit file | RED (from the nojunit case: "no valid junit result file ... removed") |
Two of my first-round cases were invalid (a pytest.ini replaced pyproject's pythonpath); I redid them through pyproject and report only the redo. Not tried: forged junit plus os._exit (NOTES already says GREEN, deliberate only), `-k` in addopts (reasoned: the count line becomes "N/M tests collected (K deselected)", the regex does not match, RED; not run).

## Minor
- Comment in the workflow says a test calling os._exit(0) "cannot make it green"; NOTES says forged junit plus os._exit(0) is GREEN. Qualified in NOTES ("deliberate only"); consider "cannot make it green by accident".
- (4) NOTES honesty: the dropped "real file became placeholder" comparison (an `import support` added to the biggest real file, 54 tests, measured GREEN: 823/81/904 in batch7.out) is stated in NOTES "What it does not prove" and in the workflow comment ("It does NOT see one test file turning into a placeholder"). No false sentence found. The PR body must repeat it (I did not see a PR body; NOTES is the only text I judged).
- Not run on a GitHub runner; actionlint/shellcheck not run (stated in NOTES). Install steps skipped here (no network); the dependency set is lint.yml's, unmeasured on the runner.
- Floor of 85 percent against 91.2 percent leaves 6 points: about 58 tests can silently become placeholders; the limit is stated.

## Files
Evidence dir: /tmp/work/rvfresh/ (logA.txt without skip, logB.txt with patch, log-c-*.txt cases, log-s10.txt, log-p12.txt, cases*.out).
