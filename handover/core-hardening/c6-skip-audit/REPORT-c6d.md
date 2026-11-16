# C6d: video audit findings after the lead's decisions of 2026-11-16 (review round 2 of 2; read-only, nothing run, no other file edited)

Built from REPORT-c6c.md plus all findings of review-c6c-design.md and review-c6c-naive.md. Also read: inputs/DECISIONS-2026-11-16.md (in the folder above this one), evidence-lane3-recompute.md, REPORT-c6b.md, REPORT.md, review-design.md, review-codebase.md, resolve-r1.md. Every status below is my reading of those texts, not new evidence. Raw lane3 files, VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md, FINDINGS.md and the F-003 patch are not in this working tree; all line cites to them are carried over and not re-verified.

## 1. Status words (plain meaning)

| status | meaning |
|---|---|
| STILL OPEN | Work remains. It changes what is filmed or said, or the checks before filming. |
| DECISION ANSWERED / FILES NOT UPDATED | The lead has already decided (decision number given). The decision is not in question any more, but a text or plan file still says the old thing. The task is the file edit. Do not filter this out when looking for work. |
| DECISION ANSWERED / NOTHING LEFT | The lead decided and no file edit remains that I know of. |
| NOT IN TAKE (author reading) | In my reading the item is not on the path filmed in scenes 1 to 4. No decision says so; the lead may overrule. Housekeeping. |
| LATER VIDEO | Belongs only to the scenes cut by decision 1 (scenes 5 to 11, stand-in flows). Housekeeping. |
| UNKNOWN | The files do not say how the item relates to scenes 1 to 4. The row names the file that decides it and who must read it. |

"The take" means the one recorded filming run. "Gate" means: do not start the take before it is done.

## 2. Priority list (read this first)

First question to the lead (blocks four groups of rows): where does the closing card sit, and does scene 4 still show the kill cases? Deciding file: VIDEO-RUNSHEET.md (scene list and :41). Rows that wait on the answer: N5, c6b item 4, c6b item 5, review-design 4, F-007 (all parts), review-design 6, c6b item 7.

Gate (blocks filming):
1. Closing card position and scene 4 content (question above). Owner: lead.
2. N2: apply the saving settings to the 8 built flows and see one run in n8n's execution list. Needs a running n8n; not tested here. Owner: lead (decision 7: the lead imports and activates flows with scripts\n8n_api.py).
3. M1: remove the caption number "60.1 to 61.9 s" from run sheet :90 and PAGE-STATEMENTS-V4.md (decision 1 cut it). Owner: builder.
4. F-007a to F-007g: scene 4 kill-case wording, only if scene 4 keeps the kill cases. Owners: see split rows.
5. N1: check that exactly one flow set (n8n-flows-real-v5) is active and no stale folder is imported. Owner: lead.
6. F-011 wording: say "one Postgres server with two databases" (decision 10), never "one database", until the loopback re-smoke (decisions 8 and 12) has passed. Owner: lead.
7. M2: re-scope privacy test T7b before it is used with saved runs ON. Owner: builder.

Housekeeping (does not change what is filmed or said):
8. F-006 line 4 edit; decision 2 text edits; F-003 patch read; DECISION-one-store line 14 edit.
9. Ledger entries (N3a and others).
10. NOT IN TAKE and LATER VIDEO rows (F-020, F-022, F-023, F-025, N6, lane3 notes).

## 3. Rules that apply to every scene-4 caption (one place, not repeated per row)
- A time may be said only as "about a minute, in the test", with no decimals, until the lead accepts a labelled number. No caption says "alert within a minute": alert timing is not measured (counts were taken after a 20 s wait, harness.py:341, per c6b review).
- "Nothing lost" is not claimed for the mail in the K3B case (see section 5).

## 4. Findings table

Owner column: lead = needs a decision or a file I cannot reach; builder = a text or test edit in a named file. I edited none of these files.

