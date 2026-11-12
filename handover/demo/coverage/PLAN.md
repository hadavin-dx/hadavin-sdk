# Lane 7c (after review 2): coverage in the SonarQube job, patch v3

Base: public branch pr-3-tests head **558d37f**. `sonar-coverage.patch` is now **v3** (made with `git diff -U1`, 9 files);
`sonar-coverage-v2.patch` and `sonar-coverage-v1.patch` are the earlier ones. v3 applies on a fresh clone of 558d37f
alone and in BOTH orders with the lead's gitleaks fix (v1 and v2), plain and with `--3way` (evidence-r3-apply-orders.txt).
Nothing was committed or pushed to the public repo.

## 1. Failures, open points, UNVERIFIED (read first)

Failures and slips of this round:
1. **My first `gitleaks dir` run in round 3 reported findings (1, later 23)**: those were cache files my own ruff and pytest
   runs had written into the scratch tree (`.ruff_cache`, `__pycache__`, `.pytest_cache`), not the patch. I re-ran in a clean
   tree with gitleaks first (0 findings, evidence-r3-checks.txt), as lint.yml does. The first `--3way` attempts also failed
   because I had not staged the first patch; redone, evidence-r3-apply-orders.txt says so.
2. **The lead's own gitleaks allowlist in 558d37f does not work** (unchanged from round 2): without the gitleaks fix patch,
   `tests/test_hygiene.py::test_hygiene_scan_public` FAILS with the real binary (evidence-r3-checks.txt, last block). It is
   fixed by `gitleaks/gitleaks-toml-fix-v2.patch` (also v1), which is not part of my patch; the lead decides.
3. The lock-drift test of round 2 is DELETED (finding 1): a single pip call detects drift by itself (section 1b).

UNVERIFIED (nothing offline can settle these; the first real run on the pull request does):
- (a) that sonar-scanner accepts `coverage.xml` through `sonar.python.coverage.reportPaths` (docs.sonarsource.com unreachable,
  no scanner run allowed);
- (b) how Sonar treats the empty `<source/>` entry coverage.py writes next to `.` in `<sources>` (evidence-xml-check.txt);
- (c) that the action SHAs belong to the named actions and that the lock hashes are the real packages: only hash FORMAT and pip's
  `--require-hashes` acceptance are verified (pip downloaded the packages and the hashes matched, evidence-r3-pip-C.txt);
- (d) the scan time and the real run time on a hosted runner; `timeout-minutes: 60` is a placeholder (only measured: pytest on a
  shared 4-vCPU machine);
