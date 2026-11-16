# Drift report ORDER 007 refresh (egm drift), 2026-11-16 (read-only static check; nothing was run in n8n, HubSpot, SMTP or Postgres)
Old 16-line file copied to /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-drift7.md before replacing. Fixed nothing; every item below is a divergence or a plain note, with file:line.
Counts were computed by script, not by eye: `python3 -I tools/count_findings.py FINDINGS.md` (output below), plus three small scripts in the scratchpad that compared FINDINGS.md rows with LEDGER-ROWS.md rows (id set, severity cell, take column against TAKE-PATH flag, BEFORE/AFTER against GO row 6, status first word, fix cell) and that scanned every F-number in all scope documents. The raw output of those scripts was not saved as a file.

count_findings.py output: rows 45 unique 45; Blocker 5 (BEFORE 5, AFTER 0); Major 5 (5, 0); Nit 35 (BEFORE 1, AFTER 34); all 11 + 34 = 45.
Actual: 45 rows = 5 Blocker, 5 Major, 35 Nit; BEFORE 11, AFTER 34. This equals the expected numbers. The old brief's "8/8/29, BEFORE 17, AFTER 28" is stale and appears only as marked history (FINDINGS.md:97, QUESTIONS.md:493).

## FINDINGS.md
- Row count 45, ids F-001..F-046 without F-040 (merged into F-014), all unique; table at FINDINGS.md:90-95 says 5/5/35, 11/34/45; header FINDINGS.md:1 arithmetic holds (34 + 11 = 45; F-035..F-046 minus F-040 = 11). Matches the script.
- FINDINGS.md:85 says "8 items left" for BEFORE; FIX-PLAN.md:53 says "9 numbered items plus 8b" with item 1 dropped (so 8 numbered items + 8b = 9 live). Reads differently; not a count of findings. Minor wording drift.
- FINDINGS.md:85 and :103 say F-018 is a Major (reachable, round 16Z); the table row agrees (Major). See FIX-PLAN.md below for the one document that still calls it Nit-rated.

## FIX-PLAN.md
- FIX-PLAN.md:53: "items 3, 7 and 9 also carry Nit-rated lines (F-018, F-019, F-028)". Divergence: F-018 is a Major in FINDINGS.md (row, :85, :103) and LEDGER-ROWS.md, and FIX-PLAN.md:56/70/75 itself treat F-018 as a counted pass line; F-019 is AFTER (FINDINGS.md:135) with no BEFORE item. Only F-028 is a BEFORE Nit (the one BEFORE Nit in the counts table).
- BEFORE item numbers used in FINDINGS "when" cells (2, 3, 4, 5, 7, 8) all exist in FIX-PLAN.md (items 2 to 8, 8b at :101). No dangling item.

## CUT-LIST.md
No drift detected (no counts, no finding ids outside F-001..F-046).

## EXCEPTIONS.md
No drift detected (no finding counts; F-011 SQLite exception referenced by QUESTIONS.md Q18 is consistent with the F-011 row, not re-read line by line).

## QUESTIONS.md
- QUESTIONS.md Q19 (:467): "Blocker 5, Major 5, Nit 35; BEFORE 11, AFTER 34"; if F-018 reverted "Major 4, Nit 36; BEFORE 10, AFTER 35". Matches the script (the revert case was not run).
- Q21 (:469): "Blocker 4, Major 6" if F-037 re-rated. Arithmetic consistent with 5/5/35 (5-1, 5+1).
- :275 (Q9 original question) quotes the old "8 Blocker / 8 Major / 29 Nit"; its answer is recorded at :256 and the old numbers are marked SUPERSEDED at :493. Intended history, not drift.
- :52 header says 33 LEAD ACTIONS rows; the table has L1..L33 (33 rows). Match.
- Q17 (:465), Q19, Q21 are OPEN and ask about F-031, F-018, F-037 ratings. The FINDINGS and LEDGER ratings are the "audit default" (F-031 Blocker, F-018 Major, F-037 Blocker); consistent.

## LEDGER-ROWS.md
- 45 rows, ids identical to FINDINGS.md (symmetric difference empty), severity cell identical in all 45, severity first word totals 5/5/35, statuses equal the FINDINGS status first word in all 45. Rows have 9 cells (header at :1 says 9 columns).
- TAKE-PATH flag agrees with the FINDINGS take column in all 45 rows. BEFORE rows map to GO row 6 `counts`/`out`/`lead decides` in all rows except F-028 (BEFORE 7, Nit, "not counted"), which is correct for a Nit.
- Fix cell equals the FINDINGS fix cell except F-001 (LEDGER-ROWS.md:2) and F-013 (:22), which add a lead decision line; :1 states exactly this. Intended.
- Awk filter of TAKE-CHECKLIST.md Block R6 run on this file: counted rows F-037, F-008, F-011, F-029, F-041, F-018 (all OPEN); "lead decides" row F-003. Equals TAKE-CHECKLIST.md:258 and :79. Match.

