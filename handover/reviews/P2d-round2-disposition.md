# P2d round 2: disposition of every finding (ticket revision 3)

Written 2026-11-05 about 18:50 UTC (00:20 IST on 2026-11-06; IST = UTC+5:30) by the drafting agent. Applies `P2d-round2-resolve.md`. Ticket: `handover/tickets/P2d.md` revision 3. "Applied" = the ticket text now does what the resolve says; nothing was run to prove it (text only), so every new row and mutant is a hand design until the evidence runner reports. Places are ticket sections: Words, Two PRs, Facts (V1..V21), Fields-1 (P2d-1 template fields, by field name: Interface, Files, Tests, Mutation, Evidence, Done), Fields-2 (P2d-2), Classes (A..G), P5c, L1..L14, Decisions (D1..D8).

| id | sev | status | where in revision 3 | note |
|---|---|---|---|---|
| ADV-R2-1 | major | applied | Fields-1 Interface ("Written spelling in the map and the sweep-only record", items a to e); Facts V17; Tests rows SWEEP-1..5; Mutation SW-1..SW-5; Classes G; L1, L13; P5c item 6 | position (a): written slice in `mapping`, plus the sweep-only record `sweep_spellings`; `_build` and the run cache count both; restore never reads it. Refinement: a dict (folded spelling to placeholder), not a bare set, because the sweep must substitute a placeholder (D2). Run-level carry through `redact_cache["spellings"]` added (L13) |
| ADV-R2-1(b) = COR-R2-C10 | minor | applied | Fields-1 Files (`runmap.py`: `_decoded_masks`), Budget paragraph; Facts V18; Tests row HOSTILE-2; Mutation DM-1 | one deadline check per stored original; HOSTILE-2 is deterministic (fake clock) and the cap-size cost is timed by the evidence runner (Evidence step 6), the number comes from the runner, not the probe |
| ADV-R2-2 = COR-R2-C4 | minor (resolve: major) | applied | Fields-1 Interface (guarantee case 1 "ASCII-only TEXT"; "does not promise" statements 6 and 7); CHANGELOG line; Tests rows ASCII-2, ASCII-3 | the two mixed-text behaviours are stated as behaviour: `bank_near` widening and block withhold from an ASCII start line. ASCII-2 carries a control row |
| ADV-R2-3 = COR-R2-C11 (first half) | minor | applied | Fields-1 Tests (placement of the 32 moved tests; "2b" placement table) | test 17 goes to `test_redact_fold.py`; 15 + 12 + 4 + 1 = 32 |
| ADV-R2-4 = COR-R2-C8 | minor | applied | Words (stage 1 / stage 2, direct pass, bare call); Facts V19; Fields-1 Interface (Budget paragraph, Honest cost); Classes C; L6 | "direct pass" defined once; "budget plus one pass" and "every loop level" removed; true worst case is budget + direct pass + `sweep` and is MEASURED (HOSTILE-1, HOSTILE-2, Evidence step 6). The old word "direct calls" is renamed "bare calls" so the two words do not clash |
| ADV-R2-5 = COR-R2-C3 (L5 part) | minor | applied | Fields-1 Interface (docstring at line 1162 corrected; `RedactionResult.restore` covered); Tests row 14; L5 (trigger: the P5c ticket cites the section) | the false L5 sentence is corrected |
| ADV-R2-6 | minor | applied | Fields-1 Interface item (d) "Registration is deferred"; Tests row REG-1; Mutation REG-M | registration moves into `_mask_in_place` after the look-alike check, with a journal rolled back for a discarded or withheld round |
| ADV-R2-7 = COR-R2-C16 | minor | applied | Fields-1 Mutation plan ("which snippets change"); Facts V20 | 18, 19 and N1 are rewrite-snippet rows with one owner each (no near-duplicate); 5 and 7 re-pointed only (`_RETARGET`); 12 and 20 match the file. Note: the resolve says edit (a) touches the lines of 18, 19 and N1; I agree for 18 (line 1107) and N1/19 (928 to 931) and marked all three |
| ADV-R2-8 | minor | applied | Fields-1 Tests rows ERR-1, SEAM-2 | `cache_clear()` before the patch and in the fixture teardown after it |
| ADV-R2-9 = COR-R2-C7 | minor | applied | Fields-1 Tests ("How old code is built"), Evidence step 2, Done | old tree = P2d-1 head with only P2d-1's own hunks (`redact.py`, `runmap.py`, `defaults.py`) restored from the P2d-1 parent, expected `git diff --stat` shows 3 files; files `P2d-1-step2-*.txt`; Done requires L1, L4, L6 decided and recorded |
| ADV-R2-10 | nit | applied | Fields-1 Interface ("Effect on restore"); row MAP-2; L1 | restore returns the original only for kinds whose grammar allows Unicode; accented e-mail placeholders stay unrestored |
| COR-R2-C1 | major | applied | Fields-1 Tests rows GAP-1, P1B-1, CTRL-1; Facts V16; Words (raw output); Fields-2 Tests | rows decide on the RAW output; each first asserts the helper sees the leak in the input; control row CTRL-1; the P2d-2 fail-before is a HAND argument, said so (UNVERIFIED, not run) |
| COR-R2-C2 | major | applied | Fields-1 Tests rows BUDGET-1 (reworded) and BUDGET-1b; Mutation R2 | spy on `_decoded_masks` with a counter (0 with the check, 1 with R2 applied); hand argument only, not run; R2 may be excluded by name as equivalent only if no spy can fail with it |
| COR-R2-C3 | major | applied | Fields-1 Tests row 14; Facts V21; Mutation N9 and mutant 10 | row 14 edited deliberately to the written slice (L1) plus a companion assertion on `sweep_spellings`. **Count:** by my reading 7 of 10 rows change (1, 2, 3, 6, 7, 8, 9); the reviewer said 8 of 10; UNVERIFIED which, the evidence runner reports per row |
| COR-R2-C4 | major | applied | see ADV-R2-2 | merged duplicate |
| COR-R2-C5 | minor | applied | Fields-1 Tests row BUDGET-2 | relabelled A; the text is ASCII with percent-escapes (two views) because `runmap.time` and `redact_mod.time` are the same module object |
| COR-R2-C6 | minor (narrowed) | applied, narrowed | Fields-1 Tests rows ALIGN-1 (marked: near tautology, not in the unit step) and ALIGN-2; Mutation N12; Classes B | ONE sequence row, a unit test; Class B reworded (the run-time `text == fold(body)` check fails closed to a withhold). N12 added as the mutant for ALIGN-2; whether ALIGN-2 kills it is UNVERIFIED |
| COR-R2-C7 | minor | applied | see ADV-R2-9 | merged duplicate |
| COR-R2-C8 | minor | applied | see ADV-R2-4 | merged duplicate |
| COR-R2-C9 | minor | **contested in part** | Fields-1 Interface items (d) and (e); Tests row MAP-4; Mutation N10, REG-M; L1; D4 | applied: the restructure (`_place` and `_mask_ex` exist at `748849c`; dedupe happens before the written slice is known, so registration is deferred), the rule for `full` and `_PIECE` (stated, UNVERIFIED how it runs), the two-occurrence row. **Contested:** the resolve says "one placeholder, both written slices recorded". A map holds one string per placeholder, so one placeholder would restore one occurrence with the other's spelling (the wrong-value restore this change removes). I use two placeholders, consistent with revision 2's rule "two spellings never share a placeholder". The lead can overrule (L1) |
| COR-R2-C10 | minor | applied | see ADV-R2-1(b) | merged duplicate |
| COR-R2-C11 | minor | applied | Fields-1 Tests ("2b" placement table) | every new row has a file; `perf`-marked tests named (test 13, ALIGN-1, HOSTILE-1; all in `test_redact_fold_budget.py`) |
| COR-R2-C12 | minor (narrowed) | applied, narrowed | Fields-2 Mutation plan | M-D1..M-D4 with provisional killers (TAG-1, UNASS-1, EMOJI-1, NEEDLE-1, GAP-GREP), "final when P1b merges"; P2d-2's k stated provisionally (`P1.md` line 53) |
| COR-R2-C13 | nit | applied | Fields-1 Interface (Honest cost); L6 | real ratios: 0.60 to 2.98 s is 5.0 times; 1.22 to 4.08 s is 3.3 times (margin 1.47); still probe, UNVERIFIED |
| COR-R2-C14 | nit | applied | Facts V8; Words | `defaults.py` comment is lines 45 to 48 (44 is `CUT_MARGIN`, 49 is `REDACT_BUDGET_S`) |
| COR-R2-C15 | nit | applied | Facts V5, V18; Interface (restore effect); row MAP-2 | every `runmap.py` line cite names its head (for example EMAIL grammar 215 at `748849c`, 170 at `ce70eb5`; `storable` 263 and 218) |
| COR-R2-C16 | nit | applied | see ADV-R2-7 | merged duplicate |
| COR-R2-C17 | nit | applied | Fields-2 Depends on; L14; Facts V15 | `has_hidden_channel` is a P1a item (`P1.md` revision 6 line 39); all `P1.md` cites moved to revision 6 line numbers (17, 32, 36, 37, 39, 52, 53, 169) |

