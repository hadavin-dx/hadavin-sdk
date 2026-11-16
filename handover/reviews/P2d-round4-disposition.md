# P2d round 4 disposition (ticket revision 4 to revision 5)

Written 2026-11-05, after lead order 9 (19:40 UTC = 01:10 IST on 2026-11-06; IST = UTC+5:30). I did not record the clock time of writing. Written by the drafting agent. Decisions applied: `handover/reviews/P2d-round4-resolve.md` and lead order 9 (relayed in my brief; it is not in `LEAD-ORDERS.md`). Findings: `P2d-round4-adversarial.md` (ADV-R4-1..12) and `P2d-round4-correctness.md` (COR-R4-1..7). Ticket: `handover/tickets/P2d.md` revision 5. Text only; nothing was run except read-only checks and two read-only probes (the BUDGET-2 text through `_views` and `redact_text`), not saved as evidence.
Status words: applied = done as the resolve says; contested = the resolve contests it and I carried that out; declined = not done. Contested: none. Declined: none.
Every claim that rests on P1 is marked "depends on P1 rev 8" in the ticket; I did not read `P1.md` and did not edit it.

| id | sev | status | where in the ticket | note |
|---|---|---|---|---|
| ADV-R4-1 | Major | applied | Word "view" definition; V27; guarantee cases (1) and (4); statement (8) cases (i) to (iii); VARIANT-1(a), (b), (c); VIEW-2 `_held` case; CHANGELOG sentence | Both adopt clauses of `runmap.py` 519 quoted. VARIANT-1 split: (a) bare redact xfail, (b) `redact_text` ZWSP and full-width plain assertion (status R, UNVERIFIED), (c) Cyrillic copy xfail. |
| ADV-R4-2 | Major | applied (moot by the cut) | P2d-2 Interface; v1.1 row V11 | No `deny_hit` call, so no placement or `PLAIN-REPEAT` question remains. The fallback design stays only in the resolve file |
| ADV-R4-3 | Major | applied (moot by the cut) | Budget and cap round-4 additions (i); P2d-2 cost line | P2d-2 adds one linear clockless scan; "half of REDACT_BUDGET_S" sentence deleted |
| ADV-R4-4 | Major | applied (moot by the cut) | Two-PR table; "Depends on" of P2d-1 and P2d-2; one merge list; plan row; L2, L14, L21 | P2d-2 depends on P1a (not P1b) and P2d-1; no `prepare_needles`, `needle_problem`, `allow_empty`, k, or clock default. Merged with COR-R4-2 |
| ADV-R4-5 | Minor | applied | P2d-2 Interface step (1); rows HIDDEN-1, HIDDEN-2; mutant M-D8 | `has_hidden_channel` once per text on the whole cleaned text. Row placement: P2d-2 (9 rows) |
| ADV-R4-6 | Major | applied | V28; guarantee case (1); ASCII-1 reworded; ASCII-4; Budget (ii); Evidence steps 6 and 7(e) | Corrected: an ASCII text still builds the alias when the map holds a non-ASCII value. N = 1,000 measurement is a MEASUREMENT, not code; v1.1 row V13 if over budget |
| ADV-R4-7 | Minor | applied | V29; row DM-2; Budget (iii); v1.1 row V12 | 257 decomposed names refuse the text, fail closed. The skip is v1.1 V12, not code |
| ADV-R4-8 | Major | applied | Whole P2d-2 block; L19; Class H; v1.1 V11 | `deny_hit` step cut per lead order 9. V11 trigger exactly "before any pilot or any real client data". One plain line that P1's text fold is the only defence is in P2d-2 Interface (5) and statement (8)(iii). Rows NEEDLE-1, K-1, ORDER-1, SHORT-1 and mutants M-D3, M-D5, M-D6, M-D7 deleted |
| ADV-R4-9 | Minor | applied | Alias index (a) key-agreement note; rows MAP-6, MAP-7; mutant N13 | Key is `fold(written slice)`; the miss case returns to a second placeholder (availability only) |
| ADV-R4-10 | Minor | applied | Budget (iv); v1.1 rows V8 (extended), V10 | The unchecked loops are named; the worst case is measured (HOSTILE-1, Evidence step 6) |
| ADV-R4-11 | Nit | applied | BUDGET-2; V26 | Literal `"pw=ab%41 x \\u0041"` in code font, with its precondition. Merged with COR-R4-1 |
| ADV-R4-12 | Nit | applied | ALIGN-2 | Named string `chr(0x1100)+chr(0x1161)`, expected `None`; UNVERIFIED, not run |
| COR-R4-1 | Major | applied | BUDGET-2; V26 | `assert len(_views(text)) == 2` first line; 4 clock reads listed with their lines (484, 496, 509, 509); `InputTooLarge` at read 4; 2 `runmap.redact` calls. Probed now, not evidence |
| COR-R4-2 | Major | applied (moot by the cut) | As ADV-R4-4 | Cross-ticket coupling disappears with the needle scan |
| COR-R4-3 | Minor | applied | "Mutant targets after the edit" | Mutants 18 and 19 and N1 each name the edited statement and the killer. The `promoted_mutants.py` line numbers are the reviewer's; UNVERIFIED by me |
| COR-R4-4 | Minor | applied | MAP-2 | Added as an addition: `_aligned_fold` is a VERIFYING return, `None` case. The phrase "always maps" does not exist in the ticket (grep found none), so there was nothing to replace |
| COR-R4-5 | Minor | applied | Files, helper-copy list; Evidence step 2 `--collect-only` command | Helper names read in the snapshot tests; which helper each moved test uses is UNVERIFIED |
| COR-R4-6 | Nit | applied | Section 2b arithmetic; mutant counts; Done | Every count recomputed and printed per file |
| COR-R4-7 | Nit | applied | Evidence step 6 round-4 additions | CI unit step and separate `perf` step cited by name and by line of `ci.yml` and `pyproject.toml`, re-read now |

