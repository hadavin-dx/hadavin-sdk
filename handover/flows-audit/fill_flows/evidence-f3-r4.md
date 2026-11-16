# evidence-f3-r4 (EVIDENCE RUNNER: raw results, no judgement)
Run: Mon Nov 16 09:32:38 UTC 2026 UTC. AWS_* unset. Scratch: /tmp/f3ev4/ (copy of repo tool + demo/n8n-flows-{real,film}-v5 in relative layout; repo files untouched; this file is the only repo write). Ran as uid 0 (root).

## COUNTS
Unit tests: rc=0, Ran 75 tests, OK (python3 -I -m unittest).
ruff check: rc=0 'All checks passed!'. ruff format --check: rc=0 '14 files already formatted'. bandit -ll (/tmp/core-venv/bin/bandit -r folder): rc=0 'No issues identified' (3 Low only, below -ll). bandit on fill_flows.py alone (pip-installed system bandit 1.9.4): rc=0, 0/0/0.
Mutants: 13 run, 10 KILLED, 3 SURVIVED.

## SURVIVED (full suite stayed OK, 75 tests)
1. M5b: values-file 'not S_ISREG' check disabled (fill_flows.py read_values, line 84-85).
2. P-del: new symlinked-output-parent check REMOVED FROM do_delete (line 557); suite stays OK. (Removed from fill: killed.)
3. S2: check mode skips placeholder SMTP_CREDENTIAL_ID in its PH_RE scan (line 490 loop).

## KILLED
M5a delete no-manifest S_ISREG (2 tests); M7 manifest-exists refusal on fill (1); M13 manifest symlink/folder check on delete (1); P-fill symlinked-parent check in fill (1: test_symlinked_parent_made_by_another_user_is_refused); S1 PH_RE without INTAKE_ADDRESS_PLACEHOLDER (1); H1 delete changed hash without --force-hash (1); E1 unresolved $env passes in fill (2); E2 check ignores 'other $env use' (1); E3 check ignores TOKEN matches (3); S3 fill leftover placeholder count off (13).
Note: the tool has no separate 'secret scan'. Closest analogues mutated: S1/S2/S3 (placeholder name scan), E1-E3 ($env scan).

### Raw mutant log
M5a no S_ISREG (delete no-manifest signature) | rc=1 | KILLED | Ran 75 tests in 6.489s | FAILED (failures=2) | 2 failing: test_no_manifest_force_hash_refuses_a_folder_named_like_a_json_file; test_no_manifest_refuses_a_fifo_without_hanging
M5b no S_ISREG (values file) | rc=0 | SURVIVED | Ran 75 tests in 6.715s | OK | 0 failing: 
M7 no manifest-exists refusal on fill | rc=1 | KILLED | Ran 75 tests in 6.851s | FAILED (failures=1) | 1 failing: test_fill_names_a_leftover_manifest_plainly
M13 no manifest symlink/folder check on delete | rc=1 | KILLED | Ran 75 tests in 6.544s | FAILED (failures=1) | 1 failing: test_delete_no_manifest_refuses_a_symlink_or_folder_in_the_manifest_place
P-fill no symlinked-parent check in fill | rc=1 | KILLED | Ran 75 tests in 6.445s | FAILED (failures=1) | 1 failing: test_symlinked_parent_made_by_another_user_is_refused
P-del no symlinked-parent check in delete | rc=0 | SURVIVED | Ran 75 tests in 6.431s | OK | 0 failing: 
S1 leftover/placeholder scan skips INTAKE_ADDRESS_PLACEHOLDER | rc=1 | KILLED | Ran 75 tests in 6.514s | FAILED (failures=1) | 1 failing: test_placeholders_filled_when_keys_given
H1 delete removes changed-hash file without --force-hash | rc=1 | KILLED | Ran 75 tests in 6.595s | FAILED (failures=1) | 1 failing: test_hash_change
E1 unresolved $env token passes (fill leftover check) | rc=1 | KILLED | Ran 75 tests in 6.789s | FAILED (failures=2) | 2 failing: test_odd_spellings; test_dynamic_env_use_refused
E2 check ignores other $env use (dynamic form) | rc=1 | KILLED | Ran 75 tests in 7.206s | FAILED (failures=1) | 1 failing: test_check_reads_parsed_json_forms
E3 check ignores TOKEN matches | rc=1 | KILLED | Ran 75 tests in 6.588s | FAILED (failures=3) | 3 failing: test_check_mode; test_check_reads_parsed_json_forms; test_token_in_every_location
S2 check skips one placeholder name (PH_RE in check only) | rc=0 | SURVIVED | Ran 75 tests in 6.540s | OK | 0 failing: 
S3 fill leftover count skips placeholders | rc=1 | KILLED | Ran 75 tests in 6.068s | FAILED (failures=13) | 13 failing: test_placeholder_inside_longer_string_counts; test_symlinked_parent_of_my_own_is_accepted_and_works_end_to_end; test_trailing_slash_in_url_warns

