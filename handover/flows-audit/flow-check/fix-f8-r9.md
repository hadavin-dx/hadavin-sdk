# fix-f8-r9: the 4 Majors of reviews/f8-design-r3.md (all four were real; checked against the code first)
Files changed: check_flows.py (disabled external-call node = FAIL), take_check.sh, run_all.sh (new cases), selftest.py (new case), README.md, new take-warns.pin.
M1 no WARN baseline: top block (6) and FINAL print RESULT and WARN count; WARN set pinned in take-warns.pin (22 lines, includes 2 new "patch F-002 UNPROVEN" WARNs that appear because F-002 content check now runs); any change = exit 4; missing pin = exit 4; `--write-warn-pin FILE` writes a new pin; disabled external-call node = FAIL (checker).
M2 run saving: exact all/all/True on every flow except mf-recovery.json; recovery must print the ACCEPTED line, else exit 4.
M3 key check: ABSENT = exit 4; both entry flows have KeyOk -> `--patch-checks F002` is passed. F-008 is NOT passed to --patch-checks (it would turn the exit-4 cases into exit 1); the exact settings check covers it.
M4 patched copy auto-detected by the KeyOk node (15:14 vs 12:11, per file); README documents `TAKE_CHECK_FLOWS=<patched folder> bash take_check.sh`.
Not done (scope, lead Q17): no --baseline/--strict/film-v5 work; nits of the review (README order, ANY_CRASH, exit 127, SQL alias WARNs) untouched.
Old-code proof: old take_check.sh exit 0 on form-odd, sub-nokey, hook-emptyset, f008-only, warn-new (new: 4 each); old checker fails the new selftest case on 5 files.
