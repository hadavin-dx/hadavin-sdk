# c6t-CHANGES: what changed from REPORT-c6s.md to REPORT-c6t.md (one batched fix)

Times are UTC with IST (IST = UTC + 5:30). REPORT-c6s.md, c6s-CHANGES.md, the three c6s reviews and evidence-c6s-independent/ are unchanged.

## 1. What failed, what is uncertain, what was not checked (first)
- NOT FIXED: design minor m1 (needs a new edit row 95; it would change the row count in about 30 places). It is stated plainly in REPORT-c6t.md sections 0, 8 and 9 with the proposed row text. Next step: the studio lead says yes or no to row 95.
- NOT RUN: the studio lead's EGM steps (independent evidence runner, egm:* result reviewers, resolve, drift report). The checks below prove TEXT (words, numbers, times, file names), not that the report is true or that the video will work.
- NOT RUN: n8n, the loopback re-smoke, the key scan, the stopwatch run. The command to provoke the alert mail (test K3) is UNVERIFIED.
- UNCERTAIN: another session keeps rewriting the owner sheets and release notes (v31 sheets were rewritten at 17:46:03 UTC = 23:16:03 IST, after my first check). The report names the check time and the written times it saw; the verifier now fails on any sheet or note newer than the check time, so a new rewrite means run_all.sh must be run again.
- NOT PORTED: 8 older negative controls of c6r/c6s name text that no longer exists in c6t (listed as PORT-SKIPPED in evidence-c6t/neg-output.txt); each rule behind them has a c6t control or check.
- run_all.sh needs the environment variable C6T_TREE (folder of the copied demo tree, an input of the audit); it is the only machine-specific path and is not written in any file.

## 2. Finding -> fix -> where -> check
| Finding | Fix | Where | New check (each shown to fail on a changed copy) |
|---|---|---|---|
| Design M1 (45-second sentence) | No text says the sheets carry it; L-POST cites LRN14:149 item 11 and LRN14:150; TASK (9) is a question | box, 1c-F, section 3, section 9 | M1 (2 checks), E-lrn, T-M1, T-M1b |
| Design M2 (lease words on the video) | HELD under gate G12 in box and L-POST | box, section 3 | M2, T-M2 |
| Design M3 (alert-mail gate) | check row C-12; TASK (5) provokes the alert (test K3); Table B has line 2 cut and lines 1+2 cut with Time cells | section 7, 1c-C, 1c-F | M3 (3 checks), T-M3a-d |
| Design M4 (box length honesty) | the box states its real count (2,495) and the verifier recounts | box, section 9 | E-count, N5, M4, T-E15, T-E16, T-M4 |
| Design m2-m6 | wording and labels fixed as listed in REPORT-c6t.md section 8 | see section 8 | E-defs, E-defs2, E-scan, m6 |
| Reader M1 (two step lists) | STEPS (WHAT TO TYPE 1-5) and TASKS (1)-(12) | box, 1c-F | N1, T-N1 |
| Reader M2 (claim) | CLAIM = reserve; a video sentence is a STATEMENT | box, 1c-A | N2, T-N2 |
| Reader M3 (row) | ROW / LINE / RECORD defined | 1c-A | N3, T-N3 |
| Reader M4 (scenes 5-11) | box says scenes 1-4 and a closing card; 5-11 listed, not filmed | box | N4, T-N4 |
| Reader M5 (under 2,500 words) | box 2,495 words; detail moved to section 1c, nothing deleted | box, 1c | E-count, N5 |
| Reader M6 (option b) | option (b) printed in the box with the five dropped items | box | N6, T-N6 |
| Evidence: stale check time | all times read from the files at run time; check time 17:50:39 UTC | static-checks.sh, builder | E-mtime (3 checks), T-E19..E23 |
| Evidence: absolute paths | run_all.sh and the scripts use paths relative to their own folder | evidence-c6t | E-paths |
| Evidence: 13 missed mutations | first box number, L-CARD default, key end tied to 18:29, key-shaped string with hyphens (regex widened), release note v14 to v15, 18 kept runs to 17, OWNER ONLY removed, wrong file name, 3 to 4 check rows, title UTC + 5:00, card word count, R-number in box, all box numbers changed | verifier | E-numbers, E-defaults, E-keyend, E-secret, E-rn, E-kept, E-owneronly, E-files, E-title, E-cardwords, E-rnum; controls T-E1..T-E14 |
| Evidence: stated count never compared | recount in the verifier | verifier | E-count |

## 3. Evidence (files in evidence-c6t/)
- verify-c6t-output.txt: 199 checks, 0 failed (all old checks kept, 34 new).
- neg-output.txt: 170 changed copies, 0 wrong (45 new T- controls; the unchanged copy exits 0, every changed copy exits non-zero).
- c6s-through-c6t-verifier.txt: the same verifier run on REPORT-c6s.md: 13 of the new checks fail on it (E-count, N5, E-files, two E-mtime, M1, M2, M3, M4, N2, N3, N6, m6). The others pass on c6s because c6s had no defect there; they are proved by the T- changed copies instead.
- static-checks-output.txt, steps-snapshot/ (copy of the sheets and notes at check time).
- Re-run: C6T_TREE=<copied demo tree> bash evidence-c6t/run_all.sh
