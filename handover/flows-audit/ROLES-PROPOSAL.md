# ROLES-PROPOSAL: separate database logins for the lead-intake flows (queue item F6, finding F-010)

1. WHAT THIS IS: a written proposal only. It splits one shared database login into four logins, each allowed to touch only the columns its own step needs. Nothing was run, created or changed, and no Postgres was available.
2. BEFORE THE VIDEO: do nothing to the video take's database or flows. Reason: changing logins changes what the flows run on, so the whole lead path (form, webhook, sub-workflow, recovery) must be re-tested end to end, and that re-test has not been done. The only allowed action before the video is the read-only look in section 5 (it reads the database's own lists and changes nothing).
3. UNVERIFIED, COULD BREAK LEAD INTAKE (I could not fetch the Postgres manual: the proxy refused it with HTTP 403; every Postgres statement below is from memory): (a) whether `INSERT ... ON CONFLICT DO NOTHING RETURNING` works with column-only rights (if not, the two doors accept no leads); (b) whether `FOR UPDATE SKIP LOCKED` works with column-only rights (if not, stuck leads are never taken over and alerts never go out); (c) whether `gen_random_uuid()` exists on the Postgres version in use (if not, the door insert fails); (d) how n8n's connection pool behaves against the connection limits (if wrong, leads are refused at busy moments). Details in section 8.
4. WHAT FAILED IN REVIEW ROUND 1 (all fixed in this version, not yet re-reviewed): the recovery role lacked the right to read `claim_token`, which statement 10 returns, so recovery would have failed (a real blocker); the old login was never retired; the "deny by default" start was incomplete; the test list was not exact; and the top did not say what to do before the video.

STATUS: PROPOSAL ONLY. This version has not passed a second review round.

## 0. Plain words used in this file (read before section 1)

- **n8n**: the workflow tool that runs the flows. **Flow**: one n8n workflow file. **Credential** (n8n word): a saved database login inside n8n (name plus password). **Postgres**: the database. **Role** (Postgres word): a database login with its own list of allowed actions; I say "login" for a role that can log in. **Grant**: one entry on that list. **Column-level grant**: the entry names exact columns of a table, not the whole table. **PUBLIC**: Postgres's built-in group that every login belongs to.
- **The video take**: the one recorded run of the demo video. **The laptop**: the machine that runs n8n and the take's database.
- **Door**: a flow that receives a lead. There are two: the form door (file `mf-form.json`) and the webhook door (`mf-hook.json`; a webhook is a web address another system calls). **Sub-workflow** (`mf-sub-crm-mail.json`): the flow the doors call to save the lead in the customer-contact system (the CRM) and send the lead's mail. **Recovery** (`mf-recovery.json`): the flow that runs on a timer, takes over leads that got stuck, and sends alert mails.
- **Claim** has two meanings in the old text; here it always means one of: **claim insert** = the first save of a new lead (the insert itself decides who owns the lead); **claim token** (column `claim_token`) = a random text that proves which run owns the lead right now; **take over** = recovery giving a stuck lead a new claim token. **Alert** = mail telling a person a lead ended in `failed` or `unknown`.
- **Terms inside the SQL statements**: `RETURNING` = the statement hands back columns of the row it just wrote, which counts as reading them. `ON CONFLICT DO NOTHING` = if the lead already exists, do nothing. `FOR UPDATE SKIP LOCKED` = lock the chosen rows and skip rows another run has locked. `NOINHERIT` = a login does not automatically gain the rights of groups it belongs to (none here; kept as a margin). `SQLSTATE 42501` = Postgres's 5-character code for "permission denied".
- **Re-test**: running the real flows again end to end after any change to their logins (I wrote "re-smoke" before). **Rule list**: "CODE-LAST" is the studio rule that our own code is the last choice; "EGM" is the studio's review process. Finding ids (F-010, F-011, F-030, F-041) are rows in the flows-audit findings list; they are only labels here.
- **`mf_`** is the prefix of the existing table name `mf_leads`; I did not find what it stands for. **Owner** below always means the studio owner (the person who decides money and risk); the database object's owner is called **table owner**.

## 1. What I established, and how sure I am

