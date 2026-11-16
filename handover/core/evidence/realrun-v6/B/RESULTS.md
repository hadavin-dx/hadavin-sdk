# RUNNER B results (10:0x UTC 2026-11-13). Heads: all trees at 61ded9e (+patches in M/A1)

Variants: patched = tree-M (main+patch1+patch2, same as A1); before = tree-B (clean main src, new/changed test files + patched conftest copied in); oldconftest = tree-B with ORIGINAL conftest (7 existing files only); precheck = copy of tree-B plus scripts/precheck.py and scripts/terminal_guard.py only (the demo session's own fail-before set-up, labelled extra).
All runs: unshare -n + lo up (run1.sh), TMPDIR private, PYTHONPATH=tree/src, package path printed under the tree. No hang in any run. No y/host typed.

| run | file | result | wall |
|---|---|---|---|
| patched | test_clock_steps | 29 passed in 99.63s (0:01:39) | rc=0 wall=100s |
| patched | test_core_key_readers | 12 passed in 4.01s | rc=0 wall=4s |
| patched | test_crm_hubspot | 56 passed in 28.72s | rc=0 wall=29s |
| patched | test_desk_address_required | 16 passed in 0.76s | rc=0 wall=1s |
| patched | test_env_numbers | 354 passed in 5.53s | rc=0 wall=6s |
| patched | test_ledger_amounts | 104 passed in 0.68s | rc=0 wall=1s |
| patched | test_live_claude | 48 passed in 16.58s | rc=0 wall=17s |
| patched | test_path_confinement | 227 passed, 1 skipped in 2.40s | rc=0 wall=3s |
| patched | test_real_check_dry | 71 passed in 200.02s (0:03:20) | rc=0 wall=200s |
| patched | test_real_run_v6 | 74 passed in 0.88s | rc=0 wall=2s |
| patched | test_start_prompt_hardening | 129 passed in 1.47s | rc=0 wall=2s |
| patched | test_take_script_refusals | 143 passed in 126.35s (0:02:06) | rc=0 wall=127s |
| before | test_clock_steps | 2 failed, 27 passed in 0.63s | rc=1 wall=1s |
| before | test_core_key_readers | 7 failed, 5 passed in 1.89s | rc=1 wall=3s |
| before | test_crm_hubspot | 56 passed in 28.65s | rc=0 wall=29s |
| before | test_desk_address_required | 13 failed, 3 passed in 0.73s | rc=1 wall=2s |
| before | test_env_numbers | 354 passed in 5.02s | rc=0 wall=6s |
| before | test_ledger_amounts | 2 failed, 101 passed, 1 error in 0.82s | rc=1 wall=1s |
| before | test_live_claude | 3 failed, 45 passed in 15.98s | rc=1 wall=16s |
| before | test_path_confinement | 1 skipped, 227 errors in 1.81s | rc=1 wall=3s |
| before | test_real_check_dry | 71 errors in 0.70s | rc=1 wall=1s |
| before | test_real_run_v6 | 1 error in 0.22s | rc=2 wall=0s |
| before | test_start_prompt_hardening | 1 error in 0.26s | rc=2 wall=1s |
| before | test_take_script_refusals | 143 errors in 1.17s | rc=1 wall=1s |
| oldconftest | test_clock_steps | 27 passed, 2 errors in 0.63s | rc=1 wall=1s |
| oldconftest | test_crm_hubspot | 56 passed in 28.55s | rc=0 wall=29s |
| oldconftest | test_env_numbers | 354 passed in 5.51s | rc=0 wall=6s |
| oldconftest | test_ledger_amounts | 2 failed, 101 passed, 1 error in 0.75s | rc=1 wall=1s |
| oldconftest | test_live_claude | 3 failed, 45 passed in 16.44s | rc=1 wall=17s |
| oldconftest | test_path_confinement | 1 skipped, 227 errors in 0.35s | rc=1 wall=1s |
| oldconftest | test_real_check_dry | 71 errors in 0.17s | rc=1 wall=0s |
| precheck | test_clock_steps | 2 failed, 27 passed in 0.66s | rc=1 wall=1s |
| precheck | test_core_key_readers | 7 failed, 5 passed in 2.06s | rc=1 wall=3s |
| precheck | test_crm_hubspot | 56 passed in 28.08s | rc=0 wall=28s |
| precheck | test_desk_address_required | 13 failed, 3 passed in 0.65s | rc=1 wall=2s |
| precheck | test_env_numbers | 354 passed in 5.51s | rc=0 wall=6s |
| precheck | test_ledger_amounts | 2 failed, 102 passed in 0.93s | rc=1 wall=2s |
| precheck | test_live_claude | 3 failed, 45 passed in 16.22s | rc=1 wall=16s |
| precheck | test_path_confinement | 1 failed, 226 passed, 1 skipped in 2.05s | rc=1 wall=3s |
| precheck | test_real_check_dry | 5 failed, 66 passed in 2.49s | rc=1 wall=3s |
| precheck | test_real_run_v6 | 70 failed, 4 passed, 10 warnings in 16.76s | rc=1 wall=17s |
| precheck | test_start_prompt_hardening | 52 failed, 77 passed in 2.20s | rc=1 wall=3s |
| precheck | test_take_script_refusals | 69 failed, 74 passed in 107.15s (0:01:47) | rc=1 wall=107s |

## Fails-before per new/changed test function
Full per-function table (patched / before / precheck / oldconftest, with counts of parametrized cases): per-test.txt. Logs: <variant>-<file>.log and .xml. Function = new or changed against 61ded9e (ast compare).
- before (strict, unpatched src): test_real_run_v6.py and test_start_prompt_hardening.py do not collect (ModuleNotFoundError: precheck / terminal_guard, the patch's new scripts); test_take_script_refusals, test_path_confinement, test_real_check_dry = every test ERRORS at setup (conftest fixture imports terminal_guard). These count as failing but for a missing-module reason, not for behaviour. So the "precheck" variant (add scripts/precheck.py + terminal_guard.py only, as the demo session did) is the informative one.
- precheck variant new/changed functions that PASS on old code (45 lines, passes-on-old.txt). Deliberate pins named by the demo notes: test_hubspot_accept_and_refuse_are_identical_to_the_old_rule_on_1512_key_files, test_smtp_..._1512_key_files (pass: confirmed). Others passing on old code: test_no_message_holds_the_key_text_the_file_name_or_the_folder (3), test_hubspot_from_env_accepts_the_vendors_own_address..., test_live_settings_from_env_accept_the_providers_own_address..., test_the_address_is_only_read_when_the_live_model_is_on, the 3 precheck unit tests, test_a_fresh_result_path_still_reaches_the_question, real_check assume_yes/dry-fakes/real-never-assume-yes, 7 of 9 cases of test_only_the_destination_host_starts..., stdin/terminal helper tests (6), the guard/scan sample tests (guard finds 34, no cry wolf 10, shell guard 14+4, no_shell_script_asks_a_question), test_the_live_key_file_is_not_looked_at_without_the_live_flag, tempdir/keep-scan tests (7, incl. 64-sample scan), test_a_new_live_ledger_*, test_the_ledger_read_takes_no_lock..., plus changed existing tests in crm_hubspot (3), ledger_amounts (junk numbers 8, timeouts 5, worst-case figure), live_claude (2), path_confinement (1), real_check_dry (3). These are the tests that cannot fail-before unless a missing import is counted; whether each is a deliberate "nothing else moved" pin I did not judge (not asked).
- Comparison with the demo session evidence: key readers 7 failed / 5 passed = same. desk-address: I get 13 failed / 3 passed = same as evidence-q4h-da-fail-before.txt (13/3); src-v6/README.md says 12 failed / 4 passed, that line differs from its own evidence file. Scripts: test_real_run_v6 70 failed / 4 passed in the precheck variant = the "70 failed cases" of the demo evidence; I did not count their "16 distinct tests" (my table shows 16 of 20 functions fail in that file, but the same 70 cases are spread over more files: take_script 69 failed, start_prompt 52 failed, real_check_dry 5, path_confinement 1, ledger 2, clock_steps 2, live_claude 3 also fail there).
- Not all failures in the strict/precheck variants of existing files are new tests: test_clock_steps (2 failed), live_claude (3), ledger_amounts (2) are the changed tests failing on old src, as expected.
- Patched tree-M: every file passes (counts in the table; 1 skip in path_confinement, which is skipped on the old tree too). Sum of patched passed = 1263 (29+12+56+16+354+104+48+227+71+74+129+143 = 1263), 1 skipped, 0 failed.

## Mutation sets: NOT RUN
The driver and mutant definitions are not on this machine. evidence-q4h-mutants.txt lists only names and the first-pass result (start-prompt M1-M23, R1-R20, S1-S12, K1-K15, C1-C9, N1-N20); NOTES-v6.md and README.md name no driver. The files it cites (harness mut.py "scratchpad", b12-harness/muts1.json) are not in src-v6/, src-v6/drivers/ (only lo_up, sitecustomize, make_synthetic_config, pty_ans, run-dry-checks.sh, results.tsv), RR/drivers (empty), tree-A1/tools (hygiene.py, pathconfine.py only) or anywhere on disk (find for mut.py and muts*.json: nothing). I did not reconstruct the mutants from their names (would be invented). tree-M was never rewritten: git status there is the same 29 patched entries as before. Next step: ask the demo session for mut.py + muts1.json + the other mutant JSON/diffs.
Recorded from their evidence only (not re-run by me): see evidence-q4h-mutants.txt for the per-mutant table; first-pass survivors C9 (equivalent), N12, N14, N20, K6, K10, S2.

## Not run / other
Not run: any other test file (only the 12 files above; the other ~60 test files and the full suite), mutation sets, Windows, run-dry-checks.sh. tests/keep_scan.py and keep_scan_cases.txt are helpers, exercised through test_take_script_refusals. tests/conftest.py is covered via every run.
Side effects: tree-B now holds the copied test files (tests/conftest.py restored to the original afterwards; the others remain; the patched conftest copy is saved as conftest-patched-copy.py). tree-B2 scratch copy removed.
Commands: out/B/run1.sh (unshare -n python lo_up-q4g.py python -m pytest -q -p no:cacheprovider -rA --junitxml ...), batch.sh (xargs -P 2), analyze.py.