## Raw hostile inputs (film-v5 input, made-up values 127.0.0.1)
(first pass: sed-based cases E and F did not edit anything because the token is only in mf-sub-crm-mail.json; their output below is not valid evidence; redo follows)
## A symlinked parent
--- own link parent fill
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
o1
o1.manifest.json
--- own link parent delete
deleted 4 files, the folder and the manifest
rc=0
--- other-user link parent fill
refused: a folder in the output path is a symlink made by another user
rc=1
--- fill real/o3
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
--- other-user link parent delete
refused: a folder in the output path is a symlink made by another user
rc=1
o3
o3.manifest.json
--- cleanup real/o3
deleted 4 files, the folder and the manifest
rc=0
## B output inside git repo
--- fill into git repo
refused: output path is inside a git repository (a parent folder has .git)
rc=1
--- fill into git subfolder
refused: output path is inside a git repository (a parent folder has .git)
rc=1
## C hostile values (MF_STAGE_URL)
--- value[1] a"b
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
outputs parse as JSON
--- check c1
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- value[2] a'b
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
outputs parse as JSON
--- check c2
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- value[3] a\b
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
outputs parse as JSON
--- check c3
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- value[4] a`b
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
outputs parse as JSON
--- check c4
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- value[5] a${x}b
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
outputs parse as JSON
--- check c5
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- value[6] a$(id)b
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
outputs parse as JSON
--- check c6
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- value[7] a\nb
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
outputs parse as JSON
--- check c7
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- value[8] a{{b
refused: values file line 3: value of MF_STAGE_URL contains '{{' or '}}'
rc=1
--- real newline value
refused: values file line 4: no '=' (expected KEY=VALUE)
rc=1
## D missing value
--- missing MF_STAGE_URL
refused: mf-sub-crm-mail.json: cannot fill these names (missing or empty in the values file, or not a DESK_/MF_ name): MF_STAGE_URL
rc=1
ls: cannot access 'd1': No such file or directory
ls: cannot access 'd1.manifest.json': No such file or directory
--- empty MF_STAGE_URL
refused: mf-sub-crm-mail.json: cannot fill these names (missing or empty in the values file, or not a DESK_/MF_ name): MF_STAGE_URL
rc=1
## E leftover env
--- check on unfilled input
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: token $env MF_STAGE_URL
mf-sub-crm-mail.json: token $env MF_STAGE_TIMEOUT_MS
mf-sub-crm-mail.json: token $env MF_CRM_URL
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 22 problem(s)
rc=1
--- fill with unknown token
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
## F hand-edited output
--- fill ok
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
--- check clean
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- check after adding env token
mf-form.json: placeholder PG_CREDENTIAL_ID x2
mf-form.json: placeholder SUB_WORKFLOW_ID x1
mf-hook.json: placeholder PG_CREDENTIAL_ID x2
mf-hook.json: placeholder SUB_WORKFLOW_ID x1
mf-recovery.json: placeholder PG_CREDENTIAL_ID x5
mf-recovery.json: placeholder SMTP_CREDENTIAL_ID x1
mf-recovery.json: placeholder SUB_WORKFLOW_ID x1
mf-sub-crm-mail.json: placeholder PG_CREDENTIAL_ID x5
mf-sub-crm-mail.json: placeholder SMTP_CREDENTIAL_ID x1
check: 4 files, 19 problem(s)
rc=1
--- delete hand-edited (no force)
deleted 4 files, the folder and the manifest
rc=0
--- delete hand-edited --force-hash
refused: output folder and manifest are both missing; nothing to delete
rc=1

## Raw redo and extra cases
## C2 value as written in output (c1,c3,c5)
ame: CRM + mail (sub-wo
rl": "={{ \"a\\\"b\" 
ame: CRM + mail (sub-wo
rl": "={{ \"a\\\\b\" 
ame: CRM + mail (sub-wo
rl": "={{ \"a$\\u007bx\\
## E2 leftover token redo
1
--- fill unknown token name
refused: output folder or its manifest already exists (delete it first)
rc=1
--- fill dynamic env form
refused: mf-sub-crm-mail.json: not valid JSON (JSONDecodeError)
rc=1
ls: cannot access '/tmp/f3ev4/h2/e2': No such file or directory
ls: cannot access '/tmp/f3ev4/h2/e2.manifest.json': No such file or directory
## F redo hand-edited output
--- fill ok
NOT READY TO IMPORT: 19 placeholders left (create the credentials, import the sub-flow, fill again, then run check)
filled 4 files, 3 names and 0 placeholders
rc=3
1
--- check after adding env token
mf-sub-crm-mail.json: token $env MF_STAGE_URL
check: 4 files, 1 problem(s)
rc=1
--- delete hand-edited (no force)
refused: mf-sub-crm-mail.json: content changed since it was written (use --force-hash); nothing deleted
rc=1
f2
f2.manifest.json
--- delete hand-edited --force-hash
deleted 4 files, the folder and the manifest
rc=0
ls: cannot access 'f2': No such file or directory
--- delete with files perm 644
rc=0
--- redo fill unknown token name (MF_UNKNOWN_X): rc=1 refused "cannot fill these names ... MF_UNKNOWN_X"
--- redo dynamic env form $env[('MF_'+'CRM_URL')]: rc=1 refused "a $env token is left after substitution (dynamic or odd form)"; no output folder or manifest created
