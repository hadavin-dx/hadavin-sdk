# Lane 7 (ORDER D7): coverage in the SonarQube job

Final tree = public branch pr-3-tests head b29bb1f5b1c0b702e37198120d08b080861006fc (ORDER D8 move; the long run was done on
this tree, not on bee6fff4). b29bb1f already holds main's sonar.yml, sonar-project.properties, .codeant and .deepsource.toml
(identical to main). The patch `sonar-coverage.patch` is against b29bb1f; `git apply --check` passes on a fresh copy
(evidence-apply-check.txt). Nothing was committed or pushed.

## 1. Failures, open points, UNVERIFIED (read first)

1. UNVERIFIED: that `sonar-scanner` accepts `coverage.xml` through `sonar.python.coverage.reportPaths`. The documentation
   (docs.sonarsource.com) is not reachable from this machine (proxy answers 403) and no scanner is installed, so I could
   not compare the file against the documented format. What I did check: the file is the standard coverage.py Cobertura XML
   (`<coverage>`, `<packages>`, `<class filename=...>`, `<line number hits>`), and every `filename` is repo-relative and exists
   on disk (evidence-xml-check.txt). My belief (from memory, not from a read page) is that Sonar's Python sensor reads
   exactly this report and resolves `filename` against the project base directory. The first real run on the PR proves it:
   the Sonar project page then shows a coverage number, and the scan log says "Imported coverage report" or, if the paths do
   not match, "Cannot resolve the file path ... of the coverage report".
2. One test failed in my local full run: `test_no_placeholder_text_ships`. Cause: my venv folder `.venv-cov` (the name the
   brief asked for) sits inside the tree and that test only skips a folder named `.venv`; it read the venv's packages. This is
   a local artefact and cannot happen in CI (no venv in the checkout; setup-python installs outside the tree). Proof: with the
   venv moved outside the tree the same test passes (evidence-rerun-failed-test.txt: 18 passed, 1 skipped = gitleaks absent).
   So the full run counts: 2348 passed + 1 failed (venv artefact, re-run passed) = 2349 passed, 116 skipped, as expected.
3. PRE-EXISTING, not caused by this patch, and found only because I ran the real gitleaks 8.30.1 (the lint.yml binary, checksum
   checked) on b29bb1f itself: `gitleaks dir` reports 1 leak, `generic-api-key` on `sonar-project.properties:4`
   (`sonar.projectKey=...`). exceptions.txt (for the git-grep scan) was given an entry for that line in b29bb1f, but
   `.gitleaks.toml` was not, so lint.yml's gitleaks step will fail on this file once it runs on the merged tree. Not fixed here
   (it is outside lane 7 and the lead owns that tree); fix = one allowlist in `.gitleaks.toml` for rule `generic-api-key`,
   path `sonar-project\.properties$`, match `^sonar\.projectKey=` ... (the key is not a secret). evidence-gitleaks.txt.
   With my patch gitleaks reports the same 1 finding and no new one (the lock hash lines and the new file name would give 133
   more with the original `.gitleaks.toml`; the patch adds the allowlist entries).
4. Timing was NOT measured on a quiet machine of the final kind: uptime before the run 19:50:38 load average 0.64 0.51 0.71
   (1/5/15 min); after 20:05:33 load average 2.91 2.05 1.32 (the other lanes started their busy loops during the last
   minutes). Measured: 894.68 s pytest (14 min 55 s), wall 895 s, with coverage on. The unloaded references from the lead
   (lane 1: 886 s, lane 4: 894.6 s, both without Playwright and without coverage) are about the same, so the coverage
   overhead was not visible in this run and the load was mostly light; I make no claim about the runner beyond that.
5. The Sonar-side figure will be lower than my local 92.57 percent: see section 4 (three scripts never imported, about 89.7
   percent worst case for those) and Sonar counts its own line set.
6. No Playwright in this run (113 tests skip: "No module named 'playwright'"); see section 4.

## 2. What the patch changes (9 files)

