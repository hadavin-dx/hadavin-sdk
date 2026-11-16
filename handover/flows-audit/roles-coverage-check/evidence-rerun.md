# evidence-rerun (EVIDENCE RUNNER: raw results, no judgement)
Scratch layout: /tmp/rolesev2/base (copies of roles-coverage-check, ROLES-PROPOSAL.md, n8n-flows-real-v5, n8n-flows-film-v5); harness /tmp/rolesev2/h/mut.py; each mutant on a fresh copy. Originals untouched.
Verdict rule: rc!=0 with message = killed; rc=0 = SURVIVED; traceback = CRASH.

## Baseline
- `python3 -I check_grants_cover_queries.py <real-v5> <film-v5>`: rc=0, 14 postgres nodes per folder, TOTAL PROBLEMS: 0 (raw: /tmp/rolesev2/run-main.txt)
- each folder alone: rc=0 (real), rc=0 (film)
- `python3 -m unittest -v test_check_grants`: rc=0, Ran 19 tests, OK (raw: /tmp/rolesev2/unit.txt)

## Mutants (22 run: 0 CRASH, 5 SURVIVED, 17 killed). SURVIVED first.
Mutant ids: D = grant text in ROLES-PROPOSAL.md section 4; F = flow file; I = input. F6a-d are the four ways of the "SQL in a node the script does not read" mutant; I4b and I4c are extra.
Notes on SURVIVED: F6a-d add a node (Code, MySQL type, postgresTool type, Set) holding DELETE/DROP SQL text; the script only reads nodes of type n8n-nodes-base.postgres, so it exits 0. I4c removes the Postgres nodes from one file while other files in the folder keep theirs; exit 0 (the zero-node rule is per folder).

