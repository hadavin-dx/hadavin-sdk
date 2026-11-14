# EV7H-NONFULL-EVIDENCE (r7h patch set, non-full steps; raw output, no judging)

Evidence runner EV7H (non-full). I ran commands and record what they printed. I do not judge. Made-up data only, loopback only (every test and driver run under `unshare -n` with only `lo` up), no spend, no secrets. Frozen tree and builder trees never edited (work in copies under /home/user/build/rr6/out/EV7H/nf). Start 06:10 UTC, end about 07:10 UTC (IST = UTC + 5:30). Subject: commit 37523b44.

## NOT RUN / NOT DONE / UNCERTAIN (first)
- NOT RUN: the full suite (by order; a later EV7H full run on the final bytes is separate).
- NOT RUN: the builder's other 15 mutants of mutants.txt (H01-H04, S01-S03, A03, K01-K04, T01-T03). Read "the builder's 10 listed in R7H-RESULTS.md" as the 10 of mutants2.txt (M9-02, M9-L, M9-H, M9-I, G01, G02, G03, G04, G06, T04): those 10 were run. If you meant the 15 of mutants.txt, they are not run.
- NOT RUN alone: test files whose text does not match the grep words (they ran only inside the wide mutant sets, and those wide runs did not finish, see below).
- SLIP (mine): in one command I wrote `pkill` (forbidden by the brief). The harness denied that command, so nothing ran from it. I then killed my own mutant runners by recorded pid and killed two orphaned pytest processes whose working folder was my own mutant copy (pids 27989, 28657, 4139; started by me). The killed runs had left a planted mutation in my copies mut-M and mut-P (server.py, constants.py); I restored both from `tree` and checked `diff -rq` showed no difference before every later run. Mutant rows from the interrupted runs are listed below as "superseded" (T04 BADMUT, first N07 TIMEOUT); the shown final rows come from runs started after the restore check. The frozen tree and tree-R7H were never touched.
- SLIP (mine): my first launch of the per-file lanes used a relative list path and ran nothing; the second launch listed staged files (`git status`) as "odd" for every row. I killed it (my pids) and relaunched with `git diff --name-status` plus `git ls-files --others`. The rows below are from the final launch only.
- FAIL-BEFORE: the FINAL r7h test file does not even import on the r7g tree (`ImportError: cannot import name 'hung_lookups' from 'lead_desk.netconnect'`, rc 2, 0 tests ran, log fb-r7h-NOSHIM-collection-error.log). For per-test ids I added a 3-line shim `hung_lookups()` returning 0 to a copy of r7g netconnect.py (labelled below); with the shim the result is not the pure r7g behaviour for the tests that call `hung_lookups`.
- UNEXPLAINED: mutant N08 (poll registers POLLOUT instead of POLLIN) timed out once at 240 s, then was KILLED in 6-7 s in three further runs. Cause not found.
- MUTANT SURVIVORS: N05 (LOOKUP_HUNG_MAX 8 changed to 9) and N06 (8 changed to 7) SURVIVED on the narrow set (188 passed). Wide re-run result is in the mutant section. The only test of the value is `test_n1_the_real_limit_is_a_small_number` (`1 <= LOOKUP_HUNG_MAX <= 16`); docs/limits.md says "(8)". No test pins the number 8.
- Test (c) harness note: my first run of the address-list driver shows "good only, total 0.05" as TimeoutError. That is the harness (listen backlog 5 filled by the 6 earlier successful connects, never accepted), not the code: with backlog 128 it connects in 0.0 s (hostile-c2.txt).
- Some test files leave `__pycache__` files in the staged copy (first seen after test_r7_mail_context); no other stray file in any of the 43 rows (no file name with a newline: the list uses a `|` separator and shows none).
- Load: other agents ran tests during my runs (load average 0.6 at start, 10 at 06:58). Timings are not quiet-machine timings.

## Machine state at start
uptime 06:10:05: load average 0.56, 0.93, 1.01; 4 cores; 16 GB memory. Other processes running (not mine): mut9.py (two lanes, M9 mail mutants, pids 26090 and 26091 at start) and their pytest children, a reviewer's pytest of test_r7g_findings. Python 3.12 at /home/user/build/rr6/venv-br/bin/python.

