# runbook-changelog: round history moved out of RUNBOOK.md (round 54, fix-runbook54.md)
Saved verbatim from RUNBOOK.md; history only, no step depends on it. Figures here are those of their own round and may be out of date.

## Status paragraph of RUNBOOK.md before round 54 (line 3)

Status: STATIC READ, newest fix round 48 of this file (log reviews/fix-runbook48.md; step 16 was rewritten as a numbered sequence, the contact count is now 12, and the Tuesday positive control uses the keysave word 19t); the round 41 edits stay (log reviews/fix-planfiles41.md; round 39 is in reviews/fix-planfiles39.md, round 38 in reviews/fix-planfiles38.md, and no file reviews/fix-planfiles40.md exists (checked with ls on 2026-11-16), so the edits tagged round 40 in the text below have no log of their own; the rounds 26 to 37 are in reviews/fix-planfiles26.md to fix-planfiles37.md (the even rounds 27, 29 and 31 are in the older fix logs), the rounds 13 to 25 are in their own fix logs in reviews/; the round numbers further down (round 30, round 32, round 33) are older rounds of this file, not newer than this one, and the text below keeps the history of rounds 2 to 12 first). Round 12 (log fix-tcfp8.md) applies reviews/runbook-tc-fp-r12-consistency.md and reviews/fp-tc-stranger-r12.md on the RUNBOOK side (M3, M4, M5, M7, M8; section 1 failure 24 says which were confirmed). Round 2 (log fix-runbook2.md) was written BEFORE the lead answers of ORDERS.md lines 159 to 171; round 3 (log fix-runbook3.md) applied the NOTE about the short re-smoke (line 160), Q28 (line 166), Q29 (line 167) and Q30 (line 171); round 4 (log fix-runbook4.md) applies the readiness review reviews/readiness-runbook-r3.md (B1 to B3, M1 to M10) and the four nits of reviews/citations-runbook-r3.md, each checked against this file, ORDERS.md lines 105 to 171, take_check.sh and the cited files before it was applied. Round 5 (log fix-runbook5.md) applies the section "RUNBOOK.md readiness round 5" of reviews/round-12z-findings.md (B1, B2, M1 to M9, the minors and the nits); each finding was checked against take_check.sh, ORDERS.md, OWNER-STEPS-q16-rows.md and TAKE-CHECKLIST.md before it was applied, and failure 15 says which were confirmed. Round 6 (log fix-runbook6.md) applies section A of reviews/round-16z-findings.md (M1 to M5 and the minors) and ORDER 037 item 3 (ORDERS.md lines 176 to 177: ONE filled flow set with the real trial-account credential in every phase; the stand-in HubSpot swap is dropped); each finding was checked against this file and TAKE-CHECKLIST.md before it was applied, and failure 18 says which were confirmed. Round 7 (log fix-runbook6.md) applies reviews/runbook-r7-findings.md and two coordinator findings (the `sed -i` pin line replaced by the TAKE-CHECKLIST python3 block; the step 14 (c) count already refuses a missing sentence, checked in the text: `lines=0` fails) (B1, M1 to M10, N1 to N9); failure 19 says which were confirmed. Round 9 (log fix-runbook6.md) applies reviews/runbook-r9-findings.md (B1, M1 to M5, N1 to N5), each checked against this file, TAKE-CHECKLIST.md and FINDINGS.md F-002 "T21 METHOD" first; failure 21 says which were confirmed. Round 10 (log fix-runbook6.md) applies reviews/runbook-r10-findings.md (M1 to M9), each checked against this file, TAKE-CHECKLIST.md and FINDINGS.md F-002 first; failure 22 says which were confirmed. Round 11 (log fix-runbook6.md) applies reviews/runbook-r11-findings.md (M1 to M3, N1 to N7) and the RUNBOOK side of reviews/tcfp-r11-findings.md (M1, M2, M7); failure 23 says which were confirmed. Every input only the lead can supply is now written `LEAD FILLS: <exact input>` in its step and listed once in the table of section 10. Nothing here was run; no command was tried; n8n never ran. Every command is copied or joined from a file named in the "Sources" line; a command marked "(mine)" is written by this audit and found in no file. Where no file holds the command, the cell says `LEAD FILLS: <what>` and says what it must do. Made-up data only; no secret value is printed or written here. Written 2026-11-16 (Mon). The lead said (ORDERS.md line 170) that the clock stamps of his earlier ORDERS blocks (13:00Z (18:30 IST) to 15:00Z (20:30 IST)) are wrong, so this file names each answer by its question number and ORDERS.md line, never by a stamp, and uses only the dated schedule values (re-pin Tue 17 Nov about 08:00 UTC (13:30 IST), GO / NO-GO Tue 17 Nov 14:00 UTC (19:30 IST), the Wednesday values, the Monday 23 Nov limits). Times: UTC first, then IST (IST = UTC + 5 h 30 min). Every minute figure is an ESTIMATE by this audit (not measured, not a promise); the arithmetic is shown in section 6.

