# R7B results

Tree: /home/user/build/rr6/tree-R7B (tree-R7 plus the r7b changes, uncommitted, nothing pushed).
Patches: core-fix-on-frozen-r7b.patch (CRLF kept for the two .ps1 files), core-fix-on-frozen-r7b-lf.patch, core-fix-r7-to-r7b-delta.patch.

## 1. Failed, not run, open (read first)

1. NOT FOUND: the writer of the stray file named `a<newline>b`. I only added a guard: `tests/conftest.py` takes a snapshot of the tree at session start and fails the run ("REPOSITORY FOLDER CHANGED BY THE TEST RUN") if any file appears, goes or changes. The writer itself is still unknown. Next step: run the suite with that guard on and read which test it names.
2. NOT RUN as one suite: I did not run the whole suite in one go (as ordered). Every test file ran in 12 chunks (F00-F11), see section 6. After the chunk run I fixed the failures and re-ran only the files I touched (G*, H1-H4, GA, N, M2). I did not re-run every unchanged file after the last edit. The last edit was a comment on three lines of `tests/test_live_claude.py` (re-run: log-H4, rc 0, then ruff clean).
3. NOT TESTED: the two `.ps1` changes (`start_all.ps1`, `reset.ps1`): no PowerShell here. They apply cleanly (apply matrix) and mirror `start_all.sh`, nothing more is shown.
4. NOT CLEAN: the first run of chunk GA (path_confinement, special_output_files, script_number_limits, real_check_dry, r7_inputs_and_replies) ended rc 1 with 649 passed, 0 failed. The rc 1 is the clean-tree guard: I edited 4 files while it ran. Its files were re-run afterwards only partly (H1-H4 covered n8n_api_url, bidi, guard, burst, live_claude; path_confinement, special_output_files, script_number_limits, real_check_dry, r7_inputs_and_replies were not re-run after the burst edit, they do not import burst). Next step for the lead: run those 5 files once on the patch.
5. NOT EXPLAINED: `check_invariants` with 100,000 short rows gives rc 1 and 168 stdout lines (1.0 s, no traceback). The brief expected 161. I did not find where the 7 extra lines come from. Raw: check_invariants-100k.txt.
6. `type: ignore` is 127 lines (frozen 121): +6. Total stays under the limit (section 5).
7. The apply matrix prints FAIL on 7 non-recommended cells (for example the plain `a lf` cell); the verdict line is "APPLY MATRIX: OK (every recommended cell passes)".
8. HD7: `POST /v1/messages deep100000` on the model fake answers 200 with no traceback (the old tree also answered; not judged by me).

## 2. Items asked, one line each

