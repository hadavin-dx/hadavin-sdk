# DRIFT REPORT (egm drift check on the review deliverables), 2026-11-16. Run by the lead with greps and the uncited_findings.py script, no file edited by the checker; the two drifts below were fixed afterwards.
## REVIEW.md, CORRECTIONS.md, LEDGER-ROWS.md against work/ and each other
- LEDGER-ROWS.md line 21 (CHR-MISS-06): the summary held "noqa|nosec|type: ignore", whose pipe characters split the row into 11 columns instead of 9. FIXED (now "for noqa, nosec, type: ignore"); re-check: all 23 rows have 9 columns.
- work/lead-notes.md line 16: said the sample was "every 5th ... 85 rows" (that would be 17 rows) while 10 were checked; REVIEW.md says the first 10 of 17. FIXED in lead-notes.md.
## Numbers that match (no drift)
- Ledger: 23 rows, 20 Major, 3 Nit, 22 OPEN, 1 FIXED-UNVERIFIED (CHR-PATCH-03). Header says 20 Major rows, 19 open.
- Rung table in REVIEW.md: 20 rows (same as verify-V5a.md).
- Uncited findings: script output 150 findings, 4 without a cite (D2-18, D2-19, D2-21, D3-22); REVIEW.md says 4 of 150, strictly 3 (D2-21 abbreviated cites).
- Lowered Majors: 7 (V1) + 5 (V2) + 8 (V3) + 4 (V4) = 24; tally 80 - 24 - 2 = 54, plus 3 lowered Blockers = 57.
- Cites past end of file: 15 raw (limits.py 9, factory.py:109 x3, prompt.py 2, test file 1); 9 distinct as REVIEW.md says.
- Patches: 5 files, 1 hunk each, `patch --dry-run -p1` rc=0 on a copy of AUDIT-FINDINGS.md equal to origin/cloud/core-hardening (work/evidence-ch-3-patch-dryrun.txt).
- Banned string search in the folder: 0 hits.
## Not checked by this drift run
Code facts inside the cited snapshot (the result reviewers did that, round 1 and 2); the 65 Nits; MASTER-MAP rows one by one.
