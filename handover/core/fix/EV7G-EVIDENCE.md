# EV7G EVIDENCE (patch round r7g). EVIDENCE RUNNER: raw numbers only, no judgement.

Raw files: /home/user/build/rr6/out/EV7G/ (wrapper.log, pytest-full.log, pytest-stage.log, pytest-rcd.log, pytest-fb.log, raw/mut-*.txt.*, hostile-a-table.txt, hostile-c.txt, odd-r7g.txt, ruff-*.txt, checkpoint.md).
Frozen tree 49d3c859 never edited. Made-up data, loopback only (every test and driver run under `unshare -n` with only lo up), no spend, nothing pushed.

## NOT RUN / CUT / NOT COVERED (first)
1. The FULL suite was run once, in the plain copy (no .git). In the STAGED copy (git init, git add -A, no commit) I ran only the six git-dependent files (test_hygiene, test_nosemgrep_form, test_raw_bidi_chars, test_shell_single_bracket, test_file_call_guard, test_no_placeholders), NOT the whole suite. So `git ls-files -o` in the staged copy was read after those six files only (empty). The stray-file check for the whole suite rests on the plain copy listing (no odd names) plus the tmp-dir walk below.
2. No per-file bisection was needed or run (no odd name appeared). No per-file orphan listing was needed (no orphan appeared).
3. The load-driver odd patterns and M1 drivers were each run once; no repeat for timing noise.
4. Not run: PowerShell, Windows, Python 3.13/3.14 (1 test skipped for that), real mail/HubSpot/model services, no live model call.
5. 8 tests skipped in the full run (reasons in the table below); not run by me in another way.
6. Mutants: only the builder's 15 (r7g). Pre-existing r7f mutant sets were not re-run. No full mutation run.
7. CRLF patch line endings: the LF-patch check was made on an LF checkout copy of the frozen tree only (apply --check), not applied.
8. One of my own driver slips: the first hostile_a run used a password file with a one-letter password, so the counts_by_key path stopped at "the mailbox password file holds no password" before the host look-up; I fixed the driver (FAKE_PASSWORD from demo_only) and re-ran; the table below is the second run. The first run's text is not kept.

## Machine state before start
uptime:  05:12:35 up 22 min,  0 user,  load average: 0.29, 0.52, 0.56
loadavg: 0.29 0.52 0.56 1/126 29386
python/pytest procs: 5
UTC: 2026-11-14T05:12:35Z
nproc 4
(other runners were active on the machine during my runs; load at my full-run start 0.77, end 2.77; max seen 2.97)

## Step 1: patch apply
```
d819e6a0fcce6d7f36f98e4b9d05b9eb688a8b8dded3cbcc622ed3982434c05e  /home/user/hadavin-sdk/handover/core/fix/core-fix-on-frozen-r7g.patch
2e31f323fae6e3cc8850475e50e4958171b72f7b8a38bf491656aaf084ceed81  /home/user/hadavin-sdk/handover/core/fix/core-fix-on-frozen-r7g-lf.patch
```
- sha256 of the CRLF patch equals the value in sha256-r7g.txt (d819e6a0...c05e); LF patch 2e31f323...ed81 also equals.
- Fresh copy of /home/user/build/rr6/demo-frozen/repo2 without data/ and without .git -> /home/user/build/rr6/tree-EV7G. In a staged copy (git init; git add -A; no commit): `git -c core.autocrlf=false apply --check <CRLF patch>` rc=0; `git apply` rc=0 (no output). Then .git removed from the main copy (it must not have one).
- diff -r tree-EV7G vs tree-R7G: src, scripts, tests, load_tools, docs: 0 differences in content. The only differences are in the builder's tree: `__pycache__` folders (src/lead_desk, scripts, tests, tools, demo_only) and `.ruff_cache`. `diff -rq -x __pycache__ -x .ruff_cache tree-EV7G tree-R7G | wc -l` = 0 (whole tree).
- LF patch on an LF checkout copy of frozen (git init, git add -A): `git apply --check core-fix-on-frozen-r7g-lf.patch` rc=0. The CRLF patch on the same copy: rc=0 too.
- Main copy had no data/ at start (checked).

