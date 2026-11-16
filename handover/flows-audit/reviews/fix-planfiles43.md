# fix-planfiles43: round 43 (round 2 of 2, non-security) fixes for TAKE-CHECKLIST.md and FIX-PLAN.md only (static; nothing run in n8n, Postgres or HubSpot; made-up data only)

## Gaps and failures first
- Nothing was RUN on the real tree. One command was tried: the new GO row 3 (e) command, in a scratch git repository on made-up files (a pin file plus a flow json changed: it printed `code-check-ran` and `exit 0` and nothing else; a changed `take_check.sh` printed `NOT PASSED` and its name; an unknown branch printed `NOT PASSED: git exit 128` and the `fatal:` line); `bash -n` of the extracted command: ok. It is a table-cell command, not a fenced block; no fenced block was changed, so there was no fence to syntax-check.
- LINE SHIFT (the top note and the Wednesday table add 24 lines to TAKE-CHECKLIST.md): other files cite TAKE-CHECKLIST line numbers and I may not edit them (RUNBOOK frozen, QUESTIONS append only, FINDINGS not mine). Stale citations the lead must change: RUNBOOK.md lines 66 and 237 ("TAKE-CHECKLIST.md line 6, Pass rule" is now line 30); QUESTIONS.md line 431 and 653 area ("line 59" is now 83; "line 119" is now 143), line 466 and 739 ("line 6" is now 30), lines 734 and 738 ("line 48" is now 72, "line 59" is now 83), line 741 ("about line 73": item 14 is now line 97); FINDINGS.md line 276 ("line 310" is now 332). Lines before the Placeholder table moved +24, lines after it +22. check_refs does not check these line numbers (it passed before and after).
- Not done or only partly done: (1) the Placeholder table third column does not start with a supplier word in every row (rows such as `$TOOL`, `$FLOWS`, `$EXPORT`, `$RUNSHEET` keep their older wording; a legend above the table defines the five supplier words; the rows I did change are KEY group, SHA group, PGCONN, PGCONN_SERVER, PGCONN_TAKE, FLOWS_PW, NEW_PIN, ENVSH, N8N_PORT, TAKE_FOLDER, JUDGE_WHO); (2) "re-pin defined twice" (reader r43 minor, lines 112 and 116 before the edit) NOT merged; (3) the sentence fragment in the "If NO-GO" schedule row (reader: "row 130 scrambles cells") NOT examined; (4) UTC labelling: I labelled the schedule table, the new table and the FIX-PLAN slot paragraph and "Needed by" table header; I did not audit every time in the 490-line file; a script that lists bare HH:MM tokens still finds many in the FIX-PLAN example-lines table (they sit under a header that now says "UTC, then IST in brackets"); (5) the matching RUNBOOK change: RUNBOOK step 17 (3) still holds the OLD form of the GO row 3 (e) command, and RUNBOOK writes "T19 / T20 / T21" in places; the lead aligns both (RUNBOOK is frozen); (6) the clock block changed (see below), so RUNBOOK section 6 and the two copies agree only if the lead agrees with the two edited lines.
- Reader words were unverified; each was checked in the file.