## Section 1 item 2 (was [HISTORY])

2. [HISTORY] **Placeholder greps in round 1 were wrong and passed for the wrong reason.** `grep -rlE 'A\|B'` treats `\|` as a plain pipe character, so it finds nothing and "prints nothing" is true on any folder. Checked read-only on the committed folder handover/demo/n8n-flows-real-v5 (2026-11-16): the `\|` form printed nothing; the plain `A|B` form listed mf-form.json, mf-recovery.json, mf-hook.json and mf-sub-crm-mail.json (plus two non-flow files there). This runbook uses the plain form and a control that must list the four files of the unfilled folder (steps 10 and 18 of section 5).

## Section 1 item 10 (was [HISTORY])

10. [HISTORY] **Not checked by this audit:** whether the four patches still apply to the committed tree today (`check_patches.sh` was not run); whether `build_mainframe.py` still reproduces real-v5; whether fill_flows and take_check run on the lead's laptop; every n8n screen, setting name and port; the real HubSpot reply; the file DECISIONS-2026-11-16.md wording beyond items 1 to 12 as read; every duration below; whether `egm/tools/ledger_check.py` and the ledger topic exist (they are in the studio folder, not read here).

## Section 1 item 11 (was [HISTORY])

11. [HISTORY] **Caption wording is joined by this audit, not quoted.** Q28-1 (line 166) gives only the phrase "one e-mail message in the intake mailbox". The full sentence used below, `In this recording, the same lead ID sent twice gave one e-mail message in the intake mailbox.`, joins it to the Q25-2 sentence; the lead confirms it word for word (I35). Step 14 (c) greps for exactly this sentence, so a different wording breaks that grep.

## Section 1 item 12 (was [HISTORY])

12. [HISTORY] **Added in round 3, all estimates by this audit and not measured:** the 10 min of step 19a (positive control), the raise of step 14 from 20 to 30 min, and the arithmetic of sections 6 and 8 that depends on them. The meaning of the "recount" in Q29-2 is read as: the mailbox is counted after the stated wait and counted again once more; the time between the two counts is not given (I20).

## Section 1 item 14 (was [HISTORY])

14. [HISTORY] **Not checked in round 4:** that the F-003 and F-004 patches change only the two markdown files (checked only by `grep -n '^diff --git'` on both patch files); the output format of `egm/tools/ledger_check.py` and the real ledger (the `egm/` folder is not in this checkout, so the step 17 filter is unverified); whether the studio folder and the take scripts exist at all; every estimate of section 6 (mine, not measured); the new writing and review times (estimates). The sums of section 6 were re-run with python3 (output pasted in fix-runbook4.md); nothing was run in n8n.

## Section 1 item 15 (was [HISTORY])

