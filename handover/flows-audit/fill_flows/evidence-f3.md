# Evidence F3 (fill_flows), EVIDENCE RUNNER, raw record, no judgement
Started: Mon Nov 16 09:04:18 UTC 2026 (UTC). Machine: Linux, python3 Python 3.13.18, ruff 0.17.1 at /tmp/core-venv/bin/ruff

## 1 Unit tests: cd fill_flows; timeout 300 python3 -I -m unittest -v  -> exit code 0, 'Ran 27 tests', OK
```
test_delete_ok (test_fill_flows.Delete.test_delete_ok) ... ok
test_hash_change (test_fill_flows.Delete.test_hash_change) ... ok
test_manifest_has_no_values (test_fill_flows.Delete.test_manifest_has_no_values) ... ok
test_no_manifest (test_fill_flows.Delete.test_no_manifest) ... ok
test_refuses_extra_file (test_fill_flows.Delete.test_refuses_extra_file) ... ok
test_symlink_in_folder (test_fill_flows.Delete.test_symlink_in_folder) ... ok
test_symlinked_out_dir_and_manifest_names (test_fill_flows.Delete.test_symlinked_out_dir_and_manifest_names) ... ok
test_bad_values (test_fill_flows.Negative.test_bad_values) ... ok
test_braces_cannot_close_expression (test_fill_flows.Negative.test_braces_cannot_close_expression) ... ok
test_dynamic_env_use_refused (test_fill_flows.Negative.test_dynamic_env_use_refused) ... ok
test_empty_value (test_fill_flows.Negative.test_empty_value) ... ok
test_extra_unknown_key_warns_only (test_fill_flows.Negative.test_extra_unknown_key_warns_only) ... ok
test_invalid_json_input (test_fill_flows.Negative.test_invalid_json_input) ... ok
test_leftover_token_in_added_node (test_fill_flows.Negative.test_leftover_token_in_added_node) ... ok
test_missing_key (test_fill_flows.Negative.test_missing_key) ... ok
test_output_exists (test_fill_flows.Negative.test_output_exists) ... ok
test_output_inside_repo (test_fill_flows.Negative.test_output_inside_repo) ... ok
test_symlink_input_refused (test_fill_flows.Negative.test_symlink_input_refused) ... ok
test_value_with_env_and_duplicate_key (test_fill_flows.Negative.test_value_with_env_and_duplicate_key) ... ok
test_already_filled_input_exit_4 (test_fill_flows.Positive.test_already_filled_input_exit_4) ... ok
test_check_mode (test_fill_flows.Positive.test_check_mode) ... ok
test_expression_forms_are_correct (test_fill_flows.Positive.test_expression_forms_are_correct) ... ok
test_idempotent_same_bytes (test_fill_flows.Positive.test_idempotent_same_bytes) ... ok
test_real_and_film (test_fill_flows.Positive.test_real_and_film) ... ok
test_property_roundtrip_random_values (test_fill_flows.Unit.test_property_roundtrip_random_values) ... ok
test_token_forms (test_fill_flows.Unit.test_token_forms) ... ok
test_values_never_in_messages_in_process (test_fill_flows.Unit.test_values_never_in_messages_in_process) ... ok

----------------------------------------------------------------------
Ran 27 tests in 1.918s

OK
```
(full 27-line verbose list trimmed to last 40 lines; full log /tmp/ff13e/logs/ut1.txt)

## 2 Order independence
Note: unittest -p is a FILE PATTERN, not random order; no pytest-randomly installed. Done instead:
- second full run: rc=0, Ran 27, OK
- each class alone via 'python3 -I -m unittest -k <Class>': Unit rc=0 3 tests OK; Delete rc=0 7 OK; Negative rc=0 12 OK; Positive rc=0 5 OK (3+7+12+5=27)
- all 27 tests in reversed order (classes Unit,Delete,Negative,Positive; tests reversed): rc=0, Ran 27, OK
- Observation: 'python3 -I -m unittest test_fill_flows.Unit' (dotted name with -I) fails with ImportError because -I drops the cwd from sys.path; rc=1. Discovery (no name) and -k work.