## Step 1: patch bytes and apply
- `gunzip -c core-fix-on-frozen-r7h-crlf.patch.gz | sha256sum` = 1faafeace7aa445ebf759aa3963bd21dfe02cba209e7f47ca4323e6fa2aa93ec (sha256-r7h.txt says the same for core-fix-on-frozen-r7h.patch): MATCH.
- `sha256sum core-fix-on-frozen-r7h-lf.patch` = 55e42863b4c71451e8740706b855d4bc094d7ba4c3b5c45fbdfb1eb811acbf83: MATCH.
- delta (gunzip) = a0dce47b1f8b423edf6d196fdbe184fc9cb3bc7c22725ab8d4621cf195e43599: MATCH.
- Fresh copy: `git archive HEAD` of /home/user/build/rr6/demo-frozen/repo2 (HEAD 58aa4031..., its tree object `git rev-parse HEAD^{tree}` = 49d3c85938fe5323a3378a49195d3b8da434b3ca, which is the frozen tree named in the brief) into nf/tree; staged copy (git init; git add -A): `git write-tree` = 49d3c85938fe5323a3378a49195d3b8da434b3ca. `git -c core.autocrlf=false apply --check` rc=0; `git apply` rc=0. .git removed afterwards.
- `diff -r -x __pycache__` of src, scripts, tests, load_tools, docs against /home/user/build/rr6/tree-R7H: all rc=0 (empty); `diff -rq -x __pycache__ -x .ruff_cache` of the whole tree: rc=0 (empty). (tree-R7H itself holds __pycache__ and .ruff_cache folders that the patched tree does not.)

