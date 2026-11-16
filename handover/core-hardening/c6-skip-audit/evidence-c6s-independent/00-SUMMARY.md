# 00-SUMMARY: independent evidence for c6s (EVIDENCE RUNNER, raw results only, no judgement)
Run 2026-11-16 about 17:14 to 17:30 UTC (22:44 to 23:00 IST). No commit, no push, no edits to any existing file; all runs on copies in the scratchpad.

## Failures and deviations first
1. STALE TIME IN THE REPORT (real, found by me): OWNER-SHEET-v30-A.md and v30-B.md were rewritten at 17:13:55 UTC (23:43:55 IST), after the report's check time 17:13:05 UTC. REPORT-c6s.md (L-SHEET row, section 0 bullet, OS28 row) states both were written 17:12:09 UTC. Run on the live files, the builder's verifier fails 3 checks (03-builder-verify-on-ORIGINAL-live-steps.txt: check-time/newest-version, L-SHEET real written times, F4). Newest sheet name and time now: OWNER-SHEET-v30-A.md and OWNER-SHEET-v30-B.md, 17:13:55Z; v30-SOURCE.md 17:12:09Z (01-newest-sheets.txt). The count lines of the sheet check (C-10c) are unchanged (04-static-checks-diff-builder-vs-mine.txt: only the times differ).
2. The builder's run_all.sh cannot run on a copy as written: paths are absolute. I rewrote the paths with sed in the COPY only (and removed one line of static-checks.sh that reset S). On the copy it rebuilds REPORT-c6s.md; the rebuilt file differs from the original in 7 lines, all of them the check time (17:14:54 vs 17:13:05) and the v30 file times in the same lines. Baseline for the mutations used the original report, the original static-checks-output.txt and v30-A/B mtimes set back to 17:12:09 on the copy: 165 checks, 0 FAILED (03b).
3. Gaps of the builder's verifier shown by mutations (section below): box word count stated in the report is not compared with the real count (mutations 16, 17 missed); card line word count 11 to 12 missed (23); key-cancel time tied to the money stop 18:29 missed (22); L-CARD default Yes to No missed (20); R447 added to the box missed (31); a key-shaped string 'sk-ant-api03-...' missed because its pattern sk-[A-Za-z0-9]{10,} stops at the hyphen (32); '3 check rows' to 4 missed (34); title 'UTC + 5:00' missed (35); release note v14 to v15 missed (37); '18 kept runs' to 17 (first) missed (39); OWNER ONLY removed (42); wrong file name in box (43).
4. Gaps of MY checker (it does not read old/new text against the source files, nor sheet/version claims, so it missed:): 02, 03, 11, 12, 16, 19, 20, 22, 28, 29, 32, 33, 34, 35, 36, 37, 38, 39, 41, 42, 43, 45.
5. Mutations 19 and 45 were caught by the builder's verifier only through the 'box under 3,490 words' check (the inserted text made the box longer), not through the planted fact. Mutation 18 and 11 are caught for the right reason.
6. I deleted three copies of the copy-run outputs (neg-output, static-checks-output, verify-c6s-output) from this folder before finishing; the run_all stdout (02) and the baseline outputs (03b) remain. Nothing in the original folder was touched.

## Results
| Item | Result |
|---|---|
| (1) sha256 before and after (REPORT-c6s.md, c6s-CHANGES.md, REPORT-c6r/q/p.md, every OWNER-SHEET and LEAD-RELEASE-NOTE file, every file of evidence-c6s/) | identical before and after (01-, 08-). There is no inputs/ folder in c6-skip-audit; the sheets and release notes of steps-edits were hashed instead. |
| (2) run_all.sh on a copy | exit lines: verify exit 0 (165 checks, 0 FAILED); neg exit 0 (137 copies, 0 wrong) (02). 24 s. Original untouched. |
| (3) my own checker (my_check.py, 20 checks) on REPORT-c6s.md | 20 PASS, 0 FAIL (05). Row count 94 (ids exactly 1..94, table is in apply order, not numeric order), status split 49 + 36 + 3 + 6; 61 UTC/IST pairs all +5:30; 19 weekday/date pairs right (23 Nov 2026 is a Monday, 18 and 25 Nov Wednesdays); closing card lines 11+35+22+22 = 90 words; 6 length-table rows right (words/150*60, rounded up to 5, plus 150); box 3,488 words by my count (report says 3,490 in two places, 3,488 elsewhere in c6s-CHANGES.md); no internal-code pattern in the box; 0 banned strings of 10. Same checker on REPORT-c6r.md: 2 FAIL (05b). |
| (4) mutations | 45 planted plus 1 no-change control (06). My checker caught 23 of 45; builder verifier caught 32 of 45; the control passed both. Missed by BOTH: 16, 20, 22, 32, 34, 35, 37, 39, 42, 43. Table below. |
| (5) builder verifier on REPORT-c6r.md | 56 FAIL lines, exit 1 (07); builder's claim of 56 confirmed. It reports '170 checks' on c6r vs 165 on c6s. |