## 3 Lint
ruff check fill_flows.py test_fill_flows.py -> rc=0 'All checks passed!'
ruff format --check fill_flows.py test_fill_flows.py -> rc=0 '2 files already formatted'

## 4 End to end (copies in /tmp/ff13e/in-real, in-film; values file mode 0600, made-up values; outputs in /tmp/ff13e/out-*, outside any repo)
Usage: real-v5 uses DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO; film-v5 uses MF_CRM_URL, MF_STAGE_TIMEOUT_MS, MF_STAGE_URL.
| run | rc | stdout/stderr (values never shown) |
|---|---|---|
| fill-real | see below | filled 4 files, 3 names used, 23 placeholder strings still present (filled by a later step) warning: key MF_CRM_URL in the values file is not used by any node warning: key MF_STAGE_TIMEOUT_MS in the values file is not used by any node warning: key MF_STAGE_URL in the values file is not used by any n |
| fill-film | see below | filled 4 files, 3 names used, 19 placeholder strings still present (filled by a later step) warning: key DESK_ALERT_TO in the values file is not used by any node warning: key DESK_TIMEOUT_MS in the values file is not used by any node warning: key DESK_URL in the values file is not used by any node  |
| check-real | see below | mf-form.json: placeholder SUB_WORKFLOW_ID x1 mf-form.json: placeholder PG_CREDENTIAL_ID x2 mf-hook.json: placeholder SUB_WORKFLOW_ID x1 mf-hook.json: placeholder PG_CREDENTIAL_ID x2 mf-recovery.json: placeholder PLACEHOLDER x1 mf-recovery.json: placeholder SUB_WORKFLOW_ID x1 mf-recovery.json: placeh |
| check-film | see below | mf-form.json: placeholder SUB_WORKFLOW_ID x1 mf-form.json: placeholder PG_CREDENTIAL_ID x2 mf-hook.json: placeholder SUB_WORKFLOW_ID x1 mf-hook.json: placeholder PG_CREDENTIAL_ID x2 mf-recovery.json: placeholder SUB_WORKFLOW_ID x1 mf-recovery.json: placeholder PG_CREDENTIAL_ID x5 mf-recovery.json: p |
| check-real-tok | see below | check: 4 files, 0 problem(s)  |
| fill-again | see below | refused: output folder or its manifest already exists (delete it first)  |
| fill-on-filled | see below | nothing to fill: no $env token in the input (already filled, or wrong folder)  |
| missing | see below | filled 4 files, 3 names used, 23 placeholder strings still present (filled by a later step) warning: key MF_STAGE_TIMEOUT_MS in the values file is not used by any node warning: key MF_STAGE_URL in the values file is not used by any node  |
| inrepo | see below | refused: output path is inside a git repository (a parent folder has .git)  |
| missing2 | see below | refused: mf-sub-crm-mail.json: a $env token is left after substitution (DESK_URL)  |
| missing3 | see below | refused: mf-sub-crm-mail.json: a $env token is left after substitution (MF_STAGE_URL)  |
| del-changed | see below | refused: mf-form.json: content changed since it was written (use --force-hash); nothing deleted  |
| del-symlink | see below | refused: folder holds files not in the manifest: extra-link; nothing deleted  |
| del-symlink-file | see below | refused: mf-form.json: symlink or not a regular file; nothing deleted  |
| del-stray | see below | refused: folder holds files not in the manifest: stray.txt; nothing deleted  |
| del-force | see below | deleted 4 files, the folder and the manifest  |
| del-real | see below | deleted 4 files, the folder and the manifest  |
| del-nomanifest | see below | refused: output folder is missing or a symlink  |

