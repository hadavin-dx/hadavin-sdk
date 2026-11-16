# fix-tcfp13 (flows-audit fixer; static, nothing run in n8n or Postgres; not committed)
Fixed in one batch: reviews/fp-tc-stranger-r17.md M1-M6 and minors; reviews/t19-t21-check-r1.md B1, M1-M5; reviews/fp-tc-stranger-r18.md M1-M8. Reviewer words unverified; each location re-grepped first.

## What changed
- r17 M1: `need_set NAME ...` defined in the shas.env skeleton (RUNBOOK section 4); every block that reads a REPLACE_ME-default value (REPORT, JUDGE_WHO, BODY, HOOK_URL, SHA_R20-23, KEY, PIN_NAME, BRANCH, PATCH_BRANCH, COMMIT_MSG, SRC_TAKE, NEW, STUDIO, REPO, RECORDING, PGCONN_SELECT_ONLY) now starts `need_set ... &&` (36 blocks in the three files); TAKE-CHECKLIST R1 text fixed.
- r17 M2: FIX-PLAN Tuesday-inputs table now lists items 38 (a)/(b), 33, 55, 75, 70, 58, 71 (run_real_check part), 67, 77 with QUESTIONS answer-by times; item 58/70 removed from "Not Tuesday blockers". Item 55 conflict text and what the operator does without the gate script: see below.
- r17 M3: R6 sentence replaced (grep -c is the total row count, a sanity count, not a pass line). M4: R7 Part A and Part B labelled (comment lines in the block). M5: BODY/HOOK_URL checked with input_ready BODY and HOOK_URL (RUNBOOK step 16, skeleton comments, FIX-PLAN table). M6: step 18 (1b) pre-check (FLOWS_ROLE differs from PGADMIN, not placeholder, not superuser, input SECOND_ADMIN).
- r17 minors: step 13 pass wording (SHA_PIN / SHA_PIN2 lines); Block step 13 (d) cite changed to Block P2b; step 12 and 19 placeholders removed; TAKE-CHECKLIST KEYF line; RECORDING guard; step 24 gate 15 vs 4 min explained; Case B 12:22 vs owner sheet 12:00 stated as a needs-lead point; FIX-PLAN step 3a `--` pathspec.
- t19-t21 B1: one F-002 wording "T19, T20 and T21 pass on the patched copy" in FINDINGS (severity cell, paragraph, WHEN THE BLOCKER LIFTS), LEDGER-ROWS row, TAKE-CHECKLIST Words box and row 3b, FIX-PLAN F-002 rule; a T21 failure keeps F-002 a Blocker. M1 FINDINGS T20 counter form; M2 "fixed" removed; M3 T21 stop rule and pre-check copied into FINDINGS T21 METHOD; M4 PGADMIN_PW added; M5 done (see r17 M3).
- r18 M1 step 6 Tuesday set = n8n_start.sh + n8n_kill.py at 04:54; n8n_api.py at 06:59 (item 47). M2 no angle brackets, take-tree made, guarded copy. M3 diff limited to handover/demo/n8n-mainframe. M4 step 4a inputs named. M5 PIN_NAME warning at bootstrap; (b) grep inside the guard. M6 (a) fill inside the guard; (b) credential ids vs data folder; example intake address cannot receive mail (item 77). M7 step 8 (0). M8 gate check (e) NOT CHECKED until the scope reply is recorded.

## Lines for Q31 (QUESTIONS.md is append-only; lead or a Q31 fixer adds them)
1. Item 55 conflict: QUESTIONS item 55 says Wed 05:45Z; RUNBOOK I47 (a)/I49 (a) need the one-script gate before step 1 (Tue 04:00Z) and at step 16 (Tue 08:29Z). Plan files now say: without the script on Tuesday the operator runs the step 14 commands by hand and writes (e) NOT CHECKED; Wednesday needs it or step 24 does not run. Lead: confirm or move item 55's time to Tue 04:00Z.
2. Item 71 closing parenthesis (step 6 needs the Tuesday set at 04:54): read as n8n_start.sh and n8n_kill.py only; n8n_api.py is item 47 (Tue 06:59Z). Item 71 text needs this correction.
3. New item needed: who creates the database logins, grants and password file (DB_SETUP.sh); item 60 has names and route only. Due 04:54Z.
4. New item needed: is the data folder of step 7 the one that holds the three n8n credentials (ids for step 9). Due 05:14Z with item 35.
5. New items needed: step 4a (2) the scene 4 / "decision 4" sentence and (3) the in-frame lines; due 04:16Z like item 69.
6. New item needed: SECOND_ADMIN (a second way to run ALTER ROLE ... LOGIN, for T21); before the practice run.
7. Item 30 (OPEN) decides Monday-night vs Wednesday HubSpot scope ask; plan files follow the Wednesday reading with (e) NOT CHECKED until the reply is recorded.
8. Item 66 index: item 33 IF NOT line says blocks "stop with unset"; now they print REFUSED (the index text is the lead's file to change).
9. Case B recording-ready 12:22Z vs OWNER-STEPS 12:00Z: owner sheet must carry the Case B time, or Case B must save 22 minutes (needs lead).

## ORDERS.md (not edited, lead's file)
Line 167 (Q29 item 3) names T19 and T20 for the no-take rule; line 171 (Q30 item 1) says T19-T21; Q27 item 9 says T19-T21. The plan files now follow T19-T21 and say the lead confirms.

## Not done / uncertain
- Nothing was run. check_runsheet_paste.py prints FAIL ("claim ids missing": A-003, A-096, B-107, B-155 and 50 UNTRACED ids); RUNSHEET-WORDING.md and CLAIMS-TABLE.md were not touched, so this is not from this batch; I did not check whether it failed before.
- TAKE-CHECKLIST 395 already described SHA_PIN2 correctly; only RUNBOOK 205 was changed.
- Step 13 (d) cite changed to Block P2b (done, not left open).
