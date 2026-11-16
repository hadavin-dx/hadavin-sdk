# P2d round 4 correctness review (egm:egm-codebase-details), ticket rev 4. Condensed by the lead; reviewer read-only, ran nothing. Written from the reviewer's notes after its own context compaction (cites not freshly re-checked). Verdict: not clean; 2 major, 3 minor, 2 nit.
| id | sev | where | problem | fix |
|---|---|---|---|---|
| COR-R4-1 | Major | BUDGET-2 (~162), V26 (~60) | Literal has `%` but no `\u` escape, so only one view; the clock reads cannot reach the shared deadline check (`runmap.py` 496, `_decoded_masks` gated on `views` 498); test may pass or fail for the wrong reason; a mutant removing the shared deadline may survive | Restore the `\u` escape in both literals; state the view count and expected clock reads |
| COR-R4-2 | Major (cross-ticket) | P2d-2 Interface (k = 1, `prepare_needles([])`, `allow_empty`), L15/L16, statement 9 | Relies on P1 details that the P1 r6 resolve (rev 8) changes: `allow_empty` dropped, `needle_problem`, `thread_time` default, tier N limit 4; P2d-2 W(text)/TextTooLong claims depend on P1a textnorm, not in tree | Cite P1 by item name; one list of P1-dependent items; mark each "depends on P1 rev 8" |
| COR-R4-3 | Minor | Mutants 18, 19 | Re-pointed slash-branch mutants: ticket does not name the edited line and killing test (`redact.py` 905-935; `promoted_mutants.py` 1937-1951); count 21+19 = 40 right | Name line and killer per mutant |
| COR-R4-4 | Minor | MAP-2 | `redact.py` 1107 is a verifying return (None on mismatch), "always maps" too strong | Reword; add the None case |
| COR-R4-5 | Minor | Files / moved tests | Helpers from several PR #50 test files not listed for copying | Helper-copy list |
| COR-R4-6 | Nit | Counts | Counts agree (39 = 27+5+7; 11; 32 = 15+12+4+1; 40 = 21+19) | State per-file sums |
| COR-R4-7 | Nit | Evidence | CI split cites missing (ci.yml 88, 94; pyproject 87-89) | Add cites |
Verified: counts, 17 template fields, runmap/redact cites at 748849c, CI. Not checked: anything needing P1a/P1b code, ALIGN-2, every new row and mutant (hand arguments), step-7 evidence files (absent).
