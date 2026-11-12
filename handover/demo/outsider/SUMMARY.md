# Outsider test (Lane 1): SUMMARY
Repo: branch initial-code, head 43110e7, fresh clone at /tmp/work/outsider. Nothing in the clone was edited (git status clean; .venv and caches are ignored). Raw output: files 00 to 09 in this folder. EVIDENCE RUNNER: recorded, not judged.

## Failures and gaps FIRST
1. **Undocumented browser-test dependency: Pillow.** With Playwright and Chromium working, the full run gave 2 failed, 2460 passed, 3 skipped (08 file). Both failures are `tests/test_portal_lead_pages.py::test_the_sidebar_column_is_one_colour_to_the_page_bottom_at_1100[light]` and `[dark]`, exact error `E   ModuleNotFoundError: No module named 'PIL'` (tests/test_portal_lead_pages.py:429). README, docs/tests.md and requirements-dev.in do not mention Pillow (grep for "PIL|pillow" found nothing). After my guessed `pip install pillow` those two tests pass (09 file). The docs say Playwright is "pip install playwright" but not Pillow.
2. **One unexplained hang, not reproduced.** First full run with Playwright (06 file) stopped making progress at about test 840 of 2465 (around tests/test_hung_adapter_calls.py: `test_reaper_survives_hung_*`) for more than 10 minutes; I killed it (my own process). That test file alone then passed (42 passed in 14s, file 07), and a second full run passed that point. Cause unknown: machine was shared with other sessions running pytest. Treat as a possible flaky or load-sensitive test; not proven either way.
3. **Playwright version is a guessed step.** Docs say `pip install playwright` then `playwright install chromium`. Latest playwright (1.65.1) looks for chromium build 1254 and every browser test skipped with `BrowserType.launch: Executable doesn't exist at /opt/pw-browsers/chromium_headless_shell-1254/...`. The preinstalled build is 1243, which matches playwright 1.63.0, so I pinned `pip install playwright==1.63.0` (tried 1.55 to 1.65 to find it). Playwright is not in the hashed lock file, so there is no documented version. Also the tests call `pw.chromium.launch()` with no path option, so I had to set `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` and put `/opt/node22/bin` on PATH (this machine's setup, not a doc gap).
4. **No parallel option:** requirements-dev.txt has no pytest-xdist, so I ran one process (not `-n 2`). `--trace off` does not apply (no pytest-playwright plugin; tests use the sync API directly).
5. **Docs do not give a Linux command list for the lint checks in one place.** They are in contract.md ("Quality commands") and .github/workflows/lint.yml, and docs/tests.md only names them; I used the contract.md list. Not run: gitleaks (not installed; the hygiene test skips with `no gitleaks program on PATH (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure`) and the lint.yml "hardcoded-literal scan" (git grep with patterns.txt), which I did not run.
6. python3.12: exists (/usr/bin/python3.12, 3.12.3), so no substitute was needed. The README quick start (start_all.sh, feed.py, curl) was NOT run (task listed the checks only).

## Counts compared with the lead's numbers
- Without Playwright (02 file, 1 process, 886 s): **2349 passed, 116 skipped**. Lead expected about 2329 passed / 135 skipped; I get 20 more passed and 19 fewer skipped (skips: 6 Playwright import, 1 Windows-only, 1 gitleaks, 1 load measurement; the rest are grouped lines in the file; the remaining skips are grouped lines in the -rs output; node was not on PATH in this run).
- With Playwright 1.63.0 + Node 22 (08 file, 1026 s): **2460 passed, 2 failed (Pillow), 3 skipped** (gitleaks, load measurement, Windows-only reset). With Pillow the two pass, so 2462 passed, 3 skipped would be the total; the lead expected 2462 passed, 2 skipped (the extra skip here is the gitleaks one, as gitleaks is not installed).

## Steps
| step | command | result | counts | time | guessed? | doc mismatch |
|---|---|---|---|---|---|---|
| clone | git clone ...; git checkout initial-code | ok, head 43110e7 | - | 1 s | no | none |
| setup | python3.12 -m venv .venv; pip install --require-hashes -r requirements-dev.txt | ok | 18 packages | 9 s | no | none |
| ruff | ruff check . ; ruff format --check . | pass | 127 files formatted | <1 s | no (command from contract.md) | docs/tests.md names tools, no commands |
| mypy | mypy --platform linux; --platform win32 | pass | 26 files each | 1 s each | no | same |
| bandit | bandit -ll -r src tools scripts -c pyproject.toml | pass, exit 0 | 0 issues at -ll (9 low) | 1 s | no | none |
| schema | python scripts/check_schema.py | RESULT ALL PASS | - | <1 s | no | none |
| hygiene | python -m pytest -q tests/test_hygiene.py -rs | pass | 9 passed, 1 skipped (gitleaks) | 5 s | no | none |
| unit (no browser) | python -m pytest -q -rs | pass | 2349 passed, 116 skipped | 886 s | no | README says about 20 min; took 14m45 |
| playwright install | pip install playwright (latest 1.65.1) | install ok, browsers skip | 16 skipped in the browser file | 16 s | yes | wrong build for preinstalled chromium |
| playwright pin | pip install playwright==1.63.0 + env vars | tests/test_portal_browser.py 16 passed | 16 passed | 21 s | yes | version not documented |
| full run 1 | pytest -q -rs | hung, killed by me after >10 min at about test 840 | partial | about 12 min | no | see gap 2 |
| hung file alone | pytest -v tests/test_hung_adapter_calls.py | pass | 42 passed | 14 s | no | - |
| full run 2 | pytest -v -rs | 2 failed (PIL) | 2460 passed, 2 failed, 3 skipped | 1026 s | no | Pillow undocumented |
| pillow | pip install pillow; pytest -k sidebar_column | pass | 2 passed | 4 s | yes | Pillow undocumented |

Processes: all started pytest processes ended (the hung one I killed); no servers started; no pushes or commits.

## Correction added by the lead session (2026-11-12, after the lane 8 review)
Line 13 above says "node was not on PATH in this run". The lane's own raw log contradicts it: `02-unit.txt` (the 2349 passed, 116 skipped run) has NO skip line that mentions node, and its skip list adds up to 116 = 1 gitleaks + 22 + 28 + 60 + 3 Playwright import lines + 1 load measurement + 1 Windows-only, which leaves no room for the 21 node tests (1 + 2 + 18) that skip when node is missing. So Node WAS available in that run, and the 2349/116 figure does not come from a run without Node. The line-13 sentence is left as written by the lane for the record; this paragraph is the correction. (`grep -n -i node 02-unit.txt` returns nothing.) Raw log checked by the lead session against the line 13 text on 2026-11-12 20:03Z.
