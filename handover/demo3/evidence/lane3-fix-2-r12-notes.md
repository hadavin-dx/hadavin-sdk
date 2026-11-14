# lane3 fix-2 round 12 notes (builder B22)
Final tree (index, never committed): 5d1442599b17e4dfd1006d01ccda0ee6e6adf988. Base: round 11 tree 77fa1c0d; patch is cut on fix-1-r6 tree ad6060db4e74f8dba3464d68d4ef318d8d5332e2.

## FAILED / UNCERTAIN first
- My earlier "full run hangs" claim was NOT proven. My live logs sat inside the git tree and were cut by the coordinator's `git pull --rebase --autostash`; the one stack I took (via gdb) showed a teardown wait and I never re-checked it. With logs outside the tree, four groups of test files (round-robin of all 101 files) all finished: raw/g0..g3.log + .xml: 821+1386+1528+690 = 4425 passed, 171 skipped, rc=0 each. Skips are the chmod-000 and other root-only tests; the non-root run runs them (0 skipped).
- Not one single-process full run: it takes over 10 minutes here (a foreground run was cut at 67% by my own 580 s timeout, rc=124, raw/b22-r12-full-fg.log). Two kinds of earlier partial logs (raw/b22-r12-full.log, -full-fg.log) are incomplete and must be ignored.
- Lint logs from r11 in raw/ were overwritten by same-name r12 logs (lint rc=0 on a clean git ls-files copy at this tree id).
- Not checked: Windows (only simulated by patched winerror tests); Python 3.11/3.12 were checked only in the earlier non-root proof (raw/b22-r12-nonroot.log, tree 0b2031ee), the final non-root run is 3.13 only (raw/b22-r12-nonroot-final.log).
- The mutation log (raw/b22-r12-mutation.log, 18 mutants, 0 survivors) was run on an earlier r12 tree; source files lockfile/live_claude/run_stats/envnum did not change after it (index tree unchanged since the lint run), but I did not rerun it.

## Rows
1 stale n8n test: exact text asserted + root twin. FIXED. 2 docs name the link refusal (settings, limits, contract) + doc-guard test. FIXED.
3 non-root: final run 951 passed, 0 skipped (raw/b22-r12-nonroot-final.log); real chmod-000 tests ran. FIXED.
4 sibling names .tmp/.lock go through envnum.open_without_following_link. FIXED (tests in test_one_key_file_rule_r12.py).
5 autouse lock-handle guard in conftest (weakrefs). FIXED, S2 mutant killed.
6 red run with honest split: raw/b22-r12-fails-before.log. 7 mutants: 18, 0 survivors. 8 exit 4 + link text pinned, loop at path for three builders. 9, 10 docs wording and Windows gap stated. 12, 13 (RawStub empty-connection guard), 14 (POSIX marker), nit 4 FIXED.
11 (dedupe of rows 13/14 test helpers) DEFERRED to the stack docs pass, due 2026-11-14 round end of the stack pass (owner-free; a pure refactor with no behaviour change). 15 DECLINED as in the resolve file (reason there).

## Counts
Changed-file run (951 tests incl. r6-r12, path_walk, n8n, settings, docs claims, load tools, stamp locks) three times in a row on the final tree: 948 passed, 3 skipped (root-only) x3. Non-root: 951 passed.
Patch: lane3-fix-2-r12-on-fix-1-r6.patch plus parts/part01..06 (each under 85 KB); both applied to a fresh archive of tree ad6060db give tree 5d14425...; sha256 in raw/b22-r12-patch-sha256.txt.