- No file in the repository creates a Postgres role or a grant (I searched `handover` outside `flows-audit` for the words CREATE ROLE and GRANT: no hit). So today's rights of the login behind the n8n credential `n8n-publish-pg` are unknown, and the database login's real name may differ from the credential's name. The take's database setup may exist only in laptop notes.
- The table the v5 flows need is `handover/demo/n8n-flows-v4/mf_leads.sql` (15 columns, including four alert columns). The older `handover/demo/n8n-flows/mf_leads.sql` has 11 columns and no alert columns, but the v5 recovery flow reads and writes them, so the older file does not fit v5.
- Folders checked: `handover/demo/n8n-flows-real-v5` and `handover/demo/n8n-flows-film-v5` (4 flow files each). I extracted the `query` field of every node of type `n8n-nodes-base.postgres` with a script: 14 nodes per folder, 28 in all. The script compared both folders' lists (credential name, operation and SQL text) and found them identical. A second script search found none of the words DELETE, TRUNCATE, DROP, ALTER, CREATE, COPY, GRANT, REVOKE or SET ROLE in any of the 28 queries, and no table other than `mf_leads`. Every node uses the credential `n8n-publish-pg` and the operation `executeQuery` (raw SQL). The scripts only read JSON text; they are in the session scratchpad, not in the repository, and were not run against any database.
- Not covered by that search: SQL built in code nodes or expressions outside the `query` field (I found none in the Postgres nodes; I did not search the other node types for database calls).

## 2. Every Postgres statement (table `mf_leads`; same text in real-v5 and film-v5)

Legend: Reads = columns the statement reads anywhere (WHERE, subquery, the right side of SET, RETURNING). Writes = columns it sets or inserts. Statement numbers are called S1 to S14 (not to be confused with test ids in section 5).

| # | Flow (file) | Node | Action | Writes | Reads | Reason |
|---|---|---|---|---|---|---|
| S1 | Form door (mf-form) | Claim | INSERT ... ON CONFLICT (lead_key) DO NOTHING RETURNING | lead_key, email, name, state, claimed_until, claim_token, attempts (other columns take table defaults) | lead_key, claim_token, state (RETURNING); lead_key (conflict check, UNVERIFIED) | The claim insert: first writer of a lead_key wins, a repeat does nothing. |
| S2 | Form door | Stored | SELECT | none | state, lead_key | When the insert did nothing (repeat lead), tell the caller the lead's state. |
| S3 | Webhook door (mf-hook) | Claim | same text as S1 | same as S1 | same as S1 | Same job for the webhook door. |
| S4 | Webhook door | Stored | same text as S2 | none | state, lead_key | Same. |
| S5 | Sub-workflow (mf-sub-crm-mail) | SetCrmId | UPDATE ... RETURNING | crm_id, updated_at | lead_key, claim_token, state | Record the CRM record id, only for the holder of the claim token while state is processing. |
| S6 | Sub-workflow | MailClaim | UPDATE ... RETURNING | mail_sent, updated_at | lead_key, claim_token, mail_sent, state | Mark the lead mail as sent exactly once. |
| S7 | Sub-workflow | MarkDone | UPDATE ... RETURNING | state, updated_at | lead_key, claim_token, state | Finish the lead. |
| S8 | Sub-workflow | MarkUnknownA | UPDATE ... RETURNING | state, updated_at | lead_key, claim_token, state | Say "unknown" when the outcome cannot be told. |
| S9 | Sub-workflow | MarkUnknownB | UPDATE ... RETURNING | state, updated_at | lead_key, claim_token, state, mail_sent | Same, when the mail may have gone out. |
| S10 | Recovery (mf-recovery) | ClaimStuck | UPDATE ... WHERE lead_key IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING lead_key, email, claim_token | claimed_until, claim_token, attempts, updated_at | lead_key, state, claimed_until, attempts, created_at; RETURNING lead_key, email, claim_token | Take over leads whose claim ran out (at most 5, 3 tries each). It hands back the NEW claim token and the email so the sub-workflow can run again. (Round 1 found the old table omitted claim_token here.) |
| S11 | Recovery | MarkFailed | UPDATE ... RETURNING lead_key | state, updated_at | state, claimed_until, attempts, mail_sent, lead_key | Close leads that used up their tries (failed, or unknown if the mail was sent). |
| S12 | Recovery | AlertClaim | UPDATE ... WHERE lead_key IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING lead_key, state, alert_token | alert_until, alert_token, alert_attempts | lead_key, state, alert_sent, alert_until, created_at, alert_attempts (read in `alert_attempts+1`); RETURNING lead_key, state, alert_token | Claim up to 5 leads that need an alert. |
| S13 | Recovery | AlertBackoff | UPDATE ... RETURNING lead_key | alert_until | lead_key, alert_token, alert_sent, alert_attempts | After a failed alert mail, wait before the next try. |
| S14 | Recovery | AlertMark | UPDATE ... RETURNING lead_key | alert_sent, updated_at | lead_key, alert_token, alert_sent | Mark the alert as sent. |

