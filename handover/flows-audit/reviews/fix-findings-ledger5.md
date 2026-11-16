# fix-findings-ledger5 (fixer, 2026-11-16; static, nothing ran in n8n; edited only FINDINGS.md and LEDGER-ROWS.md and this log; not committed; QUESTIONS.md not touched)

Source: reviews/findings-ledger-reader-r4.md (13 findings and word notes; reviewer words unverified, each point checked against the files first). Severities unchanged (5 Blocker, 5 Major, 35 Nit; BEFORE 11, AFTER 34, recounted by the script below). Edits were made by one script that applied each change to both files and refused to run if an old text did not occur exactly once (65 edits).

## Not verified / not done (first)
- Nothing ran in n8n, Postgres or HubSpot. Every n8n behaviour sentence stays UNVERIFIED.
- Files other than the two edited ones are NOT changed, so these still need the lead: patches/F-003-runsheet-claims.patch still carries the retention sentence "as built the four real-v5 flows save no runs, until F-008 is applied" (point 13); the spoken line "ends unknown with one alert mail to the owner" may also stand in other files (I grepped only for the exact phrase: it was found in FINDINGS.md and LEDGER-ROWS.md only); FIX-PLAN and RUNBOOK were not re-read beyond the "Time:" line of FIX-PLAN and the TAKE-CHECKLIST rows 6 and 7.
- The reader's point 8 claim that rebuild and re-pin time is unmeasured is true and stays unmeasured; I added the audit's reading (a failed T19 at 07:00Z probably means no time left), marked UNVERIFIED, not a measurement.
- I did not check the reader's "about 2 days left" text: I found only the "2 to 3 working days" estimate (FINDINGS line 86), which FIX-PLAN.md itself calls SUPERSEDED, and fixed line 86 to say so.
- Allowed-hit list of F-007 (point 11) is still not written: it is LEAD FILLS (needs the studio lead).

## Fixed (point, verdict, change)
1. Who is who: CONFIRMED. Words list now has "WHO DECIDES WHAT" (studio lead decides the questions, the ledger, GO or NO-GO: ORDERS.md line 156 items 5 and 7; owner decides money, spending, publishing, what a later video claims). Who may overrule a Blocker rating or a NO-GO is written nowhere: "unknown: lead answers (question text below)".
2. F-003 has no Q31 item: CONFIRMED (items 11, 16, 17, 19, 21, 23, 31 etc. exist, none for F-003). F-003 row now says "unknown: lead answers (question text in the audit log)", names the nearest real item (31, due Tue 17 Nov 06:45Z) and says the Tuesday GO or NO-GO for F-003 is unstated.
3. Wrong Q31 items: CONFIRMED. F-007 now says item 11 asks only who applies; the "what an open F-007 means" question has no item (text below). F-031 now lists the real items: 17 (still a Blocker, 06:30Z), 23 (which part closes, 07:00Z), 19 (severity changes, 07:15Z, interacts with 17) and says none asks the take question. "Who applies" in F-003, F-007, F-031 is now written as the audit's reading with item 11 open.
4. "Take path" two meanings: CONFIRMED. Words (3) now matches the 'take' column and the ledger header: the file or node is in the take; it does not say a scene reaches the failure; F-011 and F-041 are in by ruling Q27 item 9. Ledger header carries the same sentence.
5. "Blocker" three meanings: CONFIRMED, with one correction to the reader: ORDERS.md line 32 item 2 also names F-003 a Blocker, so F-003 is "by rubric" and also in the lead's list. Defined once in the severity rubric (BLOCKER KINDS): Blocker by rubric = F-003 and F-037; Blocker by lead order = F-002, F-007, F-031; Major by lead order = F-011, F-041; F-008, F-018, F-029 Major by rubric as the audit rates them. 5 Blockers = 2 by rubric + 3 by lead order. A "RATING KIND" line sits in each of the 7 fix cells (identical in both files). Lines 89 and 100 now list every exception and say F-003 and F-037 are not exceptions.
6. F-011 and F-041 Major without take risk, and GO row 6 against GO row 7: CONFIRMED (TAKE-CHECKLIST row 6 = no open Blocker or Major in take-path code; row 7 = F-011 and F-041 fixed or downgraded, otherwise automatic NO-GO). Both rows now say Major by lead order (by the rubric Nit). Ledger area cells say "GO row 6: counts, and GO row 7 decides it"; the words list says the two rows give the same outcome and row 7 has the deadline.
7. F-018 open at Tuesday GO: CONFIRMED. Words list and ledger area cell now say it is necessarily open at the Tuesday test unless flagged out; Q31 item 31 (due Tue 06:45Z) decides. The F-018 fix cell already held the TUESDAY CONTRADICTION text (ledger4).
8. F-002 window and fallback naming: CONFIRMED in part. The sentence "same question as Q31 items 8 (e) and 49" was wrong (those ask what a T21 failure does). Now: no Q31 item asks whether 07:30Z moves; nearest items 8 (e), 49, 16 named; audit's reading added. One meaning of the fallback written: F-002b is for a failed T19; items 8 (e) and 49 ask whether it may also be used after a failed T21; item 16 asks whether it is written now. The T19 wait is tied to Q31 item 50.
9. F-007 spoken line vs F-014: CONFIRMED. Spoken line is now "ends in state unknown, and an alert mail goes to the owner if the alert mail can be sent" (no number of mails); the bracket sentence now says a single alert holds only if the mark step succeeds.
10. ALERT RULE vs softer rows: CONFIRMED for F-012 and F-013 (F-014 and F-030 already carry the caveat). Both now say a person is told only if the alert mail can be sent (ALERT RULE in the F-037 evidence cell, UNVERIFIED). F-013 is in both files; F-012 is in FINDINGS only (its cell is not copied to the ledger).
11. F-007 needs F-004: CONFIRMED. F-007 fix cell has a DEPENDENCY ON F-004 sentence; line 86 says the F-004 patch is work for the re-pin that the BEFORE column does not show and that the "2 to 3 working days" estimate is superseded by the lead's schedule in FIX-PLAN.md. The count table is unchanged because the rule "BEFORE = the 'when' cell starts with BEFORE" is canonical and I did not change F-004's label.
12. Role count and SECOND_ADMIN: CONFIRMED. F-011 no longer says "the three roles of F-010 stay"; it says the number is not chosen (F-010 ROLE COUNT) and n8n's own role is one more, FIX-PLAN proposes four. SECOND_ADMIN is now defined in the F-002 T21 METHOD (a second way to run ALTER ROLE ... LOGIN, file inputs/SECOND_ADMIN.sh not existing, Q31 item 82, due Wed 05:45Z). "Flows role" is already defined in the same cell as $FLOWS_ROLE.
13. F-003 retention note stale: CONFIRMED. The F-003 cell now says F-008 and the patch land at the same re-pin, gives the true sentence after F-008, and orders F-008 before the F-003 re-read. The patch file itself is not edited here (listed above).
Word notes: step = node and "655" (defined in the words list; F-026 summary now says "525 of 655 steps"); lead ID = lead key = lead_key (defined); "ends unknown" replaced in the F-007 spoken line (the two other hits quote withdrawn wording inside the F-037 cell and are left as quotes); F-018 "demoted to Nit" on line 104 now says history only, Major again since round 16Z.

