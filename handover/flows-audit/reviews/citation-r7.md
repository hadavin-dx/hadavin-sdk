# Citation, time and date check, round 7 (EVIDENCE RUNNER output; no judging)

Run 2026-11-16 (Mon). Tool: `python3 -I` scripts c1.py (citations), c2.py (UTC to IST), c2b.py (weekday and date), c3.py (minute sums) in `/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/cite7/`. Raw output: `out-run-c1.txt`, `out-run-c2.txt`, `out-run-c2b.txt`, `out-run-c3.txt`, `out-cite-rows.txt`, `out-q-rows.txt`, `out-qpairs.txt`, `out-ist.txt`, `out-dates.txt`, `out-sums.txt`, `out-estmin.txt` in that folder. Nothing in `handover/flows-audit/` except this file was written.

## Inputs (copies; other sessions are editing the originals)

| File | sha256 of the checked copy | Copy equals original when copied | Original at the end of the run |
|---|---|---|---|
| RUNBOOK.md | 8034738e0fd58746... | yes | CHANGED (bef7226dd1bd5080...): the results below are for the copy, not for the newer text |
| TAKE-CHECKLIST.md | 0eb589ea3f4e0095... | yes | same |
| FIX-PLAN.md | facf3c46a73bc4c9... | yes | same |

Cited files (ORDERS.md 177 lines, sha256 7e55983537642dfe...; QUESTIONS.md 439 lines, sha256 706ce8361eba2b72...) were read live; other sessions may edit them.

## Failures first

### Part 1 (citations): 6 FAIL rows

- **RUNBOOK.md** `PLAN-4-NLITE-FROM-LEAD.md:106` -> handover/demo/PLAN-4-NLITE-FROM-LEAD.md:106 : MANUAL FAIL: the text names this line among those that say saved runs are deleted at clean-up; line 106 is '4. The notice (3 made-up people ... n8n killed once by hand and restarted) ...' and has no deletion wording (grep of the file for 'saved run', 'saved exec', 'delete' finds no such line; closest is line 196 'n8n execution data holds made-up names ... until cleanup')
- **TAKE-CHECKLIST.md** `ORDERS.md line 166` -> handover/flows-audit/ORDERS.md:166 : MANUAL FAIL: text says Q27 item 10 (line 156) and Q28 item 4 (line 166) both say 'with times'; 'with times' is on line 156 only; line 166 item 4 lists the owner items without times.
- **TAKE-CHECKLIST.md** `QUESTIONS.md lines 116, 322, 330 and 350` -> handover/flows-audit/QUESTIONS.md:116,322,330,350 : MANUAL FAIL for lines 322, 330, 350: the text says S9-2 and S9-3 are defined there; the token S9-2/S9-3 is on QUESTIONS.md lines 116, 339, 347 and 381 only (line 116 PASS). Stale line numbers.
- **TAKE-CHECKLIST.md** `QUESTIONS.md lines 116, 322, 330 and 350` -> handover/flows-audit/QUESTIONS.md:116,322,330,350 : MANUAL FAIL for lines 322, 330, 350: the text says S9-2 and S9-3 are defined there; the token S9-2/S9-3 is on QUESTIONS.md lines 116, 339, 347 and 381 only (line 116 PASS). Stale line numbers.
- **TAKE-CHECKLIST.md** `inputs/DECISIONS-2026-11-16.md lines 116, 178 and 322` -> handover/flows-audit/inputs/DECISIONS-2026-11-16.md:116,178,322 : FAIL: the copy in inputs/ has 13 lines (2889 bytes); lines 116, 178 and 322 do not exist. The original in the studio folder is not in this repo, so the claim cannot be checked there.
- **TAKE-CHECKLIST.md** `handover/demo/PLAN-4-NLITE-FROM-LEAD.md:106` -> handover/demo/PLAN-4-NLITE-FROM-LEAD.md:106 : MANUAL FAIL: the text names this line among those that say saved runs are deleted at clean-up; line 106 is '4. The notice (3 made-up people ... n8n killed once by hand and restarted) ...' and has no deletion wording (grep of the file for 'saved run', 'saved exec', 'delete' finds no such line; closest is line 196 'n8n execution data holds made-up names ... until cleanup')

Four more rows are `N/A`: "line 2" of `take-warns.pin` or of a file the lead creates at run time (no repo file named; cannot be checked).

### Part 2 (UTC and IST): 0 FAIL, 0 not paired. Dates: 0 FAIL.
### Part 3 (minute sums): 0 FAIL (after removing two rows my first generic parser got wrong; the hand-written versions of those two sums pass).

## Counts

| Check | Items | PASS | FAIL | Not checkable |
|---|---|---|---|---|
| file:line, "line N", "lines N to M" citations (3 documents, every occurrence) | 170 | 160 | 6 | 4 |
| Q<number> and Q<number>-<item> references (unique), heading exists and item marker seen | 70 | 70 | 0 | 0 |
| "Q<n> (line N)" pairs: that ORDERS.md line or its `##` heading mentions Q<n> | 28 | 28 | 0 | 0 |
| UTC time with an IST pair: IST = UTC + 5 h 30 min (all 145 IST times paired, none left over) | 145 | 145 | 0 | 0 |
| Weekday and date pairs (Mon 16 to Mon 23 Nov 2026, plus Wed 25 Nov) | 94 | 94 | 0 | 0 |
| Minute sums, clock arithmetic, ranges, derived figures | 90 | 90 | 0 | 0 |
| est. min column of the step table against the 17 numbers summed in section 6 (and the sub-sums 10+5+10=25, 10+5+3+8+4=30, 10+5=15, 15+10=25) | 21 | 21 | 0 | 0 |

Weekday check: every pair is right (Mon 16 Nov = 2026-11-16, Tue 17, Wed 18, Mon 23, Wed 25 Nov). Dates outside 16 to 23 Nov: only Wed 25 Nov (the post of a slipped take), also right.

## How each check was done, and its limits