In the 28 queries I searched, none deletes, truncates, creates, alters, or names another table or a sequence (search method in section 1). S1 and S3 call the built-in `gen_random_uuid()`.

How the rights below were checked: a script read each of the 28 queries, derived Reads and Writes from the text, and tested that each is covered by the grants in section 4. Run on the grants of this version it reports 0 uncovered statements; run on the OLD grants of round 1 (recovery without `claim_token`) it reports S10 uncovered in both folders (so the check does catch the blocker). This is a text check, not a database run. It is a rough text parser and could miss an unusual statement; the real proof is test group P in section 5.

## 3. Proposed logins (one function per login)

Four flow logins plus one table-owner login that no flow uses. Names are placeholders.

| Login (placeholder) | Function | Statements | Maps to n8n credential |
|---|---|---|---|
| mf_tableowner | Owns the table; used only to run the create/migrate script by hand on the laptop. NOLOGIN (nobody logs in as it); the database administrator reaches it with `SET ROLE` (to be confirmed in the throwaway test). Decision made: NOLOGIN. | none | none |
| mf_door | The two doors: save a new lead and read its state | S1 to S4 | `n8n-publish-pg-door` (new) |
| mf_sub | The sub-workflow: record CRM id, mail sent, final state | S5 to S9 | `n8n-publish-pg-sub` (new) |
| mf_recover | Recovery sweep: take over stuck leads, close exhausted ones | S10, S11 | `n8n-publish-pg-recover` (new) |
| mf_alert | Alert bookkeeping only (claim, wait, mark) | S12 to S14 | `n8n-publish-pg-alert` (new) |
| (readers) | Not proposed: nobody needs a read-only person login for the take. | | |

n8n's own storage login (F-011) is a separate fifth identity on a separate database or schema and is not defined here.

### What the split costs

- n8n picks a credential per node, not per workflow, so 14 nodes can use 4 credentials (the recovery flow uses `-recover` on ClaimStuck and MarkFailed, `-alert` on the three Alert nodes).
- Cost: 4 credentials created in n8n (each password typed by hand into n8n, never into a file); in each of the 8 flow files the `credentials.postgres` entry of each Postgres node changes from `n8n-publish-pg` to the matching new name; the 8 files are re-imported. That is a flow change, so it needs the re-test. It is not a config-only change.
- **Option B (two logins, not proposed).** An earlier version offered one login for the doors plus sub-workflow and one for recovery plus alerts. That puts the claim and alert functions under one identity, which breaks the studio rule "one identity per function" (least-privilege rule). I removed it from the proposal. Using it would be an exception to that rule and needs the owner's explicit yes, with the exact extra rights written out: the merged door-and-sub login would hold INSERT on 7 columns, SELECT on 5, UPDATE on 4 (crm_id, mail_sent, state, updated_at) - so a door could change the state of any existing lead; the merged recovery-and-alert login would hold SELECT on 10 columns and UPDATE on 8 - so the claim step could rewrite alert columns. Nobody asked for it; no yes exists.

## 4. SQL (UNTESTED; for a throwaway Postgres only)

