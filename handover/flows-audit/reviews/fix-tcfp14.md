# fix-tcfp14 (flows-audit fixer; static, nothing run in n8n or Postgres; not committed)
Fixed in one batch: reviews/plan-operator-r19.md M1 to M8 and reviews/plan-consistency-r19.md M2 (TAKE-CHECKLIST Inputs item 13), M5, M6, M7. Reviewer words unverified; each cited location was re-read first. Files edited: RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md only.

## Not fixed here
- Consistency M4 (item 55 time conflict): needs the lead's decision; left untouched.
- Consistency M1 and M3: belong to the other fixer (FINDINGS.md, LEDGER-ROWS.md); not touched.
- Nothing was run against n8n or Postgres. The guards were tested only in a local bash with a made-up folder (see Evidence).

## What changed
- Operator M1 (RUNBOOK step 1): guard, evidence-head test, status check and `git switch -c` are now ONE `&&` chain that starts with `. "$ENVSH" && need_set REPO PATCH_BRANCH BRANCH FINAL_SHA`; a REFUSED or a dirty tree creates no branch. The `status-DIRTY` line no longer exists (a dirty tree stops the chain); pass and failure columns reworded.
- Operator M2/M3: interactive bash is now stated in the RUNBOOK "Machine" line, the skeleton header and the bootstrap sentence (type `bash`, `echo "$BASH_VERSION"` must print a version; zsh and sh give a bad substitution). Every `${X:?unset}` is gone from all three files (grep count 0 for the colon-question form in each). Skeleton line 90 is now a `case` that prints BLOCKED and returns 1 (or exits when not sourced).
- Operator M4/M5: `input_ready` returns 1 on `BLOCKED-NAME`; new helper `need_new NAME` (returns 1 when the path exists, prints `ok-new-NAME` otherwise). Guards now sit in the same `&&` chain as what they guard: step 12 export (empty-folder test chained in front of the export command), step 18 (1b) and (2) (roles-differ test, `ready-SECOND_ADMIN`, and a `rolsuper = f` test are in front of each of the two cut commands; roles-differ and REFUSED lines go to `$TESTLOG` with `tee -a`), step 22 (`need_new TESTREC` in front of the start command), step 26 (0) (`need_set RECORDING && need_new RECORDING && START_RECORDING`). TAKE-CHECKLIST multi-line blocks are `( ... || exit 1` ... `)` groups, with a "How to paste a block" paragraph after the GO row command-blocks heading.
- Operator M6: step 4b (c) now says type Block P1b WHOLE, first line included, with `$PIN_FILE` in place of `$NEW_PIN` in both places of that line (the first line holds `need_set PIN_NAME`). Step 4b (d) says the lead types Block P1b whole and then the WHOLE Block P1c (copy, commit, `SHA_PIN1`), so (e) is not typed after (d). Step 4b (e) and step 13 (d) commit chains now start with `. "$ENVSH" && need_set ...`, check the branch, check that the reviewer line holds `$PIN_NAME` and contains no PLACEHOLDER, session or "lead to confirm" word. Step 13 (d) names Block P2b whole. TAKE-CHECKLIST P1b: the committed-pin sentence says `PIN_FILE`, never `NEW_PIN` (contradiction removed).
- Operator M7 (step 8): order is now 0a keep folder, 0b logins (`input_ready DB_SETUP`), (i) CREATE DATABASE, (ii) table, (ii-b) grants (`input_ready DB_GRANTS`), (iii) to (v). (i) to (iv) and the insert test carry `need_set` for PGCONN_SERVER, TAKE_DB, PGCONN_TAKE, PGCONN_SELECT_ONLY, REPO, INSERTLOG.
- Operator M8: "new item needed" replaced by Q31 item 80 and 81 (step 4a (2),(3), Tue 04:16Z), item 79 (step 9 data folder, Tue 05:14Z), item 78 (step 8 DB_SETUP, Tue 04:54Z), item 82 (SECOND_ADMIN, Wed 05:45Z). FIX-PLAN table: item 60 lists all eight names plus the password route; new rows for 32, 69, 80, 81, 78, 35, 79, 82. TAKE-CHECKLIST Inputs items 25 to 33 added for the same inputs.
- Consistency M2: TAKE-CHECKLIST Inputs item 13 now says Q27 item 9 names T19 to T21 and only Q29 item 3 names T19 and T20.
- Consistency M5/M6: RUNBOOK I1, step 6 LEAD FILLS (3) and the SHA_SCRIPTS status command now list the Tuesday set as `n8n_start.sh` and `n8n_kill.py` (04:54Z); `n8n_api.py` is I12 (06:59Z, item 47); I18 is now only `n8n_drive.py` and the commands (Wed 05:45Z), while `run_real_check_n8n.py` and the post-twice script go through I33 (Tue 09:00Z, items 70 and 71).
- Consistency M7: FIX-PLAN rows added (see M8 above) and the same inputs in the TAKE-CHECKLIST Inputs list.

## Evidence (commands run from /home/user/hadavin-sdk/handover/flows-audit)
- `python3 -I tools/check_refs.py`: exit 0, `PASS 5168 references`.
- `python3 -I tools/check_names.py`: exit 0, `PASS 655 rows`.
- `python3 -I tools/check_secrets.py`: exit 0, `PASS 0 hits in 1985 files`.
- `ruff format --check .`: `699 files already formatted`.
- `diff <(sed -n 14,47p FIX-PLAN.md) <(sed -n 8,41p TAKE-CHECKLIST.md) | wc -l`: `0`.
- `bash -n` on 49 extracted pieces (the RUNBOOK skeleton, every fenced block of TAKE-CHECKLIST and FIX-PLAN, every RUNBOOK inline command that starts with `. "$ENVSH" &&`): 48 pass; 1 fails: the RUNBOOK sentence fragment `. "$ENVSH" && need_set NAME ... &&` in the skeleton comment, which is prose, not a command.
- Guard behaviour tested in a local bash with a made-up folder and the real skeleton: `input_ready PIN_NAME` printed `BLOCKED-PIN_NAME` and returned 1; `need_set REPO PIN_NAME` printed REFUSED and returned 1; `need_new TAKE_FOLDER` returned 1; `need_new RECORDING` printed `ok-new-RECORDING` (so step 26 puts `need_set RECORDING` first, because a REPLACE_ME word is a path that does not exist); a group `( . "/nonexistent" && ... || exit 1 )` returned 1.

## Not checked / uncertain
- No block was run against real n8n, Postgres or git; every command is marked "mine, not tried". The `rolsuper = f` chain in step 18 and the step 4b (e) / step 13 (d) grep tests were checked with `bash -n` only.
- `DB_GRANTS` is a new answer-cell name I added to split grants from logins; Q31 item 78 may name only one file. The lead must answer both under item 78 or split the answer.
- `check_secrets.py` passed, so no failure on flow-check/raw was seen to report.
- Backups of the originals are in the session scratchpad (orig/), not in the repository.
