# fix-review53: fixes to REVIEW.md after reader reviews r50 to r53 and design review r51 (Z1 part 4A)
Only REVIEW.md was edited in the repository. No patch file, RUNBOOK.md or QUESTIONS.md was touched. Static work: nothing was built or run beyond the two commands at the end. Nothing here is marked done or verified; the reviewers have not seen the result.

## Failures and uncertainty first
1. Line 77 of REVIEW.md changed its sha256 prefix (7f8da2ce to a3ab18f0). Cause: the commit-id removal (constraint 1), the r50 M3 addition and the change from "I" to "the audit" all touch line 77 (plain-summary item 3). This was required, not silent. Line 5 is unchanged (e6db355c); it still uses first person, because it is hash-guarded.
2. Z1 4A design items were applied as a PROPOSAL text. None of it is built or tested; every new refusal phrase below is the audit's own wording (not taken from any reviewer or source file): 'the log is not the one named in the root pin', 'signature does not verify', 'signature keys differ from the log's record', 'next key differs from the root pin', 'minimum revocation counter is below the log's', 'previous file not allowed at a first release', 'start refused: a check failed', 'override counter is more than one above the log's', 'record reset needs the signatures of both keys', 'nonce expired', 'nonce already used' (this one reuses an existing phrase for the old 'override already used'), 'stopped: ...' unchanged.
3. Not fixed in full: r51 m19 (each Z part is a block of 1,000 to 2,000 words; history should move to a changelog). Done: the pointer gloss ('r49 M3', OL-22, Z6 (iv) are explained) and the explicit ordered case list. Not done: moving the history text out of part (4A) into a changelog. Reason: it would shift or break the line positions that other files cite and would risk losing facts; it needs the lead's yes. Next step: lead decides; due AUDIT PROPOSAL 2026-11-18 12:00 UTC (17:30 IST).
4. The count of 16 new tests was counted by listing (aw ax ay az ba bb bc bd be bf bg bh bi bj bk bl), by hand, not by script. The earlier planned 'by-case floor' figure (158) from my notes was dropped; it had no source in the reports and is not in the file.
5. Line 524 and lines 27, 368, 546, 753, 780 keep the word 'I' on purpose: they are quoted answers or the studio head's own sentence.
6. The time in checkpoint-r53.md for the start was not recorded.

## Per item
- r50 (lines 1-132): fixed (commit ids removed, terms and the line-40/41 parenthesis, plain-summary items; see the earlier part of this work; line count before line 77 unchanged).
- r51 (333-407): fixed (earlier part).
- r52 M1 to M7, m8 to m19: fixed in text (patch base commit explained without an id; counting job key named; criterion (8) option (a) is a stop-gap; criterion (7) right exception in release 2; signing program needs no 'does not checkpoint-sign' setting; next key pinned in both root pin and (B); terms table rows added (finding ids, patch ids, row/part/Major item, Z items, OL-n, lists A/B/C, key-set generation, mode A/B, K1b, F2/F3/F7/F8, two headings, the lead/reviewers/heavy lane); size ranges and dependencies aligned).
- r53 M1 to M7, m: fixed (Decision 28 size, OL-n numbering, due and default table 'DUE AND DEFAULT FOR EVERY DECISION' with every time and default labelled AUDIT PROPOSAL or LEAD FILLS, key counts (sixth signing key, seventh with the passkey), reconciliation wording and shallow-clone caveat, grammar leftovers). LEAD FILLS: the sitting times in that table (proposed 2026-11-18 12:00 UTC / 17:30 IST and 2026-11-20 12:00 UTC / 17:30 IST), the name of the verifier person, the number of releases per client per year, the second holder of the counter record.
- Z1 4A (design r51): M1 log checks the (B) signature at append; M2 log identity and genesis hash in the root pin; M3 entry types (release, start, lineage, override, stop, counter-unconfirmed, seed); M4 full record and two signatures for a seed; M5 distinct keys equal to the log's record; M6 ordered cases, checks 4.1 to 4.9, tests name H; M7 phrases for the untested refusals plus a general else; M8 client id check against the start command; M9 record reset signed by both keys and an override cap at L+1; M10 RESET removed from the light profile; M11 one cause one phrase; m12 to m18 applied; m19 partly (item 3 above).
- Fixed separately: line 83 and 425 grammar ('baseline tree').

## Totals, with arithmetic
- Z1 tests: 48 + 16 = 64 (letters (a) to (z) = 26, (aa) to (az) = 26, (ba) to (bl) = 12; 26 + 26 + 12 = 64). Refusals 40 + 13 = 53; starts or continues 8 + 3 = 11; 53 + 11 = 64.
- Z block: 95 + 16 = 111 (chain 64 + 5 + 3 + 2 + 8 + 13 + 3 + 3 + 1 + 2 + 3 + 1 + 1 + 2 = 111).
- Total negative tests: 39 + 111 = 150.
- Counts unchanged: 28 rows, Major 4, Minor 13, Nit 11, PROPOSE FIX 25, DECLINE 3. No row added or removed.

## Commands and output (run from handover/flows-audit/, 2026-11-16 20:10 UTC / 2026-11-17 01:40 IST)
$ python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md
rows 28 ['C-1', ..., 'X-6']
severity {'Nit': 11, 'Minor': 13, 'Major': 4}
decision {'DECLINE': 3, 'PROPOSE FIX': 25}
(exit 0)
$ ruff format --check .
1101 files already formatted
(exit 0)
$ sed -n 5p REVIEW.md | sha256sum  -> e6db355c...
$ sed -n 77p REVIEW.md | sha256sum -> a3ab18f0... (was 7f8da2ce; change explained above)
Lines 75 to 79 are still plain-summary items 1 to 5. No 40-character commit id remains (grep run).
