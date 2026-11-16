# fix-fixplan3-r1 (FIX-PLAN item 3 rewritten into one run order; static; nothing ran in n8n)
Source: reviews/readiness-fixplan3-r1.md (reviewer words checked against take_check.sh, flow-check/README.md, fill_flows/README.md, V5-README.md, patches). Backup: scratchpad/bak-fp3/FIX-PLAN.md. Only FIX-PLAN.md edited (items 2, 3, 4).
## Findings checked
- B1 true: item 3 b6 needed F-008 of item 4. Fixed: steps 0-4 apply both patches first.
- B2 true: patches edit build_mainframe.py; V5-README command writes in place. Fixed: step 1 (git apply, repo root, order), step 2 (new folder + in-place consequence: run_all.sh:56 loses --diff-base), step 3 (commit, sha). F-008 after F-002 and the reverse both apply (scratch copy in a throw-away git dir; real tree untouched).
- B3 true: default 12:11 vs patched 15:14; TAKE_CHECK_FLOWS is a test hook (take_check.sh:15). Fixed in step 4 and lead fix 1; --accept-no-save is passed by take_check.sh:23, missing in README:31 (lead fix 3).
- B4 true: NOKEY is not in PROBLEMS (missing F-002 still exits 0; missing F-008 exits 4). Fixed: step 4 pass test is four grep counts plus exit 0; stated until the F8 fixer adds --patch-checks to take_check.sh (check_flows.py already has it, run_all.sh:56). INFO/key check/ACCEPTED counts stated; N of open items is lead fills in.
- B5 partly: n8n_api.py never seen; method is take_check on the export plus greps; byte diff always differs (stated by the brief/reviewer, not verified here). Missing inputs listed in step 9.
- M1/M2 fixed as pseudo-commands (steps 5, 14) with 'lead fills in: connection' and schema column. M3: rehearsals are steps 11 and 13, N and 10 s set in step 12 before steps 14-16. M4: SELECT-only login commands and negative test (step 5), sign-off (step 15); run-list template and sign-off format remain 'lead fills in'. M5: run list is filtered, not emptied (Q19-1); whole-table 0 kept. M6: grep -rl with a control on the unfilled folder, six placeholder names, F-018 quiet loop, fill_flows check, import order and one copy (steps 6-8). M7: marked SUPERSEDED in plan, lead fixes listed. M8: Machine paragraph.
- Nits: grep -c replaced by -rl; 'four share one gate' now five; placeholder names listed once (six names from fill_flows README).
## Not checked / lead fills in
Nothing was run except count_findings.py and check_patches.sh. Expected take_check lines are read from the script and evidence-q18.md, not produced on the new folder. Whether generator output equals the committed real-v5 (before patches) is unverified (step 2 diff is the test). Missing values: REPO, OS/shell, folder name, values file, connection and schema, SELECT-only role text, take keys, N, 10 s, date X, re-pin time, sha, export script arguments/outputs, HubSpot search method, run-list template, sign-off format, F-018 loop, T19-T21 runner, observed N of open items.
## Lead fixes (files not mine)
take_check.sh:60 and the 15/18 test-hook comments; fill_flows/README.md:240; flow-check/README.md:31 and :17; F8 --patch-checks in take_check.sh.
## Outputs
count_findings.py FINDINGS.md: rows 45 unique 45, Blocker 5 / Major 7 / Nit 33; 13 BEFORE / 32 AFTER. check_patches.sh: PASS 4 patches (rc 0). Not committed.