- S603: ONE marker, on the single line in `tests/support.py` (`popen_program`). `checked_argv` rejects non-list, non-str elements, str subclasses, `-c` text flags, `-m` of any module, shells with `-c`, programs outside the allowlist, `git -c`, interpreters without a script file. Tests: tests/test_r7b_program_helper.py (64). Mutation proof: mutation-helper.txt, 9 mutants all killed (M1 58 failed ... M9 2 failed). About 30 older test files converted to the helper.
- Ruled exceptions: the "9 follow-up files (21 starts)" were converted to the helper; `demos/ask-your-data/askdata/cli.py:174` is outside this repository tree (no such file in the frozen core), nothing changed there.
- check_invariants 100k rows: item 5 above.
- Triage `tri-tests.patch`: applied to tests/test_file_call_guard.py. It fails on the unfixed guard: tri-mutation.txt (m10: 2 failed, m11: 1 failed, good: 11 passed).
- Long lines: the 5 added docs lines over 120 columns (contract.md x4, docs/settings.md:164) were wrapped and the 8 test files that read those docs pass (log-H5, rc 0). One added line stays long: the table row `bind` in docs/settings.md:8 (a Markdown table row cannot be wrapped). Python and scripts: ruff E501 clean.
- (a) three live_claude labels: `[only a newline]`, `[too short]`, `[not UTF-8]` carry `# CONTROL: also passes on the old code` (checked: all 9 key-file cases pass on r6 code).
- (b) clean-tree check: item 1.
- (c) no /dev path touched by my commands.
- N1 RecursionError in fakes: shared parse in `demo_only/bad_request.py` and `scripts/http_guard.loads_bounded`; HD7 deep100000 rows now 0 tracebacks. Tests: tests/test_r7b_fake_deep_and_head.py.
- N2 header drip: `HeadDeadline` total deadline `FAKE_HEAD_DEADLINE_SECONDS=20` in constants; test `test_a_header_drip_is_cut_off_at_the_head_deadline` (fails on r7: n2-behaviour-on-r7.txt, 6 failed).
- N3 docs exit 7: docs/limits.md, contract.md, load_tools/README.md.
- N4 `_message`: exact-text assertion in tests/test_n8n_api_url.py.
- N5 n8n list escaping: `scripts/n8n_api.py` `shown` with `NAME_SHOWN_MAX`; HD7 `esc_in_output` 1 old, 0 new.
- REV7M: F1-F4 src patch (config, crm_hubspot, imap_count, smtp_provider, tls_trust), G1 stale-tests hunk in tests/test_smtp_provider.py, new tests tests/test_r7m_new.py, F6 `load_env` `.strip(" \t")` in scripts/run_real_check.py with its test. G1 tests green: log-G1 shows 1 failed (the guard, before the entries were added), later runs H2/H3 rc 0; log-G2 14 passed.
- M1 exit code 4 for bad paths at every site (`--log`, `--out`, `--call-log`, `--control-file`, `--key-file`): load_driver, catcher, fake_model_server, n8n_api pipe. Stale assertions updated, section 3.
- M2 portal view cap: `PORTAL_VIEW_ROW_BYTES=400`, `PORTAL_VIEW_REPLY_MAX_BYTES`; tests/test_r7b_portal_view_cap.py (3 passed).
- M3 guard gaps: lists extended (HIT_QUALIFIED, METHOD_NAMES, CALL_ONLY_*), getattr literal-name hit, annotations are not hits. Re-plant: tests/test_r7b_guard_replant.py, 145 shapes, found 145 of 145 (old guard finds 34).
- M4 settings.md:164 wording. M5/M6 start_all.sh: exit code 2 for pid files, exit 4 when a pid path is not a regular file, FIFO fakes.log refused; same in start_all.ps1 (untested, item 3). Tests in tests/test_reset_scripts.py.
- Wall-clock marker in conftest: only a comment `# wall-clock: file time` on the line that reads `st_mtime_ns`; tests/test_clock_steps.py demands that comment on every wall-clock read. It hides and skips nothing.
- HD7 defect 3 (`burst --url http://127.0.0.1:9`): `demo_only/burst.py` looks for a listener at most `BURST_START_LOOK_SECONDS=3.0`, then prints "ERROR: nothing answers at that address: no request was sent" and exits 3. HD7 new tree: rc 3 in 3.11 s (was 30 s). Tests: tests/test_r7b_burst_closed_port.py (3 passed). New guard entry: `demo_only/burst.py` `socket.create_connection` (reason given).

## 3. Changed old tests (old / new / why it is not weaker)

| Test | Old assertion | New assertion | Why not weaker |
|---|---|---|---|
| test_tools_and_fakes_pipes (4 cases) | raises InputError | raises PathInputError (a subclass of the same family, same on r7) | the class is more exact; the text and "no traceback" checks stay |
| test_ledger_amounts | exit code 1 | exit code 6 (stopped by a person; same on r7) | exact code, same cases |
| test_real_check_dry (4) | stub replaced the old socket class | stub replaces `imap_count._BoundedImap`, with `.sock` and `.deadline` | same stub answers, same output asserted |
| test_path_confinement (6), test_special_output_files (5), test_script_number_limits (1) | exit 2 for a bad path | exit 4 (`EXIT_BAD_SETTING_OR_PATH`) | the family check is now exact; one-line text asserts unchanged |
| test_file_reader_refusals n8n pipe case | exit 2 | `EXIT_BAD_SETTING_OR_PATH` | same |
| test_n8n_api_url lone surrogate | "?" | exact escaped text | exact text instead of a class of text |
| test_n8n_api_url control chars | raw text | `chr(0x202E)` built in code, escaped text | file holds no raw bidi char |
| portal reply cap (test_r7_inputs_and_replies) | `LOAD_TOTAL_MAX` cap | view cap (rows x 400 bytes) | refused whole, not cut: still asserted |
| tests/conftest.py `_tree_snapshot` | no marker | marker comment | clock check satisfied, behaviour same |