1. Citation forms found: `name.ext:N`, `name.ext line(s) N`, `name.ext line N to M`, and a bare "line N" (see below). A bare "line N" with N from 100 to 177 and no file written just before it was read as ORDERS.md ("default ORDERS.md" in the table). Lines with N under 100 and no file were resolved only by 4 hand-set contexts (OWNER-STEPS item 3 line 78, "line 4 on 2026-11-16", mf_leads.sql line 5, VIDEO-RUNSHEET line 90) and otherwise reported N/A.
2. "Quote found" is a weak test: a quoted text within 45 characters of the citation (straight or curly quotes) is searched on the cited lines, "..." in a quote as a wildcard. Where no quote is near, only "line exists" is tested ("no quote nearby"). A citation without a nearby quote is NOT checked for content, except the ones I checked by hand and list here: PLAN-4:106, QUESTIONS lines, DECISIONS lines, ORDERS 166, fill_flows/README.md:240, QUEUE.md:8, ORDERS.md:20, inputs/DECISION-one-store.md 23 and 27, OWNER-STEPS-realrun-v3.md:121, AGENT-SCOPE-DO-AND-DONT.md:9, FINDINGS.md 115/117, N8N-START.md 15-27, DESIGN-A-README.md:23, mf.py:358 (holds T7b), mf_leads.sql:5 (holds lead_key), the four "killed after the mail left" hits.
3. Files named without a folder were looked up by name in the repo (copies under tools/scratch skipped); REPORT.md, VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md and PLAN-4-NLITE-FROM-LEAD.md were read as the handover/demo ones (they are the ones the text means; handover/flows-audit/REPORT.md also exists).
4. Q items: "Q27-9" or "Q27 item 9" is only checked as: a block for Q27 exists (ORDERS.md `##` block or QUESTIONS.md section) and an item marker 9 occurs in it. That does not prove the item says what the text claims.
5. Times: a UTC marker is `Z` or `UTC`; an IST time is paired with the nearest UTC time (or chain "A to B") before it; a few RUNBOOK lists have no marker on the UTC time ("1 04:00 (09:30 IST)") and were read as UTC (section header says so). 145 pairs, all IST = UTC + 5:30 (a day change such as 19:50 -> 01:20 was accepted as the next day).
6. Sums: each sum or clock calculation written in the text was matched by pattern and recomputed. A sum written in a form my patterns do not match was not recomputed (see "Could not check").

## Could not check

- Content of the roughly 144 citations that have no quote near them (existence of the line only), apart from those listed in item 2 above.
- "PLAN-4:106" (short name in FIX-PLAN.md) and "inputs/" without a line are not extracted as citations; PLAN-4-NLITE-FROM-LEAD.md:106 is (it FAILS, see above).
- Estimates themselves (3, 5, 25 min, 4 h 29 min is only as good as the 17 terms), "about 1 hour", "3.5 to 4.5 h", and round-4 historical figures (234, 171, 350, 365 min): not recomputed except 234 + 25 + 10 = 269.
- Quotes of studio-only files (the original DECISIONS-2026-11-16.md in the studio folder, bible R-numbers): not in this repo.
- Content of lines in other repos' files named only by role. Command text (`grep`, `sed`) in the documents was not run.
- Whether each claimed ORDERS item (for example "Q27 item 10") says what the text says: only the 28 line-to-Q pairs and the quotes listed were tested.
- RUNBOOK.md changed on disk after my copy (new sha above): any citation added or edited since then is not covered.

## Table: citations (cite | file:line | exists | quote found | result)

