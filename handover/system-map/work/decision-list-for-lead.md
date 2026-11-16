# Decisions the studio lead owes, one answer each
Written Mon 16 Nov 2026 by the system-map session from digest entries 143-198 (work/agent-reports-batch4.md). Reader: the studio lead. Made-up data only. Every date and every default below is MY PROPOSAL, not a fact from a file; the lead may change any of them. Where a default says "if silent", it is only what this session suggests happens when no answer comes. No item here has been run or tested.

Words: **studio lead** = the Claude session that works with the owner. **owner** = the human. **run (a)** = the loopback re-smoke; **run (b)** = the first laptop run of real-v5 with made-up data (names used on TAKE-BLOCKERS.md line 34). **take** = the one filmed run.

Proposed answer times: items that block the filming by Tue 17 Nov 12:29 UTC / 17:59 IST (the time LEAD-PAGE.md already uses for LP-1, LP-4, LP-5); items that block only the post (Wed 25 Nov 15:00 UTC / 20:30 IST) by Fri 20 Nov 12:29 UTC / 17:59 IST. The latest filming start is Mon 23 Nov 18:14:40 UTC / 23:44:40 IST, and the start notice must come at least 3 hours before it.

## Terms used below (all proposals/readings, not new facts)
- **studio lead** = **the lead** = the one Claude session that works with the owner (same party everywhere in this list).
- **decision N** = item N in inputs/DECISIONS-2026-11-16.md (12 items). **D-04, D-05, LP-1..LP-5, S9-n, F-008, C-01** = row ids on LEAD-PAGE.md, decisions/ and drift/REPORT.md; the row text is on those pages.
- **T19** = the planned test that sends one lead twice and expects one processing; **crash test** = the planned test that stops n8n mid-run and restarts it; neither has run. **"rehearsal passed"** = the result file of a rehearsal run with every row PASS (the owner's card requires the studio lead to say it). **rerun margin** = the time kept free after a take's start so one failed take can be repeated (proposed: 4 hours). **engineering session** = a Claude session that does the technical steps.
- **step J** = the "post" step of inputs/OWNER-STEPS-realrun-v5-core-hardening.md. **core-hardening** = the other cloud session that owns that file.
- **digest N** = numbered entry N in work/agent-reports-batch4.md (the reasoning behind a row).
- **Proposed run dates (mine):** run (a) Mon 16 Nov 14:00 UTC / 19:30 IST if the lead agrees today; run (b) Tue 17 Nov 14:00 UTC / 19:30 IST; start-notice deadline for the last-day take: Mon 23 Nov 15:14:40 UTC / 20:44:40 IST.
- "If silent: none" means no fallback is proposed; filming stays blocked until someone answers. Every such item is answered or escalated to the owner by Fri 20 Nov 12:29 UTC / 17:59 IST at the latest (proposal).

**Escalation rule (proposal):** if a filming blocker (section A) has no answer by Tue 17 Nov 12:29 UTC / 17:59 IST, the lead asks the owner the same day; no answer by Wed 18 Nov 12:29 UTC / 18:59 IST means no take is scheduled before the next answer. The take date can never pass Mon 23 Nov (latest start 18:14:40 UTC / 23:44:40 IST).
**Two meanings of "run (a)":** this list uses run (a) = loopback re-smoke (TAKE-BLOCKERS.md line 34). LEAD-PAGE.md line 13 uses it for the stand-in rehearsal. A2 asks the lead to say which one the rule "rehearsal passed" means.
**Crash test and the take:** LEAD-PAGE.md says D-05 blocks the post, not the take; A3 asks whether the crash test is also required before the take. If the lead answers no, A3 closes and B2 stays.

## A. Blocks the filming
| # | Question (yes/no or a name) | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| A1 | Name the builder of the flow-fill step (`fill_flows.py`, not built): ____ . | Mon 16 Nov 18:00 UTC / 23:30 IST | if no name by then, the studio lead assigns an engineering session with finish Tue 17 Nov 12:29 UTC / 17:59 IST (a person or a session, either is accepted) | TAKE-BLOCKERS.md row 1 (line 33); LEAD-PAGE.md ask 1; digest 143, 189, 193 |
| A2 | Does the rule "rehearsal passed" cover run (a), run (b) or both? | Tue 17 Nov 12:29 UTC / 17:59 IST | both | TAKE-BLOCKERS.md line 34; LEAD-PAGE.md ask 2; digest 189 |
| A3 | Is the mail-crash test required before the take: yes/no? | Tue 17 Nov 12:29 UTC / 17:59 IST | yes (T19 and the crash test are not run yet) | TAKE-BLOCKERS.md line 47, 51; digest 150 |
| A4 | Does run (a) start Mon 16 Nov 14:00 UTC / 19:30 IST: yes/no? (If no, write the new hour in UTC and IST.) LEAD-PAGE.md ask 6 still says "LEAD FILLS". | Mon 16 Nov 13:00 UTC / 18:30 IST | if silent, run (a) moves to Tue 17 Nov 08:00 UTC / 13:30 IST and the take date stays unconfirmed | LEAD-PAGE.md lines 6, 20, 21; digest 193 |
| A5 | Which date and start time (UTC and IST) does the owner get for the take? It must reach the owner at least 3 hours before the start. | within 2 hours of the run (b) result, and before Mon 23 Nov 15:14:40 UTC / 20:44:40 IST at the latest | none; Wed 18 Nov is NOT confirmed. Last allowed message time: Mon 23 Nov 15:14:40 UTC / 20:44:40 IST | OWNER-VIEW.md line 4; TAKE-BLOCKERS.md row 4 |
| A6 | Which counts proof does the video use: a rehearsal screenshot or the Postgres node preview (decision 9 leaves it open)? | Tue 17 Nov 12:29 UTC / 17:59 IST | rehearsal screenshot | DECISIONS-2026-11-16.md item 9; digest 192 |
| A7 | Which port does the take use (decision 6 says "its own free port", no number)? Who picks it? | before run (b) | the engineering session that builds A1 picks one free port and writes it in the plan | DECISIONS item 6; digest 172, 192 |
| A8 | Name who supplies the path to `n8n_api.py` (not in this checkout): ____ . | Mon 16 Nov 18:00 UTC / 23:30 IST | if silent, the studio lead asks the owner on Tue 17 Nov; flow import cannot be tested until then | TAKE-BLOCKERS.md; digest 189 |
| A9 | Fill four things on the run-day card: how the receiver account looks (line 31), how the demo HubSpot account looks (line 59), the candidate proof screens and who films (both line 35). Will the studio lead fill all four by Tue 17 Nov 12:29 UTC / 17:59 IST: yes/no? | Tue 17 Nov 12:29 UTC / 17:59 IST | yes; the card stays unusable until then | OWNER-RUN-DAY-CARD.md lines 31, 35, 59; digest 146, 154, 157, 188, 197 |
| A10 | Replace "the take deletes" wording in v5 lines 31, 63, 114, 124, 127-130, the program's notice and prompt, drift/REPORT.md:33, drift/APPLIED-S9.md:12 and inputs/AGENT-SCOPE-DO-AND-DONT.md:20 (which says the code makes a DELETE call; check run_real_check_n8n.py:1051 too) with "the take never deletes; the owner deletes leftovers by hand" (decision 2). Who edits what? | Tue 17 Nov 12:29 UTC / 17:59 IST | core-hardening edits v5 and the program text; this session edits only its own pages | DECISIONS item 2; digest 164, 191, 195 |
| A11 | Does the Route-config check of decision 4 apply (only if the model program loads Route config; nobody has checked)? Who checks? | before run (b) | the engineering session from A1 checks and writes yes or no | DECISIONS item 4; digest 172, 192 |
| A12 | Who checks n8n's run list for stored lead data after patch F-008? | before run (b) | the engineering session from A1 | digest 192 (QUESTIONS item 7) |
| A13 | The last day allows a start before 18:14:40 UTC / 23:44:40 IST. TAKE-BLOCKERS.md line 54 uses a 4-hour rerun margin that no file sets; with it the last first-try start is 14:14:40 UTC / 19:44:40 IST. Do you set the rerun margin at 4 hours: yes/no? | Tue 17 Nov 12:29 UTC / 17:59 IST | yes | TAKE-BLOCKERS.md lines 28, 54; digest 222 |
| A14 | Define T19 inside TAKE-BLOCKERS.md (it occurs 0 times in the re-smoke plan, line 55 says so): yes/no? | Tue 17 Nov 12:29 UTC / 17:59 IST | yes (the list's terms section defines it) | TAKE-BLOCKERS.md lines 34, 55; digest 222 |

## B. Blocks only the post (Wed 25 Nov 15:00 UTC / 20:30 IST)
| # | Question | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| B1 | Apply D-04 (post says only "A lead sent twice with the same id is processed once."): yes/no? | Fri 20 Nov 12:29 UTC / 17:59 IST | yes | decisions/D04-D05.md; LEAD-PAGE.md ask 3 |
| B2 | Apply D-05 (the post waits for the crash-test result; the lead gives the limit wording): yes/no? | Fri 20 Nov 12:29 UTC / 17:59 IST | yes | decisions/D04-D05.md; digest 185 |
| B3 | Who edits step J of the owner steps file (core-hardening's file)? One name. | Fri 20 Nov 12:29 UTC / 17:59 IST | the studio lead | decisions/D04-D05.md line 9; digest 185 |
| B4 | Who accepts a crash limit in writing if the test shows a double mail: the owner or the lead? Three pages name three different people. | Fri 20 Nov 12:29 UTC / 17:59 IST | the owner accepts in writing | digest 198 (item 13) |
| B5 | Who (a person other than the author) checks the post text against the banned list? One name. | Fri 20 Nov 12:29 UTC / 17:59 IST | none | OWNER-VIEW.md row 6 |
| B6 | Does any sentence beyond "A lead sent twice with the same id is processed once." stay in the post: yes/no? | Fri 20 Nov 12:29 UTC / 17:59 IST | no | D04-D05.md line 16 |

## C. Pages that disagree (a person must pick one; no date needed beyond A10)
| # | Conflict | Source |
|---|---|---|
| C1 | banned-claims.md vs v5 step J: the banned list is stricter than step J's wording. Which wins? (Decision 1 allows one claim.) | digest 164, 183 |
| C2 | OWNER-VIEW.md line 14 says the yes holds three figures; line 21's example also holds the run name. Does the yes hold: (1) the three figures only, or (2) the three figures plus the run name? Answer 1 or 2. | digest 147, 158, 166 |
| C3 | OWNER-CLEANUP-CARD vs v5 step I: screenshot count (4 vs 3), step 6a missing from v5, "STILL WORKS" handling is opposite, retire-check command form missing on the card. Edit the card or v5? | digest 169, 182 |
| C4 | Add QUESTIONS.md entries for LP-1, LP-3, LP-5 and a map from D-01..D-05 to the 12 decisions: yes/no, and who? QUESTIONS.md has no entry for LP-1, LP-3, LP-5; D-01 to D-05 cannot be mapped to the 12 decision numbers. | digest 192, 193 |
| C5 | Mark these pages stale or fix them: yes/no, and who? (A10 covers the "take deletes" wording; this row is the rest.) Stale pages: film-v5 still filled in plan lines 120, 236, 298; C-01 still open in FINAL-CROSSCHECK lines 54, 63, 102; APPLIED-S9.md and ONE-PLACE-TABLE:183 still say "apply" for S9-1, S9-2, S9-4 (decision 5 defers them). | digest 164 |
| C6 | REPORT.md says "citations 1020 of 1020"; SWEEP.md:5 says 2013 of 2013. Which is current? | digest 176 |
| C7 | Which numbers are right for M3, M5, M14: drift/REPORT.md or the board (the board is mine and follows the last check)? The two disagree. Answer: drift/REPORT.md, board, or a named recount. | STATUS-BOARD.md; digest 150 |
| C8 | Add a Decision column to ARCHIVE-CUT-LIST: yes/no (a second question, inside or outside the repo, is C9). ARCHIVE-CUT-LIST has no Decision column and says in lines 28-30 that M and K must stay, D and E hold, L folds into the cross-check, while rows A-M still say move. Add a Decision column? And where is the archive: inside or outside the repo? | digest 173, 179 |

| C9 | Is the archive kept inside or outside the repo? Answer: inside or outside. | digest 173, 179 |

## D. Small, safe changes that need the lead's yes because the files are not mine
- Yes/no each: (D1) add a placeholder check in `tools/scan_outputs.py` (flag "[studio lead fills" and "LEAD FILLS"): digest 165.
- (D2) yes/no: add one-line "terms are defined below" pointers and a job-key legend (STORE, FILTER, RETRY, NOTICE, COUNTER, LOG, OTHER) at the top of MASTER-MAP.md, ONE-PLACE-TABLE.md and SWEEP.md: digest 175, 178, 181, 190.
- (D3) Who wrote the ORDER 028 stamp (11:31 UTC)? Name one. The stamp is later than the real clock at the time (11:15:50 UTC): who wrote it? Digest 150.

## E. Added 16 Nov after batch 199-206 (more pages read; all proposals)
| # | Question | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| E1 | Fix ORDERS.md: l.115 "no film pause" vs l.128 (pause stays); the agent count is "6+", "up to 8" and "8 to 10" in different lines; l.87 should say superseded by l.97. Who edits (the file is the lead's)? | Tue 17 Nov 12:29 UTC / 17:59 IST | the lead edits; this session keeps 8 agents | digest 204 |
| E2 | banned-claims.md: does it override v5 step J? Allow "crash-safe" only after a named result file? Add bans for "one database", "least privilege / separate logins", "the program checks the settings"? yes/no each | Fri 20 Nov 12:29 UTC / 17:59 IST | yes to all four | digest 201 |
| E3 | DECISION-one-store.md lines 1, 13, 14, 16, 20: change to "one Postgres server, two databases" (decision 10) and say the proof screen is decided (decision 9)? | Tue 17 Nov 12:29 UTC / 17:59 IST | yes | digest 201 |
| E4 | M17-end-never-deletes.md: replace the wrong quote at v5 43-44 and the shortened quote of v5 124 with the exact text. Who? | Fri 20 Nov 12:29 UTC / 17:59 IST | the lead | digest 202 |
| E5 | flowcheck/REPORT.md: who owns the two Blockers (no password on lead-intake entry points; five patches not listed) and the 8 Majors? | Tue 17 Nov 12:29 UTC / 17:59 IST | engineering session from A1 | digest 200 |
| E6 | drift/REPORT.md: correct six cite slips (D-06, D-14, D-15 and three "agree" rows)? | Fri 20 Nov 12:29 UTC / 17:59 IST | yes, core-hardening edits | digest 203 |
| E7 | MAP-ADDITIONS.md: FINAL-CROSSCHECK line count 108 to 110; show all 7 job keys; split row 009 counts. Who edits (hand-kept)? | Fri 20 Nov 12:29 UTC / 17:59 IST | the lead | digest 206 |
| E8 | REPORT.md and MASTER-MAP counts: "797 rows" is now about 812; "314 raw" vs 322. Restate with date? | Fri 20 Nov 12:29 UTC / 17:59 IST | yes | digest 199 |
| E9 | MASTER-MAP line 588 (L2-K-005) says an n8n encryption key was committed and is still in git history, and the pushed-keys Blocker in FINAL-CROSSCHECK line 33 is unchecked. Who checks whether the committed values are made-up (yes/no) and who rotates a real one? Name: ____ | Wed 18 Nov 12:29 UTC / 17:59 IST | if silent, the studio lead checks and writes yes/no; no real key is to be reused until then | MASTER-MAP.md 588; FINAL-CROSSCHECK.md 33; SWEEP.md 52; digest 243, 254 |

## F. Rows that were only in work/open-items-table.md (added 16 Nov). Each row: answer yes (owner and date as proposed) or name another owner and date. The row text is on the table line given.
| # | Open item (answer: yes, or another owner and date) | Table line | Proposed owner and date (proposal) |
|---|---|---|---|
| F1 | `$vars` use in flows | 8 | engineering session from A1, before run (b) |
| F2 | The plan's UNVERIFIED list | 10 | engineering session from A1, before run (b) |
| F3 | LP-1 shared form code | 16 | the lead, Tue 17 Nov 12:29 UTC / 17:59 IST |
| F4 | LP-3 `extract.py` (can wait) | 17 | the lead, Fri 20 Nov 12:29 UTC / 17:59 IST |
| F5 | LP-4 estimate 20 h / 41 h | 19 | the lead, Tue 17 Nov 12:29 UTC / 17:59 IST |
| F6 | LP-5 secrets / second laptop user | 20 | the lead, Tue 17 Nov 12:29 UTC / 17:59 IST |
| F7 | v3 click paths unverified | 21 | engineering session, before run (b) |
| F8 | F-002, C-01 full fix, ORDER 013 | 22 | the lead, Fri 20 Nov 12:29 UTC / 17:59 IST |
| F9 | HubSpot check line and which login key to replace (OWNER-VIEW row 7) | 7 | the lead, Tue 17 Nov 12:29 UTC / 17:59 IST |
| F10 | How the program pause shows on screen (run-day card step 17 depends on it) | 14 | engineering session, before run (b) |

## Overlaps (one answer can close several rows; proposal)
A1's answer covers A7, A11, A12 and E5. A10, C5 and E4 touch the same "take deletes" and v5 line 124 wording. A3, B2 and B4 are one crash-test question asked three ways (take blocker, post wording, who accepts). C1 and E2 ask the same banned-claims against step J question. A6 and E3 both depend on decision 9. C6 and E8 both cover REPORT.md counts; C7 and E6 both cover drift/REPORT.md.

## G. SWEEP.md decisions A-E (lines 400-423) are placeholders
SWEEP.md decisions A, B, C say "Decide by: Tue 17 Nov 18:29 UTC / 23:59 IST (placeholder)"; D and E have no deadline; the dollar limit and agent-days at lines 403-404 are blank. G1 (proposal): the lead fills the blanks and gives each of A-E a deadline in UTC and IST by Tue 17 Nov 12:29 UTC / 17:59 IST: yes/no? Source: digest 213.

## What this session did not check
Every item above comes from model reads of single pages. I verified only the few cites listed as confirmed in digests 161, 162, 170, 176, 191. The list is not complete: items on pages no agent has read yet are missing, and work/open-items-table.md and this list now cover each other (sections E and F); the A-D rows are not yet in the table.
