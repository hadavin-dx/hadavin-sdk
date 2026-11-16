# B-P3a2-4b builder notes (round 14, security path)

Branch core/p3a2-4b (from f1ec83a8). Push target: wip/cloud-p3a2-4. EGM review of the result is the lead's step; I ran none.

## Issues
1. Error classifier: a lost session (closed, broken, bad transaction status) is never "a file's own error"; SQLSTATE class 25 handled: 25P03 and 25P04 are session-ending (25P04 PG17 only, UNRUN on a server, visible skip on 16). Mutants V88-V99.
7. pg_roles marker traced and reworded; step-5 message differs for a lost connection; reset killers; K8 fourth form (group owns the schema).
4. Tables are dicts; count test computes the totals (580 cells, 40 empty by logic, 540 built, 32 stop at step 0, 508 reach the data checks, 517 refused, 23 return; 72 hand-made states: 48 refused, 24 return). Carriers C6b, C8, C9, C13 and variant (O) built. V100.
6, 5. Third-role right on a family table with no role argument is refused (test named in the matrix file); X01t/X11/X12 comments reworded.
2. O8 reworded to the real rule (owner of the run schema may not change during the run); strict reading behind ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START (OFF). V101, V102. Question q-p3a2-o8-schema-owner updated in handover/questions-for-lead.md.
3. CHANGELOG paragraph rewritten from the computed numbers; three unstated limits named; PG17 UNRUN.
8. Direction-2 test can now fail (positive and negative stand-in); comment says server-wide objects are not looked at; `has {right}` checker anchored to the whole string literal, with a planted fault only on the short form. V103.

## Fail-before (f1ec83a8, clean detached worktree, only the 4 changed test files copied in, PYTHONPATH to old src)
- verify + verify_pg + rules: 26 failed, 349 passed, 1 skipped (logs-4b/old-a.log). The 2 rules failures are because the old mutant list was not copied in (not a killer).
- matrix: 1103 passed on old code (logs-4b/old-b.log). Reason: Issues 4, 5, 6 change tests and tables, not src; each matrix cell is a control by table (one row per effect/carrier); the killers are the mutants V100 and the count test.

## Mutants
V88-V103: 16 of 16 killed (logs-4b/mut-new.log, mut-new2.log).
