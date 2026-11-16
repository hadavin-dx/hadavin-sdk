# Fix report, round 39 (REVIEW.md only; nothing committed)

## Failures and uncertainty first
- NOT FULLY DONE, said plainly. Only a part of the two review lists was fixed. Not done: (a) splitting long table rows; (b) moving all superseded text under History; (c) stripping every round tag (about 59 lines still hold "round 3x"; only two live tags were removed); (d) stating Decision 29's size once with the others pointing to it, wave definition before first use, the circular wave-1 dependency, receiver vs freezer, owner of Decisions 20/23a/24, who decides the rewrite, sixth part mandatory, the approver-proof criterion test, the criterion (9) producer; (e) renaming other uses of "ceiling" (27 mentions remain). These need a further fixer pass; I did not check each reviewer claim one by one for these items.
- The new key table, the criterion (9) login counts (12 / 16 / 18) and the three DEAD-MAN sentences are proposals by this audit. The counts come from my reading of the login table and were not recounted by a script.
- Due times in the open questions are proposed (2026-11-18 12:00 UTC, 17:30 IST), not agreed.
- Contested: reviewer minor "Decision 19 asked before 18": the Decision 18 table row says "decide after Q1, and 19", so the order is consistent. The 733 vs 738 mismatch is two different texts (short row vs full working text); not merged.

## Finding-to-result table
| finding | result |
|---|---|
| design B1 (signer of (B) named four ways; next key vs counter) | FIXED on paper: KEY TABLE block before Decision 28, root pin outside (B), release key signs (B), current/next defined, minimum counter rule, separation tests; (B), login, ceiling meanings stated |
| design: hash binding of security inputs | stated plainly that host, database settings and secrets are not covered |
| design: criterion (9) vs login lists | rule added (derived from login table lists A and B), counts to be recounted |
| design: counting-run authenticity, drain writer column, expiry time source | named as open questions with due time; not decided |
| design: approver-proof criterion test, criterion (9) producer | NOT DONE |
| reader: apply-check / ancestry / 964 wording | FIXED (985 commits not in b4cce5b, b4cce5b not an ancestor, shallow clone, 2026-11-16 17:26 UTC at `17c4e4d50`) |
| reader: DEAD-MAN edit list with vanished line numbers | FIXED: single source is `patch-copies/DEAD-MAN-CHECK.md`; status table; three open sentences in full |
| reader: round tags | PARTLY (2 removed, ~59 lines left) |
| reader: other contradictions, long rows, History move | NOT DONE (see above) |

## Facts re-checked 2026-11-16 17:26 UTC (22:56 IST)
b4cce5b exists, not an ancestor of HEAD `17c4e4d50` (exit 1), shallow clone, 985 commits; `/tmp/ch`, `/tmp/core-b4m`, `/tmp/core-b4p`, `/tmp/smfull` exist; apply checks: all six patch files exit 0 on b4cce5b; on HEAD C-01 (original, copy, price-only) and G5 exit 1, A-01 exit 0.

## Lines and headings that moved
Lines 5 and 77 did NOT move. "### Edit list for DEAD-MAN-CHECK.md" stays at 193 (heading text changed). Shifted: Missed risks 203 to 213, login table 242 to 252, Decisions 343 to 353, Decision 28 490 to 522, History 592 to 624. Later headings shifted by 32. Fix any cites by heading name.

## Raw outputs
See `fix-review39.raw` (count_review: 28 rows, Major 4 / Minor 13 / Nit 11, PROPOSE FIX 25, DECLINE 3; check_refs PASS 5177; check_names PASS 655; check_secrets PASS 0 hits in 2721 files; ruff format --check: 868 files already formatted).