15. [HISTORY] **Round 5: what the review said and what was found (each checked in the named file; nothing was run).** B1 CONFIRMED: the FINAL line of take_check.sh (its last line) prints `status $RC. Flow files sha256 (four files, combined): $FLOWSHA. RESULT: ...`, so the old one-pattern grep never matched; steps 5 and 13 now use two greps. B2 CONFIRMED: take-warns.pin line 2 reads "reviewed by: flows-audit session ... lead to confirm" and take_check.sh exits 4 on any reviewer line that holds "session" or "lead to confirm" or is not `NAME, YYYY-MM-DD`; `--write-warn-pin` writes a PLACEHOLDER line (exit 4 too); new step 4b and step 13 (d) fix that; EXTRA found in the same script: the pin also holds the sha256 of the four flow files, and the unfilled copy of step 3 is a NEW folder, so pin 1 may need rewriting (step 4b (d)). M1 CONFIRMED as a gap (no file read says how the same imported flows reach a stand-in and then the real HubSpot): section "Which services each step talks to" (renamed in round 6, now "One filled flow set") and I43. M2 CONFIRMED: step 22 now holds the apply step and the recording test, with times (I44). M3 CONFIRMED: step 14 (a) now holds the re-read commands and pass lines; the NEW wording of F-007 and F-028 is not in any file: LEAD FILLS (I34). M4 CONFIRMED: ORDERS.md line 156 item 2 and OWNER-STEPS row 6 say once, at take prep, Wednesday about 07:00 UTC (12:30 IST); moved from step 15 to step 19. M5 CONFIRMED: OWNER-STEPS item 3 (line 78) says the comparison comes before the take, reply by 09:45 UTC (15:15 IST); moved to step 24 (g). M6 CONFIRMED: one watch, step 29, 20 min, budgeted. M7 CONFIRMED (and it is a question for the lead, not a fact): I41 and I42. M8 CONFIRMED, my figures differ from the reviewer's (the reviewer left out step 17 and step 4b): sections 3 and 6. M9 CONFIRMED: step 6 and step 7. Minors and nits CONFIRMED: the stale "ignore the INFO sentence" text is gone (the script no longer prints it; checked), failure 13 is completed (j to p), I-numbers added, step 14 (c) now matches TAKE-CHECKLIST "Words on screen", step 13 (c) no longer hides its output, the I-table gaps are closed (I2, I10, I38, I45), the rows of section 7 are labelled RC1 to RC15 (not R1 to R11: "R" plus a number already means a bible rule in this studio, and there are 15 rows), and the 171-min repeat was an overestimate (steps 6 to 8 are not repeated when only the flow files change); the repeat is now 146 min (steps 3, 4, 4b, 5, 9 to 13).

## Section 1 item 17 (was [HISTORY])

17. [HISTORY] **Round 5: not checked.** Whether the pin's flows sha256 line (989f5529...) equals the sha of the regenerated unfilled folder (take_check.sh was not run; step 4b decides it at the re-pin); whether `/healthz/readiness` exists in the n8n version of the take (named only in inputs/plan-wp6-resmoke-v5.md); whether the exported flow files carry an `active` flag that take_check.sh minds (step 22); every new minute figure (mine; arithmetic in section 6, re-run with python3 and pasted in fix-runbook5.md).

## Section 1 item 18 (was [HISTORY])

