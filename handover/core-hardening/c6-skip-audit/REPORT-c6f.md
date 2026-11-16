# C6f: video audit findings after the lead's decisions of 2026-11-16 (read-only audit; nothing run; no flow or program file edited)

Built from REPORT-c6e.md with every finding of review-c6e-design-r2.md (2 Blockers, 6 Majors) and review-c6e-naive-r2.md (4 Majors, 8 Nits) fixed, plus the lead's answers of 10:13 UTC (15:43 IST) at the bottom of H/core-hardening/ORDERS.md. Where a finding could not be fixed, c6f-CHANGES.md says so. This report is a draft for the next independent review; the lead decides whether another review round runs.

Base folders: H = /home/user/hadavin-sdk/handover. C = H/core-hardening/c6-skip-audit (this folder). Where I could find a file under H, its path is given. Where I could not, the text says NOT FOUND (see section 9).

Every status below is my reading of the texts, not new evidence. Nothing was run. Where a number or line cite comes from an earlier report and I did not open the file, the row says "carried over". All times are given in UTC and IST (IST = UTC + 5:30).

Terms such as run sheet, page, caption, closing card, kill cases, demo, T-ROLES, group L, S1b, G5, lane3, K1/K2/K3/K3B/K6 are defined in section 10 (glossary). Read section 1 first, then section 10 when a word is new.

## 1. Words used in this report

People and records. One word, one meaning:

| word | meaning here |
|---|---|
| lead | the studio lead: the decision maker who answers the questions in this report and made the decisions of 2026-11-16 (H/core-hardening/inputs/DECISIONS-2026-11-16.md). Always "the lead", never a sales contact. |
| owner | the studio owner: types y, the challenge and end in the take, deletes leftover made-up contacts by hand after the take (decision 2), revokes keys at clean-up, and may veto any decision. Not the same role as the lead. |
| builder | an agent or person who edits a named text or test file. |
| lead record | one made-up sales contact (a record with a lead id) that the flows process. Written "lead record" everywhere. |
| lead id | the identifier of one lead record. The narrow claim is about the same lead id arriving twice. |

One word, one meaning for the words that were overloaded in earlier reports:

| word | meaning here | words I use instead for the other meanings |
|---|---|---|
| lane3 | the separate test session and git branch (origin/demo/lane3) that ran the 45-second-lease crash tests. Whether it is a person or an agent: not stated in any file I read. | the harness's own queue number (0, 1, 3) is called "test queue"; a review agent is called "review agent" |
| row | one row of a table in this report, called "report row". | a line of results.jsonl is a "result line"; a contact in the CRM is a "CRM contact"; a claim table entry is a "claim-table entry" |
| run | one execution of a test (a "test run", for lane3 data) or the one filmed execution (the "take"). | the owner steps' "recording run" is the take |
| claim table | the Postgres table `mf_leads` that reserves and records each lead record (DECISION-one-store.md). | the HubSpot side is always "CRM" or "CRM contact"; the word "table" alone is not used for either |
| UNKNOWN | the status word in capitals (below). | the lead record's end state is written `unknown` in code font ("end state `unknown`") |
| findings table | section 5; "naming table" is section 6; "recompute table" is section 8. | |

Status words (one status per findings row; a second fact goes in the Notes column, never into the status):

| status | meaning |
|---|---|
| STILL OPEN | Work remains. It changes what is filmed or said, or the checks before filming, or it is a housekeeping edit still to do. The List column says which. |
| CONDITIONAL | STILL OPEN only if a stated condition holds. If the condition is false, the row becomes NOT IN TAKE or LATER VIDEO. The Notes column names the condition. |
| DECISION ANSWERED / FILES NOT UPDATED | The lead has already decided (decision number given). At least one text or plan file still says the old thing. The task is the file edit. Do not filter this out when looking for work. |
| DECISION ANSWERED / NOTHING LEFT | The lead decided and no file edit remains that I know of. Used only where I read the relevant file. |
| NOT IN TAKE (author reading) | In my reading the item is not on the path filmed in scenes 1 to 4. No decision says so; the lead may overrule. |
| LATER VIDEO | Belongs only to the scenes cut by decision 1 (scenes 5 to 11, stand-in flows, film-v4 and film-v5 data). |
| DUPLICATE | The row repeats another row; the row it is folded into is named. No separate task. |
| UNKNOWN | The files I can read do not say how the item relates to scenes 1 to 4 (or what it is). The row names the file that decides it and who must read it. |

List column: G = gate (blocks filming, section 3 gate list), GC = gate only if the named question is answered a certain way (section 3), H = housekeeping (does not change what is filmed or said), A = archive (LATER VIDEO), D = duplicate (no task).

Other terms:
- "The take" = the one recorded filming run. "Gate" = do not start the take before it is done.
- real-v5 = the n8n flows in folder n8n-flows-real-v5, which talk to the real mail and CRM services; the only flow set in the one video (decision 1).
- film-v4 / film-v5 = flow sets that talk to stand-in (fake, controlled by us) services. Their scenes (5 to 11) are a possible later video.
- lease = how long a claimed lead record stays reserved before the recovery sweep may take it again. Older tests used 20 s, lane3 used 45 s, one older series 120 s (unit: seconds).
- alert = the one mail the system sends to a named address when it cannot tell what happened to a lead record. Alert timing is not measured (see N7 and section 7).
- end state `unknown` = the lead record's final state when the program could not tell whether the contact and mail happened; a person decides.
- Question labels: Q1 to Q10 in this report are this report's own questions. The "Q14" and "Q15" in ORDERS.md are other questions with other numbers; their answers are used where they touch rows. "REPORT-c6b question 4/5" means the numbered questions in C/REPORT-c6b.md.

## 2. What the video shows (from the decisions file only)

Source: H/core-hardening/inputs/DECISIONS-2026-11-16.md, decisions 1, 2, 6, 7, 8, 9, 12, and the lead's answers of 10:13 UTC. I did not find the run sheet (VIDEO-RUNSHEET.md: NOT FOUND), so I cannot describe the scenes from the scene list.

