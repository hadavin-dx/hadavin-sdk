# EVIDENCE RUNNER report EV2 (raw record, no verdict)
Run 2026-11-13 16:01 to ~16:31 UTC (21:31 to ~22:01 IST). Patch under test: /home/user/build/rr6/out/R2/core-fix-on-frozen-r2.patch. RESULTS.md was not read.

## 0. Facts and things that differ from the brief (read first)
* A directory /home/user/build/rr6/tree-EV2 already existed (older, detached HEAD 61ded9e, modified files). I did not use or delete it: renamed to tree-EV2.stale-before-run (not mine; the lead may delete it). A fresh clone was made as tree-EV2.
* The brief names SmtpProviderOutbox._context_from_file for the hostile SMTP CA test. That function does NOT exist on the old (frozen) code (AttributeError), so I used the constructor SmtpProviderOutbox(ProviderSettings(..., ca_file=X)) on both trees (it calls the helper on new code).
* A real run_real_check run (SMTP CA file, HubSpot key file, SMTP password file) reads those files only AFTER the "Start? [y/N]" question, which I never answer. So through run_real_check, SMTP CA / key / password FIFO cases stop at the question (rc=1) on old AND new: not exercised there. The SMTP CA file was exercised in-process (section 5). The IMAP CA file IS read before the question and was exercised through run_real_check.
* Tests ran as root (uid 0), so permission-based tests are skipped or weak (one skip says so).
* NUL cannot be put in argv/env, so "NUL" cases use file contents (100 MB NUL file, ctl.txt with NUL) and one in-process path with an embedded NUL.
* The hostile harness ran every case under `unshare -n` with loopback up (lo_up-q4g.py), stdin </dev/null, 5 s timeout (kill of process group). Package path printed in logs (lead_desk: line) shows tree-EV2/src for new and tree-old-EV2/src for old.

## 1. Apply tests (plain `git apply`, no flags) - apply.log
* sha256 core-fix-on-frozen-r2.patch = 9cc0cfdd24d17c55ed1efa4d7fa5d9f182ac266376c6c39479f34c734cde22f8
* sha256 core-fix-on-frozen-r2-lf.patch = c6ea81bae11c4deee0e819296051204e478ed9affd1583369e821f91a746c351
* Base: git write-tree in /home/user/build/rr6/demo-frozen/repo2 (branch frozen2, HEAD 58aa4031e911e682ec5702e0641d11cbaf927817) = 49d3c85938fe5323a3378a49195d3b8da434b3ca (matches 49d3c859). repo2 not edited.
* (a) patch on `git clone -b frozen2` (tree-EV2): exit 0.
* (b) patch on `git archive` copy (both .ps1 are CRLF there, checked with `file`): exit 0.
* (c) -lf patch on a copy with both .ps1 converted to LF (checked with `file`: "ASCII text"): exit 0.
* diff -rq -x .git -x __pycache__ -x '.*cache' -x data tree-EV2 vs tree-R2: 0 differences (diff-EV2-vs-R2.txt empty).

