# fix-runbook54: round 54 fixes for RUNBOOK.md only (static; GUARD, WORDING and CONSISTENCY edits; nothing run in n8n, Postgres or HubSpot; made-up data only)

## Gaps and failures first
- NOT everything was fixed. About 40 of roughly 95 reader items are fixed or turned into a `LEAD DECIDES` line; the rest are listed below as "not fixed" with the reason. Rows are up to 20,000 characters and the brief had a 60-minute box.
- Rows 306 to 433 (I7 to I58 and section 9 details) were NOT judged by reader r54 (only first 160 characters seen): they still need a second reader pass. Not done by me.
- Two new commands were written and tried only on made-up files in a scratch folder (bash -n plus a run): step 3 file-by-file check (prints `differs-ok-...` / `same-ok-mf-recovery.json`), step 7 health check (prints `n8n-ready` or `n8n-DOWN`; tried against a closed port: printed `n8n-DOWN`). Not run on the real tree or a real n8n. The step 13 (g) `status-clean` command was moved from existing text, not newly tried. The RC13 guard and the step 13 sub-step were not run.
- New time figures (step 4b-wait shifts 05:18Z / 05:38Z, the table of section 8) are arithmetic on the file's own numbers (checked by hand: 12:00 minus 307 = 06:53, minus 362 = 05:58, minus 146 = 04:27 and 03:32), not measured.
- Backup of the file before the round: scratchpad fix54/RUNBOOK.bak. Round history moved to reviews/runbook-changelog.md (status paragraph of line 3, 15 [HISTORY] items of section 1 with stubs that keep their numbers, the two OLD FORM `git checkout` commands of step 13).

