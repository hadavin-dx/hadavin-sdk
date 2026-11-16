# EV7N evidence (independent run of the r7n patch set on the frozen tree)

Evidence runner EV7N. I ran commands and saved raw output; I do not judge. Raw files: `/home/user/build/rr6/out/EV7N/` (wrapper.log, pytest-full.log, fail-ids-ev7n.txt, stage-*.log, stage-summary.txt, alone-*.log, order-*.log, alone-counts.txt, hostile-*.txt, odd-r7n.txt, probe-builder-server.txt, ruff-*.txt, suppressions.txt, apply-matrix-ev7n.txt, bytecompare.txt, patches/, checkpoint.md). Run tree: `/home/user/build/rr6/out/EV7N/tree` (plain copy, no .git, no data/). Times UTC (IST = +5:30). Started 09:41, patches and apply 09:42, full run 09:42:38 to 10:12:37, last step 10:13. About 32 min of the 70 min box. No spend, no live service, loopback only, no prompt answered.

## What failed, what is uncertain, what I did not check (read this first)
1. **The builder's own mailbox test server never sends the login line, so the r7n "echo" tests do not test what their header says.** The fake server `_EchoImap` in `tests/test_r7n_findings.py` answers every line except LOGIN with `BAD`, including the client's `CAPABILITY` line. Under this machine's Python 3.12 imaplib that aborts the connection BEFORE `LOGIN` is sent. I counted the lines that server read: only `CAPABILITY`, then end of stream, in all 6 modes; `LOGIN reached: False` (raw: `probe-builder-server.txt`). So the server never gets to echo the login line. The tests still pass and still catch the leak through the error chain and frame locals (r7m fails them the same way, see 6c), but "the server repeats the LOGIN line in its refusal" is never exercised by the test suite. My own hostile run (6c) does reach LOGIN (server logins counted, all rows greater than 0) and is clean. Not checked: whether another Python version answers differently (only 3.12 here).
2. **My slip, hostile run (6c), twice.** First run used the host name `mail.example.test`, which cannot be looked up under `unshare -n`; second run used `localhost` but my fake server did not answer `CAPABILITY`. In both the server saw 0 logins (`server_logins=0` in all 168 rows), so both results are INVALID and are kept as `hostile-g-INVALID-first-run*.txt` and `hostile-g-INVALID-second-run-no-CAPABILITY-answer.txt`. The third run (reported below) counted server logins and is the one that counts. I found the cause by instrumenting the server, not by luck: it was visible in the table column `server_logins`.
3. Skipped count differs from the builder: builder says 37 skipped, 5892 passed; my run says **8 skipped, 5921 passed** (both total 5929). I did not find why 29 tests skipped there and passed here (the builder's log has no skip list; mine does, see step 2). Not investigated.
4. Not run: Windows (line endings of the two `.ps1` files tested only as patch application, not by running PowerShell); real IPv6 (this machine has none, errno 97 on an IPv6 socket); mutation runs (not asked); the full suite inside the staged git copy (only the 8 git-needing files, as asked); the full run on a quiet machine (other lanes ran pytest and mutation scripts during mine: load 0.80 at launch, 1.31 at end).
5. The run tree gets `__pycache__` folders during the run even with `PYTHONDONTWRITEBYTECODE=1` (4 folders: demo_only, src/lead_desk, scripts, tools; a test child process does not pass the variable on, same as EV7K). They are git-ignored. After the run, `diff -rq` of the run tree against the freshly patched tree shows no other difference.
6. One server traceback line appears in the full log (`Exception occurred during processing of request from ('127.0.0.1', ...)`, 1 time) with all tests passing; I did not look into it.
7. The three socket tests that EV7K failed (`test_real_check_dry` x3) pass now in the full run, in both test orders, and alone (see 2 and 4).

## Step 1: rebuild from the committed patches
- Unpacked sha256 equal to the expected value, all three: `core-fix-on-frozen-r7n.patch` 2b03ea13...0529 (from the .gz), `core-fix-on-frozen-r7n-lf.patch` e9b52a37...2095f05, `core-fix-r7m-to-r7n-delta.patch` 586de496...72ba (from the .gz).
- Frozen tree: tag `frozen2` of `/home/user/build/rr6/demo-frozen/repo2` has tree id 49d3c85938fe5323a3378a49195d3b8da434b3ca (commit 58aa4031...). I copied it with `git archive`; the source was not edited.
- `git apply --check --binary` (apply-matrix-ev7n.txt): checkout a (CRLF `.ps1`, CRLF patch) rc=0; checkout b (CRLF, CRLF patch) rc=0; checkout c (`.ps1` made LF with sed, LF patch) rc=0.
- Applied for real on a and c: both trees are byte-for-byte equal to `/home/user/build/rr6/tree-R7N` (`diff -r`, no output; bytecompare.txt). After applying, c's `.ps1` files hold CR bytes again (84 and 101 lines, same as tree-R7N): git's own checkout conversion wrote them, I did not look into the attribute rule.
- Tree hash by the builder's method (sha256 of the sorted `sha256sum` list of all files, no .git): `a5ac5982f0d193a76f91edad84d46aaf550eb9fceaca4cac22eb6daa7aaea84d` for checkout a and c. Equals the builder's claim. (The method was found by trying: sorted `find | xargs sha256sum | sha256sum` gave a match.)
- Delta patch applied on a copy of tree-R7M gives the same tree as checkout a (`diff -r` no output, same hash).

## Step 2: ONE full run (plain copy, full recipe, `unshare -n` with the loopback driver)
Command: `/home/user/build/rr6/out/EV7N/run-full.sh <tree> full 3000` (env -i; TMPDIR outside the tree, PYTHONPATH tree/src, PYTHONDONTWRITEBYTECODE=1, PLAYWRIGHT_BROWSERS_PATH, GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1, PATH with rr6/bin first; `unshare -n python3 .../lo_up-q4g.py venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs`). rc=1, no signal.
- Result: **7 failed, 5921 passed, 8 skipped, 60 warnings in 1797.97s (0:29:57)**.
- Failing ids (exactly), all 7 are the git-only ones: `test_hygiene.py::test_hygiene_scan_public`, `::test_no_control_characters_in_markdown`, `::test_sh_blobs_no_cr`, `::test_the_secret_scan_files_have_no_carriage_return`, `test_nosemgrep_form.py::test_no_bare_nosemgrep_comment`, `test_raw_bidi_chars.py::test_no_tracked_file_holds_a_raw_direction_control_character`, `test_shell_single_bracket.py::test_no_tracked_script_or_workflow_run_block_holds_a_single_bracket_test`.
- Diff against EV7K `fail-ids-ev7k.txt` (10 ids): only the 3 `test_real_check_dry` ids are gone (`test_a_failed_crm_read_back_ends_with_counts_a_result_file_and_a_clean_up_note`, `test_a_failed_write_after_a_failed_read_back_keeps_the_result_on_the_screen`, `test_dry_fakes_leave_no_certificate_or_key_folder_behind`); the other 7 ids are identical. Nothing new fails.
- Skips (8): root can read any file (2 files), no git work tree (1), `ntpath.isreserved` needs Python 3.13 (1), model fake only has /v1/messages (2), measurement run LEAD_DESK_LOAD_N (1), Windows-only reset (1).

## Step 3: the 8 git-needing files in a STAGED git copy (`git init; git add -A`, no commit; 315 staged entries; no data/), each file alone, same recipe
| file | result | rc | untracked after (excl. ignored / all) |
|---|---|---|---|
| test_hygiene | 24 passed in 41.60s | 0 | 0 / 0 |
| test_nosemgrep_form | 114 passed | 0 | 0 / 0 |
| test_raw_bidi_chars | 3 passed | 0 | 0 / 0 |
| test_shell_single_bracket | 146 passed | 0 | 0 / 0 |
| test_file_call_guard | 11 passed | 0 | 0 / 0 |
| test_no_placeholders | 2 passed | 0 | 0 / 0 |
| test_gitleaks_exceptions | 44 passed | 0 | 0 / 0 |
| test_gitleaks_semgrep_lock | 4 passed | 0 | 0 / 0 |
The builder said 20 passed, 4 skipped for test_hygiene; I got 24 passed, 0 skipped (different machine state; not investigated). EV7K's `test_hygiene_scan_public` failure is gone. No untracked leftovers.

## Step 4: order tests (clean copy, same recipe)
- `pytest tests/test_r7k_findings.py tests/test_real_check_dry.py`: **218 passed** in 232.95s.
- `pytest tests/test_real_check_dry.py tests/test_r7k_findings.py` (reverse): **218 passed** in 200.86s.
- Each file in the other order of the full run also passed (step 2).

## Step 5: ruff 0.17.1 on a COPY (`--no-cache`)
- `ruff check`: All checks passed (rc 0). `ruff format --check`: 226 files already formatted (rc 0).
- Suppressions (grep of py/toml/yaml/yml/ps1/sh files, whole tree excluding .git, data, caches; raw: suppressions.txt):
| | noqa | type: ignore | nosemgrep | nosec | S603 |
|---|---|---|---|---|---|
| frozen | 250 | 121 | 29 | 12 | 52 |
| r7m | 175 | 145 | 29 | 8 | 7 |
| r7n | 175 | 126 | 29 | 8 | 7 |
In src+scripts+load_tools only: frozen 78 / 22 / 0 / 9 / 1; r7m 56 / 21 / 0 / 8 / 1; r7n 56 / 21 / 0 / 8 / 1 (noqa / type: ignore / nosemgrep / nosec / S603). Tests only: r7m type: ignore 123, r7n 104 (the 19 removed in `test_r7l_findings.py`); noqa 104 in both. No new suppression in r7n against r7m.

## Step 6: hostile table (loopback only, `unshare -n`, my own copy `htree`, absolute output paths)
a. **20 hostile hosts** (4 paths x 5 hosts: label70, empty, trailingdot, singletrailing, surrogate; `hostile-a-table.txt`): all 20 rc=0, stderr 0 bytes in all 20, no traceback. Results: `ImapSettings` 5x `ImapSettingRefused` "the mailbox host must be a host name (letters, digits, hyphens and dots)"; `counts_by_key` 5x `ImapConnectionError` "the mailbox could not be read"; `connect_bounded` 5x `OSError` "the host name cannot be looked up"; `run_real_check` 5x its own "RESULT: rc=2" refusal. Same as EV7K.
b. **9 odd server patterns** (`odd-r7n.txt`, 1 worker 2 threads): same final status, stopped counts and stderr text as EV7K `odd-r7m.txt` for all 9 (diff modulo timing: equal). burst:4 first-answered-then-all-dropped: rc=3, 61.8 s, 1 stderr line of 307 bytes, "ERROR: 3 of 4 requests were not accepted: 3 until their retry time was over ... 0 because the driver itself failed ...".
c. **NEW: fake mailbox server (TLS, loopback) whose NO/BAD/BYE/untagged/echo-then-hang-up/garbage/two-line-ALERT reply to LOGIN echoes the login line** (`hostile-g.txt`, driver `hostile_g.py`). 7 server modes x 6 canary secrets (plain, with a double quote, with a backslash, with a space, 156 characters long, with `%{}`; all built from parts) x 4 callers (`counts_by_key`, `counts_for_keys`, `counts_by_inbox`, `run_real_check.poll_mailboxes` = the script that reads a mailbox) = 168 cases, in process, with log capture at DEBUG level. Each case searched for 7 forms of the secret (raw, imap-quoted, repr, first 12 characters, base64, base64 of `\0user\0secret`, hex) in: str, repr, args, `__dict__`, formatted traceback and frame locals of every error in the cause/context chain, stdout, stderr, all log records. **Result: 168 cases, 0 leaks.** Mailbox server saw a LOGIN line in every row (server_logins greater than 0 in 168 of 168). Outcomes: 126 `ImapCountError` (fixed text "the mailbox could not be read"), 42 `poll_mailboxes` returned and printed one fixed line (51 bytes), stdout/stderr of the callers 0 bytes except that line.
   - Child process that does NOT catch the error (9 runs: 3 modes x 3 secrets): rc=1, stderr 761 bytes (870 for echo-then-hang-up; r7m: 614 and 723), last line `lead_desk.imap_count.ImapConnectionError: the mailbox could not be read`, 0 secret forms. `CHILD leaks=0`.
   - **Negative control on r7m** (copy of tree-R7M, same driver, `hostile-g-NEGATIVE-CONTROL-r7m.txt`): 168 cases, **105 leaks** (all 105 raising rows: the secret is reachable in the error chain or frame locals), while the printed text of an uncaught error was clean on r7m as well (0 child leaks). So the driver can see a leak, and the r7n fix removes the reachable one; what r7m printed was already clean.
d. First address never answers (`hostile-c.txt`), 8 silent + 1 good (`hostile-d.txt`), first family unavailable and localhost (`hostile-e.txt`): all rc=0, stderr 0 bytes; same lines as EV7K (first-never-answers total 10: connected 5.0 s with timeouts 5.0/5.0; total 3: 1.5 s; one address total 4: TimeoutError 4.0 s; both never answer total 8: TimeoutError 8.0 s with 4.0 + 4.0).
e. Driver errors, burst runs (`hostile-f.txt`): burst:3 bad 0: rc=0, 3 lines, 0 stderr; burst:4 bad 4: rc=3, 4 driver_error lines, accepted 0, 1 stderr line 307 bytes; burst:5 bad 1: rc=3, accepted 4, 1 line 307 bytes; burst:6 bad 2: rc=3, accepted 4, 1 line 307 bytes. Worker pool was replaced by threads (as EV7K and the tests do); not run with a real spawned pool.

## Step 7: each new test file alone (clean copy, same recipe)
| file | result |
|---|---|
| test_r7i_findings | 37 passed in 5.06s |
| test_r7j_findings | 40 passed in 69.97s |
| test_r7k_findings | 139 passed in 26.72s |
| test_r7l_findings | 91 passed in 4.16s |
| test_r7n_findings | 97 passed in 94.80s |
| (extra) test_r7m_new | 7 passed, 6 warnings in 1.95s |

## Processes and leftovers
Started by me: the full-run wrapper (ended 10:12:37), the odd-pattern wrapper (ended), `stage.sh` and `ord.sh` (both ended, DONE lines written), foreground drivers. None left running (pids in mypids.txt checked with `kill -0`). Never edited the frozen tree, tree-R7M, tree-R7N or any tree-R7*/EV7*/M8-M12*/REV* tree (the negative-control copy `m7tree` is under my own scratch). I wrote no file into the run tree during the pytest run.
