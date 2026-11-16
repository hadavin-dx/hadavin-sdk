# evidence-f3-r4-rerun (EVIDENCE RUNNER: raw results, no judgement)
Run: 2026-11-16 09:48:34 UTC. Head: 478aa400a (working tree has uncommitted changes, including fill_flows/ files). Ran as uid 0 (root), AWS_* not set by me. No source file edited; mutants and hostile cases ran only on scratch copies under the session scratchpad (shown as <S>).
Python on this machine: /usr/bin/python3.11 /usr/bin/python3.12 /usr/bin/python3.13 - 3.9 and 3.10 NOT available, NOT run. Default python3 = Python 3.13.18. node: v22.23.4. ruff 0.16.9, bandit 1.9.4.

## 1. Unit tests (cd fill_flows; python3.XX -I -m unittest discover -v)
- python3.11: rc=0, Ran 91 tests in 9.785s, OK
- python3.12: rc=0, Ran 91 tests in 10.490s, OK
- python3.13: rc=0, Ran 91 tests in 10.045s, OK
Skipped tests: 0 lines mention skipped (the node test ran: node present).

### raw verbose output, python3.12
```
test_delete_ok (test_fill_flows.Delete.test_delete_ok) ... ok
test_hash_change (test_fill_flows.Delete.test_hash_change) ... ok
test_manifest_has_no_values (test_fill_flows.Delete.test_manifest_has_no_values) ... ok
test_manifest_left_without_folder (test_fill_flows.Delete.test_manifest_left_without_folder) ... ok
test_no_manifest_needs_the_flag (test_fill_flows.Delete.test_no_manifest_needs_the_flag) ... ok
test_no_manifest_refuses_foreign_files (test_fill_flows.Delete.test_no_manifest_refuses_foreign_files) ... ok
test_nothing_there (test_fill_flows.Delete.test_nothing_there) ... ok
test_refuses_extra_file (test_fill_flows.Delete.test_refuses_extra_file) ... ok
test_symlink_in_folder (test_fill_flows.Delete.test_symlink_in_folder) ... ok
test_symlinked_out_dir_and_manifest_names (test_fill_flows.Delete.test_symlinked_out_dir_and_manifest_names) ... ok
test_check_on_empty_folder_fails (test_fill_flows.Hardening.test_check_on_empty_folder_fails) ... ok
test_check_reports_every_one_of_the_six_placeholder_names (test_fill_flows.Hardening.test_check_reports_every_one_of_the_six_placeholder_names) ... ok
test_code_key_carried_down (test_fill_flows.Hardening.test_code_key_carried_down) ... ok
test_delete_no_manifest_refuses_a_symlink_or_folder_in_the_manifest_place (test_fill_flows.Hardening.test_delete_no_manifest_refuses_a_symlink_or_folder_in_the_manifest_place) ... ok
test_delete_of_a_half_filled_folder (test_fill_flows.Hardening.test_delete_of_a_half_filled_folder) ... ok
test_delete_path_swapped_for_a_link_after_opening_leaves_the_decoy_alone (test_fill_flows.Hardening.test_delete_path_swapped_for_a_link_after_opening_leaves_the_decoy_alone) ... ok
test_delete_refuses_a_parent_link_made_by_another_user (test_fill_flows.Hardening.test_delete_refuses_a_parent_link_made_by_another_user) ... ok
test_exit_0_only_when_nothing_is_left (test_fill_flows.Hardening.test_exit_0_only_when_nothing_is_left) ... ok
test_fill_folder_swapped_for_a_link_after_mkdir_writes_nothing_there (test_fill_flows.Hardening.test_fill_folder_swapped_for_a_link_after_mkdir_writes_nothing_there) ... ok
test_fill_into_a_symlink_that_points_into_git_names_the_real_cause (test_fill_flows.Hardening.test_fill_into_a_symlink_that_points_into_git_names_the_real_cause) ... ok
test_fill_names_a_leftover_manifest_plainly (test_fill_flows.Hardening.test_fill_names_a_leftover_manifest_plainly) ... ok
test_hand_made_folder_of_json_files_is_not_deleted_without_manifest (test_fill_flows.Hardening.test_hand_made_folder_of_json_files_is_not_deleted_without_manifest) ... ok
test_lexer_agrees_with_a_real_js_engine (test_fill_flows.Hardening.test_lexer_agrees_with_a_real_js_engine) ... ok
test_manifest_delete_refuses_a_folder_that_is_not_yours (test_fill_flows.Hardening.test_manifest_delete_refuses_a_folder_that_is_not_yours) ... ok
test_modes_that_do_not_hold_on_the_disk_refuse_and_leave_nothing (test_fill_flows.Hardening.test_modes_that_do_not_hold_on_the_disk_refuse_and_leave_nothing) ... ok
test_more_bad_values (test_fill_flows.Hardening.test_more_bad_values) ... ok
test_ms_keys_digits_only (test_fill_flows.Hardening.test_ms_keys_digits_only) ... ok
test_names_from_disk_are_printed_safely (test_fill_flows.Hardening.test_names_from_disk_are_printed_safely) ... ok
test_no_manifest_force_hash_refuses_a_folder_named_like_a_json_file (test_fill_flows.Hardening.test_no_manifest_force_hash_refuses_a_folder_named_like_a_json_file) ... ok
test_no_manifest_needs_the_marker_file (test_fill_flows.Hardening.test_no_manifest_needs_the_marker_file) ... ok
test_no_manifest_refuses_a_fifo_without_hanging (test_fill_flows.Hardening.test_no_manifest_refuses_a_fifo_without_hanging) ... ok
test_no_manifest_refuses_a_marker_for_another_folder_or_format (test_fill_flows.Hardening.test_no_manifest_refuses_a_marker_for_another_folder_or_format) ... ok
test_no_manifest_refuses_a_plain_input_folder (test_fill_flows.Hardening.test_no_manifest_refuses_a_plain_input_folder) ... ok
test_no_manifest_refuses_non_json_and_env_text (test_fill_flows.Hardening.test_no_manifest_refuses_non_json_and_env_text) ... ok
test_no_manifest_refuses_wrong_file_mode_folder_mode_and_owner (test_fill_flows.Hardening.test_no_manifest_refuses_wrong_file_mode_folder_mode_and_owner) ... ok
test_no_manifest_with_no_folder_still_validates_the_manifest (test_fill_flows.Hardening.test_no_manifest_with_no_folder_still_validates_the_manifest) ... ok
test_odd_spellings (test_fill_flows.Hardening.test_odd_spellings) ... ok
test_output_inside_input_refused (test_fill_flows.Hardening.test_output_inside_input_refused) ... ok
test_placeholder_inside_longer_string_counts (test_fill_flows.Hardening.test_placeholder_inside_longer_string_counts) ... ok
test_placeholder_name_inside_a_code_field_is_refused (test_fill_flows.Hardening.test_placeholder_name_inside_a_code_field_is_refused) ... ok
test_platform_check_refuses_plainly (test_fill_flows.Hardening.test_platform_check_refuses_plainly) ... ok
test_slash_outside_a_string_refused (test_fill_flows.Hardening.test_slash_outside_a_string_refused) ... ok
test_symlinked_out_dir_with_no_manifest_and_with_copied_manifest (test_fill_flows.Hardening.test_symlinked_out_dir_with_no_manifest_and_with_copied_manifest) ... ok
test_symlinked_parent_made_by_another_user_is_refused (test_fill_flows.Hardening.test_symlinked_parent_made_by_another_user_is_refused) ... ok
test_symlinked_parent_of_my_own_is_accepted_and_works_end_to_end (test_fill_flows.Hardening.test_symlinked_parent_of_my_own_is_accepted_and_works_end_to_end) ... ok
test_trailing_slash_in_url_warns (test_fill_flows.Hardening.test_trailing_slash_in_url_warns) ... ok
test_two_keys_that_become_one_are_refused (test_fill_flows.Hardening.test_two_keys_that_become_one_are_refused) ... ok
test_values_file_mode_0604_refused (test_fill_flows.Hardening.test_values_file_mode_0604_refused) ... ok
test_values_file_must_be_a_regular_file (test_fill_flows.Hardening.test_values_file_must_be_a_regular_file) ... ok
test_values_file_pipe_is_refused_without_hanging (test_fill_flows.Hardening.test_values_file_pipe_is_refused_without_hanging) ... ok
test_write_cut_in_the_middle_leaves_nothing_and_rerun_works (test_fill_flows.Hardening.test_write_cut_in_the_middle_leaves_nothing_and_rerun_works) ... ok
test_bad_values (test_fill_flows.Negative.test_bad_values) ... ok
test_bom_refused (test_fill_flows.Negative.test_bom_refused) ... ok
test_broken_or_nested_braces_refused (test_fill_flows.Negative.test_broken_or_nested_braces_refused) ... ok
test_comment_in_expression_refused (test_fill_flows.Negative.test_comment_in_expression_refused) ... ok
test_duplicate_key (test_fill_flows.Negative.test_duplicate_key) ... ok
test_dynamic_env_use_refused (test_fill_flows.Negative.test_dynamic_env_use_refused) ... ok
test_empty_value (test_fill_flows.Negative.test_empty_value) ... ok
test_extra_unknown_key_warns_only (test_fill_flows.Negative.test_extra_unknown_key_warns_only) ... ok
test_failed_write_removes_everything_and_manifest_goes_first (test_fill_flows.Negative.test_failed_write_removes_everything_and_manifest_goes_first) ... ok
test_inline_comment_marker_warns (test_fill_flows.Negative.test_inline_comment_marker_warns) ... ok
test_invalid_json_input (test_fill_flows.Negative.test_invalid_json_input) ... ok
test_leftover_token_unknown_name (test_fill_flows.Negative.test_leftover_token_unknown_name) ... ok
test_missing_key (test_fill_flows.Negative.test_missing_key) ... ok
test_other_name_refused_even_with_value (test_fill_flows.Negative.test_other_name_refused_even_with_value) ... ok
test_output_exists (test_fill_flows.Negative.test_output_exists) ... ok
test_output_inside_repo (test_fill_flows.Negative.test_output_inside_repo) ... ok
test_output_under_mnt_refused (test_fill_flows.Negative.test_output_under_mnt_refused) ... ok
test_quote_and_backslash_in_middle_are_escaped (test_fill_flows.Negative.test_quote_and_backslash_in_middle_are_escaped) ... ok
test_symlink_input_refused (test_fill_flows.Negative.test_symlink_input_refused) ... ok
test_token_in_code_fields_refused (test_fill_flows.Negative.test_token_in_code_fields_refused) ... ok
test_token_in_quoted_js_string_refused (test_fill_flows.Negative.test_token_in_quoted_js_string_refused) ... ok
test_token_outside_braces_refused (test_fill_flows.Negative.test_token_outside_braces_refused) ... ok
test_upper_case_json_refused (test_fill_flows.Negative.test_upper_case_json_refused) ... ok
test_values_file_modes_and_places (test_fill_flows.Negative.test_values_file_modes_and_places) ... ok
test_values_file_under_mnt_refused (test_fill_flows.Negative.test_values_file_under_mnt_refused) ... ok
test_already_filled_input_exit_4 (test_fill_flows.Positive.test_already_filled_input_exit_4) ... ok
test_check_bad_json_and_nan (test_fill_flows.Positive.test_check_bad_json_and_nan) ... ok
test_check_mode (test_fill_flows.Positive.test_check_mode) ... ok
test_check_reads_parsed_json_forms (test_fill_flows.Positive.test_check_reads_parsed_json_forms) ... ok
test_film_expressions (test_fill_flows.Positive.test_film_expressions) ... ok
test_idempotent_same_bytes (test_fill_flows.Positive.test_idempotent_same_bytes) ... ok
test_placeholders_filled_when_keys_given (test_fill_flows.Positive.test_placeholders_filled_when_keys_given) ... ok
test_real_and_film (test_fill_flows.Positive.test_real_and_film) ... ok
test_real_expressions (test_fill_flows.Positive.test_real_expressions) ... ok
test_token_in_every_location (test_fill_flows.Positive.test_token_in_every_location) ... ok
test_exit_codes_are_literal (test_fill_flows.Unit.test_exit_codes_are_literal) ... ok
test_property_roundtrip_random_values (test_fill_flows.Unit.test_property_roundtrip_random_values) ... ok
test_token_forms (test_fill_flows.Unit.test_token_forms) ... ok
test_token_refusals_in_process (test_fill_flows.Unit.test_token_refusals_in_process) ... ok
test_values_never_in_messages_in_process (test_fill_flows.Unit.test_values_never_in_messages_in_process) ... ok

----------------------------------------------------------------------
Ran 91 tests in 10.490s

OK

real	0m10.708s
user	0m6.556s
sys	0m1.425s
```

