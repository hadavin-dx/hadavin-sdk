# ROLES-PROPOSAL: Postgres roles for the n8n flows (queue item F6, finding F-010)

STATUS: PROPOSAL ONLY. Nothing here was run, created or changed. No SQL was tested (no Postgres was available, by order). No flow file, credential or database was touched.

## 0. What I could and could not establish (read first)

- No file in the repository creates a Postgres role or grants anything (F6-AUDIT.md note; I searched `handover/demo` for CREATE ROLE / GRANT: none found in the files I read). So today the rights of the role behind the n8n credential `n8n-publish-pg` are unknown. The take's database setup may live in laptop notes outside this repository. Step 0 of any change: on the laptop, ask the database what that role can do (see section 4, test R0).
- The table the real-v5 and film-v5 flows need is the v4 file `handover/demo/n8n-flows-v4/mf_leads.sql` (it has the four alert columns). The file `handover/demo/n8n-flows/mf_leads.sql` has no alert columns, but the v5 recovery flow reads and writes them, so that older table file does not fit v5 (a fact, not a new finding row; the lead may want it noted in F-010).
- real-v5 and film-v5: I extracted every Postgres node from both folders. The SQL text of all 14 distinct statements is identical in both folders (checked by reading the printed text of each node side by side, not by a diff tool). Only the sub-workflow `Execute Workflow` node differs elsewhere; it holds no SQL.
- Every Postgres node in all 8 files uses the one credential `n8n-publish-pg`. All use `executeQuery` (raw SQL), none use the node's own insert/update forms.
- Plain words: a "role" is a database login with its own list of allowed actions. A "grant" is one entry on that list. "Column-level" means a grant names the exact columns, not the whole table.

## 1. Every Postgres statement (table `mf_leads`, both real-v5 and film-v5)

Legend: R = columns the statement reads (in WHERE, SELECT, RETURNING or subquery); W = columns it writes. "Door" = a workflow that receives a lead.

