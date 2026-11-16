# fix-runbook48: round 48 fixes for RUNBOOK.md only (static; nothing run in n8n, Postgres or HubSpot; made-up data only)

## Gaps and failures first
- Nothing was RUN. Every new command is written, never tried. Only `bash -n` of the two fenced blocks was run (`fence3.py`: fences 2, bad 0). The new commands inside table cells (step 16, `need_set KEEP`) were NOT syntax-checked by a tool, because they are not in a fenced block.
- Reader words were unverified; each was checked in the file. CONTESTED or only partly applied: (1) reader a M1 "move section 1 to an appendix": NOT moved (other files and the steps cite section 1 and its item numbers; a move breaks them); instead every item is marked [RULE] or [HISTORY] and the header says a stranger starts at section 2. (2) reader a M2 "status says round 38": already round 41 in the file (planfiles41); now round 48. ORDERS.md line numbers: kept, with a sentence that says to find the line by its Q number. (3) reader b M6 "T20 row count before/after missing": it IS in step 18 ("once BEFORE the loop and once AFTER; the two numbers in `$TESTLOG` are equal"); not changed. (4) reader a M10 (decision 1 vs 4): stays open; now written LEAD DECIDES (I31). (5) reader a M8 "operator unclear": defined in the roles table; a pointer added.
- Not decided here (LEAD DECIDES, each with input, default, time): wording of ACCEPTED line (I31, before step 5, Tue 04:51Z (10:21 IST)); whether the 45 min of script and control-command writing move from W-Wed to W-Tue (I33, by Mon 21:00Z (Tue 02:30 IST); default yes, W-Tue 215 min starting 00:25Z (05:55 IST)); the "close to 45 s" margin (step 22, 08:25Z (13:55 IST); default 35 s); one batch message or one message per contact (I43, Tue 08:29Z (13:59 IST); default two batch messages); whether a repeated re-smoke on the NO-GO path includes the 14-min control (I30; default yes: latest ends 06:39Z (12:09 IST), 05:44Z (11:14 IST), 04:13Z (09:43 IST), 03:18Z (08:48 IST)).
- Pre-existing, not mine, not fixed: table rows 6, 14 and 17 of section 5 have 12, 11, 12 vertical bars against 10 in the separator row (same counts in the backup; they hold code with pipe-like text). Not checked whether they render.
- The new minute and time figures (Tuesday control 09:29Z to 09:43Z, 215 min, 135 min, the four latest ends minus 14) are arithmetic on this file's own numbers, not measured.
- Clock block untouched: `sed -n 8,55p TAKE-CHECKLIST.md | md5sum` = `sed -n 37,84p FIX-PLAN.md | md5sum` = 929febdfab0142f49dfd50627d87285d.

