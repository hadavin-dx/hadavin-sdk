# B-PR89 r27 PR notes (builder r27)
Head: cc1f6228 (code at 6690bb5f + evidence commit). Ref: wip/cloud-PR89-r27 (pushed plain, new ref). Local branch wip/cloud-PR89-r27-local, worktree /home/user/build/B-PR89-r27.

Failures and unchecked first: see handover/evidence/PR89/r27/RESULTS.md (mypy figure is now 14 not 13; Windows/macOS/3.12 pytest/perf/semgrep etc. not run; the _narrowable owner condition has no mutant of its own; builder evidence is not independent).

Per issue: 1 killer reordered (spy first, OSError -> AssertionError with fragment, comment 0500); proven: round-26 code as nobody = WRONG_REASON PermissionError, r27 as nobody and as root = 329 of 329. 2 CHANGELOG item 4 + header + prose for "a link out of the tree is accepted". 3 seven re-pointed... listed. 4 O_NONBLOCK, _narrowable before chmod, FIFO thread test, docstring. 5 pin counts, wording, missed spellings. 6 always-run docstring test + file facts test (skipped in mutant copies), CHANGELOG wording, mypy 14 re-measured. 7 all decorators read; third hand list (2 names) + derived check. 8 wording. 9 wording. 10 FAILBEFORE-TABLE.md.
Note on Issue 3: the report's list of seven is the 7 NEW mutants added in round 26 (not "5 re-pointed"); CHANGELOG now lists all seven new ones and says the re-pointed ones are in the header.