## Items (fixed / needs LEAD / not fixed)
### r50 (lines 1-220)
- M1 no "start here": FIXED (START HERE paragraph after the status line; status shortened; history moved).
- M2 first-time setup not pasteable ($KEEP files, FIX-PLAN Step 0a): NOT FIXED: needs the lead's values and FIX-PLAN.md (not my file).
- M3 step 1 start condition: FIXED (Block R3 prints `evidence-sha-written`, checked present in TAKE-CHECKLIST.md; due 03:30Z (09:00 IST)).
- M4 JUDGE_WHO / PIN_NAME supplier: FIXED as LEAD DECIDES lines (PIN_NAME by 03:30Z (09:00 IST); JUDGE_WHO by 03:30Z (09:00 IST), AUDIT PROPOSAL same person as PIN_NAME). Needs LEAD.
- M5 (e) NOT CHECKED vs where gates run: NOT FIXED: needs LEAD (Q31 item 30 and the Tuesday re-smoke and T19-T21 gates).
- M6 07:44Z rehearsal 1 two readings: NOT FIXED: needs LEAD (which clock; one gate fits).
- M7 step 3 eyeballed pass: FIXED (file-by-file `cmp` words; exit 1 of `diff -r` named as the one exception).
- M8 steps 1-3 show no wrapper: NOT FIXED (section 4 "The step log" holds the wrapper; no pointer added in the rows).
- M9 send ceiling supplier: FIXED as LEAD DECIDES (by 08:29Z (13:59 IST)). Needs LEAD.
### r51 (rows 3-7)
- F1 row 6 fixed or moving: FIXED (they move; with a full wait 05:18Z and 05:38Z).
- F2 FILES list per paste: FIXED in step 4a and step 14.
- F3 inputs (1)(2)(3) supplier, "decision 1 vs 4", "scene 4": NOT FIXED (needs the Q31 item texts).
- F4 PIN_NAME unnamed, "Anna Smith": FIXED (marked MADE UP in step 4b and in shas.env; LEAD DECIDES). Needs LEAD for the name.
- F5 route A/B default: NOT FIXED. F6 Block P1b heredoc location: NOT FIXED (both live in TAKE-CHECKLIST.md, not my file).
- F7 six files in TWO sets: FIXED (one due list with sets named). F8 step 6 pass with two files: FIXED as LEAD DECIDES (AUDIT PROPOSAL: yes). F9 due times: FIXED (one list); "fifth sha" stays I24 (LEAD).
- F10 SHA_SCRIPTS silence: FIXED (printed pass, manual sha line). F11 steps 6-7 LEAD FILLS without owner/time: PARTLY (owner and due times written; the values themselves still LEAD FILLS, step 7 BLOCKED until supplied).
- F12 step 7/8 order clocks: FIXED. F13 step 7 pass: FIXED (`n8n-ready` / `n8n-DOWN`).
- F14 eight counts / counts-ok word: NOT FIXED: needs TAKE-CHECKLIST.md Block R4 to print the word (not my file).
- F15 history in cells: PARTLY (section 1, status line, titles of steps 11, 15, 17, OLD FORM of step 13); many "round N" notes remain in cells; no mass removal because many hold live commands.
### r52 (steps 8-17)
- 1, 2, 3, 4, 5, 8, 9, 10, 11, 18, 19, 21, 22, 23: NOT FIXED (need the lead's decisions, missing writers/times, or TAKE-CHECKLIST.md blocks; each is a real gap).
- 6: PARTLY (the two OLD FORM commands removed to the changelog). 7: FIXED (OLD FORM removed; status-clean is sub-step 13 (g) with a pass line). 12: FIXED (step 14 state BLOCKED-by-I34, I35, I5 for (a) and (b)). 13: FIXED (05:45Z before step 18 at 06:00Z).
- 14 (F-003 closing step): NOT FIXED: needs LEAD (one closing step). 15 (latest start vs 08:29Z): NOT FIXED. 16: FIXED (six files). 17: FIXED (BLOCKED-by list extended with I1, I38, I55, I57).
- 20: FIXED (three vertical bars removed from cells of steps 6, 14, 17; every table row of section 5 now has 10 bars, checked by script). 24: FIXED (titles name `$JUDGELOG`). 25: NOT FIXED (terms are in section 4; no extra definitions added).
### r53 (steps 18-30)
- M1 12 or 11: FIXED. M2 fourth gate: FIXED as LEAD DECIDES (add 4 min or answer no). M3 50 to 60 min: FIXED in both places (20 + 15 + 25).
- M4 N defined twice, M5 scene 4 not tested, M6 SECOND_ADMIN blockers, M7 compare-by-eye commands, M8 JUDGE_WHO/FINAL_SHA suppliers, M9 RESULT_JSON order, M10 R5e counts, M11 split of the 20,000-character step 18 cell, M13 clean-up time: NOT FIXED (need lead inputs or a large restructure of rows I did not reach).
- M12 Case A/B defined late: ALREADY covered by the round 48 Terms bullet (checked present); no change. M14 terms: ALREADY partly covered; no change.
### r54 (lines 300-433, partial)
- B1 governing deadline: FIXED as a table in section 8 plus LEAD DECIDES (which lead rule gives way, by Tue 17 Nov 14:00Z (19:30 IST)) and an operator stop rule (AUDIT PROPOSAL). Needs LEAD.
- B2 6-8k paragraphs: PARTLY (table added at the head; the long paragraphs are relabelled COMMENTARY and "my reading" changed to "this audit's reading"; not split or moved).
- M3 clock model: FIXED (N6 states fixed times apply only if the chain can start at them; else back to back; LEAD DECIDES). M4 which re-pin: FIXED as LEAD DECIDES (steps 1 to 15 run again under N4). M5 zone labels: FIXED for all 108 pairs of section 10 (`HH:MMZ (HH:MM IST)`); "Block R3 outside the clock" not changed.
- M6 T3/T4: PARTLY (T3 how to tell apart; T4 trigger reading, AUDIT PROPOSAL); "S9-2" and N2 chat not defined beyond I45 pointer. M7 NO-GO default: FIXED (stop and ask the owner). M8 re-check column: PARTLY (RC1, RC2, RC8, RC13 guard, tick rule; RC12/RC15 untouched).
- M9 section 9 owner/deadline: FIXED (owner lead, deadline before the first step that reads the text, operator follows this runbook). M10 I5/I6 owners: NOT FIXED. M11 TAKE-CHECKLIST times 09:50Z/10:00Z/11:00Z vs runbook: NEEDS LEAD (TAKE-CHECKLIST.md not mine).
- Rows 306-433 not judged by the reader: second pass needed.

## Checkers (run from this folder, python3 -I tools/<script>)
- check_refs: PASS 5190 references
- check_names: PASS 655 rows
- check_secrets: PASS 0 hits in 2962 files
- check_counts: PASS 52 files / 655 nodes
- ruff format --check .: 1087 files already formatted
