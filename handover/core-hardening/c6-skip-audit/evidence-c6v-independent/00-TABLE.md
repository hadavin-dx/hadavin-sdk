# 00-TABLE: independent evidence for c6v (EVIDENCE RUNNER; records only, no judgement)
Folder: handover/core-hardening/c6-skip-audit/evidence-c6v-independent/ . Started 2026-11-16T19:06:49Z (= 00:36:49 IST). Last entry 19:27Z. Load average at start 3.55 (1 min), at neg run 2.0 to 2.8. REPORT-c6v.md and c6v-CHANGES.md md5 before and after: identical (pre-md5.txt). I did not run build_base.py or build_c6v.py (they overwrite REPORT-c6v.md).

## Deviations and failures first
1. LIVE verify now FAILS 4 checks (verify-live-final.txt, 19:25:37Z): OWNER-SHEET-v34-A.md, v34-B.md and LEAD-RELEASE-NOTE-v18.md have file times 19:14:05Z, after the report's check time 19:04:44Z. Content is byte-identical to my 19:07Z copy (cmp, lines 8/33/149/150 same); only the time changed. So "0 FAILED" is true for the 19:04Z state and for my 19:07Z snapshot, NOT for the live tree at 19:25Z. The report's own staleness rule fires.
2. My neg run: 267 copies, 1 wrong (V0-control-unchanged) because I had deleted contact-grep-output.txt from my copy (a file the report names). With that file regenerated, verify on the unchanged report with my snapshot = 238 checks, 0 FAILED. The V0 line in neg-output.txt is therefore my own artifact, not a builder defect; I did not re-run all 267 (another 16-minute slot wait).
3. Builder scan_c6v.py run inside my folder reports mail 39 on 416 files: all 24 hits are in my own steps-snapshot copy of the sheets (example.com 80, example.net 8, gmail.com 31 shapes, local parts 1 character), not in the report or the builder files. First run (before my snapshot) was 0/0/0.
4. Slot wait for neg run: queued 19:07:12Z, slot 3 taken 19:23:43Z (16.5 min). Other agents held all 3 slots.
5. verify-c6v.py on REPORT-c6u.md: 34 FAILs now (builder said 32; the 2 extra are the live file-time checks of item 1; at 19:07Z I counted 32).

## Runs
| # | Command (in my folder) | Start UTC | Exit | Output |
|---|---|---|---|---|
| 1 | bash static-checks.sh | 19:07:07 | 0 | static-checks-output.txt; rerun 19:25 exit 0 (static-checks-output2.txt), newest sheet v34, release note v18 |
| 2 | python3 -B -I verify-c6v.py (19:07, my folder lacked 4 report-named output files) | 19:07 | 1 | 238 checks, 1 FAILED (only the "names exist" check, my folder state) |
| 3 | same, with C6V_STEPS = my 19:07 snapshot, after neg run and contact-grep file | 19:25 | 0 | verify-snapshot-final.txt: 238 checks, 0 FAILED |
| 4 | same, live steps-edits | 19:25 | 1 | verify-live-final.txt: 238 checks, 4 FAILED (item 1) |
| 5 | verify-c6v.py ../REPORT-c6u.md | 19:07 / 19:25 | 1 | 32 FAILs / 34 FAILs |
| 6 | sh heavy-slot.sh python3 neg_controls_c6v.py (snapshot env) | 19:07:12 queued, 19:23:43 slot 3 | 0 | neg-output.txt: 267 copies, 1 wrong (item 2), 0 SKIPPED lines; neg/ 267 files; ~90 s run |
| 7 | scan_c6v.py (builder) | 19:07 | 0 | 45 files, banned 0, secret 0, mail 0 |
| 8 | myscan.py (mine: BANNED read at run time from tests/test_no_reference_material.py, 10 entries, case-insensitive; key shapes AWS, sk-, gh*_, xox*, Google, JWT, private key; mail shape) | 19:09 | 0 | scan-independent.txt: 109 files, banned 0, secret-shape 0, mail-shape 28 (all non-addresses: 13 "@pytest.mark.parametrize", 1 "@pytest.fixture", 1 version number, example.test/example.com/evil.test), 54 more on example domains excluded. Real addresses 0. |

## Fresh mutations (mut15.py, mutations-output.txt; copies in mut/; each run with verify-c6v.py <copy>; "new FAILs" = beyond the 1 baseline FAIL of run 2)
19 mutations written (15 asked, 4 extra). CAUGHT 12, MISSED 7.
| id | change | result |
|---|---|---|
| I01 | row count 104 to 103 in box | CAUGHT (3 new FAILs) |
| I02 | ready count 57 to 58 in section | CAUGHT |
| I03 | UTC/IST pair in the example ORDERS line (IST minus 30 min) | CAUGHT |
| I04 | check-time IST 00:34:44 to 00:44:44 (one place) | CAUGHT (pair arithmetic) |
| I05 | check time 19:04:44Z to 19:04:45Z in one of two places | MISSED |
| I06 | "G12 approval" to "approval" in L-LEASE row | CAUGHT but only by the box word count (the mutation changes the count); not by a G12 check |
| I19 | same as I06 with the same word count ("the OWN approval") | MISSED |
| I20 | "cannot be filmed" to "can be filmed" for G12 open gate | MISSED |
| I07 | card line 1 "(11 words)" to "(12 words)" | CAUGHT |
| I08 | wrong sheet version v34-A to v33-A in one sentence | MISSED |
| I09 | row 50 dropped | CAUGHT (13 new FAILs) |
| I10 | row 50 duplicated | CAUGHT (14) |
| I11 | box word count stated 2478 to 2476 | CAUGHT |
| I12 | "99 of 104" to "98 of 104" | CAUGHT |
| I13 | "Five items are OPEN" to "Four items are OPEN" | MISSED |
| I14 | "release note v14 line 33" to "line 34" | MISSED |
| I15 | newest release note name v18 to v17 in one sentence | MISSED |
| I16 | "3 rows that wait for a check" to 4 | CAUGHT |
| I21 | example answer line time +1 min on both UTC and IST | CAUGHT |
| I17, I18 | forged numbers in c6v-CHANGES.md (267 copies to 300; 6 runs to 3) | NOT CHECKABLE by any verifier: no verifier parses c6v-CHANGES.md numbers (verify_c6v_part2.py only excludes its name from a list); build_c6v.py mentions it |

## Builder claims vs what I saw
| Claim | Seen |
|---|---|
| static-checks exit 0 | yes, exit 0 (twice) |
| verify 238 checks, 0 FAILED | 238 checks; 0 FAILED on my 19:07Z snapshot; 4 FAILED on the live tree at 19:25Z (file times) |
| neg 267 copies, 0 wrong | 267 copies, 1 wrong, explained by my own deleted file (item 2) |
| scan 315 files banned 0, secret 0, mail 0 | builder's scan in my folder: 45 files at first run 0/0/0; my own scan 109 files 0/0/0 real hits |
| verify on REPORT-c6u.md exits 1 with 32 FAILs | exit 1, 32 FAILs at 19:07Z; 34 at 19:25Z |
Not checked by me: whether the row old texts match the REAL files outside the copied tree (the report says UNVERIFIED), EGM review, any n8n run, the 267 copies' individual correctness beyond the OK/WRONG column.