What the decisions say:
- One video, real-v5 only: scenes 1 to 4 of the run sheet. Scenes 5 to 11 (stand-in flows) are not in it. The lead confirmed at 10:13 UTC that film-v5 is OUT.
- Narrow claim: **a lead sent twice with the same id inside the lease is processed once** (lead's wording at 10:13 UTC; the lease-expiry behaviour goes into the claim text as an honest sentence, see section 7).
- The take runs on made-up data against real mail and CRM accounts of ours, never deletes contacts (decision 2), uses its own free port (decision 6; the rehearsal uses 5690), and the lead imports and activates the flows with scripts\n8n_api.py (decision 7).
- The counts proof screen is a rehearsal screenshot or the Postgres node preview, not a live claim-table screen (decision 9).
- Scene 1 shows n8n's execution list (row N2). Scene 4 contains the kill-case wording and captions this report discusses (rows M1, F-007a to F-007g).

What I do not know (so nothing below should be read as describing scenes 1 to 4):
- What each of scenes 1, 2, 3 and 4 shows, in order.
- Whether scene 4 still shows the kill cases (a crash of n8n during processing) and where the closing card sits (Q1, Q2).
- What "sent twice" means in the take: two sends at once, a second send after the first finished, after the lease ran out, or after a crash. Where the lead id comes from (the sender, or made by n8n) is also unchecked.
- Whether a same-id-twice case with a pass rule exists in the loopback re-smoke. In this pass I searched the whole of H/core-hardening/inputs/plan-wp6-resmoke-v5.md (558 lines) for "twice", "same id" and "same lead": 0 hits. That is "not found by phrase search", not "absent". The owner steps v9 (H/core-hardening/steps-edits/OWNER-STEPS-realrun-v9.md) do say, at lines 18 and 408, that person A is sent twice and B ten times at once and C once while n8n is stopped and started: 13 sends in, "treat each person once". I have not checked that this is a same-id-twice proof on real-v5.
- Measured evidence for the narrow claim on real-v5: none found. All crash numbers in this report come from film-v4 stand-in flows (lane3), not from real-v5.

## 3. Priority list (read this first)

Questions for the lead. Each is answerable with the option shown; the default is what I will assume if no answer comes (the lead may veto):

- **Q1. Scene 4 content and closing card.** Where does the closing card sit, and what does scene 4 show? Answer by reading the run sheet (VIDEO-RUNSHEET.md, NOT FOUND in this tree). Default: none (cannot be assumed). Rows that wait on it: N5, N7, c6b-4, c6b-5, review-design-4. (The c6f note at the top removes c6b-6 and review-design-6 from this list; they wait on Q2.)
- **Q2. Kill cases in scene 4.** Decision 8 allows no extra real-account smoke, so the kill cases cannot be measured on real-v5 before the take. Choose: (a) drop the kill cases from scene 4 (then rows F-007a to F-007g, c6b-1, c6b-2, c6b-6, review-design-3 and review-design-6 become NOT IN TAKE), or (b) keep them, with every kill-case line labelled "stand-in flows, film-v4" (then those rows are gate items). Default: (b), because the page and run sheet already carry kill-case text and (a) loses material the owner may want; this is my suggestion only.
- **Q3. Who runs the loopback re-smoke?** Yes or no: the lead runs the loopback re-smoke and then the first laptop rehearsal (decision 12 names the lead for the rehearsal; it does not name who runs the re-smoke). Default: yes, the lead runs both.
- **Q4. Role tests before the video.** Does any role test run before the video (T-ROLES, group L, or the fourth login of the parked roles proposal)? Default: none (decision 3).
- **Q5. S1b.** S1b (three Postgres roles with negative tests, plan line 277 and line 73) is in the loopback re-smoke plan. Decision 3 parks "four logins", not three roles. Keep S1b in the re-smoke? Default: yes, keep S1b (three roles), run no other role test.
- **Q6. When are the flows activated.** The lead imports and activates the flows during take prep, before the owner types y (decision 7); decision 5 refuses the S9-1 fallback "lead activates flows after the owner's typed y" and refuses the claim "nothing can spend before both typed answers". Confirm: activation before y, no such claim anywhere. Default: yes.
- **Q7. Owner steps step 0 (HubSpot check, 7 live calls to the CRM test account).** Decision 8 replaces "real-account smoke checks a to f" by the loopback re-smoke plus ONE made-up lead in take prep. Is v9 step 0 the "one made-up lead", or is it one of the removed checks a to f? Default (changed after review): step 0 counts as the ONE made-up lead only if it makes one create and no delete; otherwise the lead must answer Q7 before G-13 and G-7 can close.
- **Q8. Who produces the counts proof screenshot** (decision 9)? Default: the lead, from the rehearsal (decision 12).
- **Q9. Time wording.** Accept the rounded wording "about a minute, in the test" in place of the cut number (section 7)? Default (changed after review): NO time caption until the lead accepts it, because the rounded wording is the cut unmeasured number again. The rounding is mine, not the lead's.
- **Q10. Which OWNER-STEPS version does the owner read?** (v9 is the highest sheet found; checkpoint-v10.md exists but no v10 sheet was found.) Default: v9.

Gate list (blocks filming), in the order the decisions put the work. Sequence per decision 12: loopback re-smoke passes, then the lead's first laptop rehearsal, then the clean start (CS1), then the take. Target for the lead's re-smoke and rehearsal: tonight or tomorrow morning IST, that is 16 Nov evening to 17 Nov morning IST (about 12:30 UTC on 16 Nov to 06:30 UTC on 17 Nov); the lead puts the real times in the handoff. The owner's aim is the video posted by Wed 18 Nov 2026 (v9 line 137); the latest post is Wed 25 Nov 2026, 15:00 UTC = 20:30 IST (v9 step J). Owner of each gate item is in the findings table.
- G-1. P1: the plan edit (plan names film-v5 where decision 1 says real-v5). Owner: lead.
- G-2. D12: the sequence and the times in the handoff. Owner: lead.
- G-3. N2: apply the saving settings to the built flows (the count 8 is carried over from earlier reports and not re-counted; if the count differs, apply to all built flows) and see one run in n8n's execution list. Needs a running n8n; not tested here. Owner: lead.
- G-4. N1: check that exactly one flow set (n8n-flows-real-v5) is active and no stale folder is imported. Owner: lead.
- G-5. M2: re-scope privacy test T7b before it is used with saved runs ON. Owner: builder.
- G-6. F-011 and section 4: the "one database" wording. Owner: lead (ratify or veto the interim sentence).
- G-7. D2: decision 2 stale text in owner steps v4 to v8 (v9 looks fixed). Owner: builder; lead closes QUESTIONS.md item 1.
- G-8. M1 with review-design-5 and F-006 with F-003: the run sheet and page edits that remove the cut caption number and set line 4 to "scenes 1 to 4". Owner: builder.
- G-9. CL1: claim sentence and honest lease-expiry sentence in the claim text (section 7). Owner: builder.
- G-10. CS1: clean start, a numbered row in the lead/owner steps (v4 and later), owner of the step = lead. Owner: builder writes, lead performs.
- G-11. D9: the proof screenshot exists from the rehearsal (Q8). Owner: lead.
- G-12. D6: the real take's own free port named once in the plan, and a stale-port check. Owner: builder (text), lead (port).
- G-13. D8: text for "loopback re-smoke plus ONE made-up lead" (Q7). Owner: builder.
- G-14. D5a and D5b: S9 items as text, and the decision 5 versus decision 7 check (Q6). Owner: builder.
- G-15. ROLE1: which role tests run (Q4, Q5). Owner: lead.

Gate only if the question is answered a certain way:
- GC-Q2b. If Q2 = (b) or no answer: F-007a to F-007g, c6b-1, c6b-2, c6b-6, review-design-3, review-design-6 (and "K3B mail before the kill", added by the c6f note) are gate items (kill-case wording and labels). If Q2 = (a): they become NOT IN TAKE.
- GC-Q1. If the closing card stays after scene 4: N5, N7, c6b-4, c6b-5, review-design-4 are gate items. If it is cut: they become LATER VIDEO.
- GC-route. Z1c: the minimal price/max_tokens check is a gate item only if the take's model program loads Route config (decision 4; unverified).

Housekeeping (does not change what is filmed or said):
- H-1. DECISION-one-store.md line 14: unconditional edit to the decision 10 wording (decision 10 orders it; this is a decision document, so it states the target). N9 and F-011 now agree on this (section 4).
- H-2. N3a: one ledger row in H/ledger.md as a client-build blocker.
- H-3. N3b: name who reads qualify_stage.py, or say out of scope.
- H-4. N8: cite the HB194 findings by a file and commit that can be looked up.
- H-5. F-020a: use one journal name (stage.journal) in take texts only. (Housekeeping because the journal name is not filmed; if a take text the owner reads uses the other name, move it to the gate.)
- H-6. D10-archive: archive line for OWNER-STEPS v3 (found at H/core-hardening/inputs/OWNER-STEPS-realrun-v3.md; archive, never delete).
- H-7. Z1b: where the G5 wording lives and whether it is already in a text (decision 4).
- H-8. F-007g: one naming table in one file (builder, after Q2).
- H-9. D11: licence copies recorded as BRANCH ARTEFACT; out of scope for the video (nothing left in this audit).
- H-10. Z1a: core patches deferred or cut; nothing left for the take.

Archive (LATER VIDEO, NOT IN TAKE; no more rounds spent): F-020b, F-022, F-023, F-025, N6.

Duplicates (no task): N4, c6b-3, c6b-7, review-design-3-warning (M3 warning), review-design-5, D10, N9.

## 4. The "one database" wording and the re-smoke (F-011 answer)

**What this section is.** It is a request to the lead to ratify or veto an interim wording that departs from decision 10. Decision 10 orders this wording: "one Postgres server with two databases (n8n's own and the take's)". That is the TARGET. I quote it as binding and I do not replace it. My finding is that the target is not yet true: row F-011 (carried over; the state was not re-checked on a running system) says n8n starts on its own SQLite file and the Postgres move is not done. So I propose an interim sentence for the time before the re-smoke has passed. Ratify it, or veto it and use the decision 10 wording only after the Postgres move has been checked. I have no authority to override decision 10.

- **True now (carried over from F-011, not re-checked):** n8n starts on its own SQLite file (a small file database).
- **Interim sentence (proposed; true now; no forward claim):** "n8n keeps its own records in its own database file. Our claim table for lead records is in a separate Postgres database. That is two stores." The claim-table fact is from H/core-hardening/inputs/DECISION-one-store.md (a decision text, not checked on a running system).
- **Target sentence (decision 10; use only after the loopback re-smoke has passed and shows the engine is Postgres):** "one Postgres server with two databases: n8n's own and the take's."
- **Who runs the re-smoke:** Q3 asks the lead to confirm. Decision 12 names the lead for the first laptop rehearsal "right after the loopback re-smoke passes"; I read this as the lead running both, but it is not literal.
- **What the plan covers:** H/core-hardening/inputs/plan-wp6-resmoke-v5.md (558 lines; I read only the lines cited in this report and ran phrase searches): real n8n 2.46.6 on loopback, made-up data, US$0, saved runs ON (lines 38, 73), a separate database, and S1b (line 277): three Postgres roles with negative tests. Whether S1b stays: Q5. Whether any other role test runs: Q4 (default none, decision 3).
- **Plan edit as text for the lead (answer Q15.1 of 10:13 UTC; I run nothing and edit no plan file).** The plan still names film-v5 at lines 120 (code-source table), 236, 284, 126 (ids "film smkForm000000001 ..."), 298 (step 2.1 imports n8n-flows-film-v5) and 543 (table M3, n8n-flows-film-v5/mf-sub-crm-mail.json). Proposed replacement: in step 2.1 import the real-v5 folder (n8n-flows-real-v5) instead of n8n-flows-film-v5; at line 126 use the real-v5 workflow ids; at line 543 use the real-v5 file names. I have not read the real-v5 JSON, so the real ids and the changes needed in the stand-in services (crm_stub, smtp_catcher: plan line 121) are for the builder to check. Real-v5 uses a HubSpot credential and a mail credential, which the loopback re-smoke does not have. That difference may make "fills real-v5" mean "real-v5 against stand-in services on loopback". The lead should say which.
- **DECISION-one-store.md line 14 edit (unconditional, decision 10 orders it).** Line 14 now says "ONE database for everything we own: the single Postgres instance of the take (one container, one engine)". Change it to the decision 10 wording ("one Postgres server with two databases: n8n's own and the take's"). It states the target of a decision document and makes no claim about the present. This edit is H-1; it is not conditional on the re-smoke. Rows F-011 and N9 now say the same.

## 5. Findings table

Owner column: lead = needs a decision or a file I cannot reach; builder = a text or test edit in a named file. I edited none of these files. NOT FOUND means Glob/find under H returned nothing.

Columns: id and finding | status | list | notes (condition, carried-over marks, second facts) | reason, task, owner, target file

1. **M1**: run sheet :90 caption "60.1 to 61.9 s" contradicts the sheet's own :22 (45 s lease unmeasured) and :85 (no number until lane3 numbers land). Status: DECISION ANSWERED / FILES NOT UPDATED. List: G-8. Notes: Decision 1 cuts the number. The sheet and page still carry it as far as carried-over cites show. Both files NOT FOUND, so not re-checked. Task: builder deletes the number in VIDEO-RUNSHEET.md :90 and PAGE-STATEMENTS-V4.md (page :149 area). Say "about a minute, in the test" (section 7, Q9).

2. **F-006**: run sheet line 4 says real CRM in "scenes 1 to 5". Status: DECISION ANSWERED / FILES NOT UPDATED (decision 1). List: G-8. Notes: C/REPORT.md (found, read) says line 4 still reads "scenes 1 to 5" and the branch never got the patch. The run sheet is what the film follows, so this changes what is said: gate, not housekeeping (the earlier filing contradicted the rule in section 1). Task: builder sets VIDEO-RUNSHEET.md line 4 to "scenes 1 to 4" and marks scenes 5 to 11 "later video". Questions at :56 and :78 are answered by decision 1. File NOT FOUND.

3. **F-003 patch** (its only hunk is run sheet line 4). Status: STILL OPEN. List: G-8. Notes: Never applied; may conflict with decision 1; same line as F-006. Patch NOT FOUND (patches in H/core-hardening/paste-check/ are plan patches, not opened). Task: lead names the patch path. Builder reads it, applies, edits or drops it; if dropped, do the F-006 edit by hand. I make no claim that it is wrong.

4. **N1**: two flow sets cannot both be active (same webhook paths mf-form, mf-hook). Status: STILL OPEN. List: G-4. Notes: One check left before the take; decision 1 removes the need to switch sets. The claim about how the two sets differ was a hand parse with no saved output (review-design m1, C/review-design.md): unverified, no longer needed. The take's n8n_api.py copy NOT FOUND (test copies under H/core/evidence/r7u-chain/). Not tested. Task: lead, before the take, confirms only n8n-flows-real-v5 is imported and active; none of n8n-flows, -v3, -v4, -real, -real-v3, -real-v4, -film, -film-v3, -film-v4. Import with scripts\n8n_api.py (decision 7).

5. **N2**: empty execution list in scene 1 until saving is applied. Status: STILL OPEN. List: G-3. Notes: F-008 says the built flows save nothing; N8N-START.md:15-27 (NOT FOUND, carried over) says all four saving settings are required. Needs a running n8n; not tested. Task: lead applies the saving settings, then sees one run in the list.

6. **F-011**: n8n starts on its own SQLite file; the "one database" claim. Status: STILL OPEN. List: G-6. Notes: Carried over: the SQLite state was not re-checked. DECISION-one-store.md line 14 (read) says the DB_POSTGRESDB_* names are allowed by n8n_start.sh line 115; I did not check n8n_start.sh or any system. Decisions 8 and 12 put the loopback re-smoke first. Task: see section 4; the lead ratifies or vetoes the interim sentence. Plan: H/core-hardening/inputs/plan-wp6-resmoke-v5.md. Role tests: Q4, Q5.

7. **M2**: saved runs ON invalidates test T7b. Status: STILL OPEN. List: G-5. Notes: Carried over, not re-checked here: mf.py:276-278 sets saving to none and T7b passes only then; the re-smoke plan sets saving ON (plan lines 38, 73; read). The "0 hits in every place searched" claim for key and mail password comes from earlier reports (nothing searched in this pass; mf.py NOT FOUND); treat it as unverified. Task: builder writes a new pass rule. Key and mail password: "0 hits" carried over from earlier reports (n8n database, n8n logs, stage journal, stage logs, spend ledger). Name and e-mail: may appear in n8n's own store only (carried over). Where T7b is written: not found; builder to find it. Not run.

8. **F-007a**: scene 4 says K3B was "killed after the mail left" (run sheet :90). Status: CONDITIONAL. List: GC-Q2b. Notes: Condition: Q2 = (b), scene 4 keeps the kill cases (else NOT IN TAKE). In all 5 kept lane3 runs of the case the file calls K3, final mail_to_intake was 0 (C/evidence-lane3-recompute.md, section 6); RESULTS.md Part 4 (C/raw-lane3/RESULTS.md :97) says that case is the demo's K3B, "killed when the mail connection opens, mail not delivered". mf.py:158 cited as agreeing (NOT FOUND, carried over). Data are film-v4 stand-in, not real-v5. Task: builder edits VIDEO-RUNSHEET.md :90, K3B sentence from section 6 (killed when the mail connection opens; in the stand-in test the mail did not arrive; end state `unknown`; one alert), labelled "stand-in flows, film-v4". Never "killed after the mail left".

9. **F-007b**: same false wording on the page (PAGE-STATEMENTS-V4.md :150, :153). Status: CONDITIONAL. List: GC-Q2b. Notes: Condition as F-007a. Same basis. File NOT FOUND. Task: builder, same K3B sentence in PAGE-STATEMENTS-V4.md :153 and :150.

10. **F-007c**: run sheet :24 defines lane3 K3 as "after the CRM write". Status: CONDITIONAL. List: GC-Q2b. Notes: Condition as F-007a. RESULTS.md:97 says lane3 K3 = the demo's K3B (killed when the mail connection opens). Task: builder edits VIDEO-RUNSHEET.md :24, follows section 6.

11. **F-007d**: K3 sentence. Status: CONDITIONAL. List: GC-Q2b. Notes: Condition as F-007a. 3 kept runs of the case the file calls K6 (the demo's K3): mail_to_intake 1, alert 1, total_mails 2. The CRM contact was already written at the kill in both K3B and K3 (CRM flag "t", C/evidence-lane3-recompute.md section 6), so the earlier phrase "before the table was updated" is not supported and is dropped (it also used "table" for two things). Whether any mail was sent before the kill in K3B: not in the data. Task: builder writes the K3 sentence from section 6: "killed after the mail was stored: the mail arrived once; the lead record ends `unknown` with one alert", labelled "stand-in flows, film-v4".

12. **F-007e**: "a real mail server might have taken it". Status: CONDITIONAL. List: GC-Q2b. Notes: Condition as F-007a. A guess, not a measurement. On real-v5 it may not apply (Q2). Task: builder keeps it only with the label "a guess"; do not attribute "may or may not have gone" to the 18 lane3 runs (review-design M3).

13. **F-007f**: other run-sheet lines with K3 (:32 :36 :38 :39 :41 :47 :54). Status: CONDITIONAL. List: GC-Q2b. Notes: Condition as F-007a. "Nine lines contain K3 (:24 :32 :36 :38 :39 :41 :47 :54 :90)" is carried over from an earlier report; the run sheet is NOT FOUND, so I did not count. Task: builder reads each line and follows section 6.

14. **F-007g**: one naming table. Status: CONDITIONAL. List: GC-Q2b, H-8. Notes: Condition as F-007a (if the kill cases leave scene 4 the table is only needed for the later video). Three sources disagree (page :150/:153, run sheet :24/:90, mf.py:153-158; all carried over). Task: lead picks the file that holds the table. Builder writes it from section 6.

15. **N4**: duplicate of F-007. Status: DUPLICATE (folded into F-007a to F-007g). List: D. Same finding found a second time by another reviewer. No separate task.

16. **N3a**: raw e-mail passed to Q.qualify (stage_server.py:54). Status: STILL OPEN. List: H-2. Notes: A ledger entry only. Nit for the take (made-up example.test addresses), Major for any client build. Whether qualify runs in scenes 1 to 4 is N3b. stage_server.py NOT FOUND (cite carried over). Task: lead writes one row in H/ledger.md (found; a second ledger is H/reviews/ledger.md) as a client-build blocker.

17. **N3b**: does the e-mail reach the model, and does qualify run in scenes 1 to 4. Status: UNKNOWN. List: H-3. Notes: PLAN-4:80 says the model input is the lead id plus the normalised made-up e-mail (a statement, not a check). qualify_stage.py, VIDEO-RUNSHEET.md and PLAN-4-NLITE-FROM-LEAD.md:64-80 NOT FOUND. Task: lead names who reads qualify_stage.py in the desk repo, or says it is out of scope for the video.

18. **N5**: narrow claim vs closing card "80 kills, 0 doubled, 0 lost" and "13 min late" (run sheet :41). Status: UNKNOWN. List: GC-Q1. Notes: Deciding file: VIDEO-RUNSHEET.md (closing card position); the lead reads it. Decision 1 cuts scene 5 and the caption number, not the closing card. The phrase searches ("80 kills" 0 files; "0 doubled" 2 files; "0 lost" 3 files in the lane3 kill folder) are carried over from c6e, not re-run. Hits in COMPARE-demo.md:5 and RESULTS.md:100 are the demo column (n = 20). The third "0 lost" hit, PLAN-V3-ALERT.md:24, was not read (file NOT FOUND), so I do not claim "0 lost" occurs only in the demo column. No readable raw for "80 kills" (laptop files, v3 flows, 20-second lease). Task: lead answers Q1. If the card stays after scene 4, builder cuts "80 kills" or labels it "older test, v3 flows, 20-second lease, not re-checked" and reads PLAN-V3-ALERT.md:24 in full. If the card is cut, status becomes LATER VIDEO.

19. **c6b-1**: voided runs VOID-fl45k3b and VOID-fl45k6c. Status: CONDITIONAL. List: GC-Q2b. Notes: Condition: an "18 kill runs" count is captioned (Q2 = b and the count is kept). Not "nothing left": decision 1 cut the 60.1 to 61.9 s number, but the count caption may still stay in scene 4. Cause of the voids UNPROVEN: lane3 calls them "my slips" (RESULTS.md:2) without a cause. VOID-fl45k3b never reached an end state; its 338.7 s is the 330 s wait limit plus restart, not a measured recovery. VOID-fl45k6c failed with fakes_not_up. A reviewer inferred a second queue emptied the claim table (harness.py:261; lane3 harness NOT FOUND); overlap alone does not show it. Task: lead, if the count is captioned, asks lane3 to confirm the cause, or re-runs K3 at lease 45 s.

20. **c6b-2 / review-design m3**: "18 kill runs" hides n = 3 for the demo's K3. Status: CONDITIONAL. List: GC-Q2b. Notes: Condition: a run count is captioned. Counts per case 5, 5, 5, 3 test runs (lane3 file names). Task: builder gives the split if captioned.

21. **c6b-3**: run sheet :24 wrong K3 definition. Status: DUPLICATE (folded into F-007c). List: D. No separate task.

22. **c6b-4**: "80 kills, 0 doubled, 0 lost" has no readable raw; "0 lost" counts end state `unknown` as not lost (mf.py:83, carried over); 40 of 80 end `unknown` (carried over). Status: UNKNOWN. List: GC-Q1. Notes: Deciding file as N5. Task: see N5.

23. **c6b-5**: small differences (raw min 52.8 s vs caption 52.9 s; closing card line 3 n = 2, from n8n up). Status: UNKNOWN. List: GC-Q1. Notes: Deciding file: VIDEO-RUNSHEET.md (NOT FOUND): whether the 52.9 to 54.9 s caption stays in scene 4. Decision 1 cuts only "60.1 to 61.9 s". Task: if they stay, builder changes 52.9 to 52.8 and line 3 to "n=2 (K1), 6 test runs between 144.2 and 144.4 s, measured from n8n coming back up", or drops them.

24. **c6b-6**: 45 s lease supported only indirectly (flows imported from a local folder not in the repo; byte-identity not proven). Status: CONDITIONAL. List: GC-Q2b. Notes: Condition: scene 4 says "45-second lease" aloud or in a caption. Label 873a908a-film-v4-lease45 is a real commit; its mf-form.json and mf-recovery.json contain interval 45 seconds (carried over). Unexplained: at lease 120 s time from n8n up is about lease + 24 s, at 45 s about lease + 8 s. Task: lead accepts the indirect support or drops the words.

25. **c6b-7**: reviewer's point that the 45 s lease is only indirectly supported (agree). Status: DUPLICATE (folded into c6b-6). List: D. Notes: c6d named "c6b item 7" without a row. C/REPORT-c6b.md has six numbered findings; its review round's point 7 is the same as item 6. Rows that waited on item 7 now wait on c6b-6.

26. **review-design-3**: three test queues overlapped (run_all.progress lines 101-127); "lane" means two things. Status: CONDITIONAL. List: GC-Q2b. Notes: Condition: lane3 timings are captioned. Overlap may have stretched restart times. run_all.progress NOT FOUND. Task: builder says so if captioned; use "lane3" only for the session.

27. **review-design-4**: closing card "nothing lost, nothing doubled" claims too much. Status: UNKNOWN. List: GC-Q1. Notes: Deciding file: VIDEO-RUNSHEET.md (card position). If the card stays after scene 4 it is STILL OPEN. In the 18 kept result lines crm_rows is 1 and stage_calls is 1 in all, so "not shown to be doubled by these two fields". crm_upsert_events is 2 in 13 of 18, stage_requests 2 in all 18 (not explained); crm_rows is only the final state. "Nothing lost" fails for the mail in the K3B case (mail_to_intake 0, 5 of 5). Task: if the card stays, builder writes "no lead record lost or duplicated by the two final counts (crm_rows 1, stage_calls 1 in all 18); in 5 test runs the mail did not arrive and a person was alerted", plus the upsert count, or drops "nothing lost".

28. **review-design-5**: the 60.1 to 61.9 s range is one test program's repeatable timing. Status: DUPLICATE (folded into M1). List: D. Notes: The number is cut by decision 1 but still appears in the files, so it is not "nothing left"; the edit is the M1 edit. Section 7 applies.

29. **review-design-6**: alert timing not measured. Status: CONDITIONAL. List: GC-Q2b. Notes: Condition: scene 4 keeps the kill cases. See section 7. Task: builder checks scene 4 wording against section 7.

30. **review-design M3 warning**: do not attribute "may or may not have gone" to the 18 lane3 runs. Status: DUPLICATE (folded into F-007e). List: D.

31. **F-020a**: stage journal has two names; the take uses stage.journal. Status: STILL OPEN. List: H-5. Notes: stage_server.py is the older prototype; the take uses a rebuild (PLAN-4:64-80, carried over); neither is in this tree. Housekeeping because the name is not filmed; becomes G if a take text the owner reads uses the other name. Task: builder uses one name, stage.journal, in take texts only; do not move the journal before the video.

32. **F-020b**: the harness's name stage-journal.jsonl. Status: LATER VIDEO. List: A. Belongs to the film-v4 harness. Archive; no more rounds.

33. **F-022**: desk doors' 502 path never reaches the error workflow. Status: NOT IN TAKE (author reading). List: A. Notes: The desk doors are retired under F-019 (not read; the fact comes from C/REPORT.md). The finding's own fix text is wrong ("Reply 2xx" is also the success reply). mf-form real-v5 :238-295 only sets n8n_error:false, so take flows do not repeat it (carried over). Task: retire the doors; no patch. Lead confirms the doors are not imported (part of N1).

34. **F-023**: claim-table-screen READMEs disagree about "NOT run" (v1 README; v2 :3, :48, :51; DOUBTFUL-SCENE.md:13). Status: NOT IN TAKE (author reading). List: A. Notes: The run sheet forbids saying it works. Decision 9 replaces the live claim-table screen by a screenshot or node preview, so these READMEs are not on the filmed path; but D9 now needs the screenshot (see D9). Files NOT FOUND. Task: lead asks the laptop agent first; then one dated run; then texts agree.

35. **F-025**: v1-superseded recovery re-claims forever (30 s sweep, 20 s lease; no attempts cap, no alert). Status: LATER VIDEO. List: A. Notes: Kept "for the compare only". Task: builder archives per CUT-LIST.md (NOT FOUND) and updates C/REPORT.md:33, :526-528 and DESIGN-A-README.md:3 (NOT FOUND).

36. **N6**: door node name "Reply error". Status: NOT IN TAKE (author reading). List: A. Notes: Same doors as F-022; F-022 and N6 rest on F-019, which I did not read. No task for the video.

37. **D2 (decision 2)**: the take never deletes contacts; the owner deletes leftovers by hand. Status: DECISION ANSWERED / FILES NOT UPDATED. List: G-7. Notes: Stale text still says the program or the key deletes contacts, in every version from v4 to v8 (phrase search for "program deletes", "deletes this run", "create and to delete", "to archive", "delete right"; other wording may exist). v4: :96 ("type end ... to archive"), :98 (key may be unable to delete, expect to delete by hand), :179 (open question 5). v5: :127 ("The program then deletes this run's contacts"), :130. v6: :135-136 (step 0 "the program deletes this run's HubSpot contacts at the end"), :206. v7: :136, :137 ("The key needs permission to create and to delete contacts"), run card row 14 (:57, scope names), :223, :226. v8: :155, :157 (same sentence), run card row 14 scope names, :247, :250. v9 is changed: :288 (F.3) says "The program does not delete contacts" and the owner deletes by hand; :169 says the program never deletes and the key needs read, create and change only. v9 :166 and :169 still have step 0 try one delete of the check's own made-up contact; whether that fits decision 2: the lead confirms with Q7 (the check is not the take). v9 :285 says the program's older text may say "to archive". QUESTIONS.md item 1 (delete right for HubSpot app 1) is answered by decision 2. Task: builder removes the "key needs delete permission" and "program deletes" statements from every version still in use, or confirms by Q10 that v9 is the only one the owner reads and archives v4 to v8. Lead closes QUESTIONS.md item 1 as answered and confirms the step 0 delete line (v9). "F-01" in the lead's note has no entry in the c6 files; may be A-01 or C-01 (decision 4); if another finding: UNKNOWN, deciding file flows-audit FINDINGS.md (NOT FOUND; H/evidence/silent-exit/FINDINGS.md is a different document).

38. **D10 (decision 10, first half)**: which OWNER-STEPS version the owner reads. Status: DUPLICATE (folded into D2 and Q10). List: D. Merged into D2; the version question is Q10.

39. **D10-archive (decision 10, second half)**: v3 archived, never deleted. Status: STILL OPEN. List: H-6. Notes: Correction of c6e: OWNER-STEPS-realrun-v3.md IS found, at H/core-hardening/inputs/OWNER-STEPS-realrun-v3.md. It is still a live file in the inputs folder, so it is not yet archived. Found in H/core-hardening/steps-edits/: realrun v4 to v9, OWNER-STEPS-v4-difflist.md, v6-OPEN-FOR-LEAD.md. Task: builder moves or copies v3 to an archive folder, writes one archive line in the handoff (location), never deletes.

40. **K3B mail before the kill**. Status: UNKNOWN. List: GC-Q2b. Notes: The data file has no field; only RESULTS.md Part 4 says "mail not delivered". Lane3 harness NOT FOUND. Deciding file: the lane3 harness. Task: lead asks the lane3 session or reads the harness.

41. **N7**: "13 min late" line and a later faster alert. Status: UNKNOWN. List: GC-Q1. Notes: Two carried-over claims that conflict with section 7. The closing card says an alert can be 13 minutes late (n = 2, older tests). c6e cited "lane3 REPORT.md:18" for a faster alert (alert at 60 s, 3 of 3, not adopted in the demo flows). I could not open that file: lane3 REPORT.md NOT FOUND (only C/raw-lane3/RESULTS.md exists). Section 7 says alert timing is not measured, so the "faster alert" claim is carried over and unverified, and the card's "13 min late" may state an old problem as current. No alert time may be captioned either way. Task: lead keeps or drops "13 min late" (REPORT-c6b question 5) and says where lane3 REPORT.md is.

42. **N8**: "HB194" name. Status: STILL OPEN. List: H-4. Notes: HB194 appears only in commit 2595b8c3's message; best match RESULTS.md Part 3 lines 83-92 (inference). Block not read. A caption or page should not use a name nobody can look up. Task: builder cites "demo3/kill/RESULTS.md, commit 2595b8c3" (file C/raw-lane3/RESULTS.md) (REPORT-c6b question 4).

43. **N9**: housekeeping items without row ids in c6d. Status: DUPLICATE (folded into F-006, F-003, H-1). List: D. Notes: Now fully covered by the F-006 and F-003 rows and H-1 (DECISION-one-store line 14, unconditional, section 4). The earlier conflict (F-011 said "after re-smoke", N9 said "now") is closed: the edit is now.

44. **P1**: the plan names film-v5 (plan :120, :236, :284, :298, :543). Status: DECISION ANSWERED / FILES NOT UPDATED (decision 1; lead's answer Q15.1). List: G-1. Notes: The plan fills film-v5; the one video is real-v5 only. The plan edit is given as text in section 4; I run nothing. Task: lead decides; builder edits plan-wp6-resmoke-v5.md.

45. **D5a (decision 5)**: S9 items (S9-5 and S9-12 apply as text; S9-3 text; S9-2 keep with the honest sentence that the program does not print the figures; S9-1 and S9-4 describe-only). Status: STILL OPEN. List: G-14. Notes: Partly done in v9: the v9 glossary line :22 says the program does not print the spending backstop; :399 says "Not shown: nothing can spend before both typed answers"; :400 says the S9-4 design is described but not built; :402 says the program does not print the backstop or the money spent. Not checked: S9-5, S9-12 (rules A, E, F, I not overridable mid-take, lead reads only masked outputs) and S9-3 (owner revokes the model key at clean-up) in v9. The lead's 10:13 UTC answer Q15.4 says the spending limit stays by owner eye plus the stage program. Task: builder checks S9-5, S9-12, S9-3 are in v9 as text and S9-2's sentence matches.

46. **D5b**: decision 5 versus decision 7. Status: STILL OPEN. List: G-14. Notes: Decision 5 refuses "lead activates flows after the owner's typed y" and any claim that nothing can spend before both typed answers; decision 7 has the lead import and activate the flows. v9 :399 says the flows and the model program are started by the lead before y, which fits both. Not checked: any other text that says the lead activates after y. Task: lead answers Q6. Builder phrase-searches the owner steps and plan for "after" y wording.

47. **D6 (decision 6)**: ports. Status: DECISION ANSWERED / FILES NOT UPDATED. List: G-12. Notes: The rehearsal port 5690 is in the plan (:121, :148). The real take's own free port is named nowhere I found: phrase search for "own free port" and "5678" gave 0 hits in v9 and the plan. Stale-port check: no text may use 5678 or 5679 (the owner's own). Task: builder names the take port once in the plan and runs the stale-port check on the take texts. Lead chooses the port.

48. **D8 (decision 8)**: real-account smoke replaced by loopback re-smoke plus ONE made-up lead in take prep. Status: STILL OPEN. List: G-13. Notes: Plan phrase search "made-up lead", "one lead": 0 hits (whole plan). v9 :396 describes the rehearsal and :147 describes step 0's 7 HubSpot calls to the CRM test account; whether step 0 is the removed check set is Q7. Task: builder writes the text once Q7 is answered. Lead answers Q7.

49. **D9 (decision 9)**: counts proof screen = rehearsal screenshot or Postgres node preview. Status: STILL OPEN. List: G-11. Notes: v9 :35 already defines the proof screen as a screenshot from the rehearsal or the Postgres node preview. Who produces it is not stated in any file I read (Q8). F-023 says "not in take", which conflicts only if the screenshot depends on the live claim-table screen; it does not. Task: lead answers Q8 and produces the screenshot in the rehearsal.

50. **D11 (decision 11)**: licence copies are never overwritten or re-licensed; BRANCH ARTEFACT. Status: DECISION ANSWERED / NOTHING LEFT. List: H-9. Notes: Read: H/core-hardening/patch-test-runs/FAIL-CAUSE.md :41 records "BRANCH ARTEFACT" for the licence test. Out of scope for the video. No task.

51. **D12 (decision 12)**: the lead runs the first laptop rehearsal after the loopback re-smoke passes. Status: STILL OPEN. List: G-2. Notes: Sequence in section 3. Target tonight or tomorrow morning IST (about 12:30 UTC on 16 Nov to 06:30 UTC on 17 Nov); times go in the handoff. Who runs the re-smoke: Q3. Task: lead puts the real times in the handoff.

52. **CS1**: clean start before the take (lead's answer Q15.2). Status: DECISION ANSWERED / FILES NOT UPDATED. List: G-10. Notes: Lead step in take prep: fresh made-up lead ids never used in the rehearsal, and the lead empties the claim table `mf_leads` in the rehearsal database before the take. Phrase search "mf_leads", "fresh lead" in v9: 0 hits. Task: builder adds one numbered row to the owner/lead steps (v4 and later); owner of the step = lead.

53. **CL1**: claim sentence (lead's answer Q15.3). Status: DECISION ANSWERED / FILES NOT UPDATED. List: G-9. Notes: Narrow claim: "a lead sent twice with the same id inside the lease is processed once"; lease-expiry behaviour as an honest sentence (section 7). Not checked: whether run sheet, page and owner steps already use this sentence. Task: builder puts the sentence and the honest sentence into the claim text.

54. **ROLE1**: the role tests (T-ROLES, group L, S1b). Status: UNKNOWN. List: G-15. Notes: T-ROLES is not found in plan-wp6-resmoke-v5.md by phrase search (carried over: c6e said it may be the same as the parked proposal). Decision 3 parks the four-login proposal and says read-only group L is not run; S1b (three roles) is a different item still in the plan (:73, :277). Reconciliation: "three roles" = S1b in the re-smoke; "four logins" = the parked proposal. Task: lead answers Q4 and Q5.

55. **Z1a**: core SDK patches (A-01 deferred, C-01 extras cut, 54 mutants, C7/C8 lanes tied to them). Status: DECISION ANSWERED / NOTHING LEFT (decisions 3 and 4). List: H-10. Notes: Core SDK is not on the take path. Not in the c6 files; named because the zoom-out lane flagged them. The lead's 10:13 UTC answer Q14 confirms: A-01 deferred, C-01 extras cut. No task.

56. **Z1b**: G5 wording edit (decision 4: G5 wording kept, text only). Status: UNKNOWN. List: H-7. Notes: The text of G5 and where it lives are not defined in any file I read. Whether the edit has been made: not checked. Task: lead names the file that holds the G5 wording; builder confirms or makes the edit.

57. **Z1c**: minimal price/max_tokens check "only if the take's model program loads Route config". Status: CONDITIONAL. List: GC-route. Notes: Condition: the take's model program loads Route config (unverified, not in the video path, decision 4). If false: nothing. Task: lead says if the program loads Route config.

LATER VIDEO archive note (one line for all LATER VIDEO and archive rows: F-020b, F-022, F-023, F-025, N6): the film-v4 and film-v5 stand-in scenes are a possible later video; their notes stay in C/ and H/core-hardening/ unchanged, no further review round is spent on them, and they are reopened only when that video is planned. Rows kept above for scene 4 stay only because scene 4 may still use lane3 numbers (Q1, Q2).

## 6. Naming table (cases)

| demo name (page, run sheet, mf.py) | lane3 file name | what happens | basis |
|---|---|---|---|
| K3B | K3 | killed when the mail connection opens; the mail did not arrive in the test (stand-in mail service); end state `unknown`, one alert | RESULTS.md Part 4 and :97 (C/raw-lane3/RESULTS.md); mf.py:153-158 carried over (NOT FOUND) |
| K3 | K6 | killed after the mail was stored; the mail arrived once; end state `unknown`, one alert | same; mf.py:159-164 carried over |
| K1, K2 | K1, K2 | same names; meaning not defined in any file I read (observed end state done, mail 1, alert 0, in 5 test runs each) | C/evidence-lane3-recompute.md |

Wording rule: scene 4 says "killed when the mail connection opens" (RESULTS.md's own words) for K3B, never "killed after the mail left" and never "before the table was updated". In both K3B and K3 the CRM contact was already written at the kill (CRM flag "t", C/evidence-lane3-recompute.md section 6), which is a CRM fact; the state of the claim table at the kill is not in the data.

All lines are film-v4 stand-in results. Whether the same cases give the same results on real-v5 is open (Q2).

## 7. Rules that apply to every scene-4 caption
- A time may be said only as "about a minute, in the test", with no decimals, until the lead accepts a labelled number (Q9; the rounding is mine, not the lead's). No caption says "alert within a minute": alert timing is not measured (counts taken after a 20-second wait, harness.py:341, per the c6b review; harness NOT FOUND). This also holds for the carried-over "faster alert" claim in N7, which is unverified: no alert time is captioned at all, fast or slow.
- "Nothing lost" is not claimed for the mail in the K3B case (section 8).
- Every lane3 number carries the label "stand-in flows, film-v4, 45-second lease, one machine, made-up data" until a real-v5 run exists (Q2).
- The claim is "a lead sent twice with the same id inside the lease is processed once"; no caption claims more.
- Honest sentence for the claim text (lease expiry; lead's answer Q15.3): "This is shown for a second send that arrives while the lead record is still reserved (inside the lease). If the second send arrives after the lease has run out, the recovery sweep may treat the lead record as free again; this video makes no claim about that case, and I found no measured result for it." The second half is my wording of what the files show: no measured lease-expiry result found.

## 8. Recomputed numbers (basis: evidence runner's recompute of results.jsonl, 128 result lines, C/evidence-lane3-recompute.md, not re-checked by me; (H) = hand recompute by the c6b reviewer)

All numbers are film-v4 stand-in results (lane3), not real-v5.

| quantity | value | field name |
|---|---|---|
| lease-45 result lines (lines with a 45 s lease) | 23 = 18 kept + 2 voided + 3 error-case lines | flows, point, label |
| kept test runs per case, lane3 file names | K1 5, K2 5, K3 5, K6 3 | point |
| kill to end state | min 60.1, max 61.9, median 60.85 seconds (number cut by decision 1; do not caption) | kill_to_final_s |
| kill_to_final_s vs restart_s + recovery_s | largest difference 0.1 s | restart_s, recovery_s |
| restart (H) | 6.6 to 8.8 s | restart_s |
| recovery (H) | 52.8 to 54.9 s | recovery_s |
| CRM upsert calls seen | 2 calls in 13 of 18 test runs (K2 5, K3 5, K6 3); 1 call in the 5 K1 test runs | crm_upsert_events |
| final CRM contacts | 1 in all 18 test runs | crm_rows |
| model-stage calls | 1 call in all 18 test runs | counts.stage_calls |
| stage requests | 2 requests in all 18 test runs (not explained) | stage_requests |
| intake mails at the end (mails at the intake address) | K1 1, K2 1, K3 0 (5 of 5 test runs), K6 1 (3 of 3; total_mails 2, my reading: intake mail plus alert mail, not confirmed) | counts.mail_to_intake |
| end states (H) | K1, K2 done (10 of 18 test runs); K3, K6 `unknown` with 1 alert (8 of 18) | states |
| voided runs | VOID-fl45k3b: 17:09:59Z to 17:16:35Z (22:39:59 to 22:46:35 IST), never terminal, 338.7 s, no error text; VOID-fl45k6c: error fakes_not_up | label |
| test runs attempted at lease 45 (H) | 20 (K1 5, K2 5, K3 6, K6 4); the 20 counts the two voided runs and excludes the 3 error-case lines | label, point (one result line per attempted test run) |

Not found: "80 kills" (0 files in the lane3 kill folder; carried over); any mail field before the kill. File-name to demo-name mapping and "mail not delivered" come from RESULTS.md Part 4 text only; there is no "K3B" label in results.jsonl.

## 9. Failures, uncertain items, not checked
1. Closing card position and scene 4 content are not stated in any file I could find; many rows depend on them (Q1, Q2).
2. Nothing re-checked against raw files; nothing run. C/raw-lane3/ not re-opened in this pass except RESULTS.md :97 and a grep of the recompute file. Real-v5 flow JSON not read; no real-v5 same-id-twice result found (section 2). Carried over, not re-verified, and marked per row: the M2 "0 hits" claim, the N7 faster-alert claim, the nine K3 lines of the run sheet, the "80 kills" phrase counts, F-011's SQLite state, the number 8 of built flows.
3. NOT IN TAKE for F-022, F-023, N6 is my reading, not a decision.
4. NOT FOUND under H by Glob/find: VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md, flows-audit FINDINGS.md (only H/evidence/silent-exit/FINDINGS.md exists, a different document), folder flows-audit and its EXCEPTIONS.md, CUT-LIST.md, COMPARE-demo.md, DESIGN-A-README.md, PLAN-V3-ALERT.md (H/studio-notes/plan-v3.md exists; relation not checked), N8N-START.md, PLAN-4-NLITE-FROM-LEAD.md, DOUBTFUL-SCENE.md, V7-NUMBERS-lead-read.md, stage_server.py, qualify_stage.py, mf.py, lane3 harness.py (two other harness.py under H/core/evidence/realrun-v6/standing/), lane3 REPORT.md (the cite REPORT.md:18 in N7), run_all.progress, the F-003 patch, project plan v5 (only plan-wp6-resmoke-v5.md found), the take's scripts\n8n_api.py (test copies under H/core/evidence/r7u-chain/). Cites into these files are carried over, unverified.
5. Correction of c6e: OWNER-STEPS-realrun-v3.md was reported NOT FOUND under H; it exists at H/core-hardening/inputs/OWNER-STEPS-realrun-v3.md (row D10-archive).
6. Found and used: H/core-hardening/inputs/ (DECISIONS-2026-11-16.md, DECISION-one-store.md, plan-wp6-resmoke-v5.md, FACTS-ALREADY-DONE.md, OWNER-STEPS-realrun-v3.md), H/core-hardening/steps-edits/ (OWNER-STEPS realrun v4 to v9, v6-OPEN-FOR-LEAD.md, EDITS.md), H/core-hardening/QUESTIONS.md, H/core-hardening/ORDERS.md (answers of 10:13 UTC), H/core-hardening/patch-test-runs/FAIL-CAUSE.md (one line), H/ledger.md and H/reviews/ledger.md (existence only), C/raw-lane3/ (results.jsonl, RESULTS.md, recompute files), C/REPORT.md, REPORT-c6b.md, REPORT-c6c.md, review-design.md, review-codebase.md, resolve-r1.md, H/core-hardening/cross-read/ZOOM-OUT-not-checked.md. C/raw-c6e-checks.txt exists and was not read in this pass.
7. The bible is not on disk as a text I read, so R460 could not be checked.
8. The zoom-out lane raised gaps no c6 review covers and I did not work on (they need new checks, not text edits): claim-table entries that may persist between rehearsal and take (CS1 now covers the clean start); real HubSpot search delay not exercised (loopback stub); real model call path not run before the take, credit window ends 23 Nov 2026, 18:29 UTC = 23:59 IST; the proof screen's database and mail grouping; nobody checks the recording for leaks (mailbox address, credentials page, token prefix, port); unrun tools on the critical path; a full timed take-day sequence. Lead: decide which get a review agent before the take.
9. Not checked in c6e and still not checked: scenes 1 to 4 (run sheet absent), the full DECISION-one-store text beyond line 14 and the lines I quoted, and the S9-5, S9-12, S9-3 text in v9 (row D5a).

## 10. Glossary (one plain sentence each; "not defined" = the files I read do not define it)
- run sheet: VIDEO-RUNSHEET.md, the scene-by-scene script of the video; NOT FOUND in this tree.
- page: PAGE-STATEMENTS-V4.md, the text of the web page that goes with the video; NOT FOUND.
- caption: text shown on screen in a scene of the video.
- closing card: the last on-screen card of the video (its position relative to scene 4: Q1).
- kill cases: crash tests where n8n is stopped while it processes a lead record (cases K1, K2, K3, K3B, K6); see section 6.
- demo: the earlier film-v4 demo whose case names (K3, K3B) the page and run sheet use; "the demo column" in COMPARE-demo.md and RESULTS.md means that demo's own numbers (n = 20).
- n8n: the workflow tool that receives the lead records and runs the flows.
- flows audit: the earlier audit of the n8n flows (C/REPORT.md and C/review-design.md); its numbered findings are F-xxx and M/N items.
- c6d, c6e: earlier versions of this report (REPORT-c6d.md, REPORT-c6e.md); c6f is this one.
- zoom-out lane: the review agent that looked at the whole project and listed what no review covers (H/core-hardening/cross-read/ZOOM-OUT-not-checked.md).
- M1, M2, M3, N1 to N6: numbered items of the flows audit review (C/REPORT.md, C/review-design.md). N7, N8, N9, D2, D10, P1, Z1, D5a to D12, CS1, CL1 and ROLE1 are row ids given in reports c6c to c6f; which report first named each: not checked.
- F-003, F-006, F-007, F-008, F-011, F-019, F-020, F-022, F-023, F-025: numbered findings of the flows audit; full text NOT FOUND; only parts quoted in C/REPORT.md are known to me.
- c6b-N (c6b item N): numbered points of C/REPORT-c6b.md (lane3 numbers against captions).
- A-01, C-01: two core patches named in decision 4 (A-01 deferred, C-01 extras cut).
- K1, K2, K3, K3B, K6: crash-test cases; see section 6. Meaning of K1 and K2: not defined in any file I read.
- lane3, lease, alert, end state `unknown`: see section 1.
- stage: the program step that asks the model to qualify a lead record (stage_server.py, Q.qualify); the take's version is a rebuild not in this tree.
- stage journal / spend ledger: files kept by the stage step; the journal is a write-ahead guard that records a model call before it is made (DECISION-one-store item 4); exact spend-ledger contents not defined.
- doors: the n8n flows desk-form-door.json and desk-webhook-door.json that pass a request to "the desk" (not defined). Retired under F-019 (not read).
- ledger: the list of open problems (H/ledger.md while the handover folder exists); "ledger it" means write one row there.
- T7b: a privacy test (name, e-mail, key and mail password must not appear in stored places); file not found.
- S1b: step S1b of the loopback re-smoke plan (plan-wp6-resmoke-v5.md :277): set up Postgres with three roles (smk_n8n, smk_app and a read-only count role) and run negative tests N1 to N10.
- T-ROLES: named in c6e as a test that database logins get "permission denied" where they should; not found in the plan by phrase search; whether it is part of the parked proposal: UNKNOWN (ROLE1).
- group L: "read-only group L" in decision 3, not run before the video; not defined in any other file I read.
- G5: "G5 wording keeps (text only)" in decision 4; the wording itself is not defined in any file I read (Z1b).
- V7: laptop files (V7-NUMBERS-lead-read.md, mf_result_*.json) behind the "80 kills" numbers; not in any git branch.
- loopback re-smoke: a one-off manual run of real n8n 2.46.6 on the laptop's loopback address only, made-up data, no real accounts, US$0 (plan-wp6-resmoke-v5.md); not the take.
- mail_to_intake, crm_rows, crm_upsert_events, stage_calls, stage_requests, total_mails: counts in results.jsonl; see section 8.
- R460: the rule behind this audit; text not available.

(End of REPORT-c6f.md text. Note for the saver: the findings table above is written as numbered entries for readability. Convert to the five-column table of section 5 if the pipe-table format is wanted. The columns are id and finding, status, list, notes, task.)
