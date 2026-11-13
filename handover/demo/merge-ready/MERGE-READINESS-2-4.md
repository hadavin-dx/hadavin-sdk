# Merge readiness for PRs #2, #3, #4 (checked 2026-11-13, builder M1)

Plain words first. The three pull requests form a stack: #2 is branch `pr-1-code` (into `main`), #3 is `pr-2-demo-folder` (into `pr-1-code`), #4 is `pr-3-tests` (into `pr-2-demo-folder`). The brief calls them "pr-2-demo-folder" and "pr-3-tests"; the GitHub numbers are #3 and #4. Head commits measured: #2 d23cf8f, #3 f31e261, #4 f5fe824 (public, read via `gh api`; no push, no PR change). Everything below ran on fresh clones with the CI gitleaks binary (8.30.1, `/tmp/work/gl/gitleaks`) and the lock-file tools in `/tmp/work/int2-venv` (ruff 0.17.4, mypy 2.4.1, bandit 1.9.4). Raw output: `evidence-m-*.txt` in this folder.

## What failed or is uncertain (read first)

1. Branches #2 and #3 are NOT green alone. On both, `gitleaks dir .` reports 1 finding (generic-api-key at `sonar-project.properties` line 4, the public SonarQube project key) and `gitleaks git .` reports 325 findings (lock-file hash lines and host names in the history). On both, `python -m pytest -q` finds no tests and exits 5, which fails the CI step. Both are fixed only by what #4 brings (Batch 1 allowlist v2, Batch 2a, the `tests/` folder). Consequence: CI on #2 and #3 cannot be green before #4 lands; this is by how the stack was built, not a new defect. I did not see the real CI results (GraphQL is blocked here; `gh pr checks` failed), so "red" is derived from the local commands, not from GitHub.
2. Windows and PowerShell were never run by me. The `requirements-dev-win.txt` install and the PowerShell commands in `docs/tests.md` are unchecked.
3. Browser (Playwright) tests: not run in my checks; they need the browser lock and Node. The only full-suite figure is INT-2b run A: 2988 passed, 6 skipped, 0 failed, 20:22 min on pristine f5fe824, but that run had no `GITLEAKS_BIN`, so 3 gitleaks tests were skipped in it. I ran `tests/test_hygiene.py` with gitleaks separately (below), which covers those.
4. CodeQL, SonarCloud (needs the repository secret `SONAR_TOKEN`; the coverage run is the full suite with `--cov`), CodeRabbit and Semgrep (its own PR) were not run and cannot be run locally here.
5. The runtime stack (speed + 6 CodeAnt patches + hang fix) was not part of these measurements except for the apply checks and the small-file test run in `evidence-m-9`; INT-2b run B had 8 failures with an old `codeant2-desk` patch and run C (fixed patch) was killed by a container restart at 50 percent, so the stack has no complete clean full run in my evidence.

## Checklist: every check CI runs, local command, expected, measured on #4 head f5fe824

Run from a clean clone (no `__pycache__`, no tool caches: gitleaks `dir` reads them, which is why CI runs it first). Paths: `GL=/tmp/work/gl/gitleaks`, venv on PATH.

| # | CI step (lint.yml unless noted) | Local command | Expected | Measured on f5fe824 |
|---|---|---|---|---|
| 1 | gitleaks tree | `$GL dir . --config .gitleaks.toml --redact --no-banner --ignore-gitleaks-allow` | exit 0, "no leaks found" | exit 0 |
| 2 | gitleaks history | `$GL git . --config .gitleaks.toml --redact --no-banner --ignore-gitleaks-allow` | exit 0 | exit 0 |
| 3 | ruff lint | `ruff check .` | All checks passed | passed |
| 4 | ruff format | `ruff format --check .` | all formatted | 135 files already formatted |
| 5 | mypy linux | `mypy --platform linux` | no issues | no issues in 26 source files |
| 6 | mypy win32 | `mypy --platform win32` | no issues | no issues in 26 source files |
| 7 | bandit | `bandit -ll -r src tools scripts -c pyproject.toml` | no medium/high | No issues identified |
| 8 | schema check | `python scripts/check_schema.py` | ends `RESULT ALL PASS` | exit 0, ALL PASS |
| 9 | hardcoded-literal scan | `git grep -n -o -I -E -f patterns.txt -- . \| grep -v -E -f exceptions.txt` | no output | 0 lines |
| 10 | canary guard | `grep -rq "def test_hygiene_scan_public" tests/` | present | present |
| 11 | tests (hygiene file, with the scan) | `GITLEAKS_BIN=$GL DPLD_REQUIRE_SCAN=1 python -m pytest -q tests/test_hygiene.py` | all pass, none skipped | 15 passed, 17 s |
| 12 | tests (everything) | `DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 GITLEAKS_BIN=$GL python -m pytest -q` (about 20 min; run alone, not while another full run is going) | 0 failed | NOT re-run by me; INT-2b run A: 2988 passed, 6 skipped, 0 failed (gitleaks tests skipped in that run) |
| 13 | sonar.yml tests with coverage | `pip install --require-hashes --only-binary=:all: -r requirements-dev.txt -r requirements-coverage.txt`, then `DPLD_REQUIRE_DEMO=1 python -m pytest -q --cov --cov-report=xml:coverage.xml`, then the scan itself | tests pass, `coverage.xml` written | NOT run (same suite as 12 plus coverage; the scan needs `SONAR_TOKEN`) |
| 14 | codeql.yml (python, actions, javascript-typescript) | none local | no new alerts | NOT run |
| 15 | pinned-workflow check | part of `tests/test_hygiene.py::test_workflows_are_pinned_and_limited` | pass | inside row 11 |

