# checkpoint B22 (lane3 fix-2 round 9)
Written 2026-11-14T07:05Z (started 06:53Z).
Done: tree b22-tree reproduced (812a97a before changes); tests first (79 failed on the r8 tree, 0 function-absent: raw/b22-fails-before.log); rows 1-18 applied; lint on a clean copy of the index all rc 0 (raw/b22-lint-*.log).
Next: changed test files + hygiene + wall-clock guard alone, mutation, patch cut, notes.
Blockers: none. Not run as root-able: the chmod-000 test skips as root (CORRECTION 07:20Z: when this line was written the monkeypatched twin did NOT exist yet; mutant M14 survived and exposed it; the twin test was added afterwards and now kills M14).

07:20Z final: all steps done; see lane3-fix-2-r9-notes.md. Final tree 151f9eff50eb3a4a523cba11fcf1dd811e448719.

r10 (lead's message after the r9 review): done; final tree 1c973634c77ef0ddb214b4f101a1aa405a8cb8b8; see lane3-fix-2-r10-notes.md.
# checkpoint B22 round 11 started 07:53Z

## round 11 checkpoint 08:05Z
Done: rows 1,4 (stub + fixture), 3 (link kind at env_file_problem), 5,6,7,8,9,11,12 coded; fails-before log saved. Next: other-suite check, lint copy, 3 runs, mutation (b22-mut3.py), patch, notes. Rows 10,13,14,15 listed OPEN-FOR-STACK-DOCS per lead 08:01Z. Rows 16,17 declined/escalated.

## round 11 stop 08:19Z
All gates done, patch cut, notes written; handing back.

## round 12 start 08:27Z
base tree 77fa1c0d

## round 12 checkpoint 08:29Z
Done: rows 1,2,4,5(conftest guard),8,9/10 docs,12,13,14; tests red-before recorded next. Next: non-root run, mutants, lint copy, full run (source changed), patch, notes.

## round 12 checkpoint 08:45Z
Done: all 15 rows coded; lint clean, non-root run 848 passed, mutation 18/18 killed (log), patch cut (tree 0b2031ee). Full run in progress: the new autouse lock-handle guard already shows an ERROR in tests/test_claim_checks_and_crm_mode.py (leaked lock handle); fixing all such tests after the run ends, then re-lint, re-run, re-cut patch.
09:26Z checkpoint: DONE all 15 rows coded, lint clean (tree 5d1442599b17e4dfd1006d01ccda0ee6e6adf988), non-root 848 passed, mutation 18/18 killed (S2 re-checked after weakref change: killed). NEXT: full run (hangs at test_desk_edge_cases::test_burst_same_email under -v, faulthandler_timeout=240 to name it), then recut patch + notes. BLOCKER: full run hangs in a different place each time, investigating.
09:51Z B22 r12 DONE: all rows fixed; 4-group full run 4425 passed/171 skipped rc=0; non-root 951 passed; tree 5d1442599b17e4dfd1006d01ccda0ee6e6adf988; hang claim withdrawn (logs in tree were cut); logs now outside tree.
10:08Z B22 r13 checkpoint: code done for rows 1-3,5,9-12,15 (ledger opener single_name, lock name resolved, run_live_check refusal, db.connect check, read_plain_file, owner check + setting names, fake server BrokenPipe), row 4 SQLite result: SQLite 3.53.1 does not follow a link at -wal/-shm/-journal (dangling: no file made; existing: not written through) -> docs + 2 tests, no refusal; row 17 dedupe done (552 test names identical before/after); tests/test_one_key_file_rule_r13.py written (35 tests). NEXT: docs rows 16, narrow runs, mutants on final tree, full runs (logs outside tree). Blockers: none. Tree id: not yet cut.
10:14Z r13: narrow set green on 3.13 (585) and 3.12 (705); lint+mypy linux/win32 clean on clean copy; next mutants then full runs
