# c6u changes (builder c6u, round 5, non-security path). Written 2026-11-16T18:23Z = 2026-11-16T23:53 IST

## FAILED OR OPEN FIRST
1. m5 (stale run sheet leftovers) is NOT FIXED. The lead marks them or asks for rows. REPORT-c6u.md section 0 item (10) says so.
2. G12 status is a question to the lead (section 0 item (9)). Not decided by me.
3. Old reports: the c6u verifier exits 1 on REPORT-c6t.md, c6s and c6r (105, 120, 145 FAILED in an earlier run, before the last fixes). I make no pass claim for them. I did not re-run those three after the final fixes.
4. Rows are checked only against the scratchpad copy of the demo tree (variable C6U_TREE). 91 of 96 rows name files this branch does not hold, so equality with the real files is UNVERIFIED.
5. Row count is 96, not the brief's 95/37/86, because row 96 (M3) was added. Counts: ready 49, on default 38, wave 1 = 87.
6. No EGM reviewer has read REPORT-c6u.md. All checks are builder-run.
7. Other sessions rewrite the owner sheets and release notes. Re-run run_all.sh last, with C6U_TREE set.
8. E-mail finding: only masked fragments (de..1@gmail.com, de..2@gmail.com) exist, inside copies of old owner sheets in evidence-c6u/steps-snapshot/ (copies of other sessions' files). No full address anywhere. Not removed, since they are verbatim copies used for tie checks. The lead may delete the snapshot after review.
9. Banned-vendor scan of REPORT-c6u.md and evidence-c6u: 0 hits (10 strings read at run time).

## What was done
- Extended c6t into c6u (evidence-c6u/): build_c6u.py, c6u_box.txt, verify-c6u.py plus part 2, neg_controls_c6u.py, run_all.sh, static-checks.sh.
- Fixed review-c6t-design M1-M5, m1-m4, m6-m8; review-c6t-naive B1-B5, M1-M10; late evidence items (mutation misses, run_all inputs and tree variable, loud failure on v32/v16, gmail check).
- Last full run (C6U_TREE set): verify exit 0, 221 checks, 0 FAILED; negative controls exit 0, 221 copies, 0 wrong, 0 skipped.
- REPORT-c6t.md untouched (sha256 starts 25f3dc35d6b5). Box 2381 words (cap 2500).

## How to run
cd evidence-c6u; export C6U_TREE=<path to the audited handover tree copy>; bash run_all.sh. No machine path is stored in the files.
