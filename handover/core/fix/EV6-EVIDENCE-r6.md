# EV6 EVIDENCE (final run on the r6 head). Raw numbers, no verdicts.

Started 19:59 UTC (01:29 IST, 14 Nov); written ~21:10 UTC (02:40 IST). Subject: frozen tree 49d3c85938fe5323a3378a49195d3b8da434b3ca (`git write-tree` of tree-EV6 before applying: 49d3c85938fe5323a3378a49195d3b8da434b3ca).

## 0. NOT RUN / NOT CHECKED (first)

* Windows PowerShell scripts (`reset.ps1`, `start_all.ps1`) were never run (no Windows here); only their line endings and whether the patches apply were checked.
* No mutation run, no CodeQL, no SonarCloud, no CodeRabbit, no semgrep run (not in the brief).
* Suite group A ran WITHOUT `--durations=10` (I added the flag to the script after A had started); group B ran with it. No slowest-tests list exists for A.
* A hostile case with a NUL byte in the HubSpot token or the IMAP user cannot be started (the operating system refuses a NUL in an argument or an environment value): rows `ctl-nul` for hubspot_probe and `imap user=nul` show `HARNESS embedded null byte` for old and new; the NUL case was tested only for the key FILE (qualify, run_live_check, n8n_api).
* Peak memory comes from `getrusage(RUSAGE_CHILDREN)` in my wrapper (`/usr/bin/time` does not exist on this machine); the `rss` column is the largest child.
* No `ss` binary: listening sockets were read from /proc/net/tcp inside the namespace (EV5 driver).
* The slow-sender case sends 1 byte per second for 15 s, with Content-Length 100 (a body that never completes).
* `run-hostile.sh` (copied from EV5) begins with `rm -f hostile/results*.jsonl`; it deleted the result files of my own earlier run of the NEW r6 cases (r6, f, f2, g, h, j). I re-ran exactly those parts afterwards (same scripts) and the tables below come from the re-run. The first run's console output of g/h/j/f is kept in `lost-run-logs/` (results agree where compared by eye; not diffed by machine).
* The 0 test failures of both suite groups mean no "failed in the suite" tests exist to re-run alone/twice; the alone list was the one given in the brief.
* Other agents' processes were on this machine (a `pytest tests/test_real_check_dry.py` of another session was seen at 20:21 UTC). Load average values are in the checkpoint listing at the end of this file.
* The brief says ~575-byte rows; the real row from `load_driver` here is 3,527 bytes (an `attempts` list of 2.7 KB). Both a 3,527-byte and an 883-byte 100,000-row log were run (see 5f).

## 1. APPLY

sha256 (`sha256.txt`):
```
0f76796bfc25b71bdacdd005ef87b12f0a5acfcc7ea1f98bf32a203f0f295fa9  core-fix-on-frozen-r6.patch
4f7a84165024022ded4d26c7fafe1e49a40449c13d163309c0974c0168d0a01b  core-fix-on-frozen-r6-lf.patch
c8a45fe45f5f3be4ee007d6bab0ed219a337353dba261608f029f336d52abcea  core-fix-r5-to-r6-delta.patch
```
Raw apply log (`apply.log`):
```
== tree-EV6 CRLF
check rc=0
apply rc=0
== (a) -lf autocrlf=true clone
check rc=0
apply rc=0
== (b) -lf plain archive
error: patch failed: scripts/reset.ps1:12
error: scripts/reset.ps1: patch does not apply
error: patch failed: scripts/start_all.ps1:7
error: scripts/start_all.ps1: patch does not apply
check rc=1
error: patch failed: scripts/reset.ps1:12
error: scripts/reset.ps1: patch does not apply
error: patch failed: scripts/start_all.ps1:7
error: scripts/start_all.ps1: patch does not apply
apply rc=1
== (c) -lf LF-converted archive
check rc=0
apply rc=0
== (d) CRLF plain archive
check rc=0
apply rc=0
== (e) CRLF LF-converted archive
error: patch failed: scripts/reset.ps1:12
error: scripts/reset.ps1: patch does not apply
error: patch failed: scripts/start_all.ps1:7
error: scripts/start_all.ps1: patch does not apply
check rc=1
== (e2) CRLF on LF-converted, apply with --ignore-whitespace (extra info)
check rc=0
== delta on copy of tree-R5
check rc=0
apply rc=0
```
Line endings after each apply (`file`):
```
-- /home/user/build/rr6/tree-EV6
reset.ps1:     ASCII text, with CRLF line terminators
start_all.ps1: ASCII text, with CRLF line terminators
-- /home/user/build/rr6/tmp-EV6/a
reset.ps1:     ASCII text, with CRLF line terminators
start_all.ps1: ASCII text, with CRLF line terminators
-- /home/user/build/rr6/tmp-EV6/b
reset.ps1:     ASCII text, with CRLF line terminators
start_all.ps1: ASCII text, with CRLF line terminators
-- /home/user/build/rr6/tmp-EV6/c
reset.ps1:     ASCII text
start_all.ps1: ASCII text
-- /home/user/build/rr6/tmp-EV6/d
reset.ps1:     ASCII text, with CRLF line terminators
start_all.ps1: ASCII text, with CRLF line terminators
-- /home/user/build/rr6/tmp-EV6/f
reset.ps1:     ASCII text, with CRLF line terminators
start_all.ps1: ASCII text, with CRLF line terminators
```
Summary of which patch applied where (from the log): CRLF patch: tree-EV6 clone yes; (d) plain archive yes; (e) LF-converted archive NO (check rc=1, reset.ps1:12 and start_all.ps1:7; `--ignore-whitespace` check rc=0). -lf patch: (a) autocrlf=true clone yes; (b) plain archive NO (same two files, rc=1); (c) LF-converted archive yes. delta onto copy of tree-R5: yes. Note (b) and (e) did not apply, so no `diff -rq` is meaningful for (e); (b) shows the unpatched tree.

`diff -rq` (ignoring .git, caches, data) (`diff-results.txt`; (b) is the not-applied archive, so it lists everything):
```
== diff -rq tree-EV6 vs tmp-EV6/a
rc=0
== diff -rq tree-EV6 vs tmp-EV6/b
rc=1
== diff -rq tree-EV6 vs tmp-EV6/c
rc=1
== diff -rq tree-EV6 vs tmp-EV6/d
rc=0
== diff -rq tree-EV6 vs tmp-EV6/f
rc=0
== tree-EV6 vs tree-R6
rc=0
```
(lines for the unapplied (b) copy omitted here; full file in `diff-results.txt`.)

tree-EV6 vs tree-R6: `diff -rq` printed nothing, rc=0. (a): rc=0, (d): rc=0, (f): rc=0, (c): only scripts/reset.ps1 and scripts/start_all.ps1 differ (CRLF vs LF).

## 2. FULL SUITE (tree-EV6, unshare -n, no cloud configuration)

Files present in tests/: 110; in group A: 55; in group B: 55; union equals present: True; overlap: 0.

Group A: `rc=0 wall=756s`; pytest summary line: `2347 passed, 3 skipped, 41 warnings in 754.81s (0:12:34)`
Group B: `rc=0 wall=875s`; pytest summary line: `2470 passed, 2 skipped, 9 warnings in 874.36s (0:14:34)`

