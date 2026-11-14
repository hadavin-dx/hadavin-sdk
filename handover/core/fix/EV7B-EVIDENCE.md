# EV7B EVIDENCE: independent evidence run on the r7b patch

Evidence runner only: raw numbers, no verdicts. Written 2026-11-13/14 UTC (IST = UTC+5:30). Machine: 4 cores (the plan assumed 6). Raw files are in /home/user/build/rr6/out/EV7B/ (names given per section).

## 0. GAPS FIRST (not run, not clean, failed, slips)

1. FAILED: `tests/test_hygiene.py::test_hygiene_scan_public` failed in full suite group A and alone (alone-run `alone/hygiene.log`: 1 failed, 23 passed). Cause measured: the test scans files listed by `git ls-files`; my tree had `git add -N -A .` (plan sections 1 and 6 do this) so the 39 new files of the patch were listed, and the scan reports hard-coded literals (URLs, IPs, hosts) in new test files (first 50 shown, e.g. tests/test_file_call_guard.py:838 `http://x`, tests/test_r5_refusals.py:282, tests/test_r7_exit_codes.py:233, tests/test_r7b_guard_replant.py:125 ...). Same test in a copy with `git reset` (new files untracked): 24 passed (`alone/hygiene-noindex.log`). Same copy after `git add -A` (new files staged, as a commit would do): 1 failed, 23 passed (`alone/hygiene-added.log`). So: on a tree where the patch files are tracked in git, this test fails; on a tree where they are untracked it passes. Not judged further. The plan's own `git add -N` step changed the tree state during the suite (the suite was started after it).
2. NOT QUIET RUN: other agents' processes ran on the same 4-core machine the whole time (for example `pytest tests/test_r7_mail_context.py ...` and `fake_model_server` of other trees at suite start; load average at suite start 1.2, during B up to 4.5 when my mutant/fb/hostile jobs were also running). Slowest tests in B (65 s `test_real_check_dry`, `test_clock_steps`, `test_path_confinement`) ran while other agents' tests ran.
3. /dev/null was a regular file during this run (tainted container, EV7-PLAN section 10). Nothing of mine was meant to write to /dev. I SLIPPED four times by typing a /dev path in tool commands: (1) `cp ... /dev/stdout`, (2) `> /dev/null` in a grep line, (3) `> /dev/null` in a sed line, (4) an `ls` and `wc -c` of /dev/null itself (a probe, forbidden by rule 7); the harness denied each one before it ran; nothing ran. I did not look at /dev/null at all, so I cannot say whether the suite runs wrote into it (section 10). The one script that wrote to /dev/null by itself, `out/HD7/run_hostile_r7.sh` (three `openssl ... >/dev/null`), I ran as a copy with the redirect changed to a file in the work folder (`run_hostile_ev7b.sh`). `hd7_case.py` opens `/dev/null` for reading only (stdin=DEVNULL). Re-check list of DEVNULL / /dev/null uses on the r7b tree: section 10.
4. Fail-before: `tests/test_reset_scripts.py` and `tests/test_r4_refusals.py` hit the 300 s timeout on the old code (rc 124, no summary line); their ids count as "no result line on old code", not as failed. 1182 of the 1439 new/changed ids have no result line on old code (whole files that failed to collect, import errors, or timeouts): `required_fails.py` cannot tell these apart from "never run".
5. The old tree for fail-before had the NEW `tests/support.py` and `tests/conftest.py` copied in (the new tests import `run_program`, `text_file`), so old-code results were measured with new helper files.
6. Mutants: my first test set was the 16-file list of the reviewer (`mutants/testset.txt`), which does NOT contain `tests/test_r7m_new.py` or the `tests/test_r7b_*.py` files. Two mutants SURVIVED with that set (N8, N12b). N8 recheck with `tests/test_r7m_new.py::test_n8_...` : KILLED (section 8). N12b rerun with the 16 files plus all 13 tests/test_r7*.py files (this includes tests/test_r7m_new.py and the IMAP/SMTP files test_smtp_provider, test_r7_mail_context): KILLED by test_r7m_new.py::test_f2_an_endless_run_of_untagged_lines_ends_at_the_total_time_limit. All other mutants KILLED. Plan counts differ: the plan names 37 (40) mutants, the lead's brief said 48; I ran the reviewer's 48 spec (REV7M/work/specs.json: M01-M30, N1-N16 with N6a/N6b, N12 split by me into N12a read and N12b readline) = 49 mutants + 1 control. Specs for M30 and N12 were adapted because the r7b source text differed (M30 now `or not self.user.isascii()` removal; N12 text appears twice).
7. Not run at all: Windows PowerShell scripts (no PowerShell here: apply and line endings only); CodeQL, SonarCloud, CodeRabbit, semgrep; section 4(d) of the plan (`run6.sh root|nonroot`, user 65534 with bind-mounted /dev/null): NOT run (time box and /dev rule). Plan section 7 hostile drivers of EV6 (`hostile_driver.py` ... `hostile_wrap.py`, `run6.py`, `run6b.py`) NOT run: I ran only the lead-ordered `run_hostile_r7.sh` (HD7 139 cases per tree). NUL byte in env/argument cannot be started by the OS.
8. `a`+newline+`b` stray file: NOT reproduced. After chunk A and chunk B of the full suite the tree root showed no such file (ls and git status compared with the baseline). Two other items did appear, see section 9: an empty folder `data/` (git-ignored, so the conftest guard does not see it) and `__pycache__` folders.
9. My own slips in the tree under test: before the suite I ran `python3 ... --help` on load_driver and fake_model_server without PYTHONDONTWRITEBYTECODE, which created `__pycache__` in src/lead_desk, scripts, tools; I removed them at 23:10 while suite A ran. Other `__pycache__` folders (demo_only, src/lead_desk, scripts, tools) appeared in tree-EV7B at 23:13:02 (between A and B); the writer is not identified (my commands then were reads; another agent's process is possible).
10. In my stray-file bisect copy, `tests/test_r7_no_replace_of_special.py` failed 3 socket cases alone with `OSError: AF_UNIX path too long` because my TMPDIR path was long; this is my harness, not the suite (the same file passed in the full runs).
11. check_invariants: the 168 lines are listed by position (section 7b); the reason for 168 is only described, not explained.
12. File guard `tests/test_file_call_guard.py`: passed alone and in the suite on r7b (section 4); the earlier r7 failure was not reproduced.

## 1. Head, patch hashes, apply (raw: sha256.txt, apply/apply-matrix.out)

```
git rev-parse 'frozen2^{tree}' (demo-frozen/repo2) = 49d3c85938fe5323a3378a49195d3b8da434b3ca
tree-EV7B base commit tree (git archive of frozen2 + git init) = 49d3c85938fe5323a3378a49195d3b8da434b3ca
07091087654bb2ca4a5aedd9f85b5d44f58aa53aa4e2b41bfae28336626704ce  /home/user/build/rr6/out/SNAP7B/core-fix-on-frozen-r7b-lf.patch
68a5e05cf6154c3776ec5c4f623998282a50fc9d1fe78accc035b76fe69f58e9  /home/user/build/rr6/out/SNAP7B/core-fix-on-frozen-r7b.patch
a3ff86c56f86c1e273b1163b5fd79a792dda7a5abf6972131bc13dd759b1f80e  /home/user/build/rr6/out/SNAP7B/core-fix-r7-to-r7b-delta.patch

sha256sum -c of SNAP7B/sha256.txt: the three patches OK; RESULTS.md OK; apply-matrix.txt OK (SNAP7B copy).
sha256sum -c of handover/core/fix/sha256-r7b.txt: the three patches OK; RESULTS.md and apply-matrix.txt are not in that folder (could not be read: 'No such file').
git apply --check core-fix-on-frozen-r7b.patch: rc 0; git apply: rc 0
changed files after `git add -N -A .`: 130 (git diff --numstat | wc -l); git apply --numstat of the patch: 130
scripts/reset.ps1 lines=80 lines-with-CR=80 ; scripts/start_all.ps1 lines=43 lines-with-CR=43
```

## 2. Apply matrix (apply/apply-matrix.out; command: sh handover/core/fix/apply_matrix.sh <crlf patch> <lf patch>, AM_OUT set; cmp of the script with out/AM copy: identical)

```
files touched: crlf patch 130, lf patch 130; .ps1 files: scripts/reset.ps1 scripts/start_all.ps1 
checkout a: .ps1 line endings before patching: CRLF CRLF
checkout b: .ps1 line endings before patching: CRLF CRLF
checkout c: .ps1 line endings before patching: LF LF
TYP PATCH MODE   CHK   APPLY PS1END FILES     CONTENT PYTEST  RESULT NOTE
--- ----- ----   ---   ----- ------ -----     ------- ------  ------ ----
a   crlf  plain  0     0    OK     130/130   SAME    -       PASS   
a   crlf  iws    0     0    OK     130/130   SAME    -       PASS   
a   crlf  iwsfix 0     0    OK     130/130   SAME    -       PASS   
a   crlf  pbin   0     0    OK     130/130   SAME    -       PASS   
a   lf    plain  1     1    OK     0/130!    n/a     -       FAIL   
a   lf    iws    0     0    BAD    130/130   SAME    -       FAIL    scripts/reset.ps1=MIXED(want CRLF); scripts/start_all.ps1=MIXED(want CRLF);
a   lf    iwsfix 0     0    OK     130/130   SAME    -       PASS   
a   lf    pbin   1     1    OK     130/130   n/a     -       FAIL   
b   crlf  plain  0     0    OK     130/130   SAME    -       PASS   
b   crlf  iws    0     0    OK     130/130   SAME    -       PASS   
b   crlf  iwsfix 0     0    OK     130/130   SAME    -       PASS   
b   crlf  pbin   0     0    OK     130/130   SAME    -       PASS   
b   lf    plain  0     0    OK     130/130   SAME    -       PASS   
b   lf    iws    0     0    OK     130/130   SAME    -       PASS   
b   lf    iwsfix 0     0    OK     130/130   SAME    -       PASS   
b   lf    pbin   1     1    OK     130/130   n/a     -       FAIL   
c   crlf  plain  1     1    OK     0/130!    n/a     -       FAIL   
c   crlf  iws    0     0    BAD    130/130   SAME    -       FAIL    scripts/reset.ps1=MIXED(want LF); scripts/start_all.ps1=MIXED(want LF);
c   crlf  iwsfix 0     0    OK     130/130   SAME    -       PASS   
c   crlf  pbin   1     1    OK     130/130   n/a     -       FAIL   
c   lf    plain  0     0    OK     130/130   SAME    -       PASS   
c   lf    iws    0     0    OK     130/130   SAME    -       PASS   
c   lf    iwsfix 0     0    OK     130/130   SAME    -       PASS   
c   lf    pbin   0     0    OK     130/130   SAME    -       PASS   

RECOMMENDED CELLS (from the README table: a=crlf:plain b=crlf:plain c=lf:plain)
type a: cell a-crlf-plain PASS   pytest: ok [67 passed in 26.45s]   (best cell by the matrix: crlf:plain)
type b: cell b-crlf-plain PASS   pytest: ok [67 passed in 26.78s]   (best cell by the matrix: crlf:plain)
type c: cell c-lf-plain PASS   pytest: ok [67 passed in 26.70s]   (best cell by the matrix: lf:plain)

COMMANDS (derived from the matrix; run from the top folder of the checkout):
  [a] plain archive / zip download (no .git folder):  git apply --check core-fix-on-frozen-r7b.patch && git apply core-fix-on-frozen-r7b.patch
  [b] git clone on Windows (core.autocrlf=true):  git apply --check core-fix-on-frozen-r7b.patch && git apply core-fix-on-frozen-r7b.patch
  [c] archive with every text file converted to LF:  git apply --check core-fix-on-frozen-r7b-lf.patch && git apply core-fix-on-frozen-r7b-lf.patch

FIX COMMAND check: cells *-iwsfix prove the line-ending fix (CRLF: sed -i 's/\r*$/\r/' ; LF: sed -i 's/\r$//'); status per type:
  a: crlf-patch=PASS lf-patch=PASS
  b: crlf-patch=PASS lf-patch=PASS
  c: crlf-patch=PASS lf-patch=PASS

APPLY MATRIX: OK (every recommended cell passes)
rc=0
```

## 3. Full suite, once, detached (raw: full-A.log, full-B.log, groupA.txt, groupB.txt, counts-per-file.txt, collect-all.txt)

Machine at start: `load-at-start.txt` = 0.87 0.90 0.88 1/130 1465 Fri Nov 13 22:58:37 UTC 2026  (that file was written just before the run; another agent's pytest was on the machine: NOT A QUIET RUN). Recipe: TMPDIR=tmp-EV7B/<group>, PYTHONPATH=<tree>/src, PYTHONDONTWRITEBYTECODE=1, unshare -n via lo_up-q4g.py, PLAYWRIGHT_BROWSERS_PATH, GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1, timeout 2400, `-q -p no:cacheprovider -rfs --durations=10`. Group files: EV6 groups plus new files to the lighter group; 123 test files = 62 (A) + 61 (B), union equals all files present, overlap 0; 5170 ids collected (`collect-all.txt`). Every test file ran; files NOT run: none.

```
group A: 1 failed, 2502 passed, 5 skipped, 47 warnings in 816.58s (0:13:36)
rc=1 wall=817s
group B: 2660 passed, 2 skipped, 11 warnings in 960.57s (0:16:00)
rc=0 wall=961s
total: 2502+2660 = 5162 passed, 1 failed, 5+2 = 7 skipped = 5170
```
Failed / skipped lines (copied):
```
FAILED tests/test_hygiene.py::test_hygiene_scan_public - AssertionError: hard...
SKIPPED [1] tests/test_n8n_api_url.py:524: root (and Windows) can read a file with no permissions
SKIPPED [1] tests/test_server_hardening.py:224: measurement run: set LEAD_DESK_LOAD_N
SKIPPED [1] tests/test_stall_eviction.py:526: the reset that destroys the reply happens on Windows only
SKIPPED [2] tests/test_r7b_fake_deep_and_head.py:58: only the model fake has /v1/messages
SKIPPED [1] tests/test_book_folder_refusals.py:233: root can read any file
SKIPPED [1] tests/test_path_confinement.py:285: ntpath.isreserved needs Python 3.13
```
Slowest ten, A:
```
36.76s call     tests/test_hygiene.py::test_hygiene_scan_public
31.65s call     tests/test_r5_refusals.py::test_the_load_driver_ends_with_exit_3_and_one_line_when_the_desk_is_not_there
20.02s call     tests/test_r7_inputs_and_replies.py::test_a_slow_sender_that_stops_midway_is_answered_408
10.03s call     tests/test_later_approval.py::test_decision_busy_is_503
10.01s call     tests/test_r7_inputs_and_replies.py::test_the_full_body_is_read_and_a_short_one_is_408
8.99s call     tests/test_gitleaks_semgrep_lock.py::test_semgrep_lock_allowances_are_narrow
7.64s call     tests/test_portal_look.py::test_one_colour_per_follow_up_state_in_ring_legend_timeline_and_badge[dark]
6.68s call     tests/test_portal_look.py::test_one_colour_per_follow_up_state_in_ring_legend_timeline_and_badge[light]
5.99s call     tests/test_portal_api.py::test_real_process_restart_x20
5.91s call     tests/test_portal_api.py::test_big_book_is_fast_and_cheap
```
Slowest ten, B:
```
65.11s call     tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end
64.89s call     tests/test_clock_steps.py::test_dry_run_survives_a_wall_clock_step[-120.0]
64.68s call     tests/test_path_confinement.py::test_a_real_run_with_every_path_outside_the_allowed_folders_runs_to_the_end
64.48s call     tests/test_real_check_dry.py::test_a_failed_crm_read_back_ends_with_counts_a_result_file_and_a_clean_up_note
36.21s call     tests/test_clock_steps.py::test_dry_run_survives_a_wall_clock_step[3600.0]
35.66s call     tests/test_real_check_dry.py::test_a_dry_run_where_every_send_ends_in_doubt_fails
34.53s call     tests/test_real_check_dry.py::test_dry_fakes_leave_no_certificate_or_key_folder_behind
33.17s call     tests/test_real_check_dry.py::test_a_failed_write_after_a_failed_read_back_keeps_the_result_on_the_screen
28.94s call     tests/test_desk_edge_cases.py::test_burst_distinct_emails
17.44s call     tests/test_desk_http_edge_cases.py::test_startup_50_pending
```
Per-file counts (collected ids): counts-per-file.txt (123 files, sum 5170).

## 4. Alone re-runs (alone/*.log; recipe as suite, one test at a time, other jobs of mine NOT running during this chain; other agents' jobs were)

```
guard                        11 passed in 1.62s | rc=0 wall=2s
hygiene                      1 failed, 23 passed in 41.82s | rc=1 wall=43s
drawer1                      1 passed in 2.60s | rc=0 wall=3s
drawer2                      1 passed in 2.72s | rc=0 wall=3s
drawer3                      1 passed in 2.66s | rc=0 wall=3s
portal-lead-pages-file       31 passed in 46.18s | rc=0 wall=47s
crm1                         56 passed in 31.23s | rc=0 wall=31s
crm2                         56 passed in 31.14s | rc=0 wall=32s
scrub                        254 passed in 26.35s | rc=0 wall=27s
shell                        146 passed in 4.39s | rc=0 wall=4s
burst                        1 passed in 6.79s | rc=0 wall=8s
hygiene-noindex              24 passed in 50.21s | rc=0 wall=50s
hygiene-added                1 failed, 23 passed in 43.65s | rc=1 wall=45s
```
Lead addition (1): `tests/test_file_call_guard.py` alone on r7b: command `./run-alone.sh guard tests/test_file_call_guard.py`, raw output `alone/guard.log` = `11 passed in 1.62s`, rc=0 wall=2s. In the full suite it was inside group A, which had only the hygiene failure. `test_every_import_and_file_call_in_the_code_is_listed_with_a_reason_or_goes_through_the_one_reader` passed alone (1.07 s).
Not run: plan 4(c) extra new time/port/thread test files alone, and 4(d) root vs non-root step 6.

## 5. Fail-before as a required-fails check (raw: fb/*.log (74 files, -rA), fb-all.log, fb-summary.txt, new-ids.txt, required-fails-vs-frozen.out/.txt, fb-support-diff.txt)

Old tree: tree-FB-EV7B = clean `git archive frozen2` + the 74 new/changed test files of the patch + new tests/support.py and tests/conftest.py (the only two non-test files in tests/ that differ). Each file alone, `-rA --continue-on-collection-errors`, timeout 300 s, 2 chains in parallel (NOT quiet). Not run: the r6-head comparison (`tree-FB2`), since the lead's order named the unpatched frozen tree.

```
new-test ids given: 3881; checked as new/changed: 1439; failed or errored on old code (named FAILED/ERROR in the input): 155; PASS on old code: 102; no result line on old code: 1182
unchanged tests skipped: 2442; helper-changed files (module-level code differs, tests not flagged for it): 28

     1  tests/test_codeant_demo_only.py
     1  tests/test_codeant_hygiene.py
    11  tests/test_crash_points.py
     1  tests/test_crm_hubspot.py
     9  tests/test_file_call_guard.py
     1  tests/test_followup_b.py
     7  tests/test_hygiene.py
     1  tests/test_ledger_amounts.py
     1  tests/test_mode_safety.py
     1  tests/test_nosemgrep_form.py
     2  tests/test_portal_demo.py
     1  tests/test_portal_mode.py
     3  tests/test_r7b_guard_replant.py
    32  tests/test_r7b_program_helper.py
     3  tests/test_r7m_new.py
     9  tests/test_review_item_edge_cases.py
     5  tests/test_scrub_n8n_export.py
     3  tests/test_special_files_and_plain_text.py
     8  tests/test_special_output_files.py
     2  tests/test_vendor_hosts.py
```
All 102 `REQUIRED <id>` lines (new/changed tests that PASS on old code) are in `required-fails-vs-frozen.out`; I do not judge them. `helper-changed` files (28) are listed in the same file; for them the tool cannot see a helper-only change.

```
TOTAL passed-on-old 2017
files that timed out on old code (rc 124, 300 s): tests/test_reset_scripts.py, tests/test_r4_refusals.py
```

## 6. Lint, bandit, suppressions, long lines (raw: lint.log, bandit.log, suppress.txt, cols.txt)

```
ruff 0.17.1
$ ruff check
All checks passed!
rc=0
$ ruff format --check
198 files already formatted
rc=0
$ bandit -ll -r src tools scripts
(bandit part of lint.log: `bandit -ll -r src tools scripts` via venv python -m bandit: rc=0, 'No issues identified', Medium 0, High 0, Low 9)
```
Second bandit run with the repo's own comment command `bandit -ll -r src tools scripts -c pyproject.toml` (bandit 1.9.4, bandit.log): rc=0, No issues identified, Low 9, Medium 0, High 0. ruff = pinned 0.17.1 binary at /.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/ruff-0.17.1.data/scripts/ruff.

Suppressions (lines containing the word; frozen from a clean archive copy, r7b from tree-EV7B; r6 numbers copied from EV7-PLAN):

| word | frozen | r6 (plan) | r7b |
|---|---|---|---|
| noqa | 250 | 246 | 174 |
| type: ignore | 121 | 127 | 127 |
| nosec | 12 | 11 | 8 |
| nosemgrep | 32 | 32 | 32 |
| S603 | 52 | 66 | 7 |

Added lines that contain a suppression word, verbatim (cut at 200 columns):
```
+    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})  # noqa: S310 (open_http checks it)
+                except Exception:  # noqa: BLE001 - any parse failure must still leave a visible line
+    except Exception:  # noqa: BLE001  (SystemExit of the parser is not an Exception and passes)
+    return http_only_opener(follow_redirects, use_proxy).open(req, timeout=timeout)  # noqa: S310  # nosec B310
+    return subprocess.Popen(checked_argv(argv), **kwargs)  # noqa: S603 (argv is checked by checked_argv above)
+    import subprocess  # noqa: S404
+        with ctx.wrap_socket(far, server_hostname=name) as c:  # type: ignore[attr-defined]
+import subprocess  # noqa: S404
+    assert rrc.folder_cannot_be_made(None) is True  # type: ignore[arg-type]
+        real_mkdir(self, *args, **kwargs)  # type: ignore[arg-type]
+import subprocess  # noqa: S404
+    text = value.text  # type: ignore[attr-defined]
+        def do_GET(self) -> None:  # noqa: N802 (the name the server looks for)
+The S603 ruling: ONE inline marker, on the single start in `popen_program`, and a test that proves the helper refuses a
+    marker = "noqa: " + "S603"
+        with pytest.raises(Exception):  # noqa: B017, PT011  (any refusal; the server log below is the proof)
+import subprocess  # noqa: S404
+        seen.append(kw["key"])  # type: ignore[arg-type]
+        return real(path, max_bytes)  # type: ignore[arg-type]
+import subprocess  # noqa: S404
+            queue.put(f"ok|{PortalDemo._armed(None, FlagFileHooks(p))}")  # type: ignore[arg-type]
```
Added lines over 100 columns by kind (the repo line limit is 120; ruff E501 is clean): tests py: 842; code (src/scripts/tools/demo_only/load_tools) py: 580; docs and other md: 84; code (src/scripts/tools/demo_only/load_tools) sh: 20; code (src/scripts/tools/demo_only/load_tools) md: 6; code (src/scripts/tools/demo_only/load_tools) ps1: 5. Added lines over 120 columns: 1 over120 b/docs/settings.md (r6 had README.md 1 and docs/limits.md 2). Per-file table: cols.txt.

## 7. Hostile runs, check_invariants, load_driver and fake model server (raw: hd7/, hd7.out, inv/, extra/)

### 7a. HD7 hostile run (command: `sh run_hostile_ev7b.sh tree-EV7B tree-old-HD7 out/EV7B/hd7`, a copy of the lead's script with the three `>/dev/null` changed to a log file; ran 23:32-23:39 UTC while my mutant and fail-before jobs were also running)

```
old rows 139 traceback 22 hang 11 raw ESC 1 runs >14s 7 max wall_s 30.02 rows missing traceback key 7
new rows 139 traceback 0 hang 0 raw ESC 0 runs >14s 0 max wall_s 6.13 rows missing traceback key 7
NEW scripts port_desk_taken 3 6.13 False False
```
The only new-tree row with wall time over 5 s: scripts / port_desk_taken, rc 3, 6.13 s. Full table with every row: hd7/hostile-table.md; raw rows hd7/results-r7.jsonl (139 per tree). `mk_table.out`: see file. Not run: the EV6 drivers of plan section 7 and the 7 new-case drivers (`hostile_r7.py`).

### 7b. check_invariants with 100,000 short rows (inv/inv_run.py, tree-EV7B, made-up data from tests/test_load_tools.make_world; raw: inv/out-tree-EV7B-N100000.txt)

```
/home/user/build/rr6/tree-EV7B rc 1 wall 0.5s stdout lines 168 stderr lines 0 traceback False
(re-run with request counts 10, 1000, 20000: also rc 1, 168 stdout lines, 0 stderr lines, no traceback; json starts at line 20 and the sentence 'AT LEAST ONE CHECK FAILED' is line 19 in every run)
```
What the 168 lines are (listed by position, no judging): lines 1-2 table header; lines 3-18 seven checks as a PASS/FAIL table (a 'result check' line, then a detail line, and for failed checks a 'first N of M' line): checks 1 FAIL (100000 without a receipt; first 10 listed), 2 FAIL (1 failed, 1 unknown; first 2 listed: L5, L6), 3 PASS, 4 PASS, 5 PASS, 6 PASS, 7 FAIL ('no intended send time or no drain moment'); line 19 `AT LEAST ONE CHECK FAILED`; lines 20-168 (149 lines) one JSON document: `checks` with 7 objects of 32, 24, 22, 20, 18, 17 and 13 lines (fields id, name, ok, detail, offender_count, offenders (10 entries in check 1, 2 in check 2, empty otherwise), values). First 18 lines saved in inv/table-lines-1-18.txt.

### 7c. Lead addition (2): load_driver burst 1 and 20 against a dead desk port, fake_model_server --port=0 (extra/run-extra.sh; each command wrapped in `timeout -k 2 30`, `unshare -n` with loopback up, PYTHONDONTWRITEBYTECODE=1, work files only in tmp-EV7B/extra)

```
load_driver --base-url http://127.0.0.1:9 --scenario burst:1  : rc=124 wall=30.019142560s (timeout 30 s, rc 124 = hang)
   output: 2 lines, a multiprocessing resource_tracker UserWarning ('6 leaked semaphore objects'); no other text
load_driver --base-url http://127.0.0.1:9 --scenario burst:20 : first run lost its rc line (a leftover worker wrote over the file), rerun separately: rc=124 wall=30.011120262s
   output (rerun): 2 lines, same resource_tracker warning only
fake_model_server --mode ok --port=0 (python -m demo_only.fake_model_server): output 'fake model listening on port 43529'; rc=124 wall=30.012761245s (timeout 30 s, rc 124 = still running when cut)
```
Hang: yes for both load_driver runs (killed by the 30 s timeout, rc 124, no refusal line printed); the fake model server listens and keeps running until the timeout (it is a server). Raw: extra/*.out, extra/*.rc, extra/extra-tmp-listing.txt. Dead port = 127.0.0.1:9 inside `unshare -n` with only loopback up (nothing listens; connect is refused at once). Not judged.

## 8. Mail-path mutants (raw: mutants/mutants.tsv, mutants/*.log, mutants/diffs/, mutants/specs.json, mutants/ext/, mutants/N8-recheck.txt, helper-mut/helper-mutants.tsv)

Method: reviewer's spec (REV7M/work/specs.json: M01-M30, N1-N16) adapted to the r7b source (M30, N12 re-pointed; N12 split into N12a read, N12b readline) = 49 mutants plus a control, my own runner `mutants/runmut.py`: one copy of tree-EV7B per mutant, plant by exact text (count must be 1), `pytest -q -x` with the test files listed in `mutants/testset.txt` = the 16 files: tests/test_r7_mail_context.py tests/test_r6_refusals.py tests/test_r5_refusals.py tests/test_ca_file_reads.py tests/test_smtp_provider.py tests/test_file_reader_refusals.py tests/test_live_claude.py tests/test_n8n_api_url.py tests/test_hubspot_probe.py tests/test_crm_hubspot.py tests/test_cli_refusals.py tests/test_special_files_and_plain_text.py tests/test_r7_no_replace_of_special.py tests/test_special_output_files.py tests/test_wrapper_setting_refusals.py tests/test_regfile_limits_in_constants.py (test_real_check_dry.py added for M20 and M23). Timeout 420 s (600 s for those two). Two workers in parallel. CONTROL = copy with no change: SURVIVED = rc 0 in 179 s (so a mutant counts only if killed). NOT in that set: tests/test_r7m_new.py, tests/test_r7_*.py other than test_r7_mail_context and test_r7_no_replace_of_special, tests/test_r7b_*.py.

| id | result | first failing test | s | what |
|---|---|---|---|---|
| CONTROL | SURVIVED |  | 179 | control: plain copy, no change |
| M02 | KILLED | tests/test_ca_file_reads.py::test_the_context_trusts_only_the_file_and_checks_the_name | 58 | cadata PLUS system store |
| M04 | KILLED | tests/test_r7_mail_context.py::test_m04_optional_chain_check_with_name_check_on_is_refused | 1 | verify_mode test removed |
| M06 | KILLED | tests/test_ca_file_reads.py::test_a_non_ascii_character_inside_a_certificate_block_is_refused[body-line-trust] | 61 | non-ASCII inside PEM block allowed |
| M08 | KILLED | tests/test_r5_refusals.py::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[ledger] | 13 | S_ISREG check removed (open_regular) |
| M10 | KILLED | tests/test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[raw5-too | 85 | size check removed (read_secret_line) |
| M01 | KILLED | tests/test_ca_file_reads.py::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[empty-trust] | 50 | blank-setting check removed (empty cadata) |
| M03 | KILLED | tests/test_r7_mail_context.py::test_m18a_a_context_weakened_after_construction_is_refused_before_any_connectio | 2 | check_hostname test removed |
| M12 | KILLED | tests/test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[\xff\xfep\x00w\x00-\x00f\x00 | 88 | UTF-16 check removed |
| M14 | KILLED | tests/test_r6_refusals.py::test_non_ascii_or_control_key_refused[aaaaaaaa\x7f] | 10 | control-char (isprintable) check removed |
| M05 | KILLED | tests/test_ca_file_reads.py::test_a_valid_ca_file_still_works[trust] | 53 | PEM always read as DER |
| M16 | KILLED | tests/test_r7_mail_context.py::test_f2_ascii_white_space_around_a_key_is_still_dropped | 9 | BOM strip removed |
| M18a | KILLED | tests/test_r7_mail_context.py::test_m18a_a_context_weakened_after_construction_is_refused_before_any_connectio | 2 | no re-check in send |
| M19 | KILLED | tests/test_r6_refusals.py::test_context_and_ca_file_together_refused | 9 | ca_file + context both allowed |
| M21 | KILLED | tests/test_r7_mail_context.py::test_a_mailbox_context_weakened_after_the_settings_were_made_sends_no_login[no_ | 4 | no require_verifying in _session |
| M23 | KILLED | tests/test_r7_mail_context.py::test_m23_a_blank_mailbox_ca_file_setting_is_refused[] | 5 | blank REAL_IMAP_n_CA_FILE falls back |
| M07 | KILLED | tests/test_ca_file_reads.py::test_an_unusable_ca_file_is_refused_at_once_with_fixed_text[text-trust] | 50 | ssl error translation removed |
| M09 | KILLED | tests/test_r5_refusals.py::test_a_key_file_or_ledger_that_is_a_pipe_is_refused_before_the_cost_line[key] | 22 | O_NONBLOCK removed |
| M11 | KILLED | tests/test_r6_refusals.py::test_secret_read_is_bounded | 9 | unbounded read (read_secret_line) |
| M25 | KILLED | tests/test_live_claude.py::test_ok_label_and_cost_log | 92 | live key read AFTER ledger reserve |
| M27 | KILLED | tests/test_r7_mail_context.py::test_f2_the_n8n_key_file_with_a_trailing_odd_space_is_refused_with_exit_4[\xa0] | 8 | own weaker reader restored |
| M29 | KILLED | tests/test_r7_mail_context.py::test_m29_a_non_ascii_token_is_refused_with_exit_2_and_no_connection | 5 | hubspot token weak check |
| N1 | KILLED | tests/test_r7_mail_context.py::test_f1_the_user_goes_to_the_server_as_one_quoted_word[reader | 6 | IMAP user quote removed |
| N3 | KILLED | tests/test_r7_mail_context.py::test_f5_a_five_megabyte_literal_is_refused_without_being_read | 10 | literal cap removed |
| N5 | KILLED | tests/test_r7_mail_context.py::test_f2_the_smtp_password_file_with_a_trailing_odd_space_is_refused[\xa0] | 7 | ASCII-only strip reverted to str.strip |
| N6b | KILLED | tests/test_r7_mail_context.py::test_f3_the_settings_print_no_ca_or_stats_path | 7 | ProviderSettings ca_file repr=False reverted |
| M13 | KILLED | tests/test_smtp_provider.py::test_password_file_formats_give_a_helpful_fixed_text[pw-for-tests-only\nsecond | 83 | multi-line check removed |
| M15 | KILLED | tests/test_r7_mail_context.py::test_m29_a_non_ascii_token_is_refused_with_exit_2_and_no_connection | 5 | ASCII check removed |
| M17 | KILLED | tests/test_r7_mail_context.py::test_m04_the_outbox_and_the_mailbox_reader_refuse_it_too | 1 | no require_verifying in __init__ |
| M18b | KILLED | tests/test_r7_mail_context.py::test_m18b_a_context_weakened_between_the_send_check_and_the_wrap_sends_no_login | 3 | no re-check in _wrap |
| M20 | KILLED | tests/test_r7_mail_context.py::test_m20_a_blank_ca_file_setting_is_refused_not_read_as_system_authorities[] | 4 | blank DESK_SMTPP_CA_FILE falls back |
| M22 | KILLED | tests/test_smtp_provider.py::test_imap_default_trust_rejects_an_untrusted_certificate_and_sends_no_password | 83 | default context unverified (None) |
| M24 | KILLED | tests/test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[a\nb] | 5 | imap user control-char (isprintable) check removed |
| M26 | KILLED | tests/test_r7_mail_context.py::test_f2_the_live_key_file_with_a_trailing_odd_space_is_refused_and_no_ledger_li | 8 | key validation skipped before reserve |
| N8 | SURVIVED |  | 177 | new_verifying_context: min TLS 1.2 not set |
| N10 | KILLED | tests/test_r7_mail_context.py::test_f4_a_context_with_a_security_level_zero_cipher_list_is_refused | 9 | weak cipher check removed |
| N12a | KILLED | tests/test_r7_mail_context.py::test_f5_the_read_cap_and_the_deadline_hold_on_the_reader_class | 8 | read: deadline check removed (read) |
| N13 | KILLED | tests/test_r7_mail_context.py::test_f1_the_user_goes_to_the_server_as_one_quoted_word[rea\\der] | 6 | quote_user backslash escape removed |
| M28 | KILLED | tests/test_file_reader_refusals.py::test_the_one_reader_refuses_every_bad_content_with_one_error_type | 89 | read_regular_bytes size check removed |
| N15 | KILLED | tests/test_r7_mail_context.py::test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused | 9 | MINIMUM_SUPPORTED shortcut inverted (all contexts pass) |
| M30 | KILLED | tests/test_r7_mail_context.py::test_m30_a_non_ascii_smtp_user_is_refused_where_the_settings_are_made[\u03b1\u0 | 5 | smtp user non-ASCII check removed |
| N2 | KILLED | tests/test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[] | 5 | IMAP user check removed |
| N4 | KILLED | tests/test_r7_mail_context.py::test_f4_the_default_context_passes_and_an_old_minimum_version_is_refused | 8 | min-TLS check removed |
| N6a | KILLED | tests/test_r7_mail_context.py::test_f3_the_settings_print_no_ca_or_stats_path | 8 | ProviderSettings stats_file repr=False reverted |
| N7 | KILLED | tests/test_r5_refusals.py::test_the_secret_reader_refuses_each_bad_shape_with_a_fixed_text_that_never_repeats_ | 47 | secret_text_ok: inner whitespace check removed |
| N9 | KILLED | tests/test_r7_no_replace_of_special.py::test_the_counters_writer_leaves_a_special_target_alone[fifo] | 170 | refuse_replacing_special: kind check removed |
| N11 | KILLED | tests/test_r6_refusals.py::test_plain_ascii_key_accepted | 9 | secret length min/max removed |
| N12b | SURVIVED |  | 171 | readline: deadline check removed |
| N14 | KILLED | tests/test_r7_mail_context.py::test_f1_a_bad_mailbox_user_is_refused_where_the_settings_are_made[ | 5 | IMAP user leading/trailing space check removed |
| N16 | KILLED | tests/test_smtp_provider.py::test_starttls_login_and_one_message_to_a_test_inbox_never_to_the_lead | 66 | smtp password read after verifying (order) -> read removed from send |

Counts (50 rows incl. control): {'SURVIVED': 3, 'KILLED': 47}. 49 mutants: 47 KILLED, 2 SURVIVED with the 16-file set (N8, N12b); TIMEOUT 0, OTHER 0, PLANT-FAILED 0.

N8 recheck (lead order): file mutants/N8-recheck.txt. Command: the single test `tests/test_r7m_new.py::test_n8_the_one_context_maker_names_tls_1_2_itself_even_if_the_library_default_is_lower` on a copy with the line `    ctx.minimum_version = ssl.TLSVersion.TLSv1_2` removed from src/lead_desk/tls_trust.py (line 99). Raw result: `1 failed in 0.12s`, rc=1, `assert <TLSVersion.MINIMUM_SUPPORTED: -2> == <TLSVersion.TLSv1_2: 771>`; on the unmutated tree: `1 passed in 0.09s`. The mutant therefore survived in my run only because my test set did not select tests/test_r7m_new.py.

N12b re-run with the 16 files plus all 13 tests/test_r7*.py files: N12b | KILLED | tests/test_r7m_new.py::test_f2_an_endless_run_of_untagged_lines_ends_at_the_total_time_limit | 285 | readline: deadline check removed.

Builder's helper mutants (tests/support.py, 9 mutants from out/R7B/mut_helper.py, run on copies against tests/test_r7b_program_helper.py; raw helper-mut/helper-mutants.tsv):
```
M1 no check at all (return list(argv) first)	rc=1	58 failed, 6 passed in 0.75s
M2 non-str elements accepted	rc=1	7 failed, 57 passed in 0.75s
M3 -c text flags accepted (flag check removed)	rc=1	6 failed, 58 passed in 0.76s
M4 -m any module accepted	rc=1	5 failed, 59 passed in 0.74s
M5 shell with -c accepted	rc=1	10 failed, 54 passed in 0.72s
M6 program allowlist removed	rc=1	6 failed, 58 passed in 0.74s
M7 str subclass accepted (isinstance)	rc=1	1 failed, 63 passed in 0.72s
M8 git -c any	rc=1	2 failed, 62 passed in 0.75s
M9 interpreter needs no script file	rc=1	2 failed, 62 passed in 0.75s
```
Mutation points not found: none. Mutants of the plan's N07-N09 (optional) not run; the plan's own 37-mutant table was replaced by the 48-spec above.

## 9. Stray file `a`+newline+`b` and other tree changes (raw: stray/results.txt, chunk-status.txt, ls-after-A.txt, ls-after-B.txt, ls-baseline.txt, status-baseline.txt)

Full suite chunks: after A and after B the tree root (ls -A | cat -A, git status --short) was compared with the baseline taken before the run: the only difference was a new empty folder `data/` (created 23:09:13 UTC, during A; it is in .gitignore). No file named `a`+newline+`b` appeared in either chunk. The clean-tree guard in tests/conftest.py printed nothing (no 'REPOSITORY FOLDER CHANGED' line in full-A.log or full-B.log; `data/` is git-ignored, which the guard does not see).

Per-file bisect (stray/bisect.sh): every test file run alone, one after the other, in a scratch copy of the tree, root listing and git status compared after each file. Files done at the time of writing: 100 of 123. Files that changed the root listing or git status:
```
tests/test_mode_safety.py rc=0 ls-diff=[< data$ ] status-extra=[]
tests/test_reset_scripts.py rc=0 ls-diff=[< data$ ] status-extra=[]
```
Files with rc not 0 in this bisect: tests/test_hygiene.py rc=1; tests/test_r7_no_replace_of_special.py rc=1 (test_hygiene = the index state described in section 0; test_r7_no_replace_of_special = my long TMPDIR path, AF_UNIX path too long). No file named `a`+newline+`b` appeared after any of these runs.

## 10. /dev/null uses on r7b (devnull-uses-r7b.txt; plan command: grep -rIn -E 'DEVNULL|/dev/null|os\.devnull' tests scripts src tools load_tools demo_only)

35 lines in 15 files on r7b (r6 list: 31 lines in 16 files). Lines that REDIRECT to /dev/null from a shell script or a shell text in a test: scripts/start_all.sh (8), scripts/reset.sh (8), tests/test_shell_single_bracket.py (3), tests/test_book_folder_refusals.py:153, tests/test_nosemgrep_form.py:466. While /dev/null was a regular file, a test or script run that executes these may have written into it; I did not look at /dev/null (rule 7). `tests/test_r4_refusals.py:359` and `tests/test_book_folder_refusals.py:58-59` use the path `/dev/null/x.db` as a bad path (not written). `scripts/run_live_check.py:90` compares with `os.stat(os.devnull)`. The rest are `stdin=subprocess.DEVNULL` (open for read). In my full-suite results those tests passed (no failure named DEVNULL).
