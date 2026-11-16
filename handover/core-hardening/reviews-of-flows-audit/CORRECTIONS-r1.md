# CORRECTIONS to the flows-audit (target: branch cloud/flows-audit, folder handover/flows-audit)
Each entry: where, old text (exact, from the pinned head 35235ace), new text, why, review id. Owner of every entry: the lead (the person who owns the audit). I did not change the target. Evidence: REVIEW.md, result-review-R1..R4.md, evidence-A1..A4.

## Findings text (FINDINGS.md)
C-01 FINDINGS.md:29 (F-002 row). Old: "If n8n passes an empty string (UNVERIFIED whether it does or passes null), the first keyless lead is stored and every later one is answered as a stored repeat and never processed". New: "A lead with an empty key is never processed and never alerted, whether n8n passes an empty text or null: Claim stores the empty key, the check 'Claimed is not empty' is false so the lead is answered as a repeat, recovery skips it (mf-recovery.json:60 StuckRow), and the alert step skips it too (mf-recovery.json:158 AlertRow); the row is re-claimed every 720 s with no mail. UNVERIFIED only: whether n8n passes empty text or null." Why: the audit understates the Blocker (missed M1).
C-02 FINDINGS.md:40 (F-013 row). Old: "PLAN-4-NLITE-FROM-LEAD.md:78-79 says that is deliberate (money-safe)". New: "n8n-mainframe/stage_server.py:4 says that is deliberate (money-safe); PLAN-4-NLITE-FROM-LEAD.md:78-79 does not contain those words". Why: citation DRIFT (R1, A1).
C-03 FINDINGS.md, F-019 row. Add "UNVERIFIED: the desk store is outside this repository" to the verdict cell. Why: it could not be checked (R1).
C-04 FINDINGS.md, F-001 row. Add after the table sentence: "The file n8n-flows/mf_leads.sql is correct for the old v2 flows in its folder; v5 ships no table definition of its own." Why: precision (R1).
C-05 FINDINGS.md, F-014 row. Old wording "loses nothing". New: add "but see F-009: with no webhook authentication every wrong key adds one alert, with no cap and no table size limit". Why: missed M5 (R2-4).
C-06 FINDINGS.md, add new rows F-035 to F-041 as Major (take) for M1 (extend F-002), M2, M3, M4, M5, M6, M7 in REVIEW.md section 2, each with file:line from the review notes. Mark runtime parts UNVERIFIED. Why: six Majors that touch the take were missed.

## Fix plan text (FIX-PLAN.md)
C-07 FIX-PLAN.md step 4 (line 5). Old: "after import, the flow text must contain no PLACEHOLDER and no SUB_WORKFLOW_ID; DESK_ALERT_TO and the other environment variables are set before the first lead (F-018)." New: "after import, the flow text must contain none of PLACEHOLDER, SUB_WORKFLOW_ID, PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID or the HubSpot credential id; set N8N_BLOCK_ENV_ACCESS_IN_NODE=false (N8N-START.md:13) and DESK_ALERT_TO, DESK_URL, MF_STAGE_URL, MF_CRM_URL before the first lead (F-018)." Why: M2, M3.
C-08 FIX-PLAN.md, add a step "swap the film set for the real set": only one set can be active (same webhook paths); say who does it and when. Why: M2.
C-09 FIX-PLAN.md, patch F-001 and F-002 entries: add "A take database built from the old SQL needs a manual ALTER TABLE (an edited .sql file does not change an existing table); F-002 needs the 8 files rebuilt and re-imported with the placeholders filled again." Mark both "risk", not "safe". Why: R2 deployment matrix.
C-10 FIX-PLAN.md, patch F-002: write the sender contract in one place: "422 = final, never resend; 503 = resend with the same key". Say it is UNVERIFIED that the sender follows it (the sender is not in this repository). Why: M7.
C-11 FIX-PLAN.md, patches F-003 and F-004: add leftovers: VIDEO-RUNSHEET.md lines 85 and 90 still conflict; PAGE-STATEMENTS statement 18 still says "four n8n settings turned off" (against F-008). Why: R2.
C-12 FIX-PLAN.md, new item for F-009/F-014: a cap on alerts per hour and a database-down alert (M4, M5). Why: missed.

