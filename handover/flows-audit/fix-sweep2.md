# fix-sweep2 log (flows-audit fixer, 2026-11-16, after the 11:25Z lead answer to Q21)
Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-sweep2/ (7 files). Files edited: FINDINGS, FIX-PLAN, CUT-LIST, EXCEPTIONS, QUESTIONS, REPORT, LEDGER-ROWS (plus this log). Nothing ran in n8n.

## Failures and unfixed items first
Unfixed, and why:
1. Sweep nits 13 and 14 (decision-9 sentence 7 times, "film-v5 not in this video" about 25 times): NOT done. The real counts in FINDINGS are 2 to 16 occurrences, and each sits in a cite the row needs; removing them would take cites away. Cheap fix would be a find-and-replace; I judged it not worth the risk. Lead may say "do it".
2. Sweep nit 12 (T19-T21 pass lines twice): fixed in FIX-PLAN item 2 (now points at the F-002 row); the line-21 definition in FINDINGS "Words used" stays (it names the tests, it is not the pass line).
3. Needs the lead (files I may not edit): QUEUE.md:8 and the F1-F8 tags ("journal-only exception, delete at clean-up", answered-but-written-open tags); patches/F-008 comment (already reads "never deletes", checked: no edit needed); flow-check/README:17 and its parked-roles wording; fill_flows/README:240 (reads like a delete step); CLAIMS-TABLE:9, :183, :216 (one database / run list empty / about 61 s), RUNSHEET-WORDING:57-58, :63, :70, :77, :143-144, :201-211 (K1 captions A-017b/A-019b, held A-057, rows with 60.8/61.9/61.2 s), OWNER-STEPS:5-7 vs :20 and :29 (US$0; use the Q21 cost line), OWNER-STEPS-realrun-v3 references in CLAIMS-TABLE (:181-182,:201,:212-213,:222), the two READMEs (Python 3.10+ vs 3.11+). Also decision 10 "fix DECISION-one-store line 14" is not visible in my inputs.
4. Q20 item 4 (DESK_ALERT_TO value and who sets it) stays open. Exact missing input: the value source in the lead's take start script.
5. Not checked: I did not re-read FLOWS-AUDIT.md or any lane file; line numbers inside FINDINGS shifted by +5 after the new NOT COVERED items, so any other file citing FINDINGS line numbers (the checker table above all) needs a re-run.

No failures in the edit scripts: every replacement found exactly the text it expected (one script run each; one follow-up fix for an unclosed bracket in F-003).

## Citation checker table: verified myself against the source files
- F-008 manual runs: checker right; patch sets saveManualExecutions True (patches/F-008 line 12). Fixed.
- n8n-owns-vs-desk-owns.md quote: checker right, it is line 12 (item 9). Fixed in FINDINGS row 2 and CUT-LIST step 3b.
- table-screen-v2 README: checker right, "public" is line 49, "NOT run" lines 3 and 51 (line 50 is blank). Also: the "conflict" is between the two READMEs (v1 README says NOT RUN; v2 README says v1 "was run live ... and works"), not inside one file; wording corrected.
- mf.py: checker right, T17 is 339-347, T18 348-357. Fixed.
- build_mainframe.py: checker right, 82-83 INSERT, 84 Claimed IF. Fixed in F-002 row. (FINDINGS row 1 already said 82-83.)
- PLAN-4 "single-flight": checker only partly right. The claim "one single-flight lock" is supported at :79 ("ONE in-process lock (single flight)"); the hyphenated word is only at :82. :78 is the "three idempotency layers" line and does not support the claim. Cite changed to :79 with a note on :82.
- Bare REPORT.md: FINDINGS F-037 (REPORT.md:695) and F-041 (:622) are handover/demo/REPORT.md (read lines 695, 622: match). CUT-LIST had five more bare cites (:29 :32 :84 :21 :38), also demo/REPORT.md (read: match). All now carry the full path. The checker's ":53" has no bare REPORT.md; not found.
- REPORT.md 08:47 stamp: correction note added, stamp kept. PASS 5 vs 4 patches: FIX-PLAN is right (check_patches now 4 after F-001 archived); REPORT:8 now says 5 at that time, 4 now.

