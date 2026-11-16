# Fix report, findings ledger, round 30 (non-security, one batch)

## Gaps first (read these before the table)
1. Nothing was run against real n8n, Postgres, HubSpot or a mailbox. Only `bash -n` and stub runs (fake need_set, mailbox_count, psql, openssl, fake folder tree) of five blocks: the VARIABLES FIRST guard (F-002), T21 step 0, T21 step 2 (syntax only, `bash -n`; the stub run of step 2 was NOT done), F007-1, F018-10B. Stub results: guard prints VARS-OK only when all names are set, WAIT_S is digits and mailbox_count exists (empty FLOWS_PW prints REFUSED; WAIT_S=abc and missing mailbox_count print nothing, so no VARS-OK); step 0 PASS only with a passing SECOND_ADMIN dry run, FAIL when the dry run says FAILED; F007-1 PASS with both K3B control files, FAIL with one; F018-10B PASS, FAIL on HS18=2, FAIL on empty KEY18 and on missing mailbox_count. These prove the shell logic only, not the real services.
2. Brief mismatch: the brief says 8 Blocker / 8 Major / 29 Nit. `python3 -I tools/count_findings.py` printed 45 rows, Blocker 5, Major 5, Nit 35 (before and after my edits). I did not change any severity or status cell. Please correct the brief or tell me which count is right.
3. Other files still say "three new tests": QUESTIONS.md, RUNBOOK, TAKE-CHECKLIST, FIX-PLAN (I was told to edit only FINDINGS.md and LEDGER-ROWS.md). The rows now say four tests (T19, T19H, T20, T21). The lead must align those files.
4. Reader claims were checked against the rows, not trusted. Contested: (a) F-018 "split the row" would change the 45 rows and the counts, so I split the pass line into PART A (F018-7, Tuesday) and PART B (F018-10B, Wednesday) inside the one row. (b) "Three Blockers vs five": the sentence meant the three Blockers by lead order; it now says so.
5. The guard line prints nothing on refusal beyond the REFUSED name (or nothing for WAIT_S/mailbox_count); the signal is the absence of VARS-OK. It is not a pass line, so I left it.
6. Not verified: that the F-018/F-041 wording matches the real checker output on a real take; F-041 Part B says today R2-tables.md is listed (read from the row, not re-run).

## Proposed new Q31 items (QUESTIONS.md not edited; lead to add)
- N1: supplier of PGSELECT_PW (F-031).
- N2: supplier of KEYS31 (F-031).
- N3: supplier of the export command (F-037, F-029).
- N4: runner and supplier named in F-008 (the row cites Q31 item 26 for the runner; N4 covers the remaining unsupplied input).
- Extensions of existing items 25 (WAIT_S, F-002), 50 and 82, and 137 (OWNER_SHEET, F-041). Due times: set by the lead in UTC and IST (IST = UTC+5:30); I did not invent dates.

## Finding to change table
| Finding | Change in FINDINGS.md (mirrored in LEDGER-ROWS.md) |
|---|---|
| F-002 | One RATING BASIS; one THE CLOSING TEST LIST (T19, T19H, T20, T21); "four tests" everywhere; VARIABLES FIRST adds WAIT_S (Q31 item 25) and sources mailbox_count; guard checks WAIT_S digits and mailbox_count; T21 step 0 runs SECOND_ADMIN dry run; step 2 guarded and uses psql -w; STATUS MOVE and WHAT IT PROVES mention T19H |
| F-003 | Evidence sentence reworded; single RATING BASIS (rubric, narrow-route clause); "(1) to (4)"; four outputs; closing test list added |
| F-007 | TAKE RISK, RATING BASIS, BLOCKED UNTIL (1), WHO APPLIES made consistent; lane3 mapping optional; cd fixed; positive control changed to a K3B check on two files; explicit PASS/FAIL |
| F-031 | Named suppliers for PGSELECT_PW and KEYS31 (N1, N2) |
| F-037 | Single RATING BASIS; rating source and note point to it; stale F-029 quote replaced; export command supplier (N3) |
| F-029 | Export command supplier (N3) in two places |
| F-008 | `ls` prose fixed; suppliers and runner (Q31 item 26) named |
| F-011 | "four database roles" wording; BLOCKED UNTIL (2) rewritten; VARIABLES FIRST line and guard in PASS LINE; item (a) cites F041-R7, F041-CTRL, F041-OWNER |
| F-018 | PASS LINE split into PART A and PART B with closing list and commands; STATUS MOVE cites the list |
| F-041 | VARIABLES FIRST adds R7OUT and OWNER_SHEET (Q31 item 137); Part B wording matches checker; "four database roles" wording |

New text contains no " | " (it would break the cell split). Earlier open items from r28 and fix-findings-ledger29 were not re-audited beyond the rows above.

## Raw last lines
- compare14: `45 45 differences: 0`
- count_findings: `sev {'Blocker': 5, 'Major': 5, 'Nit': 35}` (45 rows)
- ruff format --check .: `1030 files already formatted`
- check_refs: `PASS 5193 references`; check_names: `PASS 655 rows`; check_secrets: `PASS 0 hits in 2905 files`; check_counts: `PASS 52 files / 655 nodes`
