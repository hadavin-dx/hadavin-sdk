# fix-rwct4: round 2 fixes for RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT)
Date 2026-11-16. Fixer sub-agent. Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rwct4/. No commit. Only RW, CT and this log were written.

## Failures, gaps and things not checked (first)
1. Reviewer error: BL1 says R:75 holds a "processed once" copy. R:75 of handover/demo/VIDEO-RUNSHEET.md reads "claim is same id twice only"; it has no such sentence, so no RW or CT row was made for it. R:4 does need a row: added as A-002 (live DELETE).
2. Not fully verified: a script that checks every double-quoted RW paste string against CT found about 100 RW strings not present word for word in CT. Most are RW-only extra rows (N-, V-, S5-voice, A-016b/d/g, A-087b/d) or lane B rows where CT keeps the wording in a different shape (partial quote, two sentences in two cells). I checked only the ones named in MJ4 and the ones I edited. One real mismatch was found and fixed (A-008b: CT said scenes 5 to 11, RW says scenes 5 to 10). The rest of the list (for example B-010, B-011, B-032, A-040/A-041 second sentence, A-033a/b) was NOT compared one by one. This is a gap, not a pass. Next step: a reader checks those pairs, or the lead decides the checker should enforce the pairing.
3. CT Table 2 rows 41 to 77 and lane rows I did not edit were not re-read in full.
4. A-084 caveat: the claim "no private address on screen" is true only for addresses the owner decides to crop, blur or cover (Q28). The lead never edits footage.
5. The checkers test coverage and quote rules, not sense. They passing does not show the wording is right.

## Per finding
- BL1 (checked against files: true for R:32 and R:41 "processed once"; wrong for R:75). Live DELETE rows now exist that do not depend on HELD A-016f: A-002 (R:4), A-016c (R:32), A-016e (R:41). CT carries the same actions (A-002, A-015 via A-016c, A-049 via A-016e).
- MJ1 (true). A-019a and A-019b are both CUT (R:90). A-087a and A-087b are PASTE; A-087c/d are marked as duplicates. A-053 and A-053b are CUT with no condition; P2 wording, section 0b and the Q-F row no longer say conditional (A-050c is the only voice item left in Q-F).
- MJ2 (true). N-9, N-10 and N-11b are HELD (lead applies at re-pin, HELD, DO NOT QUOTE marker). N-11a is a live DELETE of "Label sped up with the real wait from the overlay."
- MJ3 (true). RW rows added: A-020, A-085, A-086 (DELETE of P:151 and P:152). CT actions aligned for A-052, A-023, A-073, A-076, A-020, A-085, A-086. Old sentences A-073b and A-076a/b are CUT (one status each); A-073a/A-073c/A-076c now say "no sentence of its own".
- MJ4 (true). CT strings synced to RW (RW wins) for A-001, A-005, A-007, A-008, A-021, A-057, A-059, A-084, A-088, A-092, A-098 (Table 1 row 26), A-023, plus Table 1 and Table 2 rows 1, 2, 5, 6, 19, 21, 23 to 27, 41.
- MJ5 (true). RW row B-003 added (replaces the broad sentence at PLAN:9, :57, :184). CT B-003 action is replace; verdict stays SUPPORTED; the CT summary sentence near the old line 805 says replaced, not kept.
- "processed once" appears only as a changed or rejected note.

## Q28 (lead answer, ORDERS.md line 166)
Scoped caption everywhere: "In this recording, the same lead ID sent twice gave one e-mail message in the intake mailbox." RWQ-8 and RWQ-9 are ANSWERED. A-016f status is PASTE-with-proof-in-frame: the post-wait mailbox count and the mf_leads row are shown on screen (Postgres node preview or screenshot step). A-012 and A-084 notes list any private address on screen for the owner, who decides crop, blur, cover or not needed. CT Start-here item 14 records this. Not done: no footage touched.

## Counts
Verdict counts unchanged (327). RW section 6 Coverage text updated to 168 rows (46 / 19 / 62 / 41) and the N list.

## Checker output (run from handover/flows-audit)
$ python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
section '1': 46 rows
section '2': 19 rows
section '3': 62 rows
section '7': 41 rows
total rows: 168
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 80 | with no row here: []
claim ids marked UNTRACED there: 50 | with no row here: 43 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
rc=0
$ python3 claims-count.py CLAIMS-TABLE.md
verdicts: {'UNSUPPORTED': 29, 'SUPPORTED': 124, 'UNTRACED': 51, 'OVERSTATED': 54, 'RELAYED-ONLY': 69} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 327 unique: 327
rc=0