## Disputed / reviewer words found wrong
- Point 5: not only F-003 is rubric-based in the lead's list: F-003 is also named in ORDERS.md line 32 item 2 (see above). F-037 is the audit's own rating.
- Point 11 "about 2 days left": not found in any file I read; only the "2 to 3 working days" text, now marked superseded.
- Point 8 "T19 wait BEFORE T19 starts but LEAD FILLS": not a contradiction (the lead fills it before T19 starts); I added the Q31 item 50 pointer instead of changing the rule.

## Question texts for the lead (QUESTIONS.md is not mine to edit; each is plain-worded and standalone)
A. (F-003) "Does an open F-003 (the stale and wrong captions in the video run sheet) count in Tuesday's GO test row 6? If it is still open on Wed 18 Nov 06:00Z, does the take still run? Today no file answers this and no Q31 item asks it. Please answer by Tue 17 Nov 06:45Z (12:15 IST), the same time as Q31 item 31. If unanswered the row stays Blocker and OPEN and the audit invents no default."
B. (F-007) "If F-007 (the kill case names K3 and K3B differ between the page, the run sheet and the test program) is still not applied and re-read on Wed 18 Nov 06:00Z, does the take run or is it NO-GO? Q31 item 11 asks only who applies the text. Answer by Tue 17 Nov 07:00Z (12:30 IST)."
C. (F-031) "If F-031 (a sales lead with an invalid e-mail address ends in state review and nothing alerts) is still open on Wed 18 Nov 06:00Z, does the take run? Q31 items 17, 23 and 19 ask other things (still a Blocker, which pass part closes it, severity changes). Answer by Tue 17 Nov 06:30Z (12:00 IST)."
D. (F-002) "If test T19 fails at the Wed 18 Nov practice run (about 07:00Z), does the 07:30Z check move to leave time for the fallback patch F-002b, a rebuild and a new re-pin, or is that day NO-GO? Q31 items 8 (e), 49 and 16 ask about a T21 failure and about writing F-002b now, not about this. Answer by Tue 17 Nov 07:00Z (12:30 IST)."
E. (who may overrule) "The studio lead (the Claude session) decides GO or NO-GO and the ledger. May the owner overrule a Blocker rating or a NO-GO, and who may overrule a rating the studio lead set by order? No file says. Answer by Tue 17 Nov 06:50Z (12:20 IST), in the same message as Q31 item 6 (the GO or NO-GO message)."
F. (F-007 allowed-hit list) existing input, LEAD FILLS in the F-007 row: the list of allowed hits of "killed after the mail left" by file and line. No new question; the lead writes it by Wed 18 Nov 06:00Z.

## Comparison script and output
(`python3 -I` script, each table row split on ' | '; 45 ids; fix cell FINDINGS column 8 against LEDGER column 7, equal except the known lead-decision prefix of F-001 and F-013; plus severity, status first word and the bold first sentence against LEDGER column 5; script kept in the session scratchpad)
```
ids F 45 L 45 only one side []
fix cells compared 45 ; differences: [] ; other diffs: []
prefix ids ok {'F-001': True, 'F-013': True} wrong column counts []
--- count_findings: rows 45 unique 45; Blocker 5/0/5, Major 5/0/5, Nit 1/34/35, all 11/34/45; sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
--- check_refs: PASS 5176 references
--- check_names: PASS 655 rows
--- check_secrets: PASS 0 hits in 2011 files
--- ruff format --check .: 724 files already formatted
```
