# C7b fix pass 2, evidence angle, round 3 (security path), codebase-details, condensed copy, 2026-11-16
No Blocker. Reviewer recomputed no hash and ran nothing; compared hash strings printed in the builder's logs.
Backed by raw files: 9514 passed 455 skipped rc 0 (log lines 142-143), 9969 collected, exactly 23 g4 ids; test-file sha a27dc6e6... equal in tree and patch; old code 11 failed 12 passed, new 23 passed; patch sha 12e4be6f... matches .sha256, README and log; all patches apply rc 0, no .orig/.rej, 14 modified + 4 new.
## Major
1 Nothing ties the 9514 tree to the patched gate.py at run time: manifest has no gate.py hash; the old-code log says tree p gate.py WITHOUT the fix, so gate.py was reverted and restored between 10:41 and 10:43; the only restoration evidence is "23 passed" at 10:42:45, the full run began 10:43:09. Fix: save sha256 of gate.py in tree p before and after the full run and compare with a clean tree built from the shipped patch.
2 "env -i uv run worked with no network" has no log; runfull.sh does not disable network; envdump is a separate call. Not opened: uvsync-fixdev.log, uvsync-p.log. Fix: show the logs support it or drop "no network"; M-A is closed only for "runs the same as base after a prior sync".
## Nits
Stray "0" line at start of old-code log; manifest has one timestamp; a -v run of only the g4 file on the final tree would show 23 PASSED lines. Not checked: base run log (9391), patch hunks, lookahead correctness, ruff/bandit logs.