## REPORT.md
- REPORT.md:28 says "45 rows; counts: see the FINDINGS counts table (canonical)" and gives no number of its own. Matches.
- REPORT.md:82 ("34 findings = 2 Blocker, 23 Major, 9 Nit") and :100 ("34 findings (1 Blocker, 27 Major, 6 Nit)") are older dated sections (ORDER 002). They are not marked SUPERSEDED in place. A reader who stops there gets wrong counts. Divergence (labelling), not a calculation error.
- REPORT.md:28 and :29 still say F-002, F-031, F-007 are Blockers "by the lead's order"; FINDINGS.md rates all three Blocker. Match.
- REPORT.md:3 says "That is 8 agents" and lists 8 ids. Match. The register in STATUS-BOARD.md lists 6 (different time, board is later).

## STATUS-BOARD.md
- :6 ITEMS_TOTAL 12 but the ITEMS table (:16-:25) has 10 rows (F1-F9, H1); :7 ITEMS_OPEN 30 is larger than the total and matches no row count (5 rows say "running"). Internal divergence; no finding counts on this board.
- :8 AGENTS_RUNNING 6 equals the 6 rows in the AGENTS table.
- :52 "Answer Q4-Q9 in QUESTIONS.md ... Not blocking" is stale: REPORT.md:31 and QUESTIONS.md:248-256 say Q4 to Q9 are ANSWERED.

## RUNBOOK.md and TAKE-CHECKLIST.md
- TAKE-CHECKLIST.md:79, :258, and RUNBOOK F-ids: every F-number cited exists in FINDINGS.md (script scan of all scope documents found no F-number outside F-001..F-046; F-040 appears only in "merged into F-014" or "F-040" notes: FINDINGS.md:1, :103, :131, :147; FIX-PLAN.md:105; QUESTIONS.md:248, :256; LEDGER-ROWS.md:23, :40; each intentional).
- TAKE-CHECKLIST.md:382 says "the 45 findings"; matches.
- TAKE-CHECKLIST.md:284 says the checks table has 16 rows (1 to 14 plus 3b, 5b); not recounted.

## patches/ and lanes7/
- patches/ holds 4 .patch files (F-002, F-003, F-004, F-008); F-001 is in patches/archive/ (Q17-3). Consistent with FIX-PLAN.md:54 and FINDINGS.md F-001 row. patches/REGENERATED-NOTE.md says "now 4 after F-001 was archived"; match.
- lanes7/evidence-*: not re-read. I ran `bash tools/check_patches.sh` (read-only check) from handover/flows-audit and it printed "SKIP no patches", not a PASS. I did not find out why (it probably expects another working folder). So I have NOT verified that the 4 patches apply; the earlier "PASS 5 patches" (STATUS-007.md:3) is the only evidence and is old.

## Words searched in REPORT.md and FINDINGS.md (file:line; none fixed)
- limitation: no hits in either file.
- not done: REPORT.md:8 (Q25 item 8, no decision number exists), :21 (ORDER 023 NOT DONE, later cancelled by ORDER 024, said inline), :86 (heading "Not done and why", ORDER 002 history).
- not verified: REPORT.md:71, :102, :108 (all say UNVERIFIED items need n8n, HubSpot or SMTP; :71 carries a SUPERSEDED note).
- skipped: REPORT.md:107 (check_secrets skipped a prefix-named file, reported as fixed).
- could not: REPORT.md:107 ("first masking test could not fail", fixed), :142 (match inside a ruff note, not re-read), FINDINGS.md:114 (F-008 row, "could not tell an applied patch from an unapplied one" describing an old guard).
- out of scope: FINDINGS.md:45 (item 15, load numbers "were out of scope", still a plain statement with no next step; this is the kind of deferral CLAUDE.md fix-dont-defer asks to fix or classify). FINDINGS.md:57 ("one full watch not done", item 26, owner is the lead; classified).
- TODO, deferred: no hits.

## Not checked
Anything that needs n8n, Postgres, HubSpot or SMTP (UNVERIFIED in FINDINGS); per-node tables in FLOWS-AUDIT.md; Q-item answers against ORDERS.md (not in scope); every F-row's evidence cell against demo sources (I did not open handover/demo for this refresh); RUNBOOK.md and TAKE-CHECKLIST.md beyond the counts, F-ids and Block R6 filter; EXCEPTIONS.md and CUT-LIST.md content line by line; the revert cases in Q19 and Q21 (arithmetic checked by hand only); whether check_patches.sh passes; ledger_check (does not exist in this repository).
Drift found that needs a fix: FIX-PLAN.md:53 (F-018 and F-019 wrongly named Nit-rated lines); STATUS-BOARD.md:6, :7, :52; REPORT.md:82 and :100 (unlabelled old counts); FINDINGS.md:45 (out-of-scope item with no next step); FINDINGS.md:85 vs FIX-PLAN.md:53 (8 vs 9 items).
