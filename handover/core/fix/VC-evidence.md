# VC RESULTS (EVIDENCE RUNNER: raw results, no judgement). Tree: /home/user/build/rr6/tree-VC = tree-EV + core-fix-v1.patch (sha256 e0458dda3836ad81..., 3569 lines). Time box used: about 30 min.

## FAILED / NOT CHECKED FIRST
1. FULL SUITE: 1 failed, 4252 passed, 4 skipped, 0 errors, rc=1, 1613.60 s (full.log).
   FAILED tests/test_lead_step_route.py::test_demo_launchers_name_the_demo_file_and_the_off_switch
   First line: `ValueError: substring not found` at tests/test_lead_step_route.py:429 `assert ps.index("DESK_LEADFLOW_FILE") < ps.index("python -c")`.
   Cause (read from the files): the patch replaced every `python -c "..."` helper call in scripts/start_all.ps1 and start_all.sh by
   `scripts/desk_setting.py`; grep -c "python -c" = 0 in both files, so the old test, which anchors on that text, cannot find it.
   The same test PASSES on tree-EV (1 passed) and FAILS on tree-VC. The builder's 13-file run did not include test_lead_step_route.py.
   Line 430 (the .sh twin) would fail the same way once 429 is fixed. Not fixed by me (I do not edit the subject).
2. Skip reasons (4): test_n8n_api_url.py:512 root can read a no-permission file; test_path_confinement.py:281 ntpath.isreserved needs Python 3.13;
   test_server_hardening.py:224 set LEAD_DESK_LOAD_N; test_stall_eviction.py:526 Windows-only reaper reset. gitleaks tests ran (GITLEAKS_BIN set), 0 hygiene skips.
