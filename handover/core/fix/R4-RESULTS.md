# R4 results (builder-claimed numbers; nothing here was judged by anyone else)

Tree: /home/user/build/rr6/tree-R4 (copy of tree-R3). Frozen tree 49d3c85938fe5323a3378a49195d3b8da434b3ca. No commit, push, live call, network, mail, or y/yes answer.

## What failed, was uncertain, or was not checked (first)
- NOT run: the full suite (lead runs it). About 70 of 122 test files touch the changed modules; I ran 35 (list below). The other test files were NOT run.
- A pytest run inside tree-R3 (a rule slip, early): bytecode may have been written to tree-R3 (`__pycache__`); no source file there was edited. tree-R4 had `__pycache__` folders from the copy; removed at the end.
- The static guard (tests/test_file_call_guard.py) reads text only. It cannot see a name built at run time from pieces and handed to an object of unknown type, nor code outside the five folders. Its docstring says so.
- Tests that CANNOT fail on the old code (regression pins, plain statement): test_a_good_number_is_not_refused_by_the_parser; test_n8n_api_refusals_never_echo...; test_check_invariants_never_echoes_the_base_name... (through the command line the old code already did not echo; the old echo is pinned by the changed test_load_tools / test_path_confinement tests, which do fail on R3); test_run_real_check_config_refusals_have_the_exact_fixed_text (strengthened pin, old text the same); test_the_real_check_prompt_with_a_closed_descriptor (EBADF: R3 already had `except (EOFError, OSError)`, so this passes on R3; an older run_live_check EBADF test already exists in test_no_terminal_questions.py); the BOM-plus-comments and DER cases of test_ca_file_reads; the NUL case of the control-character test; test_the_start_scripts_say_the_same_refusal_in_both_forms (a stale source pin, corrected; the behaviour test test_the_book_helper_refuses_in_one_line_exit_4_for_both_words does fail on R3). The "no read permission" book test is skipped when run as root (it was run as root).
- Trade-off of lead addition B: check_invariants now caps --requests/--catcher/--model-log/--crm at MAX_JSON_BYTES (16 MiB, the same as --facts), down from 256 MiB. A load run whose log is over 16 MiB (roughly 50 000 requests) is now refused; raise the constant if a real run needs more.
- Real bug found by the new tests: RefusingParser did not recognise option names with digits (`--max-503-rate`), so a bad value gave a generic line. Fixed in tools/refusing_args.py.
- The refusal of run_real_check for a pipe config prints `refused: PathRefused: --config: ...` (the exception type name is printed; fixed text, no typed text). Left as is.
- Other path settings: DESK_DB_PATH with a control character is now refused in book_problem (desk + helper + start scripts). Not touched: path settings read only (CA files, key files); a control character there cannot create a file.

