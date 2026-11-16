# fix-findings-ledger21 (round 21)

## NOT done / uncertain (first)
- Nothing was run against n8n or Postgres; every check is static. The T20 before/after guards were tested only with a stub psql.
- F-031: the new run-sheet sentence is given as exact text and placement inside the F-031 row; no second patch file was written (patches are not mine). The F-031 and F-003 expected-text checks were done on a scratchpad copy of the patched run sheet, not on the real file.
- QUESTIONS.md is not mine: Q31 item 26 there still says "path:2" while F-008 now says "2 or more". F-041 and F-011 name the two new Q31 items as "number to be filled by the Q31 fixer".
- F-007 line "no Q31 item asks for it" left unchanged.
- The ACCEPTED: recovery flow wording is the script's own (not owned by the audit); the row says it is misleading and who may reword it.
- Syntax check (bash -n) covered the two T20 guard scripts; one-line grep commands in the rows were read, not run.

## Fixed by id
- F-041, F-011: question gap now "queued as NEW Q31 item", when cell shortened (old text kept in the evidence cell), sibling mentions fixed (inputs row 12, line 117, lines 46 and 66).
- F-031: full sentence, exact placement, two-line proof with heading-order check, DEFAULT and ALTERNATIVE as two plain lines, producer note change.
- F-041, F-008, F-029, F-037: variable-load line at the top of the PASS LINE; F-002: second line for pg-secrets.
- F-002: T20 before-count guard, after guard, three-part T19 summary, duplicate "Wed 18 Nov, 12:30 IST" removed.
- Wait value: one date (Tue 17 Nov 06:00Z (11:30 IST)) in READ-FIRST and both rows; F-018 contradiction written into the READ-FIRST table line.
- F-037, F-029, F-008: WHO NEXT opens "if nobody answers Q31 item 26 by Tue 17 Nov 07:00Z (12:30 IST), nobody runs the grep and Tuesday is NO-GO"; "TAG GO" explained.
- F-037 WORDS USED: filled/export/unfilled copy, $env, fill_flows, T-ENV, NOT COVERED 28c/28d, Reading A, ORDER 007 item 2.
- F-008: "at least 2" per file, recovery file stays :2 / :0, ACCEPTED wording stated plainly.
- F-003: expected text and greps for the three re-reads.
- READ-FIRST ALSO USED EARLY: Block R7, JUDGED, egm, Timing case 1 and 2, mf_leads, n8n-flows-real-v5.
- LEDGER-ROWS.md: fix cells of F-002, F-003, F-007, F-008, F-011, F-018, F-029, F-031, F-037, F-041 re-copied; header list updated (now includes F-029 and F-037); line 9 duplicate "= 19:30 IST" removed.

## QUESTIONS FOR Q31
1. (from F-011) 'F-011 FIX A, WHO RUNS IT: if the answer to item 10 (a) is fix A, who runs the three runs (T7b on Postgres, the import test of the 4 flows, one kill run), in which hours, and in which slot (inside RUNBOOK step 7 or a separate slot before Tue 17 Nov 14:00Z (19:30 IST))? Answer by Tue 17 Nov 03:00Z (08:30 IST), with item 10 (a). If unanswered: no runner is named, fix A does not run, and GO row 6 is the automatic NO-GO. Also needed from the studio lead: the exact import-test lines; who adapts T7b to Postgres; confirmation that the kill run is K1.'
2. (from F-041) 'ONE-DATABASE WORDING CHECK, TWO INPUTS: (a) the path of the owner sheet, and (b) the list of allowed places for the words one database and single database (each entry a file and the text that stays), written by the studio lead after running the grep of FIX-PLAN item 8b on the old text. Answer by Tue 17 Nov 07:00Z (12:30 IST). If unanswered: no list exists, so the wording route cannot pass and, with the default of item 10, the downgrade route is the only one left (see the decision table).'

## Outputs
- count_findings: rows 45 unique 45; Blocker 5 / Major 5 / Nit 35; BEFORE 11, AFTER 34.
- compare14: "45 45 differences: 0"
- check_refs PASS 5182 references; check_names PASS 655 rows; check_secrets PASS 0 hits in 2780 files; check_counts PASS 52 files / 655 nodes.
- ruff format --check: 906 files already formatted.
- bash -n on before.sh and after.sh: ok.
