# Evidence round 5: roles coverage check (EVIDENCE RUNNER, raw output, no judgement)

Run 2026-11-16 on the current head (see `git rev-parse --short HEAD` at the end). Tools: python3 3.13, ruff 0.16.9 (system), bandit 1.9.4 (system). `uv run` variant NOT run (system tools used). No source file edited, nothing committed. Scratch copy for mutants and hostile files: `$SCRATCH/r5/mut/` (same relative layout; a `diff -r` against the real folder printed identical before the runs). Scripts (outside the repo): `$SCRATCH/r5/mutate5.py`, `$SCRATCH/r5/hostile5.py` (hostile5 = earlier hostile.py of round 4, plus 10 new cases N01-N10, plus traceback detection in stdout as well as stderr). SCRATCH=/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad.

## Surprises first
- Mutants that SURVIVED (tests did not fail): R5-08 (main() safety net `except UNEXPECTED` replaced), R5-20 (string literal `''` escape handling removed), R5-22 (extra: notes of non-Postgres nodes no longer scanned), and the old poor round-4 mutant 'toks() on non-lowered text' (same as in evidence-r4).
- Note on the count: the brief says 20 Round5 mutants; I built 22 (20 for the 8 named checks plus README pin R5-21 and one extra R5-22). Count of Round5 mutants R5-01..R5-21: 19 killed, 2 survived (R5-08, R5-20); with extra R5-22: 19 killed, 3 survived of 22.
- No traceback in any of the 34 hostile runs (0 lines "TRACEBACK").
- H04 (uppercase table name MF_LEADS in a Postgres query) still rc=0, no FAIL line (same as round 4).

## Step 1: unit tests, from the folder, no -I
Command: `cd handover/flows-audit/roles-coverage-check && python3 -m unittest -v test_check_grants` -> rc=0, "Ran 64 tests in 0.736s", "OK". (Per-test lines are in the log; summary below.)
```

----------------------------------------------------------------------
Ran 64 tests in 0.736s

OK
```
Per-test status counts:
```
64
0
```

## Step 2: the check on the real folders
Command: `cd handover/flows-audit/roles-coverage-check && python3 -I check_grants_cover_queries.py ../../demo/n8n-flows-real-v5 ../../demo/n8n-flows-film-v5` -> rc=0
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

## Step 3: lint, from /home/user/hadavin-sdk (folder = handover/flows-audit/roles-coverage-check)
- `ruff check <folder>` -> rc=0: `All checks passed!`
- `ruff format --check <folder>` -> rc=0: `9 files already formatted`
- `bandit -ll -r <folder>` -> rc=0: "No issues identified", Low 0 / Medium 0 / High 0 (both severity and confidence tables).
- `grep -rnE 'noqa|nosec' <folder>` (ignoring __pycache__): exactly 1 hit, none in a .py file; it is the sentence in fix-roles-r5.md line 14 ("No `noqa`, no suppressions.").  No noqa or nosec comment in any source or test file.
- `uv run --all-extras --group test ...` variant: not run.

