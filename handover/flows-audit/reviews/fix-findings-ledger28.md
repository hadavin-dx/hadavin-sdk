# fix-findings-ledger28 (2026-11-16)

Fixer for reviews/findings-ledger-reader-r28.md (non-security path, round 28). Edited only FINDINGS.md, LEDGER-ROWS.md and ledger-history-cells.md. Severity, status and the counts (5 Blocker, 5 Major, 35 Nit) are unchanged. Nothing committed.

## What was NOT verified (first)

- No block was run against real n8n, Postgres or HubSpot (not allowed, not available). Every new shell block was run only against stand-in functions and made-up folders in my own scratch (good case and bad case each), which proves the block logic and nothing else.
- Every block still prints FAIL today in the real tree, which is the right answer for an unfixed row; none was run on the real take folders (they do not exist yet).
- The 35 Nit rows were not reviewed in this round. Only the cross-row note was applied (F-042, F-043 are the only other rows that start with `export TAKE_FOLDER=`).

## Reviewer items: all ten checked against the text, all real

Blockers: F-002 (T19/T20/T21 steps judged by eye, unguarded; fixed with one block each ending PASS/FAIL), F-003 (two rating bases, unguarded `cd`; one basis, three guarded blocks, re-read items worded as must NOT APPEAR), F-007 (guard echo separate from the grep; two blocks F007-1 and F007-2, table writer not named), F-031 (psql exit not printed, no control; blocks F031-1 and F031-2 print `psql exit N`, status move labelled CLOSED AS DISCLOSED, FLAW REMAINS), F-037 (no printed grep exit; block prints `grep exit N` with the needed value, CONTROL-NAMES added).
Majors: F-008 (single block F008, $LOG source stated), F-011 (decision list and BLOCKED list on top, evidence (a) in the `{ ...; } || echo "NOT A PASS"` form with wrapped controls, "BEFORE 8" defined in cell 6), F-018 (decision first, one LEAD FILLS list with times, block F018-7), F-029 (block chk29, export half blocked stated first, four search words separated from the four placeholder values), F-041 (the two forms removed, Block R7 is the one decider; downgrade (a) in the `||` form; list named THE WORDING-ROUTE STEPS and cited in STATUS MOVE).
Where the reviewer was partly wrong: for F-041 the list "To make the wording route count" already existed before STATUS MOVE; the real defect was that it had no name and STATUS MOVE cited bare step numbers, so I named it rather than writing a new list.

All ten fix cells now start with the SUMMARY, then a BLOCKED UNTIL part stated once. Old wording that was replaced is in ledger-history-cells.md, section fix-findings-ledger28.

## Left open (needs the lead; exact missing input; nothing invented)

- Take folder path: Q31 item 59, due Tue 17 Nov 03:30Z (09:00 IST). Blocks every row.
- WAIT_S value: Q31 item 25, 06:00Z (11:30 IST).
- Mail count command and test-log path: Q31 item 50, Wed 18 Nov 05:45Z (11:15 IST). SECOND_ADMIN: item 82.
- HubSpot menu path, who reads the count, probe slot: item 54 (F-018). Counts-or-out: item 31, 06:45Z (12:15 IST); audit recommends out.
- Allowed-places list and owner-sheet path: item 137, 07:00Z (12:30 IST) (F-041). Route and runner for F-011: items 10, 136, 112, 03:00Z (08:30 IST); downgrade items 10 (b), (c) 06:15Z, item 18 07:00Z.
- Export command (FIX-PLAN item 3 step 9; scripts\n8n_api.py is not in the tree): blocks the $EXPORT half of F-029 and F-037.
- F-031: PGSELECT_PW and KEYS31 are the audit's proposed names, closer and runner (items 11 and 26) not named; default stated as studio lead, a lead decision.
- F-007: who WRITES the naming table is not named (default studio lead, lead decision). F-008, F-029, F-037 runners: item 26, default nobody.
- Studio lead re-reads (F-003 item 89, F-007, F-031) are lead steps, no command can do them.
- N8N_ROLE, N8N_DB, N8N_PW (F-011 fix A) are defined nowhere.

## Raw verification output (run 2026-11-16 in handover/flows-audit)

```
$ python3 compare14.py FINDINGS.md LEDGER-ROWS.md
45 45 differences: 0
$ python3 -I tools/count_findings.py
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
$ python3 -I tools/check_refs.py
PASS 5193 references
$ python3 -I tools/check_names.py
PASS 655 rows
$ python3 -I tools/check_secrets.py
PASS 0 hits in 2861 files
$ python3 -I tools/check_counts.py
PASS 52 files / 655 nodes
$ ruff format --check .
986 files already formatted
$ bash -n on the 18 blocks (f003_1..3, f007_1..2, f008, f011a, f011ctl, f018, f029, f031_1..2, f037, t19, t20, t21_3, t21_4, t21_6)
all 18: syntax ok, and each block appears verbatim in FINDINGS.md
```
