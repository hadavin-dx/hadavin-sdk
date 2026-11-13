# BR results (browser tests) - tree RR/tree-BR, head 464fc4a (local-patched), container clock 12:00-12:08Z
No failures, no skips in the AFTER runs. Nothing was fixed or edited.
| run | command | head sha | passed | failed | skipped | errors | wall | hang |
|---|---|---|---|---|---|---|---|---|
| 1 BEFORE (venv312, no playwright), 10 files | unshare -n + lo_up-q4g.py + venv312 pytest -q -rs <10 files> | 464fc4a | 75 | 0 | 166 | 0 | 109 s | no |
| 2 test_mode_safety | same wrapper, venv-br, PLAYWRIGHT_BROWSERS_PATH=RR/pw-browsers | 464fc4a | 49 | 0 | 0 | 0 | 25.6 s | no |
| 3 test_portal_browser | " | 464fc4a | 16 | 0 | 0 | 0 | 23.4 s | no |
| 4 test_portal_drawer_long_name | " | 464fc4a | 6 | 0 | 0 | 0 | 8.3 s | no |
| 5 test_portal_layout | " | 464fc4a | 48 | 0 | 0 | 0 | 83.7 s | no |
| 6 test_portal_lead_pages | " | 464fc4a | 31 | 0 | 0 | 0 | 43.6 s | no |
| 7 test_portal_long_values | " | 464fc4a | 14 | 0 | 0 | 0 | 18.6 s | no |
| 8 test_portal_look | " | 464fc4a | 12 | 0 | 0 | 0 | 31.5 s | no |
| 9 test_portal_phone_layout | " | 464fc4a | 34 | 0 | 0 | 0 | 40.6 s | no |
| 10 test_portal_wording_and_masking | " | 464fc4a | 17 | 0 | 0 | 0 | 6.4 s | no |
| 11 test_stage_confirm_browser | " | 464fc4a | 14 | 0 | 0 | 0 | 27.9 s | no |
AFTER total: 241 passed, 0 failed, 0 skipped. BEFORE: 75 passed + 166 skipped = 241 (same total). Skip lines before: 22 mode_safety:110, 28 portal_browser:27, 113 portal_lead_pages:113, 1 each wording_and_masking:171/204/257.
## Browser facts
- Installed: playwright 1.63.0 (lock). Pinned browsers.json: chromium 1243 (browserVersion 153.0.8010.12), chromium-headless-shell 1243, ffmpeg 1011. Pre-installed: chromium-1243, chromium_headless_shell-1243, ffmpeg-1011 = SAME revisions as the pin; `chrome --version`: Google Chrome for Testing 153.0.8010.12. So no build mismatch.
- RR/pw-browsers holds 3 symlinks to /opt/pw-browsers (the only cloud-image workaround; `playwright install` not run, download host blocked).
- Chromium launches as root with no arguments (no sandbox error), both plain and under `unshare -n`; setpriv/su not needed. Node v22.23.4 at /opt/node22/bin/node on PATH.
- 10 files found by `grep -l playwright tests/*.py` (list in browser-files.txt). tests/test_portal_mode.py (Node tests, not playwright) was not run.
## Failures: none. Cloud-image-only failures: none.
## Not run: test_portal_mode.py and all other test files; ruff/mypy/bandit/gitleaks; Windows; unpatched tree.
## Commands: python3.12 -m venv RR/venv-br; pip install --require-hashes -r requirements-dev.txt then -r requirements-browser.txt (pip-install.log); browsers.json read; launch.py probes (launch-root-*.log); runs via RR/tmp-BR/runall.sh (index after-index.txt); raw logs run1..run11 in this folder.
Leftover processes of mine: 0. Scratch worktrees made: none (tmp-BR/, tree-BR/.tmp-run remain as scratch folders).
