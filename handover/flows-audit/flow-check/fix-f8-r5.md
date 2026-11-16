# fix-f8-r5 (round 5, non-security tool), 2026-11-16 (UTC; IST = UTC + 5:30)
Backup of the folder before any edit: scratchpad `bak-f8r5/` (not in the repo). Only files in `flow-check/` changed. `evidence-r4.md` not touched. No commit.

## What failed first / NOT DONE (first)
- My first self-test run after the changes: 1 case not as expected (`control_real_ids_pass_when_ids_are_required`): the new placeholder check also flagged mail addresses, so the test helper that makes "real ids" had to replace those too. Fixed in `selftest.py` (`_real_ids`).
- My first take-check test used `subprocess` in `selftest.py`; ruff (S603/S607) rejected it and I did not suppress it. The take script is now tested in `run_all.sh` instead (exit 0 plus required lines in `raw/take-check.txt`).
- My first mutant run: 6 of 20 random mutants survived (see below). 3 were real gaps (the new WARNs not counted as "known open problems"): new case added, the 3 now die. 3 remain, all equivalent or without behaviour (below).
- Not verified: n8n was never run; the `--ddl` check reads names only, not SQL meaning; an alias or an unknown SQL word in a query could give a false WARN (it is a WARN, never a FAIL); the real database is not visible (the psql gate is a person's step). Not fixed (minors not asked): duplicate-address rule across real-v5 + film-v5, non-numeric HubSpot id.

## Fixed
- M1: placeholders (words containing PLACEHOLDER, PG_CREDENTIAL_ID, ...) in every node setting except `workflowId` are a WARN per file (known open problem; FAIL with `--require-real-credential-ids`) and a block `PLACEHOLDERS IN NODE SETTINGS ... these must be filled before import` in the closing block, printed under `--quiet-info`; `take_check.sh` prints it in its top block (3 found today: `fromEmail` x2, `toEmail`).
- M2: new option `--ddl FILE`; WARN naming missing columns or undefined tables; no `--ddl` = loud WARN + `SQL COLUMNS NOT CHECKED`. `take_check.sh` passes `demo/n8n-flows-v4/mf_leads.sql` (found by path, then by `find`), says so if missing; `run_all.sh` passes it too. v4 table: no WARN (14 queries); older `demo/n8n-flows` table: AlertClaim, AlertBackoff, AlertMark WARN with the alert_ columns. README names the file (lead decision Q16) and holds the psql gate (four `alert_` columns exist before the first send); `take_check.sh` prints the gate too and `run_all.sh` requires that line.
- M3: WARN (known) when a webhook or form flow has `saveDataSuccessExecution`/`saveDataErrorExecution` = none (form and hook today, not recovery or sub-workflow); README line 3 block and take_check top block say these files do NOT contain F-002 or F-008, in plain words.
- M4: `onError` list, `maxTries`, `waitBetweenTries` and a missing `responseMode` go through `unv()` (FAIL under `--fail-unverified`).
- Minors: "nothing ran in n8n; import untested" first line of take_check; README run count 11 -> 9 checker runs (+ take script + self-test); Not-proven text without F-002/T19/T20 codes; `--accept-if` WARN says a database failure there vanishes with no alert; take_check prints the env variable names found in the files.
- evidence-r4 survivors: line 48 exit code (case `r5_python_older_than_3_10_exits_3_with_message`, patches `sys.hexversion`), FAILS.append (`r5_result_line_counts_each_fail_once`), Slack token exactly 10 chars (`secret_slack_exactly_10_chars`), connection without type (`shape_link_without_type`), deep_diff `(a or b)` (`r5_deep_diff_added_to_empty_list_and_removed_to_empty_list`), diff header (`diff_text_header_line_exact`).

## Mutants (own run, `raw/mutants-r5.txt`, scratch copies of the new check_flows.py, full self-test each)
- The 6 evidence-r4 survivors, re-created on the new code: 6 of 6 KILLED.
- 20 random mutants (seed 5) of the new code: 17 killed, 3 survived at first. Survivors: `lstrip`->`rstrip` on `query.lstrip("=")` (equivalent: `=` is no name character, no behaviour change), `not ` removed in a comment line (equivalent), and 3 `known=True` -> False (counted as 6 survivors with repeats): killed after adding `r5_new_warns_are_counted_as_known_open_problems` (3 of 3 re-run killed).
- Not independent: this is my own mutant run.

## Raw results
- `bash run_all.sh`: rc 0; self-test 629 as expected, 0 not, 62 skipped (r4: 577/0/58). take_check.sh rc 0, missing lines: none.
- Round-4 checker against the new self-test (`raw/selftest-oldchecker-r4.txt`): 592 as expected, 37 NOT (all new round-5 cases).
- `ruff check` rc 0 (All checks passed); `ruff format --check` rc 0 (25 files); `bandit -ll -r` rc 0 (No issues, 0 nosec); grep noqa|nosec|type: ignore|pragma: none (rc 1).


---
# Round 5b (reviewer line, joined letters), 2026-11-16 (UTC; IST = UTC + 5:30)
**Failed / not checked first:** nothing failed in the final runs. Not checked: real names beyond the five tried by hand and four in the test; `Zed Smith` passes by design (3 letters, looks human; a script cannot tell it from a real name; said so in README.md). No commit made. Note: git showed my edits to `take_check.sh` as already committed (HEAD c79f8074...), so some other process commits in this folder; not mine.
**Cause:** `reviewer_ok` in `take_check.sh` cut names at every non-letter, so `O.L.L.M.` became the words o, l, l, m and the stand-in word `llm` was never seen.
**Fix at the choke point (`reviewer_ok`):** per space-separated part of the name, each run of one-letter pieces is joined; the run is refused when it equals a stand-in word or contains one of 3+ letters. Only one-letter runs are searched, so `Aiden`, `Botha`, `Pat Smith`, `O'Brien`, `Jane Q. Roe-Smith` are not hit. The `Testonly` test allowance is unchanged.
**By hand (function alone):** `Pat O.L.L.M.` refused, `P.a.t C.l.a.u.d.e` refused, `Pat Smith`, `O'Brien`, `Aiden Botha`, `Zed Smith`, `J.R.R. Tolkien`, `Jane Q. Roe-Smith` accepted.
**Tests added to test_take_check.sh:** two refusals (exit 4, reviewer-line message) in the M1 loop; four accepted names (exit 5 with the test override, i.e. not refused as a stand-in): Pat Smith, O'Brien, Aiden Botha, Zed Smith. Not run against the old code (no mutation proof); the old code's result for `Pat O.L.L.M.` is the exit 0 in evidence-f8-r4b.md section (5).
**Runs (exit codes taken directly):** bash -n take_check.sh / test_take_check.sh / run_all.sh: 0 / 0 / 0. `bash test_take_check.sh` on a patched copy: exit 0, "100 of 100 cases as expected, 0 not as expected". `bash run_all.sh`: exit 0. ruff check: 0. ruff format --check: 0. check_secrets.py: 0. check_refs.py: 0. After run_all: `git checkout -- raw selftest-output` done; status then clean for raw and selftest-output.
