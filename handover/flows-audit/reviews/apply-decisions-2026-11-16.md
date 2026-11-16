# Apply lead decisions 2026-11-16 to the flows-audit documents (builder log, static text edits, nothing ran)

## Failures and unsure items (first)

- FAILED: none (all 56 scripted edits matched exactly once; 0 misses). Nothing was run except a text-replace script and grep.
- UNSURE 1: decision 1 makes F-005, F-006 (scene 5/6), F-013, F6B-13, F6B-08 etc. refer to scenes that are no longer in the video. I added a marker sentence and did NOT change any severity or count (the lead or the rating owner decides whether those rows become Nit or not-in-take). Severity counts in FINDINGS.md (line 71 'Counts after ORDER 007') are therefore unchanged and may now overstate take-reachable Blockers/Majors. Not recounted: a recount needs a rating decision, not a script.
- UNSURE 2: I changed one count: 'the 8 files in real-v5 and film-v5' became 'the 4 files in real-v5' (FINDINGS.md lines 7 and the F-008 row). Counted with ls: n8n-flows-real-v5 holds 4 .json files (mf-form, mf-hook, mf-recovery, mf-sub-crm-mail). The sentence 'about four steps in five are old copies' and '655 steps / 525 / 40 files' were left unchanged (they are counts of all folders, which this decision does not change; not recounted).
- UNSURE 3: the 'A-01 / C-01 extras' (decision 4), 'S9 items' (decision 5), 'port 5678/5679/5690' (decision 6), 'n8n owner setup' (decision 7), 'real-account smoke checks a to f' (decision 8) have NO hit in the files I was allowed to edit (grep for S9-, A-01, C-01, G5, 200_000, nothing can spend, both typed, 5678, 5679, 5690, owner account, first visit, checks a to f). They appear only in CLAIMS-TABLE.md, RUNSHEET-WORDING.md, fill_flows/, flow-check/, roles-coverage-check/ (other agents) and in inputs/ copies. I did not grep those excluded files on purpose.
- UNSURE 4: patches/*.patch bodies were NOT edited. A diff hunk is not safe to edit by hand (it would stop applying). See LEAD-TO-APPLY item P1.
- NOT CHECKED: FLOWS-AUDIT.md (1 MB), lanes/, lanes7/, lanes13/, patch-apply/, heavy-test-lane/, handover/ subfolder, reviews/ older review files, the fix-*.md, evidence-*.md, review-*.md and checkpoint files. Reason: 30-minute limit; they are history of what each agent found at the time (kept as written), not statements of the plan. FLOWS-AUDIT.md summary parts: not read. Next step: a second pass over FLOWS-AUDIT.md first 200 lines and lanes13 if the lead wants them aligned.
- OVERLAP NOTE: ORDER 023 and 024 (switch EGM planning skills to Fable and back) are not part of my brief; I did nothing for them.

## Table: decision / files checked / hits / edited / not applicable
| # | Decision | Files checked | Hits | Edited | Result |
|---|---|---|---|---|---|
| 1 | Real-v5 only, scenes 1-4; no film-v5 scenes, flow-set switch, scene 5, caption '60.1 to 61.9 s' | FINDINGS, FIX-PLAN, CUT-LIST, EXCEPTIONS, QUESTIONS, LEDGER-ROWS, F6B-AUDIT, F6-AUDIT, REPORT, QUEUE, STATUS-BOARD, PLAN-002, PLAN-005, SCENE-FLOW-MAP, ID-VID-CHECK, CITATION-TRIAGE/FIXES, README, patches headers | about 100 lines | see the edit log (items tagged 1); total 56 edits over 12 files, per-file counts at the end | done; patches not edited (P1) |
| 2 | Take never deletes contacts | all above | QUESTIONS.md line 38 only (+ F-044/other clean-up rows concern n8n runs and table rows, not contacts) | 1 (QUESTIONS.md line 38) | done; OWNER-STEPS v3 lines 104, 112 need change (LEAD-TO-APPLY) |
| 3 | ROLES parked | all above | FINDINGS T-ROLES line 21, QUESTIONS Q11, STATUS-BOARD 14/18 (already says parked) | 2 (FINDINGS T-ROLES, QUESTIONS Q11) | STATUS-BOARD already correct |
| 4 | C5 A-01 deferred, C-01 extras cut, G5 text kept, 200_000 moot | all above | 0 | 0 | not applicable in editable files |
| 5 | S9 items wording | all above | 0 ('nothing can spend before both typed answers' not found) | 0 | not applicable; found in inputs/OWNER-STEPS-realrun-v3.md line 97 (marker file after both typed answers; read-only copy, LEAD-TO-APPLY) |
| 6 | Ports: rehearsal 5690 | all above | 0 | 0 | not applicable (only inputs/plan-wp6-resmoke-v5.md has ports, and it already says 5690/5691) |
| 7 | n8n owner setup already done | all above | 0 | 0 | not applicable; inputs/OWNER-STEPS-realrun-v3.md line 75 asks the owner to open n8n on port 5678 (LEAD-TO-APPLY) |
| 8 | Real-account smoke replaced by loopback re-smoke plus one made-up lead | all above | 0 'checks a to f' | 0 | not applicable |
| 9 | Counts proof screen = rehearsal screenshot or node preview | FINDINGS 43, FIX-PLAN 22, LEDGER-ROWS F-023, SCENE-FLOW-MAP 46/72 | 5 | see edit log (items tagged 9) | already consistent; scene 10 is also cut by decision 1 |
| 10 | 'one Postgres server with two databases (n8n's own and the take's)' | FINDINGS, EXCEPTIONS, FIX-PLAN, LEDGER-ROWS, QUEUE, PLAN-002, QUESTIONS Q4 | about 15 | see edit log (items tagged 10) | done; DECISION-one-store line 14 is outside scope (LEAD-TO-APPLY) |
| 11 | Licence copies, BRANCH ARTEFACT, patch tests on clean tree | all above | 0 | 0 | not applicable |
| 12 | First laptop rehearsal by the lead after loopback re-smoke | all above | 0 | 0 | not applicable |

Per-file edit counts come from the script log below.

## LEAD-TO-APPLY (outside handover/flows-audit editable set)
- L1. DECISION-one-store.md line 14 (original in egm/duplicate-proof-lead-desk and in handover/system-map/decisions; copy at handover/flows-audit/inputs/DECISION-one-store.md line 14, which I left untouched as a lead input). Old: '**ONE database for everything we own: the single Postgres instance of the take** (one container, one engine). n8n's internal data in its own schema or database, our claim table `mf_leads` in an `app` schema, ...'. New first words: '**One Postgres server with two databases (n8n's own and the take's)** for everything we own (one container, one engine). n8n's internal data sits in n8n's own database; our claim table `mf_leads` sits in the take's database (`app` schema), ...' (lead decision 2026-11-16 item 10).
- L2. OWNER-STEPS v3 -> v4: archive v3 (never delete). v4 must change: line 75 (n8n first-visit/owner setup and port 5678: setup is already done, FACTS-ALREADY-DONE.md; the lead imports and activates flows with scripts/n8n_api.py; owner types y, the challenge and end; rehearsal port 5690; the real take uses its own free port, 5678/5679 are the owner's own) (items 6, 7); lines 104 and 112 (the take archives/deletes contacts: now the take deletes none; owner deletes leftover made-up contacts by hand in HubSpot after the take, from a list by lead key and contact id) (item 2); line 97 (any 'nothing can spend before both typed answers' sentence is not allowed unless a closed gate exists) (item 5); any real-account smoke step (item 8).
- L3. VIDEO-RUNSHEET.md (handover/demo): lines 4, 11, 12, 33, 39, 41, 50, 62, 82, 85, 90 and scene 5 to 11 rows: cut scenes 5-11, remove 'scenes 1 to 5', remove caption '60.1 to 61.9 s' (decision 1). Owner of that file: lead / RUNSHEET-WORDING agent.
- L4. Patches: patches/F-003-runsheet-claims.patch (lines 8, 18, 19, 29, 31, 38, 45, 51, 67 mention scene 5, film-v4 K1 figure and the '60.1 to 61.9 s' range) and patches/F-004-page-statement-17.patch (lines 13, 35 insert 60.1 to 61.9 s) must be regenerated against the 4-scene, real-v5-only sheet; do not apply them as they stand. Likewise 'rebuild real-v5 and film-v5' for F-002.
- L5. handover/demo/n8n-flows-film-v5 stays (not archived) because film-v5 scenes are a possible later video (CUT-LIST.md line 2 now says so).
- L6. Decision 2 against the desk repo: scripts/run_real_check.py:993 and :1101-1107 call archive_all and crm_hubspot.py:492-499 sends DELETE (QUESTIONS.md line 38). The take must run with that off or the claim 'never deletes contacts' is false; lead to say which script and option (still open, needs the lead).
- L7. CLAIMS-TABLE.md, RUNSHEET-WORDING.md, fill_flows/, flow-check/, roles-coverage-check/: not touched by me (other agents); they carry the same decisions to apply.

## Edit log (old text kept here; every new sentence carries the marker '(lead decision 2026-11-16 item N)')

- OK | FINDINGS.md | item 1,9 | count 1 | OLD: `The filmed run uses the 8 files in n8n-flows-real-v5 and n8n-flows-film-v5, plus the table screen (1 file)`
- OK | FINDINGS.md | item 1 | count 1 | OLD: `made with the files in n8n-flows-real-v5 and n8n-flows-film-v5. `
- OK | FINDINGS.md | item 1 | count 1 | OLD: `The numbers 60.1 to 61.9 s, 18 runs, 13 minutes and 144.3 s are relayed, not seen.`
- OK | FINDINGS.md | item 1 | count 1 | OLD: `The film set exists because the real CRM cannot be told to refuse (scene 5, run sheet risk 7).`
- OK | FINDINGS.md | item 10 | count 1 | OLD: `the lead decided (ORDER 004) it moves into the same Postgres, and`
- OK | FINDINGS.md | item 1 | count 1 | OLD: `**Scene 6 says the intake list is still empty, but n8n answers only after the mail step.**`
- OK | FINDINGS.md | item 1 | count 1 | OLD: `**Scene 5 uses the stand-in CRM, which only the film flows have; the sheet says the real CRM is used in scenes 1 to 5.**`
- OK | FINDINGS.md | item 1 | count 1 | OLD: `statement 20 gives 60.1 to 61.9 s at 45 s;`
- OK | FINDINGS.md | item 10 | count 1 | OLD: `**n8n keeps its own state (workflows, credentials, run history with lead name and e-mail) in its own SQLite file, not in the take's one Postgres.**`
- OK | FINDINGS.md | item 10 | count 1 | OLD: `**The audit text says 'one database' in 15 different ways.**`
- OK | FINDINGS.md | item 1 | count 1 | OLD: `film-v5 mf-sub-crm-mail.json (3 reads)`
- OK | FINDINGS.md | item 3 | count 1 | OLD: `T-ROLES = tests proposed in lanes7/N7-new-findings.md.`
- OK | FINDINGS.md | item 1 | count 1 | OLD: `all 8 files in n8n-flows-real-v5 and n8n-flows-film-v5 (settings)`
- OK | FINDINGS.md | item 1,9 | count 1 | OLD: `scene 10 table screen (never run in n8n).`
- OK | FIX-PLAN.md | item 1 | count 1 | OLD: `rebuild real-v5 and film-v5 with the V5-README commands`
- OK | FIX-PLAN.md | item 10 | count 1 | OLD: `The one-database wording to use is the conditioned paste in EXCEPTIONS.md.`
- OK | FIX-PLAN.md | item 9,1 | count 1 | OLD: `scene 10 uses a rehearsal screenshot or the Postgres node preview.`
- OK | CUT-LIST.md | item 1 | count 1 | OLD: `The take uses only n8n-flows-real-v5 and n8n-flows-film-v5 (ORDER 003).`
- OK | EXCEPTIONS.md | item 10 | count 1 | OLD: `the lead decided Reading A (ORDER 004): n8n's own state moves into the take's Postgres (DB_TYPE=postgresdb)`
- OK | EXCEPTIONS.md | item 10 | count 1 | OLD: `KEEP-ONE = the one database for the take (n8n Postgres, table mf_leads).`
- OK | EXCEPTIONS.md | item 10 | count 1 | OLD: `> One database. For the filmed run, everything we keep about leads and the workflow lives in one Postgres server:`
- OK | EXCEPTIONS.md | item 10 | count 1 | OLD: `They sit in two separate places in that server,`
- OK | LEDGER-ROWS.md | item 1 | count 1 | OLD: `Scene 5 uses the stand-in CRM, which only the film flows have; the sheet says the real CRM is used in scenes 1 to 5`
- OK | LEDGER-ROWS.md | item 10 | count 1 | OLD: `The audit text says 'one database' in 15 different ways`
- OK | LEDGER-ROWS.md | item 1,9 | count 1 | OLD: `Table screen (filmed in scene 10 of the run sheet): README claims conflict on whether it was run live`
- OK | QUESTIONS.md | item 1 | count 1 | OLD: `Q6 ANSWERED: 'a stand-in CRM' on screen for scene 5; 'HubSpot' only for scenes that use real-v5.`
- OK | QUESTIONS.md | item 1 | count 1 | OLD: `The take must switch from real-v5 (scenes 1-4) to film-v5 (scenes 5-11) between scenes 4 and 5.`
- OK | QUESTIONS.md | item 3 | count 1 | OLD: `Until you answer I keep it marked`
- OK | QUESTIONS.md | item 2 | count 1 | OLD: `Lead decision 2026-11-16 item 2 says the take never deletes contacts.`
- OK | F6B-AUDIT.md | item 1 | count 1 | OLD: `Scenes 5 to 11 use the **film set** (`
- OK | F6B-AUDIT.md | item 1 | count 1 | OLD: `Scenes 5 to 11 use the film set (`
- OK | F6B-AUDIT.md | item 1 | count 1 | OLD: `Order matters: switch flows off first, then check, then truncate, then switch the film set on.`
- OK | F6B-AUDIT.md | item 1 | count 1 | OLD: `4. **Switch on the film set, and only it.**`
- OK | F6B-AUDIT.md | item 1 | count 1 | OLD: `whether the order of the three jobs in one tick can delay alerts into scenes 5 and 9 (F6B-08)`
- OK | F6B-AUDIT.md | item 1 | count 1 | OLD: `**Two recovery flows from different sets can run at once on one table`
- OK | F6B-AUDIT.md | item 1 | count 1 | OLD: `**IF scenes 6 to 8 create `unknown` leads`
- OK | F6-AUDIT.md | item 1 | count 1 | OLD: `scenes 1 to 4 use real-v5, scenes 5 to 11 use film-v5.`
- OK | REPORT.md | item 1 | count 1 | OLD: `patches F-003/F-004 insert relayed numbers (60.1 to 61.9 s).`
- OK | QUEUE.md | item 10 | count 1 | OLD: `ONE database for the take = its Postgres (n8n state + claim rows)`
- OK | QUEUE.md | item 1,7 | count 1 | OLD: `any switch is a manual step by the lead with scripts/n8n_api.py (import/activate/deactivate)`
- OK | PLAN-002.md | item 1 | count 1 | OLD: `| n8n-flows-film-v5 | 4 | 54 | A | none (current) |`
- OK | PLAN-002.md | item 10 | count 1 | OLD: `one database for the take = n8n Postgres plus table mf_leads;`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `Status: round 1 fixes applied`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `and the caption near line 90, "18 kill runs, 60.1 to 61.9 s")`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `| 5 CRM refuses |`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `| 6 Doubtful case, lead goes in |`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `| 7 Mail may or may not have gone |`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `| 8 Answer says unknown |`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `| 9 Alert, no second mail |`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `| 10 The table row |`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `| 11 Alert refused twice (optional) |`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `Kind B: scene 5, film-v5 with a stand-in CRM`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `Kind C: scenes 6 to 11, film-v5 with stand-in stage, CRM and mail server`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `- C1 (NEW, switching sets):`
- OK | SCENE-FLOW-MAP.md | item 1 | count 1 | OLD: `- C2 (mail panes in scene 5):`
- OK | SCENE-FLOW-MAP.md | item 1,9 | count 1 | OLD: `- C7 (scene 10):`

## Per-file edit counts
- CUT-LIST.md: 1
- EXCEPTIONS.md: 4
- F6-AUDIT.md: 1
- F6B-AUDIT.md: 7
- FINDINGS.md: 14
- FIX-PLAN.md: 3
- LEDGER-ROWS.md: 3
- PLAN-002.md: 2
- QUESTIONS.md: 4
- QUEUE.md: 2
- REPORT.md: 1
- SCENE-FLOW-MAP.md: 14

No severities were changed. Counts changed: only the 'files in the take' count (8 to 4, by ls). Nothing committed. No secret printed.