| finding | status | reason | task, owner, target file |
|---|---|---|---|
| M1: run sheet :90 caption "60.1 to 61.9 s" contradicts the sheet's own lines :22 (45 s lease unmeasured) and :85 (no number until lane3 numbers land) | DECISION ANSWERED (decision 1) / FILES NOT UPDATED | Decision 1 cuts the number. The sheet and the page still carry it as far as the carried-over cites show. | Builder: delete the number in VIDEO-RUNSHEET.md :90 and PAGE-STATEMENTS-V4.md (page :149 area). Keep "about a minute" only under the caption rule in section 3. |
| F-006: line 4 says real CRM in "scenes 1 to 5" | DECISION ANSWERED (decision 1: scene 5 cut) / FILES NOT UPDATED | REPORT.md says the line still reads "scenes 1 to 5"; scenes 5 to 11 remain in the sheet. | Builder: VIDEO-RUNSHEET.md line 4 to "scenes 1 to 4"; mark scenes 5 to 11 "later video". The open question at :56 and :78 (cut or keep scene 5) is answered by decision 1. |
| F-003 patch (its only hunk is run sheet line 4) | STILL OPEN | Never applied; may now conflict with decision 1. Patch file location: UNKNOWN (not found under handover/ in this tree). | Lead: name the patch path. Builder: read the patch, then decide whether to apply, edit or drop it. I did not read it, so I make no claim that it is wrong. |
| N1: two flow sets cannot both be active (same webhook paths mf-form, mf-hook) | DECISION ANSWERED (decision 1: no switch) / one check left | Only the real-v5 set is used. | Lead, before the take: confirm only n8n-flows-real-v5 is imported and active; none of the stale folders (n8n-flows, -v3, -v4, -real, -real-v3, -real-v4, -film, -film-v3, -film-v4). Import with scripts\n8n_api.py (decision 7). Not tested here. The claim about how the two sets differ was a hand parse with no saved output (review-design m1): unverified, no longer needed. |
| N2: empty execution list in scene 1 until saving is applied | STILL OPEN (gate) | Scene 1 is filmed; F-008 says the 8 built flows save nothing; N8N-START.md:15-27 still says all four saving settings are required. | Lead: apply the saving settings, then see one run in the list. Needs a running n8n; not tested. |
| F-011: n8n starts on its own SQLite file; the "one database" claim | STILL OPEN | Decision 10 fixes the wording ("one Postgres server with two databases: n8n's own and the take's"). The Postgres work and role tests are not done. Decisions 8 and 12 put the loopback re-smoke first. Plan v5:550 and flows-audit/EXCEPTIONS.md:5 already hold the fix. The DB_* names exist only under handover/flows-audit. | Lead: do not paste "one database" before the re-smoke. Builder: fix DECISION-one-store line 14 (decision 10; file not read by me). Tests named by the finding: T-ROLES plus the re-scoped T7b. Whether T-ROLES is part of the roles proposal that decision 3 parks: UNKNOWN; deciding file flows-audit/inputs/plan-wp6-resmoke-v5.md (not in this tree). Lead: say which role tests run before the video. |
| M2: saved runs ON invalidates test T7b | STILL OPEN | mf.py:276-278 sets saving to none, and T7b passes only then (name and e-mail 0 hits). Plan v5:125 sets saving to all. | Builder: new pass rule. The key and the mail password: 0 hits in every place searched (n8n database, n8n logs, stage journal, stage logs, spend ledger). Name and e-mail: may appear in n8n's database only; 0 hits in the stage journal, stage logs and spend ledger. Where T7b is written: not named in the files I read; builder to find it. Not run. |
| F-007a: scene 4 says K3B was "killed after the mail left" (run sheet :90) | STILL OPEN if scene 4 keeps the kill cases; otherwise NOT IN TAKE. Deciding file: VIDEO-RUNSHEET.md scene list (lead) | Basis: in all 5 kept lane3 runs of the case the file calls K3, final mail_to_intake was 0 (evidence-lane3-recompute.md); RESULTS.md Part 4 says that case is the demo's K3B and "mail not delivered"; mf.py:158 is cited as agreeing (carried over, not re-read). The lane3 data come from film-v4 stand-in flows, not the real-v5 flows. | Builder: VIDEO-RUNSHEET.md :90, K3B sentence: "stopped while the mail was being sent: in the test the mail did not arrive; the lead ends unknown with one alert". Never "killed after the mail left". |
| F-007b: same false wording on the page (PAGE-STATEMENTS-V4.md :150, :153) | STILL OPEN (same condition) | Same basis. | Builder: PAGE-STATEMENTS-V4.md :153 and :150, same K3B sentence. |
| F-007c: run sheet :24 defines lane3 K3 as "after the CRM write" | STILL OPEN (same condition) | RESULTS.md:97 (via REPORT-c6b) says lane3 K3 = the demo's K3B (killed when the mail connection opens). | Builder: VIDEO-RUNSHEET.md :24, follow the naming table in section 6. |
| F-007d: K3 sentence | STILL OPEN (same condition) | In the 3 kept runs of the case the file calls K6 (the demo's K3): mail_to_intake 1, alert 1, total_mails 2. Whether any mail was sent before the kill in K3B: not in the data (no field). | Builder: VIDEO-RUNSHEET.md, K3 sentence: "stopped after the mail was stored, before the table was updated: mail arrived once, lead ends unknown, one alert". |
| F-007e: "a real mail server might have taken it" | STILL OPEN (same condition) | It is a guess, not a measurement. | Builder: keep it only with the label "a guess"; do not attribute "may or may not have gone" to the 18 lane3 runs (review-design M3). |
| F-007f: the other run-sheet lines that contain K3 (:32 :36 :38 :39 :41 :47 :54) | STILL OPEN (same condition) | Nine lines contain K3 in total (:24 :32 :36 :38 :39 :41 :47 :54 :90). I have not read them, so I do not know which naming each uses. | Builder: read each line and make it follow the naming table. |
| F-007g: one naming table | STILL OPEN | Three sources disagree (page :150/:153, run sheet :24/:90, mf.py:153-158). | Lead: pick the file that holds the table. Builder: write it from section 6. |
| N4: duplicate of F-007 | folded into F-007a to F-007g | | none separate |
| N3a: raw e-mail passed to Q.qualify (stage_server.py:54, confirmed) | STILL OPEN as a ledger entry; relation to the take UNKNOWN | Rated Nit for the take (made-up example.test addresses), Major for any client build. Whether the qualify step runs in scenes 1 to 4: deciding files VIDEO-RUNSHEET.md scene list and PLAN-4-NLITE-FROM-LEAD.md:64-80. | Lead: write one row in handover/ledger.md as a client-build blocker. |
| N3b: does the e-mail reach the model | UNKNOWN | PLAN-4:80 says the model input is the lead id plus the normalised made-up e-mail (a statement, not a check). qualify_stage.py was not read and is not in this tree. | Lead: name who reads qualify_stage.py in the desk repo (outside this tree), or say it is out of scope for the video. Blocked until the file is available. |
| N5: narrow claim vs closing card "80 kills, 0 doubled, 0 lost" and "13 min late" (run sheet :41) | UNKNOWN (closing card position); if it sits after scene 4 then LATER VIDEO | Decision 1 cuts scene 5 and the caption number; it does not name the closing card. Phrase search in the lane3 kill folder: "80 kills" 0 files; "0 doubled" 2 files and "0 lost" 3 files, where the hits in COMPARE-demo.md:5 and RESULTS.md:100 are the demo session's column (n = 20). The third "0 lost" hit, PLAN-V3-ALERT.md:24, was NOT read in full, so I do not claim "0 lost" occurs only in the demo column. The number has no readable raw (laptop files, v3 flows, lease 20 s). | Lead: say whether the closing card stays. If yes, builder: cut "80 kills" or label it "older test, v3, lease 20 s, not re-checked"; read PLAN-V3-ALERT.md:24 in full. |
| c6b item 1: voided runs VOID-fl45k3b and VOID-fl45k6c | DECISION ANSWERED (decision 1) / NOTHING LEFT for this video; STILL OPEN only if an "18 kill runs" caption comes back | Cause UNPROVEN. Lane3 itself calls voided runs "my slips" (RESULTS.md:2) without naming a cause. Data: VOID-fl45k3b never reached an end state; its 338.7 s is the 330 s wait limit plus restart (c6b reviewer), so not a measured recovery. VOID-fl45k6c failed with fakes_not_up. A reviewer inferred that a second queue emptied the table (harness.py:261); overlap alone does not show it. | Lead, if the number returns: ask lane3 to confirm the cause, or re-run K3 at lease 45 s. |
| c6b item 2 / review-design m3: "18 kill runs" hides n = 3 for the demo's K3 | STILL OPEN only if a run count is captioned | Counts per case 5, 5, 5, 3. | Builder: give the split if captioned. |
| c6b item 4: "80 kills, 0 doubled, 0 lost" has no readable raw; "0 lost" counts unknown as not lost (mf.py:83); 40 of 80 end unknown | UNKNOWN (closing card position), else LATER VIDEO | See N5. | See N5. |
| c6b item 5: small differences (raw min 52.8 vs caption 52.9; closing card line 3 n = 2, from n8n up) | UNKNOWN (closing card position; whether the 52.9 to 54.9 caption stays in scene 4) | Decision 1 cuts only "60.1 to 61.9 s". Deciding file VIDEO-RUNSHEET.md. | If they stay, builder: 52.9 to 52.8; line 3 to "n=2 (K1), 6 runs between 144.2 and 144.4 s, measured from n8n coming back up", or drop. |
| c6b item 6: 45 s lease supported only indirectly (flows imported from a local folder not in the repo; byte-identity not proven) | STILL OPEN only if scene 4 says "45-second lease" aloud | Label 873a908a-film-v4-lease45 is a real commit; its mf-form.json and mf-recovery.json contain interval 45 seconds (c6b). Unexplained: at lease 120 s time from n8n up is about lease + 24 s, at 45 s about lease + 8 s. | Lead: accept the indirect support or drop the words. |
| review-design 3: three queues overlapped (run_all.progress lines 101-127); "lane" means two things | STILL OPEN only if lane3 timings are captioned | Overlap may have stretched restart times. | Builder: say so if captioned; use "lane3" only for the session. |
| review-design 4: closing card "nothing lost, nothing doubled" claims too much | UNKNOWN (closing card position), else LATER VIDEO | crm_rows was 1 and stage_calls was 1 in all 18 kept rows, so "not shown to be doubled by these two fields". Other counts differ: crm_upsert_events 2 in 13 of 18, stage_requests 2 in all 18 (not explained); crm_rows is only the final state. "Nothing lost" fails for the mail in K3B (mail_to_intake 0, 5 of 5). | If the card stays, builder: "no lead row lost or duplicated by the two final counts (crm_rows 1, stage_calls 1 in all 18); in 5 runs the mail did not arrive and a person was alerted", plus the upsert count, or drop "nothing lost". |
| review-design 5: the 60.1 to 61.9 s range is one test program's repeatable timing | DECISION ANSWERED (decision 1) / NOTHING LEFT | Number cut. | Section 3 rule applies. |
| review-design 6: alert timing not measured | STILL OPEN if scene 4 keeps the kill cases | See section 3. | Builder: check scene 4 wording against section 3. |
| review-design M3 warning: do not attribute "may or may not have gone" to the 18 lane3 runs | STILL OPEN (see F-007e) | | |
| F-020: stage journal has two names (stage.journal in the take, stage-journal.jsonl in the harness) | STILL OPEN (Nit) | The cited stage_server.py is the older prototype; the take uses a rebuild (PLAN-4:64-80) not in this tree. | Builder: one name in texts only; do not move the journal before the video. |
| F-022: desk doors' 502 path never reaches the error workflow | NOT IN TAKE (author reading) | REPORT.md: doors retired under F-019 (not read). The finding's own fix text is wrong ("Reply 2xx" is also the success reply). mf-form real-v5 :238-295 only sets n8n_error:false, so the take flows do not repeat it. | Retire the doors; no patch. |
| F-023: table-screen READMEs disagree about "NOT run" (v1 README; v2 :3, :48, :51; DOUBTFUL-SCENE.md:13) | NOT IN TAKE (author reading) | The run sheet forbids saying it works. | Lead: ask the laptop agent first; then one dated run; then make the texts agree. |
| F-025: v1-superseded recovery re-claims forever (30 s sweep, 20 s lease; no attempts cap, no alert) | NOT IN TAKE (author reading) | Kept "for the compare only". | Builder: archive the folder per CUT-LIST.md; update REPORT.md:33, :526-528, DESIGN-A-README.md:3. |
| N6: door node name "Reply error" | NOT IN TAKE (author reading) | Same doors as F-022. | none for the video |
| Decision 2: the take never deletes contacts; the owner deletes leftovers by hand | DECISION ANSWERED (decision 2) / FILES NOT UPDATED | Related text: core-hardening/QUESTIONS.md item 1 and steps-edits/OWNER-STEPS-realrun-v8.md (step F, "archive" meaning delete, key needs the delete right, about :155-167 and :244-250). Not re-read here. | Builder: the take lists leftover contacts by lead key and contact id; remove the "key needs delete permission" requirement. Lead: "F-01" has no entry in the c6 files; it may be a mix-up with A-01 or C-01 (decision 4). If it is another finding: UNKNOWN; deciding file flows-audit/FINDINGS.md or the C5 edit list (not read). |
| Whether any mail was sent before the kill in K3B | UNKNOWN | The data file has no field; only RESULTS.md Part 4 says "mail not delivered". Harness code not checked. | Lead: ask lane3 or read the harness. |
| "13 min late" line and lane3's later fix (alert at 60 s, 3 of 3, lane3 REPORT.md:18, not adopted in the demo flows) | UNKNOWN (closing card position) | | Lead: keep or drop "13 min late" (c6b question 5). |
| "HB194" name | STILL OPEN (wording) | HB194 appears only in commit 2595b8c3's message; best match RESULTS.md Part 3 lines 83-92 (inference). The HB194 block itself was not read. | Builder: cite "demo3/kill/RESULTS.md, commit 2595b8c3" instead (c6b question 4). |

## 5. Recomputed numbers (one table; basis: evidence runner's recompute of results.jsonl, 128 rows, not re-checked by me; (H) = hand recompute by the c6b reviewer)

| quantity | value | field name |
|---|---|---|
| lease-45 rows | 23 = 18 kept + 2 voided + 3 error-case rows | flows, point, label |
| kept runs per case, file names | K1 5, K2 5, K3 5, K6 3 | point |
| kill to end state | min 60.1, max 61.9, median 60.85 s | kill_to_final_s |
| kill_to_final_s vs restart_s + recovery_s | largest difference 0.1 s | restart_s, recovery_s |
| restart (H) | 6.6 to 8.8 s | restart_s |
| recovery (H) | 52.8 to 54.9 s | recovery_s |
| CRM upsert calls seen | 2 in 13 of 18 (K2 5, K3 5, K6 3); 1 in the 5 K1 runs | crm_upsert_events |
| final CRM rows | 1 in all 18 | crm_rows |
| model-stage calls | 1 in all 18 | counts.stage_calls |
| stage requests | 2 in all 18 (not explained) | stage_requests |
| intake mails at the end | K1 1, K2 1, K3 0 (5 of 5), K6 1 (3 of 3, total_mails 2) | counts.mail_to_intake |
| end states (H) | K1, K2 done (10 of 18); K3, K6 unknown with 1 alert (8 of 18) | states |
| voided runs | VOID-fl45k3b: 17:09:59Z to 17:16:35Z, never terminal, 338.7 s, no error text; VOID-fl45k6c: error fakes_not_up | label |
| runs attempted at lease 45 (H) | 20 (K1 5, K2 5, K3 6, K6 4) | |

Not found: "80 kills" (0 files in the lane3 kill folder); any mail field before the kill. The mapping of file names to demo names and "mail not delivered" come from RESULTS.md Part 4 text only; there is no "K3B" label in results.jsonl.

## 6. Naming table (cases)

| demo name (page, run sheet, mf.py) | lane3 file name | what happens | basis |
|---|---|---|---|
| K3B | K3 | stopped while the mail connection opens; mail not delivered in the test | RESULTS.md Part 4 and :97 via the evidence runner; mf.py:153-158 carried over |
| K3 | K6 | stopped after the mail was stored, before the table update; mail arrived once | same; mf.py:159-164 carried over |
| K1, K2 | K1, K2 | same names; meaning UNDEFINED here (observed end state done, mail 1, alert 0) | evidence file |

## 7. Failures, uncertain items, not checked
1. Closing card position and scene 4 content are not stated in any file I read; several rows depend on them (section 2).
2. Nothing re-checked against raw files; nothing run. raw-lane3/ was not opened by me.
3. NOT IN TAKE for F-022, F-023, F-025, N6 is my reading, not a decision.
4. Not read: F-003 patch, VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md, FINDINGS.md, plan v5, lane3 harness, PLAN-V3-ALERT.md:24. The bible is not on disk, so R460 could not be checked.
5. T-ROLES against decision 3 is unresolved (F-011 row).

## 8. Glossary (one plain sentence each; UNDEFINED = the files I read do not define it)
- M1, M2, M3, N1 to N6: numbered items from the review of the flows audit (REPORT.md, review-design.md): M = Major, N = new item noticed.
- F-003, F-006, F-007, F-008, F-011, F-019, F-020, F-022, F-023, F-025: numbered findings of the flows audit, text in handover/flows-audit/FINDINGS.md (not in this tree; only parts quoted in REPORT.md are known to me).
- c6b item N: the numbered points of REPORT-c6b.md (lane3 numbers against captions).
- A-01, C-01: two core patches named in decision 4 (A-01 deferred, C-01 extras cut).
- K1, K2, K3, K3B, K6: crash-test cases; see section 6. Meaning of K1 and K2: UNDEFINED.
- lane3: the separate test session and git branch (origin/demo/lane3) that ran the 45-second-lease crash tests; whether it is a person or an agent: UNDEFINED. The harness's own LANE number (0, 1, 3) is a different thing: which test queue ran.
- lease: how long a claimed lead stays reserved before the recovery sweep may take it again (my reading of "30 s sweep with a 20 s lease"). Older tests used 20 s, lane3 used 45 s, one older series 120 s.
- real-v5: the set of n8n flows (folder n8n-flows-real-v5) that talks to the real mail and CRM services; the only set used in the one video.
- film-v5: the set of n8n flows (folder n8n-flows-film-v5) that talks to stand-in services we control; its scenes 5 to 11 are a possible later video.
- stand-in: a fake service we control.
- stage: the program step that asks the model to qualify a lead (stage_server.py, Q.qualify); the take's version is a rebuild not in this tree; exact role UNDEFINED beyond that.
- stage journal / spend ledger: files kept by the stage step; exact contents UNDEFINED here.
- doors: the n8n flows desk-form-door.json and desk-webhook-door.json that receive a request and pass it to "the desk"; "the desk" is UNDEFINED. Retired under F-019 (not read).
- ledger: the list of open problems (handover/ledger.md while the handover folder exists); "ledger it" means write one row there.
- T7b: a privacy test (name, e-mail, key and mail password must not appear in stored places); file location UNDEFINED.
- T-ROLES: a test that database logins get "permission denied" where they should (F-011 row); whether it is in the parked roles proposal: UNKNOWN.
- V7: laptop files (V7-NUMBERS-lead-read.md, mf_result_*.json) behind the "80 kills" numbers; not in any git branch.
- HB194: a block name in lane3 results; see the last table row.
- take / gate: see section 1.
- mail_to_intake, crm_rows, crm_upsert_events, stage_calls, stage_requests: counts in results.jsonl; see section 5.
- R460: the rule behind this audit; text not available.