## Step 4a: Round 5 mutants (scratch copy; one replacement each; then `python3 -m unittest test_check_grants` in the copy)
Anchor text had to occur exactly once; all did (no "ANCHOR NOT FOUND").
```
MUTANT 'R5-01 top level not object check': rc=1 KILLED | FAILED (failures=2, errors=3) | ['ERROR: test_malformed_shapes_clean', 'ERROR: test_malformed_shapes_clean', 'ERROR: test_malformed_shapes_clean', 'FAIL: test_malformed_shapes_clean']
MUTANT 'R5-02 nodes not list check': rc=1 KILLED | FAILED (failures=5) | ['FAIL: test_malformed_shapes_clean', 'FAIL: test_malformed_shapes_clean', 'FAIL: test_malformed_shapes_clean', 'FAIL: test_malformed_shapes_clean']
MUTANT 'R5-03 node not object check': rc=1 KILLED | FAILED (failures=3) | ['FAIL: test_malformed_shapes_clean', 'FAIL: test_malformed_shapes_clean', 'FAIL: test_malformed_shapes_clean']
MUTANT 'R5-04 name/type must be text': rc=1 KILLED | FAILED (failures=1, errors=4) | ['ERROR: test_malformed_node_fields_clean', 'ERROR: test_malformed_node_fields_clean', 'ERROR: test_malformed_node_fields_clean', 'ERROR: test_malformed_node_fields_
MUTANT 'R5-05 parameters/credentials must be object': rc=1 KILLED | FAILED (failures=3) | ['FAIL: test_malformed_node_fields_clean', 'FAIL: test_malformed_node_fields_clean', 'FAIL: test_malformed_node_fields_clean']
MUTANT 'R5-06 credentials.postgres must be object': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_malformed_node_fields_clean']
MUTANT 'R5-07 RecursionError caught in json load': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_deeply_nested_json_clean']
MUTANT 'R5-08 main safety net removed': rc=0 SURVIVED | OK | []
MUTANT 'R5-09 UnicodeDecodeError (ValueError) not caught in read': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_non_utf8_file_clean']
MUTANT 'R5-10 stray SQL scan in Postgres node off': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_sql_in_postgres_node_notes', 'FAIL: test_sql_in_postgres_other_parameter']
MUTANT 'R5-11 stray scan ignores notes': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_sql_in_postgres_node_notes']
MUTANT 'R5-12 stray scan ignores other parameters': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_sql_in_postgres_other_parameter']
MUTANT 'R5-13 disabled flag off': rc=1 KILLED | FAILED (failures=3) | ['FAIL: test_disabled_node_with_bad_query_still_read', 'FAIL: test_disabled_postgres_node_flagged', 'FAIL: test_disabled_text_value_flagged']
MUTANT 'R5-14 disabled flag only for boolean True': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_disabled_text_value_flagged']
MUTANT 'R5-15 size limit check off': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_big_flow_file_refused_unread', 'FAIL: test_big_roles_document_refused']
MUTANT 'R5-16 size limit raised to 50 MB': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_big_flow_file_refused_unread', 'FAIL: test_big_roles_document_refused']
MUTANT 'R5-17 forbidden keyword in string literal off': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_delete_inside_string_literal_flagged', 'FAIL: test_drop_inside_escaped_literal_flagged']
MUTANT 'R5-18 dollar-quote flag off': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_dollar_quote_flagged']
MUTANT 'R5-19 unbalanced quote flag off': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_unbalanced_quote_flagged']
MUTANT "R5-20 literal '' escape handling removed": rc=0 SURVIVED | OK | []
MUTANT 'R5-21 README command pin (README mutated: -I added)': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_readme_unittest_command_has_no_dash_i']
MUTANT 'R5-22 foreign-node scan ignores notes (extra)': rc=0 SURVIVED | OK | []
RESTORED copy rc 0 OK
```
Killed 19 of 21 (R5-01..R5-21); R5-22 (extra) survived. Survivors: R5-08, R5-20, R5-22.