- (e) the pip behaviour on the hosted runner: tested with pip 24.0 (the venv's pip) and 26.2.2 on Python 3.12.3 here; the pip that
  `actions/setup-python` ships on the runner was not looked at (both pips I tried gave the same result);
- (f) **the full suite on 558d37f with the v3 patch**: DONE in round 3 (it was missing in round 2): one serial run of the job command on 558d37f + v3 + gitleaks fix v2: `2349 passed, 116 skipped in 875.10s (0:14:35)`, exit 0, 0 failures (evidence-r3-full-run.txt). Machine load was 1.3 at the start and 1.1 at the end (shared). That run was in a tree outside /tmp/work/venv-cov2, so the `.venv-cov` artefact did not recur. Still UNVERIFIED: the same run on a hosted runner.
- (g) **the pip single-invocation result** is now TESTED (finding 1), not unverified: see 1b and evidence-r3-pip-*.txt.

Open points: the Sonar-side settings (section 6) and the owner decisions A and B (section 8) are described, not done.

## 1a. Numbers: what they are and where they come from

- **Round 3 run (558d37f + v3 + gitleaks fix v2): `2349 passed, 116 skipped`, collected 2465, 0 failed**, 875.10 s. Coverage: line-rate
  **0.9253** (6539 of 7067 lines), 35 files, all repo-relative and present on disk, `<sources>` = `.` plus the empty entry (evidence-r3-xml-check.txt,
  evidence-r3-coverage.xml). Worst case if Sonar counts the three never-imported scripts as uncovered: 6539 / 7294 = 89.7 percent.
- The v1 run on b29bb1f (evidence-pytest-coverage.txt) gave `1 failed, 2348 passed, 116 skipped` (collected 2465) and line-rate 0.9257 (6542 of 7067).
  The "2349" quoted earlier was passed plus failed of that run, so it left out the 116 skips; its one failure was the `.venv-cov` artefact
  (a virtual environment inside the tree, section 9), which passes outside. The difference of 3 covered lines between the two runs (6542 vs 6539)
  is not explained by any change in Python source (there is none, see next point); I did not investigate it (run-to-run timing of subprocess tests is the likely cause, UNVERIFIED).
- Did 558d37f change Python source against b29bb1f? No: `git diff --stat b29bb1f 558d37f` is one file, `.gitleaks.toml`, 7 lines added (evidence-r3-base-diff.txt).
  So the round 3 run and the v1 run measure the same Python code.
- The 116 skips: 113 playwright (22 + 28 + 60 + 3 of `-rs`), 1 gitleaks test (no `DPLD_REQUIRE_SCAN` in the job), 1 load setting, 1 Windows-only.

## 1b. What changed after review 2

| # | Finding | What I did | Proof file |
|---|---|---|---|
| 1 | MAJOR rule 20: pip itself was not tried as the higher rung | Tested one call `pip install --require-hashes -r requirements-dev.txt -r requirements-coverage.txt`. Identical pins (the real case): accepted. Conflicting pins (pytest 9.2.0 vs 9.1.0 with its real hash): hard error `ResolutionImpossible ... The user requested pytest==9.2.0 / pytest==9.1.0`, exit 1, in both file orders, with the version edited alone too, and with pip 26.2.2. Today's two separate calls: the second one silently replaced pytest 9.2.0 by 9.1.0, exit 0. `-c requirements-dev.txt` also works (error shown as "constraint"). So sonar.yml now uses the single call; the lock-drift test (12 lines), the helper and its mutation evidence are DELETED; the `.in` header and docs/tests.md say pip stops on a drifting pin | evidence-r3-pip-A.txt (identical pins), -B.txt (conflict), -C.txt (real install, single call, plus today's two-call downgrade), -D.txt (`-c`), -E.txt (pip 26.2.2) |
| 2 | NIT apply order (exceptions.txt line 24) | Line 24 is no longer edited. Two NEW lines are added after line 9 (`^requirements-coverage\.txt:[0-9]+:[0-9a-f]{64}$` and `^[^:]+:[0-9]+:requirements-coverage\.in[^A-Za-z0-9_-]?$`); the dev lock's line 9 is no longer edited either. All orders pass | evidence-r3-apply-orders.txt |
| 3 | NIT stale PLAN.md statements | Re-read the whole file; fixed: v1 venv name, "no Python file is changed" (now true and shown against 558d37f; mypy linux and win32 re-run, 26 files each), hygiene count (19 passed, the v2 count 20 included the deleted test), the `pip --dry-run` claim (removed; the evidence is the real install of evidence-r3-pip-C.txt), file list, rung table, section 2 table, design points, section 8 count | this file; evidence-r3-lint-checks.txt, evidence-r3-hygiene-tests.txt |
| 4 | NIT counts (2349) | Section 1a: what 2349 was, the collected figure, and whether 558d37f changed any Python (it changed only `.gitleaks.toml`, 7 lines; no `.py`). Full suite: ran ONE serial run now: 2349 passed, 116 skipped, 0 failed, 875.10 s, coverage 92.53 percent | evidence-r3-base-diff.txt, evidence-r3-full-run.txt |
| 5 | NIT 'the lane 7 plan' in sonar.yml:12 | Replaced with "an open owner decision (see the pull request description)" | patch, sonar.yml |
| 6 | NIT `ubuntu-latest` floats; `--only-binary` | main's sonar.yml has `ubuntu-latest` only in its header and the `runs-on` line, with no reason given (not deliberate), so it is now `ubuntu-24.04` like lint.yml (header updated). `--only-binary=:all:` added: a real install of both locks with it succeeded (every locked package has a wheel; no source build) | evidence-r3-base-diff.txt, evidence-r3-pip-C.txt |
| 7 | NIT hygiene test details (`_`/`-`, hashes, guards, mutation commands) | Moot: the test and its parser are deleted (finding 1), so there is no parser to normalise and no guard to mutate. The tool that compares is now pip, which normalises names itself and checks hashes | evidence-r3-pip-B.txt |
| 8 | NIT gitleaks path regex shape | Kept as is: `(^|[/\\])requirements-(dev(-win)?|coverage)\.txt$` in `.gitleaks.toml` allows a 64-hex value only inside a file of that name in ANY folder (and the rule still needs the hex shape), while `exceptions.txt` is anchored at the repository root. NOTE for the lead: this also TIGHTENS the dev lock's old entry (it was unanchored: `requirements-dev(-win)?\.txt$` matched `old-requirements-dev.txt`; that file is now reported too) | evidence-r2-gitleaks.txt (4) |
| 9 | NIT UNVERIFIED list incomplete | Section 1 now lists the full suite on 558d37f and the pip single-invocation result | this file |

