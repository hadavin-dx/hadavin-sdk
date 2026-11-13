# ORDER 4: why 56 F on main, and why the log ends at 71 percent (evidence runner lane; raw facts, I fixed nothing)

## Answer in four lines (failures and my own slips first)
1. **The 56 F on main 61ded9e are caused by how agent A started pytest, not by a product defect I can show.** A used `TMPDIR=<private>/tmp` but `--basetemp=<private>/base` (a folder OUTSIDE TMPDIR). The repo's path-confinement helper then refuses every test folder: message `path is outside the allowed folders (add a folder with LEAD_DESK_PATH_ROOTS)`. Reproduced on main: the same 56 ids run with `--basetemp` OUTSIDE TMPDIR = **56 failed** (raw/failures-basetemp-outside-main.log); run with `--basetemp` INSIDE TMPDIR = **56 passed in 6.65 s** (raw/failures-alone-main.log). The runs of D and C2 (basetemp inside TMPDIR, `-v`) show 0 FAILED so far in the same files (see section 5). So A's four suite runs are INVALID as product evidence for pass/fail. A's earlier note said the first hang-hunt attempt was invalid for the same reason, but A's own runs had the same flaw and I did not catch it. That is my supervision gap.
2. **pytest did NOT stop at 71 percent. The log file was cut.** A's script writes `pytest ... > file` and then `echo EXIT_CODE >> file`. I committed and pushed those live log files (`git add -A`, and `git pull --rebase` while the logs were being written). Git replaces a tracked file in the working folder when it rebases or stashes, so pytest kept writing into a deleted copy of the file and only the later `echo EXIT_CODE` line landed in the new copy. That is why every log ends mid-progress followed directly by `EXIT_CODE=1 ...` with no summary. Proof of the mechanism on the live processes of D and C2 (their logs got the same treatment at 10:27:39Z when I ran `git pull --rebase --autostash`): `ls -l /proc/<pid>/fd` shows `.../suite-final-run1.log (deleted)` for the pytest still running. The exit code 1 and the wall time (about 1110-1172 s, the whole suite) are real; the output after the cut was lost. I did NOT recover the lost tail of A's four runs (those processes are gone).
3. **Why the cut is at the same test in both runs:** not proven. In run 1 and run 2 of main the cut falls on the same mark (2650 of 3605 tests; the next test not shown is `tests/test_real_check_dry.py::test_a_dry_run_where_every_send_ends_in_doubt_fails`). That file alone passes (71 passed, 167 s, raw/stoptest-file-alone-main.log) so I find no test that kills pytest. I cannot show why both runs were cut at the same mark; it needs a rerun with logs that git never touches. (Not claimed: that my commits fell at the same elapsed percent each time.)
4. **My slip, now fixed:** from now on I do not `pull --rebase`, `stash` or `checkout` while a test run is writing into this repo folder; I only `git add` and `git commit` the finished files, and I copy the orphaned logs of D and C2 out of `/proc/<pid>/fd/5` (rescue loop, files `raw/*.recovered.log`). D run 2 writes a new log file that I will not touch until it ends.

## (1) Failing test ids (main 61ded9e, A run 1 and run 2 identical positions): 56
Counts per file: tests/test_load_tools.py 49, tests/test_n8n_api_url.py 5, tests/test_http.py 1, tests/test_path_confinement.py 1. First 12 ids:
```
tests/test_http.py::test_crash_d2_subprocess_with_the_blind_smtp_sender
tests/test_load_tools.py::test_clean_case_passes
tests/test_load_tools.py::test_planted_fault_fails_one_check[fault_lost_receipt-1-form:r-gone]
tests/test_load_tools.py::test_planted_fault_fails_one_check[fault_double_mail-3-L1]
tests/test_load_tools.py::test_planted_fault_fails_one_check[fault_sent_without_mail-3-L2]
tests/test_load_tools.py::test_planted_fault_fails_one_check[fault_crm_missing-4-L3]
tests/test_load_tools.py::test_planted_fault_fails_one_check[fault_crm_extra-4-L5-ghost]
tests/test_load_tools.py::test_planted_fault_fails_one_check[fault_five_model_calls-5-L4]
tests/test_load_tools.py::test_planted_fault_fails_one_check[fault_pending_left-2-L4]
tests/test_load_tools.py::test_mail_that_cannot_be_matched_fails_check_3[fault_wrong_recipient-wrong-recipient:L1]
tests/test_load_tools.py::test_mail_that_cannot_be_matched_fails_check_3[fault_unreadable_message-unparseable-message]
tests/test_load_tools.py::test_all_unknown_book_fails_unless_allowed
```
Full list: raw/failing-ids-main-61ded9e.txt. How I got the ids: the progress marks of the -q log are in test order (serial run), mapped onto `pytest --collect-only -q` of the same commit (3605 tests). The 56 ids were then rerun alone (section 4), which confirms they are the right ids. PR #12 head 8d65577: run 1 gives 57 ids (the 56 plus `tests/test_path_confinement.py::test_scrub_script_started_without_pythonpath_refuses_a_missing_file_and_shows_usage`, collected 3686 tests); run 2 of PR #12 has 2 `E` marks and a different spread of F; its mapping is NOT reliable (that log was cut and rewritten differently), see raw/failing-ids-pr12-8d65577-run*.txt with that caveat.

## (2) First failure message of each distinct kind (text only)
From raw/failures-basetemp-outside-main.log (the same 56 ids, `--basetemp` outside TMPDIR):
- 44x `tools.pathconfine.PathRefused: book desk.sqlite3: path is outside the allowed folders (add a folder with LEAD_DESK_PATH_ROOTS)` (shown through `load_tools.check_invariants.InputError` with the same text)
- 2x the same with `log file`; 1x `book d.sqlite3`; 1x `--log` ; 1x `assert 2 == 0` (a script run as a subprocess exited 2 with the same refusal).
No secrets appear in these messages.

## (3) What ends the log at 71 percent
See answer 2 above: the log file was replaced by git while pytest ran; pytest itself ran to its end (exit code 1 from the real failures of answer 1, wall time 1110-1172 s). Not found: crash, `os._exit`, `-x` in config, memory kill or timeout plugin (the process ran the full time; no dmesg or OOM data was read; I did not check pyproject for `-x`; `-q -rs` was the only option, per A's script run.sh).

## (4) Do the same ids fail when run alone?
- Alone, basetemp inside TMPDIR: 56 passed (raw/failures-alone-main.log, 6.65 s).
- Alone, basetemp outside TMPDIR: 56 failed (raw/failures-basetemp-outside-main.log).
- Lockstep (main and PR #12 copies started in the same second, files test_http, test_load_tools, test_n8n_api_url, basetemp inside TMPDIR): 226 passed, 1 skipped on both (raw/lockstep-main.log, lockstep-pr12.log): running two copies at once does not cause these failures.
- The stop-point file alone: 71 passed in 167.61 s.

## (5) D and C2 -v runs (basetemp inside TMPDIR) so far
Counted from the recovered logs at about 10:34Z: D (PR #14 d5b4451) 1942 PASSED, 0 FAILED up to tests/test_path_confinement.py; C2 (main) 1596 PASSED, 0 FAILED up to tests/test_mutants_more.py. Both are past test_load_tools, test_n8n_api_url and test_http. Final counts come when they end.