## Step 4b: the 19 earlier round-4 mutants (17 plus the 2 case-insensitive ones) re-run on the current code (same anchors as evidence-r4, adapted where the code moved)
```
MUTANT 'database-word node types': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_f6b_mysql_type_node', 'FAIL: test_f6c_postgres_tool_node']
MUTANT 'SQL text in non-Postgres nodes': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_f6a_sql_in_code_node', 'FAIL: test_f6d_sql_text_in_set_node']
MUTANT 'at-least-one-Postgres-node per file': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_i4c_file_without_postgres_node']
MUTANT '4 flow files expected': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s1_wrong_folder_missing_file']
MUTANT '14 nodes expected': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s1_wrong_node_count']
MUTANT 'no-folder-given': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s1_no_folder_given']
MUTANT 'non-executeQuery operation': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_s2_missing_operation', 'FAIL: test_s2_operation_not_execute_query']
MUTANT "'=' query": rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s2_expression_query']
MUTANT 'SELECT *': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_s4_returning_star', 'FAIL: test_s4_select_star']
MUTANT 'INSERT without columns': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s4_insert_without_column_list']
MUTANT 'UPDATE...FROM': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s4_update_from']
MUTANT 'WITH': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s4_cte_write']
MUTANT 'case-insensitive columns: column scan on non-lowered text only': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_s5_mixed_case_write', 'FAIL: test_s5_uppercase_column_is_read']
MUTANT 'case-insensitive columns: toks() on non-lowered text': rc=0 SURVIVED | OK | []
MUTANT 'quoted names': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s5_quoted_name']
MUTANT 'credential missing check': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s3_missing_credential']
MUTANT 'new-credential check (whole branch)': rc=1 KILLED | FAILED (failures=2) | ['FAIL: test_s3_old_shared_credential_rejected', 'FAIL: test_s3_wrong_credential_for_login']
MUTANT 'old shared credential rejected': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s3_old_shared_credential_rejected']
MUTANT 'credential equals document name': rc=1 KILLED | FAILED (failures=1) | ['FAIL: test_s3_wrong_credential_for_login']
RESTORED copy rc 0 OK
```
Result: 18 of 19 killed; 1 survived ('toks() on non-lowered text', the same one that survived in round 4); the restored copy passes (rc 0).

