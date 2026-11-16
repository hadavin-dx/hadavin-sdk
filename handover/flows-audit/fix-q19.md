# fix-q19 (fixer log, lead answer Q19), 2026-11-16

Failures first: none of the edits failed. Not run: nothing in n8n, no flow. Not decided by me (listed below): the other needs-lead items. Nothing committed. Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-q19/ (CLAIMS-TABLE.md, RUNSHEET-WORDING.md).
Things I chose where the answer left room (check them): (a) the card sentence uses the words "with the same id" (the lead's Q19 sentence; ANSWER-Q15-lead.md writes the shorter "a lead sent twice is processed once"); (b) the same sentence is also the scene 3 caption, because CLAIMS-TABLE Start here item 1 already keeps that caption; (c) I added ONE row, RW A-016f, to carry it, so the RW paste-row count is now 158 (section 1: 39); (d) the card now has one line, so the old lines 2 to 6 rows stay as audit trail and are listed as "not on the card"; (e) the hedged retention sentence is notes only, so A-010 is no longer spoken in scene 1.
Alert wording check: mf-recovery.json (real-v5): AlertClaim picks leads in state unknown or failed with alert_sent=false; AlertMark has onError continueRegularOutput, so a failed follow-up update lets the alert come again. So rows now say only "an alert e-mail is sent when a lead is given up on; it can come again if the follow-up table update fails". How many alerts per lead: not measured.

## Changed rows
- Q19-1 (no deletion promised): CT lane A-007 (replace text), CT lane A-010, RW A-007, A-010, A-010b, A-053 (paste/notes), RW step 0c.3 (read the run list, tell the lead; no deletion), step 0c.11 (do not delete, do not promise). CT row 6 note already agreed; left.
- Q19-2: new RW A-016f (card line and scene 3 caption: "A lead sent twice with the same id is processed once."); RW A-016c and A-016e kept, marked "NOT USED by decision Q19-2"; steps 7 and 10, rule 2, card intro and card table, Q-F row rewritten; CT Start here item 10 added.
- Q19-3: "normally one" removed from CT rows 23, 24, 27, 30, 62, 71, the CT line before lane A (rows A-039 sentence), lane rows A-021, A-057, A-076, B-077, B-150, B-173; RW rule 7 reworded, RW A-057 note, RW A-021 note.
- Q19-4: CT row 78 words copied unchanged into RW N-3 and A-057 and into CT row 24 and lane A-057 (identical text).
- Q19-5: one sentence "n8n may keep a copy of each submitted form, including the made-up name and e-mail address, until its own pruning removes it; how long is not measured." in CT row 16, CT lane A-010 and A-053, RW A-010, A-010b, A-053; RW A-053 and A-053b marked notes only, off the card; the other-AI-session sentence in CT row 16 removed.

## fix-sweep.md needs-lead items settled by these answers
1 saved runs, 4 scene 3 caption, 5 retention, 9 normally one, 10 invalid e-mail sentence, 13 closing card (one line; old rows kept as audit trail, not deleted).

## Still needs lead (not decided here)
2. E-mail domain: CT row 2 says example.com; RW A-005 and A-084 drop the domain; lane A A-084 text says example.test.
3. Time figure: CT row 3 "about 61 s"; RW A-087a "about 62 s"; defaults A-087c and A-087d "not measured".
6. A-091 (R:41 line 6): CT says "leases other than 45 s"; RW says "other than 20, 45 and 120 s". (No longer on the card, but the two texts still differ.)
7. B-051: CT row 39 LIVE adds text; RW B-051 NO PASTE.
8. One store: CT row 36 text contains "ONE database", banned by RW rule 1; RW X-5a and X-5b.
11. Measured against relayed: RW B-168 "one measured case: 272 s"; CT rows 16, 19, 25, 27 put "relayed" in viewer text.
12. Q13 contacts text: CT rows 32, 33, 48 against RW B-213, B-215, B-215b, B-067, B-091.
14. A-050c against A-036b and N-1: the strings differ; pick one wording.
15. Verdict-count duplicates, repeated definitions, D2 figures copied in many rows, and the other non-mechanical items of fix-sweep.md item 15.
(Both texts for each are in fix-sweep.md items and its item 6 table.)

## Commands and own rc
- python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md : rc=0, RESULT: PASS (total rows 158 = 157 + A-016f; 80 with no row []; UNTRACED 50 / 43 no row).
- python3 claims-count.py CLAIMS-TABLE.md : rc=0, ids 327 unique 327, to-do rows 87, offenders 0.
Count change: RW paste rows 157 -> 158 (stated line updated). Claims 327 and to-do rows 87 unchanged.
