# v19 evidence (EVIDENCE RUNNER: records, does not judge). Mon 16 Nov 2026
Preamble read: handover/BRIEF-PREAMBLE.md (STUDIO-PREAMBLE v1). No git, no spend, no secrets. Python run with -I on a scratch copy only. Banned words were never printed (counts only).

## A. Failures and mismatches first
1. Citation ambiguity, v19-OPEN-FOR-LEAD.md row 7: "AGENT-SCOPE section 3, line 1051, F-01". inputs/AGENT-SCOPE-DO-AND-DONT.md has 35 lines; 1051 is the script line `run_real_check_n8n.py:1051` quoted inside AGENT-SCOPE line 20. Read literally, the pointer does not exist. The Note (item 0.1) words it correctly.
2. Map pointer, v19-MAP.md SM5 ("UNVERIFIED items"): "Open 19". Open 19 is "Places and tools (G24), page button words, key list cancelled word". It does not cover UNVERIFIED items. The other pointer on that row (Note 3 template) exists.
3. Map overstatement, SC-C: "order table rows 6 to 10 ('NOT safe')". Only rows 8, 9, 10 in the sheet's order table say "NOT safe". Row 6 says "a made key stays alive: cancel it". Row 7 says "no run; cancel the key".
4. Map pointer, SB3: "6.5 (a failed save leaves no older key and the sheet says why it is no loss)". The "why no loss" sentence is in sheet 6.2 ("the run does not need it ... start again with a new run name (6.5)"). 6.5 only covers the failed-save steps.
5. Map pointer, SM6: "Note 0 (money words)". The money-word definitions sit in the Note's opening paragraph (line 3), before "## 0", not in section 0.
6. Source not found in the reviews, SQ-len: the map says SQ = "the stranger's two extra questions" and cites "stranger: aim shorter than 98 lines". review-v18-stranger.md contains no length question (grep for short/98/length/long: none). Only SQ-len exists in the map, so "two" is not matched by a second SQ row. The review file is a condensed copy, so the full report may hold it; I could not check that.
7. Note section 3 template, last line: "Statements: G1 to G15, G17 to G24 all YES". G31 and G32 are 1a gates (before the numbers message) but are not in that statements list. G31 and G32 appear elsewhere in the template (second way, older key lines). Recorded as a gap, not judged.
8. Note G20 says `stage.journal` is "the one stated second record (decision 10)". DECISIONS-2026-11-16 item 10 does not mention stage.journal. The wording "the one stated exception of decision 10" is in ORDERS.md line 152 (Q21.3). DECISION-one-store line 26 says "(decision 4)". So the "decision 10" label rests on ORDERS.md:152, not on the DECISIONS file.
9. Note 8 closing paragraph: "The AGENT-SCOPE and FACTS lines that say the owner types a worst-case figure shown in the notice are stale". AGENT-SCOPE line 22 has "the typed worst-case figure ... shown in the notice". In FACTS I found no "worst-case" or "figure"; FACTS line 4 says "the written yes with the numbers shown by the take notice". The claim holds for AGENT-SCOPE and only loosely for FACTS.
10. Not a failure, recorded: v19-CHANGES.md says "I did not re-verify every v18 citation". I re-verified the ones listed in section D.

## B. (1) check-v19.py on a scratch copy
- Scratch copy changed only the `D = ...` line (diff shows 1 line). Copied files: the four package files. The checker still read /home/user/hadavin-sdk/tests/test_no_reference_material.py for the banned list (that path line was not changed).
- Result: exit code 0; output identical to v19-check-output.txt (`diff` printed nothing; "SAME").
- Output as run: lines {S 102, N 136, M 115, O 37}; sheet headings 9; R1..R10 once each; G1..G32 once each; open rows 31; glossary order ok; banned words: 10 listed, case-sensitive 0, case-insensitive 0; UTC = IST pairs checked 15; map table rows 94; TOTAL PROBLEMS 0.
- Note: the checker's own "TOTAL PROBLEMS 0" is form only. I did not run its planted-mistake test (CHANGES claims four plants were caught; not re-run).

## C. (2) Recomputed times, pairs, weekdays, money (by my own Python, not the checker)
- Weekdays 2026: Mon 16 Nov, Wed 18 Nov, Mon 23 Nov, Wed 25 Nov: all correct in all 5 files (33 mentions, 0 wrong).
- UTC/IST pairs (+5:30), 24 occurrences in sheet and note: 0 wrong. Checked values: 18:29 = 23:59; 11:30 = 17:00; 11:55 = 17:25; 12:05 = 17:35; 18:14:40 = 23:44:40; 15:00 = 20:30; 17:54:00 = 23:24; 18:19:00 = 23:49; 18:29:00 = 23:59.
- Time arithmetic: 11:30 + (5+10+10) = 11:55; + 10 = 12:05. 18:29:00 - 860 s = 18:14:40. 18:29 - 35 min = 17:54:00; + 25 = 18:19:00; + 10 = 18:29:00. Sample: latest start 11:30 is before 18:14:40 and before 17:54. All correct.
- Money: (40,000 x 3 + 10,000 x 15) / 1,000,000 = 0.27; 3 x 0.27 = 0.81; 12.40 + 0.81 = 13.21; 3.10 to 3.90 = 0.80 (not over 0.81), 4.00 would be 0.90 (over); balance 189 is between 0.81 and 200; 13.21 and 12.40 + 0.81 = 13.21 are below 180. All correct.
- Word counts: sheet 5,246 words, 102 lines; v18 sheet 4,246 words, 98 lines. Matches "about 5,200 / 5,250" and "4,250". v18 open-for-lead has 25 numbered rows, v19 has 31, matches CHANGES.
- Source of the 860 s: inputs/OWNER-STEPS-realrun-v3.md line 171 (default lease 860 s, last start before 18:14:40Z). The sheet/note do not cite this line; they say `need_seconds` at the final head.

