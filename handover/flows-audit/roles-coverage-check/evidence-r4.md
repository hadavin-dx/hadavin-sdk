# Evidence round 4: roles coverage check (EVIDENCE RUNNER, raw output, no judgement)

Run 2026-11-16, folder handover/flows-audit/roles-coverage-check/. Tools: python Python 3.13.18, ruff 0.16.9, bandit 1.9.4. No source file edited, nothing committed. ruff picked up the repo pyproject.toml rules.

## Step 1: unit tests
### 1a. Exact command from the brief: python3 -I -m unittest test_check_grants -v
rc=1. Raw: "ModuleNotFoundError: No module named test_check_grants" (Ran 1 test, FAILED errors=1). Cause: -I drops the current folder from the import path, so -m cannot find the test file. Same failure on the unchanged folder; evidence-rerun.md used it without -I.
### 1b. Same tests without -I: python3 -m unittest test_check_grants -v  (rc=0)
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
Ran 44 tests in 2.699s

OK
```

## Step 2: the check on the real folders (from the checker folder, paths relative)
### 2a. python3 -I check_grants_cover_queries.py ../../demo/n8n-flows-real-v5 ../../demo/n8n-flows-film-v5   -> rc=0
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
```
### 2b. same plus --require-new-credentials (placed before the folders)  -> rc=1, 28 FAIL lines (14 per folder), TOTAL PROBLEMS: 28
```
FAIL n8n-flows-real-v5 mf-form Claim: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-form Claim -> mf_door: covered
FAIL n8n-flows-real-v5 mf-form Stored: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-form Stored -> mf_door: covered
FAIL n8n-flows-real-v5 mf-hook Claim: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-hook Claim -> mf_door: covered
FAIL n8n-flows-real-v5 mf-hook Stored: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-hook Stored -> mf_door: covered
FAIL n8n-flows-real-v5 mf-recovery ClaimStuck: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-recovery ClaimStuck -> mf_recover: covered
FAIL n8n-flows-real-v5 mf-recovery MarkFailed: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-recovery MarkFailed -> mf_recover: covered
FAIL n8n-flows-real-v5 mf-recovery AlertClaim: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-recovery AlertClaim -> mf_alert: covered
FAIL n8n-flows-real-v5 mf-recovery AlertBackoff: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-recovery AlertBackoff -> mf_alert: covered
FAIL n8n-flows-real-v5 mf-recovery AlertMark: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-recovery AlertMark -> mf_alert: covered
FAIL n8n-flows-real-v5 mf-sub-crm-mail SetCrmId: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-sub-crm-mail SetCrmId -> mf_sub: covered
FAIL n8n-flows-real-v5 mf-sub-crm-mail MailClaim: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-sub-crm-mail MailClaim -> mf_sub: covered
FAIL n8n-flows-real-v5 mf-sub-crm-mail MarkDone: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-sub-crm-mail MarkDone -> mf_sub: covered
FAIL n8n-flows-real-v5 mf-sub-crm-mail MarkUnknownA: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-sub-crm-mail MarkUnknownA -> mf_sub: covered
FAIL n8n-flows-real-v5 mf-sub-crm-mail MarkUnknownB: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-real-v5 mf-sub-crm-mail MarkUnknownB -> mf_sub: covered
n8n-flows-real-v5: 14 postgres nodes
FAIL n8n-flows-film-v5 mf-form Claim: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-form Claim -> mf_door: covered
FAIL n8n-flows-film-v5 mf-form Stored: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-form Stored -> mf_door: covered
FAIL n8n-flows-film-v5 mf-hook Claim: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-hook Claim -> mf_door: covered
FAIL n8n-flows-film-v5 mf-hook Stored: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-hook Stored -> mf_door: covered
FAIL n8n-flows-film-v5 mf-recovery ClaimStuck: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-recovery ClaimStuck -> mf_recover: covered
FAIL n8n-flows-film-v5 mf-recovery MarkFailed: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-recovery MarkFailed -> mf_recover: covered
FAIL n8n-flows-film-v5 mf-recovery AlertClaim: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-recovery AlertClaim -> mf_alert: covered
FAIL n8n-flows-film-v5 mf-recovery AlertBackoff: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-recovery AlertBackoff -> mf_alert: covered
FAIL n8n-flows-film-v5 mf-recovery AlertMark: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-recovery AlertMark -> mf_alert: covered
FAIL n8n-flows-film-v5 mf-sub-crm-mail SetCrmId: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-sub-crm-mail SetCrmId -> mf_sub: covered
FAIL n8n-flows-film-v5 mf-sub-crm-mail MailClaim: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-sub-crm-mail MailClaim -> mf_sub: covered
FAIL n8n-flows-film-v5 mf-sub-crm-mail MarkDone: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-sub-crm-mail MarkDone -> mf_sub: covered
FAIL n8n-flows-film-v5 mf-sub-crm-mail MarkUnknownA: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-sub-crm-mail MarkUnknownA -> mf_sub: covered
FAIL n8n-flows-film-v5 mf-sub-crm-mail MarkUnknownB: still uses the old shared credential 'n8n-publish-pg'
n8n-flows-film-v5 mf-sub-crm-mail MarkUnknownB -> mf_sub: covered
n8n-flows-film-v5: 14 postgres nodes
TOTAL PROBLEMS: 28
```

