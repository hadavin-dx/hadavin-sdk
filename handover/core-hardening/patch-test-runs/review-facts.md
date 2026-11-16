# C7 report facts review (egm codebase-details), condensed copy, 2026-11-16
No Blockers. VERIFIED against raw logs: baseline 2 failed 9389 passed 455 skipped (base-pytest.log:255), 241 s wall, 424 MB; ruff check/format exit 0; bandit via uvx exit 0 (base-bandit.log); C-01 full 2 failed 9399 passed; A-01 2 failed 9394; G5 2 failed 9389; targeted C-01 10 passed, A-01 46, G5 14; before-C-01 8 failed 2 passed, before-A-01 6 failed 40 passed; ruff exit 0 on all patched copies; test 1 (vendor word) shown identically on all four copies.
Findings (all Major unless noted):
1 apply --check / apply exit codes "0 / 0" have no log line (A-01-applycheck.log etc. empty or no rc; no log at all for the real apply).
2 "same two tests fail on every patched copy" shown by test name only: in every scratch run test 2 (licences) fails with CalledProcessError git ls-files exit 128 (scratch copy has no .git), so it never reached its assertion; the real assertion (10 items under handover/promotion-inputs) appears only in fresh-clone-b4.log and fresh-clone-branch.log, not on any patched copy. Run test 2 on each patched copy inside a working git repository, or say plainly it was not shown there.
3 "uv run bandit exit 2 Failed to spawn" has no log.
4 bandit and the guard tests not run on patched copies and the report's Not-run list (l.12) does not say so (gate requires bandit -ll).
5 patches-ready/v2 not mentioned: state it was not tested; tie tested patches to files by hash.
6 G5-wording "none shipped" has no log (no before-G5-wording.log; its 14 passed is an existing test file).
Nits: 7 commands not in logs (targeted test file lists); 8 timing wrapper /tmp/c7/run.py not saved; wall 241 s vs pytest 237.88 s not explained; 9 "299 files formatted" should read already formatted; 10 logs were edited after capture (redaction token): say so; 11 checkpoint.md one line, no scratch paths.
