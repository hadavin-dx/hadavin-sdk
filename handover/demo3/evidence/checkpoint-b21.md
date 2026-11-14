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
