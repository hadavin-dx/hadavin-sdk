# fix-rwct15 (fixer, static, nothing run in n8n/Postgres/HubSpot, nothing committed)
Edited only CLAIMS-TABLE.md (CT) and RUNSHEET-WORDING.md (RW). Reviewer words were unverified; each cited line was opened first. Final counts (python3 -I claims-count.py CLAIMS-TABLE.md): SUPPORTED 103, RELAYED-ONLY 64, OVERSTATED 84, UNSUPPORTED 15, UNTRACED 64 = 330; lane A 21/23/39/6/11 (100), lane B+X 82/41/45/9/53 (230).

## What I did NOT check or could not settle (first)
- I did not re-read CT in full or re-verify the cited source files for rows I did not touch. I re-opened only the cited rows and READMEs (n8n-table-screen README lines 3 and 22, v2 README line 3, V5-README lines 1, 16, 17, AGENT-SCOPE line 15, ORDERS.md 156 and 171, QUESTIONS.md items 13, 33, 39, 43, 45, 73, 76, 77).
- The "95 claims in 87 rows" figure of CT line 170 is derived by the reviewer's own arithmetic (84+15=99, minus 18 no-row OVERSTATED = 81, plus 14 others = 95); I could not reproduce 95 with a regex over the to-do tables (my regex found 91 or 97 depending on sub-rows), so it is arithmetic, not a script count.
- Needs lead (exact questions):
  1. Rehearsal 1 start on Wed 18 Nov: 07:30Z = 13:00 IST (ORDERS.md:171) or 07:40Z = 13:10 IST (QUESTIONS.md item 13)? RW:29 now states both and "unknown: lead answers".
  2. Who is the presenter of steps 5 to 9, and who records the voice rows? New RWQ-10 (RW section 4). Not yet a Q31 item; the lead adds it (I cannot edit QUESTIONS.md). Proposed default written there: the lead speaks live.
  3. Which made-up address domain do the take's lead addresses use (must land in the intake mailbox)? Q31 item 77, unchanged.
  4. Are the four new NO PASTE rows (A-074, B-086, B-126, B-140) acceptable, or does the lead want a replacement string (the A-010 string is named as the safe wording)?

## CT findings (claims-r7-design.md, citation-remaining-r1.md)
- M1 (line 116 stale): fixed. 95 claims in 87 rows; outside rows 235 = 101 SUPPORTED, 63 RELAYED-ONLY, 53 UNTRACED, 18 OVERSTATED (old text had an impossible 69 > 68). OVERSTATED list is now 18 (CT:116, :170).
- M2 (lines 120, 121): fixed to 64 RELAYED-ONLY, 64 UNTRACED, 15 UNSUPPORTED; "Most of the 64 ... and 64" fixed (CT:120, :121).
- M3 (line 161): fixed, now says OVERSTATED in both lanes, relayed basis after "second verdict, not counted:" (CT:161). Line 216 relayed list drops A-074 (23 in lane A).
- M4/citation M2 (one grade): fixed. A-074 -> OVERSTATED (CT:586), B-086 (:798), B-126 (:858), B-140 (:872) -> OVERSTATED with "second verdict, not counted: SUPPORTED ONLY BY RELAYED NUMBER". A-010 "same grade" sentence rewritten (CT:520). A-007, A-045 already OVERSTATED. DISPUTED in part: B-125 (:857) is a different sentence (what the four settings do, not whether the body stays); kept UNTRACED, note added saying why. Consequence: RW now needs rows for A-074, B-086, B-126, B-140 (checker); I added four NO PASTE rows (RW sections 2, 7, 3, 3).
- M5 (A-007, A-010 inferences): fixed by wording: "unverified inference about what n8n does" (CT:517, :520); grade stays OVERSTATED. "unverified" is lower case, not a verdict.
- M6 (second verdicts): fixed with "second verdict, not counted:" in A-003 (:513), A-072 (:584), A-093 (:605), A-096 (:608), B-155 (:891), B-107 (:827), B-219 (:975), B-054 (:758). A-053 (:566) has no true second verdict (it cross-refers to A-010); reworded to say so. History words lower case in B-038, B-045, B-046, B-085, A-097, B-054 and the change-log lines 121, 479, 648. B-085's "second verdict, not counted: none" removed.
- N1 (runtime claims): A-065, A-066, A-067, B-129, B-082, B-167, B-152, B-009 now "SUPPORTED (text-only, needs run: ...)". B-005 note plus "text-only" wording (kept SUPPORTED; honest note that the n8n-side half is shown by no file; I judged a regrade to OVERSTATED not worth a new RW row). B-073 and B-141 -> UNTRACED (absence only; READMEs disagree for B-073). B-176 kept SUPPORTED but its basis is now the file's own statement V5-README:17, not absence of result files. Counts of text-only rows now 17 (CT:127, :170).
- B-196 -> UNTRACED (CT:948), table row 346 and verdict-list row 73 (CT:455) fixed; RW:B-196 DELETE row wording fixed (status unchanged). Line 170 "13 others" is now 14 (B-196 added).
- X-3 cite :15 fixed (CT:1014; verified AGENT-SCOPE-DO-AND-DONT.md line 15 is the MUST NOT line).
- RW/CT string differences: A-016 "lead record" -> "lead ID" (CT:526), A-008 (CT:518), A-098 (CT:610, now the RW string), A-057 (CT:569), and the PASTE meaning at CT:274 now matches RW. check_rw_ct_pairs: 140 of 140 found.

