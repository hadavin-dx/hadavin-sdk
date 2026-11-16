# A4 review round 2, docs lens (egm comprehension, agent aef0379efb49d3af9)
Read-only review of snapshot A4r2 (README.md, contract.md, CONTRACT-DELTA.md). Findings (full text was returned inline; summary here):
1 Blocker README 195-196 broken `scripts\reset.ps1` (a `\r` became a line break). FIXED.
2,3 Major README 227: cap counts connections being read, not threads; 408/503 bodies missing; 503 meaning. FIXED (rewritten).
4 Major contract 75: header/body deadlines contradict the old "only draining has a total limit" and the 30 s body timeout. FIXED.
5 Major README 69: 408 after 30 s, "both counted as rejected" (not true for a header-phase 408). FIXED.
6,7 Major contract 90 (wrong timeout named), contract 62 (408 body without receipt_id). FIXED.
8 Major contract: no row for the connection-limit 503; lines 19/81/91 say every 503 carries receipt_id. Rows added, line 19 reworded; lines 81/91 still say receipt_id for the lock-wait 503 (correct for that 503).
9 Major README 68: three meanings of 503 busy. FIXED (sentence); the 4-93/231 figures are from the earlier Windows desk run before A4 (not re-measured here).
10 Major reaper described as start-up only (README 59, contract 21 rules 4 and 5, start-up order line). FIXED from CONTRACT-DELTA text. contract line 53 `_fail_pending` mention: not changed (see OPEN).
11 Major CONTRACT-DELTA.md stale lines 28, 82. FIXED (marked APPLIED in A4).
12,13 README 247 list, "first reply byte" wording. FIXED.
14 Nit test counts stale. FIXED from the A4 full run (590 cases, 583 passed, 7 known-red).
Reader aids added to README "Words used here": Reaper, 503 busy, Door. Not done: HTTP status list in README:24 (H), data-map `mode` note (I), B/E wording items.
OPEN: none for docs except H, I, B, E wording items.