Exit codes captured directly (no pipe): fill-real 0; fill-film 0; check-real 1 (placeholders listed, 4 files; 23 placeholder strings); check-film 1; check-real --tokens-only 0; fill again into existing out 1 (refused: output folder or its manifest already exists); fill on an already filled copy 4 (nothing to fill); values file missing MF_CRM_URL while filling REAL flows (key not used by real flows) 0 with warnings only; real flows with DESK_URL missing 1 ("a $env token is left after substitution (DESK_URL)"), output not created; film flows with MF_STAGE_URL missing 1 (names MF_STAGE_URL), output not created; output inside /home/user/hadavin-sdk 1 (refused: inside a git repository), nothing written; delete with changed file 1 (nothing deleted, 4 files and manifest remain); delete with unlisted symlink planted in the output folder 1 ("folder holds files not in the manifest: extra-link"); delete with a listed file replaced by a symlink 1 ("symlink or not a regular file"); delete with an unlisted plain file 1; delete --force-hash on the changed folder 0 (deleted 4 files, the folder, the manifest); normal delete of out-real 0 (4 files, folder, manifest gone; keepme.txt and other siblings untouched); delete again with no folder 1 ("output folder is missing or a symlink").

Python verification (ver.py): every output file parses; nodes in = nodes out and connections JSON equal, for all 4 files in both sets:
```
real: 12/12, 12/12, 10/10, 20/20 nodes, connections equal True; film: same counts, equal True
```
grep -c '$env' over out-real and out-film json: 0 and 0 (also 0 for '$env.(DESK_|MF_)' and '$env[').
Canary placement real: DESK_ALERT_TO only in mf-recovery.json toEmail (as {{ "..." }}); DESK_URL and DESK_TIMEOUT_MS only in mf-sub-crm-mail.json url/timeout (Number("2500" || 10000)). Film: MF_STAGE_URL, MF_STAGE_TIMEOUT_MS, MF_CRM_URL only in mf-sub-crm-mail.json lines 19,25,75. Film input files already contain desk@/intake@example.test addresses (not values from my file).
Permissions: output folder 700, files 600, manifest 600. Manifest has 0 hits for 127.0.0.1 or example.test.
Leak grep over stdout+stderr of ALL runs for each value (full URLs, alerts@example.test, 2500, 15000, 127.0.0.1): 0 hits each.

## 5 Mutation sample (copy in /tmp/ff13e/mut; originals untouched; FF_DEMO_DIR and FF_TEST_BASE set; baseline copy: rc=0, 27 OK)
```
M1 skip leftover scan rc= 1 ['Ran 27 tests in 2.009s', 'FAILED (failures=1)'] ['FAIL: test_dynamic_env_use_refused (test_fill_flows.Negative.test_dynamic_env_use_refused)']
M2 value in error message rc= 0 ['Ran 27 tests in 1.955s', 'OK'] []
M3 ignore missing/empty key rc= 1 ['Ran 27 tests in 1.928s', 'FAILED (failures=3, errors=1)'] ['ERROR: test_token_forms (test_fill_flows.Unit.test_token_forms)', 'FAIL: test_empty_value (test_fill_flows.Negative.test_empty_value)', 'FAIL: test_leftover_token_in_added_node (test_fill_flows.Negative.test_leftover_token_in_added_node)', 'FAIL: test_missing_key (test_fill_flows.Negative.test_missing_key)']
M4 files mode 0644 rc= 1 ['Ran 27 tests in 2.056s', 'FAILED (failures=2)'] ['FAIL: test_manifest_has_no_values (test_fill_flows.Delete.test_manifest_has_no_values)', 'FAIL: test_real_and_film (test_fill_flows.Positive.test_real_and_film)']
M5 value in unused-key warning: tests FAIL rc=1 (test_extra_unknown_key_warns_only, test_real_and_film), 27 run, failures=2
```
(An earlier first attempt without FF_DEMO_DIR gave errors=25 from FileNotFoundError, not valid evidence; discarded.)
M1 skip leftover scan: caught by 1 test. M2 (full values dict appended to the 'cannot fill these names' refusal message): NOT caught, 27 OK, mutant survived. M3 ignore missing/empty: caught (4). M4 file mode 0644: caught (2). M5 caught (2).