```sql
-- ############################################################################
-- DO NOT PASTE INTO THE VIDEO TAKE'S DATABASE OR SERVER. UNTESTED.
-- Run only on a separate, throwaway Postgres server (section 6) with made-up rows.
-- The REVOKE lines below remove rights from EVERY other login on the server too,
-- and roles are shared by the whole server, not by one database.
-- Passwords: set by hand with psql's \password or in n8n's credential form. Never write them in this file.
-- <db> and <old_flow_role> are placeholders. <date> = a real expiry date.
-- ############################################################################
\set ON_ERROR_STOP on

-- 1. Logins. No superuser, no create-role, no create-db, no bypass of row rules.
CREATE ROLE mf_tableowner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
CREATE ROLE mf_door    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 6 VALID UNTIL '<date>';
CREATE ROLE mf_sub     LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 6 VALID UNTIL '<date>';
CREATE ROLE mf_recover LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 3 VALID UNTIL '<date>';
CREATE ROLE mf_alert   LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 3 VALID UNTIL '<date>';
-- (set each password by hand: \password mf_door ... ; use scram-sha-256, see section 8)

-- 2. The table belongs to mf_tableowner, not to a flow login.
ALTER TABLE mf_leads OWNER TO mf_tableowner;

-- 3. Start from nothing: take away what PUBLIC (everyone) gets by default.
REVOKE ALL ON DATABASE <db> FROM PUBLIC;            -- removes CONNECT and TEMP (create temporary tables)
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON TABLE mf_leads FROM PUBLIC;
REVOKE ALL (lead_key, email, name, state, claimed_until, claim_token, attempts, crm_id, mail_sent,
            created_at, updated_at, alert_sent, alert_token, alert_until, alert_attempts)
       ON TABLE mf_leads FROM PUBLIC;               -- column-level too; whether a table-level REVOKE already does this is UNVERIFIED, the catalog check in section 5 decides

-- 4. Retire the old shared login (only after the P tests pass on the new logins; see section 7).
-- REVOKE ALL ON TABLE mf_leads FROM <old_flow_role>;
-- REVOKE ALL (<same 15 columns>) ON TABLE mf_leads FROM <old_flow_role>;
-- ALTER ROLE <old_flow_role> NOLOGIN PASSWORD NULL;   -- if it is a superuser or the administrator's own login: STOP, ask the owner

-- 5. Let the four logins in.
GRANT CONNECT ON DATABASE <db> TO mf_door, mf_sub, mf_recover, mf_alert;
GRANT USAGE   ON SCHEMA public TO mf_door, mf_sub, mf_recover, mf_alert;

-- 6. mf_door: S1-S4
GRANT INSERT (lead_key, email, name, state, claimed_until, claim_token, attempts) ON mf_leads TO mf_door;
GRANT SELECT (lead_key, state, claim_token)                                      ON mf_leads TO mf_door;

-- 7. mf_sub: S5-S9
GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;
GRANT UPDATE (crm_id, mail_sent, state, updated_at)          ON mf_leads TO mf_sub;

-- 8. mf_recover: S10-S11 (claim_token added in round 1: S10 returns it)
GRANT SELECT (lead_key, email, claim_token, state, claimed_until, attempts, created_at, mail_sent) ON mf_leads TO mf_recover;
GRANT UPDATE (claimed_until, claim_token, attempts, state, updated_at)                              ON mf_leads TO mf_recover;

-- 9. mf_alert: S12-S14
GRANT SELECT (lead_key, state, created_at, alert_sent, alert_token, alert_until, alert_attempts) ON mf_leads TO mf_alert;
GRANT UPDATE (alert_until, alert_token, alert_attempts, alert_sent, updated_at)                  ON mf_leads TO mf_alert;
```

Built-in functions: Postgres lets everyone run built-in functions such as `gen_random_uuid()` and `now()`. I do not revoke that (it would break the flows and I cannot safely do it for built-ins).

### Reason for each grant

