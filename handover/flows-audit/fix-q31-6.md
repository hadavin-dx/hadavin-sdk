# fix-q31-6 (flows-audit fixer; static, nothing run in n8n or Postgres; only QUESTIONS.md edited; not committed)
Source: reviews/fix-tcfp13.md "Lines for Q31" (9 lines), RUNBOOK.md steps 4a, 7, 8 (0), 18 (1b), section 8, FIX-PLAN.md Tuesday-inputs table, ORDERS.md lines 156 and 166.

## Done
- New Q31 items 78 (DB_SETUP, due Tue 04:54Z), 79 (data folder holds the three n8n credentials, due Tue 05:14Z), 80 (step 4a (2), due Tue 04:16Z), 81 (step 4a (3), due Tue 04:16Z), 82 (SECOND_ADMIN, due Wed 05:45Z). Layout as items 74-77 (answer-by UTC and IST, who answers, IF UNANSWERED as "AUDIT PROPOSAL, lead to confirm", RUNBOOK steps that wait named in each item).
- Item 55: time conflict (Wed 05:45Z against RUNBOOK I47 (a) / I49 (a): Tue 04:00Z, first use Tue 08:29Z) written as a question to the lead; the audit does not pick a time; item 55 also listed in the index 04:00Z row (only if the lead chooses that time).
- Item 66 index: item 33 IF NOT line corrected (need_set prints REFUSED; "stop with unset" was stale); new items added to the 04:16Z, 04:54Z, 05:14Z and Wed 05:45Z rows; "items 67 to 77" now "items 67 to 82".
- Item 6: plain correction added (RUNBOOK section 8 counts 367 minutes Case A, 422 Case B, not 355). Take = last 60 minutes, so the take starts 307 min (Case A) / 362 min (Case B) after the re-pin end. Latest re-pin END for take start by 11:55Z: Case A 06:48Z (12:18 IST), Case B 05:53Z; for the 12:00Z limit (ORDERS.md 156 item 7): 06:53Z / 05:58Z. A re-pin end at 07:00Z (ORDERS.md 156 item 6, read as END) gives a Case A take start 12:07Z, 7 min after the limit. RUNBOOK section 8 checks only the credits stop (12:22Z), not the 12:00Z limit. ORDERS.md line 166 (Q28) holds no timing. Four options put to the lead; none chosen.
- Counts updated by script (QUESTIONS.md lines 40, 42, 449, 597): main list 75 numbered items (numbers 1 to 39 and 47 to 82): 73 OPEN, 1 ANSWERED (item 20), 1 NOTE (item 66); second list 7 (1 OPEN, 1 ANSWERED, 5 NOTE); plus 15A (OPEN): 83 labelled, 75 OPEN. Script output: keys 82, OPEN 74 (+15A = 75), ANSWERED 2, NOTE 6, main 75.

## Checks (run after the edit)
- python3 tools/check_refs.py: PASS 5166 references (exit 0)
- python3 tools/check_names.py: PASS 655 rows (exit 0)
- python3 tools/check_secrets.py: FAIL 1 hits: flow-check/raw/test-take-check.txt:178 token-like (length 47) (exit 1). Not from this batch: that file was modified at 14:59Z by another session and QUESTIONS.md was not part of the hit. Not fixed here (outside the allowed file); needs the owner of that file.

## Not done / uncertain
- Nothing run against n8n or Postgres. The minute figures are RUNBOOK's estimates. No step-clock time of the new items was checked against a later RUNBOOK edit.
- FIX-PLAN table, RUNBOOK and TAKE-CHECKLIST were not edited (not allowed): they do not yet list items 78 to 82 (FIX-PLAN Tuesday-inputs table needs rows for 78, 79, 80, 81; RUNBOOK step 4a/8/9/18 text still says "new item needed").
- Item 71 correction (line 2 of fix-tcfp13 "Lines for Q31"), line 7 (item 30) and line 9 (Case B 12:22Z vs owner sheet 12:00Z) were not in this brief and are not done.
