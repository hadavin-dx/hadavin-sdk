# E8 evidence, lane3-fix-6.patch (raw numbers; EVIDENCE RUNNER, no judgement)
Base f3c39cf8, tree /home/user/work/e8-base, patch applied (git apply --check ok, git apply ok), `git add -A`, nothing committed. 4 files, 79 insertions, 6 deletions.

## Failures first
- Full suite: no failure. 3689 passed, 200 skipped in 1222.02s (0:20:22), EXIT_CODE=0, WALL_SECONDS=1223. Skips are playwright missing (143), Windows/root-only, python 3.13-only, LEAD_DESK_LOAD_N measurement run.
- Added lines over 120 characters: 8 of 79 (lengths 428, 684, 658, 1474, 1591, 794, 1471, 907). These are long prose lines in README.md / docs (the surrounding docs already use long lines).
## Numbers
- Fails-before: tests/test_docs_tests_md_lane3.py on base (test file copied in, patch not applied): 6 failed in 0.05s (assertion failures on missing doc text, not import errors). On patched tree: 6 passed in 0.04s.
- Command checks, private ports 18765/18766, made-up data, DB under /home/user/work/priv/e8/tmp2:
  - `PYTHONPATH=src:. python -m demo_only.fakes_server --outbox keyed --port 18766`: started.
  - `PYTHONPATH=src:. python scripts/crash_desk.py`: printed flag path, listened; after `D2` written to flag and `PYTHONPATH=src python scripts/feed.py --source form --index 1` (201 new), desk printed "simulate crash" and exited 137.
  - `PYTHONPATH=src:. python scripts/run_real_check.py --dry-fakes --assume-yes`: rc=0 (35.4s, 8 mails sent).
  - Processes I started: all stopped (pgrep shows none of mine; other agents' b5d-old pytest is not mine).
## Files (evidence/raw/)
e8-fix-6-suite.log, e8-fix-6-failsbefore-base.log, e8-fix-6-failsbefore-patched.log, e8-fix-6-commands.log, progress-E8.txt
Not checked: Windows commands, playwright tests (module absent), `scripts/start_all.sh` path.
