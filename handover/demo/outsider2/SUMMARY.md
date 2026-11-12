# Outsider pass 2 (lane 4): branch pr-3-tests, head bee6fff4a47ffefa34c3470190104a11a0e4cb82
EVIDENCE RUNNER: recorded, not judged. Fresh clone /tmp/work/outsider2. Tool: uv 0.11.32 + CPython 3.12.3. Made-up data only, no spend, no sub-agents. Nothing committed or pushed; repo files untouched (git status clean). All started processes finished.

## Failures and problems (first)
1. docker unusable: `failed to connect to the docker API at unix:///var/run/docker.sock; check if the path is correct and if the daemon is running: dial unix /var/run/docker.sock: connect: no such file or directory` (02-docker-ps.txt). Moved to uv.
2. First full pytest run (12-pytest-full.txt, no -v) ENDED EARLY: output stops at ~87% (about test 2187 of 2465, near tests/test_server_*), no summary line, wrapper recorded `exit 0 elapsed 848s`. Cause not found. Isolated rerun of tests/test_server_main_reaper.py + tests/test_slow_sender.py: 71 passed (14-reaper-slow-v.txt). A second full run with -v completed normally (15). Not reproduced; reason unknown (other lanes ran on the same machine; I did not check).
3. Browser tests: 2 failed on first run, `ModuleNotFoundError: No module named 'PIL'` at tests/test_portal_lead_pages.py:429, in test_the_sidebar_column_is_one_colour_to_the_page_bottom_at_1100[light] and [dark]. Pillow is not in requirements-dev.txt, README or docs. After my guessed `uv pip install pillow` (13.0.0) both passed (19-pillow-rerun.txt).
4. Skips with no gitleaks on PATH: 1 test in tests/test_hygiene.py (message says set DPLD_REQUIRE_SCAN=1 to make it a failure). Not run: gitleaks.
5. Not run: other 5 skip reasons in the full run (see table), a Windows-only test, the load measurement test.

## Guessed steps (not in README/docs)
- `uv venv --python 3.12` and `uv pip install --python .venv/bin/python --require-hashes -r requirements-dev.txt` (task told me to use uv; docs say pip).
- Lint command lines taken from .github/workflows/lint.yml and pyproject.toml comments (docs/tests.md only names ruff, mypy, bandit): `ruff check .`, `ruff format --check .`, `mypy --platform linux`, `mypy --platform win32`, `bandit -ll -r src tools scripts -c pyproject.toml`, `python scripts/check_schema.py`.
- `uv pip install playwright==1.63.0` (docs say `pip install playwright`; the version was my pick, no lock entry). No `playwright install` run; used PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers and /opt/node22/bin on PATH. `--trace off` is a pytest-playwright option; the repo uses the plain playwright API without that plugin, so not applicable.
- `uv pip install pillow` (see item 3).
- All runs used `export PYTHONPATH=src`.

## Results
| Step | Command | Result | Time | File |
|---|---|---|---|---|
| venv | uv venv --python 3.12 | ok | 0.2s | 03 |
| install | uv pip install --require-hashes -r requirements-dev.txt | 18 packages, ok | 3.6s | 04 |
| ruff check | ruff check . | All checks passed | <1s | 05 |
| ruff format | ruff format --check . | 127 files already formatted | <1s | 06 |
| mypy linux | mypy --platform linux | no issues, 26 files | 1s | 07 |
| mypy win32 | mypy --platform win32 | no issues, 26 files | 1s | 08 |
| bandit | bandit -ll -r src tools scripts -c pyproject.toml | "No issues identified" (-ll), exit 0 (Low severity 9 counted below the -ll cut-off); many "Test in comment: ... not a test name" warnings | 1s | 09 |
| schema | python scripts/check_schema.py | RESULT ALL PASS | <1s | 10 |
| hygiene | pytest -q -rs tests/test_hygiene.py | 9 passed, 1 skipped | 4s | 11 |
| full pytest, run 1 | pytest -q -rs | truncated, see item 2 | 848s | 12 |
| full pytest, run 2 (no playwright) | pytest -v -rs --durations=10 | 2349 passed, 116 skipped, 0 failed (2465 collected) | 894.6s | 15, 13 |
| browser (7 files, playwright 1.63.0, system chromium) | pytest -v -rs on test_portal_browser, _lead_pages, _wording_and_masking, test_mode_safety, _portal_layout, _portal_look, test_stage_confirm_browser | 185 passed, 2 failed (PIL), 0 skipped | 225s | 17 |
| browser rerun with pillow | the 2 failed tests | 2 passed | 3.6s | 19 |

Run-2 skips (116 = 1 gitleaks missing + 113 playwright not installed (22 test_mode_safety, 28 test_portal_browser, 60 test_portal_lead_pages, 3 test_portal_wording_and_masking) + 1 load measurement (set LEAD_DESK_LOAD_N) + 1 Windows-only test_stall_eviction). Slowest: test_real_check_dry::test_dry_fakes_run_end_to_end 64s. Load average stayed below 2 on start of every run (uptime checked).

## Diff vs initial-code (git diff --stat origin/initial-code...pr-3-tests, names in 01-diffnames.txt)
199 files changed, 53080 insertions, 0 deletions: all additions. Adds .coderabbit.yaml, .gitattributes, .github (dependabot, codeql.yml, lint.yml), .gitignore, .gitleaks.toml, .sonarcloud.properties, contract.md, demo_only/, docs/ (7 pages), exceptions.txt, patterns.txt, load_tools/, n8n/, scripts/, src/lead_desk/, tests/ (about 70 test files plus portal fixtures), tools/, versions.md, pyproject.toml, requirements-dev(.in/-win).txt. (initial-code held far less; so the whole project is the diff.)

## Comparison vs lane 1 (read at end)
/tmp/demo-wt/handover/demo/outsider/SUMMARY.md was still marked 'in progress' when I read it (branch initial-code, head 43110e7, python3.12 venv + pip). It lists ruff, mypy (linux, win32), bandit, check_schema and hygiene (9 passed, 1 skipped: no gitleaks) as done; no full-pytest result yet. My lint and hygiene results match that list; the full-run comparison cannot be made yet. Lane 1 said 'no guessing needed so far'; I needed 3 guessed installs (playwright, pillow, workflow-file lint commands) only for the browser and lint steps.
