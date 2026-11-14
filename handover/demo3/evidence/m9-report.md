# m9 evidence report (facts only, no judgement)

Checkpoint 2026-11-14T03:54Z: run at about 63%, data folder had appeared at 03:52:00 (see below).

## Command (verbatim, wrapped in bash -c so rc is written after python)
```
cd /home/user/work/m9-tree && PYTHONPATH=/home/user/work/priv/watch DATAWATCH_REPO=/home/user/work/m9-tree DATAWATCH_OUT=/home/user/work/priv/m9-tmp/datawatch.txt TMPDIR=/home/user/work/priv/m9-tmp /home/user/work/py313-venv/bin/python -m pytest -p datawatch -q -p no:cacheprovider --basetemp=/home/user/work/priv/m9-tmp/bt -rs --durations=0 --durations-min=1.0 > /home/user/work/priv/m9-tmp/full.log 2>&1; echo rc=$? >> /home/user/work/priv/m9-tmp/full.log
```
No gitleaks on PATH, GITLEAKS_BIN and DPLD_REQUIRE_SCAN unset. Tree HEAD f3c39cf.

## Result
- Summary line: `3684 passed, 199 skipped in 892.56s (0:14:52)`
- rc=0. Started 2026-11-14T03:45:42Z, ended 2026-11-14T04:00:36Z (wall 14 min 54 s by clock).
- Failures: none.

## datawatch lines (verbatim)
```
start present=False
03:52:00 APPEARED (dir) after tests/test_mode_safety.py::test_reset_sh_refuses_when_ps_is_missing
end present=True exit=0
```
Only one APPEARED line and no GONE line: the data folder was created at 03:52:00 after the test named above and stayed to the end (`end present=True`).

## Tree before / after
Before: `ls data` -> No such file or directory; `git status --porcelain --ignored` -> empty.
After (/home/user/work/priv/m9-tmp/after.txt): `ls data` printed nothing (folder exists, empty; `ls -la` shows it created Nov 14 03:58 dir mtime, parent mtime 03:51); `git status --porcelain --ignored` lists only __pycache__ folders:
```
!! demo_only/__pycache__/
!! load_tools/__pycache__/
!! scripts/__pycache__/
!! src/lead_desk/__pycache__/
!! tests/__pycache__/
!! tools/__pycache__/
f3c39cf
```
The empty data folder does not appear in git status (git does not list empty folders).

## Skip reasons (SKIPPED [n] lines, 15 lines)
```
SKIPPED [24] tests/test_gitleaks_exceptions.py:145: no gitleaks program (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure
SKIPPED [2] tests/test_gitleaks_semgrep_lock.py:38: no gitleaks program on PATH (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure
SKIPPED [1] tests/test_hygiene.py:150: no gitleaks program on PATH (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure
SKIPPED [1] tests/test_hygiene.py:344: no gitleaks program on PATH (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure
SKIPPED [1] tests/test_hygiene.py:533: no gitleaks program on PATH (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure
SKIPPED [1] tests/test_hygiene.py:580: no gitleaks program on PATH (set GITLEAKS_BIN)
SKIPPED [22] tests/test_mode_safety.py:110: could not import 'playwright.sync_api': No module named 'playwright'
SKIPPED [1] tests/test_n8n_api_url.py:510: root (and Windows) can read a file with no permissions
SKIPPED [28] tests/test_portal_browser.py:27: could not import 'playwright.sync_api': No module named 'playwright'
SKIPPED [113] tests/test_portal_lead_pages.py:113: could not import 'playwright.sync_api': No module named 'playwright'
SKIPPED [1] tests/test_portal_wording_and_masking.py:171: could not import 'playwright.sync_api': No module named 'playwright'
SKIPPED [1] tests/test_portal_wording_and_masking.py:204: could not import 'playwright.sync_api': No module named 'playwright'
SKIPPED [1] tests/test_portal_wording_and_masking.py:257: could not import 'playwright.sync_api': No module named 'playwright'
SKIPPED [1] tests/test_server_hardening.py:224: measurement run: set LEAD_DESK_LOAD_N
SKIPPED [1] tests/test_stall_eviction.py:526: the reset that destroys the reply happens on Windows only
```
Grouped: gitleaks missing 24+2+1+1+1+1 = 30; playwright not installed 22+28+113+1+1+1 = 166; root can read file with no permissions 1; LEAD_DESK_LOAD_N measurement run 1; Windows-only reset 1. Sum 30+166+1+1+1 = 199, equals the 199 in the summary line.