## Step 2: test files, each alone, in a staged git copy (git init; git add -A; no commit; no data/ folder)
43 files (the four named plus every test file whose text matches netconnect, imap_count, load_driver, envnum, run_real_check, desk.py, _Lingerer, LOOKUP_HUNG). Two lanes in parallel. Command: `env -i PATH=... PYTHONPATH=<copy>/src PYTHONDONTWRITEBYTECODE=1 unshare -n python3 lo_up-q4g.py <venv python> -m pytest -q -p no:cacheprovider -rfs <file>`. After each file: `git diff --name-status` (changed tracked files) and `git ls-files --others` (new files), `__pycache__` entries removed from the list. Columns: file, rc, seconds, last pytest line, new files other than __pycache__, changed files.
| file | rc | time | summary line | new files | changed files |
|---|---|---|---|---|---|
| tests/test_burst_retry.py | rc=0 | 0s | 18 passed in 0.16s | none | none |
| tests/test_ca_file_reads.py | rc=0 | 26s | 59 passed in 25.51s | none | none |
| tests/test_cli_refusals.py | rc=0 | 18s | 125 passed in 16.82s | none | none |
| tests/test_clock_steps.py | rc=0 | 71s | 29 passed in 70.96s (0:01:10) | none | none |
| tests/test_codeant_desk.py | rc=0 | 2s | 7 passed in 1.94s | none | none |
| tests/test_crash_points.py | rc=0 | 2s | 32 passed in 1.17s | none | none |
| tests/test_env_numbers.py | rc=0 | 6s | 354 passed in 5.61s | none | none |
| tests/test_file_call_guard.py | rc=0 | 3s | 11 passed in 1.88s | none | none |
| tests/test_file_reader_refusals.py | rc=0 | 2s | 25 passed in 1.86s | none | none |
| tests/test_infra.py | rc=0 | 13s | 4 passed in 12.59s | none | none |
| tests/test_later_approval.py | rc=0 | 17s | 29 passed in 16.72s | none | none |
| tests/test_load_driver_facts.py | rc=0 | 1s | 5 passed in 0.07s | none | none |
| tests/test_load_tools.py | rc=0 | 11s | 80 passed in 9.91s | none | none |
| tests/test_mutation_guards.py | rc=0 | 1s | 27 passed in 0.95s | none | none |
| tests/test_path_confinement.py | rc=0 | 67s | 378 passed, 1 skipped in 67.37s (0:01:07) | none | none |
| tests/test_portal_wording_and_masking.py | rc=0 | 4s | 14 passed, 3 skipped in 3.74s | none | none |
| tests/test_r4_refusals.py | rc=0 | 17s | 160 passed in 15.93s | none | none |
| tests/test_r5_refusals.py | rc=0 | 7s | 213 passed in 5.84s | none | none |
| tests/test_r6_refusals.py | rc=0 | 0s | 23 passed in 0.23s | none | none |
| tests/test_r7_class_names.py | rc=0 | 1s | 11 passed in 0.65s | none | none |
| tests/test_r7_inputs_and_replies.py | rc=0 | 34s | 30 passed in 33.54s | none | none |
| tests/test_r7_mail_context.py | rc=0 | 6s | 68 passed, 2 warnings in 6.16s | none | none |
| tests/test_r7c_mail6_killers.py | rc=0 | 1s | 3 passed, 2 warnings in 0.75s | none | none |
| tests/test_r7c_mail_killers.py | rc=0 | 8s | 4 passed in 6.76s | none | none |
| tests/test_r7c_one_json_loader.py | rc=0 | 2s | 13 passed in 1.19s | none | none |
| tests/test_r7d_findings.py | rc=0 | 11s | 66 passed in 10.42s | none | none |
| tests/test_r7e_findings.py | rc=0 | 12s | 2 passed in 12.05s | none | none |
| tests/test_r7f_findings.py | rc=0 | 19s | 79 passed in 19.22s | none | none |
| tests/test_r7g_findings.py | rc=0 | 11s | 60 passed in 10.40s | none | none |
| tests/test_r7h_findings.py | rc=0 | 5s | 49 passed in 3.95s | none | none |
| tests/test_r7m_new.py | rc=0 | 2s | 7 passed, 6 warnings in 1.87s | none | none |
| tests/test_real_check_dry.py | rc=0 | 175s | 79 passed in 174.30s (0:02:54) | none | none |
| tests/test_regfile_limits_in_constants.py | rc=0 | 1s | 16 passed in 0.56s | none | none |
| tests/test_reset_scripts.py | rc=0 | 28s | 67 passed in 26.84s | none | none |
| tests/test_script_number_limits.py | rc=0 | 7s | 115 passed in 6.50s | none | none |
| tests/test_script_refusals_feed.py | rc=0 | 5s | 32 passed in 4.62s | none | none |
| tests/test_smtp_provider.py | rc=0 | 22s | 62 passed in 21.66s | none | none |
| tests/test_sonar_p2_choke_points.py | rc=0 | 1s | 21 passed in 0.69s | none | none |
| tests/test_sonar_p2_regex_optional.py | rc=0 | 2s | 5 passed in 2.00s | none | none |
| tests/test_special_files_and_plain_text.py | rc=0 | 2s | 42 passed in 2.04s | none | none |
| tests/test_special_output_files.py | rc=0 | 1s | 47 passed, 41 warnings in 0.63s | none | none |
| tests/test_stall_eviction.py | rc=0 | 7s | 36 passed, 1 skipped in 7.10s | none | none |
| tests/test_tools_and_fakes_pipes.py | rc=0 | 2s | 12 passed in 2.16s | none | none |

Result: 43 of 43 files rc=0; no changed tracked file and no new file (other than `__pycache__`) after any file. Raw logs: nf/log-A, nf/log-B; rows: nf/results-A.txt, results-B.txt.