Skips and slowest tests (raw tail of each log):
```
--- A

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/test_n8n_api_url.py:515: root (and Windows) can read a file with no permissions
SKIPPED [1] tests/test_server_hardening.py:224: measurement run: set LEAD_DESK_LOAD_N
SKIPPED [1] tests/test_stall_eviction.py:526: the reset that destroys the reply happens on Windows only
2347 passed, 3 skipped, 41 warnings in 754.81s (0:12:34)
rc=0 wall=756s
--- B
============================= slowest 10 durations =============================
65.27s call     tests/test_real_check_dry.py::test_dry_fakes_leave_no_certificate_or_key_folder_behind
64.95s call     tests/test_path_confinement.py::test_a_real_run_with_every_path_outside_the_allowed_folders_runs_to_the_end
35.57s call     tests/test_clock_steps.py::test_dry_run_survives_a_wall_clock_step[3600.0]
34.72s call     tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end
34.52s call     tests/test_clock_steps.py::test_dry_run_survives_a_wall_clock_step[-120.0]
34.16s call     tests/test_real_check_dry.py::test_a_dry_run_where_every_send_ends_in_doubt_fails
33.74s call     tests/test_real_check_dry.py::test_a_failed_write_after_a_failed_read_back_keeps_the_result_on_the_screen
33.26s call     tests/test_real_check_dry.py::test_a_failed_crm_read_back_ends_with_counts_a_result_file_and_a_clean_up_note
28.55s call     tests/test_desk_edge_cases.py::test_burst_distinct_emails
17.51s call     tests/test_desk_http_edge_cases.py::test_startup_50_pending
SKIPPED [1] tests/test_book_folder_refusals.py:228: root can read any file
SKIPPED [1] tests/test_path_confinement.py:284: ntpath.isreserved needs Python 3.13
```
### ALONE runs (nothing of mine running next to them)
```
burst.log: (1 durations < 0.005s hidden.  Use -vv to show these durations.) | 1 passed in 6.70s | rc=0 wall=7s
crm1.log: 0.52s call     tests/test_crm_hubspot.py::test_timeout_after_create_then_retry_finds_it_and_does_not_double | 56 passed in 31.71s | rc=0 wall=32s
crm2.log: 0.52s call     tests/test_crm_hubspot.py::test_timeout_after_create_then_retry_finds_it_and_does_not_double | 56 passed in 31.10s | rc=0 wall=31s
drawer1.log: (1 durations < 0.005s hidden.  Use -vv to show these durations.) | 1 passed in 2.78s | rc=0 wall=3s
drawer2.log: (1 durations < 0.005s hidden.  Use -vv to show these durations.) | 1 passed in 2.66s | rc=0 wall=3s
drawer3.log: (1 durations < 0.005s hidden.  Use -vv to show these durations.) | 1 passed in 2.70s | rc=0 wall=4s
portal-lead-pages-file.log: 1.64s call     tests/test_portal_lead_pages.py::test_demo_pick_lists_neutral | 31 passed in 43.65s | rc=0 wall=44s
scrub.log: 1.74s call     tests/test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[MAIL] | 254 passed in 26.63s | rc=0 wall=27s
shell.log: 0.15s call     tests/test_shell_single_bracket.py::test_one_megabyte_of_a_shape_is_scanned_in_linear_time[;a=;a= ] | 146 passed in 4.23s | rc=0 wall=5s
```
Tests that failed in the suite: none (both groups rc=0), so there are no extra alone/second runs.

## 3. FAIL-BEFORE

### 3a. clean frozen2 + only the test files the r6 patch adds/changes (35 files), each alone, `timeout -k 5 300`
```
tests_test_book_folder_refusals.py                      passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.21s ===============================
tests_test_burst_retry.py                               passed=  16 failed=   2 error=   0 [('1', '0s')] =============== 2 failed, 16 passed in 0.13s =========================
tests_test_ca_file_reads.py                             passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.07s ===============================
tests_test_cli_refusals.py                              passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.19s ===============================
tests_test_crash_flag_reads.py                          passed=   0 failed=   0 error=   1 [('1', '0s')] ===================== 1 error in 0.05s ===============================
tests_test_crm_hubspot.py                               passed=  56 failed=   0 error=   0 [('0', '32s')] =================== 56 passed in 31.15s ==============================
tests_test_except_clause_hierarchy.py                   passed=  51 failed=   1 error=   0 [('1', '1s')] =============== 1 failed, 51 passed in 0.36s =========================
tests_test_file_call_guard.py                           passed=   8 failed=   1 error=   0 [('1', '2s')] =============== 1 failed, 8 passed in 1.48s ==========================
tests_test_file_reader_refusals.py                      passed=   0 failed=   0 error=   1 [('1', '0s')] ===================== 1 error in 0.10s ===============================
tests_test_hubspot_probe.py                             passed=  41 failed=   1 error=   0 [('1', '4s')] =============== 1 failed, 41 passed in 3.86s =========================
tests_test_lead_step_route.py                           passed=  19 failed=   1 error=   0 [('1', '3s')] =============== 1 failed, 19 passed in 2.26s =========================
tests_test_ledger_amounts.py                            passed= 102 failed=   2 error=   0 [('1', '2s')] ============== 2 failed, 102 passed in 1.08s =========================
tests_test_ledger_and_bind_retry.py                     passed=  12 failed=   1 error=   0 [('1', '8s')] =============== 1 failed, 12 passed in 8.03s =========================
tests_test_live_claude.py                               passed=  52 failed=   6 error=   0 [('1', '19s')] ============== 6 failed, 52 passed in 18.17s =========================
tests_test_load_driver_facts.py                         passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.04s ===============================
tests_test_load_tools.py                                passed=  78 failed=   2 error=   0 [('1', '11s')] ============== 2 failed, 78 passed in 11.07s =========================
tests_test_n8n_api_url.py                               passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.09s ===============================
tests_test_no_terminal_questions.py                     passed=   0 failed=   4 error=   0 [('1', '21s')] ==================== 4 failed in 20.78s ==============================
tests_test_path_confinement.py                          passed= 368 failed=  10 error=   0 [('1', '68s')] === 10 failed, 368 passed, 1 skipped in 67.98s (0:01:07) =============
tests_test_portal_demo.py                               passed= 126 failed=   3 error=   0 [('1', '86s')] ========= 3 failed, 126 passed in 85.67s (0:01:25) ===================
tests_test_r4_refusals.py                               passed=   0 failed=   0 error=   0 [('124', '300s')] (no summary)
tests_test_r5_refusals.py                               passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.08s ===============================
tests_test_r6_refusals.py                               passed=   0 failed=   0 error=   1 [('1', '0s')] ===================== 1 error in 0.06s ===============================
tests_test_real_check_dry.py                            passed=  71 failed=   8 error=   0 [('1', '200s')] ========= 8 failed, 71 passed in 199.54s (0:03:19) ===================
tests_test_regfile_limits_in_constants.py               passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.05s ===============================
tests_test_reset_scripts.py                             passed=  34 failed=  25 error=   0 [('1', '41s')] ============== 25 failed, 34 passed in 40.51s ========================
tests_test_script_number_limits.py                      passed=   0 failed=   0 error=   1 [('1', '0s')] ===================== 1 error in 0.08s ===============================
tests_test_script_refusals_feed.py                      passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.06s ===============================
tests_test_scrub_n8n_export.py                          passed= 254 failed=   0 error=   0 [('0', '26s')] =================== 254 passed in 26.08s =============================
tests_test_smtp_outbox.py                               passed=  54 failed=   0 error=  13 [('1', '4s')] ============== 54 passed, 13 errors in 3.73s =========================
tests_test_sonar_p2_feed_optional.py                    passed=   2 failed=   1 error=   0 [('1', '0s')] =============== 1 failed, 2 passed in 0.05s ==========================
tests_test_special_files_and_plain_text.py              passed=   3 failed=  39 error=   0 [('1', '41s')] ============== 39 failed, 3 passed in 40.46s =========================
tests_test_special_output_files.py                      passed=   8 failed=  39 error=   0 [('1', '57s')] ======== 39 failed, 8 passed, 37 warnings in 55.95s ==================
tests_test_tools_and_fakes_pipes.py                     passed=   0 failed=  12 error=   0 [('1', '51s')] =================== 12 failed in 50.51s ==============================
tests_test_wrapper_setting_refusals.py                  passed=   0 failed=  15 error=   0 [('1', '1s')] ==================== 15 failed in 0.74s ==============================
TOTAL passed-on-old 1355

```
Test files in the list with ZERO failures on old code: `tests/test_crm_hubspot.py` (56 passed), `tests/test_scrub_n8n_export.py` (254 passed). `tests/test_r4_refusals.py` on old code did not finish: rc=124 at 300 s, no summary line. Files with collection ERROR on old code (missing module): see the table (error=1).