## Step 3: lint
### ruff check .  -> rc=1, 21 errors (16 auto-fixable); concise list:
```
check_grants_cover_queries.py:25:1: I001 [*] Import block is un-sorted or un-formatted
check_grants_cover_queries.py:31:8: SIM905 [*] Consider using a list literal instead of `str.split`
check_grants_cover_queries.py:51:5: FURB167 [*] Use of regular expression alias `re.I`
check_grants_cover_queries.py:51:12: FURB167 [*] Use of regular expression alias `re.S`
check_grants_cover_queries.py:66:51: FURB167 [*] Use of regular expression alias `re.S`
check_grants_cover_queries.py:66:58: FURB167 [*] Use of regular expression alias `re.M`
check_grants_cover_queries.py:71:31: FURB167 [*] Use of regular expression alias `re.I`
check_grants_cover_queries.py:118:89: FURB167 [*] Use of regular expression alias `re.M`
check_grants_cover_queries.py:137:76: FURB167 [*] Use of regular expression alias `re.I`
check_grants_cover_queries.py:138:100: FURB167 [*] Use of regular expression alias `re.I`
check_grants_cover_queries.py:139:61: FURB167 [*] Use of regular expression alias `re.I`
check_grants_cover_queries.py:175:60: FURB167 [*] Use of regular expression alias `re.I`
check_grants_cover_queries.py:181:84: FURB167 [*] Use of regular expression alias `re.I`
check_grants_cover_queries.py:181:91: FURB167 [*] Use of regular expression alias `re.S`
check_grants_cover_queries.py:189:50: FURB167 [*] Use of regular expression alias `re.I`
check_grants_cover_queries.py:229:35: SIM115 Use a context manager for opening files
test_check_grants.py:3:1: I001 [*] Import block is un-sorted or un-formatted
test_check_grants.py:12:9: S603 `subprocess` call: check for execution of untrusted input
test_check_grants.py:12:9: PLW1510 `subprocess.run` without explicit `check` argument
test_check_grants.py:84:65: S608 Possible SQL injection vector through string-based query construction
test_check_grants.py:250:12: RUF012 Mutable default value for class attribute
Found 21 errors.
[*] 16 fixable with the `--fix` option.
```
### ruff format --check .  -> rc=1
```
unformatted: File would be reformatted
unformatted: File would be reformatted
2 files would be reformatted, 5 files already formatted
```
### bandit -ll -r .  -> rc=1 (one Medium finding; the Low ones are hidden by -ll)
```
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through string-based query construction.
   Severity: Medium   Confidence: Low
   CWE: CWE-89 (https://cwe.mitre.org/data/definitions/89.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
   Location: ./test_check_grants.py:84:68
83	    def test_f3c_delete_hidden_in_second_statement(self):
84	        self.set_query("mf-sub-crm-mail", "MarkDone", lambda q: q + " DELETE FROM mf_leads;")
Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 2
		Medium: 1
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 2
Files skipped (0):
```

