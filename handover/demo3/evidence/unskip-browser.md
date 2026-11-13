# Unskip browser tests (EVIDENCE RUNNER K), 2026-11-13 ~12:00-12:08Z (17:30-17:38 IST)

Failures: none. Skips left: none. Not checked: ruff/mypy/bandit/gitleaks (out of scope); only the 10 browser-using files were run, not the full suite; no timing repeats (one run each).

| side | group (files) | tests passed | failed | skipped | wall |
|---|---|---|---|---|---|
| BASE f3c39cf | pass 1: test_mode_safety 49, test_portal_browser 16, test_portal_lead_pages 31, test_portal_wording_and_masking 17 | 113 | 0 | 0 | 104 s |
| BASE | pass 2: drawer_long_name 6, layout 48, long_values 14, look 12, phone_layout 34, stage_confirm_browser 14 | 128 | 0 | 0 | 207 s |
| STACK (f3c39cf + claims patch) | pass 1 (same files, same counts) | 113 | 0 | 0 | 105 s |
| STACK | pass 2 (same counts) | 128 | 0 | 0 | 206 s |

Notes: the 166 skips were one shared helper (`importorskip` in tests/test_portal_lead_pages.py:113 and siblings) used by many files, so whole files were run; they include some non-browser tests in the same files (total 241 per side, all passed, 0 skipped).
Versions: Playwright 1.63.0, pytest 9.2.0, Python 3.12 (venv /home/user/work/k-venv), Chromium build 1243 (matches; /opt/pw-browsers has chromium-1243, chromium_headless_shell-1243), Node v22.23.4.
Setup: worktrees /home/user/work/k-base, /home/user/work/k-stack (patch applied cleanly); both lock files installed with --require-hashes.
Command (run by /home/user/work/k-run.sh and k-run2.sh): `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers PATH=/opt/node22/bin:$PATH TMPDIR=/home/user/work/k-tmp/<side> timeout 1500 python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt <files>`; both sides ran at the same time. EXIT_CODE=0 on all four runs.
Logs: raw/unskip-browser-base.log, raw/unskip-browser-stack.log (pass 1 then pass 2 appended), progress in raw/progress-K.txt.
