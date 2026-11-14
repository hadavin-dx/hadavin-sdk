# M6 evidence report (facts only)
Head: f3c39cf89ec989f032ea48a23cfd824b88da9c68, worktree /home/user/work/m7-tree. Python 3.13.18. Started 03:26 UTC, done about 03:45 UTC (IST +5:30).

## Failures
None. No failed, skipped or errored test in either run. (-rs -rf printed nothing; "skip" does not occur in either log.)

## Results
| Run | Files | pytest rc | Result | Wall |
|---|---|---|---|---|
| 1 | test_portal_lead_pages, test_portal_browser, test_mode_safety, test_portal_wording_and_masking | 0 | 113 passed, 0 skipped | 97.5 s |
| 2 | test_portal_api, _demo, _drawer_long_name, _layout, _log, _log_poll, _long_values, _look, _mode, _phone_layout, test_stage_confirm_browser | 0 | 533 passed, 0 skipped | 422 s |

Comparison with the 166 earlier playwright skips (113+28+22+3): all four groups now run. Run 1 shows 113 passed (matches the 113 group). The 28, 22 and 3 groups could not be mapped to individual files from the output (not checked per file); run 2 has 0 skips. Total 646 passed, 0 skipped. Default order, run once each, no re-runs needed (no failures).

## Setup
- New venv /home/user/work/priv/browser-venv (from py313-venv python). `pip install --require-hashes -r requirements-dev.txt -r requirements-browser.txt`: rc 0, 9.7 s, through the preset proxy, TLS verification on. playwright 1.63.0 (also greenlet 3.5.6, pyee 13.0.1, pytest 9.2.0). Logs: raw/m6-pip-install.log, raw/m6-pip-list.txt.
- Browser: playwright 1.63.0 expects chromium revision 1243 (browsers.json). /opt/pw-browsers has chromium-1243 and chromium_headless_shell-1243, so the pre-installed one was used with PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers; no download, no `playwright install`.
- Env: TMPDIR=/home/user/work/priv/m7-tmp, --basetemp inside it, -p no:cacheprovider; DPLD_REQUIRE_SCAN and GITLEAKS_BIN unset; AWS/ANTHROPIC/GOOGLE/AZURE variables unset via env -u (none were necessarily set). pytest-playwright is not installed or used (tests call playwright sync API directly, `pw.chromium.launch()`), so no --trace option.
- Raw: raw/m6-run1.log, m6-run1.rc, m6-run2.log, m6-run2.rc, m6-run2-files.txt.

## Clean-tree check
- Before: only `?? handover/` (my own evidence folder, untracked). After: same plus ignored files: `__pycache__` in demo_only, scripts, src/lead_desk, tests (Python bytecode), and the .log files in handover/demo3/evidence/raw (ignored by .gitignore).
- No new tracked or untracked files in the repo tree besides handover/. No screenshots, traces or data folders in the repo.
- Outside the repo: /home/user/work/priv/m7-tmp has bt1, bt2 and 4 `.org.chromium.Chromium.*` temp dirs (chromium leftovers inside TMPDIR). The venv is in priv. Nothing else attributable seen outside TMPDIR (I only listed /tmp top level, not exhaustive).
- Processes: a `ps | grep chrom|pytest` count was 5 lines, including the grep itself; I did not inspect them individually (not checked whether any are stray).

## NOT DONE / NOT CHECKED
| Item | Why | Next step |
|---|---|---|
| Per-group mapping to the 28/22/3 skip counts | skips are now 0, so no per-file comparison was needed | Run `pytest --collect-only -q` per file if a table is wanted |
| Stray process check detail | grep count only | `ps -eo pid,etime,cmd | grep -E 'chrom|pytest'` |
| Flakiness | one run each by order; no re-runs | Re-run run 2 twice if flakiness evidence is wanted |
| Whole-suite (non-portal/browser files) | out of scope | n/a |
| Whether py313 env variables had cloud vars set | not inspected | `env | grep -E '^(AWS|ANTHROPIC)'` |

## WHAT I WOULD DO NEXT (ranked 3)
1. Record that the 166 skips were only a missing browser install: the same tests pass 646/0 with the repo's pinned playwright 1.63.0 and the pre-installed chromium 1243.
2. Make the environment bootstrap use the venv recipe above (requirements-browser.txt, PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers) so CI-in-cloud does not skip.
3. Run run 2 once more alone to check timing flake risk (the 422 s run included timing-sensitive layout/log-poll tests).