## Applied (order a to k)
(a) Counts: FINDINGS counts table is canonical. FINDINGS paragraph, the scenes-line copy, FIX-PLAN lines 3 and 22, REPORT result line and LEDGER-ROWS header now say "see the FINDINGS counts table". Old 8/8/29 stays once, tagged AUDIT TRAIL, in FINDINGS (the line above the scenes note). QUESTIONS Q4 and Q9 old numbers tagged SUPERSEDED.
(b) Q19-1: removed "deleted at clean-up" and the delete step from FINDINGS (short answer 4, F-008 row, F-011 row, F-043), FIX-PLAN item 4, EXCEPTIONS paste, REPORT lines 8 and 52. Wording: no deletion promise in the video or owner sheet (Q19-1); the lead's optional clean-up of the take's own database is written nowhere in them (Q21). F-008 row also says manual runs saved too and recovery ACCEPTED (Q18).
(c) EXCEPTIONS paste: bracket that role separation is conditioned on the parked ROLES work (decision 3) and not part of the video claim; F-010 named canonical for the role count (F-011, F-041); F-041 T-ROLES row says PARKED. Cost line added to EXCEPTIONS row 1.
(d) CUT-LIST: steps 1 and 2 marked DROPPED (Q17-3), kept as trail; header exception sentence rewritten; gate added at step 4 (no archive of n8n-flows-v4 or v3 until the take folder holds its own mf_leads.sql and the psql four-column check passed); pointer row for archiving OWNER-STEPS v3 (decision 10); FINDINGS rows 9, 58 and F-026 fixed the same way. QUESTIONS Q16 text fixed: v3 and v4 copies are byte-identical (cmp run by me), the take uses the v4 file.
(e) FIX-PLAN item 7: F-023 is "after the video, nothing now". FIX-PLAN :10, FINDINGS F-003 and F-004 rows, REPORT:89: I read the current patches. F-003 and F-004 were regenerated 10:38 UTC; the added lines carry no 60.1 or 61.9 (grep) and no scene 5; they move scenes 5 to 11 to a not-for-this-video section and strike statement 20. Text now says exactly that.
(f, answered by Q21 so no "route unsettled" needed) F-037, F-029, F-018, FIX-PLAN item 3, LEDGER rows: the take's route is fill_flows literals; the check is that no flow node reads $env; the old N8N_BLOCK_ENV_ACCESS_IN_NODE/T-ENV route is one line, "not the take's". F-044: both options written, lead decides at re-pin. F-011 and F-041 stay Major, never downgraded by counting. Cost line written.
(g) Card retention (F-003, F-032, LEDGER F-032): tagged SUPERSEDED by Q15 and Q19-5.
(h) QUESTIONS: Q1 (ORDER 003), Q4 to Q9 (ORDER 013), Q10, Q11 (10:02Z), Q18 (11:10Z), Q19 and Q20 (11:20Z; Q20 item 4 open), Q21 (11:25Z) marked ANSWERED.
(i) REPORT open-decisions line rewritten (Q4 to Q9 and Q18 to Q21 answered; open: Q20 item 4 and Q22).
(j) QUESTIONS Q22 added: pointer list of open lead decisions with no number. FIX-PLAN: psql check and take_check exit 4 added to item 3; decision 2 (owner deletes leftover contacts by hand) added as an unnumbered line (keeps "9 items"). FINDINGS NOT COVERED items 18 to 21 added (take scripts unseen, v4 columns lead-verifies, HubSpot id probe pending, decision 2).
(k) Rubric defined once (FINDINGS counts paragraph points to Words used); F-012 row moved to the AFTER Nit group and a heading added above the findings table; full paths; EXCEPTIONS row 2 "delete this row" now "mark CLOSED (rows are never deleted)"; LEDGER F-001 status CLOSED-DROPPED. Coordinator note: K1 numbers now read "relayed, raw not seen, measured on stand-in film-v4 flows" (NOT COVERED item 5, F-004 row).

## Verification (command output)
python3 tools/count_findings.py FINDINGS.md:
rows 45 unique 45
| Blocker | 5 | 0 | 5 |  | Major | 7 | 0 | 7 |  | Nit | 1 | 32 | 33 |  | all | 13 | 32 | 45 |
sev {'Blocker': 5, 'Major': 7, 'Nit': 33}
(The tool has no line named RESULT; the last line is the sev dict above.)
LEDGER-ROWS.md: 45 rows; ids and severity words equal FINDINGS (python comparison printed True, no mismatch).
Needs from QUEUE.md (lead-owned, not edited): line 8 stale "delete at clean-up" exception; F1-F8 tags answered-but-open (Q18 to Q21).
