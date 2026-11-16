# Evidence r6 (raw output; EVIDENCE RUNNER, no judgement)
Date 2026-11-16 UTC. Run on Python 3.13, system ruff/bandit (not uv run). Nothing committed; real script untouched.

## Failures first
- Steps 1-3: none. All exit codes 0.
- Step 4: 0 of 18 mutants survived (3 named + 15 random). Not covered: the 15 random mutants are one-line operator swaps chosen with seed 20261116 from lines >= 31; most hit error-path lines. Equivalent-mutant check not done.
- Difference from claim: ruff format says '11 files already formatted' (fix-roles-r6.md claimed 10). Only 2 .py files are in the folder; the count includes other files ruff found (not investigated).
- Not run: pytest repo suite, uv run variant, CodeQL/Sonar/CodeRabbit.

## 1. python3 -m unittest -v test_check_grants
```
test_f6a_sql_in_code_node (test_check_grants.Round4.test_f6a_sql_in_code_node) ... ok
test_f6b_mysql_type_node (test_check_grants.Round4.test_f6b_mysql_type_node) ... ok
test_f6c_postgres_tool_node (test_check_grants.Round4.test_f6c_postgres_tool_node) ... ok
test_f6d_sql_text_in_set_node (test_check_grants.Round4.test_f6d_sql_text_in_set_node) ... ok
test_f6e_innocent_node_text_not_flagged (test_check_grants.Round4.test_f6e_innocent_node_text_not_flagged) ... ok
test_i4c_file_without_postgres_node (test_check_grants.Round4.test_i4c_file_without_postgres_node) ... ok
test_s1_no_folder_given (test_check_grants.Round4.test_s1_no_folder_given) ... ok
test_s1_wrong_folder_missing_file (test_check_grants.Round4.test_s1_wrong_folder_missing_file) ... ok
test_s1_wrong_node_count (test_check_grants.Round4.test_s1_wrong_node_count) ... ok
test_s2_expression_query (test_check_grants.Round4.test_s2_expression_query) ... ok
test_s2_missing_operation (test_check_grants.Round4.test_s2_missing_operation) ... ok
test_s2_operation_not_execute_query (test_check_grants.Round4.test_s2_operation_not_execute_query) ... ok
test_s3_correct_credentials_pass (test_check_grants.Round4.test_s3_correct_credentials_pass) ... ok
test_s3_missing_credential (test_check_grants.Round4.test_s3_missing_credential) ... ok
test_s3_old_shared_credential_rejected (test_check_grants.Round4.test_s3_old_shared_credential_rejected) ... ok
test_s3_wrong_credential_for_login (test_check_grants.Round4.test_s3_wrong_credential_for_login) ... ok
test_s4_copy (test_check_grants.Round4.test_s4_copy) ... ok
test_s4_cte_write (test_check_grants.Round4.test_s4_cte_write) ... ok
test_s4_insert_without_column_list (test_check_grants.Round4.test_s4_insert_without_column_list) ... ok
test_s4_returning_star (test_check_grants.Round4.test_s4_returning_star) ... ok
test_s4_select_star (test_check_grants.Round4.test_s4_select_star) ... ok
test_s4_update_from (test_check_grants.Round4.test_s4_update_from) ... ok
test_s5_mixed_case_write (test_check_grants.Round4.test_s5_mixed_case_write) ... ok
test_s5_quoted_name (test_check_grants.Round4.test_s5_quoted_name) ... ok
test_s5_uppercase_column_is_read (test_check_grants.Round4.test_s5_uppercase_column_is_read) ... ok
test_big_flow_file_refused_unread (test_check_grants.Round5.test_big_flow_file_refused_unread) ... ok
test_big_roles_document_refused (test_check_grants.Round5.test_big_roles_document_refused) ... ok
test_deeply_nested_json_clean (test_check_grants.Round5.test_deeply_nested_json_clean) ... ok
test_delete_inside_string_literal_flagged (test_check_grants.Round5.test_delete_inside_string_literal_flagged) ... ok
test_disabled_false_not_flagged (test_check_grants.Round5.test_disabled_false_not_flagged) ... ok
test_disabled_node_with_bad_query_still_read (test_check_grants.Round5.test_disabled_node_with_bad_query_still_read) ... ok
test_disabled_postgres_node_flagged (test_check_grants.Round5.test_disabled_postgres_node_flagged) ... ok
test_disabled_text_value_flagged (test_check_grants.Round5.test_disabled_text_value_flagged) ... ok
test_dollar_quote_flagged (test_check_grants.Round5.test_dollar_quote_flagged) ... ok
test_drop_inside_escaped_literal_flagged (test_check_grants.Round5.test_drop_inside_escaped_literal_flagged) ... ok
test_escaped_quote_keeps_one_literal (test_check_grants.Round5.test_escaped_quote_keeps_one_literal) ... ok
test_flow_file_just_under_limit_read (test_check_grants.Round5.test_flow_file_just_under_limit_read) ... ok
test_harmless_literal_not_flagged (test_check_grants.Round5.test_harmless_literal_not_flagged) ... ok
test_literal_starting_with_escaped_quote_harmless_is_balanced (test_check_grants.Round5.test_literal_starting_with_escaped_quote_harmless_is_balanced) ... ok
test_main_safety_net_unexpected_error_is_one_clean_line (test_check_grants.Round5.test_main_safety_net_unexpected_error_is_one_clean_line)
An unexpected error type inside run() ends as one FAIL line, rc=1, no traceback. ... ok
test_malformed_node_fields_clean (test_check_grants.Round5.test_malformed_node_fields_clean) ... ok
test_malformed_shapes_clean (test_check_grants.Round5.test_malformed_shapes_clean) ... ok
test_non_utf8_file_clean (test_check_grants.Round5.test_non_utf8_file_clean) ... ok
test_plain_notes_on_non_postgres_node_not_flagged (test_check_grants.Round5.test_plain_notes_on_non_postgres_node_not_flagged) ... ok
test_plain_notes_on_postgres_node_not_flagged (test_check_grants.Round5.test_plain_notes_on_postgres_node_not_flagged) ... ok
test_readme_unittest_command_has_no_dash_i (test_check_grants.Round5.test_readme_unittest_command_has_no_dash_i) ... ok
test_real_input_overflowing_the_stack_is_clean (test_check_grants.Round5.test_real_input_overflowing_the_stack_is_clean)
A very deeply nested parameter can overflow the stack inside the check (the exact depth ... ok
test_sql_in_notes_of_non_postgres_node (test_check_grants.Round5.test_sql_in_notes_of_non_postgres_node) ... ok
test_sql_in_postgres_node_notes (test_check_grants.Round5.test_sql_in_postgres_node_notes) ... ok
test_sql_in_postgres_other_parameter (test_check_grants.Round5.test_sql_in_postgres_other_parameter) ... ok
test_unbalanced_quote_flagged (test_check_grants.Round5.test_unbalanced_quote_flagged) ... ok
test_uppercase_table_name_is_the_same_table_by_decision (test_check_grants.Round5.test_uppercase_table_name_is_the_same_table_by_decision)
Decision (round 6): MF_LEADS passes. Postgres folds an unquoted name to lower case, so ... ok
test_baseline_passes (test_check_grants.Tests.test_baseline_passes) ... ok
test_empty_folder (test_check_grants.Tests.test_empty_folder) ... ok
test_f1_new_column_read (test_check_grants.Tests.test_f1_new_column_read) ... ok
test_f3_delete (test_check_grants.Tests.test_f3_delete) ... ok
test_f3b_truncate_and_other_kind (test_check_grants.Tests.test_f3b_truncate_and_other_kind) ... ok
test_f3c_delete_hidden_in_second_statement (test_check_grants.Tests.test_f3c_delete_hidden_in_second_statement) ... ok
test_f4_second_table (test_check_grants.Tests.test_f4_second_table) ... ok
test_f4b_join_second_table (test_check_grants.Tests.test_f4b_join_second_table) ... ok
test_g7_table_level_grant (test_check_grants.Tests.test_g7_table_level_grant) ... ok
test_g7b_extra_column_grant (test_check_grants.Tests.test_g7b_extra_column_grant) ... ok
test_grant_on_second_table (test_check_grants.Tests.test_grant_on_second_table) ... ok
test_grant_removed_in_doc_uncovered (test_check_grants.Tests.test_grant_removed_in_doc_uncovered) ... ok
test_malformed_json_clean_message (test_check_grants.Tests.test_malformed_json_clean_message) ... ok
test_missing_doc (test_check_grants.Tests.test_missing_doc) ... ok
test_missing_role_clean_message (test_check_grants.Tests.test_missing_role_clean_message) ... ok
test_nonexistent_folder (test_check_grants.Tests.test_nonexistent_folder) ... ok
test_real_default_doc_and_both_folders (test_check_grants.Tests.test_real_default_doc_and_both_folders) ... ok
test_script_and_document_cannot_differ (test_check_grants.Tests.test_script_and_document_cannot_differ) ... ok
test_zero_postgres_nodes (test_check_grants.Tests.test_zero_postgres_nodes) ... ok

----------------------------------------------------------------------
Ran 71 tests in 0.927s

OK
rc=0
```

