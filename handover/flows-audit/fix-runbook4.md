# fix-runbook4 (flows-audit, round 4, 2026-11-16)

Backup of the round 3 file: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rb4/RUNBOOK.md. Only RUNBOOK.md and this log were written. Nothing was run in n8n; no git command; no commit. Edits were applied by two python scripts (edit1.py, edit2.py in the scratchpad rb4 folder) with an exact-match count check per replacement; both exited ok. I did NOT re-read the whole new file line by line after the edit (I checked the table cell counts, grepped stale figures and ran the two checkers). No EGM review of the result was run by me; the lead runs it.

## Failures and doubts first
1. Reviewer nit 1 ("spare 10 min should be 20") is NOT applied as stated: the 2-hour block 07:30 to 09:30 holds the positive control (10) and the rehearsal pieces (100): 110 of 120, spare 10. The 20 counts the 10 min before 07:40 that the positive control uses. The sentence is now explicit (section 6).
2. Inputs that only the lead can supply were NOT guessed: every one is a `LEAD FILLS:` cell and a row of the table of section 10 (39 rows, I1 to I39; I36 to I39 new). Not given by ORDERS.md and kept open: the commands of steps 7 to 13, 16, 18 to 26; the WARN reader's name (I36); the answer if no day fits before Mon 23 Nov 18:29 UTC (I37); the new text of DECISIONS items 1 and 7 and N-9 to N-11 (I31); the I14 re-smoke command; the ledger_check output format (the egm/ folder is not in this checkout, so the step 17 filter is UNVERIFIED).
3. Decisions I took myself (none is an ORDERS.md answer; listed as failure 13 in RUNBOOK section 1; the lead may override): one n8n instance and port for steps 7 to 26 (default 5690; a different take port = repeat of steps 11 to 13, 65 min); the re-smoke does not repeat steps 7 to 13 (default: separate throw-away n8n); three shas defined (SHA_FOLDER, SHA_PIN, SHA_SCRIPTS) and a take tree outside the repository; one run sheet path; step 4a before step 5; S9-2 before the edit and S9-3 after the full watch (clock times mine); positive control as first 10 min of the 07:30 block.
4. All new minute figures are estimates by me (step 4a 10, step 14 split a 10 b 5 c 3 d 8 e 4, 14(f) 60, writing 150 and 180, review 60 plus fix 30, S9-2 10, S9-3 5). Not measured.
5. Not checked: that the F-003 and F-004 patches change only the two markdown files (only `grep -n '^diff --git'` on the two patch files was read: one md file each); which files the sentences F-007 and F-028 go into; that mf.py, take_check.sh behaviours match the text (take_check.sh read, not run); the real ledger rows.

## What changed, by review finding
- B1 (step 16): command is `LEAD FILLS`; decided it does not repeat steps 7 to 13; default (ii) separate throw-away n8n (INSTANCE untouched), option (i) on the INSTANCE with a re-export rule; 60 min and the 90-min slot both kept (I14).
- B2 (step 17): exit number is not the pass line; `grep -e OPEN -e FIXED-UNVERIFIED "$LOG3"`; rows expected open and not counted (F-002, F-031, F-007; text rows F-003, F-004, F-042, F-043; rows closed by results F-008, F-037, F-029), counted rows (F-011, F-041 and any other); who judges: LEAD FILLS. Q21-3 "never downgrade by counting" against Q27-9 "downgraded with evidence": one reading written in failure 7 and step 14 (f).
- B3 (instance): section 4 defines INSTANCE and TAKE_PORT; steps 7, 11, 16, 18, 21, 26 use them; up Tue to Wed not required; step 18 checks and restarts with the same command.
- M1: all `lead provides` cells became `LEAD FILLS`; one table (section 10); writing time (W-Tue 150, W-Wed 180) and the Q29-4 review (60 wall + 30 fix) added to section 6.
- M2: take tree, SHA_SCRIPTS, six paths, `test -f` loop and sha256sum in step 6; I1 and I18 list names, not only commands.
- M3: WARN reader = I36 (LEAD FILLS); SHA_FOLDER and SHA_PIN defined in section 4 and steps 4 and 13.
- M4: step 27 split: S9-2 11:00 to 11:10 UTC, S9-3 13:30 to 13:35 UTC after the full watch (a retake needs the key); the 15 min are in section 6; edit now 11:10 to 13:10.
- M5: step 15 asks the token-scope question; the reply is a gate of step 19 (latest 06:55 UTC Wed); "line 4" is now "the line that starts `> Re-check done:` (line 4 on 2026-11-16; read in OWNER-STEPS-q16-rows.md)".
- M6: step 14 uses `$RUNSHEET` (handover/demo/VIDEO-RUNSHEET.md, the file the F-003 patch changes); items in order a to f; patches F-003 and F-004 change no flow file (checked); item g moved to step 4a; est 30 for a to e with sub-minutes, (f) 60 separate.
- M7: new step 4a puts the lead's DECISIONS and N-9 to N-11 edits and the scene 4 sentence before step 5.
- M8: step 21 starts 07:40 inside the dated 07:30 to 09:30 block; slip post date Wed 25 Nov 15:00 UTC (ORDERS.md line 147); step 26 fail action names the latest retake gate (10:55 UTC); F-031 and F-007 are applied Tuesday and re-read 05:45 UTC, before the 06:00 start of step 18.
- M9: section 8 now has triggers T1 to T5 and ordered steps N1 to N7; the regenerated copy is defined (steps 3 to 13, new folder name, 171 min); the Wed 07:30 NO-GO has a path.
- M10: step 26 has recording start, stop and file check, the scene 4 cut rule, and a rehearsal test of the recording (step 23, I39).
- Citation nits: (1) clarified, see failure 1; (2) step 21 heading; (3) failure 7 now cites ORDERS.md line 132 "never downgrade by counting" and FINDINGS lines 115 and 117; (4) Sources line now Q25 lines 143 to 144, Q26 lines 146 to 147, Q27 lines 155 to 157.
- Also updated: header status, section 2 terms, section 3 limits (09:06 and 08:36), section 7 port row, section 9 (two bullets).

