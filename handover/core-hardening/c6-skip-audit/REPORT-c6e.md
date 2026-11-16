# C6e: video audit findings after the lead's decisions of 2026-11-16 (final fix pass; read-only audit, nothing run, no flow or program file edited)

Built from REPORT-c6d.md with every finding of review-c6d-naive.md fixed, plus the advice of the zoom-out lane (cross-read/ZOOM-OUT-not-checked.md). No further review round goes to this report; only blockers found by use would reopen it.

Base folder used below: H = /home/user/hadavin-sdk/handover. C = H/core-hardening/c6-skip-audit (this folder). Where I could find a file under H with Glob/find, its path is given. Where I could not, the text says NOT FOUND (see section 9).

Every status below is my reading of the texts, not new evidence. Nothing was run. Line cites into files that are NOT FOUND are carried over from earlier reports and not re-verified.

## 1. Words used in this report (read first)

People and records. One word, one meaning:

| word | meaning here |
|---|---|
| lead | the studio lead: the decision maker who answers the questions in this report and made the decisions of 2026-11-16 (H/core-hardening/inputs/DECISIONS-2026-11-16.md). Always "the lead", never a sales contact. |
| owner | the studio owner: types y, the challenge and end in the take, deletes leftover made-up contacts by hand after the take (decision 2), revokes keys at clean-up, and may veto any decision. Not the same role as the lead. |
| builder | an agent or person who edits a named text or test file. |
| lead record | one made-up sales contact (a row with a lead id) that the flows process. Written "lead record" everywhere. "The lead record ends unknown" means that row, not the studio lead. |
| lead id | the identifier of one lead record. The narrow claim is about the same lead id arriving twice. |

Status words (only these are used in the findings table):

| status | meaning |
|---|---|
| STILL OPEN | Work remains. It changes what is filmed or said, or the checks before filming. |
| CONDITIONAL | STILL OPEN only if a stated condition holds (for example: scene 4 keeps the kill cases, or a number is captioned). If the condition is false, the row becomes NOT IN TAKE or LATER VIDEO. The row names the condition. |
| DECISION ANSWERED / FILES NOT UPDATED | The lead has already decided (decision number given). A text or plan file still says the old thing. The task is the file edit. Do not filter this out when looking for work. |
| DECISION ANSWERED / NOTHING LEFT | The lead decided and no file edit remains that I know of. |
| NOT IN TAKE (author reading) | In my reading the item is not on the path filmed in scenes 1 to 4. No decision says so; the lead may overrule. Housekeeping. |
| LATER VIDEO | Belongs only to the scenes cut by decision 1 (scenes 5 to 11, stand-in flows, film-v4 and film-v5 data). Housekeeping. One archive line is given; no further review round goes to these rows. |
| DUPLICATE | The row repeats another row; the row it is folded into is named. No separate task. |
| UNKNOWN | The files I can read do not say how the item relates to scenes 1 to 4. The row names the file that decides it and who must read it. |

Other terms:
- "The take" = the one recorded filming run. "Gate" = do not start the take before it is done.
- real-v5 = the n8n flows in folder n8n-flows-real-v5, which talk to the real mail and CRM services; the only flow set in the one video.
- film-v4 / film-v5 = flow sets that talk to stand-in (fake, controlled by us) services. Their scenes (5 to 11) are a possible later video.
- lane3 = the separate test session and git branch (origin/demo/lane3) that ran the 45-second-lease crash tests. Raw data copy: C/raw-lane3/results.jsonl and C/raw-lane3/RESULTS.md. The harness's own LANE number (0, 1, 3) is a different thing: which test queue ran. Whether lane3 is a person or an agent: not stated in any file I read.
- lease = how long a claimed lead record stays reserved before the recovery sweep may take it again. Older tests used 20 s, lane3 used 45 s, one older series 120 s (unit: seconds).
- alert = the one mail the system sends to a named address when it cannot tell what happened to a lead record. Alert timing is not measured.
- "unknown" end state = the lead record's final state when the program could not tell whether the contact and mail happened; a person decides.

## 2. What the video shows (from the decisions file only)

Source: H/core-hardening/inputs/DECISIONS-2026-11-16.md, decisions 1, 2, 6, 7, 8, 9, 12. I did not find the run sheet (VIDEO-RUNSHEET.md: NOT FOUND), so I cannot describe the scenes from the scene list.