18. [HISTORY] **Round 6: what the review said and what was found (each checked against this file and TAKE-CHECKLIST.md; nothing was run).** M1 CONFIRMED: take_check pins the sha256 of the four flow files (step 4b (d), step 13 (b)), so after pin 2 any new export with other bytes exits 4 on the pin; the repeat is now the whole of step 13 (a) to (f) with export-N, a new pin file and the named reader (steps 13, 16, 18, 24 (f), I36). M2 CONFIRMED: step 24 (f) was in no minute figure and the recommended default (recovery off, step 22 (ii)) edits the INSTANCE after step 13; two ways out are now written: leave the recovery flow inactive from step 11 when the lead decides before step 11 (no edit later, 0 min), or count the 10 + 45 min (section 6, three cases). M3 CONFIRMED: only step 24 held the start-state gate although TAKE-CHECKLIST check 14 and FIX-PLAN item 3 step 14 want it before every send; it is now named in section 2 and in steps 16, 18, 19, 19a, 21, 23, with 4 min each (mine) in section 6. M4 CONFIRMED: step 17 now holds the commands of TAKE-CHECKLIST Tuesday GO rows 1, 2, 3 and 7 (copied, not invented). M5 PARTLY CONFIRMED: the status checks of steps 1, 4 and 4b were already limited to folders, not to named paths, so they are narrowed further; step 2 used plain `git diff --stat` (fixed); the greps of step 14 (a) lacked `-i` (fixed); the third command of step 14 (c) printed 0 when the sentence was missing (replaced with the awk form of TAKE-CHECKLIST "Words on screen"). Minors CONFIRMED: step 13 (d) lacked cp, git add and git commit (added); "round 5" in the header and "234 min" in section 6 (the 234 of the sentence "It is not part of the 234 min" was stale; the other "234" is the round-4 figure and stays); the reader is needed by 04:26 UTC (I36) but TAKE-CHECKLIST says about 08:00 UTC (13:30 IST) (listed in section 9; this file is the clock source). ORDER 037 item 3 APPLIED: step 16 option (ii) (a throw-away n8n running mf.py flows) and the table row and text that kept the rehearsals out of the real HubSpot are removed; every phase now uses the one filled copy and the real trial-account credential, which means every send leaves a made-up contact (section "One filled flow set", I43). Not checked: the minutes added in round 6 (the gate 4 min, the re-export 45 min) are mine and were not measured.

## Section 1 item 19 (was [HISTORY])

19. [HISTORY] **Round 7: what the review said and what was found (each checked against this file and TAKE-CHECKLIST.md; nothing was run).** B1 CONFIRMED: steps 4, 4b and 13 commit onto the branch of step 1, so HEAD is not `$FINAL_SHA`, and the edits of steps 4a and 14 were never committed; now two names (`$BRANCH` with `$FINAL_SHA` for the evidence, `$PATCH_BRANCH` for every re-pin commit; TAKE-CHECKLIST Inputs-list item 18 (a) keeps them as two names), a commit in steps 4a and 14 (g), and step 17 (3) tests "ancestor and only non-code paths changed". M1 CONFIRMED: the two-script review is a GO row 2 item, reported about 10:30 UTC (16:00 IST) Tuesday; Wednesday 05:30 UTC (11:00 IST) is only the latest for the take program; the re-smoke starts before the branch exists, so it posts with the checklist's own stored-body loop. M2 CONFIRMED and fixed in section 10 (I10, I17, I19, I20, I21, I41, I43). M3 CONFIRMED (step 16 and I9). M4 CONFIRMED: the gate script is now in the writing time (W-Tue 150 -> 170 min), the first use is step 16, and leftover rows are cleaned before a gate. M5 CONFIRMED: step 16 now needs the log with exactly 2 posts of identical bytes. M6 CONFIRMED: section 6 states the budget with a second re-smoke (a repeat after a failed first re-smoke has 170 - 146 - 60 = -36 min, so it is NO-GO on Tuesday; the step 1 limits become 635 and 665 min) and section 8 uses the 127-min block. M7 CONFIRMED: I48, I49 and the extended I5, I34, I39. M8 CONFIRMED, and round 8 (M7) corrects it: `REVOKE CONNECT` alone changes nothing (PUBLIC holds CONNECT) and does not end open sessions; the tested T21 method is `ALTER ROLE ... NOLOGIN` plus `pg_terminate_backend`, a proof that a login prints `not permitted to log in`, then `ALTER ROLE ... LOGIN` (FINDINGS.md F-002 "T21 METHOD"). M9 CONFIRMED (step 8 now needs the words `permission denied`). M10 CONFIRMED (the F-003 and F-004 patches are applied at the start of step 4a, before any hand edit of the run sheet). N1 to N9 CONFIRMED and fixed (N9: step 1 compared `--show-toplevel` with `$REPO` as text; a symlinked path would fail; now `pwd -P`). Not checked: take_check.sh, fill_flows, OWNER-STEPS, N7-verdicts section C, patches (as in the review); the new minutes are mine.