## 2. python3 -I check_grants_cover_queries.py ../../demo/n8n-flows-real-v5 ../../demo/n8n-flows-film-v5
```
n8n-flows-real-v5 mf-form Claim -> mf_door: covered
n8n-flows-real-v5 mf-form Stored -> mf_door: covered
n8n-flows-real-v5 mf-hook Claim -> mf_door: covered
n8n-flows-real-v5 mf-hook Stored -> mf_door: covered
n8n-flows-real-v5 mf-recovery ClaimStuck -> mf_recover: covered
n8n-flows-real-v5 mf-recovery MarkFailed -> mf_recover: covered
n8n-flows-real-v5 mf-recovery AlertClaim -> mf_alert: covered
n8n-flows-real-v5 mf-recovery AlertBackoff -> mf_alert: covered
n8n-flows-real-v5 mf-recovery AlertMark -> mf_alert: covered
n8n-flows-real-v5 mf-sub-crm-mail SetCrmId -> mf_sub: covered
n8n-flows-real-v5 mf-sub-crm-mail MailClaim -> mf_sub: covered
n8n-flows-real-v5 mf-sub-crm-mail MarkDone -> mf_sub: covered
n8n-flows-real-v5 mf-sub-crm-mail MarkUnknownA -> mf_sub: covered
n8n-flows-real-v5 mf-sub-crm-mail MarkUnknownB -> mf_sub: covered
n8n-flows-real-v5: 14 postgres nodes
n8n-flows-film-v5 mf-form Claim -> mf_door: covered
n8n-flows-film-v5 mf-form Stored -> mf_door: covered
n8n-flows-film-v5 mf-hook Claim -> mf_door: covered
n8n-flows-film-v5 mf-hook Stored -> mf_door: covered
n8n-flows-film-v5 mf-recovery ClaimStuck -> mf_recover: covered
n8n-flows-film-v5 mf-recovery MarkFailed -> mf_recover: covered
n8n-flows-film-v5 mf-recovery AlertClaim -> mf_alert: covered
n8n-flows-film-v5 mf-recovery AlertBackoff -> mf_alert: covered
n8n-flows-film-v5 mf-recovery AlertMark -> mf_alert: covered
n8n-flows-film-v5 mf-sub-crm-mail SetCrmId -> mf_sub: covered
n8n-flows-film-v5 mf-sub-crm-mail MailClaim -> mf_sub: covered
n8n-flows-film-v5 mf-sub-crm-mail MarkDone -> mf_sub: covered
n8n-flows-film-v5 mf-sub-crm-mail MarkUnknownA -> mf_sub: covered
n8n-flows-film-v5 mf-sub-crm-mail MarkUnknownB -> mf_sub: covered
n8n-flows-film-v5: 14 postgres nodes
TOTAL PROBLEMS: 0
rc=0
```