List of tests that PASS on old code: `fb-passes-on-old.txt` (1355 lines).
### 3b. delta (r5->r6) test files copied onto a clean copy of tree-R5 (19 files)
```
tests_test_burst_retry.py                               passed=  16 failed=   2 error=   0 [('1', '0s')] =============== 2 failed, 16 passed in 0.10s =========================
tests_test_cli_refusals.py                              passed= 125 failed=   0 error=   0 [('0', '16s')] =================== 125 passed in 15.63s =============================
tests_test_crm_hubspot.py                               passed=  56 failed=   0 error=   0 [('0', '32s')] =================== 56 passed in 31.63s ==============================
tests_test_except_clause_hierarchy.py                   passed=  51 failed=   1 error=   0 [('1', '1s')] =============== 1 failed, 51 passed in 0.33s =========================
tests_test_file_call_guard.py                           passed=   9 failed=   0 error=   0 [('0', '2s')] ==================== 9 passed in 1.25s ===============================
tests_test_file_reader_refusals.py                      passed=  20 failed=   1 error=   0 [('1', '2s')] =============== 1 failed, 20 passed in 1.90s =========================
tests_test_live_claude.py                               passed=  57 failed=   1 error=   0 [('1', '18s')] ============== 1 failed, 57 passed in 17.44s =========================
tests_test_load_tools.py                                passed=  79 failed=   1 error=   0 [('1', '10s')] =============== 1 failed, 79 passed in 9.99s =========================
tests_test_n8n_api_url.py                               passed= 130 failed=   7 error=   0 [('1', '8s')] ========= 7 failed, 130 passed, 1 skipped in 7.24s ===================
tests_test_portal_demo.py                               passed= 126 failed=   3 error=   0 [('1', '86s')] ========= 3 failed, 126 passed in 85.92s (0:01:25) ===================
tests_test_r4_refusals.py                               passed= 150 failed=   0 error=   0 [('0', '19s')] =================== 150 passed in 18.14s =============================
tests_test_r5_refusals.py                               passed= 212 failed=   1 error=   0 [('1', '38s')] ============== 1 failed, 212 passed in 38.26s ========================
tests_test_r6_refusals.py                               passed=   0 failed=   0 error=   1 [('1', '1s')] ===================== 1 error in 0.07s ===============================
tests_test_regfile_limits_in_constants.py               passed=  15 failed=   1 error=   0 [('1', '1s')] =============== 1 failed, 15 passed in 0.86s =========================
tests_test_reset_scripts.py                             passed=  58 failed=   1 error=   0 [('1', '19s')] ============== 1 failed, 58 passed in 18.66s =========================
tests_test_script_refusals_feed.py                      passed=  32 failed=   0 error=   0 [('0', '6s')] ==================== 32 passed in 5.36s ==============================
tests_test_scrub_n8n_export.py                          passed= 254 failed=   0 error=   0 [('0', '28s')] =================== 254 passed in 27.75s =============================
tests_test_sonar_p2_feed_optional.py                    passed=   3 failed=   0 error=   0 [('0', '1s')] ==================== 3 passed in 0.04s ===============================
tests_test_special_output_files.py                      passed=  47 failed=   0 error=   0 [('0', '1s')] ============= 47 passed, 41 warnings in 0.67s ========================
TOTAL passed-on-old 1440

```
List of tests that PASS on r5 code: `fb2-passes-on-old.txt`. The delta list is in `fb-delta-testfiles.txt`; 19 files were run, the table above lists only files with a log.

