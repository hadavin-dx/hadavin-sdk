# drift-008 (read-only drift lane, 2026-11-16). Nothing was edited except this file.
Ran: python3 tools/count_findings.py (rows 45; 5/7/33; BEFORE 13, AFTER 32) and python3 claims-count.py CLAIMS-TABLE.md (327 = 124/69/54/29/51; 87 to-do rows; A97 B226 X4; 0 offenders). All quoted counts in the 11 files match. LEDGER-ROWS has 45 unique F-ids = FINDINGS 45. CUT-LIST sums (40 files, 525 nodes) check out.

## Contradictions (file:line | what | disagrees with | fix)
1. FINDINGS.md:129 (F-018) and LEDGER-ROWS.md:27 | "value of DESK_ALERT_TO ... still open (QUESTIONS Q20 item 4)" | QUESTIONS.md:68,72,96, REPORT.md:13, FIX-PLAN.md:6 say ANSWERED (lead sets at take prep, verifies at re-pin) | replace "still open" with the answer in both.
2. LEDGER-ROWS.md:22 (F-013) status OPEN "OWNER/lead: confirm the trade-off" | FINDINGS.md:124 and REPORT.md:13 say ACCEPTED as the trade-off (ORDERS.md line 138 item 2) | set status to the accepted state, cite the order.
3. QUESTIONS.md:5 (Q2 answer) "saved ON ... and deleted at clean-up" with no SUPERSEDED mark; REPORT.md:51 same words (only the later paragraph at :53 is marked) | FINDINGS F-008, FIX-PLAN:20, EXCEPTIONS:16: no deletion promise (Q19-1) | add "[SUPERSEDED by Q19-1]" to both.
4. RUNSHEET-WORDING.md:352 (Q-A) "nothing says who does these actions; until answered [WHO: Q-A]" | RUNSHEET-WORDING.md:63 and CLAIMS-TABLE.md:22,34: scene 4 answered (lead runs it, Q22 item 1) | update :352 (scenes 1 to 3 still open).
5. RUNSHEET-WORDING.md:224 (A-017a) "Default while D1 is not decided: no number on screen" | RUNSHEET-WORDING.md:107: "D1 IS DECIDED (decision 1): no recovery number" | change to "D1 decided".
6. RUNSHEET-WORDING.md:363 "5690 is named in no file here" | OWNER-STEPS-q16-rows.md:63 names 5690 (once, by design) | say "5690 is the rehearsal port (OWNER-STEPS:63); the real-take port is not named".
7. Wording drift, same decision: REPORT.md:9 "the lead's optional clean-up of saved runs" vs FINDINGS:109, FIX-PLAN:20, QUESTIONS:75, CLAIMS-TABLE:141 "of the take's own database" | pick one (database).
8. CLAIMS-TABLE.md:447 "Q7 ... NOT DONE: no sentence about the review state" | QUESTIONS Q7 ANSWERED, FIX-PLAN item 5 owns the sentence, FINDINGS F-031 | confirm the sentence is now written in RUNSHEET-WORDING, or mark the row as FIX-PLAN item 5 pending.

## Checked, no conflict
Take uses demo/n8n-flows-v4/mf_leads.sql (FINDINGS, FIX-PLAN:4, CUT-LIST, QUESTIONS:46, OWNER-STEPS:82, flow-check/README:8, CLAIMS:236). "Processed once" proof = 1 mail + mf_leads row done + POST 2 reply under 10 s (FIX-PLAN:8, QUESTIONS:85, OWNER-STEPS:106, flow-check/README:13, RUNSHEET, CLAIMS). No file says "the CRM was called once" except as a prohibition. "Retries forever" appears only as "never retries forever". "film-v5" is always marked out of this video (RUNSHEET:97,164,382,413 are later-video sections). One video, real-v5 only: consistent. Port 5690 appears only in OWNER-STEPS:63. No recovery number on screen: consistent (RUNSHEET:77,107; CLAIMS:350,352).

## Stale line cites into FINDINGS / FIX-PLAN
FINDINGS.md:57 "FINDINGS 1 to 96 / 97 to 136" (reviewer scope, historic; FINDINGS now 147 lines) and CLAIMS-TABLE.md:112 "FINDINGS.md:21" (still the tests line, OK). REPORT.md:9 "FIX-PLAN line 1" is correct. Item cites (FIX-PLAN items 2, 3, 6, 8) match the current numbering. No other line cites found. Fix: reword FINDINGS:57 as "historic scope, at that time".

## Word search (limitation, not done, skipped, TODO, deferred, out of scope, not verified, could not)
0 hits for limitation and deferred. Hits and class:
- FINDINGS:83,111; FIX-PLAN:25; QUESTIONS:18 "F-011 / item 8 not done before the video": allowed only as needs owner or lead plus the laptop (impossible here, n8n not installed); the rows do not name the exception class or a finish date. Fix: add "needs lead (laptop re-smoke)" and the date.
- FIX-PLAN:24 F-005/F-006/F-023 "not done before the video": needs owner (lead decision Q14); allowed.
- OWNER-STEPS:82 "not done yet; audit has not seen those scripts": needs lead (scripts not in checkout); allowed, no date given.
- OWNER-STEPS:124 "not verified" HubSpot id vs vid: needs third party (real HubSpot); allowed.
- CLAIMS-TABLE:447 "NOT DONE" Q7 sentence: ITEM TO FIX (see contradiction 8).
- REPORT:89 "skipped / could not" are fixed historic defects; CLAIMS-TABLE:778,779 "skipped" are quoted test counts; flow-check/README:60 TODO is a scanned token; RUNSHEET:266,429 and CLAIMS "could not" are claim text. Not deferrals.
- "UNVERIFIED" tags throughout are the stated allowed exception (nothing ran in n8n).

## Not read
Full bodies of the very long table rows of FINDINGS, CLAIMS-TABLE (848 lines) and RUNSHEET-WORDING (464 lines) were searched by pattern, not read line by line. ORDERS.md, DECISIONS-2026-11-16.md, flow JSON, patches and the other reviews were not opened, so decision wording was compared only between the 11 files.
