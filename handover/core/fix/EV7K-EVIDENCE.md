# EV7K EVIDENCE (r7m = r7j + r7k delta + r7l delta; the one full run). EVIDENCE RUNNER: raw facts only, no judgement.
Raw files: /home/user/build/rr6/out/EV7K/ (wrapper.log, pytest-full.log, fail-ids-ev7*.txt, stage-*.log, stage-summary.txt, alone-*.log, alone-counts.txt, hostile-*.txt, hostile-f*.out/.err, odd-r7m.txt, odd-burst4-detail.txt, ruff-*.txt, suppress-counts.txt, sha256-r7m.txt, apply-matrix-r7m.txt, build.log, the three patches, checkpoint.md). Run tree: /home/user/build/rr6/out/EV7K/tree-EV7K (plain copy, no .git, no data/, rebuilt from the frozen tree + my r7m patch). Staged copy: tree-EV7K-stage.

## NOT RUN / NOT CHECKED / FAILED (first)
- FAILED, full run on the plain copy: 10 failed. 7 are the git-only ids of EV7G/EV7I/EV7J. 3 are NEW (never failed in EV7G/EV7I/EV7J): `tests/test_real_check_dry.py::test_dry_fakes_leave_no_certificate_or_key_folder_behind`, `::test_a_failed_crm_read_back_ends_with_counts_a_result_file_and_a_clean_up_note`, `::test_a_failed_write_after_a_failed_read_back_keeps_the_result_on_the_screen`. Cause text in the log: `AttributeError: 'types.SimpleNamespace' object has no attribute 'get_lock'` at load_tools/load_driver.py:419 (`_ERRORS.get_lock()`). Facts in "New failures" below: test_real_check_dry.py ALONE = 79 passed; `tests/test_r7k_findings.py` then `tests/test_real_check_dry.py` in one run = 5 failed (the 3 above plus 2 more). Not fixed, not explained beyond those facts.
- FAILED, staged copy: `tests/test_hygiene.py::test_hygiene_scan_public` FAILS in the staged git copy (twice: 1 failed 23 passed, both times). In EV7J all 24 passed there. The hardcoded-literal scan lists 017.0.0.1, 15.0.0.1, 10.0.0.1, 10.0.0.2, 1.2.3.4, 999.1.1.1, http://x.test/ and a test name in CHANGELOG.md, docs/limits.md, src/lead_desk/netconnect.py and tests/test_r7k_findings.py (list below). The other 7 git-needing files pass staged.
- The 8th EV7J id (test_r7f_findings::test_f1_...) PASSES in this full run (not in the failed list).
- NOT RUN: Windows; real IPv6 (this machine has none; errno 97 on AF_INET6 sockets); mutation runs (not asked); a full run inside the staged copy; the full run on a quiet machine (other agents' pytest and a mutation script `mutw3.py` ran during it: load 2.53 at launch, 2.68 at end).
- Hostile driver (f) (driver errors -> exit 3) was run with the worker pool replaced by threads (as tests/test_r7k_findings.py does, because the real pool uses `spawn` and cannot carry a patched sender); the HTTP server and the real `send_with_retries` for the non-failing requests are real. Not run with a real spawned pool.
- tree-R7M contains a `.ruff_cache` folder (made by someone else); the run tree does not (my ruff runs were on a separate copy, before the run).

## Slips of mine
1. First full-run launch (08:00:20Z) was ABORTED by me at about 08:02Z: while it ran I started hostile drivers with `run_hd.sh` and a RELATIVE output path; that script does `cd <tree>`, so hostile-c/d/e.txt(.err) (6 files) were written INTO the run tree during the pytest run (the tree guard would have turned the exit status to 1). I killed only the pids I had started (20385, 20391, 20392; 20682 ended with them), deleted exactly those 6 files, removed `__pycache__` folders, checked the tree equal to tree-R7M again, and relaunched at 08:02:32Z. Logs of the aborted start are kept as wrapper-aborted-first-run.log and pytest-full-aborted-first-run.log (about 2 min of progress, no result line). The hostile (a), (c), (d), (e) runs happened before the relaunch (so 4 `__pycache__` folders exist in the run tree, as in EV7J; they are git-ignored).
2. In the same command I wrote `rm -f $T/hostile-*...` with `$T` not yet set (it expanded to `/hostile-*.txt*`; nothing existed there, checked: `ls /hostile*` = no such file).
3. A first attempt to delete a folder with a glob was refused by the safety check and not run (I used a fresh folder name instead).
4. My first start of the odd-pattern run silently did nothing (scripts had no execute bit; stderr was discarded); I found it from the missing output files and re-ran it with `chmod +x`.
5. Checkpoint lines were written about every 5-10 min but not on an exact 10-minute clock.

## Step 1: patches and tree
- Built with out/R7K/build_patches.sh, same method, paths changed to out/EV7K (build_patches.sh there); scratch git repos are my own copies under out/EV7K/tmp-patch (copied from tmp-R7K: scratch-frozen, scratch-delta, r7j-copy; r7j-copy equals tree-R7J apart from .ruff_cache). build.log: `BYTE-FOR-BYTE-SAME` (frozen + CRLF patch vs a cleaned copy of tree-R7M) and `DELTA-ON-R7J-GIVES-R7M`.
- sha256 (sha256-r7m.txt):
  - ca2fb8c09affd8fe0a72625aaaaf9dc11d59aeeae947185695e583738310590f  core-fix-on-frozen-r7m.patch (CRLF)
  - 722bb90ec808fae0e41ff2a5add9cdc7d46b215d231cd6e165467c92df521feb  core-fix-on-frozen-r7m-lf.patch
  - 9e0cc41d668d893afe34a95bca3994df8e0b299d872b45ccd32a126205966e4b  core-fix-r7j-to-r7m-delta.patch
- Sizes: 1269241 / 1269061 / 136340 bytes. Frozen tree object 49d3c85938fe5323a3378a49195d3b8da434b3ca (same as the brief).
- apply-matrix-r7m.txt: checkout a (.ps1 CRLF CRLF) crlf patch `git apply --check` rc=0; b (CRLF CRLF) crlf patch rc=0; c (LF LF) lf patch rc=0.
- Tree check: tree-R7M vs tree-R7K: differs only in tests/test_r7i_findings.py and tests/test_r7l_findings.py (only in R7M). tests/test_r7i_findings.py and tests/test_r7l_findings.py in tree-R7M are byte-equal to the ones in tree-R7L (`cmp`). The run tree (frozen archive + `git apply --binary` of my CRLF patch, rc=0, `.git` removed) vs tree-R7M: `diff -r` empty before the run (checked after slip 1's clean-up), and after all runs the only differences are tree-R7M's `.ruff_cache` and `__pycache__` folders in the run tree.

## Step 2: the one full run (plain copy)
- Recipe as EV7J (run-full.sh = EV7J's with paths changed: env -i, PLAYWRIGHT_BROWSERS_PATH, GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1, PATH with rr6/bin first, own TMPDIR out/EV7K/tmp-full, PYTHONPATH=<tree>/src, PYTHONDONTWRITEBYTECODE=1, venv-br python -m pytest -q -p no:cacheprovider -rfs, wrapper `timeout -k 20 2700 unshare -n python3 lo_up-q4g.py`).
- wrapper.log: `full start 2026-11-14T08:02:32Z` (IST 13:32:32), `full end 2026-11-14T08:29:05Z rc=1 signal=none` (IST 13:59:05). Result line: **10 failed, 5821 passed, 8 skipped, 60 warnings in 1590.98s (0:26:30)**.
- Failures (10): test_hygiene x4 (test_no_control_characters_in_markdown, test_hygiene_scan_public, test_sh_blobs_no_cr, test_the_secret_scan_files_have_no_carriage_return), test_nosemgrep_form::test_no_bare_nosemgrep_comment, test_raw_bidi_chars::test_no_tracked_file_holds_a_raw_direction_control_character, test_shell_single_bracket::test_no_tracked_script_or_workflow_run_block_holds_a_single_bracket_test, and the 3 test_real_check_dry ids above.
- Skipped (8, same as EV7J): book_folder_refusals:237 (root), n8n_api_url:524 (root), no_placeholders:27 (not a git work tree), path_confinement:285 (Python 3.13), r7b_fake_deep_and_head:58 x2, server_hardening:224 (measurement run), stall_eviction:526 (Windows only). BrokenPipe noise blocks in this log: 0 (EV7J: 2).
### Comparison by test id (sorted FAILED ids, `diff`)
| run | tree | result |
|---|---|---|
| EV7G | r7g | 7 failed, 5468 passed, 8 skipped |
| EV7I | r7i | 7 failed, 5554 passed, 8 skipped |
| EV7J | r7j | 8 failed, 5594 passed, 8 skipped |
| EV7K | r7m | 10 failed, 5821 passed, 8 skipped (1591 s) |
- EV7K vs EV7J: in EV7J only: tests/test_r7f_findings.py::test_f1_a_connect_that_never_completes_ends_at_the_total_not_at_the_step. In EV7K only: the 3 test_real_check_dry ids. EV7K vs EV7I: in EV7K only: the same 3 test_real_check_dry ids; in EV7I only: none. The 7 git-only ids are in all of EV7I, EV7J, EV7K.
### New failures (test_real_check_dry), facts
- Full run: the first failing line of each is `AttributeError: 'types.SimpleNamespace' object has no attribute 'get_lock'` at load_tools/load_driver.py:419 (`with _ERRORS.get_lock():` in `_note_attempt`), reached from scripts/run_real_check.py `send_item` -> `send_with_retries`. tests/test_r7k_findings.py's `_fake_pool_context` builds `ctx.Value = lambda _t, v: types.SimpleNamespace(value=v)` (SimpleNamespace has no get_lock) and runs `load_driver.main`.
- ALONE (`tests/test_real_check_dry.py`, t.sh recipe, plain tree): **79 passed in 205.90s, rc=0** (alone-real_check_dry.log).
- `tests/test_r7k_findings.py tests/test_real_check_dry.py` in that order, one run: **5 failed, 213 passed in 45.02s**; failed ids: test_dry_fakes_run_end_to_end, test_dry_fakes_leave_no_certificate_or_key_folder_behind, test_a_dry_run_where_every_send_ends_in_doubt_fails, test_a_failed_crm_read_back_ends_with_counts_a_result_file_and_a_clean_up_note, test_a_failed_write_after_a_failed_read_back_keeps_the_result_on_the_screen (alone-r7k-then-real_check_dry.log). (In the full run 3 of these 5 failed; the other 2 were not in the failed list there.)
- I did not edit any file to test a cause; no timing involvement is visible (the error is an AttributeError).

## Step 3: staged copy (tree-EV7K-stage: pre-run copy of the tree, `git init; git add -A`, no commit; 313 staged entries via `git status --short | wc -l`; no data/), each file alone, t.sh recipe
| file | result |
|---|---|
| test_hygiene | **1 failed, 23 passed in 37.33 s, rc=1** (rerun: 1 failed, 23 passed in 45.29 s) |
| test_nosemgrep_form | 114 passed in 1.50 s, rc=0 |
| test_raw_bidi_chars | 3 passed in 0.12 s, rc=0 |
| test_shell_single_bracket | 146 passed in 3.56 s, rc=0 |
| test_file_call_guard | 11 passed in 1.56 s, rc=0 |
| test_no_placeholders | 2 passed in 0.15 s, rc=0 |
| test_gitleaks_exceptions | 44 passed in 12.77 s, rc=0 |
| test_gitleaks_semgrep_lock | 4 passed in 7.72 s, rc=0 |
- Untracked listing after each file: `git ls-files -o --exclude-standard` = 0 and `git ls-files -o` = 0 every time (the staged copy had no caches). Names with a control character (a<newline>b etc.) in tree-EV7K and tree-EV7K-stage: 0 (find with a control-character class). data/ absent.
- test_hygiene failure, raw (stage-test_hygiene.log): `AssertionError: hardcoded literals found (file:line:match)`:
  CHANGELOG.md:12 (017.0.0.1, 15.0.0.1); docs/limits.md:191 (017.0.0.1); src/lead_desk/netconnect.py:10 and :56 (017.0.0.1); tests/test_r7k_findings.py:35 (017.0.0.1), :268 (http://x.test/), :611 (test_k6_the_documentation_says_what_the_code_does), :818 (10.0.0.1, 10.0.0.2), :831 (10.0.0.1, 10.0.0.2), :834 (10.0.0.1), :887 (017.0.0.1, 15.0.0.1), :926 (1.2.3.4, 999.1.1.1). I did not look into the rule behind the scan.

## Step 4: ruff and suppression markers
- `/.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/ruff-0.17.1.data/scripts/ruff` = `ruff 0.17.1`, run in a SEPARATE copy (out/EV7K/ruff-copy) before and during the run (never in the run tree). `ruff check .`: "All checks passed!", rc=0. `ruff format --check .`: "224 files already formatted", rc=0 (EV7J: 222).
- Suppression counts (grep -rIo occurrences, .git/__pycache__/.ruff_cache excluded; same method on the three trees): 
| marker | frozen | r7j | r7m |
|---|---|---|---|
| noqa | 251 | 176 | 176 |
| nosemgrep | 40 | 40 | 40 |
| type: ignore | 121 | 126 | 145 |
| nosec | 12 | 8 | 8 |
| S603 | 52 | 7 | 7 |
- The +19 `type: ignore` r7j -> r7m are all in tests/test_r7l_findings.py (per-file count diff, suppress-typeignore-diff.txt: only that file differs).

## Step 5: hostile table (r7m, run tree, `unshare -n`, loopback only)
### (a) 20 hostile hosts (hostile_a.py; 4 paths x 5 hosts): every process rc=0, stderr 0 bytes in all 20, no traceback
- ImapSettings(...), all 5 hosts (label70, empty, trailingdot, singletrailing, surrogate): ImapSettingRefused "the mailbox host must be a host name (letters, digits, hyphens and dots)".
- counts_by_key, all 5: ImapConnectionError "the mailbox could not be read".
- connect_bounded, all 5: OSError "the host name cannot be looked up".
- run_real_check, all 5: its own RESULT rc=2; text "refused: the mailbox host must be a host name (letters, digits, hyphens and dots)" (surrogate: config written with the raw byte 0xff).
Same as EV7J.
### (b) 9 odd server patterns (odd_patterns.py, 1 worker 2 threads; odd-r7m.txt)
```
only202: rc=0 1.9s final={'202': 4}
only429: rc=0 1.9s final={'429': 4}
503-for-3s-then-202: rc=0 3.5s final={'202': 4}
503-twice-then-202: rc=0 2.0s final={'202': 4}
drops-3s-then-answers: rc=3 2.2s  err='ERROR: the desk cannot be reached: every request ended in a connection error (is it running?)'
drops-6-then-answers: rc=3 2.2s  same line
first-202-after-2s-others-closed(M2): rc=3 3.8s final={'202': 1, 'error': 1} stopped=1 err='ERROR: the run was stopped early: 1 of 2 requests were never sent or were given up, because the first tries got no answer; the desk answered ...'
first-202-after-3s-others-closed-burst8: rc=3 4.8s final={'202': 1, 'driver:stopped': 6, 'error': 1} stopped=7
first-answered-then-all-dropped-burst4: rc=3 61.8s final={'202': 1, 'error': 3} stopped=0 unreachable=False
```
- burst:4 detail (odd-burst4-detail.txt): rc=3, 61.8 s, 1 stderr line, 307 bytes: "ERROR: 3 of 4 requests were not accepted: 3 until their retry time was over (gave_up deadline in the log), 0 because the run was stopped early, 0 because the driver itself failed (gave_up driver_error); the desk did not take them, so this run is not a pass (exit code 3); run check_invariants.py on the log". All other lines equal EV7J's (EV7J burst:4 text lacked the "driver itself failed" part).
### (c) first address never answers (hostile_c.py unchanged; hostile-c.txt; stderr 0 bytes)
```
first never answers, second ok, total 10 | connected | 5.0s | timeouts given m-a 5.0, m-b 5.0 | closed 1
first never answers, second ok, total 3  | connected | 1.5s | m-a 1.5, m-b 1.5 | closed 1
one address never answers, total 4       | TimeoutError: timed out | 4.0s | m-a 4.0 | closed 1
both never answer, total 8               | TimeoutError: timed out | 8.0s | m-a 4.0, m-a 3.99 | closed 2   (EV7J: 4.0, 4.0)
```
### (d) 8 silent + 1 good at a 1.2 s total (hostile_d.py; stderr 0 bytes)
```
8 silent then 1 good       | connected | 1.07s | silent 0.133 x4, 0.128 x3, 0.127 (last silent) , good 0.127 | closed 8
1 good first then 8 silent | connected | 0.00s | good 0.133 | closed 0
8 silent only              | TimeoutError: timed out | 1.20s | each silent 0.15 (last 0.149) | closed 8
```
### (e) NEW r7k: first family unavailable; localhost (hostile_e.py; hostile-e.txt; stderr 0 bytes)
```
localhost resolve_bounded                          | [('127.0.0.1', <port>)]   (one address, 127.0.0.1 only)
localhost connect_bounded (real listener)          | connected 0.00s
v6 first (OSError errno 97 at socket creation), v4 second | connected | 0.00s | log: make AF_INET6 (raised), make AF_INET, connect 127.0.0.1
v6 first, v6 second (no address works)             | OSError [Errno 97] Address family not supported by protocol | 0.00s | both sockets attempted
```
The fake raises errno 97 from the socket constructor for AF_INET6 (name look-up and socket class replaced, as in the earlier drivers).
### (f) NEW r7k: driver errors (hostile_f.py; main() in process, thread pool replacing the spawn pool, real HTTP server answering 202; first N sends raise); one stderr line each (307 bytes)
```
burst:4, 4 fail: main rc=3, 4 lines, 4 driver_error lines, accepted 0 | stderr 1 line: "ERROR: 4 of 4 requests were not accepted: 0 until their retry time was over (gave_up deadline in the log), 0 because the run was stopped early, 4 because the driver itself failed (gave_up driver_error); ... (exit code 3); run check_invariants.py on the log"
burst:6, 2 fail: rc=3, 6 lines, 2 driver_error lines, accepted 4 | 1 line "ERROR: 2 of 6 ..."
burst:5, 1 fail: rc=3, 5 lines, 1 driver_error line, accepted 4   | 1 line "ERROR: 1 of 5 ..."
burst:3, 0 fail: rc=0, 3 lines, 0 driver_error, accepted 3        | stderr 0 bytes
```

## Step 6: test counts, each file ALONE (plain tree, t.sh recipe; alone-counts.txt)
| file | result |
|---|---|
| tests/test_r7i_findings.py | 37 passed in 4.80 s, rc=0 |
| tests/test_r7j_findings.py | 40 passed in 69.97 s, rc=0 |
| tests/test_r7k_findings.py | 139 passed in 28.09 s, rc=0 |
| tests/test_r7l_findings.py | 91 passed in 3.95 s, rc=0 |
(EV7J's alone count for the r7f file is not repeated here; in this full run test_r7f_findings had no failure.)

## Clock (UTC; IST = UTC + 5:30)
Start 07:59:45; patches and apply matrix about 08:00; ruff and counts 08:00; first full launch 08:00:20, aborted about 08:02 (slip 1); full run 08:02:32 to 08:29:05; hostile (a), (c), (d), (e) about 08:01 (before the relaunch); staged files, test_real_check_dry alone and with r7k first, and the four alone counts 08:29 to 08:36 (the real_check_dry alone run took 3:26); hostile (f) and the odd patterns 08:36 to 08:41. About 61 min of the 75 min box. Processes started by me: the full-run wrapper (aborted once, ended once), foreground test and driver runs, the odd-pattern wrapper (ended), two background wait loops (ended); none left running (ps checked for "EV7K").