## 2. Lint and security (cd /home/user/hadavin-sdk)
$ ruff check handover/flows-audit/fill_flows -> rc=0
```
All checks passed!
```
$ ruff format --check handover/flows-audit/fill_flows -> rc=0
```
16 files already formatted
```
$ bandit -ll -r handover/flows-audit/fill_flows -> rc=0 (5 Low findings are below the -ll threshold; 0 Medium, 0 High)
```
Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 5
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 5
Files skipped (0):
```
(system ruff/bandit used; uv run was not needed.)

## 3. Mutation check (scratch copies, python3.12 -I -m unittest discover, FF_DEMO_DIR set to the real demo folder read-only)
Mapping: the 14 checks are the mutants A-N of fix-f3-r3.md Round 4 (A,B,C from the survivors; D,E=M1; F,G=M3; H,I,J,K=Nit 7; L=Nit 5; M,N=M2). I wrote each mutant by hand from that description; if the fixer meant different lines for any letter, that letter is my reading.
Result: 14 run, 14 KILLED, 0 SURVIVED. Harness: <S>/mut/run_mutants.py (each mutant is one exact text replacement, asserted to match once).
```
A values-file S_ISREG check off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=2) | by: test_values_file_must_be_a_regular_file, test_values_file_pipe_is_refused_without_hanging
B delete: symlinked-parent check off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_delete_refuses_a_parent_link_made_by_another_user
C check: skip SMTP_CREDENTIAL_ID | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_check_reports_every_one_of_the_six_placeholder_names
D new-file mode/owner fstat check off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_modes_that_do_not_hold_on_the_disk_refuse_and_leave_nothing
E new-folder mode/owner fstat check off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=43) | by: test_already_filled_input_exit_4, test_bad_values, test_bom_refused, test_broken_or_nested_braces_refused, test_check_bad_json_and_nan, test_check_mode +37 more
F marker file required: off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=2) | by: test_hand_made_folder_of_json_files_is_not_deleted_without_manifest, test_no_manifest_needs_the_marker_file
G marker content check off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_no_manifest_refuses_a_marker_for_another_folder_or_format
H manifest-delete folder owner check off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_manifest_delete_refuses_a_folder_that_is_not_yours
I key-collision refusal off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_two_keys_that_become_one_are_refused
J placeholder name in code field refusal off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_placeholder_name_inside_a_code_field_is_refused
K no-manifest, no folder: manifest validation off | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_no_manifest_with_no_folder_still_validates_the_manifest
L printed names not ascii-escaped | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_names_from_disk_are_printed_safely
M delete unlinks by path not dir_fd | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_delete_path_swapped_for_a_link_after_opening_leaves_the_decoy_alone
N folder open follows links (no O_NOFOLLOW) | rc=1 | KILLED | Ran 91 tests | FAILED (failures=1) | by: test_fill_folder_swapped_for_a_link_after_mkdir_writes_nothing_there
```
Note: mutant E (folder mode check off) is killed by 43 tests, i.e. a broad kill, not a targeted one.

