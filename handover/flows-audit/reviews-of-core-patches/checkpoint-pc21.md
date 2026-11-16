# checkpoint pc21 (fixer round 21, README.md + DEAD-MAN-CHECK.md in patch-copies)
Checkpoint 1, 2026-11-16 19:15 UTC = 00:45 IST on 2026-11-17 (sandbox clock; work started 19:12 UTC).
Done: read both files in full; read reader reports r21, r20b, r20c; checked claims against the text. Found that `git show b4cce5b:<path>` works in this checkout (the tree is present), so cites can be read; tick_state columns are TIMESTAMPTZ (0003_approvals_tick.sql:30-35).
Next: edit README (M1, m1-m9) and DEAD-MAN-CHECK (M1-M4, m1-m10), run bash -n on changed blocks, run a fake-stand-in test of the changed job script, then the tool checks, then write fix-patchcopies21.md.
Blockers: none. Contested already: DMC nit (S5 last_run_at is used by the query, lines 70 and 84); DMC m7 PUBLIC part (check 3 a already counts rights that come through PUBLIC).