3. One stray line in full.log: "Exception occurred during processing of request from ('127.0.0.1', 60278)" (a fake server's own log text; no test failed on it; not investigated).
4. Not checked: Windows .ps1 scripts (no PowerShell here), a real run, mutations beyond the 10.
5. Load note: the full suite, the mutation job and the two slow files ran together with another runner (V6) on 4 cores; times are inflated.

## Builder-claimed vs measured
| | builder (COMBINE) | measured (VC) |
|---|---|---|
| tests | 522 passed, 5 skipped on 13 files | full: 1 failed / 4252 passed / 4 skipped (4257 tests) |
| baseline | AF 3978 passed 0 failed 4 skipped; V2 (F2 alone) 4103 passed +1 failed | VC adds 149 passed over V2, 1 failed (a different test: launcher text) |
| ruff | clean, 176 files | `ruff check` All checks passed, rc=0; `ruff format --check` 176 files already formatted, rc=0 (ruff.log) |
| bandit | High 0 Medium 0 | severity High 0, Medium 0, Low 9; rc=0 (bandit.log) |
| diff vs COMBINE | none | `diff -rq tree-VC tree-COMBINE -x .git -x __pycache__ -x '*cache' -x data`: no output |

## (2) the two slow files (alone, 13:5x-14:10 UTC)
- tests/test_real_check_dry.py: 71 passed in 230.52 s (slow-test_real_check_dry.log)
- tests/test_clock_steps.py: 29 passed in 100.92 s (slow-test_clock_steps.log)
Both also inside the full suite (no failure of either there).

## (3) 100 MB file of NUL bytes (bigkey.log; file deleted afterwards; each in a fresh process, max resident memory of the child)
| reader | tree-EV (old) | tree-VC (patched) |
|---|---|---|
| live_claude key file | ACCEPTED, read whole (len 104857600): 223.0 MB, 0.31 s | REFUSED LiveTransport "the key file is too large: it must hold only the key": 23.5 MB, 0.12 s |
| smtp read_secret_file | REFUSED too large: 22.2 MB, 0.10 s | REFUSED too large: 22.2 MB, 0.11 s |
| hubspot _key | REFUSED too large: 23.5 MB, 0.12 s | REFUSED too large: 23.8 MB, 0.11 s |
| n8n_api.py N8N_API_KEY_FILE | refused with the fixed line (rc 1): 22.9 MB, 0.09 s | same line (rc 1): 22.6 MB, 0.10 s |
So the gap on the old tree is the live_claude reader only. The n8n reader uses its own MAX_KEY = 4096 (not SECRET_FILE_MAX_BYTES) in both trees.

## (4) hostile inputs: hostile-VC.md (25 rows, 10 s timeout each, under unshare -n + loopback, tty stdin where the script asks a question)
Result: 0 tracebacks, 0 hangs, 0 typed marker echoed, 0 canary key / address printed in 25 rows. Exit codes: 2 refused, 3 desk unreachable (feed with DESK_PORT=1), 4 desk setting refused (reset.sh, start_all.sh, desk_setting.py).
Cosmetic observations (output text, not failures): row 7 prints `refused: --config: --config: no such file` (the option name twice); row 4 (an unknown option and no --source) says `--source: not given`, not the unknown option; row 15 `hubspot_probe --plan --token-env "a b ..."` exits 0 (plan only, the name is checked only in the real run, row 16 refuses a token with a space with exit 2).

## (5) lint: ruff check and format --check clean, bandit -ll rc=0 (see above).
## (6) added lines in the patch: 2297; over 100 columns: 279; over 120 columns: 5 (README.md 840 columns; scripts/reset.sh, reset.ps1, start_all.sh, start_all.ps1 124 columns each; none is Python, so ruff does not check them). linelen.log.

## (7) 10 mutations (copy tree-VCmut, restored and cmp-identical after each): mutations.md
All 10 killed. Targeted test files were tried first; where the targeted file survived, the 13 builder files were run with -x.
| # | mutation | first killing test | note |
|---|---|---|---|
| M1 | stock argparse in feed.py | test_cli_refusals.py::test_what_was_typed_is_never_printed_back[feed: value of a number option] | test_script_refusals_feed.py ALONE did NOT kill it |
| M2 | refusals.py re-export EXIT_UNREACHABLE = 1 | test_file_reader_refusals.py::test_feed_last_valid_index_reaches_the_desk_step_and_the_next_one_does_not | test_cli_refusals + test_script_refusals_feed did NOT kill it |
| M3 | open_regular without kind check | test_file_reader_refusals.py::test_n8n_api_key_file_and_workflow_file_that_are_pipes_are_refused_not_waited_for | |
| M4 | open_output without kind check | test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[lock-pipe] | |
| M5 | live reader size check removed | test_core_key_readers.py::test_live_accept_and_refuse_equal_the_old_rule_except_more_than_one_line_or_too_large | the read stays capped at 4097 bytes |
| M6 | desk_setting.py echoes the value | test_wrapper_setting_refusals.py::test_a_wrapper_shows_the_refusal_line_and_exits_4_for_a_bad_setting[bad1-reset.sh] | |
| M7 | exit code 3 -> 1 (unreachable) | test_file_reader_refusals.py::test_feed_last_valid_index_reaches_the_desk_step_and_the_next_one_does_not | same single test as M2 (-x stops at the first) |
| M8 | pathconfine accepts a FIFO | test_special_output_files.py::test_confine_refuses_an_existing_pipe_for_a_written_file_and_keeps_new_names[pipe] | |
| M9 | future --price-date accepted | test_cli_refusals.py::test_the_live_script_refuses_a_bad_price_date_and_effort_with_the_exact_line[over5-...] | |
| M10 | wall-clock marker removed (run_live_check.py:192) | test_clock_steps.py::test_wall_clock_is_only_used_for_calendar_stamps | |

## Files (all in /home/user/build/rr6/out/VC/): full.log, slow-*.log, bigkey.log, hostile-VC.md, mutations.md, ruff.log, bandit.log, linelen.log, checkpoint.md, scripts hostile.py mutate.py measure.py bigkey_reader.py run-full.sh.
## Processes: none of mine running (full suite, mutation job, slow-file runs all ended). My 100 MB file deleted. tmp-VC, tmp-VCmut and tree-VCmut are left as scratch. tree-EV and tree-COMBINE not touched.
Token use: about 150k tokens (Sonnet 5.5).
