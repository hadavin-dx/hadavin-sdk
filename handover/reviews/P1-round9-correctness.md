# P1 round 9: correctness review of tickets/P1.md revision 10 (head 82b477e)

Status: saved by the lead from the re-run reviewer's hand-back (condensed). The first round 9 correctness reviewer ran out of context and produced no findings (register: REPORTED-INCOMPLETE); this is the re-run. Nothing run; items needing a run are UNVERIFIED.
Verdict: no Blocker; 2 Major, 3 Minor, 5 Nit. No arithmetic, `__all__` or cite error in the ticket's own counts.
Lead note on COR-R9-3: the reviewer read a copy of LEAD-ORDERS.md that ended at order 11; order 12 and 13 are now in the file, so the "order 12 absent" half is stale; the inconsistency between "orders 5 to 11" and "5 to 12" inside the ticket stands.

| id | sev | where | problem | fix |
|---|---|---|---|---|
| COR-R9-1 | Major | tickets/P2d.md lines 3, 315, 334, 336 vs P1.md lines 19, 21, 267, 269, 275 | P2d.md says P2d-2 "depends on P1a and P2d-1 (not on P1b)" (and lines 315, 334, 336 repeat it). P1.md, after order 11 (reverses 9(2) in part), puts P2d-2 after P1b: merge order P1m, P1a, P2a, P2d-1, P1b, P2d-2, P4d-a2-i. P2d.md is stale. P4d.md line 17 and P2a.md line 32 match P1.md. | The P2d author rewrites those four lines to "depends on P1b"; P1.md keeps the relay at line 289. |
| COR-R9-2 | Major | P1.md line 318 (also 276(f)) | No mutant exists for "entity step skipped in scan_keyset" (gap 7, a no-cap redaction path); the ticket states it as a gap. Against fix-dont-defer. | Add one P1b mutant "entity step not run in scan_keyset" with the re-pointed row `"&#6"+ZWSP+"5;"` vs `"&#65;"` as killer. Recount: P1b 17, distinct 97, runs 125 + k, at most 156. |
| COR-R9-3 | Minor | P1.md lines 3, 275, 325 vs 312 | Ticket cites order 12 while saying "orders 5 to 11" elsewhere. | Make line 312 and the others agree. |
| COR-R9-4 | Minor | P1.md line 258, limit (9) | Cites PENDING LEAD 34 for the ASCII look-alike relay; PL 34 is the unfoldable stored value. The relay is Couplings item (4), line 289. | Fix the cite. |
| COR-R9-5 | Minor | P1.md line 312 | Still says round-7 resolve has 30 rows; header says 29. | Write 29 (revision 9 said 30, COR-R8-5). |
| COR-R9-6 | Nit | P1.md line 98 | "13 of the 14 ... the 14th is under Not moved": the 14th is test 404 in test_pr50_fix_batch.py, a different file. | Reword. |
| COR-R9-7 | Nit | P1.md line 178 | P1a-new = 31 only if the `_DROP_CATEGORIES`-without-Cn mutant is counted; it is in the import-time paragraph, not a numbered list. | Add it to the "Added in revision 8" list or to "How many". |
| COR-R9-8 | Nit | P1.md line 102 | "scan job at line 104": the job is `security` (line 96); line 104 is its checkout step. | Name the job. |
| COR-R9-9 | Nit | P1.md lines 21, 269, 289 | LOOKALIKE_* constant list: three names at line 21, two at 269 and 289. | Say "P2d-2 owns the list" everywhere. (Draft 5 now has three different names: see coupling.) |
| COR-R9-10 | Nit | P1.md lines 83, 302, 309 | pyproject `extend-select` is line 72 at 748849c; the on-disk worktree has 74 (extra extend-exclude line). | Add the note. |

Recomputed by the reviewer: P1m 21 (3 judge + 13 runner + 5 fix-batch); P1a re-pointed 28; P1a new 31 (12+5+1+5+8); P1b new 16 (6 kept + 4 tag + 2 contract + 4; and 19-7+4); distinct 96; runs 124 + k, at most 155; `__all__` 18 in P1a, +3 in P1b = 21; tier rows 22; tier P 27; tier N 964,312; capacity 32,786; 30+ file:line cites matched the snapshot and worktree; symbols kept/new/absent as stated; R4-A/B, KC-A..D, R6-A..F, TAG-T0..T3 traced by hand and consistent.
Not checked: any run; sha256 values and Unicode counts (only arithmetic on them); evidence file; reviews; Files section, CI golden-step text, v1.1 table, Not-in-v1, Rules and sources; the look-alike design; ce70eb5 itself (not on disk).
