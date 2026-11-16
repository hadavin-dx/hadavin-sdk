# Independent evidence for REPORT-c6q.md (EVIDENCE RUNNER: records, does not judge)
Run 2026-11-16 (clock after 16:34 UTC = 22:04 IST). Target sha256 before and after: e9b5a06b3b83602cc3c7289363f976722e1601f41b50e4c06c4296e3e793f686 = the builder claim, unchanged (sha-before.txt, sha-after.txt). No file outside this folder was written; __pycache__ deleted (count 0).

## FAILURES AND DEVIATIONS (first)
1. SOURCE COPY IS NOT IN THE REPOSITORY. The builder checks 89 of 94 rows (9 of the 10 target files: VIDEO-RUNSHEET.md, the four mf-*.json flows, N8N-START.md, PAGE-STATEMENTS-V4.md, build_mainframe.py, mf.py) against a copy at /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover/ (builder verify-c6q.py constant T). Only inputs/DECISION-one-store.md (row 90, 91 and others on it) exists in the repo. Against the repo, 89 rows are unreadable (run-repo-source.txt). Against the scratchpad copy all 94 old texts occur exactly once on the stated line. I did not verify that the copy equals the studio's real files; the report should say which copy it used and that the repo does not hold them.
2. BUILDER verify-c6q.py NOW EXITS 1 (92 checks, 1 failed): "no owner sheet changed after the stated check time". OWNER-SHEET-v29-A.md and -B.md were written 16:34:17 UTC (22:04:17 IST) and v29-SOURCE.md 16:34:27 UTC, after the report's check time 16:32:07 UTC = 22:02:07 IST. So the report's statement "only a template of v29 exists" was true at its check time and is stale now (L-SHEET row of section 3 and the box). Consequence: the builder's own control copy "V0-control-unchanged" in neg_controls_c6q.py now exits 1 (marked WRONG); 54 of 55 controls OK, 1 wrong, for that reason only (bcopy run, builder-neg-run.txt).
3. MY CHECKER, 1 FAIL (a format note, not a wrong time): the box line 50 has the example "2026-11-16T16:40:00Z" with the IST "(22:10:00)" about 90 characters later, not within 40. The pair is correct (16:40 + 5:30 = 22:10); builder's own check allowed 60 characters. No other UTC time lacks IST.
4. Builder's verifier does not check weekdays, the lease sentence on caption row 21, a capitalised "The lease question", a single wrong "42 apply" or "91 rows" statement, a stale "58 s" in the box: 8 of my 32 mutations passed it (below).
5. I tuned my own checker after the first mutation run (it missed 6 of the 32 at first: wave-1 count in one place, "58 s" in the box, a capitalised label, row-count in section 0, the 60.1 to 61.9 range, a card total). The final 32/32 is therefore a fit to my own mutations, not a blind result. Builder's 24/32 is a blind run of its script as written.

## PASSES (indep_check.py, run-builder-source.txt: 41 PASS, 1 FAIL = item 3)
- 94 rows parsed; ids exactly 1..94, no duplicate.
- Old text once on its stated line, all 94 (scratchpad copy; see item 1).
- Counts 49 ready / 42 default / 3 check (rows 23, 58, 59); wave 1 = 91; every statement of those numbers in the box and section 0 agrees (the 42 includes row 23, which is "after check C-4; on the default of L-SAVE").
- Card: four spoken lines of 11, 35, 22, 22 words = 90 words = 36.0 s, budget 40 s, total about 190 s; box prints the four lines verbatim; no "58 s" in any new text or the box.
- Lease x card-length table (6 rows) recomputed from the quoted lines: none a/b 90/74 words, answer 1 115/87, answer 2 130/114; seconds 36.0, 29.6, 46.0, 34.8, 52.0, 45.6; budgets 40, 30, 50, 35, 55, 50; totals 190, 180, 200, 185, 205, 200. Equal to the report. Sentences are 25 and 40 words.
- 40 "UTC = IST" pairs all exactly +5:30; every other UTC/Z time outside old-text quotes has an IST (except item 3).
- 11 weekday+date pairs for 2026 correct (Wed 18 Nov, Mon 23 Nov, Wed 25 Nov and others).
- No report label (C-n, row N, KEY:digits, reading 1/2, this report, the lease question, L-xxx, Qn, ORDERS.md, REPORT-c6) in any new text or viewer cell of all 94 rows.
- Lease sentences ("within 45 seconds", "called the lease") appear in no new text of rows 11, 13, 14, 21 or any other row; absent from the spoken lines. (Card line 4 does say "other lease settings"; the report itself notes this.)
- Row 90 new text ends with database `n8n`, old text ends with SEPARATE database `n8n`.
- Defined words: 22+ uppercase labels of the box word list each first appear where defined; nothing before the list uses n8n, lease, contact, take, rehearsal, owner, alert, gate; no label used inside an earlier definition. (Lower-case words such as "send" and "take" are weaker: not checked beyond this.)
- 60.1 to 61.9 exact in all occurrences outside old-text cells; no banned strings (count 0 of 10 listed); no secret-shaped string (0).
- Builder verify-c6q.py on REPORT-c6q.md: 91 PASS, 1 FAIL (item 2). neg_controls: 55 copies, 54 OK, 1 wrong (item 2); REPORT-c6p given to it fails 32 checks as intended.

## MUTATIONS (mutation-results.txt; 32 planted + 1 unchanged control, each run through my checker and the builder's verify)
Mine: 32 of 32 caught (after tuning, item 5); control: no new failure. Builder verify: 24 of 32 caught.
Caught by both (24): 48 ready; row 11 card "58 s"; "row 13", "RS:41", "reading 1", "this report" label leaks; wrong IST on 18:04 and 15:00; lease sentence in row 13; row 90 ending "own state"; a removed word on card line 2; table seconds 46.0->45.0; table budget 55->50; row 5 old text altered; row 5 line +1; row 50 deleted; duplicate id; row 1 status changed; term used before defined; sk- shaped string; UTC time without IST; "Of the 93 rows"; "60.1 to 61.1"; total 100 words.
Missed by the builder's verify, caught by mine (8): M02 "41 apply on the default"; M03 "90 rows" for wave 1; M04 "58 s" in the box; M10 capitalised "The lease question"; M14 lease sentence on the scene 3 caption (row 21); M16 "Tue 23 Nov"; M17 "Thu 18 Nov 2026"; M32 "(within 45 seconds)" in row 14.
Not run in sample: mutations of rows' JSON line numbers on flow files, whole-file (not line) uniqueness of old texts.

## NOT RUN
- No import into n8n, no live checks C-3/C-4/C-5/C-8/C-9, no stopwatch measurement of the card (seconds are words/150*60 only).
- Not verified: that the scratchpad source copy equals the studio's files; that the 94 new texts are correct in meaning; section 8 coverage lines; cites (ORD:, MF: line numbers) beyond what the builder's own check reads.
- Folder scan of c6-skip-audit (546 files): banned strings 0 files, secret-shaped 0 files, non-example e-mail-shaped 0 files (folder-scan.txt; counts only).

Files here: indep_check.py, mutate.py, mutation-results.txt, run-builder-source.txt, run-repo-source.txt, builder-verify-on-c6q.txt, builder-neg-run.txt, bcopy/ (builder scripts copied; neg_controls D/E paths pointed at this folder; outputs in bcopy/neg), folder-scan.txt, sha-before.txt, sha-after.txt.
