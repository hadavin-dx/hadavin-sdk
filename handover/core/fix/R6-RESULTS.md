# R6 RESULTS (builder: step c; not a review; no verdict)

## Lead with what is NOT done or NOT proven
1. The full suite was NOT run (an independent runner does that). I ran the files that touch changed code: 5 batches, listed below. About 1,000 tests of other files never ran (batch 2/3 selected files by grep for the changed module names).
2. Suppressions: frozen 250 noqa / 121 type: ignore / 12 nosec; R5 287 / 130 / 11; R6 246 / 127 / 11 (grep of *.py, *.sh, *.ps1 lines). So R6 is BELOW frozen for noqa and nosec, and +6 above frozen for type: ignore. Removed: all E402 in scripts/ and tools/ (restructured to inline sys.path.insert calls before the imports), 5 test files, PT011, F401, three type: ignore in test_r5_refusals. NOT removed (about 15 added lines, listed by file:line in the last section) with the reason.
3. start_all.ps1 / reset.ps1 untested: no PowerShell here. Only start_all.sh got the bounded poll test.
4. 20 added lines over 120 columns remain in non-Python files (scripts/*.sh, *.ps1, README, docs). Ruff cannot check them and I did not wrap them (risk of breaking shell quoting without a shell test for each). Python files: ruff E501 clean.
5. Shared exit-code pairs (3 = unreachable = check failed; 1 = stopped = adapters unreachable) are DOCUMENTED and PINNED (docs/limits.md, test_shared_exit_code_pairs_are_pinned), not renumbered.
6. I reverted one change of mine mid-run: burst `--url` loopback-only (not asked; it broke 8 tests and changed behaviour). Burst is as in R5 again.
7. The AST guard cannot see dynamic names (a file call built from a runtime string). Internal `type(e).__name__` uses in src/ (desk log lines) are left: they are not refusal/status lines to a person.
8. test_the_load_driver_ends_with_exit_3...: 31.7 s under load (batch 1), passes; timing cause not changed.

## Findings
A non-ASCII/control key refused in file and env, one check `regfile.secret_text_ok`, before any reserve. B/C smtp context re-checked in send()/_wrap; context + ca_file refused. D n8n key via read_secret_line (fixed texts, exit 3 unreachable), hubspot_probe env token via shared check, imap user control chars refused. E dead cert_store guard deleted; bounded-read test added. F second REPLY_MAX_BYTES renamed SCRIPT_REPLY_MAX_BYTES (4 MiB; kept, not deleted, because workflow lists can exceed 1 MiB) + ast duplicate-name test. G class names and typed text removed from refusal/status lines (n8n_api, lock file, burst, portal_demo, check_schema, run_real_check, run_live_check); guard test test_scripts_print_no_class_names. H catcher over-limit line (handler split, pin updated). I shared bounded body helper (scripts/http_guard.read_request_body) in the 3 fake servers. J streamed read_jsonl, row cap, exit 4. K file-call AST guard: aliases, getattr/__import__ literals, pathlib readers, 81 planted shapes (15 missed by the old guard). L see item 5. #8 start_all.sh bounded poll, exit 3 + one line (test added). #12 weak tests strengthened where I touched them (exact rc + exact text). #13 docs/limits.md + CHANGELOG.md (new file; none existed). M sonar stand-in `read(self, size=-1)`; timing: scrub 1 MB tests use process_time (CPU) not wall; crm_hubspot lag 2.0 s / wait 15.0 s constants.

## Test runs (all under `unshare -n` with loopback up, venv312, ruff 0.17.1)
- ruff check: All checks passed. ruff format --check: all files formatted. bandit -ll: no issue lines (only comment warnings).
- Batch 1 (guard, r6, r5_refusals, load_tools, sonar_p2, reset_scripts): 386 passed (out/R6/batch1.log).
- ALONE: test_crm_hubspot 56 passed 31 s, slowest 3.8 s; test_scrub_n8n_export 254 passed 27 s, slowest 12.7 s (CPU-time based now).
- Batch 2 first half of related files: 7 failed -> all were tests pinning old text/class names or an old handler tuple, updated; re-run 169 passed, 4 skipped. Batch 3 (second half): 19 failed (class names / n8n key texts / burst), updated; re-run of those files plus load_tools + burst_retry: 530 passed, 1 skipped.
- The 26 tests of batch 1 files in the 2nd half after my final edits (test_portal_demo etc.) are in that 530.
- Tests that failed on old code and were changed are all pins of text this round changes on purpose (listed in the logs); no test deleted, none weakened except that old class-name expectations became the fixed words.

## Fail-before (clean copy of tree-R5 + new/changed test files; out/R6/failbefore1.log, failbefore2.log)
Only 1 shim in the old copy: test_r6_refusals imports `secret_text_ok` via getattr (absent in R5). Result: 25 failed + 2 failed + start_all exit-3 test failed on old code (rc 0 "started"). Passed on old code (regression pins, not proofs): test_file_call_guard (the guard lives in the test; R5 sources contain no shape it flags), test_sonar_p2_feed_optional (the fix is in the test stand-in; the old stand-in was the defect), test_secret_read_is_bounded, test_scripts_print_no_class_names, test_shared_exit_code_pairs_are_pinned, most of test_load_tools / r5_refusals / reset_scripts (349 passed).

## Patches (out/R6/), `git apply --check` and real apply, result compared with the tree
core-fix-on-frozen-r6.patch (CRLF kept, applied to frozen export: identical to tree), core-fix-on-frozen-r6-lf.patch (applied to an LF copy without .gitattributes: identical; with eol=crlf git re-converts .ps1), core-fix-r5-to-r6-delta.patch (applied to a copy of tree-R5: identical). Note: R5 patch lines for the empty `data/` folder are not in a git diff.

## Added suppressions still present (not removable now)
S603/S607 subprocess in tests: test_cli_refusals:39,59; test_script_number_limits:248; test_r5_refusals:241; test_no_terminal_questions:107,125; test_reset_scripts:485 (fixed argument lists; removal needs one shared ruled helper in tests/support.py, not done). BLE001 catcher.py:161 and check_invariants.py:811 (a parse failure must still leave a line). S310 burst.py:113 and http_guard.py:88 (+nosec B310; the scheme is checked before). type: ignore in tests: test_tools_and_fakes_pipes:87, test_cli_refusals:338,351, test_ca_file_reads:234, test_script_number_limits:205,232 (deliberate wrong-type arguments to test refusals).

## Clean-up
tmp-R6 removed at the end; no process of mine left (the pytest runs ended). No commit, no push, no network, no spend, no sub-agent.