## Finding to change
| Finding | Verdict | Change in RUNBOOK.md |
|---|---|---|
| a M1 section 1 changelog, 13(f) vs 13(p)/16(a) | partly (not moved) | 13(f) S9-2 text deleted, points to 13(p); items marked [RULE] (1,3,4,5,6,7,8,9,13,16) or [HISTORY]; header explains; old tallies in items 22 and 23 marked as round-10 figures |
| a M2 status round 38, ORDERS line numbers | partly | status line now round 48; sentence: find ORDERS lines by Q number |
| a M3 TAKE_FOLDER, eight names, no answer file | confirmed | section 4: the lead types the real value over the REPLACE_ME word in shas.env; `bootstrap-ok` is the proof |
| a M4 three start times, two re-smoke ends | confirmed | "Which clock to follow" paragraph at the head of section 5 |
| a M5 rehearsal 1 07:40Z vs 07:44Z | confirmed | 13(g): 07:40Z dated, 07:44Z corrected clock; follow section 6 |
| a M6 NOT CHECKED rule, 600-word paragraph, I47(a) missing | confirmed | one-sentence rule and "script does not exist yet, due Tue 04:00Z (09:30 IST)" at the start of the gate bullet |
| a M7 terms defined late | confirmed | new Terms bullet: Case A/B, Form 1/2, SHA_PIN2, Step 0a, Blocks P1b/P2b/P1c, R4f, I47(a) |
| a M8 operator, placeholders, ceiling | confirmed | Terms bullet "Placeholders that stop a Tuesday step"; ceiling now "about 12 sends", source named |
| a M9 TAKE_CHECK_FLOWS correction | confirmed | section 9 status line: all items OPEN until the lead writes done |
| a M10 decision 1 vs 4 | contested | LEAD DECIDES (I31) added; not decided |
| a M11 FNMISS never reset | confirmed | `FNMISS=""` before the function check loop in the skeleton |
| b B1 Tuesday control keysave 19a clash, two addresses, no pass line/time, I32 vs W-Wed | confirmed | keysave word `19t` for Tuesday (section 4 word list, step 19a, step 16.9); two addresses named; pass line `mail-count 2`; start 09:29Z, end 09:43Z (15:13 IST); W-Wed LEAD DECIDES |
| b B2 step 16 not followable | confirmed | step 16 rebuilt as 16.1 to 16.10 in run order: four inputs, logs, cleanup, key and body, gate, refused second start (kept as 16.6, so TAKE-CHECKLIST cites stay valid), `POSTLOG=` typed then Block R5e/R5f with what each prints, mailbox `mail-count 1`, control, instance unchanged; bold markers balanced; pass cell lists each printed word in order |
| b M3 contact tally | confirmed | 12 = 9 + 3 (11 without hook leg; 10 without Tuesday control; 9 without both) in step 20, step 30, section 5 table (new row), I43, line-54 bullet; Tuesday control's 2 contacts named in message 1 |
| b M4 step 29 vs 26 retake, step 26 fail merged | confirmed | step 29 fail now says no same-day retake and slips next day; step 26 fail split into stop / why no same-day retake / what happens instead / the owner's yes |
| b M5 step 23 pass vs recovery off, "close to 45 s", N | confirmed | step 23 pass conditional (`scene 4: not tested, recovery off`); step 22: N defined, 35 s default with LEAD DECIDES |
| b M6 step 18 take program, addresses | partly | take program start/pass line/contact count named LEAD FILLS (I18); NOT CHECKED is not a pass; repeat of T19 types a new address; T20 count contested (present) |
| b M7 step 30 vs step 20 | confirmed | step 30: post pass is "post is up"; Step D replies are a hand-off record; step 20 governs |
| b M8 three latest-end values, terms, 16.11 vs 365(a) | confirmed | ONE governing value paragraph at the head of the time-statements item (06:53Z (12:23 IST) etc.); (A) readings named as money-stop comparisons; ONE owner ask rule in 16.5 |
| b M9 step 17 pass lines | confirmed | new 17.0: report count, mutation line, F-011 runner (LEAD FILLS), names from shas.env, counted list empty after marking, F-003 path |
| b M10 post-twice script and control command budget | confirmed | W-Wed bullet: LEAD DECIDES with the 215 / 135 min arithmetic |
| b M11 `$KEEP/pg-secrets.env` without need_set KEEP | confirmed | `need_set KEEP &&` inserted in 10 commands of step 18 |
| b note "v3 table" | confirmed | step 8 wording: comment says v3, file is v4, comment changes nothing |

## Matching changes needed in other files (not edited; the lead or the owner of each file does them)
- FIX-PLAN.md line 24 cites "RUNBOOK step 24 and 16.7" for the start-state gate: it is now 16.5.
- TAKE-CHECKLIST.md: the contact total and the Tuesday control wording (Inputs list, Step D, check 5b) should say 12 and keysave word `19t`; Citations of step 16.6 (still the refused second start) stay valid; line numbers not re-checked.
- QUESTIONS.md is append only: Q31 items 25, 50, 55 and 70 may be appended with the new due times (control command needed Tue about 09:29Z (14:59 IST); post-twice script Tue 09:00Z (14:30 IST)).
- OWNER-STEPS-q16-rows.md: one message per contact vs two batch messages (I43) and 12 contacts.

## Raw tool output (run from handover/flows-audit after the edits)
```
1043 files already formatted
check_refs: PASS 5193 references
check_names: PASS 655 rows
check_secrets: PASS 0 hits in 2918 files
check_counts: PASS 52 files / 655 nodes
RUNBOOK.md fences 2 bad 0
```
- Note: the file counts in the tool lines differ between two runs (1043 then 1044 formatted files) because files were added by someone else while I worked; both runs passed.
