# Decisions the studio lead owes, one answer each
Written Mon 16 Nov 2026 by the system-map session from digest entries 143-198 (work/agent-reports-batch4.md). Reader: the studio lead. Made-up data only. Every date and every default below is MY PROPOSAL, not a fact from a file; the lead may change any of them. Where a default says "if silent", it is only what this session suggests happens when no answer comes. No item here has been run or tested.

**Top five (these hold up the first filming step):** A1 (who builds the flow-fill step), A4 (does run (a) start today), A5 (take date), A7 (port number), A8 (where `n8n_api.py` is). Everything else can wait for the times in each row.

**Who answers:** the studio lead, a Claude session, answers or passes the question to the owner. Where a row says "name", write a person or a session id. Rows in sections C and D have no answer time of their own: proposed answer time for every C and D row is Fri 20 Nov 12:29 UTC / 17:59 IST, except C2, C3, C6 and C7, which block the owner cards, so Tue 17 Nov 12:29 UTC / 17:59 IST. "Before run (b)" in section F means before Tue 17 Nov 14:00 UTC / 19:30 IST.

Words: **studio lead** = the Claude session that works with the owner. **owner** = the human. **run (a)** = the loopback re-smoke; **run (b)** = the first laptop run of real-v5 with made-up data (names used on TAKE-BLOCKERS.md line 34). **take** = the one filmed run.

Proposed answer times: items that block the filming by Tue 17 Nov 12:29 UTC / 17:59 IST (the time LEAD-PAGE.md already uses for LP-1, LP-4, LP-5); items that block only the post (Wed 25 Nov 15:00 UTC / 20:30 IST) by Fri 20 Nov 12:29 UTC / 17:59 IST. The latest filming start is Mon 23 Nov 18:14:40 UTC / 23:44:40 IST, and the start notice must come at least 3 hours before it.

