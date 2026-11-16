# fix-findings-ledger4 (fixer, 2026-11-16, static; nothing ran in n8n; edited only FINDINGS.md and LEDGER-ROWS.md; not committed)
Source: reviews/findings-ledger-reader-r3.md (reviewer words unverified; each cited row and source opened first: flow JSON in handover/demo/n8n-flows-real-v5, ORDERS.md, QUESTIONS.md Q31, EXCEPTIONS.md, the F-003 patch header). Severities unchanged (5 Blocker, 5 Major, 35 Nit). No lead decision invented: open points read "unknown: studio lead answers X by <time>" with a Q31 item number where one exists.

## Fixed (finding, what changed, where)
1. F-018 Tuesday NO-GO contradiction: CONFIRMED (pass line = step 10b, Wednesday; flag 'counts'). Now stated plainly in the F-018 fix cell ("TUESDAY CONTRADICTION") as the audit's safe default, not a ruling; the question already exists as Q31 item 31 (answer by Tue 17 Nov 06:45Z, 12:15 IST), so nothing new was appended to QUESTIONS.md (not mine). FINDINGS.md F-018 row (line 117) fix cell; LEDGER-ROWS.md line 27 (same text).
2. F-031 pass line (2) vs F-003: CONFIRMED (the F-003 patch edits only handover/demo/VIDEO-RUNSHEET.md, checked in patches/F-003-runsheet-claims.patch line 4; it cannot change flow behaviour). The claim "the F-003 patch ends a stop in the mail window as unknown with one alert" is removed; replaced by: unknown and failed rows are the two states AlertClaim selects (build_mainframe.py:105 read), whether a mail arrives is UNVERIFIED. FINDINGS:113, LEDGER:8.
3. Silent failure vs alert: one ALERT RULE (a) to (d) written once in the F-037 evidence cell (FINDINGS:114), marked UNVERIFIED, from mf-recovery.json (connections: AlertSend error output -> AlertBackoff; AlertClaim state IN unknown, failed; MarkFailed; line 177 fromEmail placeholder, line 178 toEmail $env) and mf-sub-crm-mail.json (Qualify, LabelOk, CrmUpsert, CrmIdOk error or false outputs -> OutStage before MailClaim). F-031, F-018 (ALERT HALF pointer and the answer-shape sentence) and F-029 point to it. F-029 headline fixed (the garbled "trace named here" sentence): FINDINGS:118 bold sentence and LEDGER:15 summary (identical). F-037's "AlertSend error output goes to AlertBackoff" now says wiring read, behaviour UNVERIFIED. F-031's stale sentence "is this really a Blocker? is not yet asked in QUESTIONS.md" was WRONG: it is Q31 item 17; corrected in both cells.
4. F-018 grep command vs prose: CONFIRMED (the old command tested fromEmail, line 177, the sender). Replaced by `grep -c -E "\"toEmail\".*$INTAKE_ADDR" "$FILLED"/mf-recovery.json` (prints 0; no pipe, because a " | " inside a cell splits the table row; my first version used a pipe and broke the column count, caught by the comparison script and redone). I tested the pattern on a made-up two-line file: other address prints 0, same address prints 1, empty variable prints 1 (fails safe). A control for the toEmail line is added. Not run against the real filled copy (does not exist here).
5. F-008/F-011 decider wording: checked ORDERS.md line 20. ORDER 004 is written by the studio lead and holds TWO decisions: Reading A (studio lead, F-011) and "executions saved ON for the take only (owner 2026-11-16)" (owner, relayed; F-008). Both rows now say so; the F-011 'OWNER' label is called a wrong label for Reading A. SQLite/EXCEPTIONS clash stated once (F-011 fix cell, "Then edit the SQLite row"): EXCEPTIONS.md row 2 says "NOT an exception" and its own status cell says mark CLOSED with the date, rows never deleted; the studio lead confirms the edit (unknown, by Tue 17 Nov 07:00Z, with Q31 item 26). The duplicate "Wording gap" sentence is removed from the F-011 summary. Also corrected a wrong claim in F-011 downgrade part (b): EXCEPTIONS.md DOES have a removal trigger ('the re-smoke runs on Postgres (F-011)'); what it lacks is a review date and a named owner word.
6. F-002 timing: re-pin now stated as the Tuesday 17 Nov event (glossary; RUNBOOK steps 1 to 15; Q26 item 1 answer about 08:00Z) instead of "date and hour LEAD FILLS"; only the start hour stays LEAD FILLS. F-002b (due Tue 12:00Z) is said to come after the re-pin; Q31 item 16 cited. The 30-minute window (tests from about 07:00Z, Blocker checked 07:30Z) is written as "TIME WINDOW", durations of rebuild and re-pin marked unmeasured, UNVERIFIED, and the open question tied to Q31 items 8 (e) and 49 (Tue 17 Nov 07:00Z). The headline (and LEDGER summary, identical) now gives the real Blocker reason (the untested patch) before the flaw.
7. "not stated" consequences replaced: F-003 (unknown; studio lead answers by Tue 17 Nov 06:45Z; no Q31 item for F-003 yet, see "for lead" below), F-007 (by Tue 07:00Z with Q31 item 11), F-031 (by Tue 06:30Z with Q31 item 17), F-008 and F-029 (Q31 item 26, whose default NO-GO rule is quoted, ORDERS.md line 156 item 9), F-018 (Q31 item 31), F-037 (Q31 item 21 by Tue 07:00Z; filled folder unknown, Q31 item 59 by Tue 03:30Z).
8. Words: bare "lead" converted (F-007 pasted table text and spoken line -> "sales lead"; quoted "lead sets" kept and labelled as the studio lead's words; F-011 'lead' explained). F-041 take column is now plain "take" (FINDINGS:119) and the LEDGER area cell reads "take inconsistent; TAKE-PATH: yes; ..." (LEDGER:16; the ruling text is already in the when cell and the fix cell). "always=False" glossed as alwaysOutputData off in F-002 (3 places). "re-pin" qualified at first use in the fix cell of each row that uses it.
9. UNVERIFIED marks added: F-008 (run saving none keeps no record; saved runs hold names), F-011 (n8n starts on SQLite inferred from a grep; DB_TYPE and DB_POSTGRESDB_* names), F-002 (bare 500 in headline and summary; array value becomes a string), F-037 (AlertSend error output).
10. Five-part summary: the existing DECISION block of each of the 10 rows now stands at the top of its fix cell as "SUMMARY (five short parts ...)", identical in both files (the old end-of-cell block removed, so no duplicate). LEDGER-ROWS.md line 1 got one sentence saying so.

## For lead (question text; Q31 is not mine to edit)
- F-003 (no Q31 item exists): "Does an open F-003 (run sheet captions) count in Tuesday's GO row 6, and if F-003 is still open at Wed 18 Nov 06:00Z does the take run? Answer by Tue 17 Nov 06:45Z (12:15 IST). If unanswered the row stays Blocker and OPEN and no default applies."
- F-018 (already Q31 item 31): confirm "counts or out"; the audit recommends "out".

## Disputed / reviewer words found wrong
- Reviewer point 3 said F-031 states unknown and failed rows are alerted "unconditionally": true as written, and F-037 contradicted it; resolved by the ALERT RULE, not by deleting either row's finding.
- Reviewer point 7 said F-031 "is this really a Blocker?" has no owner or time: it has one (Q31 item 17, Tue 06:30Z); the row text was stale, now corrected.
- Reviewer "F-008 vs F-011 decider clash" is partly a misreading: both are right for different decisions inside ORDER 004; wording now says that.
- F-011's own claim "EXCEPTIONS.md has no removal trigger" was wrong (found while checking); fixed.

## Needs lead (not decidable here)
Tuesday GO flag for F-003 and F-018 (above); which EXCEPTIONS.md edit for SQLite; whether the 07:30Z check moves if T19 fails; F-037 rating (Q31 item 21).

## Not done / not checked
Nothing ran in n8n or HubSpot. I did not re-read the other 35 rows or the other documents. Bare "lead" outside the 10 rows is unchanged. The reviewer said rows are many thousands of words: the summary at the top helps, but F-002 is still about 20,000 characters; I did not shorten the detail (the detail holds test commands other files point to).

## Comparison script and output
(inline python3 -I, same as fix-findings-ledger3: each row split on ' | '; 45 ids x 7 columns incl. fix cell with the two known prefixes for F-001 and F-013; plus a plain FINDINGS col 7 vs LEDGER col 6 compare)
```
ids FINDINGS 45 LEDGER 45 only in one: []
cells compared 315 (45 ids x 7 columns); differences: 0
differing ids (plain fix-cell compare, F-001 and F-013 excluded): []
prefixed ids differ only by the known prefix: [('F-001', True), ('F-013', True)]
rows with wrong column count: FINDINGS [] LEDGER []
--- count_findings: rows 45 unique 45; Blocker 5/0/5, Major 5/0/5, Nit 1/34/35, all 11/34/45; sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
--- check_refs: PASS 5176 references
--- check_names: PASS 655 rows
--- check_secrets: PASS 0 hits in 1997 files
--- ruff format --check .: 711 files already formatted
```