## 4. LINT
```
ruff 0.17.1
//.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/ruff-0.17.1.data/scripts/ruff: ELF 64-bi
## //.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/ruff-0.17.1.data/scripts/ruff ruff 0.17.1
$ ruff check
All checks passed!
rc=0
$ ruff format --check
183 files already formatted
rc=0
## /home/user/build/rr6/venv-br/bin/ruff ruff 0.17.4
$ ruff check
All checks passed!
rc=0
$ ruff format --check
183 files already formatted
rc=0
## bandit -ll
rc=0
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.12.3
Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01
Run started:2026-11-13 20:01:23.157435+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 15335
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 12
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 12
Files skipped (0):
```
Suppression counts (lines containing the word), frozen vs patched, and every added suppression line (`suppress.txt`):
```
noqa frozen=250 patched=246
type: ignore frozen=121 patched=127
nosec frozen=12 patched=11
nosemgrep frozen=32 patched=32
S603 frozen=52 patched=66
--- added lines containing suppressions (diff of frozen vs patched, tracked+untracked)
+    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})  # noqa: S310 (open_http checks it)
+                except Exception:  # noqa: BLE001 - any parse failure must still leave a visible line
+    except Exception:  # noqa: BLE001  (SystemExit of the parser is not an Exception and passes)
+    return http_only_opener(follow_redirects, use_proxy).open(req, timeout=timeout)  # noqa: S310  # nosec B310
+    import subprocess  # noqa: S404
+    done = subprocess.run(  # noqa: S603
+    import subprocess  # noqa: S404
+    subprocess.run(  # noqa: S603
+        with ctx.wrap_socket(far, server_hostname=name) as c:  # type: ignore[attr-defined]
+import subprocess  # noqa: S404
+            subprocess.run(  # noqa: S603 (a fixed program, no input)
+    r = subprocess.run(  # noqa: S603 (this repository's interpreter and files)
+    assert rrc.folder_cannot_be_made(None) is True  # type: ignore[arg-type]
+        real_mkdir(self, *args, **kwargs)  # type: ignore[arg-type]
+import subprocess  # noqa: S404
+        done = subprocess.run(  # noqa: S603
+            r = subprocess.run(  # noqa: S603
+    r = subprocess.run(  # noqa: S603
+        done = subprocess.run(  # noqa: S603
+        done = subprocess.run(  # noqa: S603
+    proc = subprocess.Popen(  # noqa: S603  (our own script; stopped below)
+        return subprocess.run(  # noqa: S603
+            ["bash", str(REPO / "scripts" / "reset.sh")],  # noqa: S607
+import subprocess  # noqa: S404
+        done = subprocess.run(  # noqa: S603
+        seen.append(kw["key"])  # type: ignore[arg-type]
+        return real(path, max_bytes)  # type: ignore[arg-type]
+    r = subprocess.run(  # noqa: S603
+import subprocess  # noqa: S404
+    done = subprocess.run(  # noqa: S603
+            queue.put(f"ok|{PortalDemo._armed(None, FlagFileHooks(p))}")  # type: ignore[arg-type]
--- added lines >120 cols
1 tree-EV6/README.md
2 tree-EV6/docs/limits.md
3 tree-EV6/docs/settings.md
2 tree-EV6/load_tools/README.md
3 tree-EV6/scripts/reset.ps1
4 tree-EV6/scripts/reset.sh
2 tree-EV6/scripts/start_all.ps1
3 tree-EV6/scripts/start_all.sh

```
## 5. HOSTILE
Old = clean frozen2 clone (tree-old-EV6), new = tree-EV6. Timeout 5 s per case unless noted. Full tables: `hostile-table.md` (every case, old and new: rc, hang, traceback, lines, class-name, typed echo). Counts of rows with a traceback / that hit my timeout:
```
('results-ci-validfacts.jsonl', 'new', 'no-tb') 17
('results-ci-validfacts.jsonl', 'old', 'no-tb') 17
('results-ev5.jsonl', 'new', 'hang') 2
('results-ev5.jsonl', 'new', 'no-tb') 155
('results-ev5.jsonl', 'new', 'tb') 2
('results-ev5.jsonl', 'old', 'hang') 16
('results-ev5.jsonl', 'old', 'no-tb') 133
('results-ev5.jsonl', 'old', 'tb') 24
('results-f.jsonl', 'new', 'no-tb') 5
('results-f.jsonl', 'old', 'no-tb') 5
('results-f2.jsonl', 'new', 'no-tb') 1
('results-f2.jsonl', 'old', 'no-tb') 1
('results-new-cases.jsonl', 'new', 'hang') 2
('results-new-cases.jsonl', 'new', 'no-tb') 141
('results-new-cases.jsonl', 'old', 'hang') 10
('results-new-cases.jsonl', 'old', 'no-tb') 118
('results-new-cases.jsonl', 'old', 'tb') 23
('results-r6.jsonl', 'new', 'no-tb') 66
('results-r6.jsonl', 'new', 'tb') 1
('results-r6.jsonl', 'old', 'hang') 1
('results-r6.jsonl', 'old', 'no-tb') 58
('results-r6.jsonl', 'old', 'tb') 9
('results.jsonl', 'new', 'hang') 1
('results.jsonl', 'new', 'no-tb') 149
('results.jsonl', 'old', 'hang') 26
('results.jsonl', 'old', 'no-tb') 132
('results.jsonl', 'old', 'tb') 17
```
### 5(a)-(e) new r6 cases, raw observations (old / new)