## Step 2: full run (one pytest invocation, plain copy tree-EV7G, no .git)
- Test files: 141 `tests/test_*.py` files (146 python/js/helper entries in tests/ incl. conftest and helpers). Collected: 5483 tests.
- Wrapper (wrapper.log): `full start 2026-11-14T05:12:57Z ... full end 2026-11-14T05:38:57Z rc=1 signal=none` (exit code 1 = tests failed; not cut by a signal; no 137, no 143). Pytest time 1559.68 s (0:25:59).
- Result: **7 failed, 5468 passed, 8 skipped, 60 warnings**.
- The 7 failures (all of the kind "needs a git work tree"; the plain copy has none):
```
FAILED tests/test_hygiene.py::test_no_control_characters_in_markdown - subpro...
FAILED tests/test_hygiene.py::test_hygiene_scan_public - RuntimeError: git gr...
FAILED tests/test_hygiene.py::test_sh_blobs_no_cr - subprocess.CalledProcessE...
FAILED tests/test_hygiene.py::test_the_secret_scan_files_have_no_carriage_return
FAILED tests/test_nosemgrep_form.py::test_no_bare_nosemgrep_comment - Asserti...
FAILED tests/test_raw_bidi_chars.py::test_no_tracked_file_holds_a_raw_direction_control_character
FAILED tests/test_shell_single_bracket.py::test_no_tracked_script_or_workflow_run_block_holds_a_single_bracket_test
```
- 8 skipped:
```
SKIPPED [1] tests/test_book_folder_refusals.py:237: root can read any file
SKIPPED [1] tests/test_n8n_api_url.py:524: root (and Windows) can read a file with no permissions
SKIPPED [1] tests/test_no_placeholders.py:27: not a git work tree (a source archive): the file list is not available
SKIPPED [1] tests/test_path_confinement.py:285: ntpath.isreserved needs Python 3.13
SKIPPED [2] tests/test_r7b_fake_deep_and_head.py:58: only the model fake has /v1/messages
SKIPPED [1] tests/test_server_hardening.py:224: measurement run: set LEAD_DESK_LOAD_N
SKIPPED [1] tests/test_stall_eviction.py:526: the reset that destroys the reply happens on Windows only
```
- Clean-tree guard: did not fire in the plain run (no "REPOSITORY FOLDER CHANGED" text in pytest-full.log or pytest-rcd.log; checked by grep, 0 hits in rcd).

### Staged copy (tree-EV7G-stage: git init, git add -A, no commit), six git-dependent files
`stage start 2026-11-14T05:39:10Z ... stage end 2026-11-14T05:39:57Z rc=0 signal=none`: **300 passed in 47.00 s** (test_hygiene, test_nosemgrep_form, test_raw_bidi_chars, test_shell_single_bracket, test_file_call_guard, test_no_placeholders; test_no_placeholders is skipped in the plain copy and ran here).
(The other git-mentioning files, test_gitleaks_exceptions, test_gitleaks_semgrep_lock, test_r7b_program_helper, test_r7c_program_helper_rejects, test_vendor_hosts, passed in the plain full run.)

### tests/test_real_check_dry.py alone on the final tree (tree-EV7G)
`rcd start 05:40:08Z ... rcd end 05:44:00Z rc=0 signal=none`: **79 passed in 231.70 s**; no "REPOSITORY FOLDER CHANGED" text (grep count 0).

