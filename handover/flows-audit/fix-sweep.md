# fix-sweep (fixer log, sweep one-place-per-job), 2026-11-16

Failures first: none of the edits failed. Both scripts exit 0 after the edits. Not run: nothing in n8n, no flow. Not edited: anything that chooses between two wordings (list below). Nothing committed. Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-sweep/ (CLAIMS-TABLE.md, RUNSHEET-WORDING.md).

## Review checked before acting
Spot-checked each item against the two files. Confirmed: CT live-rows list omitted 85, 86, 87 (Count line 19 says 20 live rows: 10 + 7 + 3); RW pointers to CT sections "Decisions" and "Who decides what" as sections and "bullet After the take" do not exist as named; RW coverage line named A-004, A-010 and A-043 as not in CT, but all three are CT claim ids. Review error found: RW says A-050c, A-036b and N-1 are the same sentence; A-050c has a different first words ("When a lead ends unknown, the alert gives ..." against "The alert gives ..."), so only A-036b and N-1 got "same string as" (see needs lead 14).

## Done (mechanical)
1. Precedence sentence added under the title of both files.
2. "Tables 1 and 2 win over every row below; ..." added under the LANE A and LANE B headings of CT; Part 5b header "Superseded by the Owner steps already done section for steps 4 and 6" added.
3. CT order-of-work item 3 now reads "... 36, 39, 79, 85, 86 and 87".
4. Note cells (paste cells untouched): "Superseded by Q15: one line, no numbers (see CLAIMS-TABLE Start here item 8)." on A-050a, A-050b, A-051a, A-051b, V-41, A-023a, A-053, A-053b, A-091, N-3, and under both closing-card headings. "Same string as <first id>." on A-019b and A-081b (A-017b), A-023b and A-075 (A-023a), A-010b (A-010), N-1 (A-036b), X-6 (B-056). Checked by script: paste cells equal. Not in the list given: A-016e, A-023b not given the Q15 pointer (A-023b not named).
5. RW pointers fixed: "section Decisions, D1/D2/D3" -> "section Choices the coordinator must make before the take (D1 to D3), bullet Dn"; "section Who decides what" -> "section Start here, paragraph Who decides what"; "bullet After the take" -> "Order of work item 5 (After the take)"; "section Start here, bullet n8n runs on its own database today" -> "section Quick words, bullet ..."; "section Checks, P.." -> "section Checks (P1, P2, P4a, P4b, P4c), bullet P..". RW coverage line: A-004, A-010, A-043 removed from the not-in-CT list and from the exists-only list.
6. Definitions: pointer "(definitions: see the glossary line)" added at CT Start here UNTRACED/UNSUPPORTED line and the lane A Verdicts line (text kept); RW 0-words and Words lists got a pointer to the CT glossary line. CT line 103 (labels RELAYED-INDEPENDENT and others) left alone: it defines tags, not verdicts.
7. P2: RW 0a now says "4 real-v5 flow files" (CT row 6 and the CT Checks P2 line both say 4; verified). Left alone: RW row A-007 note and CT lane row A-007 say "all 8 flow files save nothing today": that is a fact about the built files (4 real-v5 plus 4 film-v5), not the P2 scope.
8. D1: RW 0a D1 line now says D1 is settled for this video and that A-017b, A-019b, A-051b and A-081b are CUT / for the later video only (the rows already show the CUT marking).

## Needs lead (not edited; two wordings, a decision)
1. Saved n8n runs: CT row 6 (line 185) says do not promise deletion; RW A-007 (line 149), A-010 (150), A-010b (151), A-053 (180) promise "we delete the saved runs". Decide who deletes and whether it may be said.
2. E-mail domain: CT row 2 (line 181) says example.com; RW A-005 (142) and A-084 (148) drop the domain; lane A A-084 text still says example.test.
3. Time figure: CT row 3 (182) "about 61 s"; RW A-087a (143) "about 62 s"; defaults A-087c/d (145/146) "not measured". Suggest A-087c/d until D2.
4. Scene 3 caption and card line 1: CT keeps "a lead sent twice with the same id is processed once"; RW A-016c (155), A-016e (157) say "one CRM row and one e-mail message in this recording". ORDER 017 and Q15 allow the claim line.
5. Retention: CT row 16 (195) hard statement; RW A-053 (180) hedged; RW A-010 (150) against CT A-010 UNTRACED "leave out".
6. R:41 line 6 (A-091): CT says "leases other than 45 s"; RW A-091 (182) says "other than 20, 45 and 120 s".
7. B-051 (PLAN:112): CT row 39 (218) LIVE adds text; RW B-051 (235) NO PASTE.
8. DECISION-one-store:14: CT row 36 (215) text contains "ONE database", banned by RW rule 1; RW X-5a/X-5b (286/287). Suggest X-5b.
9. "normally one" alert: CT rows 24, 27, 30, 62, 71 and the lane note use it; RW rule 7 forbids it.
10. Invalid e-mail sentence (Q7): CT row 78 (220), RW N-3 (183), RW A-057 (204) differ.
11. "measured" against "relayed": RW B-168 (265) says "one measured case: 272 s"; CT rows 16, 19, 25, 27 put "relayed" in viewer text.
12. Q13 contacts text: CT rows 32, 33, 48 (211, 212, 239) against RW B-213 (278), B-215 (280), B-215b (281), B-067 (245), B-091 (248); the sentence about the old desk harness repeats about 15 times.
13. Closing card: the RW six-line card (A-050a/b, A-051a, V-41, A-023a, A-053, A-091, N-3) is only marked superseded; Q15 says one line, no numbers. Whether to delete those rows is a lead decision.
14. A-050c (RW 174) note says it is the same sentence as A-036b and N-1 (362, 363); the strings differ. Pick one wording.
15. Not done from the review (needs a decision or is not mechanical): verdict count duplicates (CT 52, 53, 58, 105, 413-421, 814-822: "18 moved from UNTRACED" against 11 named), repeated word definitions, D2 figures copied in many rows, RW 0c second order of work against the CT order, owner steps restated, RW has no live/out column, RW line 5 stacked round histories, repeated OUT statement for rows 14/15.

