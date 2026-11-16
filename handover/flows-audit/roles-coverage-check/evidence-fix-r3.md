# evidence-fix-r3 (raw)

## NEW script
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
Ran 19 tests in 0.838s

OK

## OLD script (SCRIPT=old_check.py; old script ignores --roles-doc, treats args as folders)
test_baseline_passes (test_check_grants.Tests.test_baseline_passes) ... ok
test_empty_folder (test_check_grants.Tests.test_empty_folder) ... FAIL
test_f1_new_column_read (test_check_grants.Tests.test_f1_new_column_read) ... ok
test_f3_delete (test_check_grants.Tests.test_f3_delete) ... FAIL
test_f3b_truncate_and_other_kind (test_check_grants.Tests.test_f3b_truncate_and_other_kind) ... FAIL
test_f3c_delete_hidden_in_second_statement (test_check_grants.Tests.test_f3c_delete_hidden_in_second_statement) ... FAIL
test_f4_second_table (test_check_grants.Tests.test_f4_second_table) ... FAIL
test_f4b_join_second_table (test_check_grants.Tests.test_f4b_join_second_table) ... FAIL
test_g7_table_level_grant (test_check_grants.Tests.test_g7_table_level_grant) ... FAIL
test_g7b_extra_column_grant (test_check_grants.Tests.test_g7b_extra_column_grant) ... FAIL
test_grant_on_second_table (test_check_grants.Tests.test_grant_on_second_table) ... FAIL
test_grant_removed_in_doc_uncovered (test_check_grants.Tests.test_grant_removed_in_doc_uncovered) ... FAIL
test_malformed_json_clean_message (test_check_grants.Tests.test_malformed_json_clean_message) ... FAIL
test_missing_doc (test_check_grants.Tests.test_missing_doc) ... FAIL
test_missing_role_clean_message (test_check_grants.Tests.test_missing_role_clean_message) ... FAIL
test_nonexistent_folder (test_check_grants.Tests.test_nonexistent_folder) ... FAIL
test_real_default_doc_and_both_folders (test_check_grants.Tests.test_real_default_doc_and_both_folders) ... ok
test_script_and_document_cannot_differ (test_check_grants.Tests.test_script_and_document_cannot_differ) ... ok
test_zero_postgres_nodes (test_check_grants.Tests.test_zero_postgres_nodes) ... FAIL
Ran 19 tests in 0.836s
FAILED (failures=15)

## new script, real folders
n8n-flows-film-v5 mf-sub-crm-mail MarkUnknownA -> mf_sub: covered
n8n-flows-film-v5 mf-sub-crm-mail MarkUnknownB -> mf_sub: covered
n8n-flows-film-v5: 14 postgres nodes
TOTAL PROBLEMS: 0
rc=0