## Counts
- Finding ids: 19 (ADV-R4-1..12 = 12; COR-R4-1..7 = 7). Table rows: 19 (one per id).
- Resolve rows: 17 (two rows merge two ids each: "ADV-R4-4 + COR-R4-2" and "ADV-R4-11 + COR-R4-1"). 12 + 7 = 19 ids; 19 - 2 = 17 rows.
- Status: applied 19, contested 0, declined 0. Of the 19 applied, 4 are applied as "moot by the cut" (ADV-R4-2, ADV-R4-3, ADV-R4-4, COR-R4-2).
- New P2d-1 rows: revision 4 had 39 (27 + 5 + 7). Revision 5: `test_redact_fold.py` 27 - 1 (VARIANT-1) + 3 (VARIANT-1(a), (b), (c)) + 1 (ASCII-4) + 2 (MAP-6, MAP-7) = 32; `test_redact_fold_seams.py` 5; `test_redact_fold_budget.py` 7 + 1 (DM-2) = 8. Total 32 + 5 + 8 = 45.
- P2d-2 rows: 11 - 4 (NEEDLE-1, K-1, ORDER-1, SHORT-1) + 2 (HIDDEN-1, HIDDEN-2) = 9. Whole ticket 45 + 9 = 54 (revision 4: 50).
- Mutants: 21 existing + 20 new (N1, N4 to N13 = 11, R1 R2 R3 DM-1 = 4, REG-M REG-M2 = 2, AL-1 AL-2 AL-3 = 3) = 41. P2d-2 mutants 7 - 4 + 1 (M-D8) = 4. Whole ticket 45 (revision 4: 47).
- v1.1 rows: V1..V9 kept, V7 and V8 reworded; new V10, V11, V12, V13 (the resolve's) and V14, V15 (mine). PENDING LEAD: L15 and L16 WITHDRAWN (order 9); L17 and L18 stand; new L19 to L22 (accepted by order 9); D9 rewritten, D11 and D12 added.

## Disagreements and clarifications
1. The resolve says the P2d-2 row count falls by "3 rows of 11 = 8", but its Couplings text also removes SHORT-1. I removed four rows (NEEDLE-1, K-1, ORDER-1, SHORT-1) and added HIDDEN-1 and HIDDEN-2 (ADV-R4-5), giving 9. If the lead meant 8 or 10, say so.
2. V14 (close the 1 to 4 character gap) and V15 (bare `redact()` views) are mine: L22 and VARIANT-1(a) named a hole but the resolve gave no v1.1 row for them.
3. UNASS-1 uses 5 unassigned characters (not 3) so that it passes the tier N limit of 4 per text; this limit comes from the resolve and is UNVERIFIED against P1 rev 8.

## What is not verified
No test, mutant or evidence run was made. Every new row and mutant is a hand argument. UNVERIFIED: how P1a lets callers locate hidden-channel lines (the fail-closed rule is fixed in the ticket instead); whether tag characters count in tier N or tier P; the tier N limit of 4; whether VARIANT-1(b) passes on old code; the ALIGN-2 jamo result; which helper each moved test uses; the `promoted_mutants.py` line numbers; the cost of N = 1,000 texts and of 5,000 stored values. Verified by reading or probing now: the `runmap.py` and `redact.py` cites, the CI and `pyproject.toml` cites, `_views` and `redact_text` behaviour for the BUDGET-2 text (2 views, 4 clock reads, 2 `redact` calls), tag characters being category Cf.
