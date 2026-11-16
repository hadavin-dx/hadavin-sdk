# fix-planfiles34 (round 34, fixer on RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md)

## NOT done or uncertain (read first)
1. Clash left for the lead: QUESTIONS.md Q31 items 27 and 30 hold the Monday-night ask as default. The three plan files now hold the Wednesday ask (AUDIT PROPOSAL, lead to confirm, RUNBOOK section 10 M7 (a)). I did not touch QUESTIONS.md.
2. Times marked AUDIT PROPOSAL, lead to confirm: positive-control command due Tue 09:00Z (Wed 05:45Z only the last change); Step D reply-by times (Wed 09:15Z and 13:30Z); rehearsal count decided Tue 04:00Z, last change Wed 07:40Z.
3. Nothing was run on n8n, Postgres or HubSpot. Shell blocks are only syntax-checked with `bash -n`; their behaviour is unproven.
4. Bare "item N" qualification: NOT finished as a full sweep. I qualified the ones named in the findings (step 6, section 10 M7, step 10c, Q31 items). Many remaining "item N" mentions already name a source (ORDER 037, DECISIONS, OWNER-STEPS, Qnn); a few bare ones may remain in RUNBOOK lines 34, 214-220, 378-422, FIX-PLAN lines 103-200, TAKE-CHECKLIST lines 93-198. Not checked one by one.
5. `bash -n` on inline backtick commands: 3 of 123 fail, all are pattern descriptions with placeholders (`need_set NAME ... &&`), not commands to paste.
6. Slip found: the TAKE-CHECKLIST claim "ASCII only; Jose with accent rejected" was wrong (helper `--check-reviewer-line` accepted Jose, Anna, AI on made-up lines). Replaced by pointers to `--reviewer-words` and `--check-reviewer-line`. I did not re-read `reviewer_ok` again after the final edit.
7. My Clock edits in TAKE-CHECKLIST rows 48, 49, 52 first made the two Clock blocks differ; fixed by copying the block into FIX-PLAN (diff now empty).

## Fixed
- Reader 1,3,4,5,6,7 (one due time per input, earlier-time rule): RUNBOOK section 10 M7 (a)-(g), section 8 T4, step 24 Fail cell, step 6, I12/I14/I25/I32/I34, FIX-PLAN line 1, Steps 4c, 9b, 10b, 10c, TAKE-CHECKLIST rows 48, 49, 52, line 59 items 7, 8, 16, 17.
- Reader 2: line 6 and RUNBOOK 17.6: unchecked gate (e) allows a Tuesday GO only with `JUDGED step 16 check gate-e result not-checked-scope-pending`, read back with a guarded grep count.
- Reader 8, 9: Wednesday windows and lengths in item 14; reply-by per Step D message; post without reply rule.
- Reader 10: step 16.6 passes only on the exact refusal line (`grep -c -F` = 1 and `grep exit 0`); guard refuses SAME_ARGUMENTS_AS_STEP_7; GO row 5 (c) matches.
- Shell M1 ($LOG.pin0), M2 (FIX-PLAN Step 4c guards), M3 (R6/R6j counts from ledger), M4 (new Block R3L lint, 3 lines `rc=0`), M5 (pointer to `--reviewer-words`).
- Guards (need_set group plus positive or `grep exit N` line) added to RUNBOOK steps 6, 11, 13, 15, 16.2, 17.1, 17.3, 18, 21, 22, 24; 17.4 paths aligned with step 2; 16.1 need_set before printf.

## Outputs (from handover/flows-audit)
- check_refs: PASS 5182 references
- check_names: PASS 655 rows
- check_secrets: PASS 0 hits in 2787 files
- check_counts: PASS 52 files / 655 nodes
- check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: RESULT: PASS
- ruff format --check .: 913 files already formatted
- Clock block (48 lines from the bold Tuesday 17 Nov line): diff FIX-PLAN vs TAKE-CHECKLIST printed DIFF-EMPTY
- bash -n: 28 of 28 code fences ok; 120 of 123 inline commands ok (3 placeholder descriptions, see 5)
- Not committed.