## Section 1 item 20 (was [HISTORY])

20. [HISTORY] **Round 8: what the review said and what was found (each checked against this file, TAKE-CHECKLIST.md and FINDINGS.md F-002 "T21 METHOD"; nothing was run).** B1 CONFIRMED: no command created `$PATCH_BRANCH` and nothing set `$FINAL_SHA` (step 1 now creates the branch from it and a set-once block in section 4 holds the names; step 1 needs the final evidence). M1 to M7, m1 to m9 and the nits CONFIRMED and fixed (M1 guard and count of Block R1; M2 `HTTP 200` count; M3 Block R7 instead of a home-made grep; M4 `JUDGED` lines and a `test` for the head; M5 step 6 in a Tuesday set and a Wednesday set; M6 the S9-2 message moves to the start of step 23; M7 the T21 method). M8 is a TAKE-CHECKLIST edit and is listed in the report of round 8, not done here. Not checked: take_check.sh, check_flows.py, fill_flows, the patches, CLAIMS-TABLE, OWNER-STEPS, FIX-PLAN (as in the review); all new minutes and clock times of round 8 are mine and recomputed only where noted.

## Section 1 item 21 (was [HISTORY])

21. [HISTORY] **Round 9: what the review said and what was found (each checked against this file, TAKE-CHECKLIST.md and FINDINGS.md F-002 "T21 METHOD"; nothing was run).** B1 CONFIRMED: the set-once block held `<...>` placeholders (a redirect in bash) and lacked LOG, LOG2, STUDIO, KEEP, TOOL, EXPORT, TAKE_TREE, RUNSHEET, RECORDING, FLOWS_ROLE, PGADMIN, FLOWS_PW and ENVSH, and nothing set TAKE_FOLDER before the file could be found; section 4 now holds a literal `shas.env` skeleton (every name assigned in double quotes) and a one-line bootstrap typed by hand. M1 CONFIRMED (all four points; F-002 puts LOGIN before the resend): step 18 now holds the six numbered T21 commands, with `PGPASSWORD`, `-d` and `-U`, the pass line `done`, and the rule "a 200 on the cut send = T21 INVALID"; the port name is `N8N_PORT` in both files. M2 CONFIRMED: step 4b (c) writes the python3 call with `"$PIN_FILE"`. M3 CONFIRMED: every silent pass line named in the review now prints a word or a count. M4 CONFIRMED: step 16 expects 2, 2, 2, 1 in that order and the dangling sentence is gone. M5 CONFIRMED: one visible shortfall line opens section 5; no clock changed. N1 to N5 CONFIRMED and fixed (N5: (g) is now last). Not checked: nothing was run; the skeleton was tested only with `bash -n` and a source in a scratch folder; the six T21 commands are copied from FINDINGS.md and were not run against n8n.

## Section 1 item 22 (was [HISTORY])