## Wording (FINDINGS.md, FIX-PLAN.md)
C-13 Short answer: start with the first action ("do F-001 and F-002 before the take"), then the counts; use one unit ("steps" or "nodes"), not both. Why: R4.
C-14 Add a plain-words list for ORDER, lane, L1-21, door, desk, stage service, claim, lease, T17, K1; one meaning each. Split the F-002 cell into: what breaks / why / what to do. Why: R4.
C-15 Each FIX-PLAN step gets an actor ("the lead", "the builder", "the owner"). Why: R4.

## Cut list (CUT-LIST.md)
C-16 Line 20, PAGE-STATEMENTS-DRAFT.md. Old: listed as "duplicate" and archive. New: verdict NEEDED until sections A and B are moved into PAGE-STATEMENTS-V4.md (VIDEO-RUNSHEET.md:8 cites it); then ARCHIVE. PAGE-STATEMENTS-V4-DRAFT.md stays on the list. Why: wrong call.
C-17 Line 20, the 7 top-level notes. Old: "the lead decides which one is kept as the single note". New: "distinct experiments, no merge; archive all 7 as a set". Why: wrong call.
C-18 Line 19, docker-native-pg-shim.py. Old: on the candidate list "ONLY after RUN-ON-LAPTOP.md:51 is changed". New: remove it from the list; verdict NEEDED (RUN-ON-LAPTOP.md:49-51 tells a reader without Docker to copy it). Why: wrong call (counted 0.5 if the take laptop has Docker).
C-19 Add a verdict word (NEEDED / DUPLICATE / NOT-NEEDED / CRM-COULD-DO) to every row. Never CRM-COULD-DO for money, approval, redaction, audit. Why: required format.
C-20 ORDER OF WORK step 3. Add the live references: RUN-ON-LAPTOP.md:38, :46, :82; DESIGN-A-README.md:6-8, :38, :40, :45; VIDEO-RUNSHEET.md:11, :57; PAGE-STATEMENTS-V4.md:148 (statement 20 cites "film-v4"). Otherwise step 4's grep gate fails.
C-21 Before step 4 add a step "copy first": V3-README.md and V4-README.md alert design reasons and test lists, n8n-flows-real/README.md lines 6-14 (HubSpot facts), AUDIT-VIDEO-RUNSHEET.md "Open decisions" (VIDEO-RUNSHEET.md:74 refers to them) go into the v5 documents; no other copy exists.
C-22 table-screen v1: archive only after v2 has a first live run (v1 is the only one proven in n8n).
C-23 Wording "11 older flow folders" -> "10 flow folders, the 4 plain files and table-screen v1". The totals (40 files, 525 of 655 nodes) are right.

## Added by resolve round 1 (R4 items that had no entry)
C-24 FINDINGS.md:7. Old: "52 flow files (655 steps)". New: "52 flow files made of 655 nodes (a node is one step): 9 used by the filmed run, 3 old desk entry flows, 40 older versions (8+1+3+40 = 52)". Why: R4-B1 (the CUT-LIST total of 40 files and 525 nodes is right; R4's 36 was wrong).
C-25 FINDINGS.md:12, :24; FIX-PLAN.md. Name who acts in each passive sentence ("the builder deletes the saved runs at clean-up"), explain the ordering rule so it matches the table, and give each step an actor and one label set (P/T/O explained once). Why: R4 M5, M7, M8.
C-26 FLOWS-AUDIT.md:94 and :97. run_dn1.py is called IDLE in one place and USED as a check in another: make the two lines agree. FIX-PLAN step 7: define T17, T18, K1, K3B in one line each; step 9: do not list F-034 under archive and then exclude it. Why: R4 M6, M9, M10.
C-27 FINDINGS.md:9 and the "no script or flow uses the old folders" sentence: say instead "2 to 9 documents still name them (see CUT-LIST)" and state that the file named for the current flows is in the v2 folder n8n-flows. Why: R4 unsupported claims.