## 25 slowest test durations (verbatim from the log)
```
32.69s call     tests/test_hygiene.py::test_hygiene_scan_public
28.39s call     tests/test_desk_edge_cases.py::test_burst_distinct_emails
17.52s call     tests/test_desk_http_edge_cases.py::test_startup_50_pending
15.52s call     tests/test_desk_edge_cases.py::test_startup_fast_reaper_sends
10.06s call     tests/test_infra.py::test_connection_pragmas_and_busy_503
10.04s call     tests/test_later_approval.py::test_decision_busy_is_503
10.02s call     tests/test_mutants_more.py::test_mutant_resolve_size_check_removed
9.96s call     tests/test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[_clean]
7.41s call     tests/test_portal_api.py::test_big_book_is_fast_and_cheap
7.06s call     tests/test_desk_http_edge_cases.py::test_receipt_write_retries_7s
7.06s call     tests/test_desk_http_edge_cases.py::test_decision_write_retries_7s
6.56s call     tests/test_desk_edge_cases.py::test_burst_same_email
6.18s call     tests/test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[_LOCAL_BROKEN]
5.70s call     tests/test_http.py::test_second_desk_refuses_to_start
5.16s call     tests/test_ledger_and_bind_retry.py::test_port_taken_for_good_exits_with_its_own_code
5.08s call     tests/test_desk_http_edge_cases.py::test_person_retry_resets_the_count
5.01s call     tests/test_mutants_more.py::test_mutant_resolve_413_no_drain
4.44s call     tests/test_path_confinement.py::test_a_real_run_with_every_path_outside_the_allowed_folders_runs_to_the_end
4.28s call     tests/test_reset_scripts.py::test_reset_sh_waits_for_a_desk_that_needs_a_few_seconds_to_stop
4.28s call     tests/test_clock_steps.py::test_dry_run_survives_a_wall_clock_step[3600.0]
4.25s call     tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end
4.23s call     tests/test_fakes_body_before_answer.py::test_the_desks_early_replies_leave_no_reset_under_a_late_body
4.07s call     tests/test_real_check_dry.py::test_dry_fakes_leave_no_certificate_or_key_folder_behind
4.07s call     tests/test_desk_http_edge_cases.py::test_failed_only_after_cap
4.01s call     tests/test_clock_steps.py::test_dry_run_survives_a_wall_clock_step[-120.0]
```

## Time per test file
Partial: `--durations-min=1.0` printed only the 126 setup/call/teardown entries of 1.0 s or more, so these sums cover only those entries and are not full file times. Top by sum of printed entries:
```
54.71 s  tests/test_desk_edge_cases.py
48.05 s  tests/test_desk_http_edge_cases.py
38.70 s  tests/test_portal_demo.py
32.69 s  tests/test_hygiene.py
21.37 s  tests/test_scrub_n8n_export.py
17.06 s  tests/test_mutants_more.py
15.04 s  tests/test_portal_api.py
14.75 s  tests/test_reset_scripts.py
14.27 s  tests/test_real_check_dry.py
12.09 s  tests/test_later_approval.py
11.93 s  tests/test_http.py
11.53 s  tests/test_infra.py
8.59 s  tests/test_live_claude.py
8.29 s  tests/test_clock_steps.py
7.27 s  tests/test_slow_sender.py
```