22. [HISTORY] **Round 10: what the review said and what was found (each checked against this file, TAKE-CHECKLIST.md and FINDINGS.md F-002; nothing was run).** M1 CONFIRMED: steps 2, 4 and 4a had bare `git` commands (a new shell does not keep a folder) and step 1 created the branch before the DIRTY check; now `git -C "$REPO"` everywhere and the status check comes first. M2 CONFIRMED: `<...>` is a bash redirect and no variable held a connection; the skeleton now holds PGHOST, PGPORT, PGCONN_SERVER, PGCONN_TAKE, PGCONN (as TAKE-CHECKLIST), PGCONN_SELECT_ONLY, LOG3 and RESULT_JSON, and every `psql <I6...>` is `psql "$PGCONN_..."`. M3 CONFIRMED: Block R4b-2 hard-codes `$LOG3` and restores pin 2 from `$SHA_PIN` (round 41: since then every restore of pin 2 reads `${SHA_PIN2:-$SHA_PIN}`, section 4); step 13 now copies its eight-pattern loop with `$LOG2.final` (as step 5 does with Block R4). M4 CONFIRMED: step 18 (T21) now says to run command (5) and then the proof of (3) on any stop after (2). M5 CONFIRMED (FINDINGS F-002 holds typed T19 and T20 commands, the T20 extra case and the sentence that T19 is repeated once through /webhook/mf-hook with the field message_id): the commands and pass lines are copied into step 18; the hook leg is a LEAD QUESTION (default yes, not decided here); with the default the contact total was then 10 (7 + 3), with a no 9 (6 + 3) (round 10 figures; the current total is 12, section 5). M6 CONFIRMED: step 16 had no fail action for a second start that is not refused. M7 CONFIRMED as a conflict inside this file (step 20 and section 6 said message 1 comes before step 19a sends anything; line 165 puts step 20 after 19a; TAKE-CHECKLIST says during its mailbox wait): the checklist text supports 'after the two sends of 19a', so step 20, step 19a, step 26, I43 and section 6 now say that (round 10 figure: message 1 listed 7 contacts and message 2 listed 3; now 9 and 3, section 5; no clock changed). M8 CONFIRMED: rows 21, 25 and 26 now lead with the corrected clock (Case A and Case B) and give the dated time second; no minute value changed. M9 CONFIRMED: step 17 (2), (6) and (7) now use TAKE-CHECKLIST Blocks R2j, R6, R6j and R7j (the `item` field and the distinct-file count); step 26 holds the exact command for `archive_contacts` and its path name `RESULT_JSON` (I18). Not checked: nothing was run; every new command is mine or copied from FINDINGS and was checked with `bash -n` only.

## Section 1 item 23 (was [HISTORY])

23. [HISTORY] **Round 11: what the review said and what was found (each checked against this file and TAKE-CHECKLIST.md; nothing was run).** Major 1 CONFIRMED: step 20 still ended with "the two contacts of step 19a are therefore in message 2", which contradicted message 1 then listing 7 contacts (now 9); the sentence is deleted. Major 2 CONFIRMED: the hook-leg command of step 18 set `KEY` again before the pass lines of the form leg were read; the legs now use `KEYF` and `KEYH` (commands and pass lines; TAKE-CHECKLIST holds no T19 key name, so nothing there cites it). Major 3 CONFIRMED: Block R5e needs `$KEY` and nothing set it; step 16 now sets it, and `KEY="${KEY:-REPLACE_ME_KEY}"` is in the skeleton and in the placeholder loop. TAKE-CHECKLIST/FIX-PLAN review M1 CONFIRMED: section 4 now holds the one superset skeleton (VALUES, FILLED1, FILLED, SRC_TAKE, ACTLOG added; `N8N_PORT="5690"` was already there). M2 CONFIRMED: `SHA_EVIDENCE` and `FINAL_SHA` are removed from the skeleton and the placeholder loop, and section 4 says Block R3 must refuse when `grep -q '^SHA_EVIDENCE=' "$ENVSH"` matches (the block text is in TAKE-CHECKLIST, not edited here). M7 CONFIRMED: steps 4, 4b (e) and 13 (d) joined commit and sha capture with `;`; they are now one `&&` chain with `SHA_BEFORE` and a `test` that the new sha differs, and print `sha-written`. Nits: N1 (row 10 held a literal pipe, so the row had 11 pipes; reworded, now equal to the other rows), N2 (`CREATE DATABASE $TAKE_DB`), N3 (`FILE1 FILE2` and `SAME_ARGUMENTS_AS_STEP_7` instead of `<...>`), N4 (step 18 loads `pg-secrets.env` first), N5 (step 1 names each command), N6 (step 16: `grep -c LISTEN` may print 2 on a dual-stack system), N7 (I19 07:00 (12:30 IST), I20 08:33 (14:03 IST), Step D definition). Not checked: nothing was run; the changed commands were checked with `bash -n` only.