| Grant | Reason |
|---|---|
| door INSERT on 7 columns | S1/S3 write exactly these; other columns fill from table defaults and need no grant |
| door SELECT on lead_key, state, claim_token | S1/S3 RETURNING all three; S2/S4 read state by lead_key. Note: this lets the door read claim_token of EVERY row, although its SQL text asks only for the row it just inserted (a column grant cannot say "own row"; see section 9) |
| sub SELECT on lead_key, claim_token, state, mail_sent | WHERE parts of S5 to S9; mail_sent in S6 and S9 |
| sub UPDATE on crm_id, mail_sent, state, updated_at | S5 crm_id; S6 mail_sent; S7 to S9 state; all set updated_at |
| recover SELECT on 8 columns | S10 reads lead_key, state, claimed_until, attempts, created_at and RETURNS claim_token and email; S11 reads mail_sent |
| recover UPDATE on 5 columns | S10 claimed_until, claim_token, attempts, updated_at; S11 state, updated_at |
| alert SELECT on 7 columns | S12 reads state, alert_sent, alert_until, created_at, alert_attempts and returns lead_key, alert_token; S13/S14 read alert_token, alert_sent |
| alert UPDATE on 5 columns | S12 alert_until, alert_token, alert_attempts; S13 alert_until; S14 alert_sent, updated_at |
| CONNECT on the database, USAGE on the schema | A login cannot run anything without them |
| REVOKE from PUBLIC (database, schema, table, columns) | Deny-by-default start: removes the built-in connect, temporary-table and schema rights everyone otherwise has |
| ALTER TABLE OWNER to mf_tableowner | The owner of a table has all rights on it; a flow login must not be the owner |

I intend nothing else to be granted: no DELETE, TRUNCATE, REFERENCES, TRIGGER, no other table, no sequence, no CREATE. The tests in section 5 are what proves that; this sentence does not.

### What each login can read and write after the change (columns of mf_leads)

| Login | Can read | Can write |
|---|---|---|
| mf_door | lead_key, state, claim_token | insert: lead_key, email, name, state, claimed_until, claim_token, attempts |
| mf_sub | lead_key, claim_token, state, mail_sent | update: crm_id, mail_sent, state, updated_at |
| mf_recover | lead_key, email, claim_token, state, claimed_until, attempts, created_at, mail_sent | update: claimed_until, claim_token, attempts, state, updated_at |
| mf_alert | lead_key, state, created_at, alert_sent, alert_token, alert_until, alert_attempts | update: alert_until, alert_token, alert_attempts, alert_sent, updated_at |
| mf_tableowner | everything (table owner) | everything; used only by hand |
| today's shared login | unknown | unknown |

## 5. Tests (all on the throwaway server; made-up rows only)

**A test passes only if the statement fails with SQLSTATE 42501 (the script prints the 5-character code, not just "error"), and the matching positive control succeeds.** A positive control is an allowed statement of the same shape run by the same login right before it; it proves the login can connect and the table exists, so a denial is not caused by something else (wrong password, missing table). Every denied statement runs inside a transaction that is rolled back.