Order matters in CI: step 1 and 2 run first, then the dev tools install, so keep step 1 and 2 before step 3 to 7 locally.

## What each branch needs to be green alone (measured: gitleaks, ruff, format, mypy, literal scan, pytest)

| Branch (PR) | gitleaks dir | gitleaks git | ruff / format | mypy linux and win32 | literal scan | tests |
|---|---|---|---|---|---|---|
| pr-1-code d23cf8f (#2, base main) | 1 finding (sonar key, line 4) | 325 findings | pass / 51 files | pass | 0 | no `tests/` folder: pytest exit 5 |
| pr-2-demo-folder f31e261 (#3) | 1 finding (same) | 325 findings | pass / 60 files | pass | 0 | only `tests/portal_fixtures`: pytest exit 5; no `test_hygiene.py` |
| pr-3-tests f5fe824 (#4) | 0 | 0 | pass / 135 files | pass | 0 | hygiene 15 passed; full suite per INT-2b |

To make #2 or #3 green on their own, the gitleaks allowlist (sonar key and lock files, `.gitleaks.toml` from #4) and a `tests/` folder would have to be moved down the stack; I did not build that (the lead merges the stack in order; nothing in this task asked for a split). Merge order that works: #2, #3, #4 with CI on #4 as the first fully green run; or merge #4's content last and accept red CI on #2/#3.

## After merging #2 to #4: the Semgrep PR and the runtime stack

- `merge-ready-hygiene.patch` (this folder) applies with plain `git apply` on f5fe824, after the 8 runtime patches, before or after them, and in both orders with `semgrep/semgrep-on-head.patch` (evidence-m-8). It adds `tests/test_gitleaks_exceptions.py` and one paragraph in `docs/tests.md` (quality-checks section). Overlap with the other patches: none (semgrep edits `docs/tests.md` near line 27, mine is near line 70; `codeant2-tests-hardening` edits `tests/test_hygiene.py`, which my patch does not touch).
- On the combined tree (f5fe824 + 8 runtime patches + semgrep + mine): gitleaks dir and git exit 0, literal scan 0 lines, ruff and format clean, and `test_hygiene.py` + `test_gitleaks_exceptions.py` + `test_gitleaks_semgrep_lock.py` + `test_nosemgrep_form.py` = 106 passed (evidence-m-9). mypy and bandit were not re-run on the combined tree.

## The patch: what it proves

- 26 tests, 7.6 s with gitleaks. The exact sonar key line passes both scans. 14 near-misses (another lowercase project key, last character changed, dash/equals/space/dot suffix, upper-case value, capital first letter, lower-case and upper-case key name, text before the name, look-alike file name, other file name, README) are reported by the literal scan, by gitleaks, or by both (a table in the test file says which). The exact line in a sub-folder is reported by the literal scan only; gitleaks lets it through by its path rule (harmless, same public text).
- Mutants (evidence-m-4): 8 widened versions of the exception (value class, missing end anchor, any file, missing start anchor, any properties path, case-insensitive) in `exceptions.txt` or `.gitleaks.toml`; each is caught by at least one named test (1 to 4 failures each).
- Without gitleaks: 14 tests skip; with `DPLD_REQUIRE_SCAN=1` they fail (evidence-m-7).
- Detector gap (evidence-m-5, raw output): lowercase 40+ characters after a `hadavin-dx_` prefix is not reported by gitleaks 8.30.1 with the repo config; `tools/hygiene.py` reports it. The cause inside gitleaks is unknown (by experiment only); values under 40 characters were not tested.
