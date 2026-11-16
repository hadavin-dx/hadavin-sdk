# EV7J EVIDENCE (r7j, the one full run). EVIDENCE RUNNER: raw facts only, no judgement.
Raw files: /home/user/build/rr6/out/EV7J/ (wrapper.log, pytest-full.log, rerun-r7f-alone*.log, stage-*.log, stage-summary.txt, hostile-*.txt, odd-*.txt, ruff-*.txt, suppress-counts.txt, machine*.txt, checkpoint.md). Tree: /home/user/build/rr6/tree-EV7J (plain copy, no .git, no data/); staged copy: tree-EV7J-stage.

## NOT RUN / NOT CHECKED (first)
- FAILED: 1 test fails in r7j that did not fail in EV7I or EV7G: `tests/test_r7f_findings.py::test_f1_a_connect_that_never_completes_ends_at_the_total_not_at_the_step` (see "Differences"). It failed in the full run AND again when the file was run alone (1 failed, 78 passed). The same file alone on tree-EV7I (r7i) passes (79 passed). Not explained away; facts below.
- The 7 other failures are the same 7 as EV7G and EV7I (all need a git work tree); they PASS in the staged copy (below).
- NOT RUN: Windows; IPv6 (this machine has none: `socket.socket(AF_INET6)` raises errno 97); mutation runs (not asked); a full run in the staged copy (only the git-needing files + 2 gitleaks files were run there, as asked).
- The full run was not on a quiet machine: other agents' pytest runs, a load_driver run and openssl were active during all of it (load 2.04 at start, 8.62 once seen in the EV7I wrapper log at 06:57, 2.44 at end). The one extra failure is not a timing failure by its error text (see below), but I did not run it on a quiet machine either.
- My `ruff` runs (step 5) were made with the cache on, inside tree-EV7J, 1 minute after the full run was launched: a `.ruff_cache/` folder (43 files) therefore existed in the tree during the full run (not in the frozen tree). It is a hidden folder, git-ignored; I did not repeat the full run without it.
- Step (4): I ran each of the six git files twice by mistake (first call's output overwritten by the second; both passed); the log kept is the second run.

## Step 1: patch (committed bytes)
- Committed commit 0c96e27c. `gunzip -c core-fix-on-frozen-r7j-crlf.patch.gz` sha256 = 1566a8e4d07516ec9de30f225225ccf89cf66f13c782f0130a67af9e44d8a437 (equals sha256-r7j.txt, core-fix-on-frozen-r7j.patch line). LF patch core-fix-on-frozen-r7j-lf.patch sha256 = 0ddfd77dfea11f0d6011ca9bad9a2a1e6e690181b5d9fda7b6dca63473878332 (equals sha256-r7j.txt).
- Frozen repo2: HEAD 58aa4031..., tree object 49d3c85938fe5323a3378a49195d3b8da434b3ca (the sha in the brief is the TREE sha; the commit sha is different). Fresh copy without .git and without data/ (tar, --exclude). In a throwaway `git init; git add -A` copy: `git -c core.autocrlf=false apply --check` rc=0, `git apply` rc=0, then .git removed (checked: no .git, no data/).
- `diff -r -x __pycache__` of src, scripts, tests, load_tools, docs against /home/user/build/rr6/tree-R7J: all five rc=0 (empty). Repeated after all runs: all five rc=0 (the tree-R7J has __pycache__ folders that were excluded; the only difference allowed).

## Step 2: machine state (out/EV7J/machine.txt, taken 06:51:08)
uptime load 2.05 2.66 2.46, 4 cores. Other agents' processes at that time (not touched): EV7I full run (pids 10326/10327, 23 min old), several other `pytest -x` runs, a load_tools.load_driver run, a run_live_check.py run. Load at my full start 2.04 2.65 2.46; at its end 2.44 1.85 2.54.

## Step 3: ONE full run (plain copy, method of EV7I: run-full.sh = EV7I script with the label/paths changed; wrapper limit 2700 s; env -i, PLAYWRIGHT_BROWSERS_PATH, GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1, PATH with rr6/bin first, TMPDIR out/EV7J/tmp-full, PYTHONPATH=<tree>/src, PYTHONDONTWRITEBYTECODE=1, venv-br python -m pytest -q -p no:cacheprovider -rfs under `unshare -n ... lo_up-q4g.py`)
- `full start 2026-11-14T06:51:11Z ... full end 2026-11-14T07:21:55Z rc=1 signal=none` (wrapper.log). IST = +5:30: 12:21:11 to 12:51:55.
- Result line: **8 failed, 5594 passed, 8 skipped, 60 warnings in 1842.08s (0:30:42)**.
- Failures (8):
  1. tests/test_hygiene.py::test_no_control_characters_in_markdown (subprocess.CalledProcessError)
  2. tests/test_hygiene.py::test_hygiene_scan_public (RuntimeError: git ...)
  3. tests/test_hygiene.py::test_sh_blobs_no_cr (CalledProcessError)
  4. tests/test_hygiene.py::test_the_secret_scan_files_have_no_carriage_return
  5. tests/test_nosemgrep_form.py::test_no_bare_nosemgrep_comment
  6. tests/test_raw_bidi_chars.py::test_no_tracked_file_holds_a_raw_direction_control_character
  7. tests/test_shell_single_bracket.py::test_no_tracked_script_or_workflow_run_block_holds_a_single_bracket_test
  8. **tests/test_r7f_findings.py::test_f1_a_connect_that_never_completes_ends_at_the_total_not_at_the_step**
- Skipped (8, as in EV7G/EV7I): book_folder_refusals:237 (root), n8n_api_url:524 (root), no_placeholders:27 (not a git work tree), path_confinement:285 (Python 3.13), r7b_fake_deep_and_head:58 x2, server_hardening:224 (measurement run), stall_eviction:526 (Windows only).
- Stderr noise in the log: 2 "Exception occurred during processing of request ... BrokenPipeError" blocks from scripts/http_guard.py test servers (EV7G log: 1, EV7I log: 1).

### Comparison by test id
| run | tree | result |
|---|---|---|
| EV7G | r7g | 7 failed, 5468 passed, 8 skipped |
| EV7I | r7i | 7 failed, 5554 passed, 8 skipped (1782 s) |
| EV7J | r7j | 8 failed, 5594 passed, 8 skipped (1842 s) |
- IDs failing in EV7J only (vs EV7I, `diff` of the sorted FAILED ids): exactly one, test_r7f_findings::test_f1_a_connect_that_never_completes_ends_at_the_total_not_at_the_step. IDs failing in EV7I only: none. The 7 ids of EV7G equal the 7 ids of EV7I and the first 7 above (same names).

### Differences: the extra failure, run ALONE
- Full run: `lead_desk.imap_count.ImapConnectionError: the mailbox could not be read` raised from imap_count.py:303 (the branch after `except (imaplib.IMAP4.abort, OSError)` where the error is not a TimeoutError and the deadline is not yet passed); the test expects `ImapTotalTimeout`. The settings in the failure: host='localhost', total_seconds=1.0, timeout_seconds=10.0.
- Alone on r7j (`tests/test_r7f_findings.py`, t.sh, same recipe, 07:22): **1 failed, 78 passed in 18.11 s, rc=1** (same test, same exception). Alone on r7i (tree-EV7I): **79 passed in 18.92 s, rc=0**.
- Facts measured on this machine under the same `unshare -n` + loopback setup (gai-under-unshare.txt): `getaddrinfo("localhost")` returns only 127.0.0.1; creating an AF_INET6 socket raises `OSError: [Errno 97] Address family not supported by protocol`. r7j's `netconnect._without_lookup("localhost")` returns two addresses (127.0.0.1, then ::1) without calling getaddrinfo (netconnect.py, item m3 of R7J-RESULTS). The test's listener is IPv4 only with a full backlog, so 127.0.0.1 hangs; the second address (::1) fails at once with errno 97 (m1 of R7J-RESULTS: errno 97 = this address failed, next is tried), and the last error (not a TimeoutError) is raised. I did not change any file to check a fix.
- A second look: the EV7I-run full suite and the r7j alone-run happened with load 1.3 to 2.9; the result is the same in both r7j runs and different from r7i alone.

## Step 4: staged copy (tree-EV7J-stage: copy of the post-run tree, `git init; git add -A`, no commit; 311 staged entries; no data/), each file alone, t.sh recipe
| file | result |
|---|---|
| test_hygiene | 24 passed in 45.94 s, rc=0 |
| test_nosemgrep_form | 114 passed in 1.46 s, rc=0 |
| test_raw_bidi_chars | 3 passed in 0.11 s, rc=0 |
| test_shell_single_bracket | 146 passed in 3.42 s, rc=0 |
| test_file_call_guard | 11 passed in 1.56 s, rc=0 |
| test_no_placeholders | 2 passed in 0.17 s, rc=0 (skipped in the plain copy) |
| test_gitleaks_exceptions | 44 passed in 14.24 s, rc=0 |
| test_gitleaks_semgrep_lock | 4 passed in 7.85 s, rc=0 |
(gitleaks-related = the files in tests/ that name gitleaks: those two, plus test_hygiene and support.py.)
- Untracked listing after each file: `git ls-files -o --exclude-standard` = 0 names after the two gitleaks files; `git ls-files -o` (ignored files too) = 43 names after the first six: my `.ruff_cache/` files and `__pycache__/*.pyc` (33 .pyc in the tree, git-ignored); `git status --short` shows only the staged additions.
- Stray file named `a<newline>b`: Python walk of tree-EV7J and tree-EV7J-stage for any name with a control character: none (both trees). The test TMPDIR (out/EV7J/tmp-full) holds 5 such names, all inside pytest's own temp folders where the tests create them on purpose (a\nb, nl\nname, a\nb.db, a\x01b.db, a\x7fb.db); same 5 as EV7G. `data/` absent.

## Step 5: ruff (pinned /.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/ruff-0.17.1.data/scripts/ruff, `ruff 0.17.1`, run in tree-EV7J)
- `ruff check .`: rc=0 "All checks passed!". `ruff format --check .`: rc=0 "222 files already formatted" (EV7G tree: 219).
- Suppression markers (grep -o occurrences over the tree, binary skipped, .git and __pycache__ excluded; same method for both): noqa frozen 251 / r7j 176; nosemgrep frozen 40 / r7j 40; type: ignore frozen 121 / r7j 126. (EV7G table: r7g 176 / 40 / 126: identical.)

## Step 6: hostile table on r7j (drivers of EV7G copied unchanged, run under unshare -n, loopback only; plus one new driver hostile_d.py written for the 8-silent case)
### (a) 20 hostile hosts (hostile_a.py; 4 paths x 5 hosts; every process rc=0, stderr 0 bytes in all 20, no traceback)
| path | label70 / empty / trailingdot / singletrailing / surrogate |
|---|---|
| ImapSettings(...) | all 5: ImapSettingRefused "the mailbox host must be a host name (letters, digits, hyphens and dots)" |
| counts_by_key | all 5: ImapConnectionError "the mailbox could not be read" |
| connect_bounded | all 5: OSError "the host name cannot be looked up" (EV7G: empty and "example.test." gave the raw gaierror text; now the one fixed text) |
| run_real_check | all 5: rc=2 (surrogate case written as raw byte 0xff in the config) |
### (b) odd server patterns (odd_patterns.py unchanged, 1 worker, 2 threads; odd-r7j.txt)
```
only202: rc=0 1.9s final={'202': 4} stopped=0 unreachable=False err=''
only429: rc=0 1.9s final={'429': 4} stopped=0 unreachable=False err=''
503-for-3s-then-202: rc=0 3.6s final={'202': 4} stopped=0 unreachable=False err=''
503-twice-then-202: rc=0 2.0s final={'202': 4} stopped=0 unreachable=False err=''
drops-3s-then-answers: rc=3 2.2s ... err='ERROR: the desk cannot be reached: every request ended in a connection error (is it running?)'
drops-6-then-answers: rc=3 2.2s ... same line
first-202-after-2s-others-closed(M2): rc=3 3.8s final={'202': 1, 'error': 1} stopped=1 ... 'ERROR: the run was stopped early: 1 of 2 requests were never sent or were given up, ...'
first-202-after-3s-others-closed-burst8: rc=3 4.8s final={'202': 1, 'driver:stopped': 6, 'error': 1} stopped=7
first-answered-then-all-dropped-burst4: rc=3 61.8s final={'202': 1, 'error': 3} stopped=0 unreachable=False
```
- The burst:4 case (EV7G: rc=0, 61.8 s): now **rc=3, 61.8 s, final {'202': 1, 'error': 3}, stopped=0, stderr 248 bytes, 1 line**: "ERROR: 3 of 4 requests were not accepted: 3 until their retry time was over (gave_up deadline in the log), 0 because the run was stopped early; the desk did not take them, so this run is not a pass (exit code 3); run check_invariants.py on the log" (separate run for the byte count: odd-burst4-detail.txt, same rc/time/counts). All other lines equal EV7G's except this one.
### (c) first address never answers (hostile_c.py unchanged; getaddrinfo and socket class replaced)
```
first never answers, second ok, total 10 | connected | 5.0s | timeouts given m-a 5.0, m-b 5.0 | closed 1
first never answers, second ok, total 3  | connected | 1.5s | m-a 1.5, m-b 1.5 | closed 1      (EV7G: TimeoutError 3.0s, second never tried)
one address never answers, total 4       | TimeoutError: timed out | 4.0s | m-a 4.0 | closed 1
both never answer, total 8               | TimeoutError: timed out | 8.0s | m-a 4.0, m-a 4.0 | closed 2   (EV7G: 5.0 then 3.0)
```
stderr 0 bytes.
### (d) 8 silent + 1 good at a 1.2 s total (new hostile_d.py, same replaced-socket method; hostile-d.txt; stderr 0 bytes)
```
8 silent then 1 good       | connected | 1.07s | each silent 0.133 s, good 0.132 s | closed 8
1 good first then 8 silent | connected | 0.00s | good 0.133 | closed 0
8 silent only              | TimeoutError: timed out | 1.20s | each silent 0.15 (last two 0.149) | closed 8
```
### (e) fake address list, first family unavailable
Not run as a separate driver: the machine itself has no IPv6 (errno 97 shown above), so the `localhost` path of the failing test is a real run of this case; its result is the failure in "Differences". tests/test_r7j_findings.py (m1) passed inside the full run (it is in the 5594 passed; not listed among failures).

## Clock
Start 06:50:46 UTC; steps 1-2 06:51; full run 06:51:11 to 07:21:55; r7f alone 07:22; staged files 07:23 to 07:25; ruff at 06:51; hostile (a), (c), (d) about 07:25 to 07:26; odd patterns 07:26 to 07:27; burst:4 detail 07:28. About 40 min of the 75 min box. IST = UTC + 5:30. Processes started by me: the detached full-run wrapper (ended), foreground runs (all ended); none left (checked with ps).