**Test group R (read-only look at the current state; the only step allowed on the take's server before the video, because it changes nothing).** Replace `<old_flow_role>`:

```sql
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolcanlogin, rolconnlimit, rolvaliduntil FROM pg_roles WHERE rolname='<old_flow_role>';
SELECT r.rolname AS group_role, m.rolname AS member FROM pg_auth_members am JOIN pg_roles r ON r.oid=am.roleid JOIN pg_roles m ON m.oid=am.member WHERE m.rolname='<old_flow_role>' OR r.rolname='<old_flow_role>';
SELECT c.relname, pg_get_userbyid(c.relowner) AS table_owner, c.relacl FROM pg_class c WHERE c.relname='mf_leads';
SELECT a.grantee::regrole, a.privilege_type FROM pg_class c, aclexplode(c.relacl) a WHERE c.relname='mf_leads';          -- grantee 0 = PUBLIC; no rows can mean "defaults" (relacl is null)
SELECT att.attname, a.grantee, a.privilege_type FROM pg_attribute att, aclexplode(att.attacl) a WHERE att.attrelid='mf_leads'::regclass;   -- column-level grants
SELECT datname, datacl FROM pg_database;      -- who can connect to which database
SELECT nspname, nspacl FROM pg_namespace WHERE nspname='public';
SELECT has_column_privilege('<old_flow_role>','mf_leads',column_name,p) AS allowed, column_name, p FROM information_schema.columns, unnest(ARRAY['SELECT','INSERT','UPDATE']) p WHERE table_name='mf_leads';
```
Write down the result in the handover notes (masked: no passwords, no account numbers). If the old login is a superuser, or is the administrator's own login, stop: the owner decides (section 10).

**Test group M (the full matrix; expected rights of each login on each column).** S = SELECT allowed, I = INSERT allowed, U = UPDATE allowed. Every cell NOT listed (a dash) must be refused with 42501; every listed letter needs a positive control. 15 columns x 4 logins x 3 actions = 180 cells.

| Column | mf_door | mf_sub | mf_recover | mf_alert |
|---|---|---|---|---|
| lead_key | S I | S | S | S |
| email | I | - | S | - |
| name | I | - | - | - |
| state | S I | S U | S U | S |
| claimed_until | I | - | S U | - |
| claim_token | S I | S | S U | - |
| attempts | I | - | S U | - |
| crm_id | - | U | - | - |
| mail_sent | - | S U | S | - |
| created_at | - | - | S | S |
| updated_at | - | U | U | U |
| alert_sent | - | - | - | S U |
| alert_token | - | - | - | S U |
| alert_until | - | - | - | S U |
| alert_attempts | - | - | - | S U |

How to run each cell: S = `SELECT <col> FROM mf_leads LIMIT 1`; I = `INSERT INTO mf_leads(lead_key,<col>) VALUES ('t1',<valid value>)` (for `lead_key` itself insert only that column); U = `UPDATE mf_leads SET <col>=<col> WHERE false`. Run each as the login, rollback after. The script is generated from this table so the matrix and the grants cannot drift apart; a second check compares it with `has_column_privilege(...)` for the same 180 cells. Whole-statement checks for every login: `SELECT *` (must be refused, needs all columns); `DELETE FROM mf_leads`; `TRUNCATE mf_leads`; `INSERT ... ON CONFLICT (lead_key) DO UPDATE SET state='done'` (door must be refused: no UPDATE right). Expected results of `INSERT` for logins with no I at all (sub, recover, alert): refused with 42501.

**Other tests (each with 42501 unless stated; `3D000`/`28000`-type login failures are noted where I believe the code differs, UNVERIFIED):**

| Id | Login | Test | Why |
|---|---|---|---|
| T1 | each of the 4 | `CREATE TABLE`, `CREATE TEMP TABLE`, `CREATE SCHEMA`, `DROP TABLE mf_leads`, `ALTER TABLE mf_leads ...`, `COMMENT ON`, `CREATE ROLE`, `COPY ... PROGRAM`, `COPY mf_leads TO '/path'`, `SELECT` on any other table | No structure change and no reach beyond the table (TEMP is closed by the PUBLIC revoke) |
| T2 | each of the 4 | `SET ROLE` to each other login of the list and to mf_tableowner | No login hopping (expected to fail because no memberships exist; the error code may be 42501 or another, record it) |
| T3 | a fresh login with no grants (`mf_nobody`, made for the test) | connect to our database; connect to `template1`, `postgres` and every other database listed in `pg_database` | Shows whether PUBLIC connect rights are really gone, and which other databases anyone can still open (report; changing other databases needs the owner's yes) |
| T4 | the old shared login | after retirement: cannot log in at all (expected: login refused); cannot read or write mf_leads; test also that its n8n credential password no longer works | Retirement proof |
| T5 | catalog | `pg_class.relowner` of mf_leads equals mf_tableowner; no PUBLIC entry in the table or column ACL (aclexplode queries of group R); no flow login is a member of any group | Owner and PUBLIC check |
| T6 | each of the 4 | open `CONNECTION LIMIT + 1` connections: the extra one is refused (believed code 53300, UNVERIFIED) | Limit is real |
| T7 | mf_door, mf_sub | burst: 50 parallel claim-inserts / sub updates through a pool capped at the credential maximum (section 8) | No lead is refused because of the limit; calls wait instead |
| T8 | n8n credentials | after expiry date passes (set a short test date), the login is refused; after the password is changed in Postgres and in n8n the flows work again | Rotation drill (N1) |
| W | wide spots left (section 9) | mf_door `INSERT ... state='done'` and `attempts=99`: EXPECTED TO SUCCEED, recorded as a known wide spot; mf_sub `UPDATE state` on a row whose claim token it did not use: EXPECTED TO SUCCEED | Makes the remaining wide spots visible instead of hidden |
| P1 to P14 | the login that owns statement Sn | run statement Sn, with made-up rows in the right start state, as that login; the result must equal today's (same rows returned, same new state) | Positive tests: the split must not break a flow. P1/P3 test insert and RETURNING; P10/P12 test the locking select; P1 must also run with the real `queryReplacement` shape ($1 to $4 values) |
| X | n8n | after F-011 moves n8n to Postgres, repeat T1 to read n8n's own tables as each flow login: refused | Matches test T-ROLES in F-041; cannot run until F-011 exists |

Test groups M, T, W need only Postgres. Test group P also needs the real flows run end to end (the re-test, section 7).

## 6. Where to build and test it (throwaway wording)

- Roles belong to the whole Postgres server, not to one database. A "copy of the take's database" on the same server would still create these logins on the take's server. So build and test only on a separate throwaway server: a fresh Postgres container or a new data folder on another port, with made-up rows. Never `CREATE ROLE` on the take's server for a test.
- `CREATE DATABASE ... TEMPLATE` copies only data, needs no one connected to the source, and does not isolate logins, so it is not the way to get a safe copy.
- Do not run it while filming: the throwaway server competes with the take for the laptop's processor.
- Use the same Postgres major version as the take (found with `SHOW server_version;`, a read-only query).

## 7. Order of the real change (after the video)

1. On the throwaway server: sections 4 and 5 until every test result matches; fix grants; keep the raw output.
2. On the take's server (after the video, with the owner's yes): back up; run group R; run section 4 steps 1 to 3 and 5 to 9; create 4 n8n credentials with pool maximum set (section 8).
3. Edit the 8 flow files' credential names, re-import, run the re-test (all four flows end to end: new lead, repeat lead, stuck lead, failed mail, alert).
4. Only now retire the old login: section 4 step 4, rotate or null its password, delete the n8n credential `n8n-publish-pg`, record the date. Rollback until this step: point the credentials back to the old login.
5. Run T4 and T5 on the real server.

What takes effect on the take: reading this file and running group R have no effect. Building logins and tests on a throwaway server is safe for the take if it does not run during filming. Everything in steps 2 to 4 changes what the flows run on and is NOT safe before the video.
Estimated work (agent clock; my estimate, not measured): about 1 hour for SQL and test script, 1 hour on the throwaway server, 1 hour for the 8 edits plus the re-test. The finding is rated Nit (after the video).

## 8. Open Postgres and n8n facts (UNVERIFIED; the manual could not be fetched, so these are from memory)

| Fact | Manual page I would check | What breaks if wrong |
|---|---|---|
| `INSERT ... ON CONFLICT DO NOTHING RETURNING` needs only INSERT on the written columns and SELECT on returned columns (and maybe on the conflict-check column) | postgresql.org/docs/current/sql-insert.html (Notes, ON CONFLICT) | Both doors accept no leads. Covered by P1/P3 |
| `FOR UPDATE SKIP LOCKED` needs UPDATE on at least one column besides SELECT | .../sql-select.html (The Locking Clause) | Recovery cannot take over leads or send alerts. Covered by P10/P12 |
| `gen_random_uuid()` is built in from Postgres 13; before that it needs the extension pgcrypto | .../functions-uuid.html | Door insert fails on old Postgres. Check `SHOW server_version` |
| A table-level REVOKE also removes column-level grants (my memory) versus does not (round-1 reviewer, also from memory) | .../sql-revoke.html, .../ddl-priv.html | A leftover PUBLIC column grant. I revoke at both levels and test T5 |
| `REASSIGN OWNED`/`ALTER TABLE OWNER` moves table rights as intended; a login with NOLOGIN is refused with an authorization error | .../sql-reassign-owned.html, .../sql-alterrole.html | Retirement steps incomplete. Covered by T4/T5 |
| `CONNECTION LIMIT` counts open sessions of that login; the 7th is refused (code 53300 believed) | .../sql-createrole.html | Wrong limit refuses leads or lets pools grow. Covered by T6/T7 |
| Passwords stored as scram-sha-256 (default since Postgres 14) and `pg_hba.conf` does not say `trust` for these logins | .../auth-password.html, .../auth-pg-hba-conf.html | Passwords not enforced. Not read: `pg_hba` is unchecked |
| n8n's Postgres credential has a "maximum number of connections" setting and each credential gets its own pool; queries wait when the pool is full | n8n docs, Postgres credentials page (not fetched) | Leads refused at busy moments |

Connection limits (round-1 M6): role limits are 6, 6, 3, 3 and the matching n8n credential pool maximums must be one lower (5, 5, 2, 2), so a full pool never exceeds the role limit and extra queries wait in n8n instead of being refused. One spare connection allows for a reconnect after n8n restarts. These numbers are my guesses; test T7 settles them.

Passwords (round-1 N1): each flow login gets `VALID UNTIL` (a date, for example 90 days out) and a rotation note: change in Postgres and in n8n together, drill in T8. Risk: after the date, flows fail; put the date in the calendar. Stated exception for the take only: if the owner prefers no expiry for the video, say so in writing; the logins still get long random passwords stored only in n8n.

## 9. What is still too wide (review of my own proposal)

1. **Rows and values are not limited by grants.** mf_door can insert any state the table allows (for example `done`) and any `attempts`; mf_sub can set state on any row it can see, limited only by the `WHERE claim_token=...` in the SQL text. Test group W makes this visible. Closing it needs a trigger or a database function (a small amount of our own code on the claim path). By the CODE-LAST rule: rung table below. Status: needs the owner's decision (section 10).
2. mf_door can read `claim_token` of every row (column grants cannot say "own row"), wording corrected in the grant table.
3. mf_recover reads `email` of every row (S10 needs it to run the sub-workflow again). On the take the data is made up; on a client build it is a read right that needs a masking decision.
4. PUBLIC still holds execute rights on built-in functions (section 4), and other databases on the same server may still be open to everyone (T3 reports; not changed here).
5. Four passwords are only as safe as n8n's own credential store: one n8n user who can read all four credentials undoes the split (F-011).
6. The SMTP credential (`mf-mail-smtp`) is out of scope; F-010 and F-030 still stand for it.
7. Not covered: a human read-only login, a backup login, network rules (who can reach the database port), `pg_hba.conf` (not read).

| Component (CODE-LAST rung table) | Need | Rung tried | Evidence | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Four logins with column grants | one identity per function | Postgres's own grants (standard feature) | Statement text read; grants not yet run: UNVERIFIED | nothing | KEEP as configuration (CUT-TO-CONFIG+GLUE) |
| 4 n8n credentials and 8 file edits | use the logins | n8n credential feature | read from the flow files | nothing | CUT-TO-CONFIG+GLUE |
| Trigger or function to limit state and attempts values | row and value limits | Postgres CHECK/trigger (standard feature, our few lines) | none yet; no incident evidence | a value limit on the claim path | NOT PROPOSED; owner decides after test W |

## 10. What I could not fix, and why (nothing is hidden as "known limitation")

| Item | Class | Next step |
|---|---|---|
| Postgres facts in section 8 are unverified | impossible now (manual fetch refused with HTTP 403; no Postgres available) | The lead fetches the pages listed, or runs groups M, P and T on a throwaway server; then update this file |
| Today's rights of the old login are unknown; it may be a superuser or the administrator's login | needs the owner (only he can look at the laptop and decide) | Owner or lead runs group R and sends the masked result |
| Whether another flow, script or person also uses `n8n-publish-pg` | needs the owner | Owner checks n8n's credential list and the laptop notes before step 4 of section 7 |
| Wide spots in section 9, item 1 (trigger or function) | needs the owner (a decision on extra code) | Owner decides after test W is run |
| Revoking PUBLIC connect on other databases of the same server | needs the owner | Owner decides after T3 |
| This round-2 version has had no independent review | needs the lead (the review step runs from outside this file) | Lead runs the EGM review of this file |

Not checked: any SQL against a real Postgres; whether the current login is a superuser or owner; the Postgres version; `pg_hba.conf` and network access; whether the database setup exists outside this repository; n8n's pool behaviour; flow folders v3 and v4 and the desk-* workflows; non-Postgres nodes that might call a database; studio rule numbers (not present in this repository).