## Section 1 item 24 (was [HISTORY])

24. [HISTORY] **Round 12: what the two reviews said and what was found (each opened and checked; nothing was run).** M3 CONFIRMED: the skeleton held fixed names for per-run values and a block that sources `$ENVSH` again overwrote a typed value; now `${NAME:-default}` (section 4, "Per-run names survive re-sourcing"). M4 CONFIRMED: TAKE-CHECKLIST Block R4b-2 now only restores pin 2, so step 13's sentence that it hard-codes `$LOG3` and re-runs take_check was stale; the counting block is Block R4f (named in step 13 and section 4). M5 CONFIRMED: only FIX-PLAN Step 4c held a command for `SHA_SCRIPTS`; step 6 now holds it. M7 CONFIRMED: `PGADMIN` is a login NAME here and a connection text in TAKE-CHECKLIST, `KEYF`, `KEYH`, `KEY`, `PGADMIN_PW` were in no table; one paragraph in section 4 and the TAKE-CHECKLIST table now agree; FINDINGS.md F-002 still says `$KEY` and `$PGADMIN` (not edited). M8 CONFIRMED: two restore methods existed; step 13 now says the blocks win. C3 (stranger review) CONFIRMED: FIX-PLAN item 4 said to change N8N-START.md and DESIGN-A-README.md, step 14 (d) only read them; (d) now owns the change and holds the grep. Nits: there is no `.final2` or `.final3`; a repeat types a NEW `LOG2` (round 14; the old nit text said `.final2`, `.final3`). Not checked: nothing was run; steps 25 to 30 and sections 7 to 10 were not re-read; the clock tables of section 6 were not touched.

## Section 1 item 25 (was [HISTORY])

25. [HISTORY] **Round 20 (log fix-tcfp15.md; review reviews/plan-files-r20.md, each finding checked against the three files and QUESTIONS.md first; nothing was run).** B1, M2, M3 CONFIRMED: step 8 was described three ways; one order now stands in RUNBOOK step 8 (the cell wins), FIX-PLAN Step 5 and TAKE-CHECKLIST Inputs-list items 32 and 34: logins by DB_SETUP.sh, then database, table, then grants by DB_GRANTS.sh (Q31 item 78 names only the first file); both files source `shas.env` themselves; the leftover (v) request is removed; State names I50 and I51. M4 CONFIRMED (step 18 (5) is self-contained; SECOND_ADMIN is the fall-back of (5)). M5 CONFIRMED (steps 3, 4, 4a, 14 (g), 4b (d), 5, FIX-PLAN Step 4c, Block R4 and 31 sibling REFUSED lines of TAKE-CHECKLIST groups now stop the next command). M6 CONFIRMED (Tuesday set is two files). M7 CONFIRMED except that FIX-PLAN already held rows for GATE (item 55), BODY and HOOK_URL (item 25) and PGPASSFILE (item 60); rows I50 to I58 added here; one password rule (section 4). M8 CONFIRMED (number lists and double words, one glossary line in each file). Not checked: nothing was run; every changed command was checked with `bash -n` only.


## RUNBOOK step 13, restore text with the two OLD FORM git checkout commands (removed in round 54; NOT to be typed)