## Per finding (change / tests / fail-before log). Logs in /home/user/build/rr6/out/R4/
1. AST guard: new tests/test_file_call_guard.py (alias resolution, qualified table, method names, one-argument replace/rename, getattr/vars/__dict__/__builtins__/__import__/eval/exec, deny-by-default import table with a reason per file, stale entries fail, 70 planted shapes each caught, each guarded folder). Old guard removed from test_file_reader_refusals.py; docstring overclaim fixed. Real unguarded uses found on R3 and fixed in R4: catcher `out.touch()`, load_driver and burst default opener. Fail-before: failbefore-guard.log (guard test fails on R3: catcher.py:228 out.touch, load_driver.py:137 and burst.py:100 opener.open, http_guard 2 stale reasons).
2. burst/load_driver: http/https only via shared scripts/http_guard.http_only_opener (HTTPHandler+HTTPSHandler only) and check_scheme; address parser; unsplittable URL exit 2. Tests: test_an_address_option_takes_http_or_https_only..., test_a_file_address_that_is_a_pipe_returns_at_once, test_the_shared_opener_has_no_file_handler... failbefore-refusals.log.
3. hubspot_probe --dry-run: shared `http_address(loopback_hosts)` in tools/refusing_args.py (also used by burst, load_driver). Tests: test_hubspot_probe_dry_run_address_is_refused..., changed test_dry_run_refuses_non_loopback (failbefore-changed-a.log).
4. Bounded options: bounded_int / bounded_float (finite) for all listed options, limits in constants.py (LOAD_SEED_MAX, LIVE_TIMEOUT_MIN_SECONDS, PROBE_CALLS_MAX). Test: test_every_formerly_bare_number_option_refuses_a_bad_number_in_one_line (13 options x 8 values), test_no_script_option_takes_a_bare_int_or_float (feed --index and run_real_check --dry-port-base listed with a reason). 26 of the 104 cases fail on R3 (the rest were already bounded there). The false "every script" docstring claim removed.
5. run_live_check names the option: test_the_live_check_names_the_option_not_the_setting (fails on R3).
6. Empty/blank CA file settings refused (smtp_provider, run_real_check imap_settings): test_ca_file_reads.py (6 cases fail on R3).
7. tls_trust non-ASCII only dropped outside BEGIN..END: test_ca_file_reads.py (6 fail on R3).
8. regfile.load_json_file refuses NaN/Infinity/1e999: test_file_reader_refusals.py (9 fail on R3).
9. book_problem refuses over-long name and unreadable file (also control characters, lead addition C): test_book_folder_refusals.py, test_special_output_files.py (changed pin), test_r4_refusals.py (helper exit 4 for db-path and data-dir). Fail on R3.
10. Exact fixed text and exit code for run_real_check config pipe/non-UTF-8: test_run_real_check_config_refusals_have_the_exact_fixed_text (cannot fail on R3, see above).
11. crash_desk prints the file name only: test_crash_desk_prints_the_file_name_only... (fails on R3).
12. burst as plain script: test_burst_runs_as_a_plain_script_from_any_folder (fails on R3).
13. catcher bad host / busy port, fake_model_server and fakes_server busy port: 4 tests (fail on R3). check_invariants/n8n_api echo pins (see above).
EBADF: see above (cannot fail on R3).
Lead A: behaviour test for exit 4 + one line for db-path and data-dir; ran EVERY test file that mentions desk_setting or book_problem (conftest, book_folder_refusals, codeant_hygiene, file_call_guard, lead_step_route, regfile_limits_in_constants, reset_scripts, script_number_limits, script_refusals_feed, special_output_files, wrapper_setting_refusals): all pass.
Lead B: cap via MAX_JSON_BYTES; test_check_invariants_refuses_a_log_over_the_cap_without_reading_it_whole (sparse file; fails on R3).
Lead C: REAL_RESULT_FILE and the run folder of DESK_DB_PATH refuse control characters (has_control_character in tools/pathconfine.py); test_real_result_file_with_a_control_character_... (4 of 5 fail on R3).

## Gates
- ruff check and ruff format --check on all 47 changed .py files: pass (line length 120).
- bandit -ll -r src tools scripts load_tools demo_only: no issues (bandit.log).
- Test runs on the final head (all pass): fin1.log 841 passed 1 skipped (ledger_amounts, load_tools, path_confinement, http_guard, http, script_number_limits, r4_refusals); fin2.log 298 passed 1 skipped (no_terminal_questions, crash_flag_reads, tools_and_fakes_pipes, file_reader_refusals, ca_file_reads, smtp_provider, smtp_outbox, file_call_guard, book_folder_refusals, special_output_files); r4-5.log 443 passed (r4_refusals, special_output_files, hubspot_probe, real_check_dry, cli_refusals); r4-4.log (before the last small fixes: 15 failed, all fixed after, see r4-5/fin) .
- Files NOT run: all other test files (about 87 of 122), e.g. tests for portal, desk server, adapters, schema.
- Earlier runs affA/affB/affA2 were on earlier heads (affA had 3 stale pins, fixed).

## Patches (out/R4; 68 files changed, 5683 insertions, 285 deletions vs frozen tree)
- core-fix-on-frozen-r4.patch (.ps1 hunks CRLF, spliced from the R3 patch: the two .ps1 files are byte-identical in R3 and R4), core-fix-on-frozen-r4-lf.patch, core-fix-r3-to-r4-delta.patch (28 files).
- Method check: the LF generation method reproduced out/R3/core-fix-on-frozen-r3-lf.patch byte for byte.
- Apply tests (git apply --check then real apply; `diff -rq` against tree-R4 excluding __pycache__/.git/.ruff_cache): CRLF patch on `git archive` of frozen2: rc 0, identical; LF patch on a clone of frozen2: rc 0, identical; delta onto a copy of tree-R3: rc 0, identical. (Only difference: an empty ignored `data/` folder in tree-R4.) Not tried: autocrlf clones.
