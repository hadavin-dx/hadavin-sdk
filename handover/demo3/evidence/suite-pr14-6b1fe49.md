# Full suite, PR #14 head 6b1fe49 (evidence runner F, raw output only)

Failures: none. Gaps: Playwright browser tests skipped (module not installed, by instruction); 5+24 gitleaks-dependent tests skipped (no gitleaks program); ruff, mypy, bandit, gitleaks not run (not in this job). One run only, so no flake statistics. Hang: none (the run ended by itself; no test near 10 minutes). The container clock (`date -u`) ran from about 11:08Z to 11:28Z (IST = UTC+5:30: 16:38 to 16:58).

| head | run | passed | failed | skipped | errors | wall time | hang yes/no |
|---|---|---|---|---|---|---|---|
| 6b1fe490795542c2e6916f20d2674fd5dbddd21c | 1 | 3683 | 0 | 200 | 0 | 1155.15 s (0:19:15); script wall 1156 s | no |

Last lines: `3683 passed, 200 skipped in 1155.15s (0:19:15)` then `EXIT_CODE=0 WALL_SECONDS=1156`. 3683 + 200 = 3883 = collected items.

Skip reasons (counts of tests, from `-rs`): 166 playwright not importable; 24 + 5 + 1 no gitleaks program; 1 reset that destroys the reply happens on Windows only; 1 root can read a file with no permissions; 1 `ntpath.isreserved` needs Python 3.13; 1 measurement run (`LEAD_DESK_LOAD_N` not set). Total 200.

Exact command (script /home/user/work/f-run.sh, in /home/user/work/f-final, `. final-venv/bin/activate`):
`TMPDIR=/home/user/work/f-tmp timeout 2400 python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt > /home/user/work/f-logs/suite-6b1fe49.log 2>&1`

Machine facts: Linux 6.18.44, 4 cores, 16 GB RAM, Python 3.12.3. Venv: reused /home/user/work/final-venv because `git diff edadd00..6b1fe49 -- requirements-dev.txt` is empty (0 lines); installed versions/hashes not re-compared. Other agents may have run at the same time (not touched). Worktree /home/user/work/f-final at 6b1fe49. Raw: raw/suite-6b1fe49.log, raw/suite-6b1fe49.partial.log (snapshots taken during the run). Delta tests vs edadd00: 3683 vs 3681 passed (+2 new tests); skipped 200 both.