| # | Workflow (file) | Node | Action | W (columns written) | R (columns read) | Reason |
|---|---|---|---|---|---|---|
| 1 | Door form (mf-form) | Claim | INSERT ... ON CONFLICT (lead_key) DO NOTHING RETURNING | lead_key, email, name, state, claimed_until, claim_token, attempts (the other columns take their table defaults) | lead_key, claim_token, state (RETURNING) | The insert is the claim: first writer of a lead_key wins, a repeat does nothing. |
| 2 | Door form | Stored | SELECT | none | state, lead_key | When the insert did nothing (repeat lead), tell the caller what state the lead is in. |
| 3 | Door hook (mf-hook) | Claim | same text as #1 | same as #1 | same as #1 | Same job for the webhook door. |
| 4 | Door hook | Stored | same text as #2 | none | state, lead_key | Same. |
| 5 | Sub-workflow (mf-sub-crm-mail) | SetCrmId | UPDATE | crm_id, updated_at | lead_key, claim_token, state | Record the CRM record id, only for the holder of the claim while state is processing. |
| 6 | Sub-workflow | MailClaim | UPDATE | mail_sent, updated_at | lead_key, claim_token, mail_sent, state | Mark the lead mail as sent exactly once. |
| 7 | Sub-workflow | MarkDone | UPDATE | state, updated_at | lead_key, claim_token, state | Finish the lead. |
| 8 | Sub-workflow | MarkUnknownA | UPDATE | state, updated_at | lead_key, claim_token, state | Say "unknown" when the outcome cannot be told. |
| 9 | Sub-workflow | MarkUnknownB | UPDATE | state, updated_at | lead_key, claim_token, state, mail_sent | Same, when the mail may have gone out. |
| 10 | Recovery (mf-recovery) | ClaimStuck | UPDATE ... WHERE lead_key IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING | claimed_until, claim_token, attempts, updated_at | lead_key, state, claimed_until, attempts, created_at, email (RETURNING) | Take over leads whose claim ran out, at most 5, 3 tries each. Email is needed to run the sub-workflow again. |
| 11 | Recovery | MarkFailed | UPDATE ... RETURNING | state, updated_at | state, claimed_until, attempts, mail_sent, lead_key | Close leads that used up their tries (failed, or unknown if mail was sent). |
| 12 | Recovery | AlertClaim | UPDATE ... (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING | alert_until, alert_token, alert_attempts | lead_key, state, alert_sent, alert_until, created_at, alert_token (RETURNING) | Claim up to 5 leads that need an alert. |
| 13 | Recovery | AlertBackoff | UPDATE ... RETURNING | alert_until | lead_key, alert_token, alert_sent, alert_attempts | After a failed alert mail, wait before the next try. |
| 14 | Recovery | AlertMark | UPDATE ... RETURNING | alert_sent, updated_at | lead_key, alert_token, alert_sent | Mark the alert as sent. |

No statement deletes, truncates, creates, alters, or touches another table or a sequence. Statement #1 calls the built-in `gen_random_uuid()`.

## 2. Proposed split of roles (one role per function)

Four flow roles plus two roles the proposal needs but the flows do not use. Names are placeholders; the owner may rename.

| Role (placeholder) | Function | Statements | Maps to n8n credential |
|---|---|---|---|
| mf_owner | Owns the table, runs the create/migrate script. NOT used by n8n. NOLOGIN or used only by hand on the laptop. | none | none |
| mf_door | The two doors: claim a lead and look up its state | #1 to #4 | `n8n-publish-pg-door` (new) |
| mf_sub | The sub-workflow: record CRM id, mail sent, final state | #5 to #9 | `n8n-publish-pg-sub` (new) |
| mf_recover | Recovery sweep: take over stuck leads, close exhausted ones | #10, #11 | `n8n-publish-pg-recover` (new) |
| mf_alert | Alert bookkeeping only (claim, backoff, mark) | #12 to #14 | `n8n-publish-pg-alert` (new) |
| (humans / reader) | Not proposed here: nobody needs a reader for the take. A read-only viewer role is a later question. | | |

n8n's own state role (F-011) is a separate, fifth identity on a separate database or schema and is not defined here.

### Is the split cheap? Honest answer

- n8n credentials are chosen per node, not per workflow. The 14 nodes can use 4 credentials, even inside one workflow (the recovery workflow would use two: `-recover` on ClaimStuck and MarkFailed, `-alert` on the three Alert nodes).
- Cost: 4 credentials created in n8n (each holds one password, entered by hand into n8n, never into a file), and in each of the 8 flow files (real-v5 and film-v5, 4 files each) the `credentials.postgres` entry of each Postgres node changes from `n8n-publish-pg` to the matching new name. That is an edit of 8 workflow files and a re-import, which is a flow change, so it needs the re-smoke test. It is NOT a config-only change.
- Cheaper half-step (option B): 2 roles only, `mf_flow` (#1 to #9) and `mf_sweep` (#10 to #14), 2 credentials. Gives the main gain (the doors and the sub-workflow can no longer touch alert columns or `attempts`; the sweep cannot write `crm_id` or `mail_sent`). I recommend the full four if done at all; B is the fallback.

### SQL (UNTESTED proposal, run only on the laptop)

```sql
-- UNTESTED proposal, run only on the laptop, on a COPY of the take's database first.
-- Passwords: set by hand with psql's \password or n8n's credential form. Never write them into this file.
-- The database name and schema name below are placeholders.

-- 0. Look first (read-only) what the current role can do. Replace <current_flow_role> by hand.
-- SELECT grantee, table_name, privilege_type FROM information_schema.role_table_grants WHERE grantee='<current_flow_role>';
-- SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles WHERE rolname='<current_flow_role>';

-- 1. Roles. No superuser, no create-role, no create-db, no bypass of row rules.
CREATE ROLE mf_door    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 5;
CREATE ROLE mf_sub     LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 5;
CREATE ROLE mf_recover LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 2;
CREATE ROLE mf_alert   LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 2;
-- (set each password by hand: \password mf_door  ... )

-- 2. Start from nothing.
REVOKE ALL ON TABLE mf_leads FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT  CONNECT ON DATABASE <take_database> TO mf_door, mf_sub, mf_recover, mf_alert;
GRANT  USAGE   ON SCHEMA public TO mf_door, mf_sub, mf_recover, mf_alert;

-- 3. mf_door: statements 1-4
GRANT INSERT (lead_key, email, name, state, claimed_until, claim_token, attempts) ON mf_leads TO mf_door;
GRANT SELECT (lead_key, state, claim_token)                                      ON mf_leads TO mf_door;

-- 4. mf_sub: statements 5-9
GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;
GRANT UPDATE (crm_id, mail_sent, state, updated_at)          ON mf_leads TO mf_sub;

-- 5. mf_recover: statements 10-11
GRANT SELECT (lead_key, email, state, claimed_until, attempts, created_at, mail_sent) ON mf_leads TO mf_recover;
GRANT UPDATE (claimed_until, claim_token, attempts, state, updated_at)                ON mf_leads TO mf_recover;

-- 6. mf_alert: statements 12-14
GRANT SELECT (lead_key, state, created_at, alert_sent, alert_token, alert_until, alert_attempts) ON mf_leads TO mf_alert;
GRANT UPDATE (alert_until, alert_token, alert_attempts, alert_sent, updated_at)                  ON mf_leads TO mf_alert;
```

Open technical points that the laptop test must settle (I could not test them): (a) whether `INSERT ... ON CONFLICT DO NOTHING RETURNING` is accepted with only the column grants above (my reading of the Postgres manual is that it needs INSERT on the inserted columns and SELECT on the returned columns, but I have not run it); (b) whether `FOR UPDATE SKIP LOCKED` in #10 and #12 needs UPDATE on at least one column (it does, per the manual, and the roles have it); (c) whether `gen_random_uuid()` is callable (it is a built-in in current Postgres versions, executable by everyone by default; the version in use was not checked).

## 3. Reason for each grant

| Grant | Reason (the statement that needs it) |
|---|---|
| door INSERT on 7 columns | #1/#3 write exactly these; the other columns (crm_id, mail_sent, created_at, updated_at, alert_*) fill from table defaults, so they need no grant |
| door SELECT on lead_key, state, claim_token | #1 RETURNING (all three); #2/#4 read state by lead_key |
| sub SELECT on lead_key, claim_token, state, mail_sent | WHERE clauses of #5 to #9; mail_sent in #6 and #9 |
| sub UPDATE on crm_id, mail_sent, state, updated_at | #5 crm_id; #6 mail_sent; #7 to #9 state; all set updated_at |
| recover SELECT on 7 columns | #10 reads lead_key, state, claimed_until, attempts, created_at and RETURNS email; #11 reads mail_sent |
| recover UPDATE on 5 columns | #10 claimed_until, claim_token, attempts, updated_at; #11 state, updated_at |
| alert SELECT on 7 columns | #12 reads state, alert_sent, alert_until, created_at and returns lead_key, alert_token; #13/#14 read alert_attempts, alert_token, alert_sent |
| alert UPDATE on 5 columns | #12 alert_until, alert_token, alert_attempts; #13 alert_until; #14 alert_sent, updated_at |
| CONNECT, USAGE on schema | A login cannot run anything without them |
| REVOKE from PUBLIC; REVOKE CREATE on schema | Deny-by-default start; nobody can create objects in the schema |

Not granted to anyone: DELETE, TRUNCATE, REFERENCES, TRIGGER, any table other than mf_leads, any sequence, CREATE anything.

## 4. Negative tests to write (each must FAIL with "permission denied"), and what each role can read and write

Write these as a script that connects as each role on a copy of the database; synthetic rows only. A test passes when the statement is refused.

| Id | Role | Must be denied | Why it matters |
|---|---|---|---|
| R0 | the current `n8n-publish-pg` role (before the change) | (not a denial test) print its attributes and table rights | Fact-finding: today's rights are undefined in the repo |
| R1 | mf_door | UPDATE any column; DELETE; TRUNCATE | A door can only create a lead, never change one |
| R2 | mf_door | SELECT email, name, crm_id, mail_sent, alert_* | The door reads only state and its own claim |
| R3 | mf_sub | INSERT; DELETE; UPDATE of email, name, lead_key, claim_token, claimed_until, attempts, alert_* | The sub-workflow cannot take or reset claims or touch alert state |
| R4 | mf_sub | SELECT email, name | No personal data for the sub-workflow (the flow passes the email in its own input, not from the database; to be confirmed by the re-smoke) |
| R5 | mf_recover | INSERT; DELETE; UPDATE of crm_id, mail_sent, email, name, alert_* | The sweep cannot fake a sent mail or an alert |
| R6 | mf_alert | SELECT email, name, crm_id; UPDATE of state, claim_token, attempts, crm_id, mail_sent | The alert role sees no personal data and cannot change lead state |
| R7 | every role | CREATE TABLE in the schema; DROP/ALTER mf_leads; SELECT on any other table; CREATE ROLE; COPY ... PROGRAM | No structure change, no reach beyond the table |
| R8 | every role | `SET ROLE` to another role of this list | No role hopping |
| R9 | every role | read n8n's own tables (after F-011 moves n8n to Postgres) | Matches test T-ROLES in F-041 |
| P1 to P14 | the owning role of each statement | run statement #n against synthetic rows and get the same result as today | Positive tests: the split must not break a flow (this is the part that needs the real flows run, i.e. the re-smoke) |

What each role can read and write after the change (columns of mf_leads only):

| Role | Can read | Can write |
|---|---|---|
| mf_door | lead_key, state, claim_token | insert: lead_key, email, name, state, claimed_until, claim_token, attempts |
| mf_sub | lead_key, claim_token, state, mail_sent | crm_id, mail_sent, state, updated_at |
| mf_recover | lead_key, email, state, claimed_until, attempts, created_at, mail_sent | claimed_until, claim_token, attempts, state, updated_at |
| mf_alert | lead_key, state, created_at, alert_sent, alert_token, alert_until, alert_attempts | alert_until, alert_token, alert_attempts, alert_sent, updated_at |
| today's single role | unknown (nothing in the repo defines it) | unknown |

## 5. Over-breadth review of my own proposal (what is still too wide)

1. Column grants cannot limit values or rows. mf_door can insert any state allowed by the table CHECK (for example `done`) and any `attempts`, because only the SQL text inside the flow restricts them. mf_sub can set state on any row; only the SQL `WHERE claim_token=...` limits it. A grant cannot fix this. Closing it needs either triggers or database functions that the roles call instead of raw SQL (that is new code on the claim path; by the CODE-LAST rule I name it as not proposed, and I have no evidence yet that it is needed). So the split cuts which columns each flow can touch, not which rows or values.
2. mf_recover reads `email` for every row (needed by #10). That is the one place personal data is readable beyond the door. It is made-up data on the take, but on a client build it is a read right worth a masking decision.
3. mf_sub can write `state` for any row and `mail_sent`; this is needed (#6 to #9). It cannot reset a claim or attempts.
4. Everyone keeps CONNECT and USAGE on the schema and EXECUTE on built-in functions that Postgres gives to PUBLIC. Not changed here.
5. Four separate passwords means four secrets in n8n; they are only as safe as n8n's own credential store (F-011 and the encryption key). Splitting roles does not help if one n8n user can read all four credentials.
6. The SMTP credential (`mf-mail-smtp`) is out of scope; F-010 and F-030 still stand for it.
7. Not covered: a reader role for humans, a backup role, a migration role beyond `mf_owner`, and network rules (who can reach the database port). `pg_hba` was not read.

## 6. Cost and effect on the take

- Effect on the take if nothing is done before the video: none. This file is text only.
- Take-day safe (no effect on the take): reading this proposal; running section 0 queries read-only on the laptop; building roles and the negative-test script on a COPY of the database (not the take's database) and running P1 to P14 there.
- NOT take-day safe: changing the take's database roles, creating the four n8n credentials, or editing the `credentials` entries of the 8 flow files and re-importing. These change what the flows run on and need the re-smoke. Do them after the video, unless the lead decides otherwise.
- Estimated work (agent clock, my estimate, not measured): about 1 hour to write and review the SQL and the negative-test script, about 1 hour to run it on a copy and fix grant mistakes, about 1 hour for the 8 flow edits plus one re-smoke. Rated Nit (after the video) in FINDINGS, so I recommend AFTER; option B (two roles) is the smaller step.
- EGM: this proposal has not gone through EGM review (EGM review is the lead's step; I could not invoke it from here).

Not checked: any SQL (nothing ran in Postgres); whether the current role is a superuser or owner; the Postgres version; `pg_hba` and network access; whether the take's database setup exists outside this repository; whether n8n's Postgres node handles `RETURNING` and `FOR UPDATE SKIP LOCKED` unchanged under column grants; the older v3/v4 flow folders and the desk-* workflows; whether any other workflow, script or person also uses `n8n-publish-pg`; R-numbers in the studio bible (not present in this repository).