## Arithmetic re-run with python3 (script calc.py in the scratchpad rb4 folder; output pasted unchanged)
```
Tuesday sum 3 + 5 + 5 + 3 + 10 + 3 + 10 + 15 + 25 + 30 + 15 + 20 + 15 + 30 + 30 + 15 = 234 min = 3 h 54
1 04:00 UTC (09:30 IST) 3
2 04:03 UTC (09:33 IST) 5
3 04:08 UTC (09:38 IST) 5
4 04:13 UTC (09:43 IST) 3
4a 04:16 UTC (09:46 IST) 10
5 04:26 UTC (09:56 IST) 3
6 04:29 UTC (09:59 IST) 10
7 04:39 UTC (10:09 IST) 15
8 04:54 UTC (10:24 IST) 25
9 05:19 UTC (10:49 IST) 30
10 05:49 UTC (11:19 IST) 15
11 06:04 UTC (11:34 IST) 20
12 06:24 UTC (11:54 IST) 15
13 06:39 UTC (12:09 IST) 30
14 07:09 UTC (12:39 IST) 30
15 07:39 UTC (13:09 IST) 15
end from 04:00: 07:54 UTC (13:24 IST)
start to end 08:00: 04:06 UTC (09:36 IST)
resmoke 60 from end: 08:54 UTC (14:24 IST) from 08:00 09:00 UTC (14:30 IST) 90 slot 09:30 UTC (15:00 IST)
spare from end+60 306
spare from 09:00 300
spare from 09:30 270
repeat 171
latest step1 start 60: 09:06 UTC (14:36 IST) 90: 08:36 UTC (14:06 IST)
repeat shifts 60: 06:15 UTC (11:45 IST) 90: 05:45 UTC (11:15 IST)
second event end from 08:00: 10:51 UTC (16:21 IST) resmoke: 11:51 UTC (17:21 IST) 12:21 UTC (17:51 IST) spare 129 99
Wed block 07:30 + 10 + 100 = 09:20 UTC (14:50 IST) spare to 09:30: 10
rehearsal pieces 08:25 UTC (13:55 IST) 08:35 UTC (14:05 IST) 09:20 UTC (14:50 IST)
gate 09:20 UTC (14:50 IST) 09:45 UTC (15:15 IST) 09:50 UTC (15:20 IST)
take end 11:00 UTC (16:30 IST) S9-2 to 11:10 UTC (16:40 IST) edit to 13:10 UTC (18:40 IST) watch to 13:30 UTC (19:00 IST) S9-3 to 13:35 UTC (19:05 IST)
spare to post from 13:30: 90
latest take start 11:20 UTC (16:50 IST) 220
retake chain 235 latest gate start 10:55 UTC (16:25 IST) 245
chain 350 5 50
A 12:50 UTC (18:20 IST) margin 5:39:00
A latest end 12:39 UTC (18:09 IST)
A repeat 15:41 UTC (21:11 IST) margin 2:48:00 latest end with repeat 09:48 UTC (15:18 IST)
B event end 10:54 UTC (16:24 IST)
B take end 16:44 UTC (22:14 IST) margin 1:45:00
B repeat end 19:35 UTC (01:05 IST) latest start with repeat 05:54 UTC (11:24 IST) 755 no repeat 08:45 UTC (14:15 IST) 584
W-Tue 150 W-Wed 180
review wall 60 + fix 30 = 90
Tue spare after resmoke 60 from end with 14f 60: 246
```
Note: the line "Tue spare after resmoke 60 from end with 14f 60: 246" is 306 minus 60 (14f) before the 30-min fix pass; RUNBOOK section 6 uses 216 (also minus 30) and 180 from 09:30. Arithmetic done by hand: 306-60-30 = 216; 270-60-30 = 180; the window 08:54 Tue to 05:45 Wed = 15 h 06 min + 5 h 45 min = 20 h 51 min (computed by hand, not in calc.py).

## Checks after the edit (run from handover/flows-audit)
```
$ python3 -I tools/check_secrets.py   (exit 0)
PASS 0 hits in 1757 files
$ python3 tools/check_refs.py   (exit 0)
PASS 5147 references
```
Exit codes were read directly (`echo $?` after each run, not through a pipe).

Files changed: handover/flows-audit/RUNBOOK.md (237 lines), handover/flows-audit/fix-runbook4.md (this log). Backup: scratchpad bak-rb4/RUNBOOK.md. R-numbers cited: R448 (code last) not triggered; none of the bible was read (no bible folder in this checkout).