## 2. Full suite on tree-EV2 (patched, with .git)
Command (per group; env as AF/run.sh, TMPDIR separate per group): `timeout 2400 unshare -n python lo_up-q4g.py venv-br/python -m pytest -q -p no:cacheprovider -rfs <group file list>`; 2 groups in parallel (groupA.txt, groupB.txt, 52 files each, split by file size), nohup, bounded polling, both ended before I wrote this.
* Group A (full-A.log): 1919 passed, 4 skipped, 47 warnings in 967.73s, rc=0.
* Group B (full-B.log): 2296 passed in 664.71s, rc=0.
* Union: 4215 passed, 0 failed, 0 errors, 4 skipped. Failure first lines: none.
* Skips (verbatim): tests/test_path_confinement.py:284 ntpath.isreserved needs Python 3.13; tests/test_n8n_api_url.py:512 root (and Windows) can read a file with no permissions; tests/test_stall_eviction.py:526 the reset that destroys the reply happens on Windows only; tests/test_server_hardening.py:224 measurement run: set LEAD_DESK_LOAD_N.
* Test files not run: none. 104 test_*.py files in tests/ (find), union of both lists = 104. Non-test helper files (tests/*_probe*.js, desk_env_probe_check.py, crash_launcher.py) are not pytest-collected by design (not run directly by me).
* Not checked: the full suite was run once; no repeat for flakiness. Timing tests ran while the hostile harness (light) and later fail-before overlapped with them (the brief allows max 2 heavy; the harness is light, but it did overlap with group A).

## 3. Fail-before (fail-before.log is failbefore.log; first run failbefore-run1.log)
Files from `git apply --numstat` under tests/ (fb-testfiles.txt, 18 files: 12 new, 6 changed existing) copied onto a clean `git clone -b frozen2` (tree-FB-EV2, no patch), `pytest -p no:cacheprovider -rA --continue-on-collection-errors`.
* Result: 124 failed, 375 passed, 1 skipped, 7 errors (collection) in 433.03s. (run1 with -q gave the same counts: 124 / 375 / 1 / 7.) rc=1.
* Collection errors (7 files, all on missing new code): test_book_folder_refusals.py, test_ca_file_reads.py, test_cli_refusals.py, test_crash_flag_reads.py, test_file_reader_refusals.py, test_regfile_limits_in_constants.py, test_script_refusals_feed.py. Causes (verbatim): ModuleNotFoundError lead_desk.regfile; ModuleNotFoundError desk_setting; ModuleNotFoundError refusals; ImportError CA_FILE_MAX_BYTES, FLAG_FILE_MAX_BYTES, FOLDER_CANNOT_BE_MADE_BOOK_PROBLEM (lead_desk.desk), FeedRefused (feed), LIVE_EFFORTS, lead_desk.regfile.
* Failures per file (old code): test_special_files_and_plain_text 39, test_special_output_files 39, test_wrapper_setting_refusals 15, test_tools_and_fakes_pipes 12, test_reset_scripts 10, test_ledger_amounts 2, test_n8n_api_url 2, test_no_terminal_questions 2, test_lead_step_route 1, test_real_check_dry 1, test_sonar_p2_feed_optional 1.
* PASS on old code: 375 tests, names in passes-on-old.txt. Per file: test_n8n_api_url 135, test_ledger_amounts 102, test_real_check_dry 71, test_reset_scripts 35, test_lead_step_route 19, test_special_output_files 8, test_special_files_and_plain_text 3, test_sonar_p2_feed_optional 2. Not judged here (some are pre-existing tests in changed files).

## 4. Lint, format, bandit, suppressions (lint.log) on tree-EV2
* ruff check .: "All checks passed!" rc=0. ruff format --check .: "176 files already formatted" rc=0 (line length 120 from pyproject).
* bandit -ll -r src tools scripts load_tools demo_only: rc=0; High 0, Medium 0, Low 12 (low severity is below -ll); 1 issue skipped by a specific #nosec (pre-existing count; nosec total 12 vs 12 frozen).
* Suppressions, frozen -> patched (line counts across all files): noqa 250 -> 267 (+17), nosec 12 -> 12, type: ignore 121 -> 124 (+3), nosemgrep 32 -> 32. Added lines (suppression-lines.txt, suppression-new-files.txt): in changed files 8 x `# noqa: E402` (hubspot_probe 1, n8n_api 1, run_live_check 1, run_real_check 3, scrub_n8n_export 2); in new files: scripts/refusals.py 1 noqa E402; tests/test_cli_refusals.py 7 (noqa S404, S603 x2, E402 x2, type: ignore[arg-type] x2); tests/test_file_reader_refusals.py 3 (S404, E402, S603); tests/test_script_refusals_feed.py 3 (S404, E402, S603); tests/test_tools_and_fakes_pipes.py 1 type: ignore. (The 17 + 3 add up to the counts above.)

## 5. Hostile proofs old vs new (hostile/results.jsonl raw, hostile/table.txt readable; 149 cases x 2 trees; harness hostile_driver.py, hostile_extra.py, hostile_inproc.py)
Old = tree-old-EV2 (clean frozen2), new = tree-EV2. 5 s timeout each. "HANG" = still running at 5 s.
Summary counts: old = 27 HANG and 17 with Traceback (some "HANG" rows are servers that started and listen: catcher, fake_model_server). New = 3 with Traceback, 5 HANG rows (details below).

Requested items (old -> new):
* FIFO as SMTP CA file (in-process, constructor): old HANG (no output) -> new refused in 0.1 s: SettingRefused "DESK_SMTPP_CA_FILE cannot be read as a file of trusted certificates".
* FIFO as IMAP CA file via run_real_check --config: old HANG 5 s -> new rc=2 0.2 s "refused: CaFileRefused: REAL_IMAP_1_CA_FILE cannot be read as a file of trusted certificates".
* Empty / 100 MB / whitespace-only / garbage / directory / NUL-in-name / missing SMTP CA file: old = raw SSLError / IsADirectoryError / ValueError("embedded null byte") / FileNotFoundError text; new = the same one fixed SettingRefused line for all of them, 0.1 s.
* Same for IMAP CA via run_real_check: empty, 100 MB, ws-only: old "refused: SSLError", dir "IsADirectoryError", new: one CaFileRefused line.
* Valid regular CA file (openssl self-signed made-up cert, hostile/valid-ca.pem): accepted on both (SMTP built; IMAP run reached the question rc=1).
* FIFO as live_claude key file (LiveQualifier._read_key): old HANG -> new LiveTransport "the key file cannot be read" 0.15 s.
* 100 MB NUL key file: old accepted it (key_len=104857600, peak RSS 223 MB, 0.28 s) -> new LiveTransport "the key file is too large: it must hold only the key" (peak RSS 112 MB, 0.07 s). Normal 36-byte key accepted on both.
* run_live_check with closed stdin: old Traceback (EOFError: EOF when reading a line), rc=1 -> new prints the two cost lines then "Start? [y/N] stopped, nothing was called: there is no terminal to answer the question on", rc=1, no traceback, ledger file not created (checked, both trees). Note: the output is 3 lines (two information lines and the stop line), not one.
* FIFO as: check_invariants inputs (--requests/--catcher/--crm/--model-log/--book/--facts): old HANG on --requests and --facts (the others stopped earlier on a missing facts file) -> new rc=2 "INPUT ERROR: <option>: is not a regular file ..." for all six, ~0.1 s. Catcher --control FIFO and --out FIFO: old server starts (HANG row = listening) -> new rc=2 refused. read_mode on FIFO in-process: old HANG -> new ('ok', 0.0). load_driver --log FIFO and --facts FIFO: old HANG -> new rc=2. _read_int FIFO: old HANG -> new None. fake_model_server --control-file FIFO / --key-file FIFO / --call-log FIFO: old listening/HANG -> new rc=2 refused; ModelState.current_mode FIFO: old HANG -> new 'ok'. portal_demo PortalDemo._armed FIFO: old HANG -> new None. FlagFileHooks.crash_point FIFO: old HANG -> new returns. CrashWindows.hit FIFO: old HANG -> new returns. n8n_api N8N_API_KEY_FILE FIFO: old HANG -> new "cannot read the n8n API key file (not a regular file)". scrub_n8n_export in=FIFO: old HANG -> new rc=2 refused; out=FIFO: old Traceback -> new refused.
* 100 MB as flag/control file (hooks, trace, catcher read_mode, _read_int, ModelState): old read it (peak RSS 213-223 MB, up to 0.64 s) -> new peak RSS 112 MB, 0.01-0.06 s.

Other hostile inputs (new behaviour; old in table.txt): run_real_check --dry-port-base 0 / -1 / 70000 / 99..9(40 digits): new rc=2 one refusal line (old: ran a dry run for 0, "OverflowError" for 70000/huge); --dry-smtp-script with ESC char: new refused (old ran); --config FIFO: old HANG -> new refused; --config 100 MB / NUL file: new "not UTF-8 text (or is over 1 MiB)"; --config directory/missing/ESC-char file: refused on both; REAL_RESULT_FILE=FIFO: new refused (old reached the question); REAL_PERSONS=huge, DESK_PORT=70000: refused on both. run_live_check --effort " low" and "ultra": old Traceback (EOF, accepted option) -> new rc=2 "--effort: must be one of: low, medium, high, xhigh, max"; --leads 0: new rc=2 one line; --price-date with control char: old accepted, new refused; --timeout nan/inf, --max-tokens 0, --cap-run -1 / 400 digits: refused on both. desk_setting.py (new file, absent in old so "old" rows are "cannot open file"): DESK_PORT 0 -> prints 0; -1, 70000, 99999999, 1e999, ESC text -> rc=4 one line "the desk refuses a setting: ..."; " 5" and "5 " are accepted and print 5 (uncertain whether that is wanted); DESK_DB_PATH FIFO with data-dir -> rc=4 refusal; DESK_DB_PATH directory with db-path -> prints the path, rc=0 (no check, may be intended); DESK_LIVE_EFFORT "low" ok, " low", "ultra", "low"+ESC, 100000 x "L" -> rc=4 "DESK_LIVE_EFFORT must be one of: ..."; empty effort -> rc=4 "must not be empty". feed.py --index 0 / -1 / 99..9 : old Traceback -> new rc=2 "must be a whole number from 1 to 6"; --source ESC: refused. hubspot_probe huge --yes-spend-calls, ESC token env name, ESC dry-run url: rc 2/0/2 with the plan line on both (no traceback). crash_desk with DESK_DB_PATH=FIFO: new rc=4 refusal.

FLAGGED (new code):
1. TRACEBACK in new: demo_only/fake_model_server.py --port -1, --port 70000, --port 99999999999999999999 -> last line "OverflowError: bind(): port must be 0-65535." rc=1 (same traceback on old: not fixed by the patch).
2. HANG (not finished in 5 s, killed) in new: run_live_check --leads 99999999999999999999 (also on old). Cause not analysed beyond: _emails(n) builds a list of n tuples; killed with SIGKILL at 5 s (memory grows). A 4 GB address-space limit did not make it stop within 5 s either.
3. load_driver --scenario burst:<40 digits>, --workers 0, --workers 99999999999999999999: 5 s no output on both trees. INCONCLUSIVE: a plain valid `burst:1` against the unreachable URL also did not finish in 8 s (retries), so I cannot separate a defect from normal waiting.
4. fake_model_server --port 0 "HANG" = the server started and listens (expected, not a defect).

Not covered: SMTP CA / HubSpot key / SMTP password files through run_real_check beyond the question (needs a yes, never given). check_invariants 100 MB cases stop at an empty-facts KeyError first (my facts file was `{}`), so a 100 MB --requests/--catcher/--crm/--model-log was not actually read by check_invariants; only 100 MB --facts was ("the file is too big" on new, JSONDecodeError after 0.44 s on old). Windows (.ps1) scripts were applied but not executed (no PowerShell). Real network, real model, real mail: none used. No prompt was answered.

## 6. Cleanup
Removed after writing this file: tmp-EV2, tree-old-EV2, tree-FB-EV2. Kept: tree-EV2 (patched, not committed; has untracked new files, __pycache__, .ruff_cache and data/desk.sqlite3.lock created by my --help run of crash_desk), out/EV2, and tree-EV2.stale-before-run (not mine). Processes: pgrep shows none of mine left (other agents' processes in out/R3 were not touched).
