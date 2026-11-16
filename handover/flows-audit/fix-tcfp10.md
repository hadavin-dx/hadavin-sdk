# fix-tcfp10.md: round 14 fixer log for RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md

Author: the round 14 fixer. Nothing here is "verified". Backups of the three files are in /tmp/bk (made before the first edit).

## What failed, what is uncertain, what was not checked (read this first)
- `python3 tools/check_secrets.py` prints `FAIL 1 hits: flow-check/evidence-f8-r8.md:55 token-like (length 152)` at the end of my work. That file and `flow-check/raw/test-take-check.txt` (a second hit earlier, since gone) were written by another session during my work (their change times are not mine; I did not edit anything under flow-check). I did not fix or judge them. The lead must decide.
- Nothing was run in n8n or against a real database. The skeleton and the make command of FIX-PLAN Step 0a were run in a scratch folder (`bash -n` passed; `bootstrap-BLOCKED` and `input_ready` printed as intended). Every other new command was only written, not run.
- Not all findings are fully closed. The ones that are only partly done are marked PARTIAL below, with what is left. These are my own gaps, not allowed exceptions.
- The step cells are very long; I did not shorten them (stranger "could not follow" notes for RUNBOOK step 4b and step 18, and the FIX-PLAN step 9 paragraph, are NOT fixed).
- The text of the old rounds' tags "(round N, M..)" inside commands was not removed.

## Checks run at the end (from handover/flows-audit)
- `python3 tools/check_refs.py`: `PASS 5166 references`.
- `ruff format --check .`: `606 files already formatted`.
- `python3 tools/check_secrets.py`: FAIL, 1 hit, in a file I did not touch (see above).
- Clock block: `diff <(sed -n '/^## Clock/,/| the owner | posts |/p' TAKE-CHECKLIST.md) <(sed -n '/^## Clock/,/| the owner | posts |/p' FIX-PLAN.md)` printed nothing (empty diff). The one Clock edit (the owner row: "Mon 16 Nov 22:00Z (Tue 03:30 IST)" became "Mon 16 Nov 21:00Z (Tue 02:30 IST)", to match Q31 item 27) was made in both files.
- Table-cell pipe check: I compared the pipe count of every edited table row against the backup; one row (RUNBOOK step 9) had gained pipes from my `grep -E` text, which I rewrote with `-e` patterns; its count is now equal to the backup (10 and 10). The two TAKE-CHECKLIST rows the script flagged are equal to their backup text (a key collision in my script, no difference).