## 3. ruff check / ruff format --check / bandit -ll -r / grep noqa|nosec (grep_rc=1 means no hits)
```
All checks passed!
rc=0
11 files already formatted
rc=0
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.18
Run started:2026-11-16 09:58:05.335658+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 1092
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
Files skipped (0):
rc=0
grep_rc=1
```

## 4. Mutants on scratch copy (/tmp/claude-0/ev/scratch/base, one mutation each, python3 -m unittest test_check_grants)
Harness: /tmp/claude-0/ev/scratch/mut.py (seed 20261116). Named mutants: R5-08 except UNEXPECTED->ZeroDivisionError; R5-20 removed |'' from LITERAL; R5-22 notes dropped from foreign_db_access strings().
```
R5-08 KILLED FAILED (failures=1, errors=2)
R5-20 KILLED FAILED (failures=1, errors=1)
R5-22 KILLED FAILED (failures=1, errors=1)
RANDOM1 line 149: 'if not '->'if ' | if not isinstance(raw, list): | KILLED FAILED (failures=63, errors=5)
RANDOM2 line 417: ' or '->' and ' | f"({node.get('disabled')!r}); it is checked as if enabled, remove it or enable it" | KILLED FAILED (errors=1)
RANDOM3 line 242: ' != '->' == ' | params = {k: v for k, v in (node.get("parameters") or {}).items() if k != "query"} | KILLED FAILED (failures=11, errors=1)
RANDOM4 line 145: 'return None'->'return 1' | return None, [f"cannot read flow file ({type(e).__name__}: {e})"] | KILLED FAILED (errors=1)
RANDOM5 line 444: ' == '->' != ' | if cred == OLD_CREDENTIAL: | KILLED FAILED (failures=3, errors=1)
RANDOM6 line 356: ' in '->' not in ' | for p in parts: | KILLED FAILED (errors=86)
RANDOM7 line 371: 'False'->'True' | def run(folders, doc, out=print, require_new_cred=False): | KILLED FAILED (errors=1)
RANDOM8 line 358: ' and '->' or ' | if t and t.group(1) in COLS: | KILLED FAILED (errors=1)
RANDOM9 line 364: ' in '->' not in ' | if t in skip: | KILLED FAILED (failures=52, errors=4)
RANDOM10 line 141: 'return None'->'return 1' | return None, [f"cannot read flow file ({why})"] | KILLED FAILED (errors=1)
RANDOM11 line 455: ' in '->' not in ' | if login not in grants: | KILLED FAILED (errors=86)
RANDOM12 line 147: 'return None'->'return 1' | return None, [f"malformed flow file: top level is {type_name(data)}, expected an object"] | KILLED FAILED (errors=1)
RANDOM13 line 181: 'all('->'any(' | return re.findall(r"[a-z_]+", s) | KILLED FAILED (failures=72, errors=9)
RANDOM14 line 363: ' in '->' not in ' | for t in (t for t in toks(s) if t in COLS): | KILLED FAILED (errors=86)
RANDOM15 line 280: '.strip()'->'' | return [p.strip() for p in s.split(";") if p.strip()] | KILLED FAILED (errors=1)
```
