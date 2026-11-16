# EVIDENCE.md, EV5, final run on the r5 head (evidence runner: raw output only, no verdicts)

Subject patches (sha256, sha256.txt): core-fix-on-frozen-r5.patch cc61fdbd...f9a25; core-fix-on-frozen-r5-lf.patch ca2bfdf1...8745; core-fix-r4-to-r5-delta.patch b25b56bd...b6f61 (full hashes in sha256.txt).
Frozen tree: `git write-tree` of demo-frozen/repo2 = 49d3c85938fe5323a3378a49195d3b8da434b3ca; frozen2 HEAD commit 58aa4031e911e682ec5702e0641d11cbaf927817. tree-EV5 = fresh clone of frozen2 + the CRLF patch applied (working tree changes, not committed): 53 modified, 22 untracked files (after removing one stray file, see 5.x), 1633 insertions / 393 deletions in tracked files.
Environment: 4 cores, load average 103 to 117 the whole time (other agents' jobs on the same machine, not mine). Timing tests below ran under that load.

## NOT RUN / NOT CHECKED / CAVEATS (read first)
1. Pinned ruff 0.17.1 is not cached in uv and I did not fetch it (no network): ruff run with the venv's 0.17.4 and the installed 0.16.9 only (lint.log).
2. Step 2: 114 files match tests/*.py; 109 test_*.py files were run (group A 54, group B 55). Not run (not test files): tests/conftest.py, crash_launcher.py, desk_env_probe_check.py, edge_case_helpers.py, support.py. The 2 groups ran in parallel with my hostile-case driver (step 5, small short processes) and with the step-3 runs for the last minutes of group B, so "alone" was not true for the groups; the timing tests were re-run alone afterwards (2.x).
3. Step 2 groups: 5 tests failed in the full run (4 in group A, 1 in group B). Re-run alone: all pass except tests/test_sonar_p2_feed_optional.py::test_feed_calls_the_configured_desk_address, which failed in the group run, alone, and again alone (3 of 3 failures; TypeError: _Resp.read() takes 1 positional argument but 2 were given, scripts/http_guard.py:37). tests/test_crm_hubspot.py::test_read_back_list_search_lag_and_archive failed in its first alone run (file run) and passed in a repeat alone (single test and whole file).
4. Step 3: tests/test_r4_refusals.py on the clean frozen2 tree hung on its last test (old code reads a pipe); I killed that pytest with TERM after 201 s (my timeout was 600 s), so that file has no summary line (149 of 150 results printed, rc 143). Two orphan `cat` readers of pipes (pids 1403, 1625, started by old-code reset script tests) were killed by me.
5. Step 5: the machine has no `ss` binary. Listening sockets were read from /proc/net/tcp and /proc/net/tcp6 inside the private network namespace (ss_wrap.py). fake_model_server.py and fakes_server.py have no --host option in this tree (an unknown option is refused rc 2 with the "--host" values you listed); only catcher.py has --host. I also ran each of the three with no --host to see the bind address.
6. Step 5: the first run of the `ss:` cases failed because of the missing `ss` binary and left 7 catcher processes running (pids 5637 5707 6285 6322 6328 6404 6464); I killed them. Those rows were removed and re-run (results-ev5-ss.jsonl). The first run of the n8n_api reply cases used a reply body of the wrong shape (a one-entry list the helper refuses); rows in results-ev5-main.jsonl for "n8n_api:reply ..." are superseded by results-ev5-n8n.jsonl.
7. Step 5: hostile_resultfile.py (EV3/EV4 driver) called write_result("a\nb") directly with the current directory = tree-EV5 and created a file named "a<newline>b" in the tree root at 18:42:49 UTC (12 bytes, content {"x": 1}). I deleted it after the runs. It was produced by the harness calling the function directly (the check function refused that name: "REAL_RESULT_FILE has a bad character in it").
8. Step 5 limits: each case has a 5 s wrapper timeout (30 to 60 s for the dead-desk and big-file cases); a valid address against a closed port runs longer than 5 s in both trees, so those rows show TIMEOUT. The dead-desk times were measured separately (5.x). `class-name` column = my regex finds a Python class name or "Traceback" in the output (regex in mk_table.py); `typed echo` = the typed text appears in the output (only for cases with a typed marker). Peak memory is only available for cases through the wrapper.
9. Not done: PowerShell scripts (scripts/reset.ps1, start_all.ps1): no pwsh on this machine. Real (non-loopback) network, real model, mail: not touched. SMTP/IMAP/HubSpot keys used: made-up files only.
10. Step 6: "14 most relevant new test files" is my choice (listed in 6). The 3 other new test files (test_crash_flag_reads, test_file_call_guard, test_regfile_limits_in_constants, test_special_files_and_plain_text: 4 files) were not in step 6, only in step 2. The first root run of step 6 lost its "rc=" line because I edited run6.sh while it ran; it was re-run (see 6).
11. I did not read any RESULTS.md, review file or builder note.

## 1. APPLY (apply.log, diff-results.txt, crlf-state.txt)
| target | patch | git apply --check | git apply |
|---|---|---|---|
| tree-EV5 (clone of frozen2, with .git) | CRLF | rc 0 | rc 0 |
| (a) clone with core.autocrlf=true | -lf | rc 0 | rc 0 |
| (b) plain `git archive` copy (+ empty git init) | -lf | rc 0 | rc 0 |
| (c) archive copy, *.ps1/*.sh/*.py/*.md converted to LF by sed | -lf | rc 0 | rc 0 |
| (d) plain `git archive` copy | CRLF | rc 0 | rc 0 |
| (e) LF-converted archive copy | CRLF | rc 1: "patch failed: scripts/reset.ps1:12" and "scripts/start_all.ps1:7" | not applied |
| copy of tree-R4 | delta (r4 to r5) | rc 0 | rc 0 |
Note: in (c) after apply, `file` shows scripts/reset.ps1 and start_all.ps1 with CRLF line ends (crlf-state.txt); .gitattributes says `* text=auto eol=lf`. I did not investigate why.
`diff -rq` (excluding .git, caches, __pycache__, data) of results (a), (b), (c), (d), delta-on-R4 each against tree-EV5: no differences (rc 0 each). tree-EV5 against /home/user/build/rr6/tree-R5: no differences (rc 0). (b) was checked first with --check only and then applied for real: rc 0.

## 2. FULL SUITE (full-A.log, full-B.log, groupA.txt, groupB.txt, alone/*.log)
Command per group (run-group.sh): `TMPDIR=<outside> PYTHONPATH=<tree>/src PYTHONDONTWRITEBYTECODE=1 PLAYWRIGHT_BROWSERS_PATH=... GITLEAKS_BIN=... DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 timeout 2400 unshare -n python lo_up-q4g.py <venv python> -m pytest -q -p no:cacheprovider -rfs <files>`.
* Group A (54 files): 4 failed, 2942 passed, 5 skipped, 50 warnings in 1184.05 s; pytest rc=1.
  FAILED: test_scrub_n8n_export.py::test_each_pattern_scans_one_megabyte_of_its_worst_shapes_in_linear_time[URL] (2.14 s, limit 2.0 s), [_LOCAL_BROKEN] (4.39 s), [_clean] (2.14 s and 4.66 s); test_sonar_p2_feed_optional.py::test_feed_calls_the_configured_desk_address (TypeError, see 3 of caveats).
  SKIPPED: test_path_confinement.py:284 (ntpath.isreserved needs Python 3.13); test_n8n_api_url.py:512 (root can read a file with no permissions); test_stall_eviction.py:526 (Windows only); test_book_folder_refusals.py:228 (root can read any file); test_server_hardening.py:224 (measurement run: set LEAD_DESK_LOAD_N).
* Group B (55 files): 1 failed, 1845 passed in 1682.80 s; rc=1. FAILED: test_desk_edge_cases.py::test_burst_same_email.
* Total of the two runs: 5 failed, 4787 passed, 5 skipped; 109 files run.
Alone runs (run-alone.sh, same env and namespace, nothing else of mine running; load average still about 100 from other jobs):
| run | result |
|---|---|
| test_portal_lead_pages.py::test_approve_and_deny_live_in_the_lead_drawer_... run 1 / 2 / 3 | 1 passed in 3.59 s / 4.93 s / 4.18 s, rc 0 each |
| tests/test_portal_lead_pages.py whole file | 31 passed in 118.11 s, rc 0 |
| tests/test_crm_hubspot.py (first alone run) | 1 failed, 55 passed in 42.23 s, rc 1: test_read_back_list_search_lag_and_archive: `assert 0.004652 is None where 0.004652 = wait_visible('RUN9-1', 0.05)` |
| same single test, alone | 1 passed in 1.43 s, rc 0 |
| tests/test_crm_hubspot.py whole file, repeated alone | 56 passed in 46.27 s, rc 0 |
| tests/test_shell_single_bracket.py | 146 passed in 14.61 s, rc 0 (slowest call 0.87 s) |
| re-run of the group failures: test_scrub_n8n_export.py + test_sonar_p2_feed_optional.py + test_desk_edge_cases.py::test_burst_same_email | 1 failed, 257 passed in 46.51 s: only the sonar test failed; the 3 scrub tests passed (slowest call 14.88 s for [_clean], 9.49 s, 4.08 s as total test time) and test_burst_same_email passed (12.96 s) |
| tests/test_sonar_p2_feed_optional.py again alone | 1 failed, 2 passed in 0.07 s, rc 1 |

## 3. FAIL-BEFORE (fb/*.log, fb-summary.txt, passes-on-old.txt, fb-collection-errors.txt, fb-testfiles-all.txt)
Clean clone of frozen2 (tree-FB-EV5, HEAD 58aa4031...), with ONLY the 30 test files that the patch adds or changes copied from tree-EV5 (13 modified + 17 new; list in fb-testfiles-all.txt), each file run alone with `timeout -k 5 600` under `unshare -n`, `-rA --continue-on-collection-errors`.
Totals over the 30 files: 1003 passed, 159 failed (sum of the failed counts printed by pytest per file, see table), 23 collection or setup errors lines counted below, 2 skipped. Table (pytest summary line per file, from fb-summary.txt):
    tests_test_book_folder_refusals.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.18s
    tests_test_burst_retry.py | 16 | 2 | 0 | 0 | 1 | 2 failed, 16 passed in 0.23s
    tests_test_ca_file_reads.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.08s
    tests_test_cli_refusals.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.13s
    tests_test_crash_flag_reads.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.05s
    tests_test_file_call_guard.py | 7 | 1 | 0 | 0 | 1 | 1 failed, 7 passed in 1.32s
    tests_test_file_reader_refusals.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.14s
    tests_test_hubspot_probe.py | 41 | 1 | 0 | 0 | 1 | 1 failed, 41 passed in 10.37s
    tests_test_lead_step_route.py | 19 | 1 | 0 | 0 | 1 | 1 failed, 19 passed in 5.20s
    tests_test_ledger_amounts.py | 102 | 2 | 0 | 0 | 1 | 2 failed, 102 passed in 2.76s
    tests_test_ledger_and_bind_retry.py | 12 | 1 | 0 | 0 | 1 | 1 failed, 12 passed in 11.24s
    tests_test_live_claude.py | 53 | 3 | 0 | 0 | 1 | 5 failed, 53 passed in 28.91s
    tests_test_load_driver_facts.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.04s
    tests_test_load_tools.py | 79 | 1 | 0 | 0 | 1 | 1 failed, 79 passed in 34.31s
    tests_test_n8n_api_url.py | 134 | 3 | 0 | 1 | 1 | 3 failed, 134 passed, 1 skipped in 12.94s
    tests_test_no_terminal_questions.py | 0 | 4 | 0 | 0 | 1 | 4 failed in 21.38s
    tests_test_path_confinement.py | 368 | 3 | 0 | 1 | 1 | 10 failed, 368 passed, 1 skipped in 42.81s
    tests_test_r4_refusals.py | 0 | 0 | 0 | 0 | 143 | NO SUMMARY (killed)
    tests_test_r5_refusals.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.09s
    tests_test_real_check_dry.py | 71 | 8 | 0 | 0 | 1 | 8 failed, 71 passed in 215.69s (0:03:35)
    tests_test_regfile_limits_in_constants.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.08s
    tests_test_reset_scripts.py | 34 | 24 | 0 | 0 | 1 | 24 failed, 34 passed in 46.22s
    tests_test_script_number_limits.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.08s
    tests_test_script_refusals_feed.py | 0 | 0 | 1 | 0 | 1 | 1 error in 0.06s
    tests_test_smtp_outbox.py | 54 | 0 | 13 | 0 | 1 | 54 passed, 13 errors in 5.56s
    tests_test_sonar_p2_feed_optional.py | 2 | 1 | 0 | 0 | 1 | 1 failed, 2 passed in 0.05s
    tests_test_special_files_and_plain_text.py | 3 | 38 | 0 | 0 | 1 | 39 failed, 3 passed in 42.27s
    tests_test_special_output_files.py | 8 | 39 | 0 | 0 | 1 | 39 failed, 8 passed, 37 warnings in 57.71s
    tests_test_tools_and_fakes_pipes.py | 0 | 12 | 0 | 0 | 1 | 12 failed in 50.78s
    tests_test_wrapper_setting_refusals.py | 0 | 15 | 0 | 0 | 1 | 15 failed in 1.33s
    

Collection errors (whole file not collected: 10 files) and their first error line (fb-collection-errors.txt): test_book_folder_refusals (cannot import FOLDER_CANNOT_BE_MADE_BOOK_PROBLEM from lead_desk.desk), test_ca_file_reads (CA_FILE_MAX_BYTES), test_cli_refusals (LIVE_EFFORTS), test_crash_flag_reads (FLAG_FILE_MAX_BYTES), test_file_reader_refusals (FeedRefused from feed), test_load_driver_facts (no module lead_desk.regfile), test_r5_refusals (LOAD_FILE_MAX_BYTES), test_regfile_limits_in_constants (cannot import regfile from lead_desk), test_script_number_limits (no module tools.refusing_args), test_script_refusals_feed (no module refusals). test_smtp_outbox.py: 54 passed and 13 errors at setup (`AssertionError: assert (3 == 2)`).
The count of "1003 passed" is the number of tests that PASS on the old code (list in passes-on-old.txt, 1003 lines). Files with no failing tests on old code at all: none (every changed or new file has at least one failure, error, or was killed); test_r4_refusals.py has no summary (killed, see caveat 4).
Skipped: 2 (test_n8n_api_url.py, test_path_confinement.py).

## 4. LINT (lint.log, suppress.txt)
* `ruff check .` : venv ruff 0.17.4 "All checks passed!" rc 0; installed ruff 0.16.9 "All checks passed!" rc 0.
* `ruff format --check .`: both "181 files already formatted" rc 0 (0.17.4) and rc 0 (0.16.9; see lint.log).
* `bandit -ll -r src tools scripts load_tools demo_only`: rc 0; metrics: Low 12 (confidence High 12), Medium 0, High 0 (the 12 Low are listed in the metrics although -ll was given; the output also has 12 lines "Test in comment: <word> is not a test name or id, ignoring").
* Suppression counts by `git grep -I -E` over *.py *.sh *.ps1 *.toml *.yml (tracked files only; untracked new files counted separately below): noqa 250 frozen -> 259 patched; type: ignore 121 -> 121; nosec 12 -> 11; nosemgrep 29 -> 29; S603 52 -> 53.
* Added lines with a suppression in tracked files: 20 (list in suppress.txt: S310 x2 (one with `# nosec B310`), BLE001 x1, E402 x15, S603 x1, S607 x1). In 17 untracked new files (suppress.txt "untracked files" part): 38 lines (noqa S404, S603, E402, PT011, F401; type: ignore[arg-type], [attr-defined], [union-attr]).
* Added lines (tracked diff + untracked files): 7082; over 100 columns: 922; over 120 columns: 19.

## 5. HOSTILE (hostile-table.md has every case, old and new; raw rows in hostile/results*.jsonl)
old = clean frozen2 clone tree-old-EV5, new = tree-EV5. Counts of rows (cases x 2 trees): results.jsonl 158 cases old / 150 new; results-new-cases.jsonl 141 cases (old tb 23, hang 10; new tb 0, hang 2); results-ev5-main.jsonl 62 cases... see table; Python traceback in output: old 19 + 23 + 17 + 5 (ss rows) + 0 = see hostile-table; new: 2 (both are the dead-desk cases killed by my 30 s wrapper, worker process traceback of the killed pool).
Cases where the NEW tree still ends in TIMEOUT within my wrapper: burst.py and load_driver against http://127.0.0.1:1, http://localhost:1, burst.py http://0.0.0.0:1 (valid or accepted address, nothing listening: they run past 5 s), load_driver --scenario burst:1.5, load_driver unreachable-url, fake_model_server --key-file=good and --port=0 (these are servers that run until killed).
Selected raw results (new tree unless stated; see the table for the rest):
* Servers --host (new tree, listening sockets): catcher.py --host "", 0.0.0.0, "not a host", "bad host!", 256.1.1.1, a 70-char label, full-width letters: rc 2 "refused: --host: must be this computer: localhost or 127.0.0.1", nothing listening. --host localhost and 127.0.0.1: listening only on 127.0.0.1:<port>. --host ::1: rc 2 "refused: --port: cannot be listened on (it is already in use, or not a...". No --host: 127.0.0.1 only for all three servers. fake_model_server and fakes_server: every --host value rc 2 "an option is unknown...". In the old tree 5 `ss` rows have a traceback (see table).
* URLs (burst.py --url, load_driver --base-url), new tree: refused rc 2 for 127.0.0.1:1@evil, 0.0.0.0:1 (load_driver), full-width digits, port 0, port 65536, file:// (FIFO and /etc/hostname), ftp://x@x, http://[::1; load_driver also refuses http://evil.example:1. burst.py http://evil.example:1: rc 1, output "SENT n=1 ... MISMATCH sent=0 expected=1" (the name could not be reached in the namespace; burst.py did not refuse it; same in the old tree).
* load_driver --id-prefix 129 characters, control characters, newline: rc 2 "refused: --id-prefix: cannot be used like this"; typed text not echoed. --scenario burst:1_0, nan, inf, burst:١: rc 2 "ERROR: bad scenario: use burst:N, rate:R:D or dupmix:..." (typed text not echoed).
* Dead desk (dead-desk.log, real wall time, both trees run in parallel): old burst:1 rc 0 wall 33 s, output {"final_status": {"ConnectionRefusedError": 1} ...}; new burst:1 rc 3 wall 34 s "ERROR: the desk cannot be reached: every request ended in a connection error (is it running?)"; old burst:20 rc 0 wall 39 s; new burst:20 rc 3 wall 38 s (same message).
* check_invariants with valid small inputs (a valid empty book made with lead_desk.db.init_schema, facts and one real log row from load_driver): control rc 1 (a check failed: "#  result  check" table); 100,000-row log (about 575 bytes per line, 58 MB): rc 1 (table printed). 300 MB files (A bytes and NUL bytes) for each of --requests, --catcher, --model-log, --crm: rc 2 "INPUT ERROR: cannot read --requests: the file is too big" (and the same for the others; "the CRM dump"). Wrong field values: intended_ts "abc", attempts 5, request_id 5, sent_ts NaN: rc 2 "INPUT ERROR: --requests line 1: <field> must be ..."; --drain with drained_ts "abc", [1], -5: rc 2; drain file with NaN: rc 2 "the file is not JSON that can be..."; facts intended_requests -5, 1.5, true: rc 2. So rc 2 (input refused) differs from rc 1 (a check failed).
* reset.sh and start_all.sh (results-scripts.jsonl): desk.pid as a pipe: old reset.sh: no output, killed by my timeout (wrapper 8 s, outer 14 s) in both desk.pid and fakes.pid cases; new: rc 6 in 0.2 s "refused: desk.pid is not a plain file; nothing was stopped or deleted ...". start_all.sh with a pipe as desk.pid or fakes.pid: rc 1 "pid files exist: run scripts/reset.sh first" (old and new). start_all.sh bad mode: old rc 1 "mode must be keyed or blind", new rc 2 "refused: the mode must be keyed or blind". Leftover processes after each reset case: 0 (pgrep). reset.sh with no pid files: rc 0 in both.
* run_live_check: --cap-run bad with closed stdin (<&-): rc 2 "refused: --cap-run: is not a number"; valid cap with closed stdin: rc 1 "stopped, nothing was called: there is no terminal to answer the question on"; --base-url https://127.0.0.1:99999: rc 2; key file as pipe: rc 2 "the key file cannot be read"; ledger as pipe: rc 2; --model "m=1_0,2" and "m=١,2": rc 2 "needs ID=IN_PRICE,OUT_PRICE"; --max-tokens 0, --timeout nan, --leads 0 and 1001, --runs 0 and 101: rc 2, each with its range text.
* DESK_BIND: desk_setting.py port and lead_desk.server with a 300-char name: rc 0 / rc 1 ("cannot reach the demo servers"), the typed name is not echoed (typed echo False); "[::1]": rc 0 / rc 1; "bad host!": rc 4 "the desk refuses a setting: DESK_BIND and DESK_FAKES_HOST must be plain ASCII text ...".
* run_real_check bad config (11 values + a binary file): every case rc 2 with one "refused: ..." line; class-name column false for all.
* n8n_api: no args, bad command, `import` with no file, all with no key file set: rc 2 usage line. `list` with no key file: rc 1 "N8N_API_KEY_FILE must be the path of ...". Replies from a loopback server (corrected run): 20 MB reply: new rc 1 "n8n answered with a reply that is too big to read (not shown)", child peak 28,700 KB (old: "a body that is not JSON", 89,748 KB); cut-off reply: new rc 1 "n8n answered 200 with a body that is not JSON (not shown)" (old: "cannot reach n8n (IncompleteRead)", a Python class name); small valid reply: rc 0 "w1 inactive" both.
* Secret readers (in-process; made-up files): BOM file: ok (19 characters) for SMTP password, HubSpot key and live key; space inside: SMTP password accepted (12 characters, spaces dropped), HubSpot and live key "holds no key"; two-line, control character, empty, pipe, 100 KB: refused with a fixed sentence (class names SendRefused, CrmConfigError, LiveTransport appear only in my harness line "EXC <Class>: <text>", not in a script's output).
* Empty or blank DESK_SMTPP_CA_FILE and REAL_IMAP_1_CA_FILE: run_real_check rc 2 "refused: <NAME> is empty: remove the line or name a file"; desk_setting.py port with the same env: rc 0 (prints 8765).
* SmtpProviderOutbox given an ssl context with CERT_NONE (check_hostname False) and one with check_hostname False + CERT_REQUIRED: both refused with SettingRefused "the ssl_context argument: the TLS context given does not check th...".
* EV3/EV4 drivers re-used with paths changed to EV5: results.jsonl and results-new-cases.jsonl (FIFO, 100 MB files, CA files, keys, ports, hosts, burst/load/check_invariants options, port already in use, /proc reads): all rows are in hostile-table.md.
* hostile_resultfile.py output: hostile/resultfile-old.out (old tree has no check_result_file/result_path: AttributeError) and resultfile-new.out.

## 6. WITHOUT PYTHONPATH and NON-ROOT (step6-files.txt: 14 files: test_script_number_limits, test_path_confinement, test_cli_refusals, test_file_reader_refusals, test_script_refusals_feed, test_special_output_files, test_tools_and_fakes_pipes, test_load_driver_facts, test_ca_file_reads, test_no_terminal_questions, test_wrapper_setting_refusals, test_r4_refusals, test_r5_refusals, test_book_folder_refusals)
Run script run6.sh, `env -i` environment with no PYTHONPATH.
* Root (uid 0): see the end of this file (step6-root.log).
* uid/gid 65534 (`setpriv --reuid 65534 --regid 65534 --clear-groups`) inside `unshare -n -m`, a mode-666 character device (1,3) bind-mounted over /dev/null for that namespace only (host `ls -l /dev/null` after: crw-r--r-- 1 root, unchanged; step6-nonroot.log first line shows crw-rw-rw- inside the namespace); lo brought up before dropping rights: 1189 passed, 2 skipped (test_path_confinement.py:192 needs root to start as another user; :284 ntpath.isreserved needs Python 3.13) in 228.07 s, rc=0 (step6-nonroot.log). An earlier non-root attempt failed at the lo_up step (PermissionError: not permitted, since lo_up needs root); I changed run6.sh to bring lo up first.

## Cleanup and counts
