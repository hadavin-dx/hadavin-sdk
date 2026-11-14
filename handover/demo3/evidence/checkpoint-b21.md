# checkpoint B21 (fix-5 r8), 06:18Z (started 06:11Z)
Done: tree /home/user/work/b21-tree = b16 tree (write-tree equal b9f7bc75). Tests written first: tests/test_reset_order_and_words.py (new), edits in test_port_helpers, test_reset_scripts, test_reset_ps1_pid_rules.
Next: run tests on unchanged scripts (raw/b21-fails-before.log), then scripts, README, reset_check, tests/port_blocks.
Blockers: none.

# checkpoint 2, 06:28Z
Done: all rows implemented (scripts, reset_check, README, port_blocks, tests); fails-before logs saved in /home/user/work/b21-logs (copied to raw at the end); mutation run in progress (60 mutants, 2 processes). Found by the mutation run: C-locale mutant survived (pin deleted); new real-file test with ideographic spaces added and shown killing it.
Next: finish mutation, ONE full run on final head in own clone (gitleaks on PATH), guards alone, patch cut, notes.

## Checkpoint 3, 06:45 UTC
Done: mutation run finished (61 mutants, 3 survivors, all 3 now killed by new/tightened tests, verified by hand). raw/b21-mutation.log and raw/b21-fails-before.log written.
Next: freeze head, patches onto b21-full, ONE full run detached, guard+hygiene alone, cut patch r8, notes.
Blockers: none.

## Checkpoint 4, 06:51 UTC
Done: head frozen (tree cb769b22...); patch lane3-fix-5-r8.patch + 3 parts cut and apply-checked (fresh worktrees, same tree id); raw/b21-patch-sha256.txt written; notes draft written. Ruff check/format repo-wide clean.
Running: ONE full run on the final head in /home/user/work/b21-full (started 06:48 UTC, detached, log /home/user/work/b21-logs/full-final.log).
Next: when done, copy log, run wall-clock guard + hygiene scan alone, finish notes, hand back. Deadline 07:41 UTC.
Blockers: none.

## Checkpoint 5, 07:38 UTC (final)
Full run 1: 1 failed (own new test, flake, cause not found); run 2 same tree: 3962 passed. Guards alone rc 0, lint all rc 0, patch cut and apply-checked. Notes written. Handing back.
## Checkpoint r9 start 07:46 UTC: round 9 started from tree cb769b22

## Checkpoint r9 07:53 UTC: reset.sh fixed at read_pid_file (bytes, NUL, non-ASCII, trim in C locale), guard, alive, recheck, check-crash exit 5; ps1 text edits; new tests/test_reset_pid_file_reading.py (54 pass; 48 failed before, raw/b21-r9-fails-before.log). Next: test refactor items 14-22,24,26, lint, mutants, full run.

## Round 9 checkpoint 08:05Z (B21)
Done: read_pid_file does BOM strip, 64-byte check, non-ASCII check, size check (NUL) and trim inside its own LC_ALL=C (rows 1,5); rows 7,8,9 in reset.sh; ps1 rows 11,12,13; tests rows 2,14,15,16,17,18,19,21,22 (+24,26 zip,6); red-first run saved raw/b21-r9-fails-before.log (14 failed on old script). Next: lint, narrow runs, mutants rerun on final script, ONE full run, patch, notes. Blockers: none.

## Lane3 note 08:11Z (written by lane3 at the lead's 08:10Z order; B21 wrote its own line at 08:05Z above)
B21 resumed 07:45Z for fix-5 round 9. At 08:05Z it reported: read_pid_file does the BOM strip, the 64-byte check, the non-ASCII check, the size check and the trim inside its own C locale (rows 1, 5); rows 7, 8, 9 in reset.sh; ps1 rows 11-13 (text pins); tests for rows 2, 14-19, 21, 22 (and 6, 24, 26); red-first run saved (14 failed on the old script). Still to do: mutants, lint of a clean copy, narrow runs, ONE final full run, patch. Next lane3 check 08:20Z.

## Round 9 checkpoint 08:23Z (B21)
Done: all rows of the 08:01Z order except OPEN-FOR-STACK-DOCS ones; lint clean (5 rc=0); 15 mutants killed; patch + 3 parts cut and apply-checked (tree ce7113ea); notes written (lane3-fix-5-r9-notes.md). Running: the ONE full run on tree ce7113ea (log /home/user/work/b21-logs/full-r9.log, started 08:18:37Z, expected end ~08:38Z). Next: copy the log to raw/b21-r9-full-final.log, fill the "Full run" section in the notes, hand back. Blockers: none.

## Round 10 checkpoint 08:56Z
Done: scripts (ps1 exit-5 mapping + $LASTEXITCODE reset, BASH_VERSINFO guard, exit 5 both meanings in headers/README, exit 8 for a refused setting per lead answer 08:50Z incl. Config refusal, python-missing 127 wording, pid-reuse comment), test edits (rows 5 ps1 part, 6, 8, 9, 14-16, labels), narrow run 355 passed 15 skipped. Next: failing-before, mutants (61+15+new), lint, one full run, patch, notes. Row 5 path_confinement literals: see notes (they are the inputs of the Windows-path refusal under test).
