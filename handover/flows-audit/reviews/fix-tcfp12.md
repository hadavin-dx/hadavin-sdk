# fix-tcfp12: six Majors of reviews/fp-tc-stranger-r16.md (RUNBOOK, FIX-PLAN, TAKE-CHECKLIST). Static; nothing run; not committed.
Each reviewer line was re-grepped before fixing. Files edited: RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md only.

## M1 (CONFIRMED) two answer-by times
- Section 10 header (RUNBOOK ~334) now says: ONE answer-by per input (the Q31 item's), the "Needed by" column is first use only. Rows I2, I3, I5, I36 now lead with "Answer-by Tue 03:30 (09:00) (Q31 item 59 / 48)" and keep the 04:00 to 04:26 first-use time.
- Post-twice script: I first wrote "Wednesday input, not a Tuesday GO row 2 item" (item 58). The coordinator message then told me Q31 item 70 governs (Tue 09:00Z, answered by Tue 07:00Z; item 58 points to it). I REVERTED my change and aligned: GO row 2 requires the script and its two reviews; item 70 governs, item 58's Wed 05:45Z is superseded for it (RUNBOOK steps 6, 17 (2), W-Wed bullet, review bullet, I33, I48; TAKE-CHECKLIST Inputs "Needed by", GO row 2, line 99; FIX-PLAN step 10c line 104).
- ONE literal BLOCKED line everywhere: `BLOCKED: GO row 2: post-twice script and its two reviews (Q31 item 58)` ("answer-by Wed 05:45Z" removed from the RUNBOOK review bullet).
- NOT FIXED, needs the lead: RUNBOOK W-Wed still counts the 30 min of writing the post-twice script with latest end Wed 05:45Z, but item 70 needs it by Tue 09:00Z; W-Tue does not budget it. I did not change the sums (they feed the Tuesday latest-start arithmetic). the RUNBOOK W-Wed bullet says "the lead decides, I33". Next step: lead says who writes it before Tue 09:00Z.
- Q31 items I would like in the Q31 fixer's log: none missing for M1.

## M2 (CONFIRMED) tags
- RESULT_JSON now `REPLACE_ME_Q31_71` (item 71 = I18 inputs incl. result file); RECORDING now `REPLACE_ME_Q31_72` (item 72 = recording inputs); REPORT now `REPLACE_ME_Q31_67`. Both were also changed to `${NAME:-...}` form so a value typed per take survives re-sourcing. I18 and I39 rows and the RECORDING definition name items 71 and 72.
- Note: TAKE-CHECKLIST was grepped for Q31_4 / Q31_38 tags on these names: none.

## M3 (CONFIRMED) overwrite guard
- RUNBOOK step 26 now starts with (0): `if test -e "$RECORDING"; then echo "REFUSED: ..."; else echo ok-new-recording; fi`.
- Step 22 test recording uses a new name TESTREC (skeleton line `TESTREC="${TESTREC:-$TAKE_FOLDER/test-recording.mp4}"`) with its own `test -e` guard (`ok-new-testrec`); pass line reads `found-recording` from `$TESTREC`.
- RECORDING, TESTREC, RESULT_JSON added to the per-run-names list.

## M4 (CONFIRMED) saved-log wrapper
- Step 11: title + saved-log sentence (`{ LOOK_COMMAND; echo "exit $?"; } >> "$TESTLOG" 2>&1`). Step 15: title + one `echo >> "$TESTLOG"` line. Step 16: sentence naming the wrapped checks (gate checks use `$GATELOG`). Step 17: (3) four commands and (6a) psql wrapped, title says where each pass is read. Step 19 (a),(b) psql wrapped ((b) also got the missing `psql`), (c),(d) say same wrapper. Step 24 (a),(b) wrapped with `$GATELOG`, (c) to (e) same wrapper.
- Reviewer minor (steps 5, 13 print `take_check exit N` outside the redirect): checked; the exit line is a pass line printed to the terminal AND the take_check output is in `$LOG`/`$LOG2`; the exit number is not in the saved file. NOT changed in this batch: needs `{ ...; echo "take_check exit $?"; } >> "$LOG"` and would change the count patterns of Block R4/R4f (TAKE-CHECKLIST). Next step: next round, together with those blocks.

## M5 (CONFIRMED) step-log lists
- FIX-PLAN line 72 list is now 0, 1, 2, 3, 3a, 4, 4c, 6, 7, 9b = RUNBOOK 1, 2, 3, 4, 4a, 4b, 6, 9, 10, 14; its steps 4d, 5, 8a (= RUNBOOK 7, 8, 11) write `$TESTLOG`, said in both places. RUNBOOK "The step log" now lists 11 and 15 among the own-log steps.

## M6 (CONFIRMED) pathspec
- RUNBOOK step 4 commit now `... -m "$TRAILER" -- handover/demo/n8n-mainframe/build_mainframe.py handover/demo/"$NEW"`. Siblings fixed the same way (class): step 4b and 13 (`-- handover/flows-audit/flow-check/take-warns.pin`), steps 4a and 14 (g) (`-- FILE1 FILE2`).

## Checks
- `sed -n 14,47p FIX-PLAN.md` vs `sed -n 8,41p TAKE-CHECKLIST.md`: `diff | wc -l` -> 0 (clock block untouched).
- `python3 -I tools/check_refs.py` -> `PASS 5166 references`. (No check_refs.py at flows-audit root; it is in tools/.)
- No command was run against n8n or a database; new commands not even `bash -n` checked.
- QUESTIONS.md read only; Q31 items 67 to 72 used as given.