## RW findings (rw-r8-reader.md items 5-12 and words)
- 5: fixed. RW:29 no longer cites item 13 for 07:30Z; states 07:30Z per ORDERS.md:171 and 07:40Z per Q31 item 13, lead answers. RW:28 sentence now says 39(a) and 43 are ANSWERED. Other Q31 pointers (33, 45, 73, 76, 77) checked against QUESTIONS.md and are correct.
- 6: fixed in A-016b (condition: only while A-016f is on screen, CT row A-100), A-016f (edit sync), step 7, step 10.
- 7: fixed. Section 0b P4a row, B-003b and B-219 notes now gated by P4a as well as A-016f. B-219 "In this recording": string unchanged (it is the same string in four rows); the note says it means the video the post goes out with, and the lead rewrites it if the post goes out without the video. DISPUTE-ish: I did not change the string, so the viewer sees the same words; a lead decision could still change all four rows.
- 8: fixed to one rule (RW:27 end; step 11, A-005, A-084 notes): no row names the take's address domain; example.com/.test cannot receive mail; unknown: lead verifies (Q31 item 77).
- 9: fixed by placeholders in RW:90 and new RWQ-10. Needs lead (question 2 above).
- 10: fixed. One wording: the lead records with Playwright, the studio owner edits and posts (RW:23, :89, Q-A line); CT lines 12 and 142 changed to match.
- 11: fixed. Step 2 now applies only section 1 rows before filming; section 2 (page) and 3 rows are applied after the video (their own headings say so); step 7 order A-016d then A-016a.
- 12: fixed. B-016, B-019, B-024 now say "by hand, cell by cell"; PASTE definition (RW:12) explains it; "paste-ready" removed (RW:35).
- Words: "claim" removed from the strings of B-011, B-165, B-182, B-189 (both files). DISPUTED: "claim row" in B-003a, B-003d, B-042 kept, because RW:24 defines claim row and allows that form. "the wait" now fixed to one meaning (RW:29 definition; step 8, row A-024 note, B-165 string changed); N-9, N-10, N-11 quote old run sheet text and keep "real wait". "unknown" state vs placeholder: new definition bullet. "label" vs "tag": definition and N-12, RW:27, :143 fixed; "label" in the stage-service sense (B-045 area, "same label") and the Gmail label left as they are different named things, defined or quoted.
- Minor "B-150c not in CT main table": not touched (outside the numbered list).

## Commands run (from handover/flows-audit)
- python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md -> RESULT: PASS (195 rows; 96 flagged ids all with a row; 63 UNTRACED, 52 without a row)
- python3 -I tools/check_rw_ct_pairs.py ... -> 140 found, 0 not found
- python3 -I claims-count.py CLAIMS-TABLE.md -> counts above, offenders 0
- python3 -I tools/check_refs.py -> PASS 5176 references; check_names.py -> PASS 655 rows; check_secrets.py -> PASS 0 hits in 1989 files
