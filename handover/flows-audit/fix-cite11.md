# fix-cite11 (fixer of citations, static; input reviews/citation-r9.md)

Backups of the 8 editable files: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-cite11/. Nothing was run in n8n; no commit.

| citing row | old cite | new cite | how re-read |
|---|---|---|---|
| FINDINGS F-002, LEDGER-ROWS F-002 | dn1_common.py:124-132 | sentence changed: no line shows 422 handling; take() resends when the reply has no 'verdict' | opened demo/n8n-tests/dn1_common.py lines 118-134; no '422' in file |
| FINDINGS F-008 (row 114), LEDGER-ROWS F-008 | take_check.sh lines 171-184 | stable text 'saveManualExecutions' / 'run saving not all/all/True' | read take_check.sh 445-460 (check at about 449-458 now) |
| FINDINGS F-010, LEDGER-ROWS F-010 | FIX-PLAN.md line 30; ROLES-PROPOSAL.md line 63 | FIX-PLAN [config] entry 'F-010 three database roles (plus n8n's own: four)'; ROLES-PROPOSAL section 3 'Proposed logins' | grep of both files |
| FINDINGS F-0xx (row 63) | handover/demo3/kill/RESULTS.md:40-48 | marked '(file not in this checkout)' | CANNOT-CHECK |
| QUESTIONS x2 (L29 row, item 12) | inputs/plan-wp6-resmoke-v5.md line 193 | 'the python block that starts import collections, re, sys' | read lines 190-194 (193 blank). Also: `ruff format --check .` says 589/590 files formatted, so the premise 'ruff format fails' is still UNVERIFIED (already flagged in item 12) |
| QUESTIONS (K1..K3B, SQLite, P checks, CrmIdOk, Parts of the system, 2x desk, Q148 line 45) | CLAIMS-TABLE.md:112, :73, :45 (x2), :117, :114 (x3 forms) | glossary entry / section names | grep of CLAIMS-TABLE.md; line 73 was also stale |
| QUESTIONS Q300 | CLAIMS-TABLE.md:199 ... :234, RUNSHEET-WORDING.md:217 ... :190 | row numbers 6,16,24,27,30,62,71,78 and claim ids A-007, A-053, A-057, N-3, 'rule 7' | row ids exist in Table 1 / 2 |
| QUESTIONS items 1, 2, 3 | OWNER-STEPS-q16-rows.md lines 20/227, 277-278, 28 | 'A retake' entry in Words for you, row 7 Retake decision, rows V17 and V18 in the lead-values table | grep of OWNER-STEPS-q16-rows.md |
| QUESTIONS item 29 | take_check.sh (lines 11, 184, 185) | header comment and recovery-flow check, found by text 'recovery flow not part of the take' | grep: lines 11, 461, 462 |
| QUESTIONS item 8 | run_real_check.py:993 etc., crm_hubspot.py:492-499 | '(file not in this checkout)' | CANNOT-CHECK |
| REPORT:15 | take_check.sh:60 and fill_flows README:240 | line numbers dropped; the text 'deleted at clean-up' is no longer found in either file (probably fixed; only a text search) | grep |
| REPORT:45 | harness.py:26 | '(file not in this checkout)' | CANNOT-CHECK |
| REPORT:151 | RUNBOOK.md 50/204/298, TAKE-CHECKLIST.md 67/86, fill_flows README 126 | stable phrases, no numbers | grep; recheck after edits stop |
| ID-VID-CHECK 50-57, 61, 62 | CLAIMS-TABLE.md:19,163,270,309-313,325,372,526-534,370,359,595; RUNSHEET-WORDING.md:16/25/27, :88 | claim ids / row numbers / section names | grep; cite 'P3' in row 50 names a check that does not exist in CLAIMS-TABLE.md, now pointed at check P4a |

Checks: check_refs PASS 5167 references; ruff check passed; ruff format --check 590 files formatted; count_findings FINDINGS.md: 45 rows, Blocker 5, Major 5, Nit 35. check_secrets: FAIL 3 hits, none in my files: reviews/citation-r9.md:413, flow-check/evidence-f8-r8.md:55, flow-check/raw/test-take-check.txt:177 (the first is the reviewer's file, not edited here).
