# Owner sheet v36 builder hand-back (condensed copy), 2026-11-16
## Failures and gaps first
1. Full plant run mut36.py (about 330 plants) was not finished at hand-back (pid 22677 under heavy-slot): 230 caught, 0 missed, 1 ANCHOR-NOT-FOUND (X23: stale v35 sentence in the repoint table, fixed after the run started). Need the TOTAL line and one clean re-run through heavy-slot.sh.
2. Two queued wrappers (fail-proof, gap-proof) would overwrite evidence; the direct outputs (evidence-v36/fail-proof-direct.out, gap-proof-direct.out) are the evidence. I stopped the two queued wrappers (pids 22680, 22682).
3. No independent evidence runner or egm reviewer has seen v36. Nothing live was run. Vendor paths and words, the cancel-only role, Recall, how the lead starts and stops the model program, the 55-minute window: UNVERIFIED.
4. Own slips: first build over every cap (sheet A 6,494, total 15,851), fixed by moving text; banned wording "told" fixed; 13 existing pinned checks re-pointed (listed in v36-CHANGES section 3; lead must confirm none was weakened without a design reason). Stale "v19" prose in LEAD-RELEASE-NOTE-v20-SOURCE.md.
## Results
check-v36.py 0 failures (C01-C297, incl. banned and secret scans); v36-fail-proof: 23 checks fail on built v35, 0 on v36; gap-proof: v35 checker misses 0 of 15, v36 misses 0 of 15.
## Fixes
S1 (C281) no key until helper phones both written words or card says helper none; S2 (C282) one explicit cancel-only rule, helper never does the last-resort step; S3 (C283, C297) alarms 5 and 6 repeat every 5 min, DND off, second device (named helper vs earlier human stop time = Open 132); S4 (C284) row 121 corrected, new row 133 (7.11 cancels regardless of last use). m1-m6 and stranger M2, M3, M5-M9, M11, M12, M14 fixed with checks. Lead decisions Open 134-139: page split, who verifies the three statements, 450-word yes, latest key-create time, exit-code rule, M10/M13/nits; rows 123 and L-LEN untouched.
## Reading load
Sheet A 6,270 (cap 6,286); five pages A 15,711 (cap 15,715); B 15,348.
