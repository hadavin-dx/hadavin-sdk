# Lane 7b (after review 1): coverage in the SonarQube job, patch v2

Base: public branch pr-3-tests head **558d37f** (the lead's D12 move; v1 was made on b29bb1f and is kept as
`sonar-coverage-v1.patch`; it still applies on 558d37f). `sonar-coverage.patch` (v2) is made with `git diff -U1` and passes
`git apply --check` on a fresh clone of 558d37f (evidence-r2-apply-check.txt). Nothing was committed or pushed to the public repo.

## 1. Failures, open points, UNVERIFIED (read first)

1. **The lead's own gitleaks allowlist in 558d37f does not work** (found by me with the real gitleaks 8.30.1 and, independently,
   by lane 10a): `[[allowlists]]` with `regexTarget = "line"` hands the regex the line WITH the line break before it, so `^...$`
   never matches line 4 of sonar-project.properties; on 558d37f alone `gitleaks dir` still gives 1 finding. Lane 10a's
   `/tmp/demo-wt/handover/demo/gitleaks/gitleaks-toml-fix.patch` (regexTarget "match", exact key) is NOT part of my patch (the lead
   decides). I proved my patch together with it: gitleaks dir 0, gitleaks git 0, 20 hygiene tests passed (evidence-r2-gitleaks.txt,
   evidence-r2-hygiene-tests.txt). Without the fix, tests/test_hygiene.py::test_hygiene_scan_public fails (real binary).
   I did NOT write a separate gitleaks patch (lead's order D12).
2. **Apply order:** coverage patch alone on 558d37f: OK. Fix patch first, then my patch: OK. My patch first, then the fix patch:
   FAILS (the fix patch's 3-line context includes exceptions.txt line 24, which my patch edits). Apply the fix first
   (evidence-r2-apply-check.txt). Final content is the same as far as the two touch different lines.
3. UNVERIFIED (unchanged, no offline fix): (a) that sonar-scanner accepts `coverage.xml` through
   `sonar.python.coverage.reportPaths` (docs.sonarsource.com unreachable here, no scanner run allowed); (b) how Sonar treats the EMPTY
   `<source/>` entry that coverage.py writes next to `.` in `<sources>` (evidence-xml-check.txt: `sources: [None, '.']`);
   (c) the action SHAs belong to the named actions and the lock hashes are real packages (only hash FORMAT and pip's own
   `--require-hashes` acceptance are verified). The first real run on the PR settles (a) and (b): the Sonar page shows a number and the scan log
   says "Imported coverage report" or "Cannot resolve the file path".
4. The timeout is a placeholder: no Sonar scan time was measured and the 21-minute whole-job figure in v1 was an ESTIMATE, not a
   measurement. Only measured: pytest 894.68 s on a shared 4-vCPU machine (v1 run).
5. The numbers (92.57 percent local, 89.7 worst case, 2348 + 1 + 116) come from the v1 run on b29bb1f; v2 changes no Python source,
   only the omit glob spelling (proved equivalent, item 9 below), a workflow comment and timeout, a lock comment, and one new test. I did NOT
   re-run the full suite (15 min; lead's order). Small proofs only: hygiene tests 20 passed (evidence-r2-hygiene-tests.txt).
6. Sonar-side acceptance, quality gate and settings: see section 6 (owner steps, not done).
7. The v1 plan sentence 'the subprocess experiment (103 tests, +5 lines, 114 s vs 49 s)' had no raw evidence: DELETED (not re-run).
   The note stays that code run only in child processes is not measured.

## 1b. What changed after review 1

| # | Finding | What I did | Proof file |
|---|---|---|---|
| 1 | MAJOR gitleaks projectKey | Lead fixed it upstream in 558d37f, but that fix does not work (item 1 above); lane 10a's fix verified together with my patch: dir 0, git 0, hygiene 20 passed. No own gitleaks patch (order D12) | evidence-r2-gitleaks.txt, evidence-r2-hygiene-tests.txt |
| 2 | Token not isolated from test code | Rewrote the sonar.yml header comment to say exactly what is true; two-job split written below as OWNER DECISION A, not built | sonar.yml (patch), section 8 |
| 3 | timeout 35 vs 60 | `timeout-minutes: 60` with the one-sentence rule; 21 min called an estimate | sonar.yml (patch), section 4 |
| 4 | Lock drift | Added `test_coverage_lock_agrees_with_dev_lock` (tiny, 12 lines) + header note in requirements-coverage.in; mutation: bumped dev pytest pin, test FAILS with `[('pytest','9.3.0','9.2.0')]`, passes unmutated | evidence-r2-lockdrift-test.txt |
| 5 | Unanchored path regex | `(^|[/\\])requirements-(dev(-win)?\|coverage)\.txt$`; tested with the real binary: old-requirements-coverage.txt is reported, x/requirements-coverage.txt stays allowed (accepted shape) | evidence-r2-gitleaks.txt (4) |
| 6 | Claims without raw evidence | Saved: mypy linux AND win32, check_schema, ruff, bandit; lock regenerated twice with `cmp` (identical to each other and to the committed lock); pip install log; subprocess claim deleted | evidence-r2-lint-checks.txt, evidence-r2-lock-regen.txt, evidence-r2-pip-install.txt, evidence-r2-ruff-final.txt |
| 7 | .venv-x test failure wording | Described exactly in section 9 with two fixes and a recommendation; test and .gitignore untouched | section 9 |
| 8 | Scan skipped on test failure | Owner decision B in section 8, not built | section 8 |
| 9 | omit glob may not cross `/` | Tested with coverage.py 7.17.2: `tests/*` DOES already omit nested files (the reviewer's belief was wrong); changed to `tests/**`, `demo_only/**`, `.venv*/**` only to match the Sonar globs | evidence-r2-coverage-omit.txt |
| - | Allowances in `regexTarget = "line"` have the line-break defect (order D12 point 3) | My new allowances use `regexTarget = "match"` (the existing style); tested positive (131 hash lines allowed) and negative (planted 40-hex and 64-hex values in other files reported) | evidence-r2-gitleaks.txt |

Rung table for the one new piece of code (rule 20): | component | need | rung tried | evidence | what only our code gives | verdict |
| lock drift check | catch a silently downgraded pytest pin | a tool: Dependabot does not cover pip locks here (dependabot.yml lists only Actions); `uv pip compile -c` guards at generation time, not at a later bump of the dev lock | repo files, dated 2026-11-12 | a CI failure the moment the two locks disagree (a safety property of the test run) | KEEP-CODE (12 lines in the existing hygiene test file, no new file) |

## 2. What the patch changes (10 files, 3 of them new or test)

| File | Change |
|---|---|
| `.github/workflows/sonar.yml` | setup-python 3.12; install dev lock then coverage lock with `--require-hashes`; test step; `timeout-minutes: 60`; scan step unchanged |
| `requirements-coverage.in` / `.txt` | new: separate hashed lock (section 3) |
| `pyproject.toml` | new `[tool.coverage.run]`: `relative_files = true`, `source = ["."]`, `omit = tests/**, demo_only/**, .venv*/**` |
| `sonar-project.properties` | `sonar.python.coverage.reportPaths=coverage.xml` |
| `.gitignore` | `.coverage.*` and `coverage.xml` (the dev can run it locally; `.coverage` was already ignored) |
| `exceptions.txt`, `.gitleaks.toml` | the new lock's hash lines and the file name `requirements-coverage.in` get the same allowance the dev lock has (without it the hardcoded-literal scan in lint.yml fails: shown in evidence-lint-checks.txt / evidence-gitleaks.txt) |
| `tests/test_hygiene.py` | one test: shared pins in the two locks agree |
| `docs/tests.md` | 7 lines: how to run the coverage command locally |

The lint locks `requirements-dev.txt` and `requirements-dev-win.txt` are untouched.

Design points required by the order:
- Actions: checkout `3d3c42e5...` v7.0.1 and cache `0057852b...` v4.3.0 and scan `4d1dc0c9...` v8.4.0 are the ones already in
  sonar.yml; setup-python `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` v7.1.0 is copied from lint.yml. No new SHA invented.
- Permissions: top-level `contents: read` and `pull-requests: read`, unchanged. No job-level raise.
- Secret: `SONAR_TOKEN` is set in the env of the scan step only (as before). The pip install and the test step have only
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
  requirements-dev.txt (checked), so installing on top changes nothing.
- No `coverage[toml]` extra is needed (Python 3.12 reads TOML itself).
- Local install proof: venv `/tmp/work/cov-tree/.venv-cov`, python 3.12.3, `pip install --require-hashes -r requirements-dev.txt`
  then `--require-hashes -r requirements-coverage.txt` both succeeded; `pip install --dry-run` of the lock: all satisfied.

## 4. The command, the numbers, the honest limits

Command in the job (serial):

    python -m pytest -q --cov --cov-report=xml:coverage.xml        # env DPLD_REQUIRE_DEMO=1

Difference from the order's text (`--cov=src --cov=tools --cov=scripts --cov=load_tools`): I tested that form first.
With separate `--cov=<folder>` coverage.py names files relative to each folder (`catcher.py`, not `load_tools/catcher.py`),
which would not match `sonar.sources=.`. Bare `--cov` plus `source = ["."]` and `relative_files = true` in pyproject
gives `src/lead_desk/desk.py`. The measured folders are the same: src, tools, scripts, load_tools.

Measured (evidence-pytest-coverage.txt, evidence-xml-check.txt, evidence-coverage.xml):
- `1 failed, 2348 passed, 116 skipped in 894.68s (0:14:54)`; the 1 failure is the venv artefact in section 1 (passes outside).
- coverage.xml exists (260 KB); 35 files, ALL `filename` attributes repo-relative and present on disk: 0 bad.
  By folder: src 22 files, scripts 6, load_tools 4, tools 3. `<sources>` = `.` (plus an empty entry).
- line-rate **0.9257** (6542 of 7067 lines). Per folder: src 94.1 percent, scripts 89.4, load_tools 86.6, tools 83.9.
- Branch coverage is OFF (branch-rate 0). I left it off to keep the change minimal and the run time unchanged; Sonar then
  shows line coverage only. Turning it on later = `branch = true` in `[tool.coverage.run]` (slower, lower number).
- Three tracked scripts are never imported by any test and so are absent from the report: `scripts/check_schema.py` (171
  statements; the lint job runs it directly), `scripts/crash_desk.py` (8), `scripts/n8n_api.py` (48). Sonar counts files it
  analyses that have no coverage entry as not covered: worst case for the project figure is 6542 / (7067 + 227) = 89.7
  percent. Sonar's own line counting may differ a little.
- `demo_only/` is NOT measured: sonar-project.properties excludes it (made-up data and fakes, not scored) and the tests
  reach it only as helpers. `tests/` is omitted (Sonar treats it as test code via `sonar.test.inclusions`). Reason for each
  is in the pyproject comment.
- Browser tests: of the 116 skips, 113 are "No module named 'playwright'" (counted from the -rs lines), 1 is Windows-only,
  1 needs the load-test setting `LEAD_DESK_LOAD_N`, 1 is the gitleaks test. Effect on the number: code that only
  the 113 browser tests reach counts as NOT covered; the portal JavaScript is not Python and is not in this report at all. So
  92.57 percent is the honest figure for "what the Python tests that run in CI reach", not a statement about browser behaviour.
- Subprocess code: many tests start the desk as a separate process. coverage.py's `patch = ["subprocess"]` would measure it; I did
  NOT measure the effect (the v1 numbers for it had no raw evidence and were deleted). Code run only inside such child processes (and
  SIGKILL crash scenes) counts as uncovered where in-process tests do not also reach it.

xdist: not used (no xdist in the lock). The serial command above is what was measured. pytest-cov supports xdist; when the
separate xdist patch adds pytest-xdist to the dev lock, the variant is `python -m pytest -q -n auto --cov --cov-report=xml:coverage.xml`
(needs `relative_files` as already set; this combination was NOT run here).

Time budget: measured tests 14.9 min (one run, shared machine). The Sonar scan time was never measured (no scanner run allowed) and the
"about 21 minutes" whole-job figure in v1 was an estimate. Rule in one sentence: `timeout-minutes` is 60, the same as lint.yml,
until a real run on a hosted runner shows the duration; then set it to 1.6 times the longest observed run.

## 5. Lint-type checks run on the patched tree (evidence-lint-checks.txt, evidence-rerun-failed-test.txt, evidence-gitleaks.txt)

- `ruff check .` pass; `ruff format --check .` 127 files formatted; bandit -ll exit 0; `mypy --platform linux` success (no
  Python file is changed; mypy win32 not re-run); `scripts/check_schema.py` ALL PASS.
- Hardcoded-literal scan (the git grep step of lint.yml, new files staged first because git grep reads tracked files): 0 lines
  left with the patched exceptions.txt; with the ORIGINAL exceptions.txt the lock gives about 130 lines (so the edit is needed).
- tests/test_hygiene.py incl. `test_workflows_are_pinned_and_limited` (rule applied to the new sonar.yml: all actions by
  full SHA, read-only top-level permissions, no `pull_request_target`), test_no_placeholders, test_http_guard,
  test_demo_folder_guard: 18 passed, 1 skipped (gitleaks absent for that test).
- Gitleaks 8.30.1 (tarball SHA-256 matched lint.yml's value; binary /tmp/work/gl/gitleaks): see section 1 point 1 and evidence-r2-gitleaks.txt: with the lane 10a fix, 0 findings for both `dir` and `git`.
- No hygiene test asserts that a lock file is hashed beyond the above; I checked it myself: 7 pins, every one has hashes,
  no unpinned line, `pip --require-hashes --dry-run` accepts it.
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
- First check after the first run on main: Overall coverage shows a number (about 90 percent expected, 89.7 to 92.6); if it
  shows 0 or no coverage, read the scan log for a path-resolution warning (point 1 of section 1).
- Reminder: the repository secret `SONAR_TOKEN` already exists per sonar.yml; no new secret is added by this patch.

## 7. Files here

sonar-coverage.patch, PLAN.md, evidence-pytest-coverage.txt (raw, 2349 tests), evidence-coverage.xml (the produced report),
evidence-xml-check.txt, evidence-uptime-before.txt / -after.txt, evidence-lint-checks.txt, evidence-rerun-failed-test.txt,
evidence-gitleaks.txt (v1), evidence-apply-check.txt (v1), evidence-patch-stat.txt (v1); round 2: evidence-r2-*.txt (apply-check, coverage-omit, gitleaks, hygiene-tests, lint-checks, ruff-final, literal-scan, lock-regen, lockdrift-test, pip-install); old patch sonar-coverage-v1.patch.
Rules cited from the preamble: 3 (no secrets), 4 (no spend), 5 (found problems fixed or stated), 6 (honest), 11 (least privilege:
secret only in the scan step, read-only permissions), 13 (EGM review is the lead's next step, not done by me), 19 (hygiene).
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

**B. Scan when tests fail.** GitHub skips the scan step when an earlier step fails, so one flaky test of 2349 means no Sonar analysis for that push.
Option: `if: ${{ !cancelled() }}` on the cache and scan steps. Care: after a failed test step `coverage.xml` may be missing or partial (pytest-cov
writes it at the end of the session, so a failed run normally still writes it, but a crash or timeout does not), which Sonar would then show as a
coverage drop. Safer variant: add `if: ${{ !cancelled() }}` and make the scan step stop when `coverage.xml` is missing. Decide whether a red-test push should still be analysed.

## 9. Pre-existing test behaviour: a virtual environment inside the tree (not changed)

`tests/test_no_placeholders.py` lines 20-28 build the file list with `git ls-files --cached --others --exclude-standard`: every tracked file plus every
untracked file that .gitignore does not ignore. `.gitignore` line 2 ignores only a folder named exactly `.venv/`. It does not "skip .venv" by itself:
the exclusion is .gitignore's. So any other virtual-environment folder inside the checkout (`.venv-cov`, `.venv-x`, `venv/`) is read file by file and the
test fails on text in the packages (this happened with `.venv-cov` in the v1 run; evidence-pytest-coverage.txt lines 52-53). CI is not affected (no venv in the
checkout), and moving the venv out of the tree makes the test pass (evidence-rerun-failed-test.txt; in round 2 my venv is /tmp/work/venv-cov2).
Fix 1: add `.venv*/` and `venv/` to .gitignore. Cost: two lines, covers pip/uv/IDE venvs by name, but any odd name still fails. Fix 2: skip any directory that
contains `pyvenv.cfg`. Cost: a few lines of test code, works for any name, but touches a test. Recommendation: fix 1 now (cheapest, no test change);
fix 2 only if a venv with another name turns up. The lead decides; neither is in the patch.