What the decisions say:
- One video, real-v5 only: scenes 1 to 4 of the run sheet. Scenes 5 to 11 (stand-in flows) are not in it.
- Narrow claim: **the same lead id sent twice is processed once.**
- The take runs on made-up data against real mail and CRM accounts of ours, never deletes contacts (decision 2), uses its own free port (decision 6; the rehearsal uses 5690), and the lead imports and activates the flows with scripts\n8n_api.py (decision 7).
- The counts proof screen is a rehearsal screenshot or the Postgres node preview, not a live table screen (decision 9).
- Scene 1 shows n8n's execution list (see row N2). Scene 4 contains the kill-case wording and captions this report discusses (rows M1, F-007a to F-007g).

What I do not know (so nothing below should be read as describing scenes 1 to 4):
- What each of scenes 1, 2, 3 and 4 shows, in order.
- Whether scene 4 still shows the kill cases (a crash of n8n during processing) and whether the closing card stays.
- What "sent twice" means in the take: two sends at once, a second send after the first finished, after the lease ran out, or after a crash. Where the lead id comes from (the sender, or made by n8n) is also unchecked.
- Whether a same-id-twice case with a pass rule exists in the loopback re-smoke. I searched H/core-hardening/inputs/plan-wp6-resmoke-v5.md for "twice" and "same id": 0 hits. I did not read the plan in full, so this is "not found by phrase search", not "absent". The plan does contain kill cases (section 11) and the owner steps (H/core-hardening/steps-edits/OWNER-STEPS-realrun-v9.md) send person A twice, B ten times at once and C once while n8n is stopped and started, but I have not checked that these are a same-id-twice proof on real-v5.
- Measured evidence for the narrow claim on real-v5: none found. All crash numbers in this report come from film-v4 stand-in flows (lane3), not from real-v5.

## 3. Priority list (read this first)

Questions for the lead (answer these before anything else):

- **Q1. Closing card and scene 4.** Where does the closing card sit, and does scene 4 still show the kill cases? Deciding file: VIDEO-RUNSHEET.md (NOT FOUND in this tree; the lead reads the scene list and :41). Rows that wait on the answer: N5, c6b items 4, 5 and 6, review-design 4, review-design 6, F-007a to F-007g.
- **Q2 (new). Kill cases on real-v5.** If scene 4 keeps the kill cases: do they run on the real-v5 flows (real mail and CRM), and is the stand-in result "the mail did not arrive in the K3B case" also true there? All kill numbers I have are from film-v4 stand-in flows (lane3). Real-v5 has a real mail path, so it may not hold. Until the lead or a real-v5 run answers, the K3B and K3 sentences in rows F-007a to F-007d may only be used with the label "measured on stand-in flows, film-v4".
- **Q3. Re-smoke owner.** See section 4.

Gate (blocks filming):
1. Q1 and Q2 answered. Owner: lead.
2. N2: apply the saving settings to the 8 built flows (count from earlier reports, not re-counted) and see one run in n8n's execution list. Needs a running n8n; not tested here. Owner: lead (decision 7).
3. M1: remove the caption number "60.1 to 61.9 s" from the run sheet and PAGE-STATEMENTS-V4.md. Owner: builder.
4. F-007a to F-007g: scene 4 kill-case wording, only if scene 4 keeps the kill cases. See section 6.
5. N1: check that exactly one flow set (n8n-flows-real-v5) is active and no stale folder is imported. Owner: lead.
6. F-011 wording: use the interim sentence of section 4 until the loopback re-smoke has passed; never "one database". Owner: lead.
7. M2: re-scope privacy test T7b before it is used with saved runs ON. Owner: builder.
8. D2: decision 2 stale text in the owner steps ("the key needs permission to create and to delete contacts") must be fixed before the take, because the owner reads those steps before the take. Not housekeeping. Owner: builder.
9. D10: confirm which OWNER-STEPS version is current and archive v3. Owner: lead (confirm), builder (archive note).

Housekeeping (does not change what is filmed or said):
10. F-006 line 4 edit; F-003 patch read; DECISION-one-store line 14 edit (the wording itself is gate item 6; the file edit is housekeeping once the interim sentence is used).
11. Ledger entries (N3a and others).
12. NOT IN TAKE and LATER VIDEO rows (F-022, F-023, F-025, N6, F-020). No more rounds go there.

## 4. The "one database" wording and the re-smoke (F-011 answer)