| case | tree | rc | s | lines | traceback | class name in output | typed echoed | observations |
|---|---|---|---|---|---|---|---|---|
| a:qualify key-file=greek | old | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=0; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:qualify key-file=greek | new | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the key file holds no key; connections=0; ledger=exists=False files=[] sizes=[]  |
| a:run_live_check key-file=greek | old | 0 | 0.5 | 10 | True | True | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: models: 1, calls per model: 1, prices dated 2026-11-04 |
| a:run_live_check key-file=greek | new | 0 | 0.5 | 1 | False | False | False | child_rc=2; connections=0; ledger=exists=False files=[] sizes=[] OUT: refused: --key-file: the key file holds no key |
| a:hubspot_probe env token=greek | old | 0 | 0.6 | 13 | False | False | False | child_rc=1; connections=0 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:hubspot_probe env token=greek | new | 0 | 0.7 | 3 | False | False | False | child_rc=2; connections=0 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:n8n_api key-file=greek (unreachable) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| a:n8n_api key-file=greek (unreachable) | new | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file holds no key |
| a:qualify key-file=fullwidth | old | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=0; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:qualify key-file=fullwidth | new | 0 | 0.4 | 0 | False | False | False | exc=LiveTransport; msg=the key file holds no key; connections=0; ledger=exists=False files=[] sizes=[]  |
| a:run_live_check key-file=fullwidth | old | 0 | 0.5 | 10 | True | True | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: models: 1, calls per model: 1, prices dated 2026-11-04 |
| a:run_live_check key-file=fullwidth | new | 0 | 0.5 | 1 | False | False | False | child_rc=2; connections=0; ledger=exists=False files=[] sizes=[] OUT: refused: --key-file: the key file holds no key |
| a:hubspot_probe env token=fullwidth | old | 0 | 0.6 | 13 | False | False | False | child_rc=1; connections=0 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:hubspot_probe env token=fullwidth | new | 0 | 0.6 | 3 | False | False | False | child_rc=2; connections=0 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:n8n_api key-file=fullwidth (unreachable) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| a:n8n_api key-file=fullwidth (unreachable) | new | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file holds no key |
| a:qualify key-file=ctl-esc | old | 0 | 0.4 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=1; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:qualify key-file=ctl-esc | new | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the key file holds no key; connections=0; ledger=exists=False files=[] sizes=[]  |
| a:run_live_check key-file=ctl-esc | old | 0 | 0.5 | 10 | True | True | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: models: 1, calls per model: 1, prices dated 2026-11-04 |
| a:run_live_check key-file=ctl-esc | new | 0 | 0.5 | 1 | False | False | False | child_rc=2; connections=0; ledger=exists=False files=[] sizes=[] OUT: refused: --key-file: the key file holds no key |
| a:hubspot_probe env token=ctl-esc | old | 0 | 0.6 | 13 | False | False | False | child_rc=1; connections=4 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:hubspot_probe env token=ctl-esc | new | 0 | 0.6 | 3 | False | False | False | child_rc=2; connections=0 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:n8n_api key-file=ctl-esc (unreachable) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| a:n8n_api key-file=ctl-esc (unreachable) | new | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file holds no key |
| a:qualify key-file=ctl-nul | old | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=1; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:qualify key-file=ctl-nul | new | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the key file holds no key; connections=0; ledger=exists=False files=[] sizes=[]  |
| a:run_live_check key-file=ctl-nul | old | 0 | 0.5 | 10 | True | True | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: models: 1, calls per model: 1, prices dated 2026-11-04 |
| a:run_live_check key-file=ctl-nul | new | 0 | 0.5 | 1 | False | False | False | child_rc=2; connections=0; ledger=exists=False files=[] sizes=[] OUT: refused: --key-file: the key file holds no key |
| a:hubspot_probe env token=ctl-nul | old | None | 0 | 0 | False | False | None |  OUT: HARNESS embedded null byte |
| a:hubspot_probe env token=ctl-nul | new | None | 0 | 0 | False | False | None |  OUT: HARNESS embedded null byte |
| a:n8n_api key-file=ctl-nul (unreachable) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| a:n8n_api key-file=ctl-nul (unreachable) | new | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file holds no key |
| a:qualify key-file=bom-ok | old | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=0; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:qualify key-file=bom-ok | new | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=1; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:run_live_check key-file=bom-ok | old | 0 | 0.5 | 10 | True | True | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: models: 1, calls per model: 1, prices dated 2026-11-04 |
| a:run_live_check key-file=bom-ok | new | 0 | 0.5 | 1 | False | False | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: stopped, nothing was called: there is no terminal to answer the question on |
| a:hubspot_probe env token=bom-ok | old | 0 | 0.6 | 13 | False | False | False | child_rc=1; connections=0 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:hubspot_probe env token=bom-ok | new | 0 | 0.7 | 3 | False | False | False | child_rc=2; connections=0 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:n8n_api key-file=bom-ok (unreachable) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| a:n8n_api key-file=bom-ok (unreachable) | new | 0 | 0.2 | 1 | False | False | False | child_rc=3 OUT: cannot reach n8n (no answer, refused, timed out, or a network, TLS or protocol fault; deta |
| a:qualify key-file=tab | old | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=1; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:qualify key-file=tab | new | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the key file holds no key; connections=0; ledger=exists=False files=[] sizes=[]  |
| a:run_live_check key-file=tab | old | 0 | 0.5 | 10 | True | True | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: models: 1, calls per model: 1, prices dated 2026-11-04 |
| a:run_live_check key-file=tab | new | 0 | 0.5 | 1 | False | False | False | child_rc=2; connections=0; ledger=exists=False files=[] sizes=[] OUT: refused: --key-file: the key file holds no key |
| a:hubspot_probe env token=tab | old | 0 | 0.6 | 13 | False | False | False | child_rc=1; connections=4 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:hubspot_probe env token=tab | new | 0 | 0.6 | 3 | False | False | False | child_rc=2; connections=0 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:n8n_api key-file=tab (unreachable) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| a:n8n_api key-file=tab (unreachable) | new | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file holds no key |
| a:qualify key-file=good | old | 0 | 0.5 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=1; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:qualify key-file=good | new | 0 | 0.4 | 0 | False | False | False | exc=LiveTransport; msg=the model service could not be reached in time; connections=1; ledger=exists=True files=['ledger-q', 'ledger-q.lock'] sizes=[146, 0]  |
| a:run_live_check key-file=good | old | 0 | 0.5 | 10 | True | True | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: models: 1, calls per model: 1, prices dated 2026-11-04 |
| a:run_live_check key-file=good | new | 0 | 0.5 | 1 | False | False | False | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: stopped, nothing was called: there is no terminal to answer the question on |
| a:hubspot_probe env token=good | old | 0 | 0.6 | 13 | False | False | False | child_rc=1; connections=4 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:hubspot_probe env token=good | new | 0 | 0.6 | 13 | False | False | False | child_rc=1; connections=4 OUT: planned calls: 7 (hard budget 8 incl. retries and the fallback delete) |
| a:n8n_api key-file=good (unreachable) | old | 0 | 0.2 | 1 | False | True | False | child_rc=1 OUT: cannot reach n8n (URLError: ConnectionRefusedError) |
| a:n8n_api key-file=good (unreachable) | new | 0 | 0.2 | 1 | False | False | False | child_rc=3 OUT: cannot reach n8n (no answer, refused, timed out, or a network, TLS or protocol fault; deta |
| a:run_live_check key-file=fifo | old | 0 | 0.5 | 10 | True | True | None | child_rc=1; connections=0; ledger=exists=False files=[] sizes=[] OUT: models: 1, calls per model: 1, prices dated 2026-11-04 |
| a:run_live_check key-file=fifo | new | 0 | 0.5 | 1 | False | False | None | child_rc=2; connections=0; ledger=exists=False files=[] sizes=[] OUT: refused: --key-file: the key file cannot be read |
| a:qualify key-file=fifo | old | -9 | 25.0 | 0 | False | False | None |   |
| a:qualify key-file=fifo | new | 0 | 0.5 | 0 | False | False | None | exc=LiveTransport; msg=the key file cannot be read; connections=0; ledger=exists=False files=[] sizes=[]  |
| a:n8n_api key-file=fifo | old | 0 | 8.1 | 0 | False | False | None | child_rc=TIMEOUT  |
| a:n8n_api key-file=fifo | new | 0 | 0.2 | 1 | False | False | None | child_rc=1 OUT: the n8n API key file cannot be read |
| a:imap user=cr | old | 0 | 0.4 | 0 | False | False | False | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1  |
| a:imap user=cr | new | 0 | 0.4 | 0 | False | False | False | exc=ImapCountError; msg=the mailbox user is empty or has a control character; connections=0  |
| a:imap user=lf | old | 0 | 0.4 | 0 | False | False | False | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1  |
| a:imap user=lf | new | 0 | 0.4 | 0 | False | False | False | exc=ImapCountError; msg=the mailbox user is empty or has a control character; connections=0  |
| a:imap user=crlf | old | 0 | 0.5 | 0 | False | False | False | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1  |
| a:imap user=crlf | new | 0 | 0.4 | 0 | False | False | False | exc=ImapCountError; msg=the mailbox user is empty or has a control character; connections=0  |
| a:imap user=esc | old | 0 | 0.5 | 0 | False | False | False | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1  |
| a:imap user=esc | new | 0 | 0.4 | 0 | False | False | False | exc=ImapCountError; msg=the mailbox user is empty or has a control character; connections=0  |
| a:imap user=nul | old | None | 0 | 0 | False | False | None |  OUT: HARNESS embedded null byte |
| a:imap user=nul | new | None | 0 | 0 | False | False | None |  OUT: HARNESS embedded null byte |
| a:imap user=tab | old | 0 | 0.5 | 0 | False | False | False | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1  |
| a:imap user=tab | new | 0 | 0.4 | 0 | False | False | False | exc=ImapCountError; msg=the mailbox user is empty or has a control character; connections=0  |
| a:imap user=greek | old | 0 | 0.5 | 0 | False | False | False | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1  |
| a:imap user=greek | new | 0 | 0.5 | 0 | False | False | False | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1  |
| b:smtp context AND ca_file | old | 0 | 0.2 | 0 | False | False | None | result=built (no refusal)  |
| b:smtp context AND ca_file | new | 0 | 0.2 | 0 | False | False | None | exc=SettingRefused; msg=DESK_SMTPP_CA_FILE and an ssl_context argument are both given: give only one  |
| b:smtp ca_file only, WRONG-name cert (control) | old | 0 | 0.7 | 0 | False | False | None | exc=SendUnreachable; msg=SSLCertVerificationError; connections=1; server_saw=['HS-FAIL']; password_sent=False  |
| b:smtp ca_file only, WRONG-name cert (control) | new | 0 | 0.6 | 0 | False | False | None | exc=SendUnreachable; msg=SSLCertVerificationError; connections=1; server_saw=['HS-FAIL']; password_sent=False  |
| b:smtp context strict, WRONG-name cert (control) | old | 0 | 0.7 | 0 | False | False | None | exc=SendUnreachable; msg=SSLCertVerificationError; connections=1; server_saw=['HS-FAIL']; password_sent=False  |
| b:smtp context strict, WRONG-name cert (control) | new | 0 | 0.7 | 0 | False | False | None | exc=SendUnreachable; msg=SSLCertVerificationError; connections=1; server_saw=['HS-FAIL']; password_sent=False  |
| b:smtp context weakened AFTER construction, WRONG-name cert | old | 0 | 0.7 | 0 | False | False | None | exc=SendRefused; msg=login refused; connections=1; server_saw=['TLS-OK', 'EHLO example', 'AUTH PLAIN A']; password_sent=True  |
| b:smtp context weakened AFTER construction, WRONG-name cert | new | 0 | 0.6 | 0 | False | False | None | exc=SendRefused; msg=the TLS context: the TLS context given does not check the server certificate and name; connections=0; server_saw=[]; password_sent=False  |
| b:imap context strict, WRONG-name cert (control) | old | 0 | 0.6 | 0 | False | False | None | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1; server_saw=['HS-FAIL']; password_sent=False  |
| b:imap context strict, WRONG-name cert (control) | new | 0 | 0.6 | 0 | False | False | None | exc=ImapConnectionError; msg=the mailbox could not be read; connections=1; server_saw=['HS-FAIL']; password_sent=False  |
| b:imap context weakened AFTER construction, WRONG-name cert | old | 0 | 0.7 | 0 | False | False | None | exc=ImapCountError; msg=the mailbox could not be read; connections=1; server_saw=['TLS-OK', 'CAPABILI']; password_sent=False  |
| b:imap context weakened AFTER construction, WRONG-name cert | new | 0 | 0.6 | 0 | False | False | None | exc=ImapCountError; msg=ssl_context: the TLS context given does not check the server certificate and name; connections=0; server_saw=[]; password_sent=False  |
| c:n8n_api list key-file=bom-5chars (port closed) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| c:n8n_api list key-file=bom-5chars (port closed) | new | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file holds no key |
| c:n8n_api list key-file=5chars (port closed) | old | 0 | 0.2 | 1 | False | True | False | child_rc=1 OUT: cannot reach n8n (URLError: ConnectionRefusedError) |
| c:n8n_api list key-file=5chars (port closed) | new | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file holds no key |
| c:n8n_api list key-file=two-lines (port closed) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| c:n8n_api list key-file=two-lines (port closed) | new | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file has more than one line: it must hold only the key |
| c:n8n_api list key-file=bom-ok (port closed) | old | 0 | 0.2 | 1 | False | False | False | child_rc=1 OUT: the n8n API key file must hold one word of printable ASCII (no space, second line or contr |
| c:n8n_api list key-file=bom-ok (port closed) | new | 0 | 0.2 | 1 | False | False | False | child_rc=3 OUT: cannot reach n8n (no answer, refused, timed out, or a network, TLS or protocol fault; deta |
| c:n8n_api list unreachable port, good key | old | 0 | 0.2 | 1 | False | True | False | child_rc=1 OUT: cannot reach n8n (URLError: ConnectionRefusedError) |
| c:n8n_api list unreachable port, good key | new | 0 | 0.2 | 1 | False | False | False | child_rc=3 OUT: cannot reach n8n (no answer, refused, timed out, or a network, TLS or protocol fault; deta |
| c:n8n_api activate typed name, port closed | old | 0 | 0.2 | 1 | False | True | False | child_rc=1; typed_echoed=False OUT: cannot reach n8n (URLError: ConnectionRefusedError) |
| c:n8n_api activate typed name, port closed | new | 0 | 0.2 | 1 | False | False | False | child_rc=3; typed_echoed=False OUT: cannot reach n8n (no answer, refused, timed out, or a network, TLS or protocol fault; deta |
| c:n8n_api activate typed name, n8n answers empty list | old | 0 | 0.3 | 1 | False | False | True | child_rc=1; typed_echoed=True OUT: 0 workflows named 'CANARY-NAME-7f3a91' |
| c:n8n_api activate typed name, n8n answers empty list | new | 0 | 0.2 | 1 | False | False | False | child_rc=1; typed_echoed=False OUT: 0 workflows have the NAME given (exactly one is needed) |
| d:catcher 1 MiB line | old | 0 | 1.7 | 1 | False | False | None | server_alive_after=True; reply=b'220 catcher ready\r\n'; lines=0 OUT: LISTENING 127.0.0.1 45063 |
| d:catcher 1 MiB line | new | 0 | 1.7 | 1 | False | False | None | server_alive_after=True; reply=b'220 catcher ready\r\n'; lines=0 OUT: LISTENING 41191 |
| e:fakes_server Content-Length=huge | old | 0 | 8.2 | 0 | False | False | None | status=NO ANSWER in 8 s (handler waiting); seconds_to_answer_or_close=8.0  |
| e:fakes_server Content-Length=huge | new | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 413 Request Entity Too Large; seconds_to_answer_or_close=0.0  |
| e:fakes_server Content-Length=neg | old | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fakes_server Content-Length=neg | new | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fakes_server Content-Length=nonnum | old | 0 | 0.2 | 0 | False | False | None | status=closed-by-server; seconds_to_answer_or_close=0.0  |
| e:fakes_server Content-Length=nonnum | new | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fakes_server Content-Length=missing | old | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fakes_server Content-Length=missing | new | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fakes_server Content-Length=slow | old | 0 | 15.2 | 0 | False | False | None | status=None; seconds_to_answer_or_close=None  |
| e:fakes_server Content-Length=slow | new | 0 | 15.2 | 0 | False | False | None | status=None; seconds_to_answer_or_close=None  |
| e:fake_model_server Content-Length=huge | old | 0 | 8.2 | 0 | False | False | None | status=NO ANSWER in 8 s (handler waiting); seconds_to_answer_or_close=8.0  |
| e:fake_model_server Content-Length=huge | new | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 413 Request Entity Too Large; seconds_to_answer_or_close=0.0  |
| e:fake_model_server Content-Length=neg | old | 0 | 0.2 | 0 | False | False | None | status=closed-by-server; seconds_to_answer_or_close=0.0  |
| e:fake_model_server Content-Length=neg | new | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fake_model_server Content-Length=nonnum | old | 0 | 0.1 | 0 | False | False | None | status=closed-by-server; seconds_to_answer_or_close=0.0  |
| e:fake_model_server Content-Length=nonnum | new | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fake_model_server Content-Length=missing | old | 0 | 0.1 | 0 | False | False | None | status=HTTP/1.0 200 OK; seconds_to_answer_or_close=0.0  |
| e:fake_model_server Content-Length=missing | new | 0 | 0.2 | 0 | False | False | None | status=HTTP/1.0 200 OK; seconds_to_answer_or_close=0.0  |
| e:fake_model_server Content-Length=slow | old | 0 | 15.2 | 0 | False | False | None | status=None; seconds_to_answer_or_close=None  |
| e:fake_model_server Content-Length=slow | new | 0 | 15.2 | 0 | False | False | None | status=None; seconds_to_answer_or_close=None  |
| e:fake_hubspot Content-Length=huge | old | 0 | 0.6 | 0 | False | False | None | status=HTTP/1.1 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fake_hubspot Content-Length=huge | new | 0 | 0.6 | 0 | False | False | None | status=HTTP/1.1 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fake_hubspot Content-Length=neg | old | 0 | 0.6 | 0 | False | False | None | status=HTTP/1.1 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fake_hubspot Content-Length=neg | new | 0 | 0.6 | 0 | False | False | None | status=HTTP/1.1 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fake_hubspot Content-Length=nonnum | old | 0 | 0.6 | 0 | False | False | None | status=HTTP/1.1 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fake_hubspot Content-Length=nonnum | new | 0 | 0.6 | 0 | False | False | None | status=HTTP/1.1 400 Bad Request; seconds_to_answer_or_close=0.0  |
| e:fake_hubspot Content-Length=missing | old | 0 | 0.6 | 20 | True | True | None | status=closed-by-server; seconds_to_answer_or_close=0.0 OUT: ---------------------------------------- |
| e:fake_hubspot Content-Length=missing | new | 0 | 0.6 | 20 | True | True | None | status=closed-by-server; seconds_to_answer_or_close=0.0 OUT: ---------------------------------------- |
| e:fake_hubspot Content-Length=slow | old | 0 | 15.1 | 2 | False | False | None | status=None; seconds_to_answer_or_close=None OUT: ---------------------------------------- |
| e:fake_hubspot Content-Length=slow | new | 0 | 15.1 | 2 | False | False | None | status=None; seconds_to_answer_or_close=None OUT: ---------------------------------------- |

Notes on the raw rows: the `rc` column is the exit code of my scenario wrapper; the program's own exit code is `child_rc=` in the observations.  for in-process scenarios (qualify, imap, smtp, imap TLS) the `exc=` text is what my script printed about the exception it caught, not output of the program under test (so `lines=0`). `connections` is the count of TCP connections a loopback listener inside the namespace accepted. For fake_hubspot the traceback comes from the server thread (stderr) and reads `TypeError: 'NoneType' object is not subscriptable` at fake_hubspot.py `_create` (`self._json()['properties']`) when a POST has no Content-Length; in the new tree the slow-sender case ALSO prints a traceback.

### 5(f) check_invariants
```
f:100,000-row real-shape log, valid facts                    old rc=1 wall=7.75s lines=161 peak_rss_MB=2104 tb=False hang=False | #  result  check
f:100,000-row real-shape log, valid facts                    new rc=2 wall=5.28s lines=1 peak_rss_MB=1089 tb=False hang=False | INPUT ERROR: cannot read --requests: a line or the file is too big
f:LOAD_TOTAL_MAX short rows (the limit itself)               old rc=1 wall=0.52s lines=161 peak_rss_MB=79 tb=False hang=False | #  result  check
f:LOAD_TOTAL_MAX short rows (the limit itself)               new rc=1 wall=0.56s lines=161 peak_rss_MB=80 tb=False hang=False | #  result  check
f:LOAD_TOTAL_MAX+1 short rows                                old rc=1 wall=0.58s lines=161 peak_rss_MB=79 tb=False hang=False | #  result  check
f:LOAD_TOTAL_MAX+1 short rows                                new rc=4 wall=0.38s lines=1 peak_rss_MB=51 tb=False hang=False | INPUT ERROR: --requests has more than 100000 rows: a run makes no more than that
f:300 MB file of A as --requests                             old rc=2 wall=0.93s lines=1 peak_rss_MB=620 tb=False hang=False | INPUT ERROR: big300a line 1: not JSON
f:300 MB file of A as --requests                             new rc=2 wall=0.18s lines=1 peak_rss_MB=23 tb=False hang=False | INPUT ERROR: cannot read --requests: a line or the file is too big
f:300 MB file of NUL as --requests                           old rc=2 wall=0.77s lines=1 peak_rss_MB=620 tb=False hang=False | INPUT ERROR: big300nul line 1: not JSON
f:300 MB file of NUL as --requests                           new rc=2 wall=0.16s lines=1 peak_rss_MB=23 tb=False hang=False | INPUT ERROR: cannot read --requests: a line or the file is too big
f2:100,000-row log, ~883-byte rows, valid facts              old rc=1 wall=2.82s lines=161 peak_rss_MB=640 tb=False hang=False | #  result  check
f2:100,000-row log, ~883-byte rows, valid facts              new rc=1 wall=3.24s lines=161 peak_rss_MB=490 tb=False hang=False | #  result  check
```
LOAD_TOTAL_MAX = 100000 (src/lead_desk/constants.py); LOAD_FILE_MAX_BYTES = 256 MiB. The 100,000-row real-shape file is 353,115,290 bytes (3,527 bytes per row); the 883-byte-row file is 88,815,290 bytes.

### 5(g) start_all.sh / reset.sh (copy of each tree in tmp-EV6, python stand-in in a PATH shim, namespace without network, 8 s timeout)
```
{'case': 'g:start_all.sh, python stand-in exits at once', 'tree': 'old', 'rc': 0, 'wall': 0.2, 'hang': False, 'lines': 3, 'tb': False, 'out': 'started: demo servers (keyed outbox) pid 14868, desk pid 14869\nports: desk 8765, demo CRM and outbox 8766 (check with: curl http://127.0.0.1:8765/counts)\nlogs: /home/user/build/rr6/tmp-EV6/g-old/data/g/fakes.log and /home/user/build/rr6/tmp-EV6/g-old/data/g/desk.log'}
{'case': 'g:start_all.sh, desk.pid is a FIFO', 'tree': 'old', 'rc': 1, 'wall': 0.2, 'hang': False, 'lines': 1, 'tb': False, 'out': 'pid files exist: run scripts/reset.sh first'}
{'case': 'g:reset.sh, desk.pid is a FIFO', 'tree': 'old', 'rc': -9, 'wall': 8.0, 'hang': True, 'lines': 0, 'tb': False, 'out': ''}
{'case': 'g:reset.sh, fakes.pid is a FIFO', 'tree': 'old', 'rc': -9, 'wall': 8.0, 'hang': True, 'lines': 0, 'tb': False, 'out': ''}
{'case': 'g:start_all.sh, python stand-in exits at once', 'tree': 'new', 'rc': 3, 'wall': 0.7, 'hang': False, 'lines': 1, 'tb': False, 'out': 'the desk stopped right after it was started: read its log file in the data folder, then run scripts/reset.sh'}
{'case': 'g:start_all.sh, desk.pid is a FIFO', 'tree': 'new', 'rc': 1, 'wall': 0.3, 'hang': False, 'lines': 1, 'tb': False, 'out': 'pid files exist: run scripts/reset.sh first'}
{'case': 'g:reset.sh, desk.pid is a FIFO', 'tree': 'new', 'rc': 6, 'wall': 0.2, 'hang': False, 'lines': 1, 'tb': False, 'out': 'refused: desk.pid is not a plain file; nothing was stopped or deleted (delete the pid file yourself if it is stale)'}
{'case': 'g:reset.sh, fakes.pid is a FIFO', 'tree': 'new', 'rc': 6, 'wall': 0.1, 'hang': False, 'lines': 1, 'tb': False, 'out': 'refused: fakes.pid is not a plain file; nothing was stopped or deleted (delete the pid file yourself if it is stale)'}
```
### 5(h) burst.py (strace -f -e trace=connect,sendto,socket, inside a namespace with no network)
```
{'case': 'h:burst.py --url http://evil.example:1', 'tree': 'old', 'rc': 1, 'wall': 0.3, 'hang': False, 'connect_calls_inet': 6, 'connect_lines': ['14991 connect(3, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("8.8.8.8")}, 16) = -1 ENETUNREACH (Network is unreachable)', '14991 connect(3, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("8.8.4.4")}, 16) = -1 ENETUNREACH (Network is unreachable)', '14991 connect(3, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("8.8.8.8")}, 16) = -1 ENETUNREACH (Network is unreachable)'], 'tb': False, 'out': 'SENT n=1\nSTATUS gaierror=1\nRETRIES busy503=0 refused=0\nMISMATCH sent=0 expected=1'}
{'case': 'h:burst.py --url http://192.0.2.1:1', 'tree': 'old', 'rc': 1, 'wall': 0.2, 'hang': False, 'connect_calls_inet': 1, 'connect_lines': ['15021 connect(3, {sa_family=AF_INET, sin_port=htons(1), sin_addr=inet_addr("192.0.2.1")}, 16) = -1 ENETUNREACH (Network is unreachable)'], 'tb': False, 'out': 'SENT n=1\nSTATUS OSError=1\nRETRIES busy503=0 refused=0\nMISMATCH sent=0 expected=1'}
{'case': 'h:burst.py --url http://evil.example:1', 'tree': 'new', 'rc': 1, 'wall': 0.2, 'hang': False, 'connect_calls_inet': 6, 'connect_lines': ['15026 connect(3, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("8.8.8.8")}, 16) = -1 ENETUNREACH (Network is unreachable)', '15026 connect(3, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("8.8.4.4")}, 16) = -1 ENETUNREACH (Network is unreachable)', '15026 connect(3, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("8.8.8.8")}, 16) = -1 ENETUNREACH (Network is unreachable)'], 'tb': False, 'out': 'SENT n=1\nSTATUS error=1\nRETRIES busy503=0 refused=0\nMISMATCH sent=0 expected=1'}
{'case': 'h:burst.py --url http://192.0.2.1:1', 'tree': 'new', 'rc': 1, 'wall': 0.2, 'hang': False, 'connect_calls_inet': 1, 'connect_lines': ['15031 connect(3, {sa_family=AF_INET, sin_port=htons(1), sin_addr=inet_addr("192.0.2.1")}, 16) = -1 ENETUNREACH (Network is unreachable)'], 'tb': False, 'out': 'SENT n=1\nSTATUS error=1\nRETRIES busy503=0 refused=0\nMISMATCH sent=0 expected=1'}
```
### 5(i) class-name sweep `grep -rn __name__ scripts tools load_tools demo_only` (tree-EV6)
17 hits, every one is `if __name__ == "__main__"`; 0 hits inside print / SystemExit / write / format (`classname-grep.txt`). In the frozen tree the same grep shows 24 hits that are not `__main__`. Extra: `src/` has 60 non-`__main__` hits of `type(e).__name__` (log lines and exception texts), not part of the asked grep.

### 5(j) AST guard, 10 planted shapes (one at a time in scripts/ of a scratch copy; `tests/test_file_call_guard.py`, 9 tests)
```
00-baseline-no-shape             rc=0 9 passed in 1.83s  
01-builtins-alias-open           rc=1 1 failed, 8 passed in 1.63s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
02-getattr-import-os-open        rc=1 1 failed, 8 passed in 1.42s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
03-pathlib-read_text             rc=1 1 failed, 8 passed in 1.44s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
04-io-open                       rc=1 1 failed, 8 passed in 1.59s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
05-os-fdopen                     rc=1 1 failed, 8 passed in 1.71s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
06-socketserver-TCPServer        rc=1 1 failed, 8 passed in 1.52s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
07-asyncio-start_server          rc=1 1 failed, 8 passed in 1.66s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
08-http.server-HTTPServer        rc=1 1 failed, 8 passed in 1.72s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
09-subprocess-Popen-cat          rc=1 1 failed, 8 passed in 1.87s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
10-shutil-copyfile               rc=1 1 failed, 8 passed in 1.64s  test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or
```
In every shape's log the failing assertion names the planted file `scripts/zz_shape_NN.py`. Baseline without a shape: 9 passed.

## 6. WITHOUT PYTHONPATH (env -i), root and non-root (setpriv uid 65534, unshare -n -m, mode-666 /dev/null bind-mounted)
Files (15): `step6-files.txt` = the 14 EV5 files + tests/test_r6_refusals.py.
```
root:    SKIPPED [1] tests/test_book_folder_refusals.py:228: root can read any file | 1212 passed, 2 skipped, 50 warnings in 153.21s (0:02:33) | rc=0 wall=154s
nonroot: SKIPPED [1] tests/test_path_confinement.py:284: ntpath.isreserved needs Python 3.13 | 1189 passed, 2 skipped, 50 warnings in 181.28s (0:03:01) | rc=0 wall=182s
```
The passed counts differ (1212 vs 1189); both runs list 2 skipped. I did not look into which tests are collected only as root.

## Housekeeping and load average
```
19:59:29 START EV6 (started ~19:59 UTC = 01:29 IST) | load average: 104.88, 102.83, 104.71
19:59:54 step1 done; tests: 110 files | load average: 107.19, 103.40, 104.84
20:00:00 suite A start | load average: 105.90, 103.19, 104.77
20:01:36 lint/suppress done (light) | load average: 115.90, 106.78, 105.87
20:04:47 progress check | load average: 16.28, 73.41, 93.99
20:04:59 static sweep done; waiting suite | load average: 13.77, 70.99, 92.98
20:05:41 scripts written | load average: 7.53, 62.22, 89.10
20:05:47 killed chain.sh (A continues); started B manually (load<8, 2 groups) | load average: 6.44, 60.18, 88.15
20:06:03 A ~55%, B running | load average: 5.17, 57.27, 86.75
20:13:05 poll | load average: 1.24, 15.24, 55.77
20:13:16 A ended: rc=0 wall=756s; 2347 passed, 3 skipped, 41 warnings in 754.81s (0:12:34) | load average: 1.05, 14.74, 55.18
20:13:16 fb1 start | load average: 1.05, 14.74, 55.18
20:20:07 B [ 96%], fb 21/35 | load average: 0.91, 4.62, 35.96
20:29:42 fb1 end | load average: 0.31, 1.06, 19.54
20:29:42 fb2 start | load average: 0.31, 1.06, 19.54
20:30:36 fb1 done? fb2 7/19 | load average: 0.55, 1.02, 18.46
20:34:31 fb2 end | load average: 0.77, 0.81, 14.46
20:34:38 fb2 summarized; starting alone runs | load average: 0.71, 0.79, 14.38
20:37:14 alone done | load average: 0.90, 0.80, 12.22
20:37:20 alone done; hostile start | load average: 0.91, 0.81, 12.16
20:41:18 r6 hostile done; starting f g h j | load average: 0.20, 0.54, 9.51
20:41:36 run6b g rc=0 | load average: 0.22, 0.52, 9.31
20:41:37 run6b h rc=0 | load average: 0.22, 0.52, 9.31
20:41:59 run6b j rc=0 | load average: 0.49, 0.56, 9.09
20:42:19 run6b f rc=0 | load average: 0.60, 0.58, 8.96
20:42:53 f/f2/g/h/j done; starting old EV5 drivers (run-hostile.sh) | load average: 0.48, 0.55, 8.64
20:48:49 hostile EV5 drivers running | load average: 0.54, 0.54, 6.05
20:56:57 hostile all done; step 6 start | load average: 0.86, 0.73, 3.85
20:57:10 NOTE: run-hostile.sh deleted hostile/results*.jsonl of my r6/f/f2/g/h/j runs; rerunning them after step 6 | load average: 0.95, 0.76, 3.81
21:00:09 step6 done root rc=0 / nonroot rc=0; rerun r6 hostile | load average: 0.89, 0.95, 3.36
21:03:20 run6 redo done | load average: 0.19, 0.62, 2.77
21:04:27 run6b redo done | load average: 0.76, 0.68, 2.64

```
