# fix-checklist3 (TAKE-CHECKLIST.md vs reviews/checklist-stranger-r2.md), 2026-11-16
Backup of the old file: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-chk3/TAKE-CHECKLIST.md

## Failures, doubts, not checked (first)
- Nothing was run (static edit). No grep or command in the new file was tested.
- Conflict, not resolved: take_check.sh header (line 14) says an environment override (TAKE_CHECK_WARN_PIN, TAKE_CHECK_FLOWS) gives exit 4 unless TAKE_CHECK_TEST=1, but the code at read time did not yet enforce it and the brief tells me to use TAKE_CHECK_WARN_PIN. I wrote the folder as `--flows` (documented) and the pin as TAKE_CHECK_WARN_PIN with a note that the lead confirms at the first run.
- Item 1 of the report (ACCEPTED line = 1): confirmed by reading the script (line 98 prints it in the top block, line 182 cats the full output again); pass lines now say "at least one" and a count field "____" for the lead.
- Item 14: "take_check.sh:19 comment contradicts Row 1" could not be located (file changed, line 19 is now code); stated as such. ORDERS.md:20 text is about the one database/executions deleted at clean-up: listed as stale. PLAN-4:106 (handover/demo) line read does not mention deletion of runs in the cut I printed (it is about the notice and archiving contacts); I listed it because Q25-13 names it; unverified that line 106 is still the stale one.
- Row 3 check A (HubSpot read-only, result.json): no command exists in this tree; marked NOT CHECKED until the lead writes the line. Row 4 failed-attempt Step D handling is not written anywhere; stated so.
- "Decision 4" mismatch: ORDERS Q18 and take_check.sh use it for the recovery accept; inputs/DECISIONS-2026-11-16.md item 4 is about C5 core patches. Flagged in the words box, not resolved.
- Row 8 clock start (n8n start) and the +2 to 3 h placement are my reading, marked "lead confirms".
- Wed practice run content is defined in no file; stated, not invented.
- Not checked: whether VIDEO-RUNSHEET.md exists at a path in the real tree (only scratch copies found); the run-sheet greps in row 7 therefore take a path the lead fills in. The Row 7 digit grep had a wrong pattern (`\|` under -E); fixed to `60\.8|60\.1|61\.9`, still untested.

## Row-by-row (report item -> fix)
1 pass lines at-least-one, count blanks; 2 pin on exported copy with --write-warn-pin to NEW file then TAKE_CHECK_WARN_PIN, committed pin untouched; 3 folders defined in words box; FIX-PLAN steps 1-3 and fill_flows named; 4 glosses for all listed codes; 5 GO/NO-GO list named (FINDINGS counts table), take path defined; 6 row 2 split into gates with pass lines, two logins defined; 7 row 3 commands (grep -rlF with control), check A marked NOT CHECKED; 8 row 4 contact id, four checks written, parts 1-3 defined, Step D message after all four pass; 9 rows 5-6 post 2 timing, mailbox, which mail, attempts blank; 10 row 7 one caption on screen and card, label of proof screen separate; 11 row 8 takeover defined, one limit 3 min; 12 row 10 "not found" accepted, how leftovers are listed; 13 re-smoke vs practice run separated; 14 stale list extended; 15 +2 to 3 h placed on schedule.