- **True now:** per row F-011, n8n starts on its own SQLite file (a small file database); the Postgres move is not done. So "one Postgres server with two databases (n8n's own and the take's)" (decision 10) is the wording AFTER the change, not true now.
- **Interim sentence that is true now (use until the re-smoke has passed):** "n8n keeps its own records in its own database file. Our claim table for lead records is a separate Postgres database. That is two stores. We are moving n8n's records onto the same Postgres server; until that is checked we do not call it one database." Where the claim table sits is from H/core-hardening/inputs/DECISION-one-store.md (a decision text), not checked on a running system.
- **After the re-smoke passes:** "one Postgres server with two databases: n8n's own and the take's."
- **Who runs the loopback re-smoke:** the lead. Decision 12 names the lead for the first laptop rehearsal "right after the loopback re-smoke passes"; I read this as the lead running both. The decision does not literally name who runs the re-smoke, so the lead should confirm. Target: tonight or tomorrow morning IST; times go in the handoff.
- **What it covers:** H/core-hardening/inputs/plan-wp6-resmoke-v5.md (558 lines; I read only its first lines and phrase hits): real n8n 2.46.6 on loopback, made-up data, US$0, saved runs ON, a separate database, three database roles (S1b). Whether the role tests (T-ROLES) run before the video: decision 3 parks the roles proposal and says read-only group L is not run; I could not tell if T-ROLES is the same thing. Lead: say which role tests run before the video.
- **Edit:** H/core-hardening/inputs/DECISION-one-store.md line 14 says "ONE database for everything we own". Change it to the decision 10 wording after the re-smoke, or to the interim sentence now. Owner: builder.

## 5. Findings table

Owner column: lead = needs a decision or a file I cannot reach; builder = a text or test edit in a named file. I edited none of these files. NOT FOUND means Glob/find under H returned nothing.

