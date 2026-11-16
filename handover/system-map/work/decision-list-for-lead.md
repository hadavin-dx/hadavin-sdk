# Decisions the studio lead owes, one answer each
Written Mon 16 Nov 2026 by the system-map session from digest entries 143-198 (work/agent-reports-batch4.md). Reader: the studio lead. Made-up data only. Every date and every default below is MY PROPOSAL, not a fact from a file; the lead may change any of them. Where a default says "if silent", it is only what this session suggests happens when no answer comes. No item here has been run or tested.

Words: **studio lead** = the Claude session that works with the owner. **owner** = the human. **run (a)** = the loopback re-smoke; **run (b)** = the first laptop run of real-v5 with made-up data (names used on TAKE-BLOCKERS.md line 34). **take** = the one filmed run.

Proposed answer times: items that block the filming by Tue 17 Nov 12:29 UTC / 17:59 IST (the time LEAD-PAGE.md already uses for LP-1, LP-4, LP-5); items that block only the post (Wed 25 Nov 15:00 UTC / 20:30 IST) by Fri 20 Nov 12:29 UTC / 17:59 IST. The latest filming start is Mon 23 Nov 18:14:40 UTC / 23:44:40 IST, and the start notice must come at least 3 hours before it.

## A. Blocks the filming
| # | Question (yes/no or a name) | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| A1 | Who builds the flow-fill step (`fill_flows.py`, not built)? One name and a finish date. | Mon 16 Nov, today | the studio lead assigns an engineering session, finish Tue 17 Nov 12:29 UTC | TAKE-BLOCKERS.md row 1 (line 33); LEAD-PAGE.md ask 1; digest 143, 189, 193 |
| A2 | Does the rule "rehearsal passed" cover run (a), run (b) or both? | Tue 17 Nov 12:29 UTC | both | TAKE-BLOCKERS.md line 34; LEAD-PAGE.md ask 2; digest 189 |
| A3 | Is the mail-crash test required before the take: yes/no? | Tue 17 Nov 12:29 UTC | yes (T19 and the crash test are not run yet) | TAKE-BLOCKERS.md line 47, 51; digest 150 |
| A4 | When does run (a) start (hour in UTC and IST)? LEAD-PAGE.md ask 6 still says "LEAD FILLS". | Mon 16 Nov, today | none; the take date stays unconfirmed | LEAD-PAGE.md lines 6, 20, 21; digest 193 |
| A5 | Which date and start time does the owner get for the take (UTC and IST)? | within 2 hours of the run (b) result | none; Wed 18 Nov is NOT confirmed | OWNER-VIEW.md line 4; TAKE-BLOCKERS.md row 4 |
| A6 | Which counts proof does the video use: a rehearsal screenshot or the Postgres node preview (decision 9 leaves it open)? | Tue 17 Nov 12:29 UTC | rehearsal screenshot | DECISIONS-2026-11-16.md item 9; digest 192 |
| A7 | Which port does the take use (decision 6 says "its own free port", no number)? Who picks it? | before run (b) | the engineering session that builds A1 picks one free port and writes it in the plan | DECISIONS item 6; digest 172, 192 |
| A8 | Path to `n8n_api.py` (not in this checkout): who gives it? | Mon 16 Nov, today | none; flow import cannot be tested without it | TAKE-BLOCKERS.md; digest 189 |
| A9 | Fill the three unfilled lines on the run-day card (how the receiver account looks; how the demo HubSpot account looks; the candidate proof screens; who films). Who fills, by when? | Tue 17 Nov 12:29 UTC | the studio lead fills after run (b), before the start notice | OWNER-RUN-DAY-CARD.md lines 31, 35, 59; digest 146, 154, 157, 188, 197 |
| A10 | Replace "the take deletes" wording in v5 lines 114, 124, 127-130, the program's notice and prompt, drift/REPORT.md:33, drift/APPLIED-S9.md:12 and inputs/AGENT-SCOPE-DO-AND-DONT.md:20 with "the take never deletes; the owner deletes leftovers by hand" (decision 2). Who edits what? | Tue 17 Nov 12:29 UTC | core-hardening edits v5 and the program text; this session edits only its own pages | DECISIONS item 2; digest 164, 191, 195 |
| A11 | Does the Route-config check of decision 4 apply (only if the model program loads Route config; nobody has checked)? Who checks? | before run (b) | the engineering session from A1 checks and writes yes or no | DECISIONS item 4; digest 172, 192 |
| A12 | Who checks n8n's run list for stored lead data after patch F-008? | before run (b) | the engineering session from A1 | digest 192 (QUESTIONS item 7) |

