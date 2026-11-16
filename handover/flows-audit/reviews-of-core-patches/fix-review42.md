# fix-review42: fixer batch 42 for REVIEW.md (answers review-reader-r36.md and review-design-r37.md), 2026-11-16 18:14 UTC / 23:44 IST start

Only `REVIEW.md` was edited, plus this report. Nothing committed, run against a database or applied. Before-copy: scratchpad `REVIEW.before42.md`. No line was inserted before line 77; lines 5 and 77 are in place. New block Z1-Z17 inserted after the old line 520 (no other file cites REVIEW.md lines above 500; checked by grep).

## NOT done or uncertain (first)
1. Not done: splitting very long table rows (lines of 7000 to 48000 characters remain; the longest are in History). Splitting breaks tables; larger rewrite.
2. Not done: stripping all round tags and moving all superseded text under History; I added only a round-to-review-file table (line 667 area). Which fix log answers rounds 35 and 38 is UNVERIFIED.
3. Not done: renaming T, K, C, I, (A)/(B) labels. I renamed HOLD-1/HOLD-2 (heavy lane H1 kept) and added a label-collision list (line 127).
4. Every Z item is a PROPOSAL by this audit. Nothing is built, no tool fact checked (ssh-keygen touch flag, Postgres catalog rights, object lock all UNVERIFIED). The numbers (3 renewals, dates) are proposals, not decisions.
5. Reviewer claim reader M6 (DEAD-MAN SQL still names audit_reconcile) is OUT OF DATE: `grep -n audit_reconcile patch-copies/DEAD-MAN-CHECK.md` shows `:63` with four names. I corrected the stale REVIEW.md text (lines 202, 209) and did not edit the copy.
6. Item (4) cost-sentence start 'Cost of (c)' is the reviewer's reading; not re-verified item by item.
7. Design M10/M11: I did NOT change the note-closable list; only the studio head may (Decision 1 option 3). Proposal Z11 and OPEN QUESTION 7 added; text of (7) now agrees with the table.
8. Z-block review: no egm reviewer ran on it; the lead runs the next review.

## Per item
- Reader M1 (cost sentence): done, line 611 reworded plus Z7 mapping. M2 (path omissions): done, lines 35 and 41. M3 (A-01 verdict, Decision 2/26/27): done, line 78. M4 (next key / root pin): done, Z17, row 526. M5 (price-only apply): done, line 77 (git apply --check exit 1, with -C1 exit 0, run in a scratch copy). M6: described precisely (note 5). m1 table: done, line 667. m2 pointers: done, lines 667, 669. m3: partial (note 3). m4: done, Z5. m5: done, row 528. m6: done, line 79. m7: done, line 202. m8: done, line 555. Owners: Z16. Terms before defined: line 12.
- Design B1: Z1. M1: Z2, rows 539-540. M2: Z3. M3: Z4. M4: Z5. M5: Z7. M6: Z6. M7: Z8, line 560. M8: Z9. M9: Z10. M10, M11: Z11, line 605. M12: Z13, line 35. M13: Z12, row 285. Single-dependency: line 341 and Z14. Minors: Z15, row 528, line 476. "token ceiling" changed to "token limit" (lines 769, 777 and nowhere else; 0 left).

## Checks run (from handover/flows-audit)
- count_review.py: rows 28; Nit 11, Minor 13, Major 4; PROPOSE FIX 25, DECLINE 3. Unchanged.
- check_refs.py: PASS 5182 references. check_names.py: PASS 655 rows. check_secrets.py: PASS 0 hits in 2790 files. check_counts.py: PASS 52 files / 655 nodes. ruff format --check: 916 files already formatted.
- sha256 prefixes unchanged: A-01.patch 64fdf315, C-01-price-only.patch e7ff677e, C-01.patch ca4982eb.
- Not read this batch: lines 60-271 and 661-712 in full; the reviewers' own source reading.
