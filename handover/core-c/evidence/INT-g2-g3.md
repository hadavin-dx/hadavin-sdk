# INT-g2-g3 (integration of G2 + G3 with G7), worktree /tmp/core-c-int, branch wip-int-g2g3

## Progress note 1 (after the conflict work, before the batch)
- redact.py (G7 settle + P1d-a _sub_glued + G3 fold scan in find()) imports, ruff check and format clean. settle() calls find(), so the fold scan runs in the second pass.
- 5 redact test files targeted run: 151 passed, 4 xfailed. Batch NOT yet run.
- Already in the snapshot: typography tests (tests/test_redact_g3_port.py), dm_2_257 comment, EMAIL tail fix `(?![A-Za-z])`, tests/test_text_parts_together.py.