## Stranger part 1 (reviews/fp-tc-stranger-r14.md)
- B1 fixed. RUNBOOK.md skeleton in section 4 (about lines 87-170): `REPO="${REPO:-REPLACE_ME_I2}"`, an example comment on every REPLACE_ME line, `TRAILER` default, `INSERTLOG`, `WAIT_S`, `PGPASSFILE`, the `input_ready` helper, two loops (names needed before step 1 print `bootstrap-ok` or `bootstrap-BLOCKED`; names set later print "set later" with the step), end marker `# end of shas.env`. FIX-PLAN.md Step 0a (line 72) now has six numbered actions (cd, REPO, TAKE_FOLDER, make command with sed for REPO and the new awk end marker, nano, source with pass line `bootstrap-ok`). PARTIAL: the I-numbers inside REPLACE_ME words still point to section 10 rows; where a row did not name the value I added a comment with the right pointer (JUDGE_WHO, BODY, HOOK_URL), I did not rewrite the I-table.
- B2 fixed at RUNBOOK.md step 3 (REFUSED with action), step 4b (b) and (d), step 9 (a), (b), (d), (e), step 12, step 13 (a) to (e); TAKE-CHECKLIST.md Block R3 (three REFUSED texts incl. the pointer to Block R3n), "nothing counted/read" messages (8), PATCH_BRANCH and body-file messages; FIX-PLAN.md Step 2 and Step 6. Block R3n is now named in FIX-PLAN Step R3 as the one way to clear the evidence sha.
- B3 fixed. RUNBOOK section 4 "Answer cells" defines the cell (a value in shas.env, or a file `$TAKE_FOLDER/inputs/NAME.sh` run by its step), the check `input_ready NAME`, and says Q31 is the question list only. QUESTIONS.md Q31 items 40-58 are new, one input each, each with a `BLOCKED: ... by <time UTC (IST)>` line. FIX-PLAN.md last section "Inputs the Tuesday operator waits for" is the table (item, input, cell, check, time). TAKE-CHECKLIST.md blanket rule (Block "Blanket rule", about line 99) now says the same. PARTIAL: the Tuesday command-file names in that table (for example `IMPORT_SUB.sh`) are my proposal; the lead confirms them.
- B4 fixed (as far as an audit can). `PIN_NAME` cell, `input_ready PIN_NAME` first line of RUNBOOK step 4b, Q31 item 48, TAKE-CHECKLIST Inputs item 14 and "Needed by" now say: name by Tue 03:30Z (09:00 IST); with no name steps 4b and 13 do not run. The name itself is BLOCKED (needs the lead and a person).
- B5 fixed in the text, run length BLOCKED. TAKE-CHECKLIST "Needed by" and the blanket rule now give the same times (branches and shas 03:30Z, mutation batch 03:00Z, values file 05:00Z, T19-T21 runner Wed 05:45Z). FIX-PLAN Step R3 says Block R3 runs before step 1 and is not in the 269 minutes. BLOCKED: the measured length of Block R3 (Q31 item 51). I did not add a paragraph to the Clock block (it must stay identical in two files and RUNBOOK section 6 wins); the statement is in FIX-PLAN Step R3.
- M1 PARTIAL. FIX-PLAN.md line 62 now says the operator types only from RUNBOOK section 5 and FIX-PLAN commands are copies. The duplicated branch creation (FIX-PLAN steps 0 and 1) and the check_patches placement were NOT reworked.
- M2 fixed: FIX-PLAN log rule now names `runbook-step-N.log` with N the RUNBOOK step number.
- M3 PARTIAL: logs now named for RUNBOOK steps 7, 8, 12, 13, 16, 18, 26 and FIX-PLAN step 9 and 9b-9e. FIX-PLAN steps 4d, 5, 6, 7, 8 pass lines were not individually given a log name beyond the general rule (log rule line).
- M4 fixed: FIX-PLAN step 8a now asks for the activation method (Q31 item 46), step 8 for import and print ids (item 45).
- M5 fixed: RUNBOOK step 9 (a) has the values-file recipe with examples, `nano`, `umask 077` guard, mode, REPLACE_ME and line-count pass lines; Q31 item 42 with the number DESK_TIMEOUT_MS BLOCKED (the number is the lead's). PGCONN examples are in the skeleton comments; the password route is `PGPASSFILE` (Q31 item 41).
- M6 fixed: RUNBOOK gate (e) line says "NOT CHECKED on Tuesday"; TAKE-CHECKLIST line 47 decision time matches Q31 item 27 (21:00Z).
- M7 fixed: T21 failure rule is a BLOCKED line (Q31 item 49) in TAKE-CHECKLIST (the F-002 Codes line); runner time is 05:45Z everywhere I found.
- M8 PARTIAL: TAKE-CHECKLIST Words box defines operator, lead, gate, pin file, reviewer line, pin 1 and pin 2; RUNBOOK section 4 has "Words used in this file" and the three number lists. The word "step" is still used with several numbering sets (the file name is now required); the "check" and "row" meanings were not split.
- M9 PARTIAL: the Tuesday blockers are listed with Q31 items and times in the FIX-PLAN table. The F-011 A or B choice and the n8n start command (Q31 item 35) were left as they were.

## Consistency review (reviews/fp-tc-consistency-r14.md)
- M1 fixed. RUNBOOK step 18: every T19 form and hook leg, T20 loop (now prints `done sent=200 not422=N`), T20 extra case and T21 (1)-(6) is wrapped to append to `$TESTLOG`; the wait is written into the log by the first T19 command (`wait_s=$WAIT_S`); pass lines read from `$TESTLOG`. Steps 7, 8 (iii)(iv), 26 counts proof also wrapped. Step 16 posts are read from `$POSTLOG.counts`. The pipe-free form is defined in section 4.
- M2 fixed: RUNBOOK step 3 prints REFUSED; step 4b (b) guard; step 4b (d) uses `$NEW_PIN`; step 8 insert test uses `$INSERTLOG` with a REFUSED guard; step 9 (b), (d), (e) guarded.
- M3 fixed: step 13 (d) prints `sha-written` or `sha-written-repeat`; the repeat text says type a NEW LOG2, EXPORT and EXPORT_PIN; the repeat example in section 4 has EXPORT; 13 (b) names `grep '^!!!' "$LOG2"`.
- M4 fixed: `.final2`/`.final3` removed from RUNBOOK failure 24 text, TAKE-CHECKLIST Block R4b-2 heading, Block R4f comment and Pin procedure line 332 ("no .r1/.r2").
- M5 fixed: FINDINGS.md F-002 row (line 109) now uses `KEYF`, `KEYH` and `PGPASSWORD="$PGADMIN_PW"` before every admin psql; RUNBOOK "FINDINGS wins" text replaced; FIX-PLAN step 9e no longer says `$GATELOG` is the GO test log.

## Stranger part 2 (reviews/fp-tc-stranger-r14-part2.md)
- B1 fixed for FIX-PLAN steps 10-16: each now has a command or a BLOCKED line with a Q31 item and a time (items 50, 54, 55, 56, 57, 58). Step 15 names a NEW LOG2, EXPORT and EXPORT_PIN. Step 16 points to RUNBOOK step 26. The mailbox count command itself is BLOCKED (item 50).
- B2 fixed: see consistency M1 (step 18 wrapped); FIX-PLAN steps 5-8a pass lines still rely on the general log rule (PARTIAL for FIX-PLAN steps 5, 6, 7, 8a).
- M3 PARTIAL: the three number lists are defined (RUNBOOK section 4, TAKE-CHECKLIST Words box). Existing mentions in TAKE-CHECKLIST of "Inputs item n" and in FIX-PLAN of "Inputs item 3" were not each re-checked.
- M4 fixed for the three named pointers (JUDGE_WHO, BODY and HOOK_URL comments; RUNBOOK step 21 I23 stale pointer removed).
- M5 fixed: RUNBOOK 4b and TAKE-CHECKLIST P1b now say one of two ways for pin 1, never both, and that P1c is not used with the committed file.
- M6 fixed: TAKE-CHECKLIST P2c now guards `SHA_PIN` (prints `sha-written` or `sha-written-repeat`); pass lines for P2b and P2c added.
- M7 fixed (see consistency M4).
- M8 fixed for the named cases: `RESULT_JSON` guard before the take; step 12 `$EXPORT` emptiness guard; JUDGED lines now carry `head <FINAL_SHA>` and the three counts read only the current head (TAKE-CHECKLIST R2j, R6j, R7j); Block R3 writes `recorded rc=N` into `$EVLOG` and RUNBOOK step 17 checks it with grep. The R6 counted list was not changed beyond a note about the expected count (PARTIAL).
- M9 fixed for the named secret: the CREATE ROLE example no longer carries a password in a `-c` text (FIX-PLAN step 5, Q31 item 52, RUNBOOK step 8 (v)); pin 2 content check added before P2c. The `PGPASSWORD=` environment form in the T19-T21 psql lines is kept (it is a shell variable, not a command-line argument, but it can show in the environment of the process: not changed).
- M10 PARTIAL: I aligned the decision time (21:00Z), the 03:30Z/03:00Z/05:00Z/05:45Z inputs. Not changed (not checked against RUNBOOK section 6 line by line): sha acceptance 04:00 vs 04:26, text-fix wording 05:29 vs 04:16 vs 07:44, S9-2 message times 08:52/09:02/09:15, take start 10:00 vs 10:07/11:02, Step D message 2 time. These need the lead's single time per item.
- M11 PARTIAL: see stranger part 1 M8.
- M12 NOT DONE: the repeated commands of FIX-PLAN steps 5-8, 11-15 versus RUNBOOK 8-13, 21-24 were not merged; the rule "RUNBOOK wins, type from RUNBOOK" is now in FIX-PLAN line 62. Next step: replace each FIX-PLAN command copy by a pointer to the RUNBOOK step.
- M13 fixed (FIX-PLAN step 8a asks for the activation method, item 46).
- M14 fixed: FIX-PLAN step 6 REFUSED now says to edit the one line with nano; the README pointer remains.
- M15 PARTIAL: FIX-PLAN step 10b now says it is Row 4 (RUNBOOK step 19), not an eleventh contact. The question "one message per contact or two" (OWNER-STEPS I43 versus RUNBOOK step 20) is still open and is not mine to decide.

## BLOCKED items (new Q31 items, append only; each has its time in QUESTIONS.md)
40 paths and names; 41 database names, logins and password route; 42 values file; 43 sub-workflow import; 44 values loop; 45 import of the three flows; 46 activation; 47 export; 48 PIN_NAME; 49 T21 failure rule; 50 mailbox count and WAIT_S; 51 run length of Block R3; 52 select-only statements and insert text; 53 re-smoke command; 54 HubSpot made-up lead script; 55 start-state gate tools; 56 rehearsal fit and commands; 57 sign-off format; 58 post-twice send script.