## B. Blocks only the post (Wed 25 Nov 15:00 UTC / 20:30 IST)
| # | Question | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| B1 | Apply D-04 (post says only "A lead sent twice with the same id is processed once."): yes/no? | Fri 20 Nov 12:29 UTC | yes | decisions/D04-D05.md; LEAD-PAGE.md ask 3 |
| B2 | Apply D-05 (the post waits for the crash-test result; the lead gives the limit wording): yes/no? | Fri 20 Nov 12:29 UTC | yes | decisions/D04-D05.md; digest 185 |
| B3 | Who edits step J of the owner steps file (core-hardening's file)? One name. | Fri 20 Nov 12:29 UTC | the studio lead | decisions/D04-D05.md line 9; digest 185 |
| B4 | Who accepts a crash limit in writing if the test shows a double mail: the owner or the lead? Three pages name three different people. | Fri 20 Nov 12:29 UTC | the owner accepts in writing | digest 198 (item 13) |
| B5 | Who (a person other than the author) checks the post text against the banned list? One name. | Fri 20 Nov 12:29 UTC | none | OWNER-VIEW.md row 6 |
| B6 | Does a longer sentence about how the system is built stay in the post? | Mon 23 Nov 12:29 UTC | no | D04-D05.md line 16 |

## C. Pages that disagree (a person must pick one; no date needed beyond A10)
| # | Conflict | Source |
|---|---|---|
| C1 | banned-claims.md vs v5 step J: the banned list is stricter than step J's wording. Which wins? (Decision 1 allows one claim.) | digest 164, 183 |
| C2 | OWNER-VIEW.md line 14 says the yes holds three figures; line 21 lists five items. Which figures does the yes hold? | digest 147, 158, 166 |
| C3 | OWNER-CLEANUP-CARD vs v5 step I: screenshot count (4 vs 3), step 6a missing from v5, "STILL WORKS" handling is opposite, retire-check command form missing on the card. Edit the card or v5? | digest 169, 182 |
| C4 | QUESTIONS.md has no entry for LP-1, LP-3, LP-5; D-01 to D-05 cannot be mapped to the 12 decision numbers. | digest 192, 193 |
| C5 | Stale pages: film-v5 still filled in plan lines 120, 236, 298; C-01 still open in FINAL-CROSSCHECK lines 54, 63, 102; APPLIED-S9.md and ONE-PLACE-TABLE:183 still say "apply" for S9-1, S9-2, S9-4 (decision 5 defers them). | digest 164 |
| C6 | REPORT.md says "citations 1020 of 1020"; SWEEP.md:5 says 2013 of 2013. Which is current? | digest 176 |
| C7 | The M3, M5, M14 numbers in drift/REPORT.md disagree with the board. | STATUS-BOARD.md; digest 150 |
| C8 | ARCHIVE-CUT-LIST has no Decision column and says in lines 28-30 that M and K must stay, D and E hold, L folds into the cross-check, while rows A-M still say move. Add a Decision column? And where is the archive: inside or outside the repo? | digest 173, 179 |

## D. Small, safe changes that need the lead's yes because the files are not mine
- A placeholder check in `tools/scan_outputs.py` (flag "[studio lead fills" and "LEAD FILLS"): digest 165.
- One-line "terms are defined below" pointers and a job-key legend (STORE, FILTER, RETRY, NOTICE, COUNTER, LOG, OTHER) at the top of MASTER-MAP.md, ONE-PLACE-TABLE.md and SWEEP.md: digest 175, 178, 181, 190.
- The ORDER 028 stamp (11:31Z) is later than the real clock at the time (11:15:50Z): who wrote it? Digest 150.

## E. Added 16 Nov after batch 199-206 (more pages read; all proposals)
| # | Question | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| E1 | Fix ORDERS.md: l.115 "no film pause" vs l.128 (pause stays); the agent count is "6+", "up to 8" and "8 to 10" in different lines; l.87 should say superseded by l.97. Who edits (the file is the lead's)? | Tue 17 Nov 12:29 UTC | the lead edits; this session keeps 8 agents | digest 204 |
| E2 | banned-claims.md: does it override v5 step J? Allow "crash-safe" only after a named result file? Add bans for "one database", "least privilege / separate logins", "the program checks the settings"? yes/no each | Fri 20 Nov 12:29 UTC | yes to all four | digest 201 |
| E3 | DECISION-one-store.md lines 1, 13, 14, 16, 20: change to "one Postgres server, two databases" (decision 10) and say the proof screen is decided (decision 9)? | Tue 17 Nov 12:29 UTC | yes | digest 201 |
| E4 | M17-end-never-deletes.md: replace the wrong quote at v5 43-44 and the shortened quote of v5 124 with the exact text. Who? | Fri 20 Nov 12:29 UTC | the lead | digest 202 |
| E5 | flowcheck/REPORT.md: who owns the two Blockers (no password on lead-intake entry points; five patches not listed) and the 8 Majors? | Tue 17 Nov 12:29 UTC | engineering session from A1 | digest 200 |
| E6 | drift/REPORT.md: correct six cite slips (D-06, D-14, D-15 and three "agree" rows)? | Fri 20 Nov 12:29 UTC | yes, core-hardening edits | digest 203 |
| E7 | MAP-ADDITIONS.md: FINAL-CROSSCHECK line count 108 to 110; show all 7 job keys; split row 009 counts. Who edits (hand-kept)? | Fri 20 Nov 12:29 UTC | the lead | digest 206 |
| E8 | REPORT.md and MASTER-MAP counts: "797 rows" is now about 812; "314 raw" vs 322. Restate with date? | Fri 20 Nov 12:29 UTC | yes | digest 199 |

## What this session did not check
Every item above comes from model reads of single pages. I verified only the few cites listed as confirmed in digests 161, 162, 170, 176, 191. The list is not complete: items on pages no agent has read yet are missing, and work/open-items-table.md still needs the same rows added (digest 198).