| id and finding | status | reason | task, owner, target file (folder) |
|---|---|---|---|
| M1: run sheet :90 caption "60.1 to 61.9 s" contradicts the sheet's own lines :22 (45 s lease unmeasured) and :85 (no number until lane3 numbers land) | DECISION ANSWERED / FILES NOT UPDATED (decision 1) | Decision 1 cuts the number. The sheet and page still carry it as far as the carried-over cites show. | Builder: delete the number in VIDEO-RUNSHEET.md :90 and PAGE-STATEMENTS-V4.md (page :149 area). Keep "about a minute, in the test" under section 7. Both files NOT FOUND. |
| F-006: run sheet line 4 says real CRM in "scenes 1 to 5" | DECISION ANSWERED / FILES NOT UPDATED (decision 1) | C/REPORT.md (found) says the line still reads "scenes 1 to 5"; scenes 5 to 11 remain in the sheet. | Builder: VIDEO-RUNSHEET.md line 4 to "scenes 1 to 4"; mark scenes 5 to 11 "later video". Question at :56 and :78 answered by decision 1. File NOT FOUND. |
| F-003 patch (its only hunk is run sheet line 4) | STILL OPEN | Never applied; may conflict with decision 1. Patch NOT FOUND (patches in H/core-hardening/paste-check/ are plan patches, not opened). | Lead: name the patch path. Builder: read it, then apply, edit or drop it. I make no claim that it is wrong. |
| N1: two flow sets cannot both be active (same webhook paths mf-form, mf-hook) | STILL OPEN (one check left before the take) | Decision 1 removes the need to switch sets. Only the check remains. | Lead, before the take: confirm only n8n-flows-real-v5 is imported and active; none of n8n-flows, -v3, -v4, -real, -real-v3, -real-v4, -film, -film-v3, -film-v4. Import with scripts\n8n_api.py (decision 7; the take's copy NOT FOUND, test copies under H/core/evidence/r7u-chain/). Not tested. The claim about how the two sets differ was a hand parse with no saved output (review-design m1, C/review-design.md): unverified, no longer needed. |
| N2: empty execution list in scene 1 until saving is applied | STILL OPEN (gate) | Scene 1 is filmed; F-008 says the 8 built flows save nothing; N8N-START.md:15-27 still says all four saving settings are required (NOT FOUND). | Lead: apply the saving settings, then see one run in the list. Needs a running n8n; not tested. |
| F-011: n8n starts on its own SQLite file; the "one database" claim | STILL OPEN | Decision 10 fixes the wording. Postgres move and role tests not done. Decisions 8 and 12 put the loopback re-smoke first. The DB_* names exist only under handover/flows-audit (NOT FOUND). | See section 4. Plan: H/core-hardening/inputs/plan-wp6-resmoke-v5.md (earlier cite "plan v5:550" not re-read). Lead: say which role tests run before the video. |
| M2: saved runs ON invalidates test T7b | STILL OPEN | mf.py:276-278 sets saving to none and T7b passes only then (name and e-mail 0 hits); the re-smoke plan sets saving ON (plan lines 38, 73). mf.py NOT FOUND. | Builder: new pass rule. Key and mail password: 0 hits in every place searched (n8n database, n8n logs, stage journal, stage logs, spend ledger). Name and e-mail: may appear in n8n's database only; 0 hits in stage journal, stage logs, spend ledger. Where T7b is written: not found; builder to find it. Not run. |
| F-007a: scene 4 says K3B was "killed after the mail left" (run sheet :90) | CONDITIONAL (condition: scene 4 keeps the kill cases; otherwise NOT IN TAKE). Also needs Q2. See section 6. | In all 5 kept lane3 runs of the case the file calls K3, final mail_to_intake was 0 (C/evidence-lane3-recompute.md); RESULTS.md Part 4 (C/raw-lane3/RESULTS.md) says that case is the demo's K3B, "mail not delivered"; mf.py:158 cited as agreeing (NOT FOUND). Data are film-v4 stand-in, not real-v5. | Builder: VIDEO-RUNSHEET.md :90, K3B sentence: "stopped while the mail was being sent: in the test (stand-in mail service) the mail did not arrive; the lead record ends unknown with one alert". Never "killed after the mail left". |
| F-007b: same false wording on the page (PAGE-STATEMENTS-V4.md :150, :153) | CONDITIONAL (same condition; see section 6) | Same basis. | Builder: PAGE-STATEMENTS-V4.md :153 and :150, same K3B sentence. NOT FOUND. |
| F-007c: run sheet :24 defines lane3 K3 as "after the CRM write" | CONDITIONAL (same condition; see section 6) | RESULTS.md:97 (via C/REPORT-c6b.md) says lane3 K3 = the demo's K3B (killed when the mail connection opens). | Builder: VIDEO-RUNSHEET.md :24, follow section 6. |
| F-007d: K3 sentence | CONDITIONAL (same condition; see section 6) | 3 kept runs of the case the file calls K6 (the demo's K3): mail_to_intake 1, alert 1, total_mails 2. Whether any mail was sent before the kill in K3B: not in the data. | Builder: K3 sentence: "stopped after the mail was stored, before the table was updated: mail arrived once, the lead record ends unknown, one alert". |
| F-007e: "a real mail server might have taken it" | CONDITIONAL (same condition; see section 6) | A guess, not a measurement. | Builder: keep only with the label "a guess"; do not attribute "may or may not have gone" to the 18 lane3 runs (review-design M3). On real-v5 it may not apply (Q2). |
| F-007f: other run-sheet lines with K3 (:32 :36 :38 :39 :41 :47 :54) | CONDITIONAL (same condition; see section 6) | Nine lines contain K3 in total (:24 :32 :36 :38 :39 :41 :47 :54 :90). Not read. | Builder: read each line and follow section 6. |
| F-007g: one naming table | STILL OPEN (see section 6) | Three sources disagree (page :150/:153, run sheet :24/:90, mf.py:153-158). | Lead: pick the file that holds the table. Builder: write it from section 6. |
| N4: duplicate of F-007 | DUPLICATE (folded into F-007a to F-007g) | Same finding found a second time by another reviewer. | None separate. |
| N3a: raw e-mail passed to Q.qualify (stage_server.py:54) | STILL OPEN as a ledger entry; relation to the take UNKNOWN | Nit for the take (made-up example.test addresses), Major for any client build. Whether qualify runs in scenes 1 to 4: VIDEO-RUNSHEET.md and PLAN-4-NLITE-FROM-LEAD.md:64-80 (both NOT FOUND). stage_server.py NOT FOUND. | Lead: write one row in H/ledger.md (found; a second ledger is H/reviews/ledger.md) as a client-build blocker. |
| N3b: does the e-mail reach the model | UNKNOWN | PLAN-4:80 says the model input is the lead id plus the normalised made-up e-mail (a statement, not a check). qualify_stage.py NOT FOUND. | Lead: name who reads qualify_stage.py in the desk repo, or say it is out of scope for the video. |
| N5: narrow claim vs closing card "80 kills, 0 doubled, 0 lost" and "13 min late" (run sheet :41) | UNKNOWN (closing card position, Q1); if the card sits after scene 4 the unmeasured parts are LATER VIDEO material | Decision 1 cuts scene 5 and the caption number, not the closing card. Phrase search in the lane3 kill folder: "80 kills" 0 files; "0 doubled" 2 files, "0 lost" 3 files; hits in COMPARE-demo.md:5 and RESULTS.md:100 are the demo column (n = 20). The third "0 lost" hit, PLAN-V3-ALERT.md:24, NOT read (file NOT FOUND), so I do not claim "0 lost" occurs only in the demo column. No readable raw (laptop files, v3 flows, 20-second lease). | Lead: answer Q1. If the card stays, builder: cut "80 kills" or label it "older test, v3 flows, 20-second lease, not re-checked"; read PLAN-V3-ALERT.md:24 in full. |
| c6b item 1: voided runs VOID-fl45k3b and VOID-fl45k6c | DECISION ANSWERED / NOTHING LEFT (decision 1); becomes CONDITIONAL if an "18 kill runs" caption comes back | Cause UNPROVEN. Lane3 calls voided runs "my slips" (RESULTS.md:2) without a cause. VOID-fl45k3b never reached an end state; its 338.7 s is the 330 s wait limit plus restart, not a measured recovery. VOID-fl45k6c failed with fakes_not_up. A reviewer inferred a second queue emptied the table (harness.py:261; lane3 harness NOT FOUND); overlap alone does not show it. | Lead, if the number returns: ask lane3 to confirm the cause, or re-run K3 at lease 45 s. |
| c6b item 2 / review-design m3: "18 kill runs" hides n = 3 for the demo's K3 | CONDITIONAL (condition: a run count is captioned) | Counts per case 5, 5, 5, 3 runs (lane3 file names). | Builder: give the split if captioned. |
| c6b item 3: run sheet :24 wrong K3 definition | DUPLICATE (folded into F-007c) | Same finding. | None separate. |
| c6b item 4: "80 kills, 0 doubled, 0 lost" has no readable raw; "0 lost" counts unknown as not lost (mf.py:83); 40 of 80 end unknown | UNKNOWN (closing card position, Q1) | See N5. | See N5. |
| c6b item 5: small differences (raw min 52.8 s vs caption 52.9 s; closing card line 3 n = 2, from n8n up) | UNKNOWN (closing card position; whether the 52.9 to 54.9 s caption stays in scene 4, Q1) | Decision 1 cuts only "60.1 to 61.9 s". VIDEO-RUNSHEET.md NOT FOUND. | If they stay, builder: 52.9 to 52.8; line 3 to "n=2 (K1), 6 runs between 144.2 and 144.4 s, measured from n8n coming back up", or drop. |
| c6b item 6: 45 s lease supported only indirectly (flows imported from a local folder not in the repo; byte-identity not proven) | CONDITIONAL (condition: scene 4 says "45-second lease" aloud) | Label 873a908a-film-v4-lease45 is a real commit; its mf-form.json and mf-recovery.json contain interval 45 seconds. Unexplained: at lease 120 s time from n8n up is about lease + 24 s, at 45 s about lease + 8 s. | Lead: accept the indirect support or drop the words. |
| c6b item 7: reviewer's point that the 45 s lease is only indirectly supported (agree) | DUPLICATE (folded into c6b item 6) | c6d named "c6b item 7" without a row. C/REPORT-c6b.md (read for this pass) has six numbered findings; its review round's point 7 is the same as item 6. This row removes the dangling reference. | None separate. Rows that waited on item 7 now wait on item 6. |
| review-design 3: three queues overlapped (run_all.progress lines 101-127); "lane" means two things | CONDITIONAL (condition: lane3 timings are captioned) | Overlap may have stretched restart times. run_all.progress NOT FOUND. | Builder: say so if captioned; use "lane3" only for the session. |
| review-design 4: closing card "nothing lost, nothing doubled" claims too much | UNKNOWN (closing card position, Q1); STILL OPEN if the card stays after scene 4 | crm_rows 1 and stage_calls 1 in all 18 kept rows, so "not shown to be doubled by these two fields". crm_upsert_events 2 in 13 of 18, stage_requests 2 in all 18 (not explained); crm_rows is only the final state. "Nothing lost" fails for the mail in K3B (mail_to_intake 0, 5 of 5). | If the card stays, builder: "no lead record lost or duplicated by the two final counts (crm_rows 1, stage_calls 1 in all 18); in 5 runs the mail did not arrive and a person was alerted", plus the upsert count, or drop "nothing lost". |
| review-design 5: the 60.1 to 61.9 s range is one test program's repeatable timing | DECISION ANSWERED / NOTHING LEFT (decision 1) | Number cut. | Section 7 applies. |
| review-design 6: alert timing not measured | CONDITIONAL (condition: scene 4 keeps the kill cases) | See section 7. | Builder: check scene 4 wording against section 7. |
| review-design M3 warning: do not attribute "may or may not have gone" to the 18 lane3 runs | DUPLICATE (folded into F-007e) | Same warning. | None separate. |
| F-020: stage journal has two names (stage.journal in the take, stage-journal.jsonl in the harness) | STILL OPEN for the take name; LATER VIDEO for the harness name | stage_server.py is the older prototype; the take uses a rebuild (PLAN-4:64-80), neither in this tree. Archive note: stage-journal.jsonl belongs to the film-v4 harness; no more rounds. | Builder: use one name, stage.journal, in take texts only; do not move the journal before the video. |
| F-022: desk doors' 502 path never reaches the error workflow | NOT IN TAKE (author reading) | C/REPORT.md: doors retired under F-019 (not read). The finding's own fix text is wrong ("Reply 2xx" is also the success reply). mf-form real-v5 :238-295 only sets n8n_error:false, so take flows do not repeat it. | Retire the doors; no patch. Lead confirms the doors are not imported (part of N1). |
| F-023: table-screen READMEs disagree about "NOT run" (v1 README; v2 :3, :48, :51; DOUBTFUL-SCENE.md:13) | NOT IN TAKE (author reading) | The run sheet forbids saying it works. Decision 9 replaces the live table screen by a screenshot or node preview. Files NOT FOUND. | Lead: ask the laptop agent first; then one dated run; then texts agree. |
| F-025: v1-superseded recovery re-claims forever (30 s sweep, 20 s lease; no attempts cap, no alert) | LATER VIDEO | Kept "for the compare only". Archive note: archive the folder per CUT-LIST.md (NOT FOUND); no more rounds. | Builder: archive; update C/REPORT.md:33, :526-528 and DESIGN-A-README.md:3 (NOT FOUND). |
| N6: door node name "Reply error" | NOT IN TAKE (author reading) | Same doors as F-022. | None for the video. |
| D2 (decision 2): the take never deletes contacts; the owner deletes leftovers by hand | STILL OPEN (gate item 8; before the take, not housekeeping) | Stale text found: H/core-hardening/steps-edits/OWNER-STEPS-realrun-v8.md line 157 ("The key needs permission to create and to delete contacts") and H/core-hardening/QUESTIONS.md item 1 (asks whether to give the HubSpot app the delete right). OWNER-STEPS-realrun-v9.md (same folder) has 0 phrase hits for delete right/permission and step F.3 already has the owner deleting by hand, so v9 looks fixed; I did not check which version the owner will read. | Builder: remove the "key needs delete permission" requirement from every version still in use (v8 :157 at least) and from run card row 14 (scope names), or confirm v9 is the only version. Lead: close QUESTIONS.md item 1 as answered. "F-01" in the lead's note has no entry in the c6 files; may be A-01 or C-01 (decision 4); if another finding: UNKNOWN, deciding file flows-audit FINDINGS.md (NOT FOUND; H/evidence/silent-exit/FINDINGS.md is a different document). |
| D10 (decision 10): OWNER-STEPS v3 archived, never deleted; v4 and later replace it | DECISION ANSWERED / FILES NOT UPDATED | OWNER-STEPS v3 NOT FOUND under H. Found in H/core-hardening/steps-edits/: realrun v4 to v9, OWNER-STEPS-v4-difflist.md, v6-OPEN-FOR-LEAD.md. Whether v3 was archived elsewhere: not known. Which version is current (v8/v9 or v6): the lead must say. | Lead: name the current version. Builder: write one archive line in the handoff (v3 archived, not deleted, with its location). Never delete. |
| K3B mail before the kill | UNKNOWN | The data file has no field; only RESULTS.md Part 4 says "mail not delivered". Lane3 harness NOT FOUND. | Lead: ask lane3 or read the harness. |
| N7: "13 min late" line and lane3's later fix (alert at 60 s, 3 of 3, lane3 REPORT.md:18, not adopted in the demo flows) | UNKNOWN (closing card position, Q1) | The card says an alert can be 13 minutes late (n = 2, older tests); lane3 later measured a faster alert never put into the demo flows, so the card may state an old problem as current. | Lead: keep or drop "13 min late" (c6b question 5). |
| N8: "HB194" name | STILL OPEN (wording) | HB194 appears only in commit 2595b8c3's message; best match RESULTS.md Part 3 lines 83-92 (inference). Block not read. A caption or page should not use a name nobody can look up. | Builder: cite "demo3/kill/RESULTS.md, commit 2595b8c3" (file C/raw-lane3/RESULTS.md) (c6b question 4). |
| N9: housekeeping items without row ids in c6d | STILL OPEN (housekeeping) | Now: F-006, F-003 patch read, DECISION-one-store line 14 (section 4). | As in those rows. |
| Z1 (zoom-out lane): core SDK patches (A-01 deferred, C-01 extras cut, 54 mutants, C7/C8 lanes tied to them, T-ROLES parked) | DECISION ANSWERED / NOTHING LEFT (decisions 3, 4) | Core SDK is not on the take path; only G5 wording (text) is in scope. Not in the c6 files; named because the zoom-out lane flagged them. | No more rounds. |

LATER VIDEO archive note (one line for all LATER VIDEO rows: F-020 harness name, F-025, any lane3 number captioned only in scenes 5 to 11): the film-v4 and film-v5 stand-in scenes are a possible later video; their notes stay in C/ and H/core-hardening/ unchanged, no further review round is spent on them, and they are reopened only when that video is planned. Rows kept above for scene 4 stay only because scene 4 may still use lane3 numbers (Q1, Q2).

## 6. Naming table (cases)

| demo name (page, run sheet, mf.py) | lane3 file name | what happens | basis |
|---|---|---|---|
| K3B | K3 | stopped while the mail connection opens; mail not delivered in the test (stand-in mail service) | RESULTS.md Part 4 and :97 (C/raw-lane3/RESULTS.md); mf.py:153-158 carried over (NOT FOUND) |
| K3 | K6 | stopped after the mail was stored, before the table update; mail arrived once | same; mf.py:159-164 carried over |
| K1, K2 | K1, K2 | same names; meaning not defined in any file I read (observed end state done, mail 1, alert 0, in 5 runs each) | C/evidence-lane3-recompute.md |

All rows are film-v4 stand-in results. Whether the same cases give the same results on real-v5 is open (Q2).

## 7. Rules that apply to every scene-4 caption
- A time may be said only as "about a minute, in the test", with no decimals, until the lead accepts a labelled number. No caption says "alert within a minute": alert timing is not measured (counts taken after a 20-second wait, harness.py:341, per the c6b review; harness NOT FOUND).
- "Nothing lost" is not claimed for the mail in the K3B case (section 8).
- Every lane3 number carries the label "stand-in flows, film-v4, 45-second lease, one machine, made-up data" until a real-v5 run exists (Q2).
- The claim is "the same lead id sent twice is processed once"; no caption claims more.

## 8. Recomputed numbers (basis: evidence runner's recompute of results.jsonl, 128 rows, C/evidence-lane3-recompute.md, not re-checked by me; (H) = hand recompute by the c6b reviewer)

| quantity | value | field name |
|---|---|---|
| lease-45 rows (rows with a 45 s lease) | 23 = 18 kept + 2 voided + 3 error-case rows | flows, point, label |
| kept runs per case, lane3 file names | K1 5, K2 5, K3 5, K6 3 runs | point |
| kill to end state | min 60.1, max 61.9, median 60.85 seconds | kill_to_final_s |
| kill_to_final_s vs restart_s + recovery_s | largest difference 0.1 s | restart_s, recovery_s |
| restart (H) | 6.6 to 8.8 s | restart_s |
| recovery (H) | 52.8 to 54.9 s | recovery_s |
| CRM upsert calls seen | 2 calls in 13 of 18 runs (K2 5, K3 5, K6 3); 1 call in the 5 K1 runs | crm_upsert_events |
| final CRM rows | 1 row in all 18 runs | crm_rows |
| model-stage calls | 1 call in all 18 runs | counts.stage_calls |
| stage requests | 2 requests in all 18 runs (not explained) | stage_requests |
| intake mails at the end (mails at the intake address) | K1 1, K2 1, K3 0 (5 of 5 runs), K6 1 (3 of 3 runs; total_mails 2, my reading: intake mail plus alert mail, not confirmed) | counts.mail_to_intake |
| end states (H) | K1, K2 done (10 of 18 runs); K3, K6 unknown with 1 alert (8 of 18 runs) | states |
| voided runs | VOID-fl45k3b: 17:09:59Z to 17:16:35Z, never terminal, 338.7 s, no error text; VOID-fl45k6c: error fakes_not_up | label |
| runs attempted at lease 45 (H) | 20 runs (K1 5, K2 5, K3 6, K6 4) | |

Not found: "80 kills" (0 files in the lane3 kill folder); any mail field before the kill. File-name to demo-name mapping and "mail not delivered" come from RESULTS.md Part 4 text only; there is no "K3B" label in results.jsonl.

## 9. Failures, uncertain items, not checked
1. Closing card position and scene 4 content are not stated in any file I could find; many rows depend on them (Q1, Q2).
2. Nothing re-checked against raw files; nothing run. C/raw-lane3/ not opened in this pass. Real-v5 flow JSON not read; no real-v5 same-id-twice result found (section 2).
3. NOT IN TAKE for F-022, F-023, N6 is my reading, not a decision.
4. NOT FOUND under H by Glob/find: VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md, flows-audit FINDINGS.md (only H/evidence/silent-exit/FINDINGS.md exists, a different document), folder flows-audit and its EXCEPTIONS.md, CUT-LIST.md, COMPARE-demo.md, DESIGN-A-README.md, PLAN-V3-ALERT.md (H/studio-notes/plan-v3.md exists; relation not checked), N8N-START.md, PLAN-4-NLITE-FROM-LEAD.md, DOUBTFUL-SCENE.md, V7-NUMBERS-lead-read.md, stage_server.py, qualify_stage.py, mf.py, lane3 harness.py (two other harness.py under H/core/evidence/realrun-v6/standing/), run_all.progress, the F-003 patch, project plan v5 (only plan-wp6-resmoke-v5.md found), OWNER-STEPS v3, the take's scripts\n8n_api.py (test copies under H/core/evidence/r7u-chain/). Cites into these files are carried over, unverified.
5. Found and used: H/core-hardening/inputs/ (DECISIONS-2026-11-16.md, DECISION-one-store.md, plan-wp6-resmoke-v5.md, FACTS-ALREADY-DONE.md; a plan copy also in paste-check/scratch-v5/a/inputs/), H/core-hardening/steps-edits/ (OWNER-STEPS realrun v4 to v9, v6-OPEN-FOR-LEAD.md, EDITS.md), H/core-hardening/QUESTIONS.md, H/ledger.md and H/reviews/ledger.md, C/raw-lane3/ (results.jsonl, RESULTS.md, recompute files), C/REPORT.md, REPORT-c6b.md, REPORT-c6c.md, review-design.md, review-codebase.md, resolve-r1.md, H/core-hardening/cross-read/ZOOM-OUT-not-checked.md. c6d said DECISIONS was "in the folder above this one"; it is in core-hardening/inputs/.
6. The bible is not on disk as a text I read, so R460 could not be checked.
7. T-ROLES against decision 3 unresolved (section 4).
8. The zoom-out lane raised gaps no c6 review covers and I did not work on (they need new checks, not text edits): claim rows that may persist between rehearsal and take; real HubSpot search delay not exercised (loopback stub); real model call path not run before the take, credit window ends 23 Nov 23:59 IST; proof screen's database and mail grouping; nobody checks the recording for leaks (mailbox address, credentials page, token prefix, port); unrun tools on the critical path; a full timed take-day sequence. Lead: decide which get a lane before the take.

## 10. Glossary (one plain sentence each; "not defined" = the files I read do not define it)
- M1, M2, M3, N1 to N9: numbered items from the review of the flows audit (C/REPORT.md, C/review-design.md): M = Major, N = new item noticed. N7 to N9, D2, D10, Z1 are row ids given in this report to rows that had none.
- F-003, F-006, F-007, F-008, F-011, F-019, F-020, F-022, F-023, F-025: numbered findings of the flows audit; full text NOT FOUND; only parts quoted in C/REPORT.md are known to me.
- c6b item N: numbered points of C/REPORT-c6b.md (lane3 numbers against captions).
- A-01, C-01: two core patches named in decision 4 (A-01 deferred, C-01 extras cut).
- K1, K2, K3, K3B, K6: crash-test cases; see section 6. Meaning of K1 and K2: not defined.
- lane3, lease, alert, "unknown" end state: see section 1.
- stage: the program step that asks the model to qualify a lead record (stage_server.py, Q.qualify); the take's version is a rebuild not in this tree.
- stage journal / spend ledger: files kept by the stage step; the journal is a write-ahead guard that records a model call before it is made (DECISION-one-store item 4); exact spend-ledger contents not defined.
- doors: the n8n flows desk-form-door.json and desk-webhook-door.json that pass a request to "the desk" (not defined). Retired under F-019 (not read).
- ledger: the list of open problems (H/ledger.md while the handover folder exists); "ledger it" means write one row there.
- T7b: a privacy test (name, e-mail, key and mail password must not appear in stored places); file not found.
- T-ROLES: a test that database logins get "permission denied" where they should; whether it is part of the parked roles proposal: UNKNOWN.
- V7: laptop files (V7-NUMBERS-lead-read.md, mf_result_*.json) behind the "80 kills" numbers; not in any git branch.
- loopback re-smoke: a one-off manual run of real n8n 2.46.6 on the laptop's loopback address only, made-up data, no real accounts, US$0 (plan-wp6-resmoke-v5.md); not the take.
- mail_to_intake, crm_rows, crm_upsert_events, stage_calls, stage_requests, total_mails: counts in results.jsonl; see section 8.
- R460: the rule behind this audit; text not available.