OLD FORM, DO NOT TYPE: `. "$ENVSH" && need_set REPO SHA_PIN1 && git -C "$REPO" checkout "$SHA_PIN1" -- handover/flows-audit/flow-check/take-warns.pin && echo pin1-restored` (it keeps pin 1's reviewer line, because it comes from the commit of step 4b; the old command used SHA_FOLDER, whose pin still names a session and exits 4), and install pin 2 again after the unfilled run (use Block R4b-2): OLD FORM, DO NOT TYPE: `. "$ENVSH" && need_set REPO && PINSHA="${SHA_PIN2:-$SHA_PIN}" && need_set PINSHA && git -C "$REPO" checkout "$PINSHA" -- handover/flows-audit/flow-check/take-warns.pin && echo pin2-restored`. **Round 8 (nit; applies only to the OLD FORM above, which is not typed since round 41, because the blocks stage nothing): `checkout <sha> -- <file>` STAGES the file, so after the last restore end with `. "$ENVSH" && need_set REPO && git -C "$REPO" checkout HEAD -- handover/flows-audit/flow-check/take-warns.pin && echo pin-at-head` (HEAD holds the last committed pin) and read `. "$ENVSH" && need_set REPO && git -C "$REPO" rev-parse --is-inside-work-tree > /dev/null && if test -z "$(git -C "$REPO" status --short -- handover/flows-audit/flow-check)"; then echo status-clean; else echo status-DIRTY; fi` = `status-clean`; otherwise step 17 (3) shows a false difference.**

## Round 54b: history notes removed from RUNBOOK.md next to live commands (parenthesis text only; command text unchanged)
Line numbers are those of RUNBOOK.md before this round's insertions. Each entry is the removed text.

- line 7: (round 15)
- line 11: (round 38, reader M13)
- line 51: (round 30, M8)
- line 56: (round 38, reader M9, M15)
- line 57: (round 38, reader M14)
- line 60: (round 26, finding 4)
- line 72: (round 48, reader a M7)
- line 81: (round 9, B1)
- line 98: (round 48, reader a M3)
- line 190: (round 14)
- line 192: (round 14, stranger B3)
- line 192: (round 19, M4)
- line 194: (round 14)
- line 196: (round 15)
- line 198: (round 12, M3)
- line 198: (round 38, reader M8)
- line 200: (round 12, M7)
- line 200: (round 21, M7)
- line 202: (round 10, M2)
- line 202: (round 10, M3)
- line 202: (round 22, finding 4)
- line 202: (round 22, finding 4)
- line 208: (round 13, M2)
- line 208: (round 13, M4)
- line 220: (round 21, M1)
- line 220: (round 10, M1)
- line 227: (round 5)
- line 228: (round 41, reader)
- line 228: (round 22, finding 1)
- line 232: (round 6, M2)
- line 232: (round 16, M4)
- line 235: (round 41, M3)
- line 236: (round 9, N5)
- line 236: (round 41, M10)
- line 236: (round 41, M13)
- line 236: (round 7, B1)
- line 237: (round 5)
- line 237: (round 16, M4)
- line 238: (round 48, reader B2)
- line 238: (round 48)
- line 239: (round 48, reader b M9)
- line 239: (round 41, M10)
- line 247: (round 48, reader b M6)
- line 247: (round 48, reader b M6)
- line 251: (round 5, M4)
- line 251: (round 16, M4)
- line 251: (round 33, M9)
- line 255: (round 5, M2; I44)
- line 255: (round 22, finding 7)
- line 256: (round 48, reader b M5)
- line 257: (round 22, finding 4)
- line 258: (round 41, M1)
- line 259: (round 48, reader b M4)
- line 260: (round 41, M18)
- line 260: (round 5)
- line 316: (round 22, finding 6)
- line 316: (round 26, finding 1)
- line 326: (round 10, M7)
- line 329: (round 4: 10:55)
- line 347: (round 7, N7)
- line 368: (round 33)
- line 407: (round 20)
- line 428: (round 7, B1 and M7)
- line 429: (round 22, finding 1)
- line 429: (round 10, M2)
- line 438: (round 23, Q27-4)
- line 439: (round 8, m7)
- line 448: (round 34, reader finding 5)
- line 449: (round 7, N4)
- line 457: (round 7, M7)
- line 459: (round 7, N2)
- line 470: (round 7, M4)
- line 471: (round 7, M7)
- line 472: (round 7, M7)
