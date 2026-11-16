# fix-rwct3 (flows-audit, 2026-11-16): round 2 of 2 on RUNSHEET-WORDING.md and CLAIMS-TABLE.md after reviews/adversarial-rw-ct-r1.md
Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rwct3/. Static edit; nothing ran except the two read-only checkers. Nothing committed. Only the two files and this log were edited.

## Failures and things not fixed (first)
- QUESTIONS.md NOT edited (outside my allowed files). The question about the words in the intake mailbox on the scoped caption (M1) is in RW section 4 as RWQ-8; the lead copies it to QUESTIONS.md (it is missing there: grep found no such question).
- inputs/DECISIONS-2026-11-16.md items 1 and 7 still say the broad words processed once: not my file; the lead corrects inputs/ (Q25 item 13d). Also VIDEO-RUNSHEET.md lines 6, 21, 33 (stopwatch) are applied by the lead from rows N-9, N-10, N-11.
- Open for the lead (not decided by me): RWQ-8 (add in the intake mailbox to the scoped caption; the caption was NOT reworded) and RWQ-9 (are the post-wait mailbox pane and the mf_leads row in frame, M2).
- Not checked: the exact current text of VIDEO-RUNSHEET.md lines 22, 41 beyond lines 6, 21, 23, 33 (I read those four). The N-11 old phrases are quoted from line 33 as the review and my grep showed them; the full cell text of line 33 was cut at 1200 characters, so check the two quoted phrases against the file before applying.
- Reviewer finding checks: all of B1, B2, M1 to M9 matched the files. M2 is partly by design (decision 9: proof by rehearsal screenshot or node preview, not a live screen), so I recorded it as a question, not a rewrite. M3: the parts in my two files are fixed; DECISIONS is not mine.

## Changes
- B1: CUT now means (status words) the old sentence is removed where it stands in a filmed or published file; the DELETE in the paste cell is LIVE. A-017a is CUT and relies on A-017b; A-017b, A-019b, A-051b, A-073b, A-076a, A-076b, A-081b say the DELETE is live (7 RW notes, 4 CT notes). Old card lines 2 to 6 (A-050a, A-050b, A-051a, V-41, A-023a, A-053, A-053b, A-091): paste cells are now DELETE, the former candidate text moved into the note (not to paste); N-3 NO PASTE. They left the HELD row (one status each: CUT). CT rows 14 to 17 and A-050, A-051, A-053, A-091 say DELETE live. New rows N-9 (R:6), N-10 (R:21), N-11 (R:33 stopwatch phrases) with strings, owner: the lead applies at re-pin (M8). Q-B updated.
- B2: A-012 has one status, HELD, with three conditions in the status cell (APPROVED, P4a, Q22 item 3 preparation plus Gmail filter). Row note, step 6 and CT row A-012 agree; CT verdict word SUPPORTED kept so the verdict counts stay 327 (status is written beside it).
- M1: A-016f NOT reworded; question RWQ-8. M2: RWQ-9; Gmail filter and label demo (step 4) named as a condition in A-012, A-016b/f status, step 10 and CT. M3: CT lines on processed once (Q5 x3, rules R2, claim to keep, item 10, B-003 note) now use the scoped sentence. M4: A-016a is now Here one lead record is sent twice. (no pointer at a result) in RW and CT rows A-016 and 8. M5: N-5a waits for the re-pin read too; the number 30 is out of the spoken string. M6: A-087c/d (and a/b, CT rows 3 and A-087) say on the real-v5 flows. M7: Step D wording is one sentence in RW (3 places) and CT (item 1, owner line, open steps): the owner deletes by hand. M9: A-016c and A-016e Paste cells are NO PASTE (rejected string moved to the note); the CHANGED status row is removed.
- Counts: RW paste rows 159 to 162 (section 1: 43); CT unchanged (327, no row added).

## Checker output (run from handover/flows-audit)
```
section '1': 43 rows
section '2': 17 rows
section '3': 61 rows
section '7': 41 rows
total rows: 162
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 80 | with no row here: []
claim ids marked UNTRACED there: 50 | with no row here: 43 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
```
```
verdicts: {'UNSUPPORTED': 29, 'SUPPORTED': 124, 'UNTRACED': 51, 'OVERSTATED': 54, 'RELAYED-ONLY': 69} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 327 unique: 327
```
