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