## Clock block
- Changed identically in both files (two lines: the practice-run row now names the four tests; the owner's first-message row now says 9 contacts, 8 / 7 / 6 without). New md5 dfd844ddb7085082534434075814e131 (old 929febdfab01...).
- New ranges because of the 24-line insert: `sed -n 32,79p TAKE-CHECKLIST.md | md5sum` = `sed -n 37,84p FIX-PLAN.md | md5sum` = dfd844ddb7085082534434075814e131 (old TAKE-CHECKLIST range was 8,55). FIX-PLAN range unchanged.

## Findings (r42 = FIX-PLAN/TAKE-CHECKLIST 1-120 reader, r43 = TAKE-CHECKLIST 81-290 reader, r48 = the matching list)
| Finding | Verdict | Change |
|---|---|---|
| r42 B1 Wednesday not followable | confirmed | TAKE-CHECKLIST top: section "Start here: Wednesday runs from RUNBOOK steps 18 to 26" with the one-page ordered table (14 rows: step, UTC and IST, input, who supplies); four supplier words; "lead to confirm" and "LEAD DECIDES: input, default, time" defined |
| r42 M2 / r43 M5 T19, T19H, T20, T21 | confirmed | named four everywhere (global replace, both files, clock block identical); T19H defined ONCE (TAKE-CHECKLIST top; FIX-PLAN words point to it); contact counts 12 / 11 / 10 / 9; F-002 rule rewritten as one rule in three parts, "one sentence" removed, the Q29 item 3 difference and the alwaysOutputData variant written as LEAD DECIDES with input, default, time |
| r42 M3 step mapping | confirmed | the first mapping (Plan overview item 9) is now the one complete mapping (adds RUNBOOK step 25, step 3a, 9b to 9e, R3; Step 14 = start-state gate written in RUNBOOK 16.5 and 24); the second list became a pointer with the collision and rule notes |
| r42 M4 rehearsal 2 h vs 45+45; ungated take time | confirmed | FIX-PLAN item 4 and TAKE-CHECKLIST schedule row: 07:40Z to 08:25Z and 08:40Z to 09:25Z, the ORDERS 2 h window named as the frame, take "dated 10:00Z (15:30 IST)", Case A 10:07Z, Case B 11:02Z |
| r42 M5 / r43 M3 suppliers, JUDGE_WHO | confirmed | items 14, 20, 21, 22, 23, 24 now start "LEAD DECIDES (input, default, time)"; header of the Inputs list allows LEAD FILLS, LEAD DECIDES, SETTLED; JUDGE_WHO due Tue 03:30Z (09:00 IST) (Block R3n needs it when the branch moves after R3, due 03:30Z); Q31 item 33 says 04:00Z: the earlier time governs, the lead appends the change to Q31 (not done by me); rows 2, 6, 7 without a judge are stated NOT PASSED |
| r42 M6 / r43 M1, M2 variables | partly | one defining row for KEY, KEYF, KEYH, ADDR, KEYS (supplier KEYSAVE, words 16, 19t, 18, 19a, take); duplicate KEY/ADDR, KEYS and the three SHA rows removed (SHA_EVIDENCE, FINAL_SHA now defined in the SHA row, MADE BY COMMAND); PGCONN_SERVER and PGCONN_TAKE rows added and PGCONN says it is assigned from PGCONN_TAKE; FLOWS_PW supplier (the lead writes the passwords file; no step makes it); NEW_PIN, EXPORT_PIN, ENVSH, N8N_PORT, TAKE_FOLDER suppliers (TAKE_FOLDER typed in the bootstrap line; Step 0 now says to type it first); item 18 (e) no longer lists KEYS and names the other suppliers; FIX-PLAN item 8 no longer ends "and the rest". Partly: see gaps (1) |
| r43 M4 GO row 3 (e) | confirmed | command rewritten (pathspec adds `flow-check/*.sh`, `flow-check/*.py`, `fill_flows/*.py`, not the pin file); prints exactly two lines on a pass; tried in a scratch repo; "would fail GO row 3 (e)" in the Codes row is now true |
| r43 M6 re-pin end time | confirmed | schedule row, FIX-PLAN item 4: one end time 08:29Z (13:59 IST), re-smoke ends 09:29Z (14:59 IST), the 08:00Z wish needs a start by 03:31Z (09:01 IST) |
| r43 M7 F-011 route | partly | item 22 now LEAD DECIDES, default B, with the reason for 03:00Z against DB_SETUP.sh 04:54Z written as "this audit's reading" |
| r43 M8 suppliers only "the lead" | partly | $REPORT, $HOOK_URL etc. keep "LEAD FILLS"; the legend says what that means; item 23 default stated (the standing yes of 3 live model calls and a stop at a fourth) |
| r48 line 24 gate 16.7 to 16.5 | confirmed | now "RUNBOOK section 2, written out in RUNBOOK 16.5 and step 24" |
| r48 contact total 12 | confirmed | all the counts in both files |
| r48 Tuesday control keysave 19t, check 5b | confirmed | check 5b names 19t, the two keys and addresses, `mail-count 2` (RUNBOOK 16.9 wins), 09:29Z to 09:43Z |
| r48 Block R5e keysave chain 16.4; citations of 16.6 | confirmed | "RUNBOOK step 16.4"; 16.6 cited as the refused second start (still valid) |
| r42 minor ORDERS lines 105-175 vs 105-177 | not changed | line 3 still says 177; item 1 text not re-read for 175 |

## Raw tool output (after the last edit)
```
check_refs: PASS 5190 references
check_names: PASS 655 rows
check_secrets: PASS 0 hits in 2939 files
check_counts: PASS 52 files / 655 nodes
ruff format --check .: 1064 files already formatted
clock md5 (both): dfd844ddb7085082534434075814e131
```
(File counts differ between runs because other sessions add files.) No commit made. Checkpoint: reviews/checkpoint-planfiles43.md. RUNBOOK.md, QUESTIONS.md and FINDINGS.md were not touched. Rules cited: fix-dont-defer, wording-clear-for-everyone, class-level-fixes (bible R-numbers not looked up in this session: no bible folder here).