## Step 5: hostile flow files (each one a copy of n8n-flows-real-v5 with one change; run: `python3 -I <scratch copy of script> --roles-doc ROLES-PROPOSAL.md <folder>`)
"expect" is my prior guess, not a verdict. H01-H24 = same list as evidence-r4; N01-N10 new. "TRACEBACK" would be printed after rc if "Traceback" appeared in stdout or stderr.
```
H01 SQL in a Code node | expect FAIL | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-form X: SQL-like text in a 'n8n-nodes-base.code' node ('DELETE FROM'); the check reads only n8n-nodes-base.postgres nodes
H02 SQL query in an expression in a Set node | expect FAIL | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-hook X: SQL-like text in a 'n8n-nodes-base.set' node ('SELECT email FROM'); the check reads only n8n-nodes-base.postgres nodes
H03 DELETE inside a string literal in a Postgres query | expect report | rc=1  | 2 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: forbidden keyword DELETE inside a string literal (the check cannot tell data from SQL; pass it as a parameter)
H04 uppercase table name MF_LEADS | expect report | rc=0  | 0 FAIL lines | 0.0s | first: TOTAL PROBLEMS: 0
H05 comment-hidden SQL (/* DELETE FROM mf_leads */) | expect report | rc=1  | 2 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: statement kind 'delete' not allowed (SELECT/INSERT/UPDATE only)
H06 line-comment hidden DROP after the query | expect report | rc=1  | 2 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: statement kind 'drop' not allowed (SELECT/INSERT/UPDATE only)
H07 second statement after semicolon (DROP TABLE) | expect FAIL | rc=1  | 2 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: statement kind 'drop' not allowed (SELECT/INSERT/UPDATE only)
H08 schema-qualified table public.mf_leads | expect report | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: touches table 'public.mf_leads', only mf_leads is allowed
H09 schema-qualified other table secret.users | expect FAIL | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: touches table 'secret.users', only mf_leads is allowed
H10 empty file (mf-hook.json, 0 bytes) | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: cannot read flow file (JSONDecodeError: Expecting value: line 1 column 1 (char 0))
H11 malformed JSON | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: cannot read flow file (JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 14 (char 13))
H12 huge file (about 60 MB of padding in a Set node) | expect report | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: cannot read flow file (file is 60005998 bytes, over the 5242880 byte limit (not read))
H13 top-level JSON is a list | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: malformed flow file: top level is list, expected an object
H14 'nodes' is null | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: malformed flow file: 'nodes' is null, expected a list
H15 Postgres type in different letter case (n8n-nodes-base.Postgres) with DELETE | expect FAIL | rc=1  | 2 FAIL lines | 0.0s | first: FAIL flows mf-form X: database node type 'n8n-nodes-base.Postgres' (only n8n-nodes-base.postgres is read by this check)
H16 SQL in node notes | expect FAIL | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-form Claim: SQL-like text ('DELETE FROM') in the notes or another parameter of a Postgres node; only its query field is checked, so move
H17 disabled Postgres node with bad query | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-form X: node is disabled (True); it is checked as if enabled, remove it or enable it
H18 full-width letters (DELETE written as fullwidth) in a Code node | expect report | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-form X: SQL-like text in a 'n8n-nodes-base.code' node ('mf_leads'); the check reads only n8n-nodes-base.postgres nodes
H19 dollar-quoted body hiding DELETE | expect report | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: dollar-quoted string not allowed (its body is not read by this check)
H20 query value is a list, not a string | expect FAIL | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: empty query
H21 extra flow file mf-extra.json | expect FAIL | rc=1  | 2 FAIL lines | 0.0s | first: FAIL flows mf-extra: this file has zero Postgres nodes (nothing in it was checked)
H22 split-string SQL in a Code node ('DEL'+'ETE FROM') | expect report (known miss) | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-form X: SQL-like text in a 'n8n-nodes-base.code' node ('mf_leads'); the check reads only n8n-nodes-base.postgres nodes
H23 SQL in an HTTP Request node body | expect FAIL | rc=1  | 1 FAIL lines | 0.1s | first: FAIL flows mf-form X: SQL-like text in a 'n8n-nodes-base.httpRequest' node ('UPDATE mf_leads SET'); the check reads only n8n-nodes-base.postgres nodes
H24 operation key moved: 'Operation' (capital O) instead of operation | expect FAIL | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-form Claim: operation is None, only executeQuery is checked
N01 nodes null | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: malformed flow file: 'nodes' is null, expected a list
N02 a node is a string | expect FAIL | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-hook: malformed node 12: it is str, expected an object
N03 parameters is a list | expect FAIL | rc=1  | 2 FAIL lines | 0.0s | first: FAIL flows mf-form: malformed node 3 (Claim): 'parameters' is list, expected an object
N04 100000-deep nesting | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: cannot read flow file (RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string)
N05 6 MB file | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: cannot read flow file (file is 6005998 bytes, over the 5242880 byte limit (not read))
N06 DELETE in a string literal | expect FAIL | rc=1  | 2 FAIL lines | 0.0s | first: FAIL flows mf-sub-crm-mail MarkDone: forbidden keyword DELETE inside a string literal (the check cannot tell data from SQL; pass it as a parameter)
N07 disabled Postgres node with DROP | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-form X: node is disabled (True); it is checked as if enabled, remove it or enable it
N08 SQL in notes of a Postgres node | expect FAIL | rc=1  | 1 FAIL lines | 0.0s | first: FAIL flows mf-form Claim: SQL-like text ('DELETE FROM') in the notes or another parameter of a Postgres node; only its query field is checked, so move
N09 non-UTF-8 bytes | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: cannot read flow file (UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 20: invalid start byte)
N10 empty file | expect FAIL | rc=1  | 3 FAIL lines | 0.0s | first: FAIL flows mf-hook: cannot read flow file (JSONDecodeError: Expecting value: line 1 column 1 (char 0))
```
Summary: 34 runs, 0 TRACEBACK, 0 harness errors. rc=1 in 33; rc=0 in 1 (H04, uppercase table name). Compared with round 4: H03 now rc=1 (was 0), H12 now rc=1 (was 0, no size limit), H14 no traceback (was TRACEBACK), H16 now rc=1 (was 0), H17 now flagged as disabled (message names the disabled flag).
Not run: any database or n8n instance; full repo pytest; CodeQL/SonarCloud/CodeRabbit.

Head: cd09dc9fc