### Rung table (rule 20, R448) for what v3 adds

| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| coverage measurement | a coverage figure in Sonar | free library: pytest-cov + coverage.py, standard tool; Sonar reads coverage.xml | evidence-r3-pip-C.txt (installs), evidence-coverage.xml (v1 run) | nothing | CUT-TO-CONFIG (a lock file, a workflow step, pyproject settings; no code) |
| detect a drifting pin between the dev lock and the coverage lock | the second lock must not change the dev lock's versions | (1) Dependabot: dependabot.yml lists only Actions here, pip locks are not covered (repo file, 2026-11-12); (2) `uv pip compile -c requirements-dev.txt`: guards when the lock is generated, not when the dev lock is bumped later; (3) **pip itself, one call with both `-r` files: TRIED, WORKS: a conflicting pin stops the install with `ResolutionImpossible`, exit 1; identical pins accepted** | evidence-r3-pip-A/B/C/D/E.txt, 2026-11-12, pip 24.0 and 26.2.2 | nothing | **CUT** (the round-2 test is deleted; the workflow line is the check) |

## 2. What the patch changes (9 files, 2 of them new)

| File | Change |
|---|---|
| `.github/workflows/sonar.yml` | setup-python 3.12; ONE pip call for both locks with `--require-hashes --only-binary=:all:`; test step; `timeout-minutes: 60`; `runs-on: ubuntu-24.04` (was `ubuntu-latest`); header comment; scan step unchanged |
| `requirements-coverage.in` / `.txt` | new: separate hashed lock (section 3) |
| `pyproject.toml` | new `[tool.coverage.run]`: `relative_files = true`, `source = ["."]`, `omit = tests/**, demo_only/**, .venv*/**` |
| `sonar-project.properties` | `sonar.python.coverage.reportPaths=coverage.xml` |
| `.gitignore` | `.coverage.*` and `coverage.xml` (the dev can run it locally; `.coverage` was already ignored) |
| `exceptions.txt`, `.gitleaks.toml` | the new lock's hash lines and the file name `requirements-coverage.in` get the same allowance the dev lock has (without it the hardcoded-literal scan in lint.yml fails: shown in evidence-lint-checks.txt / evidence-gitleaks.txt). In `exceptions.txt` two NEW lines after line 9, no existing line edited |
| `docs/tests.md` | 7 lines: how to install both locks in one call and run the coverage command locally |

No Python file is changed by v3 (`git diff 558d37f -- '*.py'` is empty). The lint locks `requirements-dev.txt` and `requirements-dev-win.txt` are untouched.
Design points required by the order:
- Actions: checkout `3d3c42e5...` v7.0.1 and cache `0057852b...` v4.3.0 and scan `4d1dc0c9...` v8.4.0 are the ones already in
  sonar.yml; setup-python `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` v7.1.0 is copied from lint.yml. No new SHA invented.