| mutant | rc | verdict | message |
|---|---|---|---|
| F6a SQL in Code node | 0 | SURVIVED | TOTAL PROBLEMS: 0 |
| F6b SQL in a MySQL-type node | 0 | SURVIVED | TOTAL PROBLEMS: 0 |
| F6c SQL in postgresTool node | 0 | SURVIVED | TOTAL PROBLEMS: 0 |
| F6d SQL text in a Set node | 0 | SURVIVED | TOTAL PROBLEMS: 0 |
| I4c file with no Postgres node (others remain) | 0 | SURVIVED | TOTAL PROBLEMS: 0 |
| D1 door SELECT minus claim_token | 1 | killed | FAIL n8n-flows-real-v5 mf-form Claim -> mf_door: UNCOVERED [('SELECT', 'claim_token')] / FAIL n8n-flows-real-v5 mf-hook Claim -> mf_door: UNCOVERED [('SELECT', 'claim_token')] / FAIL n8n-flows-film-v5 mf-form Claim -> mf_door: UNCOVERED [('SELECT', 'claim_token')] / FAIL n8n-flows-film-v5 mf-hook Claim -> mf_door: UNCOVERED [('SELECT', 'claim_token')] |
| D2 door INSERT minus attempts | 1 | killed | FAIL n8n-flows-real-v5 mf-form Claim -> mf_door: UNCOVERED [('INSERT', 'attempts')] / FAIL n8n-flows-real-v5 mf-hook Claim -> mf_door: UNCOVERED [('INSERT', 'attempts')] / FAIL n8n-flows-film-v5 mf-form Claim -> mf_door: UNCOVERED [('INSERT', 'attempts')] / FAIL n8n-flows-film-v5 mf-hook Claim -> mf_door: UNCOVERED [('INSERT', 'attempts')] |
| D3 sub UPDATE minus mail_sent | 1 | killed | FAIL n8n-flows-real-v5 mf-sub-crm-mail MailClaim -> mf_sub: UNCOVERED [('UPDATE', 'mail_sent')] / FAIL n8n-flows-film-v5 mf-sub-crm-mail MailClaim -> mf_sub: UNCOVERED [('UPDATE', 'mail_sent')] / TOTAL PROBLEMS: 2 |
| D4 recover SELECT minus created_at | 1 | killed | FAIL n8n-flows-real-v5 mf-recovery ClaimStuck -> mf_recover: UNCOVERED [('SELECT', 'created_at')] / FAIL n8n-flows-film-v5 mf-recovery ClaimStuck -> mf_recover: UNCOVERED [('SELECT', 'created_at')] / TOTAL PROBLEMS: 2 |
| D5 recover UPDATE minus claim_token | 1 | killed | FAIL n8n-flows-real-v5 mf-recovery ClaimStuck -> mf_recover: UNCOVERED [('UPDATE', 'claim_token')] / FAIL n8n-flows-film-v5 mf-recovery ClaimStuck -> mf_recover: UNCOVERED [('UPDATE', 'claim_token')] / TOTAL PROBLEMS: 2 |
| D6 alert UPDATE minus alert_sent | 1 | killed | FAIL n8n-flows-real-v5 mf-recovery AlertMark -> mf_alert: UNCOVERED [('UPDATE', 'alert_sent')] / FAIL n8n-flows-film-v5 mf-recovery AlertMark -> mf_alert: UNCOVERED [('UPDATE', 'alert_sent')] / TOTAL PROBLEMS: 2 |
| D7 add table-level GRANT SELECT to mf_door | 1 | killed | FAIL table-level SELECT grant (wider than columns) to ['mf_door'] / TOTAL PROBLEMS: 1 |
| D8 add unused column grant (door SELECT + name) | 1 | killed | FAIL n8n-flows-real-v5: unused grant SELECT ['name'] for mf_door (no query needs it) / FAIL n8n-flows-film-v5: unused grant SELECT ['name'] for mf_door (no query needs it) / TOTAL PROBLEMS: 2 |
| F1 add DELETE stmt | 1 | killed | FAIL n8n-flows-real-v5 mf-form Stored: statement kind 'delete' not allowed (SELECT/INSERT/UPDATE only) / FAIL n8n-flows-real-v5 mf-form Stored: forbidden keyword DELETE / FAIL n8n-flows-film-v5 mf-form Stored: statement kind 'delete' not allowed (SELECT/INSERT/UPDATE only) / FAIL n8n-flows-film-v5 mf-form Stored: forbidden keyword DELETE |
| F2 add TRUNCATE stmt | 1 | killed | FAIL n8n-flows-real-v5 mf-form Stored: statement kind 'truncate' not allowed (SELECT/INSERT/UPDATE only) / FAIL n8n-flows-real-v5 mf-form Stored: forbidden keyword TRUNCATE / FAIL n8n-flows-film-v5 mf-form Stored: statement kind 'truncate' not allowed (SELECT/INSERT/UPDATE only) / FAIL n8n-flows-film-v5 mf-form Stored: forbidden keyword TRUNCATE |
| F3 add second table | 1 | killed | FAIL n8n-flows-real-v5 mf-form Stored: comma-joined tables not allowed / FAIL n8n-flows-film-v5 mf-form Stored: comma-joined tables not allowed / TOTAL PROBLEMS: 2 |
| F4 CTE writing another table | 1 | killed | FAIL n8n-flows-real-v5 mf-form Stored: statement kind 'with' not allowed (SELECT/INSERT/UPDATE only) / FAIL n8n-flows-real-v5 mf-form Stored: touches table 'other_tbl', only mf_leads is allowed / FAIL n8n-flows-film-v5 mf-form Stored: statement kind 'with' not allowed (SELECT/INSERT/UPDATE only) / FAIL n8n-flows-film-v5 mf-form Stored: touches table 'other_tbl', only mf_leads is allowed |
| F5 UPDATE of new column (MarkDone sets name) | 1 | killed | FAIL n8n-flows-real-v5 mf-sub-crm-mail MarkDone -> mf_sub: UNCOVERED [('UPDATE', 'name')] / FAIL n8n-flows-film-v5 mf-sub-crm-mail MarkDone -> mf_sub: UNCOVERED [('UPDATE', 'name')] / TOTAL PROBLEMS: 2 |
| I1 empty folder | 1 | killed | FAIL empty: zero Postgres nodes (nothing was checked) / FAIL empty: unused grant SELECT ['alert_attempts', 'alert_sent', 'alert_token', 'alert_until', 'created_at', 'lead_key', 'state'] for mf_alert (no query needs i / FAIL empty: unused grant UPDATE ['alert_attempts', 'alert_sent', 'alert_token', 'alert_until', 'updated_at'] for mf_alert (no query needs it) / FAIL empty: unused grant SELECT ['claim_token', 'lead_key', 'state'] for mf_door (no query needs it) |
| I2 nonexistent folder | 1 | killed | FAIL nope: folder does not exist / TOTAL PROBLEMS: 1 |
| I3 malformed JSON | 1 | killed | FAIL n8n-flows-real-v5 mf-form: cannot read flow file (JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 3 (char 2)) / TOTAL PROBLEMS: 1 |
| I4 Postgres node empty query | 1 | killed | FAIL n8n-flows-real-v5 mf-form Stored: empty query / TOTAL PROBLEMS: 1 |
| I4b Postgres node query key missing | 1 | killed | FAIL n8n-flows-real-v5 mf-form Stored: empty query / TOTAL PROBLEMS: 1 |