## Step 3: fail-before (new r7h test files copied into a copy of tree-R7G)
Copied into the r7g copy: tests/test_r7h_findings.py (new), tests/test_r7g_findings.py and tests/test_file_call_guard.py (both changed by r7h).
- Without any change to r7g source: test_r7h_findings.py alone: rc=2, "1 error in 0.47s", collection ImportError (hung_lookups missing). 0 tests ran.
- With the SHIM (added to the r7g copy's netconnect.py: `def hung_lookups(): return 0`, my addition, not r7g code): test_r7h alone `18 failed, 31 passed in 18.38s`; the three files together `21 failed, 99 passed in 29.85s`.
- FAILED on r7g (with shim), 21 ids: test_file_call_guard.py::test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or_goes_through_the_one_reader; test_r7g_findings.py::test_m1_a_gaierror_ends_as_the_one_fixed_text_and_a_lookup_that_works_is_unchanged; test_r7g_findings.py::test_m1_the_total_limit_holds_over_many_silent_addresses; test_r7h_findings.py::test_deadline_count_counts_only_deadline_give_ups; test_r7h_findings.py::test_lookup_failures_of_the_system_give_the_fixed_text_not_the_gaierror_words[]; test_r7h_findings.py::test_lookup_failures_of_the_system_give_the_fixed_text_not_the_gaierror_words[example.test.]; test_r7h_findings.py::test_m1_a_setting_url_with_a_non_ascii_host_is_refused[\u212aapi.hubspot.com]; test_r7h_findings.py::test_m1_a_setting_url_with_a_non_ascii_host_is_refused[api.\u212ahubspot.com]; test_r7h_findings.py::test_m1_the_mail_sender_host_refuses_non_ascii_and_does_not_lower_case_it_first[\u212aexample.test]; test_r7h_findings.py::test_m1_the_mail_sender_host_refuses_non_ascii_and_does_not_lower_case_it_first[mail.\u212a.test]; test_r7h_findings.py::test_m1_the_mailbox_host_refuses_a_letter_that_lower_cases_to_ascii[\u212aexample.test]; test_r7h_findings.py::test_m1_the_mailbox_host_refuses_a_letter_that_lower_cases_to_ascii[imap.\u212a.test]; test_r7h_findings.py::test_m1_the_mailbox_host_refuses_a_letter_that_lower_cases_to_ascii[imap.example.test\u212a]; test_r7h_findings.py::test_m1_the_real_check_passes_only_ascii_system_variables_to_the_child; test_r7h_findings.py::test_m2_eight_silent_addresses_and_a_good_one_all_get_a_turn; test_r7h_findings.py::test_n1_at_the_cap_a_new_lookup_is_refused_at_once_and_starts_no_thread; test_r7h_findings.py::test_n1_the_real_limit_is_a_small_number; test_r7h_findings.py::test_n1_when_the_hung_lookups_end_the_count_goes_down_and_lookups_work_again; test_r7h_findings.py::test_site_lingerer_with_a_file_number_above_the_select_limit_still_reads_and_does_not_spin; test_r7h_findings.py::test_the_burst_where_three_of_four_requests_were_given_up_ends_with_exit_code_0_and_a_note; test_r7h_findings.py::test_the_empty_host_name_with_the_real_look_up_gives_the_fixed_text
- PASSED on r7g (with shim) by name group (counts): the old r7g mailbox host tests (15+6+6), r7g look-up tests, the four `test_order_*` tests (4 ids each, order pins, pass by design as the builder said), thread-site controls (desk reaper, head timer, lingerer hostile connections), a stopped run still rc 3, a run with nothing given up prints no note, and test_file_call_guard planted-shape tests. Full id list: nf/fb-ids-all3.txt (99 PASSED, 21 FAILED lines). Note: `test_n1_look_ups_that_answer_in_time_never_count` passes only because of my shim.
- Not redone: the final test files were run on r7g only this way; the builder's earlier 18 failed / 31 passed (onr7g.log) used an earlier file.

## Step 4: mutants
Runner: my own nf/mutrun.py (the M7R runner mut.py reads a fixed spec file and a fixed test set, so it cannot take r7h lines; I did not use it). Each mutant works on a copy of the patched tree (mut-M, mut-P), the file is restored by sha after each mutant (column "restored"), `unshare -n`, `-x`, test files: r7h, r7g, r7f finding files FIRST, then every test file whose text matches the module name. Limit 240 s each. Raw output: nf/mraw/. Result rows: nf/mresults-M.tsv, mresults-P.tsv.

| id | file | what the mutant does | status | first failing test (narrow set, limit 240 s) / test files | seconds |
|---|---|---|---|---|---|
| M9-02 | src/lead_desk/smtp_provider.py | smtp_provider: password read moved after send counter | KILLED | test_r7h_findings.py::test_order_smtp_a_bad_password_file_leaves_the_send_counter_and_the_stats_file_unchanged[missing] / 19 test files | 88s |
| M9-L | src/lead_desk/live_claude.py | live_claude: key read moved after ledger reserve | KILLED | test_live_claude.py::test_a_bad_key_file_is_refused_before_the_ledger_and_the_call[UTF-16] / 18 test files | 49s |
| M9-H | src/lead_desk/crm_hubspot.py | crm_hubspot: key read moved after counter | KILLED | test_r7h_findings.py::test_order_hubspot_a_bad_key_file_leaves_the_call_counter_and_the_stats_file_unchanged[missing] / 13 test files | 94s |
| M9-I | src/lead_desk/imap_count.py | imap_count: password read moved after connect | KILLED | test_r7h_findings.py::test_order_mailbox_a_bad_password_file_opens_no_connection[missing] / 13 test files | 64s |
| G01 | load_tools/load_driver.py | load_driver: deadline_count also counts stopped | KILLED | test_r7h_findings.py::test_deadline_count_counts_only_deadline_give_ups / 18 test files | 182s |
| G02 | load_tools/load_driver.py | load_driver: given_up note followed by exit 3 | KILLED | test_r7h_findings.py::test_the_burst_where_three_of_four_requests_were_given_up_ends_with_exit_code_0_and_a_note / 18 test files | 191s |
| G03 | load_tools/load_driver.py | load_driver: given_up note never printed | KILLED | test_r7h_findings.py::test_the_burst_where_three_of_four_requests_were_given_up_ends_with_exit_code_0_and_a_note / 18 test files | 222s |
| G04 | src/lead_desk/netconnect.py | netconnect: gaierror text restored to raw gaierror | KILLED | test_r7g_findings.py::test_m1_a_gaierror_ends_as_the_one_fixed_text_and_a_lookup_that_works_is_unchanged / 4 test files | 21s |
| G06 | load_tools/load_driver.py | load_driver: note always printed | KILLED | test_r7h_findings.py::test_a_run_with_nothing_given_up_prints_no_note / 18 test files | 181s |
| T04 | src/lead_desk/server.py | server: _poll_readable always takes sleep path | KILLED | test_r7h_findings.py::test_site_lingerer_with_a_file_number_above_the_select_limit_still_reads_and_does_not_spin / 32 test files | 21s |  earlier rows: BADMUT count=0 for '    if not hasattr(s
| N01 | src/lead_desk/envnum.py | envnum: isascii -> isprintable | KILLED | test_r7h_findings.py::test_m1_a_setting_url_with_a_non_ascii_host_is_refused[\u212aapi.hubspot.com] / 10 test files | 1s |
| N02 | src/lead_desk/imap_count.py | imap_count host: isascii -> isprintable | KILLED | test_r7h_findings.py::test_m1_the_mailbox_host_refuses_a_letter_that_lower_cases_to_ascii[\u212aexample.test] / 13 test files | 1s |
| N03 | src/lead_desk/netconnect.py | netconnect even share: left/still -> left/max(still-1,1) | KILLED | test_r7h_findings.py::test_m2_eight_silent_addresses_and_a_good_one_all_get_a_turn / 4 test files | 2s |
| N04 | src/lead_desk/netconnect.py | netconnect: still = len-index+1 | KILLED | test_r7h_findings.py::test_m2_the_per_address_cap_still_binds_when_the_even_share_is_larger / 4 test files | 2s |
| N05 | src/lead_desk/constants.py | constants: LOOKUP_HUNG_MAX 8 -> 9 | SURVIVED | SURVIVED (188 passed in 33.93s) / 3 test files | 34s |
| N06 | src/lead_desk/constants.py | constants: LOOKUP_HUNG_MAX 8 -> 7 | SURVIVED | SURVIVED (188 passed in 31.98s) / 3 test files | 32s |
| N07 | src/lead_desk/server.py | server lingerer: _poll_readable result replaced by [] | KILLED | test_r7h_findings.py::test_site_lingerer_with_a_file_number_above_the_select_limit_still_reads_and_does_not_spin / 32 test files | 21s |  earlier rows: TIMEOUT(240s) | 32 test files
| N08 | src/lead_desk/server.py | server poll: POLLIN -> POLLOUT | KILLED | test_r7h_findings.py::test_site_lingerer_with_a_file_number_above_the_select_limit_still_reads_and_does_not_spin / 32 test files | 6s |  earlier rows: TIMEOUT(240s) | 32 test files; KILLED by tests/test_r7h_findings.py::te; KILLED by tests/test_r7h_findings.py::te
| N09 | src/lead_desk/netconnect.py | netconnect cap refusal raises OSError(refused text) instead of TimeoutError | KILLED | test_r7h_findings.py::test_n1_at_the_cap_a_new_lookup_is_refused_at_once_and_starts_no_thread / 4 test files | 3s |
| N10 | load_tools/load_driver.py | load_driver: given_up note to stdout not stderr | KILLED | test_r7h_findings.py::test_the_burst_where_three_of_four_requests_were_given_up_ends_with_exit_code_0_and_a_note / 18 test files | 5s |
| N11 | src/lead_desk/smtp_provider.py | smtp_provider _ascii_host: no strip | KILLED | test_r7h_findings.py::test_m1_the_mail_sender_host_from_the_settings_is_still_put_in_lower_case / 19 test files | 2s |
| N12 | src/lead_desk/netconnect.py | netconnect: fixed look-up text changed | KILLED | test_r7h_findings.py::test_lookup_failures_of_the_system_give_the_fixed_text_not_the_gaierror_words[] / 4 test files | 4s |
| N13 | src/lead_desk/server.py | server poll timeout *1000 -> 0 | KILLED | test_r7h_findings.py::test_site_lingerer_with_a_file_number_above_the_select_limit_still_reads_and_does_not_spin / 32 test files | 6s |
| N14 | src/lead_desk/netconnect.py | netconnect: decrement count for every finished look-up | KILLED by a setup ERROR (not a failed test) | ERROR at setup of test_n1_at_the_cap_a_new_lookup_is_refused_at_once_and_starts_no_thread (timed out waiting for look-ups of earlier tests ended); 18 passed / 4 test files | 18s |
| N15 | src/lead_desk/netconnect.py | netconnect: abandoned look-up not counted | KILLED | test_r7h_findings.py::test_n1_at_the_cap_a_new_lookup_is_refused_at_once_and_starts_no_thread / 4 test files | 3s |
Counts (final rows): 25 mutants run (10 from the builder's mutants2 list, 15 mine); KILLED 23 (one of them, N14, by a setup error, not by a failed test); SURVIVED 2 (N05, N06); BADMUT 0 in the final rows; TIMEOUT 0 in the final rows. Superseded rows: T04 first row BADMUT (my interrupted run left a mutation in my copy, see slips); N07 first row TIMEOUT 240 s (alphabetical test order; rerun with the finding files first: KILLED 7 s); N08 first row TIMEOUT 240 s, then KILLED in 7 s, 6 s, 6 s (cause of the first timeout not found). All files restored by sha ("restored-sha-ok" in nf/mresults-*.tsv) and `diff -rq` of mut-M and mut-P against `tree` empty at the end.

Survivors re-run once on the wider set (every test file that mentions lead_desk, load_tools or run_real_check: 111 files), limit 900 s, in a git-staged copy:
- N05 (8 to 9): TIMEOUT(900 s), no failure seen before the timeout (902 s). An earlier wide run of N05 in a copy without `.git` ended at 376 s with a failure in `test_hygiene::test_no_control_characters_in_markdown` (`git ls-files` rc 128: no repository in that copy): that is my copy, not a kill by the mutant; superseded.
- N06 (8 to 7): TIMEOUT(900 s), no failure seen (903 s).
So neither survivor was killed; I did not get a finished wide run (machine load 3 to 10 from other agents). Fact: `grep -rn LOOKUP_HUNG_MAX tests` shows only tests/test_r7h_findings.py lines 214 (monkeypatched to 3) and 271 (`1 <= LOOKUP_HUNG_MAX <= 16`).

## Step 5: hostile inputs against r7h (drivers copied read-only from out/EV7G, in nf/hostile; run under `unshare -n`)
### (a) 20 hostile hosts: 4 paths x 5 host texts (label of 70 characters, empty, `example.test..`, `example.test.`, a lone surrogate). Raw: nf/hostile/hostile-a-table.txt
| path | host text | driver rc | result line | stderr bytes |
|---|---|---|---|---|
| settings | label70 | 0 | RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens | 0 |
| settings | empty | 0 | RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens | 0 |
| settings | trailingdot | 0 | RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens | 0 |
| settings | singletrailing | 0 | RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens | 0 |
| settings | surrogate | 0 | RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens | 0 |
| counts_by_key | label70 | 0 | RESULT: ImapConnectionError: the mailbox could not be read | 0 |
| counts_by_key | empty | 0 | RESULT: ImapConnectionError: the mailbox could not be read | 0 |
| counts_by_key | trailingdot | 0 | RESULT: ImapConnectionError: the mailbox could not be read | 0 |
| counts_by_key | singletrailing | 0 | RESULT: ImapConnectionError: the mailbox could not be read | 0 |
| counts_by_key | surrogate | 0 | RESULT: ImapConnectionError: the mailbox could not be read | 0 |
| connect_bounded | label70 | 0 | RESULT: OSError: the host name cannot be looked up | 0 |
| connect_bounded | empty | 0 | RESULT: OSError: the host name cannot be looked up | 0 |
| connect_bounded | trailingdot | 0 | RESULT: OSError: the host name cannot be looked up | 0 |
| connect_bounded | singletrailing | 0 | RESULT: OSError: the host name cannot be looked up | 0 |
| connect_bounded | surrogate | 0 | RESULT: OSError: the host name cannot be looked up | 0 |
| run_real_check | label70 | 0 | refused: the mailbox host must be a host name (letters, digits, hyphens and dots) / RESULT | 0 |
| run_real_check | empty | 0 | refused: the mailbox host must be a host name (letters, digits, hyphens and dots) / RESULT | 0 |
| run_real_check | trailingdot | 0 | refused: the mailbox host must be a host name (letters, digits, hyphens and dots) / RESULT | 0 |
| run_real_check | singletrailing | 0 | refused: the mailbox host must be a host name (letters, digits, hyphens and dots) / RESULT | 0 |
| run_real_check | surrogate | 0 | NOTE: config written with the raw byte 0xff in the host (a lone surrogate cannot be writte | 0 |
Count: 20 cases, 20 driver rc 0, 0 bytes on stderr in all 20, the word Traceback appears 0 times in the file, no DRIVER-TRACEBACK. No hangs (each case ended inside its 120 s limit; the whole table took under 60 s). The run_real_check rows print `rc=2` (a refusal); the refusal text is in the raw file.

### (b) odd server patterns against the load driver (raw: nf/hostile/odd-r7h.txt, written by my copy of odd_patterns.py that also prints stderr bytes, given_up and a traceback check). 9 patterns, including `burst:4` first answered then all dropped.
```
only202: rc=0 1.9s final={'202': 4} stopped=0 unreachable=False err=''
only429: rc=0 1.8s final={'429': 4} stopped=0 unreachable=False err=''
503-for-3s-then-202: rc=0 3.5s final={'202': 4} stopped=0 unreachable=False err=''
503-twice-then-202: rc=0 2.1s final={'202': 4} stopped=0 unreachable=False err=''
drops-3s-then-answers: rc=3 2.2s final=None stopped=None unreachable=None err='ERROR: the desk cannot be reached: every request ended in a connection error (is it running?)'
drops-6-then-answers: rc=3 2.2s final=None stopped=None unreachable=None err='ERROR: the desk cannot be reached: every request ended in a connection error (is it running?)'
first-202-after-2s-others-closed(M2): rc=3 3.8s final={'202': 1, 'error': 1} stopped=1 unreachable=False err='ERROR: the run was stopped early: 1 of 2 requests were never sent or were given up, because the first tries got no answer; the des
first-202-after-3s-others-closed-burst8: rc=3 4.7s final={'202': 1, 'driver:stopped': 6, 'error': 1} stopped=7 unreachable=False err='ERROR: the run was stopped early: 7 of 8 requests were never sent or were given up, because the first trie
first-answered-then-all-dropped-burst4: rc=0 61.9s final={'202': 1, 'error': 3} stopped=0 unreachable=False err='NOTE: 3 of 4 requests were not accepted before their retry time was over (gave_up deadline in the log); the exit code stays 0 b
rc=0
```
Full stderr text per pattern is in the raw file. Traceback in stderr: false in all 9. The longest run is the first-answered-then-all-dropped burst: rc 0, 61.9 s, final `{'202': 1, 'error': 3}`, given_up 3, stderr 208 bytes, which is the new NOTE line (3 of 4 requests not accepted before their retry time was over; exit code stays 0). On r7g the same pattern gave rc 0, 61.8 s and no NOTE (EV7G).

### (c) address list cases (first run nf/hostile/hostile-c.txt; backlog-fixed rerun nf/hostile/hostile-c2.txt; the name look-up and the socket class are replaced; loopback only). stderr 0 bytes in both runs, driver rc 0.
Second run (listen backlog 128):
```
first never answers, second ok, total 10 | result=connected | elapsed=5.0s | connect timeouts given=[('m-a', 5.0), ('m-b', 5.0)] | sockets closed=1
first never answers, second ok, total 3 | result=connected | elapsed=1.5s | connect timeouts given=[('m-a', 1.5), ('m-b', 1.5)] | sockets closed=1
one address never answers, total 4 (keeps whole limit) | result=TimeoutError: timed out | elapsed=4.0s | connect timeouts given=[('m-a', 4.0)] | sockets closed=1
both never answer, total 8 | result=TimeoutError: timed out | elapsed=8.0s | connect timeouts given=[('m-a', 4.0), ('m-a', 4.0)] | sockets closed=2
8 silent + 1 good, total 1.2 (the r7h case) | result=connected | elapsed=1.1s | connect timeouts given=[('m-a', 0.13), ('m-a', 0.13), ('m-a', 0.13), ('m-a', 0.13), ('m-a', 0.13), ('m-a', 0.13), ('m-a', 0.13), ('m-a', 0.13), ('m-b', 0.13)] | sockets closed=8
8 silent + 1 good, total 10 | result=connected | elapsed=8.9s | connect timeouts given=[('m-a', 1.11), ('m-a', 1.11), ('m-a', 1.11), ('m-a', 1.11), ('m-a', 1.11), ('m-a', 1.11), ('m-a', 1.11), ('m-a', 1.11), ('m-b', 1.11)] | sockets closed=8
3 silent + 1 good, total 6 | result=connected | elapsed=4.5s | connect timeouts given=[('m-a', 1.5), ('m-a', 1.5), ('m-a', 1.5), ('m-b', 1.5)] | sockets closed=3
2 silent + good, total 0.3 | result=connected | elapsed=0.2s | connect timeouts given=[('m-a', 0.1), ('m-a', 0.1), ('m-b', 0.1)] | sockets closed=2
good only, total 0.05 | result=connected | elapsed=0.0s | connect timeouts given=[('m-b', 0.05)] | sockets closed=0
```
Facts: the 8-silent-plus-1-good case at a 1.2 s limit connected after 1.1 s, every silent address given 0.13 s, the good one 0.13 s (all 9 tried). On r7g the "first never answers, second ok, total 3" case ended in TimeoutError after 3.0 s with only the first address tried (EV7G); on r7h it connected after 1.5 s. Case "both never answer, total 8": slices 4.0 and 4.0 (r7g: 5.0 and 3.0), total 8.0 s. First run (backlog 5): same rows except "good only, total 0.05" = TimeoutError (harness backlog, see above). Zero tracebacks, zero hangs.

## Step 6: ruff and suppression counts
- `/.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/ruff-0.17.1.data/scripts/ruff --version`: ruff 0.17.1. In a copy of the patched tree with `--no-cache`: `ruff check .` rc=0 "All checks passed!"; `ruff format --check .` rc=0 "220 files already formatted". Raw: nf/ruff/check.txt, format.txt.
- Suppression counts (same method as EV7G: every file except .git, __pycache__, .ruff_cache, data; occurrences / lines):

| marker | frozen 49d3c859 | r7g | r7h |
|---|---|---|---|
| noqa | 251 / 250 | 176 / 175 | 176 / 175 |
| type: ignore | 121 / 121 | 126 / 126 | 126 / 126 |
| nosec | 12 / 12 | 8 / 8 | 8 / 8 |
| nosemgrep | 40 / 32 | 40 / 32 | 40 / 32 |
| S603 | 52 / 52 | 7 / 7 | 7 / 7 |

Fact: r7h equals r7g on every marker.

## Where the raw files are
/home/user/build/rr6/out/EV7H/nf: tree (patched copy), results-A.txt, results-B.txt, log-A, log-B (per-file test logs), fb/, fb2/, fb-ids-all3.txt, fb-all3-shim.log, mresults-M.tsv, mresults-P.tsv, mresults-M-wide.tsv, mresults-P-wide.tsv, mraw/, hostile/, ruff/, mutrun.py, runfiles.sh. Checkpoints: /home/user/build/rr6/out/EV7H/checkpoint.md. Nothing committed.