## Terms used below (all proposals/readings, not new facts)
- **studio lead** = **the lead** = the one Claude session that works with the owner (same party everywhere in this list).
- **decision N** = item N in inputs/DECISIONS-2026-11-16.md (12 items). **D-04, D-05, LP-1..LP-5, S9-n, F-008, C-01** = row ids on LEAD-PAGE.md, decisions/ and drift/REPORT.md; the row text is on those pages.
- **T19** = the planned test that sends one lead twice and expects one processing; **crash test** = the planned test that stops n8n mid-run and restarts it; neither has run. **"rehearsal passed"** = the result file of a rehearsal run with every row PASS (the owner's card requires the studio lead to say it). **rerun margin** = the time kept free after a take's start so one failed take can be repeated (proposed: 4 hours). **engineering session** = a Claude session that does the technical steps.
- **mail-crash test** = the crash test (above) as it applies to the mail step. **loopback re-smoke** = run (a): the second smoke run on the studio lead's own machine where every service answers only on 127.0.0.1. **Route config** = a settings item from decision 4 that I could not find explained in any file I read; ask core-hardening. **board** = STATUS-BOARD.md. **owner cards** = OWNER-RUN-DAY-CARD.md and OWNER-CLEANUP-CARD.md. **M3, M5, M14** = rows of STATUS-BOARD.md.
- **step J** = the "post" step of inputs/OWNER-STEPS-realrun-v5-core-hardening.md. **core-hardening** = the other cloud session that owns that file.
- **digest N** = numbered entry N in work/agent-reports-batch4.md (the reasoning behind a row).
- **Proposed run dates (mine):** run (a) Mon 16 Nov 14:00 UTC / 19:30 IST if the lead agrees today; run (b) Tue 17 Nov 14:00 UTC / 19:30 IST; start-notice deadline for the last-day take: Mon 23 Nov 15:14:40 UTC / 20:44:40 IST.
- "If silent: none" means no fallback is proposed; filming stays blocked until someone answers. Every such item is answered or escalated to the owner by Fri 20 Nov 12:29 UTC / 17:59 IST at the latest (proposal).

**Escalation rule (proposal):** if a filming blocker (section A) has no answer by Tue 17 Nov 12:29 UTC / 17:59 IST, the lead asks the owner the same day; no answer by Wed 18 Nov 12:29 UTC / 17:59 IST means no take is scheduled before the next answer. The take date can never pass Mon 23 Nov (latest start 18:14:40 UTC / 23:44:40 IST).
**Two meanings of "run (a)":** this list uses run (a) = loopback re-smoke (TAKE-BLOCKERS.md line 34). LEAD-PAGE.md line 13 uses it for the stand-in rehearsal. A2 asks the lead to say which one the rule "rehearsal passed" means.
**Crash test and the take:** LEAD-PAGE.md says D-05 blocks the post, not the take; A3 asks whether the crash test is also required before the take. If the lead answers no, A3 closes and B2 stays.

## A. Blocks the filming
| # | Question (yes/no or a name) | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| A1 | Name the builder of the flow-fill step (`fill_flows.py`; the filled, patched real-v5 copy is not built, see TAKE-BLOCKERS.md line 33): ____ . | Mon 16 Nov 18:00 UTC / 23:30 IST | if no name by then, the studio lead starts one engineering session at once and reports its start time in the plan, with finish Tue 17 Nov 12:29 UTC / 17:59 IST (a person or a session, either is accepted) | TAKE-BLOCKERS.md row 1 (line 33); LEAD-PAGE.md ask 1; digest 155, 189, 193 |
| A2 | Does the rule "rehearsal passed" cover run (a), run (b) or both? | Tue 17 Nov 12:29 UTC / 17:59 IST | both | TAKE-BLOCKERS.md line 34; LEAD-PAGE.md ask 2; digest 189 |
| A3 | Is the mail-crash test required before the take: yes/no? If yes, name who runs it and when (UTC and IST). | Tue 17 Nov 12:29 UTC / 17:59 IST | yes, run by the engineering session from A1 before run (b) ends (T19 and the crash test are not run yet) | TAKE-BLOCKERS.md line 47, 51; digest 209, 220 |
| A4a | Does run (a) start Mon 16 Nov 14:00 UTC / 19:30 IST: yes/no? (A4b, if A4a is no: write the new start in UTC and IST. Decision 12 says the first laptop rehearsal is "tonight or tomorrow morning IST"; this row only checks my proposed hour.) LEAD-PAGE.md ask 6 still says "LEAD FILLS". | Mon 16 Nov 13:00 UTC / 18:30 IST | if silent, run (a) moves to Tue 17 Nov 08:00 UTC / 13:30 IST, six hours before run (b) at 14:00 UTC; run (b) then starts only if run (a) has passed, otherwise it waits; the take date stays unconfirmed | LEAD-PAGE.md lines 10, 20, 21; digest 193 |
| A5 | Name the take date and start time (give both in UTC and IST), or write "no take yet". It must reach the owner at least 3 hours before the start. | Tue 17 Nov 12:29 UTC / 17:59 IST (the same time as the escalation rule above), and in any case before Mon 23 Nov 15:14:40 UTC / 20:44:40 IST | none; Wed 18 Nov is NOT confirmed. Last allowed message time: Mon 23 Nov 15:14:40 UTC / 20:44:40 IST | OWNER-VIEW.md line 4; TAKE-BLOCKERS.md row 4 |
| A6 | Is the video's proof of the contact count the rehearsal screenshot: yes/no? (A "counts proof" is the screen that shows the 3 contacts; no means the screen of n8n's Postgres node preview instead; decision 9 leaves it open.) | Tue 17 Nov 12:29 UTC / 17:59 IST | rehearsal screenshot | DECISIONS-2026-11-16.md item 9; digest 192 |
| A7 | Port number for the take (decision 6 says "its own free port" and gives no number): ____ . | Tue 17 Nov 13:00 UTC / 18:30 IST (1 hour before run (b)) | if silent, no run starts until a number is written in the plan; the engineering session from A1 may propose a free one but the lead writes it | DECISIONS item 6; digest 172, 192 |
| A8 | Name who supplies the path to `n8n_api.py` (not in this checkout): ____ . | Mon 16 Nov 18:00 UTC / 23:30 IST | if silent, the studio lead asks the owner on Tue 17 Nov; flow import cannot be tested until then | TAKE-BLOCKERS.md; digest 189 |
| A9 | Fill four things on the run-day card: how the receiver account looks (line 31), how the demo HubSpot account looks (line 59), the candidate proof screens and who films (both line 35). Yes/no for all four: will the studio lead fill each of them by Tue 17 Nov 12:29 UTC / 17:59 IST? If any is no, write which one and a new time. | Tue 17 Nov 12:29 UTC / 17:59 IST | yes; the card stays unusable until then | OWNER-RUN-DAY-CARD.md lines 31, 35, 59; digest 154, 157, 188, 197 |
| A10 | FYI (decision 2 already settles the wording; the only open part is who edits: yes/no, core-hardening does it). Replace "the take deletes" wording in v5 lines 31, 63, 114, 124, 127-130, the program's notice and prompt, drift/REPORT.md:33, drift/APPLIED-S9.md:12 and inputs/AGENT-SCOPE-DO-AND-DONT.md:20 (which says the code makes a DELETE call; check run_real_check_n8n.py:1051 too) with "the take never deletes; the owner deletes leftovers by hand" (decision 2). Does core-hardening edit v5 and the program text: yes/no? | Tue 17 Nov 12:29 UTC / 17:59 IST | core-hardening edits v5 and the program text; this session edits only its own pages | DECISIONS item 2; digest 164, 191, 195 |
| A11 | FYI (decision 4 makes this check conditional). Does the engineering session from A1 check whether the model program loads Route config (decision 4): yes/no? | Tue 17 Nov 13:00 UTC / 18:30 IST | yes; the session writes yes or no in the plan | DECISIONS item 4; digest 172, 192 |
| A12 | Does the engineering session from A1 check n8n's run list for stored lead data after patch F-008: yes/no? | Tue 17 Nov 13:00 UTC / 18:30 IST | yes | digest 192 (QUESTIONS item 7) |
| A13 | The last day allows a start before 18:14:40 UTC / 23:44:40 IST. TAKE-BLOCKERS.md line 54 uses a 4-hour rerun margin that no file sets; with it the last first-try start is 14:14:40 UTC / 19:44:40 IST. Do you set the rerun margin at 4 hours: yes/no? | Tue 17 Nov 12:29 UTC / 17:59 IST | yes | TAKE-BLOCKERS.md lines 28, 54; digest 222 |
| A14 | FYI (this is an edit task, done by me in the terms section above). Define T19 inside TAKE-BLOCKERS.md (it occurs 0 times in the re-smoke plan, line 55 says so): yes/no? | Tue 17 Nov 12:29 UTC / 17:59 IST | yes (the list's terms section defines it) | TAKE-BLOCKERS.md lines 34, 55; digest 222 |

## B. Blocks only the post (Wed 25 Nov 15:00 UTC / 20:30 IST)
| # | Question | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| B1 | Apply D-04 (post says only "A lead sent twice with the same id is processed once."): yes/no? | Fri 20 Nov 12:29 UTC / 17:59 IST | yes | decisions/D04-D05.md; LEAD-PAGE.md ask 3 |
| B2 | Apply D-05 (the post waits for the crash-test result; the lead gives the limit wording): yes/no? | Fri 20 Nov 12:29 UTC / 17:59 IST | yes | decisions/D04-D05.md; digest 185 |
| B3 | Who edits step J of the owner steps file (core-hardening's file)? One name. | Fri 20 Nov 12:29 UTC / 17:59 IST | the studio lead | decisions/D04-D05.md line 9; digest 185 |
| B4 | Who accepts a crash limit in writing if the test shows a double mail: the owner or the lead? Three pages name three different people. | Fri 20 Nov 12:29 UTC / 17:59 IST | the owner accepts in writing, in the chat with the studio lead (no other channel is named in any file) | digest 198 (item 13) |
| B5 | Who (a person other than the author) checks the post text against the banned list? One name. | Fri 20 Nov 12:29 UTC / 17:59 IST | the post is held until a name is written (nobody posts unchecked) | OWNER-VIEW.md row 6 |
| B6 | (Same question as B1, kept for the record; answer B1 only.) Does any sentence beyond "A lead sent twice with the same id is processed once." stay in the post: yes/no? | Fri 20 Nov 12:29 UTC / 17:59 IST | no | D04-D05.md line 16 |

## C. Pages that disagree (a person must pick one; answer by the time in the "Who answers" line above: Fri 20 Nov 12:29 UTC / 17:59 IST, except C2, C3, C6, C7 on Tue 17 Nov 12:29 UTC / 17:59 IST)
| # | Conflict | Source |
|---|---|---|
| C1 | banned-claims.md vs v5 step J: the banned list is stricter than step J's wording. Which wins? (Decision 1 allows one claim.) | digest 73, 134, 262, 268 |
| C2 | OWNER-VIEW.md line 14 says the yes holds three figures; line 21's example also holds the run name. Does the yes hold: (1) the three figures only, or (2) the three figures plus the run name? Answer 1 or 2. | digest 158, 207 |
| C3 | OWNER-CLEANUP-CARD vs v5 step I: screenshot count (4 vs 3), step 6a missing from v5, "STILL WORKS" handling is opposite, retire-check command form missing on the card. Edit the card or v5? | digest 169, 182 |
| C4 | Add QUESTIONS.md entries for LP-1, LP-3, LP-5 and a map from D-01..D-05 to the 12 decisions: yes/no, and who? QUESTIONS.md has no entry for LP-1, LP-3, LP-5; D-01 to D-05 cannot be mapped to the 12 decision numbers. | digest 141, 149, 272 |
| C5 | Mark these pages stale or fix them: yes/no, and who? (A10 covers the "take deletes" wording; this row is the rest.) Stale pages: film-v5 still filled in plan lines 120, 236, 298; C-01 still open in FINAL-CROSSCHECK lines 54, 63, 102; APPLIED-S9.md and ONE-PLACE-TABLE:183 still say "apply" for S9-1, S9-2, S9-4 (decision 5 defers them). | digest 164 |
| C6 | REPORT.md says "citations 1020 of 1020"; SWEEP.md:5 says 2013 of 2013. REPORT.md also says 2013 of 2013 at line 97 (1020 is a run on SWEEP.md and ONE-PLACE-TABLE.md, lines 31, 40). Which is current? | digest 176 |
| C7 | Which numbers are right for M3, M5, M14: drift/REPORT.md or the board (the board is mine and follows the last check)? The two disagree. Answer: drift/REPORT.md, board, or a named recount. | STATUS-BOARD.md; digest 152, 218 |
| C8 | Add a Decision column to ARCHIVE-CUT-LIST: yes/no (a second question, inside or outside the repo, is C9). ARCHIVE-CUT-LIST has no Decision column and says in lines 28-30 that M and K must stay, D and E hold, L folds into the cross-check, while rows A-M still say move. Add a Decision column? And where is the archive: inside or outside the repo? | digest 173, 179 |

| C9 | Is the archive kept inside or outside the repo? Answer: inside or outside. | digest 173, 179 |

## D. Small, safe changes that need the lead's yes because the files are not mine
- Yes/no each: (D1) add a placeholder check in `tools/scan_outputs.py` (flag "[studio lead fills" and "LEAD FILLS"): digest 165.
- (D2) yes/no: add one-line "terms are defined below" pointers and a job-key legend (STORE, FILTER, RETRY, NOTICE, COUNTER, LOG, OTHER) at the top of MASTER-MAP.md, ONE-PLACE-TABLE.md and SWEEP.md: digest 175, 178, 181, 190.
- (D3) Answer by Fri 20 Nov 12:29 UTC / 17:59 IST (a question of fact, not a decision). Who wrote the 11:31 UTC time stamp inside ORDER 028 (ORDERS.md, the last order in the file)? Name one. The stamp is later than the real clock at the time (11:15:50 UTC): who wrote it? Digest 150.

## E. Added 16 Nov after batch 199-206 (more pages read; all proposals)
| # | Question | Proposed answer by | Proposed default if silent | Source |
|---|---|---|---|---|
| E1 | Fix ORDERS.md: l.115 "no film pause" vs l.128 (pause stays); the agent count is "6+", "up to 8" and "8 to 10" in different lines; l.87 should say superseded by l.97. Who edits (the file is the lead's)? | Tue 17 Nov 12:29 UTC / 17:59 IST | the lead edits; this session keeps 8 agents | digest 204 |
| E2 | banned-claims.md: does it override v5 step J? Allow "crash-safe" only after a named result file? Add bans for "one database", "least privilege / separate logins", "the program checks the settings"? yes/no each | Fri 20 Nov 12:29 UTC / 17:59 IST | yes to all four | digest 201 |
| E3 | inputs/DECISION-one-store.md (the root copy is stale, digest 263) lines 1, 14, 17: change to "one Postgres server, two databases" (decision 10) and say the proof screen is decided (decision 9)? | Tue 17 Nov 12:29 UTC / 17:59 IST | yes | digest 201 |
| E4 | M17-end-never-deletes.md: replace the wrong quote at v5 43-44 and the shortened quote of v5 124 with the exact text. Who? | Fri 20 Nov 12:29 UTC / 17:59 IST | the lead | digest 202 |
| E5 | flowcheck/REPORT.md: who owns the two Blockers (no password on lead-intake entry points; five patches not listed) and the 8 Majors? | Tue 17 Nov 12:29 UTC / 17:59 IST | engineering session from A1 | digest 200 |
| E6 | drift/REPORT.md: correct six cite slips (D-06, D-14, D-15 and three "agree" rows)? | Fri 20 Nov 12:29 UTC / 17:59 IST | yes, core-hardening edits | digest 203 |
| E7 | MAP-ADDITIONS.md: FINAL-CROSSCHECK line count 108 to 110; show all 7 job keys; split row 009 counts. Who edits (hand-kept)? | Fri 20 Nov 12:29 UTC / 17:59 IST | the lead | digest 206 |
| E8 | REPORT.md and MASTER-MAP counts: "797 rows" is now about 812; "314 raw" vs 322. Restate with date? | Fri 20 Nov 12:29 UTC / 17:59 IST | yes | digest 199 |
| E9 | MASTER-MAP line 588 (L2-K-005) says an n8n encryption key was committed and is still in git history, and the pushed-keys Blocker in FINAL-CROSSCHECK line 33 is unchecked. Who checks whether the committed values are made-up (yes/no) and who rotates a real one? Name: ____ | Wed 18 Nov 12:29 UTC / 17:59 IST | if silent, the studio lead checks and writes yes/no; no real key is to be reused until then | MASTER-MAP.md 588; FINAL-CROSSCHECK.md 33; SWEEP.md 52; digest 243, 254 |

## F. Rows that were only in work/open-items-table.md (added 16 Nov). Each row: answer yes (owner and date as proposed) or name another owner and date. The row text is on the table line given.
| # | Open item (answer: yes, or another owner and date) | Table line | Proposed owner and date (proposal) |
|---|---|---|---|
| F1 | Decide who checks that the flows read their settings through the allowed route (`$vars` in the flow files) | 9 | engineering session from A1, before run (b) |
| F2 | Decide who works through the re-smoke plan's list of items marked UNVERIFIED | 11 | engineering session from A1, before run (b) |
| F3 | LP-1: decide whether the web form needs a shared secret code | 17 | the lead, Tue 17 Nov 12:29 UTC / 17:59 IST |
| F4 | LP-3: decide what to do with `extract.py` (can wait until after the take) | 18 | the lead, Fri 20 Nov 12:29 UTC / 17:59 IST |
| F5 | LP-4: the 20 h / 41 h estimate predates the real-v5-only scope (decision 1); confirm it is dropped | 20 | the lead, Tue 17 Nov 12:29 UTC / 17:59 IST |
| F6 | LP-5: decide between accepting the secrets-on-one-laptop risk and a second laptop user (decision 5 settles what the lead reads) | 21 | the lead, Tue 17 Nov 12:29 UTC / 17:59 IST |
| F7 | The click paths in v3 are unverified; v4 and later replace v3 (decision 10), so confirm they are dropped | 22 | engineering session, before run (b) |
| F8 | Decide the open parts of F-002 (a generator patch), ORDER 013 (C-01 itself is cut by decision 4) | 23 | the lead, Fri 20 Nov 12:29 UTC / 17:59 IST |
| F9 | Send the owner the HubSpot check line and name which login key to replace (OWNER-VIEW row 7) | 8 | the lead, Tue 17 Nov 12:29 UTC / 17:59 IST |
| F10 | Say how the film pause shows on screen (run-day card step 17 depends on it) | 15 | engineering session, before run (b) |

## Overlaps (one answer can close several rows; proposal)
A1's answer covers A7, A11, A12 and E5. A10, C5 and E4 touch the same "take deletes" and v5 line 124 wording. A3, B2 and B4 are one crash-test question asked three ways (take blocker, post wording, who accepts). C1 and E2 ask the same banned-claims against step J question. A6 and E3 both depend on decision 9. C6 and E8 both cover REPORT.md counts; C7 and E6 both cover drift/REPORT.md.

## G. SWEEP.md decisions A-E (lines 400-423) are placeholders
SWEEP.md decisions A, B, C say "Decide by: Tue 17 Nov 18:29 UTC / 23:59 IST (placeholder)"; D says only "after Wed 18 Nov 2026" (SWEEP.md:420) and E has no deadline (line 423); the dollar limit and agent-days at lines 403-404 are blank. G1 (proposal): the lead fills the blanks and gives each of A-E a deadline in UTC and IST by Tue 17 Nov 12:29 UTC / 17:59 IST: yes/no? Source: digest 213.

## What this session did not check
Every item above comes from model reads of single pages. I verified only the few cites listed as confirmed in digests 161, 162, 170, 176, 191. The list is not complete: items on pages no agent has read yet are missing, and work/open-items-table.md and this list now cover each other (sections E and F); the A-D rows are not yet in the table.
