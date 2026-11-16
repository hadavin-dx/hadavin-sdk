# 00-TABLE: independent evidence for c6t (EVIDENCE RUNNER: raw results, no judgement)
Run 2026-11-16 about 17:52 to 18:00 UTC (23:22 to 23:30 IST). No commit, no push, no spend. All runs on a COPY in the scratchpad (.../scratchpad/ind-c6t); the original folder was not edited (05: only difference after the run is a new file review-c6t-naive.md written by another agent, not me).

## Failures, deviations and misses first
1. C6T_TREE was NOT supplied to me (env var empty). I used the builder's own copied demo tree found in the shared scratchpad (scratchpad/c6/tree, 3,355 files); its provenance and equality with the tree the builder used are UNVERIFIED by me. The verifier wants C6T_TREE = that tree's handover/ folder (first try with the tree root failed: FileNotFoundError on demo/VIDEO-RUNSHEET.md; run_all1-3 show this).
2. run_all.sh cannot run from a bare copy of c6-skip-audit alone. It also needs, one level up: steps-edits/, inputs/, REPORT.md and the other core-hardening files, plus tests/test_no_reference_material.py at the repository root of the copy (runs 1 to 5 each stopped on one missing file; stdout files run_all-stdout.txt to run_all-stdout6.txt).
3. THE LIVE steps-edits FOLDER CHANGED UNDER THE REPORT: another session wrote OWNER-SHEET-v32-SOURCE.md and LEAD-RELEASE-NOTE-v16-SOURCE.md (both 17:52:33 UTC = 23:22:33 IST), after the report's check time 17:50:39 UTC. On the live files, run_all.sh fails in build_c6t.py (AssertionError, newest sheet version is v32: run_all-stdout.txt) and, once past that, verify fails F4 "no owner sheet or release note has a version higher than the one named" (v16 note). Only after I deleted the v32 and v16-SOURCE files in my COPY did it run clean. So c6t's text "newest sheet v31, newest note v15" is no longer true on disk. The builder predicted this (c6t-CHANGES, section 1).
4. Rebuilding changes REPORT-c6t.md only in the check time (17:54 instead of 17:50:39) and the times derived from it: 34 diff lines, all time lines (run_all-stdout2 diff in my notes; same cause as in c6s).
5. 14 of 40 mutations that I invented were MISSED by verify-c6t.py (table below). One more attempt (no 40 "94 -> 95 last occurrence") was invalid: it hit "HB1894", so no result; the re-done version 40 (all "Of the 94 rows") was CAUGHT.
6. Verifier on the ORIGINAL REPORT-c6t.md with the checks run against my fresh static-checks-output (check time 17:54:26) gives 2 FAIL (v-orig.txt: check-time line and F4); with the builder's original static-checks-output.txt it gives 199 checks, 0 FAILED (v-orig2.txt).

## Results
| Item | Result | File |
|---|---|---|
| verify exit and SUMMARY (copy, v32 and v16-SOURCE removed, full rebuild) | verify exit 0; SUMMARY: 199 checks, 0 FAILED | run_all-stdout6.txt, run-copy-verify-c6t-output.txt |
| negative controls (same run) | neg exit 0; SUMMARY: 170 copies, 0 wrong; PORT-SKIPPED lines present (older controls whose text is gone, as the builder said) | run_all-stdout6.txt, run-copy-neg-output.txt |
| same run on live steps-edits (v32 present) | build_c6t.py AssertionError, no verify run | run_all-stdout.txt |
| verifier on original REPORT-c6t.md + builder's original static-checks-output.txt | exit 0; 199 checks, 0 FAILED | v-orig2.txt |
| verifier on original REPORT-c6t.md + my fresh static-checks-output | exit 1; 199 checks, 2 FAILED (check time, F4) | v-orig.txt |
| verifier on REPORT-c6s.md | exit 1; 223 checks, 92 FAILED (many "part 2 statement could not run") | v-c6s.txt |
| verifier on REPORT-c6r.md | exit 1; 224 checks, 117 FAILED | v-c6r.txt |
| hashes | sha256 of REPORT-c6t.md, c6t-CHANGES.md, checkpoint, REPORT-c6s.md and all 248 files of evidence-c6t; sha256 of every owner sheet and release note at the end of my run | 01-, 02- |
| banned-string scan of whole c6-skip-audit folder (list read at run time from tests/test_no_reference_material.py, 10 entries) | 1,107 files, 0 hits | 04- |
| secret-like scan (counts) | key-shaped sk-/ghp/xox/hubspot-pat/private key/Bearer: 0. AKIA: 9 matches in 8 files, all the literal AKIAIOSFODNN7EXAMPLE (allowed). 40+ hex strings: 311 matches in 17 files, from sha256 lists and similar (not examined one by one). E-mail-shaped: 104 matches in 49 files; domains example.com, example.net, gmail.com; the gmail.com ones (31 matches) have 1-character local parts in my count (not checked further whether any is a real address) | 04- |
| leftover processes | none started by me are running. Other agents' python/bash jobs are running (mutation-lane, repin8, audit-r460, r12/r18 scratch); I did not touch them | |
| __pycache__ | I ran everything with python3 -B -I; 0 __pycache__ folders in c6-skip-audit and in this folder | |
| original folder untouched | diff of sha256 list before/after: only the new file review-c6t-naive.md (not mine); steps-edits v32-SOURCE hash changed (another session, 02- vs before) | 05- |

## 40 invented mutations of REPORT-c6t.md (mut.py, mut2.py; each run with verify-c6t.py on the original report + builder's original static-checks-output; raw: mut-out.txt)
CAUGHT 25 (+3 re-done in mut2), MISSED 14, no result 1 (invalid no 29, redone as 29/29b: CAUGHT).
MISSED (verifier exits 0):
| No | Mutation |
|---|---|
| 04 | rows 23, 58, 59 -> 23, 58, 60 (rows waiting for n8n) |
| 12 | card words "90 words, about 36 s" -> 91 words (first) |
| 13 | card seconds 36 -> 38 |
| 14 | "74-word text" -> "144-word text" |
| 15 | card budget 40 s -> 45 s (first) |
| 16 | "a 45-second setting" -> 55-second (first) |
| 17 | recovery flow "wakes every 30 seconds" -> 20 |
| 24 | cite LRN14:149 -> LRN14:148 (first) |
| 25 | cite ORD:150 -> ORD:151 (all) |
| 27 | "18 stand-in crash runs" -> 17 (first) |
| 30 | "13-minute alert delay" -> 12-minute (first) |
| 31 | "(2 relayed runs)" -> 3 |
| 32 | "(rows 90, 91 edit only" -> 90, 92 |
| 40 first try | invalid (hit an unrelated number) |
CAUGHT (25): 01-03, 05-11, 18-23, 26, 28, 33-39 (details in mut-out.txt); also 29, 29b, 40 redone, 41 (R447 added to box) in mut2. Note: for "first occurrence" mutations (12, 13, 15, 16, 24, 27, 30) other copies of the same fact stay unchanged in the report, so a miss there means the verifier does not compare the copies with each other; I did not test the all-occurrence variants for those.
No-change control: original report + builder's original static-checks: exit 0 (v-orig2.txt).