### Stray file named a<newline>b (odd names)
- Plain copy after the full run, `ls` of the repo root (python repr): see list below; `data/` absent.
```
['.codeant', '.coderabbit.yaml', '.deepsource.toml', '.gitattributes', '.github', '.gitignore', '.gitleaks.toml', 'CHANGELOG.md', 'LICENSE', 'README.md', 'SECURITY.md', 'contract.md', 'demo_only', 'docs', 'exceptions.txt', 'load_tools', 'n8n', 'patterns.txt', 'pyproject.toml', 'requirements-browser-win.txt', 'requirements-browser.in', 'requirements-browser.txt', 'requirements-coverage.in', 'requirements-coverage.txt', 'requirements-dev-win.txt', 'requirements-dev.in', 'requirements-dev.txt', 'requirements-semgrep.in', 'requirements-semgrep.txt', 'scripts', 'sonar-project.properties', 'src', 'tests', 'tools', 'versions.md']
```
- Walk of tree-EV7G (360 entries) and tree-EV7G-stage (836 entries) for any name with a control character (code under 32 or 127): **none**.
- Staged copy after its six files: `git ls-files -o --exclude-standard` = `[]`; `git ls-files -o` = 0 names; `git status --short` shows 308 staged additions (the copy itself).
- Walk of the test TMPDIR (out/EV7G/tmp-full) found 5 odd names, all INSIDE pytest's own temp folders where the tests create them on purpose: `.../test_a_file_with_a_line_break_0/repo/a\nb`, `.../test_v2_an_existing_name_with_0/inside/nl\nname`, `.../test_the_sqlite_uri_check_deci3/inside/a\nb.db`, `.../deci1/inside/a\x01b.db`, `.../deci0/inside/a\x7fb.db`. None in the repo root.
- Side fact: tree-EV7G has `__pycache__` folders in demo_only/ and src/lead_desk/ after the run although PYTHONDONTWRITEBYTECODE=1 was set (some test starts a child without it); the guard did not fire.
- Bisect by single files: NOT needed (no odd name in the tree).

## Step 3: processes left behind after the full run
- `ps` (python/pytest/node) right after the run showed only other runners' jobs (EV7F mutev.py and M9 mut9.py pytest children, a playwright node of one of them, a defunct python of theirs) and no process of mine. Orphans with parent 1: only the system `/bin/sh -c ... ccr-ca-store` (not python/pytest). At the end of my work no process with "EV7G" in its command line exists.
- No test file left a process behind; no per-file listing run.

## Step 4: fail-before and mutants
### New tests on r7f (copy of tree-R7F + tests/test_r7g_findings.py from tree-EV7G; tree-EV7G-onR7F)
`fb start 05:44:05Z ... fb end 05:44:48Z rc=1`: **46 failed, 14 passed** (builder said 46/14: same). On r7g the same file: 60 passed (inside the full run: no failure in it). The 46 failing ids are in /home/user/build/rr6/out/EV7G/fail-before-ids.txt. Count by test function: settings_refuse_a_bad_host_name 15, a_name_the_lookup_refuses 7, whatever_the_lookup_raises 6, mailbox_read_with_a_bad_host_name 6, mail_send_with_a_bad_host_name 3, socket_is_closed_on_any_exception 2, and one each: listener_probe_is_bounded, m2_stopped_count_counts_both_kinds, m2_a_request_given_up_by_the_stop, total_limit_holds_over_many_silent_addresses, real_check_refuses_a_bad_mailbox_host, an_empty_box_is_never_indexed, a_first_address_that_never_answers = 46 (sum checked with `uniq -c`: 15+7+6+6+3+2+1+1+1+1+1+1+1 = 46).