## Item 6 table (CT replace-with text against RW paste text; not changed)
| CT row | id | CT line | CT text | RW line | RW text |
|---|---|---|---|---|---|
| 26 | A-098 | 205 | The cause is the 720 s claim window (statement 9) read from the v4 flow. | 212 | The cause is the 720 s claim window (statement 9): while an alert is claimed, no other check may send it for 720 s. Read from the v4 flow. |
| 34 | B-183 | 213 | marks sends it cannot be sure about so that a person looks at them; keeps its own counts | 271 | sends it cannot be sure about marked so that a person looks at them, its own counts |
| 37 | X-4 | 216 | the table shows the current state and whether the mail and the alert went out | 285 | The lead table shows the current state and whether the mail and the alert went out. |
| 40 | B-059 | 219 | stay as a record of model calls (lead keys and labels only) | 243 | The spend ledger and the stage journal stay as a record of model calls (lead keys and labels only). They do not record what happened to each lead. |
| 41 | A-059 | 232 | The demo harness did not run T8 and T15 on the v4 flows; lane3 ran one similar refuse-every-call case on film-v4 (relayed). | 205 | Our own two failure tests were not run on the version 4 flows: one where the model step refuses, fails or takes too long, and one where the CRM answers an error from the start. Another test session ran one similar CRM-error case on older flows; we have not seen its raw files. |
| 43 | B-182 | 234 | n8n receives the leads, maps the fields, keeps the one-row-per-lead claim, sends the intake mail and the alert mail. | 268 | n8n receives the leads, maps the fields, keeps the one-row-per-lead claim, sends the lead mail and the alert mail. |
| 46 | B-010 | 237 | one contact per e-mail address | 227 | One contact per e-mail address. Two different lead IDs with the same e-mail address share one contact, and the last lead ID written replaces the earlier one. The recording uses different made-up e-mail addresses for different leads. |
| 47 | B-011 | 238 | at most one mail per lead id | 228 | At most one mail per lead ID. If the send is cut off, the lead ends unknown (the mail may or may not have arrived) and an alert is sent. |
| 49 | B-037 | 240 | n8n is the only engine built; Make is only named. In the real flows HubSpot is called straight by an n8n node, with no interface of our own in front. | 237 | n8n is the only engine built; Make is only named as an alternative. In the real flows an n8n node calls HubSpot directly, with no interface of our own in front. |
| 50 | B-042 | 241 | It stops a resend or a repeat with the same id (also the same id sent to the other door). A different id for the same person is a different lead. | 239 | The n8n claim row stops a resend, or a repeat with the same lead ID (also the same lead ID sent to the other door), from starting the lead twice. A different lead ID for the same person is a different lead. |
| 52 | B-054 | 243 | K1 not yet run on v5 (V5-README.md line 17); nothing said about T1 | 242 | T1 (burst of 10) and K1 (n=5) not yet run on film-v5. |
| 58 | B-101 | 249 | lost = no final state of done, unknown or failed in time; a lead record in state review counts as lost | 253 | lost = no final state of done, unknown or failed in time; a lead in review counts as lost; a lead in done with other than 1 CRM row or other than 1 mail also counts as lost. |
| 59 | B-130 | 250 | Tested on v3 at lease 20 s (V7, numbers relayed from the coordinator's reading, raw files not seen); the hung mail server case (AF2) is not run. | 254 | Tested on version 3 at a 20 s lease (V7). The test where the mail server hangs (AF2) is not run. |
| 60 | B-145 | 251 | retry 3 in the older n8n-flows copy; 2 tries of 10 s in the shipped v5 flows | 255 | Qualify (HTTP request to the stage service, the small program that sorts each lead; 3 tries in the older n8n-flows copy; in the shipped v5 flows 2 tries with 1 s between them and a 10 s time limit per try; error output) |

## Commands and own rc
- python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md : rc=0, RESULT: PASS, total rows 157, 80 with no row [], UNTRACED 50 / 43 no row (same as before).
- python3 claims-count.py CLAIMS-TABLE.md : rc=0, ids 327 unique 327, to-do rows 87, offenders 0 (same as before).
- Diff against the backups: CT 17 changed lines, RW 78 changed lines (note cells and the lines above).
