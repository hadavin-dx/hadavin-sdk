# fix-claims11
Backup: scratchpad CLAIMS-TABLE.bak. Edited CLAIMS-TABLE.md only; QUESTIONS.md not changed (not needed).
Row 18, 19, 33 cites reworded to the cited lines (verified by reading DOUBTFUL-SCENE.md:13, PAGE-STATEMENTS-V4.md:134,156, AGENT-SCOPE-DO-AND-DONT.md:20). Row 33 now says flows-audit/ORDERS.md:82; line 13 defines every ORDERS.md as the flows-audit copy (line 644 already said flows-audit/ORDERS.md:60, verified to name OWNER-STEPS).
New section 'RunSheet-wording rows with no claim row' (13 ids, bullets, no table rows).
check_rw_ct_pairs before: found 123 of 136, 13 missing; after: 136 of 136, 0 missing.

## after
paste strings in RW: 136 | found word for word in CT: 136
not found in CT: 0
## paste
section '7': 44 rows
total rows: 185
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 86 | with no row here: []
claim ids marked UNTRACED there: 48 | with no row here: 41 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
## count
python3: can't open file '/home/user/hadavin-sdk/handover/flows-audit/tools/claims-count.py': [Errno 2] No such file or directory
verdicts: {'UNSUPPORTED': 27, 'OVERSTATED': 62, 'SUPPORTED': 119, 'UNTRACED': 49, 'RELAYED-ONLY': 70} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 327 unique: 327
## refs
PASS 5166 references
## ruff
624 files already formatted
