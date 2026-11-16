# Zoom-out on all deliverables against the one take (egm-zoom-out aa42fb49), saved condensed by flows-audit. Reviewer words unverified; I did NOT act on any park/cut suggestion because the queue items come from the lead's orders.
Short answer (reviewer): about a third of the effort removes no take risk and three real take risks have no owner.
## Over-built for one take (reviewer suggests cut/park; lead decides, see QUESTIONS Q17)
1 fill_flows (F3): README 286 lines, 8 of 20 mutants alive at round 3, security review at round 3; the job is ~3 env values and 6 placeholder ids in 4 files of made-up data; FIX-PLAN item already sets N8N_BLOCK_ENV_ACCESS_IN_NODE=false; F-029 says placeholders can come from the generator arguments. Suggest: pick env setting + generator arguments; freeze or park the tool.
2 flow-check README: only take_check.sh earns its place; --baseline, --strict, film-v5 block, run_all.sh serve no take claim; F8 duplicates.
3 QUEUE.md rule "always keep 3 agents running / take the next unreviewed area" manufactures work (F6, F8, F2; F2 already cut by decision 4); suggest stop rule = take-day gate passes.
4 Per-node table of 52 files (985 KB) for a take that uses 4 files. 5 FINDINGS rows "not in take"/"AFTER" (F-009, F-010, F-013, F-015..F-017, F-020..F-022, F-024..F-027, F-030, F-032..F-036, F-038, F-039, F-044..F-046, F-041): one client-build list, do not review. 6 FIX-PLAN "9 items" are really 5-6. 7 REPORT.md top carries ORDER 023/024 text. 8 Q10/F9 superseded.
## Conflicts
9 F-002 patch rewrites Claim (the node that proves the claim; untested in n8n; own fallback says it may break repeat-key replies): run T19 and T20 on UNPATCHED real-v5 first; patch only if T20 shows a hole.
10 F-001 (change n8n-flows/mf_leads.sql, mf.py:45) vs Q16 answer (use v4 mf_leads.sql as is + psql check): drop the F-001 patch and mf.py edit from BEFORE.
11 Q14 unanswered: re-rate F-005, F-006, F-023, F6B-01, F6B-13 to Nit (inflates 8 Blockers by up to 2). F-007 stays only if scene 4 shows a kill.
12 The audit never saw the sender, the driver or the script that starts n8n (take scripts not in tree).
## Take risks nothing owns
13 Blocker: HubSpot answer shape ('id' vs 'vid', all digits for CrmIdOk) unmeasured; a loopback re-smoke cannot test the real HubSpot node, credential or id shape: one made-up lead through the real HubSpot trial before rehearsal (lead decision 8 allows ONE made-up lead: this is it).
14 (stale: Q13 was answered 10:23Z: take cleanup OFF; still the lead verifies the exact script and option at re-pin.)
15 Test vs production webhook URL and active state not checked by anything: put in T19 (POST must hit the activated production URL).
16 Clean-up of saved runs (F-008 ON means executions, values file, fill_flows output carry lead data) is unwritten: test once at rehearsal.
17 Concurrent double-send (M1) only on a test build; T19 is sequential: if the video sends both back to back, run M1 on the take build once.
## Order for the lead (reviewer): desk: answer Q14, settle Q13. Laptop: (1) Postgres + take DB from v4 mf_leads.sql, psql gate 4 alert_* columns; (2) start script N8N_BLOCK_ENV_ACCESS_IN_NODE=false + DESK_* incl. DESK_ALERT_TO on port 5690, T-ENV; (3) rebuild real-v5 with F-008 only, fill placeholders by generator arguments, grep -c placeholders = 0, take_check.sh; (4) import + activate, confirm production webhook answers; (5) ONE real HubSpot lead: id all digits, row done, one mail, one contact, note contact id; (6) T19 unpatched: same key twice, second reply < 10 s, 1 mail 1 row 1 contact; (7) T20 unpatched: empty and junk key; patch F-002 only if needed then rerun 5-7; (8) K1 once if scene 4 kills; (9) counts screenshot + clean-up dry run, then the real take.