## Counts (recomputed from the table above)
- Finding ids: 27 (ADV-R2-1..10 = 10; COR-R2-C1..C17 = 17).
- applied: 26 (2 of them narrowed, as the resolve says: COR-R2-C6 and C12). contested in part: 1 (COR-R2-C9). declined: 0. Unaddressed: 0.
- Rows that merge two reviewers' findings (one decision each, both ids listed): ADV-R2-2 = C4, ADV-R2-4 = C8, ADV-R2-1(b) = C10, ADV-R2-3 = C11 (placement), ADV-R2-7 = C16, ADV-R2-5 (L5 part) = C3, ADV-R2-9 = C7.

## Corrections of my own revision 2 found while applying this resolve
- The `P1.md` cites of revision 2 pointed into revision 5 and were stale; they now use revision 6 line numbers.
- Revision 2's text said P2d-2 "may need `refuse_hidden=False`"; P1 revision 6 bans it under `src/`. Replaced: use the default, pin the false-withhold rate with EMOJI-1.
- Revision 2 called mutants 12 and 20 stale; re-reading shows they match the file; only 5 and 7 differ, and `_RETARGET` handles them.
- Revision 2's evidence step 2 was a no-op tree (P1a touches neither file); replaced by the P2d-1 parent with P2d-1's hunks restored.
- Revision 2 placed 31 of 32 moved tests; test 17 is now placed.
- Revision 2's L4 recommended option (a); P1 revision 6 keeps its weighted rule against it, so L4 now recommends (b) (D8) and says why.

## What is not verified (honest list)
Nothing in revision 3 was run. The hand arguments (GAP-1 and P1B-1 fail-before, BUDGET-1b counter 0 against 1, N12 killed by ALIGN-2, DM-1 killed by HOSTILE-2) are UNVERIFIED. The count "7 of 10 rows of test 14" is my reading, not a run. The measured worst-case time does not exist. See the UNVERIFIED section of the ticket.
