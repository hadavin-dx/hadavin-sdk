# M8 evidence report (facts only): flakiness check of the 11 portal/browser files
Head f3c39cf89ec989f032ea48a23cfd824b88da9c68, fresh worktree /home/user/work/m8-tree (clean, no data/ folder). Date 2026-11-14.

## Result
| Run | Order | rc (from pytest `$?`) | Summary line (verbatim) | Wall |
|---|---|---|---|---|
| A | default | 0 | `533 passed in 431.10s (0:07:11)` | 432 s |
| B | shuffled, seed 20261114 | 0 | `533 passed in 439.53s (0:07:19)` | 440 s |

Failures: none in either run (`-rfE` printed no FAILED/ERROR lines). No re-runs were needed. Same 533 count as M6 run 2 (421.98 s).

## Commands (verbatim, run in /home/user/work/m8-tree)
Common: `export TMPDIR=/home/user/work/priv/m8-tmp PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`; files = the 11 in raw/m6-run2-files.txt.
- A: `env -u AWS_ACCESS_KEY_ID -u ANTHROPIC_API_KEY /home/user/work/priv/browser-venv/bin/python -m pytest <11 files> -q -rfE -p no:cacheprovider --basetemp /home/user/work/priv/m8-tmp/bt-A > runA.log 2>&1; rc=$?`
- B: same with `PYTHONPATH=/home/user/work/priv/shuffle` and `-p shuffleorder --shuffle-seed 20261114 --basetemp .../bt-B`.
- DPLD_REQUIRE_SCAN and GITLEAKS_BIN were NOT set, because M6 did not set them (followed M6).

## Clean-tree check
- Before A: `git status --porcelain --ignored` empty; `ls data`: no such folder.
- After A: only ignored `__pycache__` in demo_only, scripts, src/lead_desk, tests; no data/.
- After B: identical to after A; no data/. No tracked or untracked files appeared.

## NOT CHECKED
- The shuffle plugin's note line ("shuffle seed ...") does not appear in the -q output (grep count 0), so I did not see the shuffled order printed. The dot-progress layout is identical, so I cannot prove from the log that the order differed; the plugin source shuffles files and tests when --shuffle-seed is given and the plugin was loaded without error (-p shuffleorder). Next step: run `--collect-only -q` with and without the seed and diff.
- Chromium leftovers in /home/user/work/priv/m8-tmp were not cleaned or inspected individually. At the end, 10 chrom|pytest lines were visible; those I inspected belong to another session (M9 full-suite run in /home/user/work/m9-tree, started ~10 min earlier), not mine. That M9 run overlapped with my run B (and possibly the end of A), so timing was under some shared load (my rule: one heavy job at a time applied only to my own runs).
- Not the whole suite; two runs only, so flake rates below 1 in 2 are not excluded.
