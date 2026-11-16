# fix-rwct43 (fixer, round 43; RW and CT only; static; no git)
## Failures, gaps, not checked
- I did not re-read RW or CT in full (about 750 KB). I read only the passages I edited and the lines around them. Every edit was checked by the four tools below, which check counts and pairs, not wording.
- Desk-repo facts (B-016, B-019, B-088, B-092): not re-checked (the repo is not in this checkout).
- Reader r43 minor "B-215b and B-214 have no lane row yet counted in the 97" is partly wrong: B-214 and B-215 have lane rows (claims-count finds both); B-215b is a sub-sentence, not counted among the 97. CT row 33d already says its own lane row does not exist. No change.
- r40 M3, M5, M6, M7 were already fixed in the files by earlier rounds (checked, text quoted in the table below); no new edit needed.
- Lead to confirm: (1) B-110 and B-112 regraded to SUPPORTED (file N8N-ENV-PROBE.md exists here and says so; it is another session's note, raw run not seen); (2) B-126 to UNTRACED and B-140 to RELAYED-ONLY, B-086 stays OVERSTATED with A-010; (3) the ten new RW rows are status NO PASTE (not HELD), because nothing is pasted and the rows are out of the take.
## Counts
Old: UNSUPPORTED 9, OVERSTATED 98, SUPPORTED 82, RELAYED-ONLY 64, UNTRACED 77, total 330; lanes A 100 / B 226 / X 4; lane B split 62/41/50/6/71.
New: UNSUPPORTED 9, OVERSTATED 107, SUPPORTED 80, RELAYED-ONLY 57, UNTRACED 77, total 330; offenders 0; ids 330 unique; to-do rows 87; lanes A 100 / B 226 / X 4; lane B split 60/34/59/6/71 (lane A unchanged 20/23/48/3/6).
check_rw_ct_pairs: 144 of 144, not found 0 (unchanged). check_runsheet_paste: PASS; flagged 104 -> 113 (all with a row); UNTRACED A/B 76, rows missing 64 -> 63. RW status rows 206 -> 216 (NO PASTE 11 -> 21; section 3: 78 -> 88).
Files that quote old counts: only RW and CT (RW lines 33, status table, Counted-by-script paragraph; CT Start-here counts, UNTRACED bullet, Count paragraph, Not-checked bullet, Verdict list). Updated. Outside files: QUESTIONS.md line 731 quotes only the total 330 (unchanged, still true). No other file quotes the old verdict counts.
## Findings -> change
| finding | change |
|---|---|
| r43 M1 | CT "(6 + 71 = 77 untraced in all)" |
| r43 M2 | RW A-004 note starts "OVERSTATED in CLAIMS-TABLE.md (regraded from UNTRACED in round 41)" |
| r43 M3 | Q21 item 2 is ANSWERED (ORDERS.md line 132); RW line 70, CT WL-8 and CT Q21 line say so and name that only the lead's own optional action is open |
| r43 M4 | CT Start-here step 3 now names the two live deletes next to OUT rows (19b, 25); step 7 already listed 19b as a sub-row not counted |
| r43 M5 | CT rows 10 and 11 strings copied from RW ("is built to ..."); other-branch cell marked RW A-030 string wins |
| r43 M6 | RW X-5b and CT row 36: hedge now names DECISION-one-store.md line 8 and N8N-START.md, "not checked here, P4b has not run" |
| r43 M7 | CT UNTRACED definition and "leave out" list: exception for A-099 (RW A-016b, A-016f, A-016h) only after the RW step 15 proof |
| r43 minors | RW Q-H: rule ANSWERED, date and hour UNANSWERED; V-41 explained (row that deletes card line 4, claim A-052); "label" -> "tag" in N-12 note; CT "11 + 71" fixed |
| r40 M1 | B-039, B-048, B-052, B-078 (SUPPORTED) and B-099, B-104, B-106 (RELAYED-ONLY) -> OVERSTATED; CT line 405 verdict list updated; RW rows added for the six without one |
| r40 M2 | B-073 -> OVERSTATED (two READMEs disagree); B-126 -> UNTRACED; B-140 -> RELAYED-ONLY (same as B-138); B-086 stays OVERSTATED with A-010 family, reason written in CT "Same claim, different lanes" |
| r40 M3 | already done in round 40 (B-043, B-047, B-135 UNTRACED); checked |
| r40 M4 | B-105, B-111, B-114 -> OVERSTATED (12/13, three/two failures, 130/129); B-110, B-112 -> SUPPORTED |
| r40 M5 | already hedged in the PASTE strings of B-016, B-019, B-088, B-092, B-130; checked |
| r40 M6 | already fixed (string splits stated, "six cells"); checked |
| r40 M7 | already fixed (31 rows without lane row counted by script); checked |
| r40 M8 | CT B-219 row: B-003c is NO PASTE corrected to SUPERSEDED; B-046 already says HELD |
| r40 M9 | RW History and "Not reviewed in their final form" now name fix-rwct43 and read r43 as latest and list the rows changed |
## Final checks (from handover/flows-audit)
ruff format --check .: 1009 files already formatted. check_refs: PASS 5193 references. check_names: PASS 655 rows. check_secrets: PASS 0 hits in 2884 files. check_counts: PASS 52 files / 655 nodes.
