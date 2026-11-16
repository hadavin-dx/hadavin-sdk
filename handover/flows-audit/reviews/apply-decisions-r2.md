# Apply lead decisions 2026-11-16, round 2 (fixer log, static text edits, nothing ran)

## Failures and open items (first)
- FAILED: none. All 67 scripted edits (one more line in the script was a disabled no-op) plus 1 paragraph rewrite matched exactly once (script in the session scratchpad, backups of the 12 files in scratchpad dec-r2/).
- NOT FIXED, lead's call: M4 (re-rating of F-005, F-006, F-023, F6B-01, F6B-13) and M8 (scene 4 caption "K1, 5 runs, median 60.8 s, max 61.9 s"). Only Q14 is now cited at: FINDINGS rows F-005, F-006, F-023 and the counts paragraph; FIX-PLAN header; LEDGER-ROWS header and F-005 row; F6B-AUDIT summary, F6B-01, F6B-13; SCENE-FLOW-MAP scene 4 row and C3. No severity was changed.
- NOT CHECKED: patches/, CLAIMS-TABLE.md, RUNSHEET-WORDING.md, fill_flows/, flow-check/ (not mine); VIDEO-RUNSHEET.md and inputs/ (read only; the run sheet still has scenes 5 to 11, L3 of the first log).
- UNVERIFIED: the statement that patches F-003 and F-004 insert scene 5 and "60.1 to 61.9 s" is from the first pass log (L4), not re-read from the patch bodies.

## What was fixed
- M1 and M2: every count statement now says 8 Blocker / 8 Major / 29 Nit, BEFORE 17, AFTER 28 AS RATED NOW and that Q14 may change them (FINDINGS counts paragraph, REPORT, FIX-PLAN, QUESTIONS Q9, LEDGER-ROWS header). F-011 and F-041 are stated as Major and counted BEFORE as the table says; the video does not say "one database"; if the lead moves them AFTER the counts are 8/6/31, BEFORE 15, AFTER 30. The old "stay AFTER (Nit)" wording in QUESTIONS Q4 and the reversed sentence in REPORT are replaced.
- M3: "8 files" is now "4 files in real-v5" in FINDINGS (rebuild line F-002, F-008, F-011 import test, row 58) and FIX-PLAN:1; kept as 8 with "of the two folders (the 4 in real-v5 are the take's)" at FINDINGS 57, 96 (twice), 101, EXCEPTIONS 14, SCENE-FLOW-MAP 46 and 71; QUESTIONS Q11 says 4 files in each of the two folders.
- M5: FINDINGS F-003, F-004, F-006 and FIX-PLAN item 7 say: regenerate against real-v5 and scenes 1-4, do not apply as is.
- M6: Q10 recommendation replaced: no run-sheet line about switching flow sets; the run sheet only needs scenes 5 to 11 cut.
- M7: F6B-AUDIT steps 1 to 5 marked NOT USED (the check for older recovery flows, F6B-15, is named as the one part kept for real-v5); step 3, F6B-02 and F6B-14 now say export lead_key and crm_id to a file before any TRUNCATE.
- M9 and nits: scene 1 sentence marked cut; F6B "11 scenes" is now 12 (11 plus closing card, as the map and run sheet); C1 rule text marked superseded; "one Postgres"/"separate database" wording at FINDINGS F-011 and LEDGER F-011; LEDGER F-005 cut marker; Q11 no longer says "until you answer"; EXCEPTIONS definition says "the take's database on the one Postgres server"; PLAN-002:27 no longer says the one-store file is absent (a copy is in inputs/). Present-tense places: FINDINGS 59, 80, 89, 96; F6B 20, 23, 82, 88, 96; QUEUE 13 and 21.

## Checks run (output)
- Recount by script: FINDINGS 45 ids, LEDGER-ROWS 45 ids, same ids, same severities (True); counts Blocker 8, Major 8, Nit 29.
- Window check (300 characters either side) for "scenes 5 to 11", "60.1 to 61.9", "flow-set switch", "switch flow set", "switch the film set" across the 12 files: 0 occurrences without a cut marker.
- grep for "8 files/8 flows": the only remaining hits say "of the two folders".