## 4. Hostile inputs (scratch tree <S>/host, tool copy + the 4 real v5 flow files; values are made-up; canary string printed 0 times in the logs, checked with grep -c)
Script: <S>/mut/hostile.sh. Each line shows the command then output then rc. Values are never printed by the tool.
```
ls in: 4 json files
### 00 baseline fill (expect rc 3 or 0 depending on placeholders)
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/out0
warning: key MF_CRM_URL in the values file is not used by any node
warning: key MF_STAGE_TIMEOUT_MS in the values file is not used by any node
warning: key MF_STAGE_URL in the values file is not used by any node
NOT READY TO IMPORT: 23 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3

### 00b check baseline
$ python3.12 -I TOOL/fill_flows.py check W/out0
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder FROM_ADDRESS_PLACEHOLDER x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder FROM_ADDRESS_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder HS_CRED_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder INTAKE_ADDRESS_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 23 problem(s)
rc=1

perms:
700 root w/out0
600 root w/out0/mf-form.json
600 root w/out0/mf-hook.json
600 root w/out0/mf-recovery.json
600 root w/out0/mf-sub-crm-mail.json
600 root w/out0.manifest.json
### 01 idempotent: fill same out again
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/out0
refused: output folder or its manifest already exists (delete it first)
rc=1

### 01b fill fresh out1, compare hashes with out0
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/out1
warning: key MF_CRM_URL in the values file is not used by any node
warning: key MF_STAGE_TIMEOUT_MS in the values file is not used by any node
warning: key MF_STAGE_URL in the values file is not used by any node
NOT READY TO IMPORT: 23 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3

identical output hashes: yes
### 01c delete out0
$ python3.12 -I TOOL/fill_flows.py delete --out W/out0
deleted 4 files, the folder and the manifest
rc=0

### 01d delete out0 again
$ python3.12 -I TOOL/fill_flows.py delete --out W/out0
refused: output folder and manifest are both missing; nothing to delete
rc=1

### 01e delete out1 then fill out1 again (round trip)
$ python3.12 -I TOOL/fill_flows.py delete --out W/out1
deleted 4 files, the folder and the manifest
rc=0

### 01f refill out1
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/out1
warning: key MF_CRM_URL in the values file is not used by any node
warning: key MF_STAGE_TIMEOUT_MS in the values file is not used by any node
warning: key MF_STAGE_URL in the values file is not used by any node
NOT READY TO IMPORT: 23 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3

### 01g delete out1
$ python3.12 -I TOOL/fill_flows.py delete --out W/out1
deleted 4 files, the folder and the manifest
rc=0

### 02 values file is a symlink
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o2
refused: values file: cannot open it (missing, a symlink, or not readable)
rc=1

### 03 values file is a FIFO (timeout 10s)
$ timeout 10 python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o3
refused: values file is not a regular file
rc=1

### 04 values file is a directory
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o4
refused: values file is not a regular file
rc=1

### 05 values file world-writable 0666
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o5
refused: values file can be read by other users (run: chmod 600 on it)
rc=1

### 05b values file 0644
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o5b
refused: values file can be read by other users (run: chmod 600 on it)
rc=1

### 05c values file missing
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o5c
refused: values file: cannot open it (missing, a symlink, or not readable)
rc=1

### 06 output is a symlink to existing dir
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/lnk
refused: output folder or its manifest already exists (delete it first)
rc=1

### 06b output is a dangling symlink
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/lnk2
refused: output folder or its manifest already exists (delete it first)
rc=1

### 06c output parent is a symlink of mine (root)
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/parentlink/o6c
warning: key MF_CRM_URL in the values file is not used by any node
warning: key MF_STAGE_TIMEOUT_MS in the values file is not used by any node
warning: key MF_STAGE_URL in the values file is not used by any node
NOT READY TO IMPORT: 23 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3

### 06d delete via symlinked parent of mine
$ python3.12 -I TOOL/fill_flows.py delete --out W/parentlink/o6c
deleted 4 files, the folder and the manifest
rc=0

### 06e output parent is a symlink made by another user (nobody)
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/parentlink/o6e
refused: a folder in the output path is a symlink made by another user
rc=1

### 06f delete with parent link made by another user
$ python3.12 -I TOOL/fill_flows.py delete --out W/parentlink/o6e
refused: a folder in the output path is a symlink made by another user
rc=1

### 07 output inside a git repo
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/repo/o7
refused: output path is inside a git repository (a parent folder has .git)
rc=1

### 07b output via symlink that points into git
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/repolink/o7b
refused: output path is inside a git repository (a parent folder has .git)
rc=1

### 07c output inside the input folder
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out IN/sub
refused: output folder is the input folder or inside it
rc=1

### 07d values file inside git repo
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o7d
refused: values file is inside a git repository (move it out; it holds secrets)
rc=1

### 08 value containing $env
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o8
refused: values file line 1: value of DESK_URL contains '$env'
rc=1

### 08b CRLF line ends
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o8b
refused: values file line 1: value of DESK_URL has a control or line-break character (Windows line ends count)
rc=1

### 08c control char (vertical tab) in value
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o8c
refused: values file line 1: value of DESK_URL has a control or line-break character (Windows line ends count)
rc=1

### 08d literal backslash-n in value (not a newline)
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o8d
refused: mf-recovery.json: cannot fill these names (missing or empty in the values file, or not a DESK_/MF_ name): DESK_ALERT_TO
rc=1

### 08e duplicate key
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o8e
refused: values file line 2: key DESK_URL appears twice
rc=1

### 08f non-UTF-8 bytes
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o8f
refused: values file: cannot read it as UTF-8 text
rc=1

### 09 leftover placeholder (no placeholder keys)
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o9
warning: key MF_CRM_URL in the values file is not used by any node
warning: key MF_STAGE_TIMEOUT_MS in the values file is not used by any node
warning: key MF_STAGE_URL in the values file is not used by any node
NOT READY TO IMPORT: 23 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3

### 09b check on that output
$ python3.12 -I TOOL/fill_flows.py check W/o9
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder FROM_ADDRESS_PLACEHOLDER x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder FROM_ADDRESS_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder HS_CRED_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder INTAKE_ADDRESS_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 23 problem(s)
rc=1

### 09c check --tokens-only
$ python3.12 -I TOOL/fill_flows.py check W/o9 --tokens-only
check: 4 files, 0 problem(s)
rc=0

### 09d delete o9
$ python3.12 -I TOOL/fill_flows.py delete --out W/o9
deleted 4 files, the folder and the manifest
rc=0

### 09e check on the raw input folder
$ python3.12 -I TOOL/fill_flows.py check IN
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: token $env DESK_ALERT_TO
mf-recovery.json: placeholder FROM_ADDRESS_PLACEHOLDER x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: token $env DESK_URL
mf-sub-crm-mail.json: token $env DESK_TIMEOUT_MS
mf-sub-crm-mail.json: placeholder FROM_ADDRESS_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder HS_CRED_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder INTAKE_ADDRESS_PLACEHOLDER x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 26 problem(s)
rc=1

### 10 fill o10
$ python3.12 -I TOOL/fill_flows.py fill --in IN --values <values> --out W/o10
warning: key MF_CRM_URL in the values file is not used by any node
warning: key MF_STAGE_TIMEOUT_MS in the values file is not used by any node
warning: key MF_STAGE_URL in the values file is not used by any node
NOT READY TO IMPORT: 23 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3

### 10b delete when output folder is a symlink
$ python3.12 -I TOOL/fill_flows.py delete --out W/o10
refused: output folder is a symlink or not a folder; nothing deleted
rc=1

### 10c delete --no-manifest without marker
$ python3.12 -I TOOL/fill_flows.py delete --out W/o10 --no-manifest
refused: no manifest, and the folder has no marker file written by this tool (.fill_flows-output); nothing deleted
rc=1

### 10d delete: extra hand-made file placed in folder
$ python3.12 -I TOOL/fill_flows.py delete --out W/o10
refused: .fill_flows-output: content changed since it was written (use --force-hash); nothing deleted
rc=1

### 10e delete, manifest gone, no --no-manifest
$ python3.12 -I TOOL/fill_flows.py delete --out W/o10
refused: manifest is missing; nothing deleted (to remove the folder anyway, use --no-manifest: it removes only the files this tool writes)
rc=1

### 10f delete --no-manifest on folder lacking marker
$ python3.12 -I TOOL/fill_flows.py delete --out W/o10 --no-manifest
refused: no manifest, and the folder has no marker file written by this tool (.fill_flows-output); nothing deleted
rc=1

```
Corrections to the script above: case 08d used a values file without DESK_ALERT_TO, so its refusal is about a missing name, not the backslash; it is redone below. Case 10d's label is wrong: it placed an EMPTY file over the marker file (not an extra file); the refusal is the changed-hash check.
```
### 08d-redo literal backslash-n with all DESK keys
NOT READY TO IMPORT: 23 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
deleted 4 files, the folder and the manifest
rc=0
### 08g real newline inside a value (splits the line)
refused: values file line 2: no '=' (expected KEY=VALUE)
rc=1
### 11 output parent world-writable 0777
NOT READY TO IMPORT: 23 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
700 w/ww/o11
deleted 4 files, the folder and the manifest
rc=0
### 12 /tmp leftovers
h0
h1
lnk
lnk2
o10
parentlink
real
repo
repolink
v.644
v.bin
v.bs
v.bs2
v.crlf
v.dir
v.dup
v.env
v.envtok
v.fifo
v.link
v.nl
v.part
v.vt
v.ww
ww
```
Grep for the canary in all hostile logs: 0

## 5. Not run / not covered
- Python 3.9 and 3.10 (not installed). macOS, WSL, a real /mnt drive, a disk that ignores modes (covered only by the unit test that fakes it).
- Run as root: owner checks against 'another user' were exercised with a symlink chown'd to nobody (06e, 06f); file-owner checks for other users are covered by unit tests only.
- Live n8n import not run.
- Output-folder-is-a FIFO/directory at the manifest place and TOCTOU swaps were not hand-tried; only the unit tests cover them.
- git status after my work: no change to fill_flows source files by me (only this file added).