| File | Change |
|---|---|
| `.github/workflows/sonar.yml` | setup-python 3.12; install dev lock then coverage lock with `--require-hashes`; test step; `timeout-minutes: 35`; scan step unchanged |
| `requirements-coverage.in` / `.txt` | new: separate hashed lock (section 3) |
| `pyproject.toml` | new `[tool.coverage.run]`: `relative_files = true`, `source = ["."]`, `omit = tests, demo_only, .venv*` |
| `sonar-project.properties` | `sonar.python.coverage.reportPaths=coverage.xml` |
| `.gitignore` | `.coverage.*` and `coverage.xml` (the dev can run it locally; `.coverage` was already ignored) |
| `exceptions.txt`, `.gitleaks.toml` | the new lock's hash lines and the file name `requirements-coverage.in` get the same allowance the dev lock has (without it the hardcoded-literal scan in lint.yml fails: shown in evidence-lint-checks.txt / evidence-gitleaks.txt) |
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

- uv 0.11.32: the version installed here; the file's header names the command, and the lock was re-generated twice and
  came out identical (only the header differs).
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
- Subprocess code: many tests start the desk as a separate process. coverage.py's `patch = ["subprocess"]` would measure it;
  I tried it on 2 test files: 103 tests, +5 covered lines (2968 vs 2963) but 114 s instead of 49 s. Not worth it, so it is
  left out; code run only inside such child processes (and SIGKILL crash scenes) counts as uncovered where in-process tests do
  not also reach it.

xdist: not used (no xdist in the lock). The serial command above is what was measured. pytest-cov supports xdist; when the
separate xdist patch adds pytest-xdist to the dev lock, the variant is `python -m pytest -q -n auto --cov --cov-report=xml:coverage.xml`
(needs `relative_files` as already set; this combination was NOT run here).

Time budget: measured tests 14.9 min; expected job = checkout + setup-python + two pip installs (about 1 to 2 min) + tests
(15) + Sonar scan (a few min, not measured: no scanner run allowed) = about 20 to 22 min. `timeout-minutes: 35` is
about 1.6 times that, the rule being: expected whole job plus about 60 percent, never below twice the measured test time
alone minus the ~15 min that the scan and setup need. The old 20 was too short for the tests alone plus setup. A hosted runner
is not under this shared load; if its speed differs by 2x the job still ends inside 35 minutes only up to about 1.6x:
after the first real run set it to about 1.6x of the observed duration (the same advice as the comment in lint.yml).

## 5. Lint-type checks run on the patched tree (evidence-lint-checks.txt, evidence-rerun-failed-test.txt, evidence-gitleaks.txt)

- `ruff check .` pass; `ruff format --check .` 127 files formatted; bandit -ll exit 0; `mypy --platform linux` success (no
  Python file is changed; mypy win32 not re-run); `scripts/check_schema.py` ALL PASS.
- Hardcoded-literal scan (the git grep step of lint.yml, new files staged first because git grep reads tracked files): 0 lines
  left with the patched exceptions.txt; with the ORIGINAL exceptions.txt the lock gives about 130 lines (so the edit is needed).
- tests/test_hygiene.py incl. `test_workflows_are_pinned_and_limited` (rule applied to the new sonar.yml: all actions by
  full SHA, read-only top-level permissions, no `pull_request_target`), test_no_placeholders, test_http_guard,
  test_demo_folder_guard: 18 passed, 1 skipped (gitleaks absent for that test).
- Gitleaks 8.30.1 (downloaded from the release, SHA-256 matched lint.yml's value) on the patched tree: 1 finding, the
  pre-existing one in section 1 point 3; none from the patch.
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
evidence-gitleaks.txt, evidence-apply-check.txt, evidence-patch-stat.txt.
Rules cited from the preamble: 3 (no secrets), 4 (no spend), 5 (found problems fixed or stated), 6 (honest), 11 (least privilege:
secret only in the scan step, read-only permissions), 13 (EGM review is the lead's next step, not done by me), 19 (hygiene).
EGM skipped by me: the lead runs the review. Token use not measured.
