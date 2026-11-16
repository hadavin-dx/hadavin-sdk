# fix-fixplan4: FIX-PLAN.md after the readiness read (B1, M1 to M6, N1 to N5) and the Q26 answer

## Failures and what was not checked (first)
- Nothing ran: no take_check.sh run, no n8n, no psql. Every command text is checked by reading take_check.sh, flow-check/README.md, fill_flows/README.md, check_patches.sh and mf_leads.sql, not by running it.
- Step 9 now says the first take_check run on a filled export exits 4 (the WARN set changed). That is read from take_check.sh lines 140 to 152, not observed. Which placeholder WARN lines vanish is read from take-warns.pin lines 2, 6, 10; the real list is for a person to read.
- The `RESULT: 0 FAIL` and `WARN set equals the pinned set` greps in step 4 are read from the script's echo lines (147, 161); the WARN count y and open items N are left for the first real run.
- M5 is only partly settled by text: the lead's Q25-2 says to use the scoped caption on screen and card; the Q24-5 caption 'one mail sent, one row in state done' is kept as the label of the proof screen. Whether the lead wants Q24-5 dropped is not stated in ORDERS.md; the lead confirms at re-pin.
- Q26-3: whether scripts/n8n_api.py exists in the final tree is unknown; the plan says 'lead provides at re-pin'.
- Not verified: run_all.sh line 56 and evidence-q18.md lines 143 to 165 (the old plan cited them; the new step 4 no longer does).

## What changed (backup: scratchpad bak-fp4/FIX-PLAN.md)
- B1: step 4 explains the WARN pin and adds pin, RESULT and FINAL lines to the pass test; step 9 and step 15 document `--write-warn-pin` plus `TAKE_CHECK_WARN_PIN`, and say a person reads each changed WARN before the export pin is written.
- M1: step 4 and lead fixes rewritten to the current script (KeyOk detected automatically, 15:14 without a variable, missing KeyOk exits 4, `--patch-checks F002` passed, exit 0 now proves both patches); line numbers corrected (INFO text is line 69). Old lead fixes that are done are listed as done.
- M2: explicit cd and return in step 2; `diff -r -x V5-README.md -x V5-NODE-DIFF.txt`, with the two expected 'Only in' lines explained.
- M3: decision: T19 keeps its OWN fixed 10 s test bound (already in the F-002 row of FINDINGS); it is not the take's 10 s line set in step 12. Rule (b3) says so.
- M4: new step 10b (real-HubSpot made-up lead before rehearsal 1) with three pass parts that can fail; rehearsals not in real HubSpot by default.
- M5: scoped caption 'In this recording, the same lead ID sent twice gave one e-mail message.' in rule (b4); proof wording in rule (b).
- M6: 3-minute scene 4 cut rule in step 12; no phone filming and no on-screen timer in rule (f).
- N1 scratch folder note (step 0); N2 mf_leads.sql is a plain CREATE TABLE, second run fails harmlessly (step 5); N3 README copy-paste setup (step 6); N4 step 7 pass wording; N5 INFO lines print once because of --quiet-info (step 4).
- Q26: two-path schedule with UTC and IST, r20/r21/r22 in plain words, scripts 'lead provides at re-pin', GO/NO-GO Tue 17 Nov 14:00Z (19:30 IST). Not in the readiness report but done: the saved-runs paragraph and rule (h) cite line 69 instead of 60.

## Verification (run from /home/user/hadavin-sdk)
- `sh handover/flows-audit/tools/check_patches.sh` printed `PASS 4 patches`.
- `python3 -I handover/flows-audit/tools/count_findings.py handover/flows-audit/FINDINGS.md` output md5 74315130723eab04c9071681ff58196c before and after (unchanged).
- FIX-PLAN.md is 71 lines (long lines). Only FIX-PLAN.md and this log were written. EGM skipped for the edit pass: the lead runs the review step.