| Doc | cite | file:line | exists | quote found | result |
|---|---|---|---|---|---|
| RUNBOOK.md | ORDERS.md lines 146 to 171 | handover/flows-audit/ORDERS.md:146-171 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md lines 159 to 171 | handover/flows-audit/ORDERS.md:159-171 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 160 | handover/flows-audit/ORDERS.md:160 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 167 | handover/flows-audit/ORDERS.md:167 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 171 | handover/flows-audit/ORDERS.md:171 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md lines 105 to 171 | handover/flows-audit/ORDERS.md:105-171 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 170 | handover/flows-audit/ORDERS.md:170 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md lines 143 to 144 | handover/flows-audit/ORDERS.md:143-144 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md lines 146 to 147 | handover/flows-audit/ORDERS.md:146-147 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md lines 155 to 157 | handover/flows-audit/ORDERS.md:155-157 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md lines 159 to 171 | handover/flows-audit/ORDERS.md:159-171 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | line 2 | - | n/a | no quote nearby | N/A: no file named; the number is a line of a file made at run time (not checkable) |
| RUNBOOK.md | ORDERS.md line 171 | handover/flows-audit/ORDERS.md:171 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 167 | handover/flows-audit/ORDERS.md:167 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 160 | handover/flows-audit/ORDERS.md:160 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 171 | handover/flows-audit/ORDERS.md:171 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 167 | handover/flows-audit/ORDERS.md:167 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 132 | handover/flows-audit/ORDERS.md:132 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | FINDINGS.md lines 115 and 117 | handover/flows-audit/FINDINGS.md:115,117 | yes (file has 152 lines) | NOT on cited line(s):  (FINDINGS.md lines 115 and 117 say  | MANUAL PASS: both lines hold 'stays Major until a fix and a test' (empty quote artefact in the extractor) |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | found: fixed or downgraded with evidence | PASS |
| RUNBOOK.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | found: Step A stays removed | MANUAL PASS: nearby quote is the audit's own proposed wording or a status word, not a quote of the cited line; cited line content checked separately |
| RUNBOOK.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 147 | handover/flows-audit/ORDERS.md:147 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 135 | handover/flows-audit/ORDERS.md:135 | yes (file has 177 lines) | found: the owner's phone/clock | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | NOT on cited line(s): the owner's phone/clock | MANUAL OK (paraphrase, not a quote): line 144 item 12 says 'No phone filming and no on-screen timer' |
| RUNBOOK.md | take-warns.pin line 2 | handover/flows-audit/flow-check/take-warns.pin:2 | yes (file has 27 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | OWNER-STEPS-q16-rows.md line 78 | handover/flows-audit/OWNER-STEPS-q16-rows.md:78 | yes (file has 295 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 160 | handover/flows-audit/ORDERS.md:160 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 160 | handover/flows-audit/ORDERS.md:160 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | line 2 | - | n/a | no quote nearby | N/A: no file named; the number is a line of a file made at run time (not checkable) |
| RUNBOOK.md | line 2 | - | n/a | no quote nearby | N/A: no file named; the number is a line of a file made at run time (not checkable) |
| RUNBOOK.md | ORDERS.md lines 148 and 149 | handover/flows-audit/ORDERS.md:148,149 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | line 2 | - | n/a | no quote nearby | N/A: no file named; the number is a line of a file made at run time (not checkable) |
| RUNBOOK.md | ORDERS.md line 132 | handover/flows-audit/ORDERS.md:132 | yes (file has 177 lines) | found: never downgrade by counting | PASS |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | found: fixed or downgraded with evide | MANUAL PASS: ORDERS.md line 132 holds "stay Major until a fix and a test exist (never downgrade by counting)" exactly; extractor cut the quote at the bracket |
| RUNBOOK.md | OWNER-STEPS-q16-rows.md line 4 | handover/flows-audit/OWNER-STEPS-q16-rows.md:4 | yes (file has 295 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | mf.py line 2 | handover/demo/n8n-mainframe/mf.py:2 | yes (file has 365 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 167 | handover/flows-audit/ORDERS.md:167 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 135 | handover/flows-audit/ORDERS.md:135 | yes (file has 177 lines) | found: the owner's phone/clock | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | NOT on cited line(s): the owner's phone/clock | MANUAL OK (paraphrase, not a quote): line 144 item 12 says 'No phone filming and no on-screen timer' |
| RUNBOOK.md | ORDERS.md line 147 | handover/flows-audit/ORDERS.md:147 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | n8n-flows-v4/mf_leads.sql line 5 | handover/demo/n8n-flows-v4/mf_leads.sql:5 | yes (file has 20 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 147 | handover/flows-audit/ORDERS.md:147 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 160 | handover/flows-audit/ORDERS.md:160 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | fill_flows/README.md line 240 | handover/flows-audit/fill_flows/README.md:240 | yes (file has 299 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 132 | handover/flows-audit/ORDERS.md:132 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | QUEUE.md:8 | handover/flows-audit/QUEUE.md:8 | yes (file has 24 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md:20 | handover/flows-audit/ORDERS.md:20 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | PLAN-4-NLITE-FROM-LEAD.md:106 | handover/demo/PLAN-4-NLITE-FROM-LEAD.md:106 | yes (file has 199 lines) | no quote nearby | MANUAL FAIL: the text names this line among those that say saved runs are deleted at clean-up; line 106 is '4. The notice (3 made-up people ... n8n killed once by hand and restarted) ...' and has no deletion wording (grep of the f |
| RUNBOOK.md | ORDERS.md line 170 | handover/flows-audit/ORDERS.md:170 | yes (file has 177 lines) | found: 13:00Z = 18:30 IST | PASS |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 160 | handover/flows-audit/ORDERS.md:160 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 167 | handover/flows-audit/ORDERS.md:167 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 170 | handover/flows-audit/ORDERS.md:170 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 171 | handover/flows-audit/ORDERS.md:171 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md lines 132 and 144 | handover/flows-audit/ORDERS.md:132,144 | yes (file has 177 lines) | found: up to 3 | PASS |
| RUNBOOK.md | ORDERS.md line 132 | handover/flows-audit/ORDERS.md:132 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 135 | handover/flows-audit/ORDERS.md:135 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 135 | handover/flows-audit/ORDERS.md:135 | yes (file has 177 lines) | no quote nearby | PASS |
| RUNBOOK.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md lines 105 to 175 | handover/flows-audit/ORDERS.md:105-175 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 169 | handover/flows-audit/ORDERS.md:169 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 170 | handover/flows-audit/ORDERS.md:170 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 171 | handover/flows-audit/ORDERS.md:171 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 173 | handover/flows-audit/ORDERS.md:173 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md lines 155 to 157 | handover/flows-audit/ORDERS.md:155-157 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 159 | handover/flows-audit/ORDERS.md:159 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 160 | handover/flows-audit/ORDERS.md:160 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 167 | handover/flows-audit/ORDERS.md:167 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md lines 169 to 171 | handover/flows-audit/ORDERS.md:169-171 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md lines 105 to 175 | handover/flows-audit/ORDERS.md:105-175 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 147 | handover/flows-audit/ORDERS.md:147 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 117 | handover/flows-audit/ORDERS.md:117 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 125 | handover/flows-audit/ORDERS.md:125 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 138 | handover/flows-audit/ORDERS.md:138 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 141 | handover/flows-audit/ORDERS.md:141 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 135 | handover/flows-audit/ORDERS.md:135 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 113 | handover/flows-audit/ORDERS.md:113 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 125 | handover/flows-audit/ORDERS.md:125 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 135 | handover/flows-audit/ORDERS.md:135 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | found: lead fills in | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 110 | handover/flows-audit/ORDERS.md:110 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 147 | handover/flows-audit/ORDERS.md:147 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 171 | handover/flows-audit/ORDERS.md:171 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 147 | handover/flows-audit/ORDERS.md:147 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | found: lead fills in | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 160 | handover/flows-audit/ORDERS.md:160 | yes (file has 177 lines) | found: import and fill | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | found: in progress | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 132 | handover/flows-audit/ORDERS.md:132 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | found: fixed or downgraded with evidence | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 167 | handover/flows-audit/ORDERS.md:167 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | NOT on cited line(s): with times | MANUAL FAIL: text says Q27 item 10 (line 156) and Q28 item 4 (line 166) both say 'with times'; 'with times' is on line 156 only; line 166 item 4 lists the owner items without times. |
| TAKE-CHECKLIST.md | QUESTIONS.md lines 116, 322, 330 and 350 | handover/flows-audit/QUESTIONS.md:116,322,330,350 | yes (file has 450 lines) | no quote nearby | MANUAL FAIL for lines 322, 330, 350: the text says S9-2 and S9-3 are defined there; the token S9-2/S9-3 is on QUESTIONS.md lines 116, 339, 347 and 381 only (line 116 PASS). Stale line numbers. |
| TAKE-CHECKLIST.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 147 | handover/flows-audit/ORDERS.md:147 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 171 | handover/flows-audit/ORDERS.md:171 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 141 | handover/flows-audit/ORDERS.md:141 | yes (file has 177 lines) | found: measured at rehearsal, lead sets | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 141 | handover/flows-audit/ORDERS.md:141 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md lines 159 to 160 | handover/flows-audit/ORDERS.md:159-160 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 147 | handover/flows-audit/ORDERS.md:147 | yes (file has 177 lines) | found: one mutation batch | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | handover/demo/n8n-mainframe/mf.py line 358 | handover/demo/n8n-mainframe/mf.py:358 | yes (file has 365 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | lanes7/N7-verdicts.md line 63 | handover/flows-audit/lanes7/N7-verdicts.md:63 | yes (file has 127 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 132 | handover/flows-audit/ORDERS.md:132 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 113 | handover/flows-audit/ORDERS.md:113 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 167 | handover/flows-audit/ORDERS.md:167 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 144 | handover/flows-audit/ORDERS.md:144 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | QUESTIONS.md lines 116, 322, 330 and 350 | handover/flows-audit/QUESTIONS.md:116,322,330,350 | yes (file has 450 lines) | no quote nearby | MANUAL FAIL for lines 322, 330, 350: the text says S9-2 and S9-3 are defined there; the token S9-2/S9-3 is on QUESTIONS.md lines 116, 339, 347 and 381 only (line 116 PASS). Stale line numbers. |
| TAKE-CHECKLIST.md | inputs/DECISIONS-2026-11-16.md lines 116, 178 and 322 | handover/flows-audit/inputs/DECISIONS-2026-11-16.md:116,178,322 | NO (file has 13 lines) | no quote nearby | FAIL: the copy in inputs/ has 13 lines (2889 bytes); lines 116, 178 and 322 do not exist. The original in the studio folder is not in this repo, so the claim cannot be checked there. |
| TAKE-CHECKLIST.md | ORDERS.md line 156 | handover/flows-audit/ORDERS.md:156 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md line 166 | handover/flows-audit/ORDERS.md:166 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | handover/demo/VIDEO-RUNSHEET.md:90 | handover/demo/VIDEO-RUNSHEET.md:90 | yes (file has 90 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md:150 | handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md:150 | yes (file has 161 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | handover/demo/REPORT.md:49 | handover/demo/REPORT.md:49 | yes (file has 6012 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | REPORT.md:49 | handover/demo/REPORT.md:49 | yes (file has 6012 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | PAGE-STATEMENTS-V4.md:150 | handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md:150 | yes (file has 161 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | VIDEO-RUNSHEET.md line 90 | handover/demo/VIDEO-RUNSHEET.md:90 | yes (file has 90 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | REPORT.md:49 | handover/demo/REPORT.md:49 | yes (file has 6012 lines) | NOT on cited line(s): no line found in the whole scope | MANUAL PASS: the nearby quote is the pass line 'no line found in the whole scope', not a quote of the cited line. The cited phrase 'killed after the mail left' IS on demo/REPORT.md:49, PAGE-STATEMENTS-V4.md:150 and :153 and VIDEO- |
| TAKE-CHECKLIST.md | PAGE-STATEMENTS-V4.md:153 | handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md:153 | yes (file has 161 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | fill_flows/README.md line 240 | handover/flows-audit/fill_flows/README.md:240 | yes (file has 299 lines) | found: remove ... the saved executions | PASS |
| TAKE-CHECKLIST.md | QUEUE.md:8 | handover/flows-audit/QUEUE.md:8 | yes (file has 24 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | ORDERS.md:20 | handover/flows-audit/ORDERS.md:20 | yes (file has 177 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | handover/demo/PLAN-4-NLITE-FROM-LEAD.md:106 | handover/demo/PLAN-4-NLITE-FROM-LEAD.md:106 | yes (file has 199 lines) | no quote nearby | MANUAL FAIL: the text names this line among those that say saved runs are deleted at clean-up; line 106 is '4. The notice (3 made-up people ... n8n killed once by hand and restarted) ...' and has no deletion wording (grep of the f |
| TAKE-CHECKLIST.md | inputs/DECISION-one-store.md lines 23 and 27 | handover/flows-audit/inputs/DECISION-one-store.md:23,27 | yes (file has 28 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | inputs/OWNER-STEPS-realrun-v3.md line 121 | handover/flows-audit/inputs/OWNER-STEPS-realrun-v3.md:121 | yes (file has 193 lines) | no quote nearby | PASS |
| TAKE-CHECKLIST.md | inputs/AGENT-SCOPE-DO-AND-DONT.md line 9 | handover/flows-audit/inputs/AGENT-SCOPE-DO-AND-DONT.md:9 | yes (file has 35 lines) | no quote nearby | PASS |
| FIX-PLAN.md | ORDERS.md lines 155 to 171 | handover/flows-audit/ORDERS.md:155-171 | yes (file has 177 lines) | no quote nearby | PASS |
| FIX-PLAN.md | mf.py:45 | handover/demo/n8n-mainframe/mf.py:45 | yes (file has 365 lines) | no quote nearby | PASS |
| FIX-PLAN.md | V5-README.md line 8 | handover/demo/n8n-flows-film-v5/V5-README.md:8 | yes (file has 22 lines) | NOT on cited line(s): $REPO | MANUAL PASS: nearby quote is the audit's own proposed wording or a status word, not a quote of the cited line; cited line content checked separately |
| FIX-PLAN.md | FINDINGS.md line 65 | handover/flows-audit/FINDINGS.md:65 | yes (file has 152 lines) | no quote nearby | PASS |
| FIX-PLAN.md | fill_flows/README.md line 240 | handover/flows-audit/fill_flows/README.md:240 | yes (file has 299 lines) | found: remove ... the saved executions | PASS |
| FIX-PLAN.md | fill_flows/README.md line 240 | handover/flows-audit/fill_flows/README.md:240 | yes (file has 299 lines) | no quote nearby | PASS |
| FIX-PLAN.md | flow-check/README.md line 17 | handover/flows-audit/flow-check/README.md:17 | yes (file has 74 lines) | no quote nearby | PASS |
| FIX-PLAN.md | flow-check/README.md line 31 | handover/flows-audit/flow-check/README.md:31 | yes (file has 74 lines) | no quote nearby | PASS |
| FIX-PLAN.md | QUEUE.md:8 | handover/flows-audit/QUEUE.md:8 | yes (file has 24 lines) | no quote nearby | PASS |
| FIX-PLAN.md | ORDERS.md:20 | handover/flows-audit/ORDERS.md:20 | yes (file has 177 lines) | no quote nearby | PASS |
| FIX-PLAN.md | fill_flows/README.md line 240 | handover/flows-audit/fill_flows/README.md:240 | yes (file has 299 lines) | no quote nearby | PASS |
| FIX-PLAN.md | n8n-flows/N8N-START.md lines 15-27 | handover/demo/n8n-flows/N8N-START.md:15-27 | yes (file has 55 lines) | no quote nearby | MANUAL PASS: lines 15-27 hold EXECUTIONS_DATA_SAVE_ON_SUCCESS=none etc. |
| FIX-PLAN.md | n8n-flows/DESIGN-A-README.md line 23 | handover/demo/n8n-flows/DESIGN-A-README.md:23 | yes (file has 45 lines) | NOT on cited line(s): saved runs ON for the take only | MANUAL PASS: line 23 holds 'Execution saving off for success and error runs' (the old claim the text wants reworded) |
| FIX-PLAN.md | handover/demo/REPORT.md:49 | handover/demo/REPORT.md:49 | yes (file has 6012 lines) | NOT on cited line(s): no line found | MANUAL PASS: the nearby quote is the pass line 'no line found in the whole scope', not a quote of the cited line. The cited phrase 'killed after the mail left' IS on demo/REPORT.md:49, PAGE-STATEMENTS-V4.md:150 and :153 and VIDEO- |
| FIX-PLAN.md | handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md:150 | handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md:150 | yes (file has 161 lines) | NOT on cited line(s): no line found | MANUAL PASS: the nearby quote is the pass line 'no line found in the whole scope', not a quote of the cited line. The cited phrase 'killed after the mail left' IS on demo/REPORT.md:49, PAGE-STATEMENTS-V4.md:150 and :153 and VIDEO- |
| FIX-PLAN.md | handover/demo/VIDEO-RUNSHEET.md line 90 | handover/demo/VIDEO-RUNSHEET.md:90 | yes (file has 90 lines) | no quote nearby | PASS |

## Table: Q references (unique)

| Reference | Exists | Documents (count) | Result |
|---|---|---|---|
| Q4 | yes (1 block(s)) | TAKE-CHECKLIST.md x1; FIX-PLAN.md x2 | PASS |
| Q9 | yes (1 block(s)) | FIX-PLAN.md x1 | PASS |
| Q13 | yes (2 block(s)) | TAKE-CHECKLIST.md x1; FIX-PLAN.md x2 | PASS |
| Q14 | yes (2 block(s)) | FIX-PLAN.md x1 | PASS |
| Q16 | yes (2 block(s)) | TAKE-CHECKLIST.md x2; FIX-PLAN.md x4 | PASS |
| Q17-3 | yes (2 block(s)) | FIX-PLAN.md x3 | PASS |
| Q17-4 | yes (2 block(s)) | TAKE-CHECKLIST.md x1; FIX-PLAN.md x2 | PASS |
| Q17-5 | yes (2 block(s)) | FIX-PLAN.md x1 | PASS |
| Q18 | yes (2 block(s)) | RUNBOOK.md x1; FIX-PLAN.md x4 | PASS |
| Q19-1 | yes (2 block(s)) | TAKE-CHECKLIST.md x1; FIX-PLAN.md x5 | PASS |
| Q20-1 | yes (2 block(s)) | RUNBOOK.md x2; TAKE-CHECKLIST.md x1 | PASS |
| Q20-2 | yes (2 block(s)) | TAKE-CHECKLIST.md x1 | PASS |
| Q21 | yes (2 block(s)) | FIX-PLAN.md x7 | PASS |
| Q21-1 | yes (2 block(s)) | RUNBOOK.md x1 | PASS |
| Q21-3 | yes (2 block(s)) | RUNBOOK.md x3; TAKE-CHECKLIST.md x2; FIX-PLAN.md x1 | PASS |
| Q22 | yes (3 block(s)) | TAKE-CHECKLIST.md x1; FIX-PLAN.md x4 | PASS |
| Q22-1 | yes (3 block(s)) | RUNBOOK.md x5 | PASS |
| Q22-2 | yes (3 block(s)) | RUNBOOK.md x1 | PASS |
| Q22-3 | yes (3 block(s)) | RUNBOOK.md x1; TAKE-CHECKLIST.md x1 | PASS |
| Q22-4 | yes (3 block(s)) | FIX-PLAN.md x1 | PASS |
| Q22-5 | yes (3 block(s)) | TAKE-CHECKLIST.md x1; FIX-PLAN.md x2 | PASS |
| Q23 | yes (2 block(s)) | TAKE-CHECKLIST.md x1 | PASS |
| Q24-1 | yes (2 block(s)) | RUNBOOK.md x2; TAKE-CHECKLIST.md x1; FIX-PLAN.md x1 | PASS |
| Q24-2 | yes (2 block(s)) | TAKE-CHECKLIST.md x1; FIX-PLAN.md x1 | PASS |
| Q24-3 | yes (2 block(s)) | TAKE-CHECKLIST.md x1 | PASS |
| Q24-4 | yes (2 block(s)) | FIX-PLAN.md x3 | PASS |
| Q24-5 | yes (2 block(s)) | FIX-PLAN.md x1 | PASS |
| Q25 | yes (2 block(s)) | RUNBOOK.md x1; TAKE-CHECKLIST.md x1 | PASS |
| Q25-1 | yes (2 block(s)) | RUNBOOK.md x7; TAKE-CHECKLIST.md x4; FIX-PLAN.md x4 | PASS |
| Q25-2 | yes (2 block(s)) | RUNBOOK.md x3; TAKE-CHECKLIST.md x2; FIX-PLAN.md x4 | PASS |
| Q25-3 | yes (2 block(s)) | RUNBOOK.md x3; TAKE-CHECKLIST.md x1; FIX-PLAN.md x8 | PASS |
| Q25-4 | yes (2 block(s)) | RUNBOOK.md x1; FIX-PLAN.md x1 | PASS |
| Q25-5 | yes (2 block(s)) | RUNBOOK.md x1; TAKE-CHECKLIST.md x2 | PASS |
| Q25-6 | yes (2 block(s)) | RUNBOOK.md x1 | PASS |
| Q25-7 | yes (2 block(s)) | RUNBOOK.md x2 | PASS |
| Q25-10 | yes (2 block(s)) | RUNBOOK.md x1; FIX-PLAN.md x2 | PASS |
| Q25-11 | yes (2 block(s)) | TAKE-CHECKLIST.md x2 | PASS |
| Q25-12 | yes (2 block(s)) | RUNBOOK.md x2; TAKE-CHECKLIST.md x1; FIX-PLAN.md x2 | PASS |
| Q25-13 | yes (2 block(s)) | RUNBOOK.md x1; FIX-PLAN.md x1 | PASS |
| Q25-14 | yes (2 block(s)) | RUNBOOK.md x1; FIX-PLAN.md x1 | PASS |
| Q26 | yes (2 block(s)) | RUNBOOK.md x7; TAKE-CHECKLIST.md x7; FIX-PLAN.md x10 | PASS |
| Q26-1 | yes (2 block(s)) | RUNBOOK.md x9; TAKE-CHECKLIST.md x6; FIX-PLAN.md x2 | PASS |
| Q26-3 | yes (2 block(s)) | TAKE-CHECKLIST.md x3; FIX-PLAN.md x3 | PASS |
| Q26-4 | yes (2 block(s)) | FIX-PLAN.md x1 | PASS |
| Q27 | yes (2 block(s)) | RUNBOOK.md x4; TAKE-CHECKLIST.md x9; FIX-PLAN.md x6 | PASS |
| Q27-1 | yes (2 block(s)) | RUNBOOK.md x10; TAKE-CHECKLIST.md x14; FIX-PLAN.md x6 | PASS |
| Q27-2 | yes (2 block(s)) | RUNBOOK.md x7; TAKE-CHECKLIST.md x2 | PASS |
| Q27-3 | yes (2 block(s)) | RUNBOOK.md x7; TAKE-CHECKLIST.md x1; FIX-PLAN.md x1 | PASS |
| Q27-4 | yes (2 block(s)) | RUNBOOK.md x4; TAKE-CHECKLIST.md x3; FIX-PLAN.md x1 | PASS |
| Q27-5 | yes (2 block(s)) | RUNBOOK.md x2; TAKE-CHECKLIST.md x3; FIX-PLAN.md x1 | PASS |
| Q27-6 | yes (2 block(s)) | RUNBOOK.md x14; TAKE-CHECKLIST.md x3; FIX-PLAN.md x4 | PASS |
| Q27-7 | yes (2 block(s)) | RUNBOOK.md x5; TAKE-CHECKLIST.md x1; FIX-PLAN.md x4 | PASS |
| Q27-8 | yes (2 block(s)) | RUNBOOK.md x5; TAKE-CHECKLIST.md x2; FIX-PLAN.md x2 | PASS |
| Q27-9 | yes (2 block(s)) | RUNBOOK.md x14; TAKE-CHECKLIST.md x10; FIX-PLAN.md x10 | PASS |
| Q27-10 | yes (2 block(s)) | RUNBOOK.md x4; TAKE-CHECKLIST.md x5 | PASS |
| Q28 | yes (2 block(s)) | RUNBOOK.md x3; TAKE-CHECKLIST.md x1; FIX-PLAN.md x1 | PASS |
| Q28-1 | yes (2 block(s)) | RUNBOOK.md x4; TAKE-CHECKLIST.md x1; FIX-PLAN.md x1 | PASS |
| Q28-2 | yes (2 block(s)) | RUNBOOK.md x9; TAKE-CHECKLIST.md x3; FIX-PLAN.md x3 | PASS |
| Q28-3 | yes (2 block(s)) | RUNBOOK.md x5; TAKE-CHECKLIST.md x2; FIX-PLAN.md x1 | PASS |
| Q28-4 | yes (2 block(s)) | RUNBOOK.md x3; TAKE-CHECKLIST.md x4 | PASS |
| Q28-5 | yes (2 block(s)) | RUNBOOK.md x4; TAKE-CHECKLIST.md x1; FIX-PLAN.md x1 | PASS |
| Q29 | yes (2 block(s)) | RUNBOOK.md x3; TAKE-CHECKLIST.md x1 | PASS |
| Q29-1 | yes (2 block(s)) | RUNBOOK.md x4; TAKE-CHECKLIST.md x2; FIX-PLAN.md x3 | PASS |
| Q29-2 | yes (2 block(s)) | RUNBOOK.md x5; TAKE-CHECKLIST.md x1; FIX-PLAN.md x2 | PASS |
| Q29-3 | yes (2 block(s)) | RUNBOOK.md x5; TAKE-CHECKLIST.md x4; FIX-PLAN.md x4 | PASS |
| Q29-4 | yes (2 block(s)) | RUNBOOK.md x5; TAKE-CHECKLIST.md x4; FIX-PLAN.md x3 | PASS |
| Q30 | yes (2 block(s)) | RUNBOOK.md x4; TAKE-CHECKLIST.md x6; FIX-PLAN.md x4 | PASS |
| Q30-1 | yes (2 block(s)) | RUNBOOK.md x6; TAKE-CHECKLIST.md x3; FIX-PLAN.md x5 | PASS |
| Q30-2 | yes (2 block(s)) | RUNBOOK.md x6; TAKE-CHECKLIST.md x5; FIX-PLAN.md x5 | PASS |
| Q30-3 | yes (2 block(s)) | RUNBOOK.md x4; TAKE-CHECKLIST.md x3; FIX-PLAN.md x2 | PASS |

## Table: UTC with IST (all 145 pairs; full list in out-ist.txt)

All PASS. Sample of the first 12:

| UTC ~ IST as written | check | result |
|---|---|---|
| 09:30 UTC ~ 15:00 IST | UTC 09:30 + 5:30 = 15:00; written 15:00 | PASS |
| 14:00 UTC ~ 19:30 IST | UTC 14:00 + 5:30 = 19:30; written 19:30 | PASS |
| 07:30 UTC ~ 13:00 IST | UTC 07:30 + 5:30 = 13:00; written 13:00 | PASS |
| 06:00 UTC ~ 11:30 IST | UTC 06:00 + 5:30 = 11:30; written 11:30 | PASS |
| 15:00 UTC ~ 20:30 IST | UTC 15:00 + 5:30 = 20:30; written 20:30 | PASS |
| 04:00 UTC ~ 09:30 IST | UTC 04:00 + 5:30 = 09:30; written 09:30 | PASS |
| 08:00 UTC ~ 13:30 IST | UTC 08:00 + 5:30 = 13:30; written 13:30 | PASS |
| 06:51 UTC ~ 12:21 IST | UTC 06:51 + 5:30 = 12:21; written 12:21 | PASS |
| 06:21 UTC ~ 11:51 IST | UTC 06:21 + 5:30 = 11:51; written 11:51 | PASS |
| 03:31 UTC ~ 09:01 IST | UTC 03:31 + 5:30 = 09:01; written 09:01 | PASS |
| 01:30 UTC ~ 07:00 IST | UTC 01:30 + 5:30 = 07:00; written 07:00 | PASS |
| 06:00 UTC ~ 11:30 IST | UTC 06:00 + 5:30 = 11:30; written 11:30 | PASS |

## Table: weekday and date (94 mentions; distinct values)

| As written | Real date | Count | Result |
|---|---|---|---|
| 2026-11-16 (Mon) | 2026-11-16 is a Mon (written Mon) | 1 | PASS |
| Mon 16 Nov | 2026-11-16 is a Mon (written Mon) | 6 | PASS |
| Mon 23 Nov | 2026-11-23 is a Mon (written Mon) | 28 | PASS |
| Monday 23 Nov | 2026-11-23 is a Mon (written Mon) | 1 | PASS |
| Tue 17 Nov | 2026-11-17 is a Tue (written Tue) | 30 | PASS |
| Tuesday 17 Nov | 2026-11-17 is a Tue (written Tue) | 1 | PASS |
| Wed 18 Nov | 2026-11-18 is a Wed (written Wed) | 17 | PASS |
| Wed 25 Nov | 2026-11-25 is a Wed (written Wed) [outside 16-23 Nov] | 9 | PASS |
| Wednesday 18 Nov | 2026-11-18 is a Wed (written Wed) | 1 | PASS |

## Table: minute sums and derived figures (all 90; out-sums.txt)

| Doc | kind | text | recomputed | written | result |
|---|---|---|---|---|---|
| RUNBOOK.md | sum | 20 + 15 + 30 = 65 min | 20 + 15 + 30 = 65 | 65 | PASS |
| RUNBOOK.md | sum | 3 + 5 + 5 + 3 + 10 + 25 + 3 + 20 + 15 + 25 + 30 + 15 + 20 + 15 + 30 + 30 + 15 = 269 min = 4 h 29 min | 3 + 5 + 5 + 3 + 10 + 25 + 3 + 20 + 15 + 25 + 30 + 15 + 20 + 15 + 30 + 30 + 15 = 269 | 269 | PASS |
| RUNBOOK.md | min->h | 3 + 5 + 5 + 3 + 10 + 25 + 3 + 20 + 15 + 25 + 30 + 15 + 20 + 15 + 30 + 30 + 15 = 269 min = 4 h 29 min | 269 min = 4 h 29 min | 4 h 29 min | PASS |
| RUNBOOK.md | sum | 5 + 3 + 25 + 3 + 30 + 15 + 20 + 15 + 30 = 146 min = 2 h 26 min | 5 + 3 + 25 + 3 + 30 + 15 + 20 + 15 + 30 = 146 | 146 | PASS |
| RUNBOOK.md | min->h | 5 + 3 + 25 + 3 + 30 + 15 + 20 + 15 + 30 = 146 min = 2 h 26 min | 146 min = 2 h 26 min | 2 h 26 min | PASS |
| RUNBOOK.md | sum | 269 + 90 + 60 + 30 + 10 = 459 min | 269 + 90 + 60 + 30 + 10 = 459 | 459 | PASS |
| RUNBOOK.md | sum | 10 + 45 + 15 + 45 = 115 min | 10 + 45 + 15 + 45 = 115 | 115 | PASS |
| RUNBOOK.md | sum | 25 + 60 + 20 + 120 = 225 min = 3 h 45 min | 25 + 60 + 20 + 120 = 225 | 225 | PASS |
| RUNBOOK.md | min->h | 25 + 60 + 20 + 120 = 225 min = 3 h 45 min | 225 min = 3 h 45 min | 3 h 45 min | PASS |
| RUNBOOK.md | sum | (take 60 + watch 20 + edit 120 + spare 10) = 15:00 minus 210 min = 11:30 | 60 + 20 + 120 + 10 = 210 | 210 | PASS |
| RUNBOOK.md | clock | (take 60 + watch 20 + edit 120 + spare 10) = 15:00 minus 210 min = 11:30 | 15:00 - 210 min = 11:30 | 11:30 | PASS |
| RUNBOOK.md | clock | 08:00 minus 4 h 29 min = 03:31 | 08:00 minus 269 min = 03:31 | 03:31 | PASS |
| RUNBOOK.md | clock | 14:00 minus 429 min = 06:51 | 14:00 minus 429 min = 06:51 | 06:51 | PASS |
| RUNBOOK.md | clock | 14:00 minus 575 min = 04:25 | 14:00 minus 575 min = 04:25 | 04:25 | PASS |
| RUNBOOK.md | clock | 15:00 minus 210 min = 11:30 | 15:00 minus 210 min = 11:30 | 11:30 | PASS |
| RUNBOOK.md | clock | 07:00 + 5 h 55 min = 12:55 | 07:00 + 355 min = 12:55 | 12:55 | PASS |
| RUNBOOK.md | clock | 18:29 minus 5 h 55 min = 12:34 | 18:29 minus 355 min = 12:34 | 12:34 | PASS |
| RUNBOOK.md | clock | 12:55 + 2 h 26 min = 15:21 | 12:55 + 146 min = 15:21 | 15:21 | PASS |
| RUNBOOK.md | clock | 18:29 minus 8 h 21 min = 10:08 | 18:29 minus 501 min = 10:08 | 10:08 | PASS |
| RUNBOOK.md | clock | 18:29 minus 10 h 24 min = 08:05 | 18:29 minus 624 min = 08:05 | 08:05 | PASS |
| RUNBOOK.md | diff | 271 minus 60 minus 30 minus 10 = 171 min | 271 - 60 - 30 - 10 = 171 | 171 | PASS |
| RUNBOOK.md | diff | 270 minus 100 = 170 min | 270 - 100 = 170 | 170 | PASS |
| RUNBOOK.md | clock | 14:00 minus 575 min = 04:25 UTC (09:55 IST), or minus 605 min = 03:55 | 14:00 - 575 = 04:25 | 04:25 | PASS |
| RUNBOOK.md | clock | 14:00 minus 575 min = 04:25 UTC (09:55 IST), or minus 605 min = 03:55 | 14:00 - 605 = 03:55 | 03:55 | PASS |
| RUNBOOK.md | clock | 07:00 + 5 h 55 min = 12:55 UTC (18:25 IST), margin 5 h 34 min to 18:29 | 07:00 + 5 h 55 min = 12:55 | 12:55 | PASS |
| RUNBOOK.md | margin | 07:00 + 5 h 55 min = 12:55 UTC (18:25 IST), margin 5 h 34 min to 18:29 | 18:29 - 12:55 = 334 min | 5 h 34 min = 334 | PASS |
| RUNBOOK.md | clock | 18:29 minus 5 h 55 min = 12:34 UTC | 18:29 - 5 h 55 min = 12:34 | 12:34 | PASS |
| RUNBOOK.md | clock | 18:29 minus 8 h 21 min = 10:08 UTC | 18:29 - 8 h 21 min = 10:08 | 10:08 | PASS |
| RUNBOOK.md | clock | 18:29 minus 10 h 24 min = 08:05 UTC | 18:29 - 10 h 24 min = 08:05 | 08:05 | PASS |
| RUNBOOK.md | clock | 12:55 + 2 h 26 min = 15:21 UTC (20:51 IST), still before 18:29 (margin 3 h 08 min) | 12:55 + 2 h 26 = 15:21 | 15:21 | PASS |
| RUNBOOK.md | margin | 12:55 + 2 h 26 min = 15:21 UTC (20:51 IST), still before 18:29 (margin 3 h 08 min) | 18:29 - 15:21 = 188 min | 3 h 08 min | PASS |
| RUNBOOK.md | sum | (4 h 29 min + 5 h 55 min + 2 h 26 min = 12 h 50 min) | = 770 min | 770 min | PASS |
| RUNBOOK.md | clock | it takes 4 h 29 min, ending 11:29 UTC (16:59 IST), then 5 h 55 min: the take ends 17:24 UTC (22:54 IST), margin 1 h 05 min; one repeat gives | 07:00 + 4 h 29 min = 11:29 | 11:29 | PASS |
| RUNBOOK.md | clock | it takes 4 h 29 min, ending 11:29 UTC (16:59 IST), then 5 h 55 min: the take ends 17:24 UTC (22:54 IST), margin 1 h 05 min; one repeat gives | 11:29 + 5 h 55 min = 17:24 | 17:24 | PASS |
| RUNBOOK.md | margin | it takes 4 h 29 min, ending 11:29 UTC (16:59 IST), then 5 h 55 min: the take ends 17:24 UTC (22:54 IST), margin 1 h 05 min; one repeat gives | 18:29 - 17:24 = 65 min | 1 h 05 min | PASS |
| RUNBOOK.md | clock | it takes 4 h 29 min, ending 11:29 UTC (16:59 IST), then 5 h 55 min: the take ends 17:24 UTC (22:54 IST), margin 1 h 05 min; one repeat gives | 17:24 + 2 h 26 min = 19:50 | 19:50 | PASS |
| RUNBOOK.md | span | 09:29 UTC (14:59 IST) Tue, if step 1 starts at 04:00 UTC) to Wed 05:45 UTC = 20 h 16 min | 09:29 Tue to Wed 05:45 = 1216 min | 20 h 16 min | PASS |
| RUNBOOK.md | clock | 08:00 minus 4 h 29 min = 03:31 UTC | 08:00 - 4 h 29 min = 03:31 | 03:31 | PASS |
| RUNBOOK.md | range | 07:40 to 08:25 (45) | 07:40 to 08:25 = 45 min | 45 | PASS |
| RUNBOOK.md | range | 08:25 to 08:40 (15) | 08:25 to 08:40 = 15 min | 15 | PASS |
| RUNBOOK.md | range | 08:40 to 09:25 (45) | 08:40 to 09:25 = 45 min | 45 | PASS |
| RUNBOOK.md | range | 07:00 to 07:30 (12:30 to 13:00 IST), 30 min | 30 min | 30 | PASS |
| RUNBOOK.md | range | 09:25 to 09:50 (14:55 to 15:20 IST), 25 min | 25 min | 25 | PASS |
| RUNBOOK.md | range | 10:00 to 11:00 (15:30 to 16:30 IST), 60 min | 60 min | 60 | PASS |
| RUNBOOK.md | range | 11:00 to 11:20 (16:30 to 16:50 IST), 20 min | 20 min | 20 | PASS |
| RUNBOOK.md | range | 11:20 to 13:20 (16:50 to 18:50 IST), 120 min | 120 min | 120 | PASS |
| RUNBOOK.md | sum | practice 1 h + Row 4 0.5 h + rehearsal 2 h + take 1 h = 4.5 h | 1 + 0.5 + 2 + 1 = 4.5 | 4.5 | PASS |
| RUNBOOK.md | sum | short re-smoke 60 + practice 60 + Row 4 30 + rehearsal block... | 60+60+30+115+25+5+60 = 355 | 355 | PASS |
| RUNBOOK.md | min->h | short re-smoke 60 + practice 6 | 355 min = 5 h 55 min | 5 h 55 min | PASS |
| RUNBOOK.md | sum | positive control 10 + rehearsal 1 45 + step 22 15 + rehearsal 2 45; with an applied change the block is 125 | 10+45+15+45 = 115; +10 for applied change = 125 | 125 stated | PASS |
| RUNBOOK.md | sum | the event 269 + the re-smoke 60 + step 14 (f) 60 +... | 269+60+60+30+10 = 429 | 429 | PASS |
| RUNBOOK.md | sum | 269 + 90 + 60 + 30 + 10 = 459 | = 459 | 459 | PASS |
| RUNBOOK.md | clock | 14:00 minus 575 min = 04:25 UTC (09:55 IST), or minus 605 min = 03:55 | 429+146 = 575; 459+146 = 605; 14:00-575 = 04:25; 14:00-605 = 03:55 | 04:25 / 03:55 | PASS |
| RUNBOOK.md | labelled sum | start command 15 + SELECT-only login and its negative test 2... | 15+20+15+20+45+35 = 150 | 150 | PASS |
| RUNBOOK.md | labelled sum | T19 to T21 runner 90 + take program commands for practice, r... | 90+20+15+30+10+15 = 180 | 180 | PASS |
| RUNBOOK.md | step start | step 1 start | 04:00 + durations before it = 04:00 | 04:00 | PASS |
| RUNBOOK.md | step start | step 2 start | 04:00 + durations before it = 04:03 | 04:03 | PASS |
| RUNBOOK.md | step start | step 3 start | 04:00 + durations before it = 04:08 | 04:08 | PASS |
| RUNBOOK.md | step start | step 4 start | 04:00 + durations before it = 04:13 | 04:13 | PASS |
| RUNBOOK.md | step start | step 4a start | 04:00 + durations before it = 04:16 | 04:16 | PASS |
| RUNBOOK.md | step start | step 4b start | 04:00 + durations before it = 04:26 | 04:26 | PASS |
| RUNBOOK.md | step start | step 5 start | 04:00 + durations before it = 04:51 | 04:51 | PASS |
| RUNBOOK.md | step start | step 6 start | 04:00 + durations before it = 04:54 | 04:54 | PASS |
| RUNBOOK.md | step start | step 7 start | 04:00 + durations before it = 05:14 | 05:14 | PASS |
| RUNBOOK.md | step start | step 8 start | 04:00 + durations before it = 05:29 | 05:29 | PASS |
| RUNBOOK.md | step start | step 9 start | 04:00 + durations before it = 05:54 | 05:54 | PASS |
| RUNBOOK.md | step start | step 10 start | 04:00 + durations before it = 06:24 | 06:24 | PASS |
| RUNBOOK.md | step start | step 11 start | 04:00 + durations before it = 06:39 | 06:39 | PASS |
| RUNBOOK.md | step start | step 12 start | 04:00 + durations before it = 06:59 | 06:59 | PASS |
| RUNBOOK.md | step start | step 13 start | 04:00 + durations before it = 07:14 | 07:14 | PASS |
| RUNBOOK.md | step start | step 14 start | 04:00 + durations before it = 07:44 | 07:44 | PASS |
| RUNBOOK.md | step start | step 15 start | 04:00 + durations before it = 08:14 | 08:14 | PASS |
| RUNBOOK.md | step start | event end | 04:00 + 269 = 08:29 | 08:29 | PASS |
| RUNBOOK.md | derived figure | 08:29 + 60 min = 09:29 | 569 | 569 | PASS |
| RUNBOOK.md | derived figure | 14:00 - 09:29 = 271 | 271 | 271 | PASS |
| RUNBOOK.md | derived figure | 14:00 - 09:00 = 300 | 300 | 300 | PASS |
| RUNBOOK.md | derived figure | 14:00 - 09:30 = 270 | 270 | 270 | PASS |
| RUNBOOK.md | derived figure | 08:29 - 08:00 = 29 min | 29 | 29 | PASS |
| RUNBOOK.md | derived figure | 08:00 + 60 = 09:00 (re-smoke if event ends 08:00) | 540 | 540 | PASS |
| RUNBOOK.md | derived figure | 08:00 + 146 min = 10:26 | 626 | 626 | PASS |
| RUNBOOK.md | derived figure | 10:26 + 60 = 11:26 | 686 | 686 | PASS |
| RUNBOOK.md | derived figure | 10:26 + 90 = 11:56 | 716 | 716 | PASS |
| RUNBOOK.md | derived figure | 14:00 - 11:26 = 154 | 154 | 154 | PASS |
| RUNBOOK.md | derived figure | 14:00 - 11:56 = 124 | 124 | 124 | PASS |
| RUNBOOK.md | derived figure | 09:00 steps 9..13 again = 30+15+20+15+30 = 110 | 110 | 110 | PASS |
| RUNBOOK.md | derived figure | 234 + 25 + 10 = 269 (round 4 -> round 5) | 269 | 269 | PASS |
| RUNBOOK.md | derived figure | 14:00 - 459 = 06:21 | 381 | 381 | PASS |
| RUNBOOK.md | derived figure | 04:00 - 150 min = 01:30 | 90 | 90 | PASS |
| RUNBOOK.md | derived figure | 07:00 + 146 min = 09:26 | 566 | 566 | PASS |
| RUNBOOK.md | derived figure | 14:00 - 575 = 04:25 (429+146) | 265 | 265 | PASS |
