# fix-findings-ledger14 (round 14, one fixer; files edited: FINDINGS.md and LEDGER-ROWS.md only)

## Failures and uncertainty first
- Item 5 (TAKE-CHECKLIST.md and FIX-PLAN.md sentence "fix A cannot close on Tuesday as things stand") NOT touched: another fixer has it, as told.
- Item 6: QUESTIONS.md NOT edited (another session owns it). The final question text is now inside the F-011 cell, part (2), with the statement that the studio lead must add it to Q31 before Tue 17 Nov 03:00Z (08:30 IST). Until the lead does, Q31 does not hold the question: this is OWNER/LEAD-ONLY, next step named in the cell.
- Item 9: the HubSpot probe has no free slot in any file; I did not invent one. The cell now says it is an input of the practice hour (Wed 06:00Z to 07:00Z, 11:30 to 12:30 IST), minutes and place in the hour LEAD FILLS, unmeasured. Who reads the HubSpot count stays NOT NAMED, lead decides (no Q31 item asks it; item 54 asks only for the command and search method; I did not add an item).
- Items 3 (reader), 7 and other claims were checked by text, nothing was run in n8n. The compare script checks severity, status first word, bold summary and the fix cell (the same checks as rounds 11 and 12); it does not compare the area, source or verified-by columns, which differ by design.
- check_refs reports 5171 references (round 12 said 5176): the difference is the removed pointers to reviews/fix-findings-ledger11.md in two places; check passes.
- Not checked: the nits "T7b/kill run used before defined" are fixed in the F-011 cell at first use there, but FINDINGS.md lines 18, 31 and 55 (top paragraphs) still use T7b before that cell; the words list does not define T7b.

## Finding to result
| item | claim | verified by text | result |
|---|---|---|---|
| 1 | F-011 step 7 time stale | TRUE. RUNBOOK 201: clock "6 at 04:54, 8 at 05:14, 7 at 05:39"; RUNBOOK 200 table: step 7 = 05:39 (11:09 IST) / 05:10 (10:40 IST); QUESTIONS 530 and 548: 05:39Z becomes 05:10Z; TAKE-CHECKLIST 59 says 05:39Z; QUESTIONS.md line 50 (Q31 item 10 ROUTE POINT) says 05:39Z on the 04:00Z clock and 05:10Z on the 03:31Z clock. 05:14Z is step 8 start, not step 7. | F-011 cell now says 05:39Z (11:09 IST) option 2, 05:10Z (10:40 IST) option 1. |
| 2 | F-011 (b) vs (5) vs EXCEPTIONS.md | TRUE. EXCEPTIONS.md row 2: "NOT an exception ... mark this row CLOSED". | (5) now splits by route: fix A closes the row; downgrade route makes it a live exception rewritten by the studio lead, words "NOT an exception" replaced; (b) says the same and that the owner cell names the studio lead. |
| 3 | "only route" vs "no route can succeed" | TRUE (FINDINGS F-011 cell, STATE OF FIX A vs IF NOBODY ANSWERS). | Now "If the studio lead answers, the only route ... is the downgrade route ...; under the unanswered defaults no route can succeed." |
| 4 | second reader has no step, time, artifact | TRUE. | New line (4b) in F-011 (WHO, WHAT, BY WHEN Tue 17 Nov 07:00Z (12:30 IST), ARTIFACT one ledger line with reader, time, agree/disagree); F-041 points to it with the same four parts. Default kept (no answer: no downgrade counts). |
| 5 | plan files | not mine | not touched |
| 6 | first Tuesday question not in Q31 | TRUE (only in reviews files). | Final text inside F-011 cell part (2); lead must add before 03:00Z (08:30 IST) Tue; pointer in the decision table row (FINDINGS line 55) updated. |
| 7 | F-002 "Q26 item 1 puts it at 08:00Z" | TRUE. 08:00Z is the planned end with 03:31Z start; RUNBOOK section 5 Shortfall: 08:29Z with 04:00Z. | Cell now: "the re-pin ends about 08:00Z (13:30 IST) if it starts at 03:31Z, and 08:29Z (13:59 IST) with the default 04:00Z start". |
| 8 | $REPO needed Wed 06:00Z | TRUE (4 rows used it: F-003, F-007, F-031, F-028). Inputs table row 3 already says first needed Tue 03:30Z. | All 4 now: "first needed Tue 17 Nov 03:30Z (09:00 IST), Wed 18 Nov 06:00Z (11:30 IST) is the latest". |
| 9 | F-018 probe slot | TRUE (WEDNESDAY CLOCK: practice run 06:00-07:00Z, T19-T21 its end, Row 4 07:00-07:30Z). | Probe marked an input of the practice hour, no separate slot held, minutes LEAD FILLS; count reader marked NOT NAMED, lead decides. |
| nits | T19 "$N8N_PORT as in T20" | TRUE | now "= the take's n8n port, defined at the T20 command below" |
| nits | Q21 vs Q31 item 21; letter A; T7b and kill run | TRUE | words list (FINDINGS only) explains Q21 and the letter A; F-011 summary explains T7b and K1 kill run at first use (T7b = mf.py scan of n8n's data files for planted fake values; K1 = n8n stopped by force after the claim insert, before the CRM write; read from mf.py lines 151 and 274). |

Changed rows (before/after diff by line): FINDINGS: F-002, F-003, F-007, F-011, F-018, F-028, F-031, F-041, line 55 (decision table), line 94 (words list). LEDGER-ROWS: header line plus the same 8 rows. No severity, status or count changed.

## Raw outputs (run from flows-audit)
```
$ python3 -I compare14.py FINDINGS.md LEDGER-ROWS.md      (scratchpad copy, same checks as fix-findings-ledger11.md)
45 45 differences: 0
$ python3 -I tools/check_refs.py   -> PASS 5171 references
$ python3 -I tools/check_names.py  -> PASS 655 rows
$ python3 -I tools/check_secrets.py -> PASS 0 hits in 2682 files
$ python3 tools/count_findings.py
rows 45 unique 45
| Blocker | 5 | 0 | 5 |
| Major | 5 | 0 | 5 |
| Nit | 1 | 34 | 35 |
| all | 11 | 34 | 45 |
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
$ ruff format --check .  -> 830 files already formatted
```
Compare script: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/compare14.py (text is the one in fix-findings-ledger11.md). EGM: this is a text fix of audit files in round 14, no code; review of the result is the lead's step. Not committed.