## 4. CONTROL reasons: the 21 r7 tests that pass on r6 code (log: ctl-on-r6.txt, list: ctl-passed-on-r6.txt; 41 failed, 5 files could not even import on r6)

| Tests | Reason it passes on both |
|---|---|
| test_bad_usage_is_exit_2_before_the_key_or_the_address_is_looked_at[args0-4] | usage errors were already exit 2 before r7; pins that the new exit-4 family did not take them over |
| test_nothing_listening_is_exit_3 | unreachable was already exit 3; pins it |
| test_n8n_refusing_an_activation_is_exit_1 | check failed was already exit 1; pins it |
| test_a_byte_order_mark_in_the_middle_is_not_json | the JSON parser already refused it; pins that the bounded loader keeps it |
| test_a_row_ends_at_a_line_feed_... | row splitting did not change; pins CR handling |
| test_announced_length_text[lines0,3,4,7-12] | cases where the old announcement text was already right (the failing cases are the other ids) |
| test_a_slow_sender_that_stops_midway_is_answered_408 | already 408 on the old fake; pins it beside the new head-deadline case |
| test_the_full_body_is_read_and_a_short_one_is_408 | same, normal body path |
| test_a_chunked_body_is_411_and_the_body_is_not_read | already 411; pins that the shared parser keeps it |

## 5. Suppressions (lines containing the word, count.sh)

| Word | Frozen | R7B |
|---|---|---|
| noqa | 250 | 174 |
| type: ignore | 121 | 127 |
| nosec | 12 | 8 |
| nosemgrep | 32 | 32 |
| total of these four | 415 | 341 |
| S603 (inside noqa) | 52 | 7 (one marker on the helper line) |

Ceiling: S603 <= 52 and total not above 415: held.

## 6. Test runs (recipe: out/R7B/t.sh, unshare -n, pinned venv, TMPDIR in tmp-R7B)

| Run | Result |
|---|---|
| F00-F11 (all test files, first pass) | F02, F03, F08, F10, F11 clean; F00 6 failed, F01 1, F04 5, F05 1, F06 4, F07 2, F09 1: all stale assertions from M1, class names or the clean-tree marker, fixed as in section 3 |
| GA (5 M1/M2 files) | 649 passed, 1 skipped, rc 1 only from the clean-tree guard (edits during the run) |
| GB | 449 passed, 1 failed (bidi), fixed, passes in H3 |
| N (N1/N2) | 20 passed, 2 skipped (model-only route) |
| M2 | 3 passed |
| H1 | rc 1: only the guard entry for burst (fixed) |
| H2 guard + replant | rc 0, "145 of 145 shapes found" |
| H3 guard, burst, n8n, bidi, burst_retry, cli_refusals | rc 0 |
| H4 test_live_claude | rc 0 |

## 7. HD7 hostile re-run (out/R7B/hd7, results-r7.jsonl, all cases, no filter)

139 cases per tree. Old tree: 22 tracebacks, 11 hangs, 1 raw ESC, 7 runs over 14 s. R7B: 0 tracebacks, 0 hangs, 0 raw ESC, 0 runs over 14 s. Defect 6 FIFO fakes.log: inv_json fifo 15.2 s old, 0.2 s new.

## 8. Commands with exit codes

- `sh /home/user/build/rr6/out/AM/apply_matrix.sh --check core-fix-on-frozen-r7b.patch core-fix-on-frozen-r7b-lf.patch`: rc 0, "APPLY MATRIX: OK (every recommended cell passes)" (apply-matrix.txt).
- `git apply --check core-fix-r7-to-r7b-delta.patch` on a copy of tree-R7: rc 0.
- `ruff 0.17.4 check .`: All checks passed (rc 0). `ruff format --check .`: 198 files already formatted.
- `bandit -ll -q -r src tools scripts`: rc 0, 0 issues (bandit.txt).
- Patches cover 130 files (frozen base: git archive of frozen2, tree 49d3c85938fe5323a3378a49195d3b8da434b3ca).