## Step 4a: mutation run on a scratch copy
Scratch copy: $SCRATCH/mut/{flows-audit/roles-coverage-check, flows-audit/ROLES-PROPOSAL.md, demo/n8n-flows-real-v5, demo/n8n-flows-film-v5} (same relative layout so the tests find the document and flows). Script: mutate.py (in the scratchpad). For each mutant one line of the checker is replaced (assert: the old text occurs exactly once), then `python3 -m unittest test_check_grants` runs in the copy. The real folder was never touched.
```
MUTANT 'database-word node types': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_f6b_mysql_type_node (test_check_grants.Round4.test_f6b_mysql_type_node)', 'FAIL: test_f6c_postgres_tool_node (test_check_grants.Round4.test_f6c_postgres_tool_node)']
MUTANT 'SQL text in non-Postgres nodes': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_f6a_sql_in_code_node (test_check_grants.Round4.test_f6a_sql_in_code_node)', 'FAIL: test_f6d_sql_text_in_set_node (test_check_grants.Round4.test_f6d_sql_text_in_set_node)']
MUTANT 'at-least-one-Postgres-node per file': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_i4c_file_without_postgres_node (test_check_grants.Round4.test_i4c_file_without_postgres_node)']
MUTANT '4 flow files expected': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s1_wrong_folder_missing_file (test_check_grants.Round4.test_s1_wrong_folder_missing_file)']
MUTANT '14 nodes expected': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s1_wrong_node_count (test_check_grants.Round4.test_s1_wrong_node_count)']
MUTANT 'no-folder-given': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s1_no_folder_given (test_check_grants.Round4.test_s1_no_folder_given)']
MUTANT 'non-executeQuery operation': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_s2_missing_operation (test_check_grants.Round4.test_s2_missing_operation)', 'FAIL: test_s2_operation_not_execute_query (test_check_grants.Round4.test_s2_operation_not_execute_query)']
MUTANT "'=' query": rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s2_expression_query (test_check_grants.Round4.test_s2_expression_query)']
MUTANT 'SELECT *': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_s4_returning_star (test_check_grants.Round4.test_s4_returning_star)', 'FAIL: test_s4_select_star (test_check_grants.Round4.test_s4_select_star)']
MUTANT 'INSERT without columns': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s4_insert_without_column_list (test_check_grants.Round4.test_s4_insert_without_column_list)']
MUTANT 'UPDATE...FROM': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s4_update_from (test_check_grants.Round4.test_s4_update_from)']
MUTANT 'WITH': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s4_cte_write (test_check_grants.Round4.test_s4_cte_write)']
MUTANT 'quoted names': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s5_quoted_name (test_check_grants.Round4.test_s5_quoted_name)']
MUTANT 'credential missing check': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s3_missing_credential (test_check_grants.Round4.test_s3_missing_credential)']
MUTANT 'new-credential check (whole branch)': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_s3_old_shared_credential_rejected (test_check_grants.Round4.test_s3_old_shared_credential_rejected)', 'FAIL: test_s3_wrong_credential_for_login (test_check_grants.Round4.test_s3_wrong_credential_for_login)']
MUTANT 'old shared credential rejected': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s3_old_shared_credential_rejected (test_check_grants.Round4.test_s3_old_shared_credential_rejected)']
MUTANT 'credential equals document name': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s3_wrong_credential_for_login (test_check_grants.Round4.test_s3_wrong_credential_for_login)']
RESTORED copy rc 0 OK
(case-insensitive mutants, re-run after the first, too broad, version broke 14 unrelated tests:)