### 15 mutants (builder's mut.py run unchanged except paths, on a copy tmp/mut of tree-EV7G; restore checked by sha256 after each; selector = tests/test_r7g_findings.py with -k plus tests/test_r7f_findings.py for D03; -x -q --tb=no; each rc=1 was read in its log: a FAILED test line, never a collection error, so no BADMUT)
| id | file | result | first failing test (from the log) |
|---|---|---|---|
| N01 | netconnect.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_whatever_the_lookup_raises_the_caller_gets_the_fixed_oserror_and_stderr_stays_em |
| N02 | netconnect.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_a_name_the_lookup_refuses_gives_one_fixed_oserror_and_no_traceback[aaaaaaaaaaaaa |
| N03 | netconnect.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_a_gaierror_and_a_lookup_that_works_are_unchanged |
| N04 | imap_count.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_the_mailbox_settings_refuse_a_bad_host_name[aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa |
| N05 | imap_count.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_the_mailbox_settings_still_take_a_plain_host_name[IMAP.Example.Test] |
| A01 | netconnect.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_a_first_address_that_never_answers_does_not_use_the_whole_limit |
| A02 | netconnect.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_a_first_address_that_never_answers_does_not_use_the_whole_limit |
| A03 | netconnect.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_the_total_limit_holds_over_many_silent_addresses |
| A04 | netconnect.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_n1_the_socket_is_closed_on_any_exception[error0] |
| A05 | netconnect.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m1_a_connection_refused_on_every_address_raises_the_last_error |
| D01 | load_driver.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m2_a_request_given_up_by_the_stop_makes_the_run_end_with_exit_code_3 |
| D02 | load_driver.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m2_stopped_count_counts_both_kinds_and_nothing_else |
| D03 | load_driver.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m2_a_request_given_up_by_the_stop_makes_the_run_end_with_exit_code_3 |
| D04 | load_driver.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_m2_a_request_given_up_by_the_stop_makes_the_run_end_with_exit_code_3 |
| L01 | load_driver.py | KILLED, restored-sha-ok | test_r7g_findings.py::test_the_load_driver_listener_probe_is_bounded_when_the_name_look_up_hangs |
Summary: 15 KILLED, 0 SURVIVED, 0 TIMEOUT, 0 BADMUT. sha256 of netconnect.py, imap_count.py, load_driver.py in the copy equal the saved originals after the whole run (mut-orig-sha.txt, `sha256sum -c` OK x3).

## Step 5: hostile drivers on r7g (tree-EV7G)
### (a) M1: bad IMAP host names, verbatim (hostile-a-table.txt). Each case in its own process under unshare -n. "settings" = ImapSettings(host,...); "counts_by_key" = valid settings made with host localhost, host forced in afterwards with object.__setattr__ (the defence at the look-up), then counts_by_key(s, "L"); "connect_bounded" = connect_bounded(host, 9, 2.0); "run_real_check" = scripts/run_real_check.main with REAL_IMAP_1_HOST set in a valid config. Hosts: label70 = 70 x "a" + ".example.test"; empty = ""; trailingdot = "example.test.."; singletrailing = "example.test."; surrogate = "\udcff.example.test". The driver itself exits 0 in all cases; stderr 0 bytes in all 20.
```
== path=settings host=label70 rc=0
stdout:
RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens and dots)
stderr (verbatim, 0 bytes):
== path=settings host=empty rc=0
stdout:
RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens and dots)
stderr (verbatim, 0 bytes):
== path=settings host=trailingdot rc=0
stdout:
RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens and dots)
stderr (verbatim, 0 bytes):
== path=settings host=singletrailing rc=0
stdout:
RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens and dots)
stderr (verbatim, 0 bytes):
== path=settings host=surrogate rc=0
stdout:
RESULT: ImapSettingRefused: the mailbox host must be a host name (letters, digits, hyphens and dots)
stderr (verbatim, 0 bytes):
== path=counts_by_key host=label70 rc=0
stdout:
RESULT: ImapConnectionError: the mailbox could not be read
stderr (verbatim, 0 bytes):
== path=counts_by_key host=empty rc=0
stdout:
RESULT: ImapConnectionError: the mailbox could not be read
stderr (verbatim, 0 bytes):
== path=counts_by_key host=trailingdot rc=0
stdout:
RESULT: ImapConnectionError: the mailbox could not be read
stderr (verbatim, 0 bytes):
== path=counts_by_key host=singletrailing rc=0
stdout:
RESULT: ImapConnectionError: the mailbox could not be read
stderr (verbatim, 0 bytes):
== path=counts_by_key host=surrogate rc=0
stdout:
RESULT: ImapConnectionError: the mailbox could not be read
stderr (verbatim, 0 bytes):
== path=connect_bounded host=label70 rc=0
stdout:
RESULT: OSError: the host name cannot be looked up
stderr (verbatim, 0 bytes):
== path=connect_bounded host=empty rc=0
stdout:
RESULT: gaierror: [Errno -2] Name or service not known
stderr (verbatim, 0 bytes):
== path=connect_bounded host=trailingdot rc=0
stdout:
RESULT: OSError: the host name cannot be looked up
stderr (verbatim, 0 bytes):
== path=connect_bounded host=singletrailing rc=0
stdout:
RESULT: gaierror: [Errno -3] Temporary failure in name resolution
stderr (verbatim, 0 bytes):
== path=connect_bounded host=surrogate rc=0
stdout:
RESULT: OSError: the host name cannot be looked up
stderr (verbatim, 0 bytes):
== path=run_real_check host=label70 rc=0
stdout:
refused: the mailbox host must be a host name (letters, digits, hyphens and dots)
RESULT: rc=2
stderr (verbatim, 0 bytes):
== path=run_real_check host=empty rc=0
stdout:
refused: the mailbox host must be a host name (letters, digits, hyphens and dots)
RESULT: rc=2
stderr (verbatim, 0 bytes):
== path=run_real_check host=trailingdot rc=0
stdout:
refused: the mailbox host must be a host name (letters, digits, hyphens and dots)
RESULT: rc=2
stderr (verbatim, 0 bytes):
== path=run_real_check host=singletrailing rc=0
stdout:
refused: the mailbox host must be a host name (letters, digits, hyphens and dots)
RESULT: rc=2
stderr (verbatim, 0 bytes):
== path=run_real_check host=surrogate rc=0
stdout:
NOTE: config written with the raw byte 0xff in the host (a lone surrogate cannot be written as utf-8)
refused: the config file is not UTF-8 text (or is over 1 MiB): save it as plain UTF-8 text
RESULT: rc=2
stderr (verbatim, 0 bytes):

```
Facts to note: connect_bounded with the empty host and with "example.test." ends in the raw `gaierror` text ("[Errno -2] Name or service not known" / "[Errno -3] Temporary failure in name resolution"), an OSError with no traceback and no host in the text; the other three ends in the fixed text "the host name cannot be looked up". A lone surrogate cannot be written into a utf-8 config file, so for run_real_check the driver wrote the raw byte 0xff there: the run ended rc=2 with the config-file-not-UTF-8 line (a different refusal than the host line).

### (b) M2: loopback fake server, 1 worker, 2 threads (odd-r7g.txt, odd_patterns.py of the builder run unchanged on tree-EV7G; each line: rc, seconds, summary final_status, stopped, unreachable, last stderr line)
```
only202: rc=0 1.9s final={'202': 4} stopped=0 unreachable=False err=''
only429: rc=0 1.9s final={'429': 4} stopped=0 unreachable=False err=''
503-for-3s-then-202: rc=0 3.6s final={'202': 4} stopped=0 unreachable=False err=''
503-twice-then-202: rc=0 2.0s final={'202': 4} stopped=0 unreachable=False err=''
drops-3s-then-answers: rc=3 2.2s final=None stopped=None unreachable=None err='ERROR: the desk cannot be reached: every request ended in a connection error (is it running?)'
drops-6-then-answers: rc=3 2.2s final=None stopped=None unreachable=None err='ERROR: the desk cannot be reached: every request ended in a connection error (is it running?)'
first-202-after-2s-others-closed(M2): rc=3 3.8s final={'202': 1, 'error': 1} stopped=1 unreachable=False err='ERROR: the run was stopped early: 1 of 2 requests were never sent or were given up, because the first tries got no answer; the desk answered'
first-202-after-3s-others-closed-burst8: rc=3 4.8s final={'202': 1, 'driver:stopped': 6, 'error': 1} stopped=7 unreachable=False err='ERROR: the run was stopped early: 7 of 8 requests were never sent or were given up, because the first tries got no answer; the desk answered'
first-answered-then-all-dropped-burst4: rc=0 61.8s final={'202': 1, 'error': 3} stopped=0 unreachable=False err=''
rc=0
```
Fact: the asked case (first real request 202 after 2 s, all other connections closed, burst:2) gives rc=3 (3.8 s) with the line "1 of 2 requests were never sent or were given up". The case "first answered, then all dropped, burst:4" ends rc=0 after 61.8 s with final_status {'202': 1, 'error': 3}: same as the builder wrote (unchanged from r7f, per docs/limits.md); I did not re-run it on r7f.

### (c) first address never answers (hostile_c.py; getaddrinfo and the socket class replaced, loopback only; "m-a" never answers, "m-b" is a real loopback listener)
```
first never answers, second ok, total 10 | result=connected | elapsed=5.0s | connect timeouts given=[('m-a', 5.0), ('m-b', 5.0)] | sockets closed=1
first never answers, second ok, total 3 | result=TimeoutError: the look-up of the host name took longer than the time limit | elapsed=3.0s | connect timeouts given=[('m-a', 3.0)] | sockets closed=1
one address never answers, total 4 (keeps whole limit) | result=TimeoutError: timed out | elapsed=4.0s | connect timeouts given=[('m-a', 4.0)] | sockets closed=1
both never answer, total 8 | result=TimeoutError: timed out | elapsed=8.0s | connect timeouts given=[('m-a', 5.0), ('m-a', 3.0)] | sockets closed=2
```
stderr 0 bytes. Fact to note: with a total limit of 3 s (at or under the 5 s per-address slice) the first address takes the whole 3 s and the second address is never tried (second row); with 10 s the second address is tried after 5.0 s and connects (first row). Sockets: every opened socket was closed in all four cases.

### Ruff (pinned /.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/ruff-0.17.1.data/scripts/ruff, version printed `ruff 0.17.1`, run with --no-cache inside tree-EV7G)
- `ruff check .` rc=0: "All checks passed!"
- `ruff format --check .` rc=0: "219 files already formatted"

### Suppression counts (python count over every file of the tree, excluding .git, __pycache__, .ruff_cache, data; occurrences / lines)
| marker | frozen 49d3c859 | r7f | r7g |
|---|---|---|---|
| noqa | 251 / 250 | 176 / 175 | 176 / 175 |
| type: ignore | 121 / 121 | 126 / 126 | 126 / 126 |
| nosec | 12 / 12 | 8 / 8 | 8 / 8 |
| nosemgrep | 40 / 32 | 40 / 32 | 40 / 32 |
| S603 | 52 / 52 | 7 / 7 | 7 / 7 |
Fact: r7g = r7f on every marker. Against frozen, `type: ignore` is +5 (121 to 126): src/lead_desk/imap_count.py -1; tests +1 each in test_ca_file_reads, test_n8n_api_url, test_script_number_limits, test_tools_and_fakes_pipes and +2 in test_cli_refusals (sum +6 -1 = +5). The others are lower or equal.

## Times (UTC, from file times and wrapper.log)
Machine state 05:12:35; full run 05:12:57 to 05:38:57; stage 05:39:10 to 05:39:57; real_check_dry 05:40:08 to 05:44:00; fail-before 05:44:05 to 05:44:48; 15 mutants about 05:45 to 05:46; hostile (a) done 05:46:34; hostile (c) 05:46:57; ruff 05:47; odd patterns (b) done 05:48:27. IST = UTC + 5:30. About 37 min of the 90 min box. Load at full start 0.77, at end 2.77.