- Permissions: top-level `contents: read` and `pull-requests: read`, unchanged. No job-level raise.
- Secret: `SONAR_TOKEN` is set in the env of the scan step only (as before). The pip install step has no environment variable and the test step has only
  `DPLD_REQUIRE_DEMO=1`. `persist-credentials: false` stays. The test step runs repository code (the tests), so
  this is also why the secret is not at job level.
- Triggers unchanged: `push` to main and `pull_request` (no `pull_request_target`; the repo test
  `test_workflows_are_pinned_and_limited` forbids it and passes).
- Fork PRs and Dependabot PRs: the existing job-level `if` skips the WHOLE job for them (no secret on those runs), so on a
  fork PR neither the tests nor the scan run: the check shows "skipped", no coverage is computed. Unchanged behaviour,
  I did not alter that line. (Same-repo PRs and pushes to main run everything.)
- If a test fails the scan step is skipped (GitHub's default), so a red test run sends no coverage to Sonar.
- One job, one checkout, `fetch-depth: 0`.
- The test step sets `DPLD_REQUIRE_DEMO=1` like lint.yml (a missing demo_only folder then stops the run instead of
  silently skipping most tests). It does NOT set `DPLD_REQUIRE_SCAN` and does not install gitleaks: the one gitleaks test
  skips here (lint.yml runs it). That is one of the 116 skips.

## 3. The separate lock

Pattern note: the repository on pr-3-tests has NO Semgrep requirements pair (grep of all branches finds nothing); the only
Semgrep pattern I found is in the other studio repo's ci.yml (`uvx --exclude-newer ... --from semgrep==...`, no lock file).
So I followed the order's description and the dev lock's header style, but generated with uv, as ordered.

Generation command (header of `requirements-coverage.txt`), uv 0.11.32 (`/root/.local/bin/uv`):

    uv pip compile requirements-coverage.in --python-version 3.12 --python-platform x86_64-manylinux_2_28 --generate-hashes --exclude-newer 2026-11-09 -c requirements-dev.txt -o requirements-coverage.txt

- uv 0.11.32: the version installed here; the file's header names the command, and the lock was re-generated twice
  with the same command and `cmp` says identical, also identical to the committed file (evidence-r2-lock-regen.txt).
- `--exclude-newer 2026-11-09`: the date lint.yml uses for its "looked up" pins and the day before the lock was made: nothing
  released after it can enter. Date only (a time such as `T00:00:00Z` contains `00:00:00`, which the repo's hardcoded-literal
  scan flags as an IPv6 address: found and fixed).
- `--python-version 3.12 --python-platform x86_64-manylinux_2_28`: Python 3.12 and Linux x86-64 only (the CI runner);
  not for the Windows lock.
- `-c requirements-dev.txt`: constraint, so every shared package keeps the dev lock's pin: pytest 9.2.0 resolved.
- The lock holds 7 pins, each with hashes: ADDED packages are **coverage 7.17.2** and **pytest-cov 7.1.0** only. The other
  five (pytest 9.2.0, pluggy 1.7.0, iniconfig 2.3.1, packaging 26.3, pygments 2.21.0) are pytest's own dependencies,
  listed because pip's `--require-hashes` needs every dependency pinned in the file; versions are identical to
  requirements-dev.txt (checked), and the job installs both files in ONE pip call, where pip itself refuses any drift (finding 1).
- No `coverage[toml]` extra is needed (Python 3.12 reads TOML itself).
- Local install proof (round 3, evidence-r3-pip-C.txt): throwaway venv outside the tree, python 3.12.3, pip 24.0:
  `pip install --require-hashes --only-binary=:all: -r requirements-dev.txt -r requirements-coverage.txt` succeeded (20 packages, all wheels);
  `pip list` shows pytest 9.2.0, coverage 7.17.2, pytest-cov 7.1.0. (Round 2's separate install logs are in evidence-r2-pip-install.txt.)

## 4. The command, the numbers, the honest limits

Command in the job (serial):

    python -m pytest -q --cov --cov-report=xml:coverage.xml        # env DPLD_REQUIRE_DEMO=1; installed before with
    python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.txt -r requirements-coverage.txt

Difference from the order's text (`--cov=src --cov=tools --cov=scripts --cov=load_tools`): I tested that form first.
With separate `--cov=<folder>` coverage.py names files relative to each folder (`catcher.py`, not `load_tools/catcher.py`),
which would not match `sonar.sources=.`. Bare `--cov` plus `source = ["."]` and `relative_files = true` in pyproject
gives `src/lead_desk/desk.py`. The measured folders are the same: src, tools, scripts, load_tools.

Measured in the v1 run on b29bb1f (evidence-pytest-coverage.txt, evidence-xml-check.txt, evidence-coverage.xml); the round 3 run (section 1a) confirms the totals:
- `1 failed, 2348 passed, 116 skipped in 894.68s (0:14:54)`; the 1 failure is the venv artefact of section 9 (it passes outside the tree).
- coverage.xml exists (260 KB); 35 files, ALL `filename` attributes repo-relative and present on disk: 0 bad.
  By folder: src 22 files, scripts 6, load_tools 4, tools 3. `<sources>` = `.` (plus an empty entry).
- line-rate **0.9257** (6542 of 7067 lines) in that run; 0.9253 (6539) in the round 3 run. Per folder (v1 run, not recomputed): src 94.1 percent, scripts 89.4, load_tools 86.6, tools 83.9.
- Branch coverage is OFF (branch-rate 0). I left it off to keep the change minimal and the run time unchanged; Sonar then
  shows line coverage only. Turning it on later = `branch = true` in `[tool.coverage.run]` (slower, lower number).
- Three tracked scripts are never imported by any test and so are absent from the report: `scripts/check_schema.py` (171
  statements; the lint job runs it directly), `scripts/crash_desk.py` (8), `scripts/n8n_api.py` (48). Sonar counts files it
  analyses that have no coverage entry as not covered: worst case for the project figure is 6539 / (7067 + 227) = 89.7
  percent (6542 / 7294 = 89.7 in the v1 run). Sonar's own line counting may differ a little.
- `demo_only/` is NOT measured: sonar-project.properties excludes it (made-up data and fakes, not scored) and the tests
  reach it only as helpers. `tests/` is omitted (Sonar treats it as test code via `sonar.test.inclusions`). Reason for each
  is in the pyproject comment.
- Browser tests: of the 116 skips, 113 are "No module named 'playwright'" (counted from the -rs lines), 1 is Windows-only,
  1 needs the load-test setting `LEAD_DESK_LOAD_N`, 1 is the gitleaks test. Effect on the number: code that only
  the 113 browser tests reach counts as NOT covered; the portal JavaScript is not Python and is not in this report at all. So
  92.5 percent is the honest figure for "what the Python tests that run in CI reach", not a statement about browser behaviour.
- Subprocess code: many tests start the desk as a separate process. coverage.py's `patch = ["subprocess"]` would measure it; I did
  NOT measure the effect (the v1 numbers for it had no raw evidence and were deleted). Code run only inside such child processes (and
  SIGKILL crash scenes) counts as uncovered where in-process tests do not also reach it.

xdist: not used (no xdist in the lock). The serial command above is what was measured. pytest-cov supports xdist; when the
separate xdist patch adds pytest-xdist to the dev lock, the variant is `python -m pytest -q -n auto --cov --cov-report=xml:coverage.xml`
(needs `relative_files` as already set; this combination was NOT run here).

Time budget: measured tests 14.9 min (one run, shared machine). The Sonar scan time was never measured (no scanner run allowed) and the
"about 21 minutes" whole-job figure in v1 was an estimate. Rule in one sentence: `timeout-minutes` is 60, the same as lint.yml,
until a real run on a hosted runner shows the duration; then set it to 1.6 times the longest observed run.

## 5. Lint-type checks run on the patched tree (round 3: evidence-r3-checks.txt, evidence-r3-lint-checks.txt, evidence-r3-hygiene-tests.txt)

Tree: fresh clone of 558d37f + v3 + `gitleaks-toml-fix-v2.patch`.
- `ruff check .` pass; `ruff format --check .` 127 files formatted; `bandit -ll` exit 0; `mypy --platform linux` and `--platform win32`
  both "Success: no issues found in 26 source files" (v3 changes no Python file, so this confirms the base); `scripts/check_schema.py` ALL PASS.
- Hardcoded-literal scan (the git grep step of lint.yml): 2150 raw hits, 0 left after the patched exceptions.txt; with the ORIGINAL
  exceptions.txt the lock gives about 130 lines (so the two new lines are needed; evidence-lint-checks.txt, v1).
- Gitleaks 8.30.1 (binary /tmp/work/gl/gitleaks): `dir` no leaks, `git` (full history plus a scratch commit) no leaks; the patched config
  was also negative-tested in round 2 (planted values reported, evidence-r2-gitleaks.txt). Without the gitleaks fix patch the public hygiene
  scan fails (section 1 failure 2).
- Hygiene tests (`tests/test_hygiene.py`, `test_no_placeholders.py`, `test_http_guard.py`, `test_demo_folder_guard.py`, with the real gitleaks
  and DPLD_REQUIRE_SCAN=1): **19 passed** (the v2 figure of 20 counted the lock-drift test that v3 deletes; v1's "18 passed, 1 skipped" was
  without the real binary). They include `test_workflows_are_pinned_and_limited` (all actions by full SHA, read-only top-level permissions,
  no `pull_request_target`) applied to the new sonar.yml.
- No hygiene test asserts that a lock file is hashed; I checked it myself: 7 pins in the coverage lock, every one has hashes, no unpinned line,
  and a real `--require-hashes` install accepted it.
- Processes: one pytest at a time; none left running; the gitleaks binary and temp copies are under /tmp/work only.

## 6. Sonar-side settings the lead/owner must do on sonarcloud.io (described, NOT done)

- Analysis method: Automatic Analysis must stay OFF (already in the sonar.yml header); a CI scan with it on stops.
- Quality gate: the default "Sonar way" gate has a condition "Coverage on New Code is less than 80 percent". Once coverage is
  reported this starts to apply to every PR: decide whether to keep 80 percent. Code added by a PR but only reachable by
  browser tests (Playwright skipped in CI) or by child processes will count as uncovered and can fail the gate. Owner
  decision: keep, lower, or exclude paths (`sonar.coverage.exclusions`).
- New-code definition: set to "previous version" or "reference branch (main)" (Project settings, New Code); the first scan of
  main has no baseline, so coverage on new code is shown from the second analysis on.
- The project's Python version setting is already `sonar.python.version=3.12` in the properties file.
- First check after the first run on main: Overall coverage shows a number (about 90 percent expected, 89.7 to 92.5); if it
  shows 0 or no coverage, read the scan log for a path-resolution warning (point 1 of section 1).
- Reminder: the repository secret `SONAR_TOKEN` already exists per sonar.yml; no new secret is added by this patch.

## 7. Files here

`sonar-coverage.patch` (v3), `sonar-coverage-v2.patch`, `sonar-coverage-v1.patch`, this PLAN.md, REVIEW-1.md, REVIEW-2.md.
Round 3 evidence (commands recorded in each file): evidence-r3-pip-A.txt .. -E.txt (pip tests), evidence-r3-apply-orders.txt,
evidence-r3-checks.txt, evidence-r3-lint-checks.txt, evidence-r3-hygiene-tests.txt, evidence-r3-base-diff.txt, evidence-r3-full-run.txt.
Round 2 (still valid where cited): evidence-r2-apply-check, -coverage-omit, -gitleaks, -hygiene-tests (v2 tree), -lint-checks (v2 tree), -ruff-final,
-literal-scan, -lock-regen, -lockdrift-test (for the DELETED test: historical only), -pip-install. Round 1: evidence-pytest-coverage.txt (v1 run on b29bb1f, 2348 + 1 failed + 116 skipped),
evidence-coverage.xml, evidence-xml-check.txt, evidence-uptime-before/-after.txt, evidence-lint-checks.txt, evidence-rerun-failed-test.txt, evidence-gitleaks.txt, evidence-apply-check.txt, evidence-patch-stat.txt (v1 patch).
Rules cited from the preamble: 3 (no secrets), 4 (no spend), 5 (found problems fixed or stated), 6 (honest), 11 (least privilege:
secret only in the scan step, read-only permissions), 13 (EGM review is the lead's step, not done by me), 19 (hygiene), 20 (R448: rung table above; pip tried first).
EGM skipped by me: the lead runs the review. Token use not measured.

## 8. OWNER DECISIONS (described, not built)

**A. Two jobs instead of one (isolation of the secret from test code).** Today (one job, lead's order) the test step and the scan step share
one runner. The secret is not in the test step's environment, but test code can write `$GITHUB_ENV` or `$GITHUB_PATH`, write
`~/.sonar/cache` (restored by the cache step) or plant `sonar-project.properties` / `coverage.xml`. Only a same-repo pull request can do it
(forks and Dependabot are skipped by the job `if`), and such an author can already edit the workflow itself, so there is no new trust boundary.
Alternative: job `test` (no secret) uploads `coverage.xml` with an upload-artifact action; job `scan` has `needs: test`, checks out again,
downloads the artifact and holds `SONAR_TOKEN`. Cost: a second checkout (full history, fetch-depth 0), two more actions to pin by full SHA
(upload-artifact, download-artifact; I invented no SHA), about 1 to 2 minutes more wall time, and the scan job still reads a file the test
job produced (so the artifact is data from repo code; the gain is that `$GITHUB_ENV`/PATH/cache tricks no longer reach the secret step).
Recommendation: keep one job until the owner wants the split; the risk is limited to people who already hold write access.

**B. Scan when tests fail.** GitHub skips the scan step when an earlier step fails, so one flaky test of about 2350 means no Sonar analysis for that push.
Option: `if: ${{ !cancelled() }}` on the cache and scan steps. Care: after a failed test step `coverage.xml` may be missing or partial (pytest-cov
writes it at the end of the session, so a failed run normally still writes it, but a crash or timeout does not), which Sonar would then show as a
coverage drop. Safer variant: add `if: ${{ !cancelled() }}` and make the scan step stop when `coverage.xml` is missing. Decide whether a red-test push should still be analysed.

## 9. Pre-existing test behaviour: a virtual environment inside the tree (not changed)

`tests/test_no_placeholders.py` lines 20-28 build the file list with `git ls-files --cached --others --exclude-standard`: every tracked file plus every
untracked file that .gitignore does not ignore. `.gitignore` line 2 ignores only a folder named exactly `.venv/`. It does not "skip .venv" by itself:
the exclusion is .gitignore's. So any other virtual-environment folder inside the checkout (`.venv-cov`, `.venv-x`, `venv/`) is read file by file and the
test fails on text in the packages (this happened with `.venv-cov` in the v1 run; evidence-pytest-coverage.txt lines 52-53). CI is not affected (no venv in the
checkout), and moving the venv out of the tree makes the test pass (evidence-rerun-failed-test.txt; in rounds 2 and 3 the venv is /tmp/work/venv-cov2, outside the tree).
Fix 1: add `.venv*/` and `venv/` to .gitignore. Cost: two lines, covers pip/uv/IDE venvs by name, but any odd name still fails. Fix 2: skip any directory that
contains `pyvenv.cfg`. Cost: a few lines of test code, works for any name, but touches a test. Recommendation: fix 1 now (cheapest, no test change);
fix 2 only if a venv with another name turns up. The lead decides; neither is in the patch.
