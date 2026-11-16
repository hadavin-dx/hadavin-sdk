# c6o independent evidence (EVIDENCE RUNNER, condensed copy of the report), 2026-11-16
Target: c6-skip-audit/REPORT-c6o.md, sha256 f9ecdfe3a1952e0913a0135460a10de158b187c75d16cdad503eeceacd0be7b4 (unchanged before and after). Raw output: c6-skip-audit/evidence-c6o-independent/ (00-SUMMARY.md). Recorded, not judged.

## Caveats first
1. The audited source files (video run-sheet, n8n flow files, mainframe files) are not in the repo checkout under handover/demo. Rows were checked against the scratchpad copy that the builder's own verify script uses; it could not be shown equal to the files the lead will edit. Only the DECISION-one-store.md rows were checked against the repo file.
2. The runner's first checker run had 4 FAILs that were bugs in its own checker (fixed); two of its mutations first failed for the wrong reason (corrected).
3. The builder's neg-controls script was run from a copy writing to builder-run/neg-redirect/.
4. The 10 done / 8 unknown split of the 18 kept runs is not in results.jsonl (no end-state field); it comes from raw-lane3/RESULTS.md.
5. Not checked: whether the 328 cites exist (only the builder's script checks them); the flow-file saving values (C-4a); whether any new text is true; the NOT FILMABLE reasoning; wording.
6. Git note: indep_check.py had already been committed by an earlier wip commit while the runner was working; the runner's final version replaced its own earlier file (not another agent's file).

## Results
- Independent checker: 28 PASS, 0 FAIL. 94 rows; old text once on its stated line for all 94; ids 1..94; rows apply in table order; counts 94/49/40/3/2 match section 0, the 3b TOTAL, prose and the 89 wave-1 rows.
- 21 explicit UTC = IST pairs all +5:30; 22 UTC clock times each have IST on the same line; 15 weekday/date strings correct for 2026; 23 ISO dates in 2026.
- "60.1 to 61.9" 23 times and "52.8 to 54.9" 5 times, no variants.
- Builder scripts as-is: verify-c6o.py 60 checks 0 FAILED; void-check.py 18 kept runs, 2 voided; neg controls 24 copies 0 wrong.
- Re-derivation from raw results: 20 crash runs at lease 45, 2 voided (VOID-fl45k6c fakes_not_up; VOID-fl45k3b 338.7 s never final), 18 kept; kill-to-final 60.1 to 61.9 s; recovery 52.8 to 54.9 s (counting the voided run would give 60.1 to 338.7).
- 24 planted mutations plus 1 control: all caught.
- Banned scan 0 in the report and 0 across 63 evidence files; secret-shape scan 0.
