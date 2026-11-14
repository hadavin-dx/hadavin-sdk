# M3 report: third order run, Python 3.13, seed 987654 (facts only)

## Failures first
- Result: 30 failed, 3684 passed, 169 skipped in 903.24 s. EXIT_CODE=1 (pytest's own rc), wall 904 s.
- All 30 FAILED lines: the gitleaks binary is not installed and DPLD_REQUIRE_SCAN=1 turns the skip into a failure (log has 60 'gitleaks binary not found' lines, 2 per failure: failure body + summary line).
- Compared with M1 (seed 20261114) and M2 (reversed): same counts (30 / 3684 / 169).
- Failed ids (sorted) in evidence/raw/m3-failed.txt vs the 30 ids in evidence/raw/m2-rerun/ids-d1 (file used; also sorted): `diff` printed nothing, IDENTICAL.
- Tests failing in M3 but not among the 30: none. No order-dependent test seen, so no solo reruns were needed (none done).

## Setup
- Worktree /home/user/work/m3-tree, detached at f3c39cf89ec989f032ea48a23cfd824b88da9c68, created from /home/user/work/src.
- Python /home/user/work/py313-venv/bin/python; TMPDIR=/home/user/work/priv/m3-tmp; --basetemp /home/user/work/priv/m3-tmp/bt; -p no:cacheprovider; DPLD_REQUIRE_SCAN=1; PYTHONPATH=/home/user/work/priv/shuffle; `-q -rs -rf -p shuffleorder --shuffle-seed 987654`. AWS_*/ANTHROPIC_* unset in the shell.
- Logs: /tmp/runlogs/m3-run.log, copied to evidence/raw/m3-run.log (EXIT_CODE and wall seconds on the last line).

## Clean-tree check
- git status --porcelain: empty before (checked right after worktree add) and empty after the run.
- `--ignored` shows only __pycache__ directories (demo_only, load_tools, scripts, src/lead_desk, tests), all git-ignored; written by Python imports, not by tests (guess).
- New files outside TMPDIR attributable to me: /tmp/runlogs/m3-run.log, the worktree itself, and evidence/raw/m3-run.log, m3-failed.txt, evidence/m3-report.md. Nothing else seen (I did not scan the whole disk).
- One extra record: git worktree metadata for m3-tree in the /home/user/work/src clone. Not removed.
- Not checked: whether tests wrote anywhere else outside TMPDIR.