## D. (3) Citations of input files (exists at the line, words present)
| Citation (where) | Result |
|---|---|
| ORDERS.md line 150 = Q21.1, "post by Wed 25 Nov 15:00 UTC = 20:30 IST" (Note 2, Open 20, Map) | present, exact |
| ORDERS.md line 81 "a lead sent twice with the same id is processed once" (Note 5) | present |
| QUESTIONS.md line 55, "post-by is Wed 25 Nov 15:00 UTC = 20:30 IST" | present (it is Q21 item 1, line 55) |
| OWNER-STEPS-realrun-v3.md line 130 "Step 23. Post Wed 25 Nov 2026, 15:00 UTC = 20:30 IST" | present |
| FACTS-ALREADY-DONE.md line 3 "US$180 of 189 in-code backstop" and "no limit questions" and n8n credential store holds HubSpot, Claude, Gmail | present, exact |
| AGENT-SCOPE-DO-AND-DONT.md line 15 "US$180 of 189 at the time of writing, checked by a human" and window end "2026-11-23 18:29Z" | present, exact |
| AGENT-SCOPE section 3 (lines 18-23): `run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, F-01, CODE-CHANGE-NEEDED, not fixed (here: "not fixed here"); `:573` "B ten times at once" literal (line 23) | present; the script files themselves are not in this checkout, so the line numbers inside them were not checked |
| AGENT-SCOPE line 22 "typed worst-case figure ... shown in the notice" | present (see A9 for FACTS) |
| DECISIONS-2026-11-16.md items 1, 2, 7, 8, 9, 10, S9-2 (item 5): wording quoted in Note/Open | present; item 1 wording exact; item 2 "the take never deletes contacts" exact |
| DECISION-one-store.md line 14 "ONE database"; CORRECTIONS heading line 25, (a) line 26 (separate database `n8n`, `stage.journal` exception) | present; "lines 25 and 26" correct |
| plan-wp6-resmoke-v5.md line 121 ports (5690/5691, 5692/5693, 5678/5679 owner's) | present |
| paste-check/plan-v10-real-v5-edits.md lines 456-459, Text B (Q21.2) | present (Text B at line 459) |
| ORDERS.md lines 147, 148, 151: Q20.3 unknown, Q20.4 exit code unverified, Q21.2 | present |
| OWNER-STEPS-realrun-v3 / OWNER-SHEET-v16 "13 submissions", A twice, B ten times | present (v16 lines 43, 231, 304) |
Not checked: that the v19 files quote "Q15.3", "v17 Open 15" or "BR-a..s" correctly (sources not opened); contents of scripts, flows, model program (not in checkout).

## E. (4) Definition counts and pointers
- Rules: `| R1 |` to `| R10 |` each defined exactly once, only in OWNER-SHEET-v19.md section 2 (own count: 10 rows; no definition rows in Note, Map, Open, Changes). The 10 key phrases the checker lists each occur once (checker output "rule phrases checked"; I did not recount them separately).
- Gates: G1..G32 each defined exactly once, only in the Note's three tables (1a 25 ids, 1b G16, G25, G26, G30, 1c G27, G28, G29; total 32). No undefined G id is referenced in any of the 5 files.
- R ids referenced in Note, Map, Open, Changes: all within R1..R10. R6 is not referenced in the Note; R5 is not in the Map; R8 not in Open; R10 not in Open. Not an error, recorded.
- Sheet sub-item pointers (5.1..5.8, 6.1..6.6, 7.1..7.8, 8.1..8.5): every "N.M" pointer in the five files exists (sheet has 8, 6, 8, 5 numbered items in sections 5 to 8).
- "Open n" pointers: all within 1..31. Pointers whose target topic I compared with the Open row: 1, 2, 6, 9, 10, 11, 12, 20, 21, 26, 27, 28, 29, 30, 31 match; 19 does not match for SM5 (A2).
- Note section pointers (0..9) all exist.

## F. (5) Review findings against v19-MAP.md
| Source | Findings in the file | In the map | Pointer exists |
|---|---|---|---|
| review-v18-stranger.md | blockers 1-6, contradictions A-D, 25 majors (counted in the Major paragraph in the same order as SM1..SM25) | SB1-SB6, SC-A..SC-D, SM1..SM25 all present | yes except A2, A3, A4, A5 above |
| review-v18-stranger.md | "if you do nothing" and "if a lead message looks odd" sections | covered by SC-C and SB2 | yes |
| review-v18-stranger.md | length question (SQ-len) | in map, not found in the file | see A6 |
| review-v18-security.md | M1-M8, N1-N8, v17 carry-over line | XM1-XM8, XN1-XN8 present in order; take-program-deletes row present | yes |
| review-v18-evidence-summary.md | M1-M5 | EM1-EM5 present | yes (EM2 mentions "Open 24" only as the old wrong pointer) |
Counts: map has SB 6, SC 4, SM 25, SQ 1, XM 8, XN 8, EM 5, K 22 ids (the script's has() check passes the same ids).
The security file says "6 Majors (+2 readiness Majors)" and lists 8 majors; map has 8. Not reconciled further.

## G. What I did not check
Truth of any statement about the take program, flows, model program, HubSpot or model-account pages (none in the checkout). Any command printed on the sheet (nothing was run). The v17 and earlier reviews. The full (non-condensed) v18 review reports. That the sheet reads clearly to a stranger. Whether each map "Fixed where" text actually fixes its finding (I checked only that the pointer exists and the topic matches, for a sample of about 30 rows; not all 94 rows in depth). Banned words were counted by the checker only (0); I did not print or list them.
