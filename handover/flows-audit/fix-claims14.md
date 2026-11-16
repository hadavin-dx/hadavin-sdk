# fix-claims14.md (fixer for reviews/claims-r4-design.md M1-M5 plus the RW sync list of fix-rswording12.md), 2026-11-16
Edited only CLAIMS-TABLE.md. No commit. Backup of the file before the edit: scratchpad CLAIMS-before.md.

## What is not decided or not done (first)
- A-016f verdict is UNTRACED: the sentence is about a recording and a proof that do not exist yet. I read RW A-016f, CT rows A-002 and B-195; none shows 1 mail for this recording.
- claims-count.py reads numeric ids only, so the lane row is A-099 (the claim of RW row A-016f). Lane A is now 98 claims, total 328, UNTRACED 50.
- Lane rows keep their pasted strings (the pair checker reads them there); not removed.
- Verdict cells keep the spelling SUPPORTED ONLY BY RELAYED NUMBER (script reads that spelling; my rename to RELAYED-ONLY made 70 offenders and was reverted). Only the lane B header text was renamed.
- Rows 1, 2, 3, 8, 9, 12, 16, 22, 36, 42 were not split: a SUPERSEDED id or an other-branch cell is not a second action (rule in the new legend). Row 36 other-branch X-5b PASTE vs X-5a HELD stays one row by that rule. Not checked: every Table 2 row 41-84 for mixed status beyond the script check on ids.
- The "older desk" tag was added to all rows of WATCH-CHECKLIST, FAILED-TAKE-NOTE, RUN-ON-LAPTOP, RERUN-RUNBOOK, CLEAN-MACHINE-1 (39 rows). I judged RUN-ON-LAPTOP and RERUN-RUNBOOK as older desk or other-machine material.

## Changes
M1: new lane A row A-099 (UNTRACED); row 8b ids and why-cell fixed; A-015 and A-016 point to it; verdict list and notes updated; counts updated everywhere (328, UNTRACED 50, lane A 98, 97 claims in to-do rows, sub-row list).
M4: split rows 14 (14b), 15 (15b, 15c), 19 (19b), 23 (23b, 23c), 27 (27b), 28 (28b), 35 (35b), 48 (48b); row 33 family "needs" cell no longer says "no decision needed" next to HELD.
M3: legend "PASTE means PROPOSED, NOT APPROVED" at the top; verdict-word rule in line 10 (capitals only as verdict; relayed in lower case); lane B header renamed.
M5: [OUT OF THIS VIDEO] on older-desk headings and rows and on the 5 later-video bullets.
M2: ONE PRECEDENCE RULE at the top; lines 3, 10 and both lane notes (were 457, 624) now say the same.
Sync list (fix-rswording12.md): B-003a, B-003d (also the earlier PLAN:9 gets and ONS:135 gets sentences), B-011 (row B-011 and Table row 47), B-088 (row B-088 and Table row 80) updated word for word.

== BEFORE ==
paste strings in RW: 136 | found word for word in CT: 136
not found in CT: 0
section '1': 51 rows
section '2': 19 rows
section '3': 71 rows
section '7': 44 rows
total rows: 185
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 86 | with no row here: []
claim ids marked UNTRACED there: 48 | with no row here: 41 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
PASS 5166 references
verdicts: {'UNSUPPORTED': 27, 'OVERSTATED': 62, 'SUPPORTED': 119, 'UNTRACED': 49, 'RELAYED-ONLY': 70} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 327 unique: 327
== AFTER ==
paste strings in RW: 136 | found word for word in CT: 136
not found in CT: 0
section '1': 51 rows
section '2': 19 rows
section '3': 71 rows
section '7': 44 rows
total rows: 185
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 86 | with no row here: []
claim ids marked UNTRACED there: 49 | with no row here: 42 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
PASS 5166 references
verdicts: {'UNSUPPORTED': 27, 'OVERSTATED': 62, 'SUPPORTED': 119, 'UNTRACED': 50, 'RELAYED-ONLY': 70} total 328
lanes (A, B incl. X): {'A': 98, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 328 unique: 328