## Mutation table (CAUGHT n = number of FAIL lines; control row: MISSED means passed cleanly)
| Mutation | My checker | Builder verifier |
|---|---|---|
| 01 wrong count: 'Of the 94 rows' -> 93 (line 24 or 71, first) | CAUGHT 1 | CAUGHT 1 |
| 02 wrong count: TOTAL row 94 -> 95 | MISSED | CAUGHT 1 |
| 03 ready 49 -> 48 in box | MISSED | CAUGHT 1 |
| 04 dropped IST (first pair) | CAUGHT 1 | CAUGHT 1 |
| 05 wrong IST (30 min short) | CAUGHT 1 | CAUGHT 1 |
| 06 wrong IST on money stop (first) | CAUGHT 1 | CAUGHT 1 |
| 07 wrong weekday Mon 23 Nov -> Tue (first) | CAUGHT 1 | CAUGHT 2 |
| 08 wrong weekday Wed 18 Nov -> Thu (first) | CAUGHT 1 | CAUGHT 2 |
| 09 wrong weekday Wed 25 Nov -> Fri (first) | CAUGHT 1 | CAUGHT 1 |
| 10 wrong weekday Mon 23 Nov -> Tue (ALL) | CAUGHT 1 | CAUGHT 2 |
| 11 stale v26 'newest' (section 0) | MISSED | CAUGHT 2 |
| 12 stale v26 in L-SHEET | MISSED | CAUGHT 1 |
| 13 row 50 deleted | CAUGHT 3 | CAUGHT 10 |
| 14 duplicate id (row 51 renumbered 50) | CAUGHT 1 | CAUGHT 3 |
| 15 row 94 deleted | CAUGHT 4 | CAUGHT 8 |
| 16 box number changed, first '3,490' -> 3,190 | MISSED | MISSED |
| 17 box number changed, ALL '3,490' -> 3,190 | CAUGHT 1 | MISSED |
| 18 box paragraph removed (WORDS YOU NEED block of 3 lines) | CAUGHT 1 | CAUGHT 19 |
| 19 defaults flipped: L-POST Yes -> No (box table) | MISSED | CAUGHT 1 |
| 20 defaults flipped: L-CARD Yes -> No | MISSED | MISSED |
| 21 lease sentence on card line 1 (first quote) | CAUGHT 1 | CAUGHT 2 |
| 22 key end tied to 18:29 (money stop) | MISSED | MISSED |
| 23 card word count 11 -> 12 | CAUGHT 2 | MISSED |
| 24 card seconds 36.0 -> 30.0 | CAUGHT 1 | CAUGHT 1 |
| 25 card budget 50 s -> 45 s | CAUGHT 1 | CAUGHT 1 |
| 26 video total 180 -> 185 | CAUGHT 1 | CAUGHT 1 |
| 27 row 20 status says APPLIED | CAUGHT 3 | CAUGHT 10 |
| 28 row 1 stated line 90 -> 91 | MISSED | CAUGHT 2 |
| 29 row 5 old text altered by one letter | MISSED | CAUGHT 2 |
| 30 banned string inserted (counts only; value never printed) | CAUGHT 1 | CAUGHT 1 |
| 31 internal code R447 added to box | CAUGHT 1 | MISSED |
| 32 key-shaped string added (built from parts) | MISSED | MISSED |
| 33 36 -> 37 defaults in box | MISSED | CAUGHT 1 |
| 34 3 -> 4 check rows in box | MISSED | MISSED |
| 35 title says UTC + 5:00 | MISSED | MISSED |
| 36 newest sheet claimed v31 | MISSED | CAUGHT 1 |
| 37 release note v14 -> v15 (first) | MISSED | MISSED |
| 38 range 60.1 to 61.9 -> 69.1 (first) | MISSED | CAUGHT 2 |
| 39 18 kept runs -> 17 (first) | MISSED | MISSED |
| 40 answer-line example IST wrong | CAUGHT 1 | CAUGHT 3 |
| 41 report truncated (last 20 lines cut) | MISSED | CAUGHT 5 |
| 42 OWNER ONLY removed from L-SHEET | MISSED | MISSED |
| 43 box names wrong file ORDER.md | MISSED | MISSED |
| 44 pipe removed from row 30 (cell merge) | CAUGHT 4 | CAUGHT 9 |
| 45 v31 sheet named as existing | MISSED | CAUGHT 1 |
| 47 no-change control (must PASS both) | MISSED | MISSED |

## What I did not run
- No n8n, flows or harness; no live call; no spend. No check that the 94 edit rows' old text matches the real files (the verifier reads the scratchpad tree copy for 89 rows; I did not compare that copy with the repository).
- My checker does not recompute the per-question counts, the cites, or the 18-run split; I did not read the box for plain wording.
- Mutations were single edits; no combined mutations. Mutation counts of 'CAUGHT n' are FAIL lines, not distinct causes.
- No timing/load tests; one heavy job at most (the run took 24 s).
- Processes: none left running; no __pycache__ created in the repository (python -B -I).
Files: my_check.py, mutate.py (the banned strings are read from tests/test_no_reference_material.py at run time and only written into scratch copies, deleted after each run; counts only), checkpoint.md.
