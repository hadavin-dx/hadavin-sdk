# fix-review31 (round 31, one fixer; static: grep/sed/python3 -I only; no git, no Postgres run)
Edited only reviews-of-core-patches/REVIEW.md. Counts unchanged: 28 rows, Major 4 / Minor 13 / Nit 11, PROPOSE FIX 25 / DECLINE 3, 33 answers (no new decision added; Decisions 2, 3, 5, 8, 12, 20, 21, 25, 27, 28, 29 and Q1 extended).
## Design review r30
F1 Blocker: fixed (Decision 27 "WHO COMPUTES IT" rewritten: verifier outside the program, registry/lockfile identity, two hashes A and B; lines 34, 407, 408, 423, 434, 435 softened). Hold stays "a promise, not a control".
F2 fixed (407: signer hashes shown bytes, revocation counter, verifier-read clock, key set current+next, key loss procedure as builder task).
F3 fixed as proposal (405: conditions 4-7, schema/grant role split; Postgres behaviour UNVERIFIED).
F4 fixed, one part contested: source confirms writer-supplied tick_state times (postgres.py:470-471) and SQL cannot verify signatures. Reviewer's "grant event_id and created_at": audit_outbox has only event_id and body (0002_audit_chain.sql:19-22), so a database-set created_at column must be added first (264).
F5 fixed (214, 432): confirmed eligibility uses runs.updated_at (postgres.py:523-524) and purge_evidence writes no audit event (tick.py:184-217).
F6 fixed (210, 242): confirmed checkpoint() signs last (seq, hash) without recompute (chain.py:299-309); signed head worded as "saw this head".
F7 fixed (400, 256, 434). F8 fixed (238, 223, 391). F9 fixed (439). Single-dependency alternatives added (407, 405, 290 store spec order). Needs head/lead: none new; all are proposals under existing Decisions 21, 25, 27, 28, 29.
## Reader r30
M1 199 fixed. M2 111 fixed. M3 30 and 71 fixed (three rows, ten Major parts). M4 374 fixed. M5 197 fixed. M6 436 fixed. M7 409 fixed. M8 size stated once on Decision 29 (341, 343, 345, 382, 409, 421). M9 qualifiers "recorded, not re-run this round" at 67, 130, 132, 137, 168, 313, 488, 591, 599 (I could not re-run git apply: static round). M10 contested, not re-rated (rating-rule question): C-3 row, line 42 and Decision 20 option 1/6 now show the reader's argument. M11 fixed (335, 370, 376: 32 of 33 decided by the head, Q1 read by builder). M12 fixed (12, 59, 376). M13 fixed (237 shorter list plus confirm-or-drop list). M14 fixed with new source evidence: gate calls inputs_view at agent_loop.py:726 and :742, so moving execute alone does not remove the map read (385, 433, 326). M15 fixed (2). Minors: 266/268 references and "five parts" of a note fixed (378, 436).
## Citation review r30 (read, folded in)
L30 nine -> three rows / ten Major parts. L125, L148, L150 line numbers: checker's numbers (365-374, 374, 375, 383) recorded as the checker's, NOT re-run by me, first-version tree gone. L127 reflog reworded. CANNOT-CHECK items marked in text (162, 508, 172, 150, 123, 141).
## Raw outputs (last lines)
count_review.py: rows 28; severity {'Nit': 11, 'Minor': 13, 'Major': 4}; decision {'DECLINE': 3, 'PROPOSE FIX': 25}
check_refs.py: PASS 5176 references | check_names.py: PASS 655 rows | check_secrets.py: PASS 0 hits in 2654 files | ruff format --check .: 802 files already formatted
Not checked: any Postgres behaviour, git apply results, whether the 33-answer text elsewhere needs the new "32 of 33" wording (grep of "ALL 33" shows none left).
