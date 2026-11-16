# ROLES-PROPOSAL: separate database logins for the lead-intake flows (queue item F6, finding F-010)

**DANGER, READ FIRST: if one of these database rights is wrong, the flows stop saving new leads, and the recorded video take would fail. Nothing in this file has been run against a database, so no right in it is proven. Do nothing from this file to the video take's database or flows before the video is recorded.**

STATUS: PROPOSAL ONLY. Written, never run. Version 3 (round-2 fixes). It has not passed a third review.

## What I need from the owner (5 lines)

1. Confirm in writing: nothing in this file touches the video take's database or flows before the video.
2. After the video: say yes or no to running the read-only look (group L in section 5) on the take's database. It only reads the database's own lists and changes nothing. Send me the masked result.
3. Say whether the old shared login may be switched off after the new logins work (section 7, step 7). If another flow, script or person uses it, say so first.
4. After the wide-spot checks (group WS) have been run, decide whether to add a small trigger on the lead path (section 9, item 1; extra code of ours, so it is your decision).
5. Decide who runs the change on the take's server: it needs the database administrator's login (section 7). I do not run it.

## 0. Plain words used in this file

- **n8n**: the workflow tool that runs the flows. **Flow**: one n8n workflow file. **Credential** (n8n word): a saved database login inside n8n (name plus password). **Postgres**: the database. **Role**: a database login with its own list of allowed actions; I say "login". **Grant**: one entry on that list. **Column-level grant**: the entry names exact columns of a table, not the whole table. **PUBLIC**: Postgres's built-in group that every login on the same server belongs to (not "the outside world").
- **The video take**: the one recorded run of the demo video. **The laptop**: the machine that runs n8n and the take's database. **Throwaway server**: a separate, empty Postgres used only for tests (section 6).
- **Door**: a flow that receives a lead. Two doors: the form door (file `mf-form.json`) and the webhook door (`mf-hook.json`; a webhook is a web address another system calls). **Sub-workflow** (`mf-sub-crm-mail.json`): the flow the doors call to save the lead in the customer-contact system (the CRM) and send the lead's mail. **Recovery** (`mf-recovery.json`): the flow that runs on a timer, takes over leads that got stuck, and sends alert mails.
- Four things were called "claim" in the old text. Here: **claim insert** = the first save of a new lead (the insert decides who owns the lead). **Claim token** (column `claim_token`) = a random text that proves which run owns the lead right now. **Take over** = recovery giving a stuck lead a new claim token. **Alert claim** = recovery reserving a lead for an alert mail (column `alert_token`). **Alert** = mail telling a person a lead ended in `failed` or `unknown`.
- **Words inside the SQL**: `RETURNING` = the statement hands back columns of the row it just wrote, which counts as reading them. `ON CONFLICT DO NOTHING` = if the lead already exists, do nothing. `FOR UPDATE SKIP LOCKED` = lock the chosen rows and skip rows another run has locked. `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE` = the login cannot become an administrator, create databases or create logins. `NOBYPASSRLS` = the login cannot skip row-level rules (none exist here; this is a safety margin). `NOINHERIT` = a login does not automatically gain the rights of groups it belongs to (none here; a margin). `CONNECTION LIMIT n` = at most n open sessions for this login. `VALID UNTIL` = the password stops working on that date (open sessions are not closed by it). `scram-sha-256` = the modern way Postgres stores and checks passwords. `TEMP` = the right to create temporary tables. `SQLSTATE` = Postgres's 5-character error code; `42501` means "permission denied".
- **Names of tests**: group **L** (the read-only look), group **MX** (the full rights matrix), **FW1 to FW14** (flow-works tests: each statement still does its job), **C1 to C8** (other checks), group **WS** (wide-spot tests). "Earlier review" means review round 1 of this file.
- "CODE-LAST" is the studio rule that our own code is the last choice; "EGM" is the studio's review process. Finding ids (F-010, F-011, F-030, F-041) are rows in the flows-audit findings list; they are labels only. `mf_` is the prefix of the existing table `mf_leads`. **Owner** always means the studio owner; the database object's owner is called **table owner**.

## 1. What I established, and how sure I am

- No file in the repository creates a Postgres login or a grant (I searched `handover` outside `flows-audit` for the words CREATE ROLE and GRANT: no hit). So today's rights of the login behind the n8n credential `n8n-publish-pg` are unknown, and the login's real name may differ from the credential's name.
- The table the v5 flows need is `handover/demo/n8n-flows-v4/mf_leads.sql` (15 columns, including four alert columns). The older `handover/demo/n8n-flows/mf_leads.sql` has 11 columns and no alert columns, so it does not fit v5.
- Folders: `handover/demo/n8n-flows-real-v5` and `handover/demo/n8n-flows-film-v5` (4 flow files each). In each, 14 nodes are of type `n8n-nodes-base.postgres`, 28 in all. The script `roles-coverage-check/check_grants_cover_queries.py` (section 2) reads their `query` field. By that text search, every such node uses the credential `n8n-publish-pg` and operation `executeQuery` (raw SQL), none of the 28 queries contains DELETE, TRUNCATE, DROP, ALTER, CREATE, COPY, GRANT, REVOKE or SET ROLE, and none names a table other than `mf_leads`. The film and real folders were compared by an earlier script (not saved); I did not re-compare them in this round, so "identical" is not claimed here. The script runs on both folders.
- Not covered: SQL built in code nodes or expressions outside the `query` field; other node types that might call a database.

## 2. Every Postgres statement (table `mf_leads`)

Legend: Reads = columns the statement reads anywhere (WHERE, subquery, right side of SET, RETURNING). Writes = columns it sets or inserts. S1 to S14 are statement numbers (not test ids).

| # | Flow (file) | Node | Action | Writes | Reads | Reason |
|---|---|---|---|---|---|---|
| S1 | Form door | Claim | INSERT ... ON CONFLICT (lead_key) DO NOTHING RETURNING | lead_key, email, name, state, claimed_until, claim_token, attempts (other columns take table defaults) | lead_key, claim_token, state (RETURNING); lead_key (conflict check, UNVERIFIED) | The claim insert: first writer of a lead_key wins, a repeat does nothing. |
| S2 | Form door | Stored | SELECT | none | state, lead_key | When the insert did nothing (repeat lead), tell the caller the lead's state. |
| S3 | Webhook door | Claim | same text as S1 | same | same | Same job for the webhook door. |
| S4 | Webhook door | Stored | same text as S2 | none | state, lead_key | Same. |
| S5 | Sub-workflow | SetCrmId | UPDATE ... RETURNING | crm_id, updated_at | lead_key, claim_token, state | Record the CRM record id, only for the holder of the claim token while state is processing. |
| S6 | Sub-workflow | MailClaim | UPDATE ... RETURNING | mail_sent, updated_at | lead_key, claim_token, mail_sent, state | Mark the lead mail as sent exactly once. |
| S7 | Sub-workflow | MarkDone | UPDATE ... RETURNING | state, updated_at | lead_key, claim_token, state | Finish the lead. |
| S8 | Sub-workflow | MarkUnknownA | UPDATE ... RETURNING | state, updated_at | lead_key, claim_token, state | Say "unknown" when the outcome cannot be told. |
| S9 | Sub-workflow | MarkUnknownB | UPDATE ... RETURNING | state, updated_at | lead_key, claim_token, state, mail_sent | Same, when the mail may have gone out. |
| S10 | Recovery | ClaimStuck | UPDATE ... WHERE lead_key IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING lead_key, email, claim_token | claimed_until, claim_token, attempts, updated_at | lead_key, state, claimed_until, attempts, created_at; RETURNING lead_key, email, claim_token | Take over leads whose claim ran out (at most 5, 3 tries each). It hands back the NEW claim token and the email so the sub-workflow can run again. (Earlier review found the first version of this table omitted claim_token here.) |
| S11 | Recovery | MarkFailed | UPDATE ... RETURNING lead_key | state, updated_at | state, claimed_until, attempts, mail_sent, lead_key | Close leads that used up their tries (failed, or unknown if the mail was sent). |
| S12 | Recovery | AlertClaim | UPDATE ... WHERE lead_key IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING lead_key, state, alert_token | alert_until, alert_token, alert_attempts | lead_key, state, alert_sent, alert_until, created_at, alert_attempts (in `alert_attempts+1`); RETURNING lead_key, state, alert_token | Reserve up to 5 leads that need an alert. |
| S13 | Recovery | AlertBackoff | UPDATE ... RETURNING lead_key | alert_until | lead_key, alert_token, alert_sent, alert_attempts | After a failed alert mail, wait before the next try. |
| S14 | Recovery | AlertMark | UPDATE ... RETURNING lead_key | alert_sent, updated_at | lead_key, alert_token, alert_sent | Mark the alert as sent. |

S1 and S3 call the built-in `gen_random_uuid()`. These readings come from the query text as I read it; the script below is a second reading by a rough text parser.

**Coverage check (text only, no database).** Run from `handover`: `python3 -I flows-audit/roles-coverage-check/check_grants_cover_queries.py demo/n8n-flows-real-v5 demo/n8n-flows-film-v5`. On the grants of this version it printed "covered" for all 28 nodes and `TOTAL UNCOVERED OR UNMAPPED: 0` (exit 0). With `claim_token` removed from the recovery SELECT grant (a copy of the script in the scratchpad), it printed UNCOVERED for ClaimStuck and exit status 1, so it does catch that one fault. The grants inside the script are a copy of section 4: if section 4 changes, change the script. It is a rough text parser and can miss unusual SQL; it never ran on a database. The real proof is groups MX and FW.

## 3. Proposed logins (one function per login)

Four flow logins plus one table-owner login that no flow uses. Names are placeholders.

| Login | Function | Statements | n8n credential |
|---|---|---|---|
| mf_tableowner | Owns the table; used only by hand for create/migrate. NOLOGIN (nobody logs in as it); the database administrator reaches it with `SET ROLE` (to be confirmed on the throwaway server). | none | none |
| mf_door | The two doors: save a new lead and read its state | S1 to S4 | `n8n-publish-pg-door` (new) |
| mf_sub | Sub-workflow: record CRM id, mail sent, final state | S5 to S9 | `n8n-publish-pg-sub` (new) |
| mf_recover | Recovery: take over stuck leads, close exhausted ones | S10, S11 | `n8n-publish-pg-recover` (new) |
| mf_alert | Alert bookkeeping only (alert claim, wait, mark) | S12 to S14 | `n8n-publish-pg-alert` (new) |

No read-only login for people is proposed. n8n's own storage login (F-011) is a separate fifth identity on a separate database or schema and is not defined here.

### What the split costs

- n8n picks a credential per node, so 14 nodes can use 4 credentials (recovery uses `-recover` on ClaimStuck and MarkFailed, `-alert` on the three Alert nodes).
- Cost: 4 credentials created in n8n (each password typed by hand into n8n, never into a file); in each of the 8 flow files the `credentials.postgres` entry of each Postgres node changes from `n8n-publish-pg` to the matching new name; the 8 files are re-imported. That is a flow change, so it needs the full re-test. It is not a config-only change.
- **Option B (two logins, not proposed).** It would put the claim and alert functions under one identity, which breaks the studio rule "one identity per function". Using it needs the owner's explicit yes with the extra rights written out: the merged door-and-sub login would hold INSERT on 7 columns, SELECT on 5, UPDATE on 4, so a door could change the state of any existing lead; the merged recovery-and-alert login would hold SELECT on 10 columns and UPDATE on 8, so the claim step could rewrite alert columns. No yes exists.

## 4. SQL (UNTESTED; throwaway server only until the owner says otherwise)

Two parts. **Part A only adds** logins and grants; it takes nothing away from the old login. **Part B removes rights** (owner change, PUBLIC revokes, old login) and is a change window (section 7). Both parts start with a guard that stops the script unless the person running it has typed a marker setting first.

```sql
-- ############################################################################
-- UNTESTED.  NOT BEFORE THE VIDEO.  Throwaway server first (section 6).
-- Run by the database administrator's own login, by hand. Not by an agent.
-- Roles belong to the whole server, not to one database; the REVOKE lines in
-- part B remove rights from EVERY login on the server, not just ours.
-- Passwords: set by hand with psql's \password or in n8n's form. Never in this file.
-- <db>, <old_flow_role>, <old_table_owner> are placeholders. <date> = a real expiry date.
-- To run: first type   SET mf.throwaway = 'yes';   (throwaway server)
--         or           SET mf.throwaway = 'owner-yes-and-backup-and-group-L-done';  (take's server, after the video only)
-- ############################################################################
\set ON_ERROR_STOP on
DO $$ BEGIN
  IF current_setting('mf.throwaway', true) IS DISTINCT FROM 'yes'
     AND current_setting('mf.throwaway', true) IS DISTINCT FROM 'owner-yes-and-backup-and-group-L-done' THEN
    RAISE EXCEPTION 'STOP: marker mf.throwaway not set; read section 7 of ROLES-PROPOSAL.md';
  END IF;
END $$;

-- ===== PART A: add only (does not change the old login's rights) =====
-- A1. Logins. No superuser, no create-role, no create-db, no bypass of row rules.
CREATE ROLE mf_tableowner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
CREATE ROLE mf_door    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 6 VALID UNTIL '<date>';
CREATE ROLE mf_sub     LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 6 VALID UNTIL '<date>';
CREATE ROLE mf_recover LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 3 VALID UNTIL '<date>';
CREATE ROLE mf_alert   LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 3 VALID UNTIL '<date>';
-- (set each password by hand: \password mf_door ... ; scram-sha-256, see section 8)

-- A2. Let the four logins in.
GRANT CONNECT ON DATABASE <db> TO mf_door, mf_sub, mf_recover, mf_alert;
GRANT USAGE   ON SCHEMA public TO mf_door, mf_sub, mf_recover, mf_alert;

-- A3. mf_door: S1-S4
GRANT INSERT (lead_key, email, name, state, claimed_until, claim_token, attempts) ON mf_leads TO mf_door;
GRANT SELECT (lead_key, state, claim_token)                                      ON mf_leads TO mf_door;
-- A4. mf_sub: S5-S9
GRANT SELECT (lead_key, claim_token, state, mail_sent)       ON mf_leads TO mf_sub;
GRANT UPDATE (crm_id, mail_sent, state, updated_at)          ON mf_leads TO mf_sub;
-- A5. mf_recover: S10-S11
GRANT SELECT (lead_key, email, claim_token, state, claimed_until, attempts, created_at, mail_sent) ON mf_leads TO mf_recover;
GRANT UPDATE (claimed_until, claim_token, attempts, state, updated_at)                              ON mf_leads TO mf_recover;
-- A6. mf_alert: S12-S14
GRANT SELECT (lead_key, state, created_at, alert_sent, alert_token, alert_until, alert_attempts) ON mf_leads TO mf_alert;
GRANT UPDATE (alert_until, alert_token, alert_attempts, alert_sent, updated_at)                  ON mf_leads TO mf_alert;

-- ===== PART B: removes rights; only inside the change window of section 7 step 8 =====
-- Before B: save the group L output (it is the re-grant record). STOP if the old login is
-- a superuser, the administrator's own login, or a member of ANY group (group L shows this): ask the owner.
-- B1. The table belongs to mf_tableowner, not to a flow login.
--     (Needs a superuser, or a login that is a member of both the old owner and mf_tableowner and has CREATE on the schema.)
ALTER TABLE mf_leads OWNER TO mf_tableowner;
-- B2. Take away what PUBLIC (every login on the server) gets by default.
REVOKE ALL ON DATABASE <db> FROM PUBLIC;            -- removes CONNECT and TEMP
REVOKE ALL ON SCHEMA public FROM PUBLIC;            -- includes CREATE on the schema
REVOKE ALL ON TABLE mf_leads FROM PUBLIC;
REVOKE ALL (lead_key, email, name, state, claimed_until, claim_token, attempts, crm_id, mail_sent,
            created_at, updated_at, alert_sent, alert_token, alert_until, alert_attempts)
       ON TABLE mf_leads FROM PUBLIC;               -- column level too; whether the table-level REVOKE already does this is UNVERIFIED
-- B3. Tables made LATER by the table owner must not be open to PUBLIC either.
ALTER DEFAULT PRIVILEGES FOR ROLE mf_tableowner IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC;
-- (group L also lists existing default privileges of the old login: pg_default_acl)
-- B4. Retire the old shared login (only after the flows have run on the new logins; section 7).
REVOKE ALL ON TABLE mf_leads FROM <old_flow_role>;
REVOKE ALL (lead_key, email, name, state, claimed_until, claim_token, attempts, crm_id, mail_sent,
            created_at, updated_at, alert_sent, alert_token, alert_until, alert_attempts)
       ON TABLE mf_leads FROM <old_flow_role>;
REVOKE CREATE ON SCHEMA public FROM <old_flow_role>;
ALTER ROLE <old_flow_role> NOLOGIN PASSWORD NULL;
-- Open sessions of the old login stay open until closed: list them with
--   SELECT pid, usename, state FROM pg_stat_activity WHERE usename='<old_flow_role>';
-- and have the administrator end them with pg_terminate_backend(pid).

-- ===== PART B ROLLBACK (re-grant what group L recorded; the text below is the shape, the recorded ACL is the truth) =====
-- ALTER TABLE mf_leads OWNER TO <old_table_owner>;
-- ALTER ROLE <old_flow_role> LOGIN;   -- then set its password again by hand
-- GRANT <the exact privileges recorded in relacl> ON TABLE mf_leads TO <old_flow_role>;
-- GRANT CONNECT, TEMP ON DATABASE <db> TO PUBLIC;   GRANT USAGE ON SCHEMA public TO PUBLIC;   -- only if group L showed them
```

Built-in functions: Postgres lets everyone run built-ins such as `gen_random_uuid()` and `now()`. I do not revoke that (it would break the flows).

### Reason for each grant

| Grant | Reason |
|---|---|
| door INSERT on 7 columns | S1/S3 write exactly these; other columns fill from table defaults and need no grant |
| door SELECT on lead_key, state, claim_token | S1/S3 RETURNING all three; S2/S4 read state by lead_key. This lets the door read claim_token of EVERY row, although its SQL asks only for the row it just inserted (section 9) |
| sub SELECT on lead_key, claim_token, state, mail_sent | WHERE parts of S5 to S9; mail_sent in S6 and S9 |
| sub UPDATE on crm_id, mail_sent, state, updated_at | S5 crm_id; S6 mail_sent; S7 to S9 state; all set updated_at |
| recover SELECT on 8 columns | S10 reads lead_key, state, claimed_until, attempts, created_at and RETURNS claim_token and email; S11 reads mail_sent |
| recover UPDATE on 5 columns | S10 claimed_until, claim_token, attempts, updated_at; S11 state, updated_at |
| alert SELECT on 7 columns | S12 reads state, alert_sent, alert_until, created_at, alert_attempts and returns lead_key, alert_token; S13/S14 read alert_token, alert_sent |
| alert UPDATE on 5 columns | S12 alert_until, alert_token, alert_attempts; S13 alert_until; S14 alert_sent, updated_at |
| CONNECT on the database, USAGE on the schema | A login cannot run anything without them |
| REVOKE from PUBLIC (database, schema, table, columns, default privileges) | Deny-by-default start: removes the built-in connect, temporary-table and schema rights everyone otherwise has |
| ALTER TABLE OWNER to mf_tableowner | The owner of a table has all rights on it; a flow login must not be the owner |

I intend nothing else to be granted: no DELETE, TRUNCATE, REFERENCES, TRIGGER, no other table, no sequence, no CREATE. The tests in section 5 are what test that; this sentence is not proof.

### What each login can read and write after the change (columns of mf_leads)

| Login | Can read | Can write |
|---|---|---|
| mf_door | lead_key, state, claim_token | insert: lead_key, email, name, state, claimed_until, claim_token, attempts |
| mf_sub | lead_key, claim_token, state, mail_sent | update: crm_id, mail_sent, state, updated_at |
| mf_recover | lead_key, email, claim_token, state, claimed_until, attempts, created_at, mail_sent | update: claimed_until, claim_token, attempts, state, updated_at |
| mf_alert | lead_key, state, created_at, alert_sent, alert_token, alert_until, alert_attempts | update: alert_until, alert_token, alert_attempts, alert_sent, updated_at |
| mf_tableowner | everything (table owner) | everything; used only by hand |
| today's shared login | unknown | unknown |

## 5. Tests (throwaway server; made-up rows only; every error code below is from memory, UNVERIFIED)

**Pass rule.** Each test row names the exact SQLSTATE expected. The script prints the 5-character code it got. A test passes only if the printed code equals the expected code AND the positive control succeeded. A different code is a failure to investigate (it may be my memory that is wrong, in which case this file is corrected), never a silent pass. Every denied statement runs in a transaction that is rolled back.

**Positive control** = an allowed statement of the same kind, run by the same login in the same session just before the denied one. It proves the login can connect and the table exists, so the denial is not caused by something else. Where a login has no allowed statement of that kind at all (for example the INSERT of mf_sub), the control is: (a) a successful allowed statement of another kind in the same session, and (b) `has_column_privilege(login, 'mf_leads', column, 'INSERT')` returning false.

**Group L (read-only look; the only step ever allowed on the take's server, and only after the video with the owner's yes, because it changes nothing).** Replace `<old_flow_role>`:

```sql
SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolcanlogin, rolconnlimit, rolvaliduntil FROM pg_roles WHERE rolname='<old_flow_role>';
SELECT r.rolname AS group_role, m.rolname AS member FROM pg_auth_members am JOIN pg_roles r ON r.oid=am.roleid JOIN pg_roles m ON m.oid=am.member WHERE m.rolname='<old_flow_role>' OR r.rolname='<old_flow_role>';   -- any row: STOP, ask the owner
SELECT c.relname, pg_get_userbyid(c.relowner) AS table_owner, c.relacl FROM pg_class c WHERE c.relname='mf_leads';
SELECT a.grantee::regrole, a.privilege_type FROM pg_class c, aclexplode(c.relacl) a WHERE c.relname='mf_leads';          -- grantee 0 = PUBLIC; no rows can mean "defaults" (relacl is null)
SELECT att.attname, a.grantee, a.privilege_type FROM pg_attribute att, aclexplode(att.attacl) a WHERE att.attrelid='mf_leads'::regclass;   -- column-level grants
SELECT datname, pg_get_userbyid(datdba) AS db_owner, datacl FROM pg_database;      -- who can connect to which database
SELECT nspname, pg_get_userbyid(nspowner) AS schema_owner, nspacl FROM pg_namespace WHERE nspname='public';   -- schema owner: if it is the old login, the owner decides
SELECT pg_get_userbyid(defaclrole) AS for_role, defaclnamespace::regnamespace, defaclobjtype, defaclacl FROM pg_default_acl;   -- default privileges
SELECT has_column_privilege('<old_flow_role>','mf_leads',column_name,p) AS allowed, column_name, p FROM information_schema.columns, unnest(ARRAY['SELECT','INSERT','UPDATE']) p WHERE table_name='mf_leads';
```
Write the result in the handover notes (masked: no passwords, no account numbers). It is also the re-grant record for the Part B rollback. If the old login is a superuser, is the administrator's own login, or is in any group, stop: the owner decides (section 10).

**Group MX (the full matrix; expected rights of each login on each column).** S = SELECT allowed, I = INSERT allowed, U = UPDATE allowed. A dash = that action must be refused with SQLSTATE `42501`. 15 columns x 4 logins x 3 actions = 180 cells.

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

How to run each cell (the script is generated from this table so matrix and grants cannot drift; run each as the login; rollback after):
- **S cell**: `SELECT <col> FROM mf_leads LIMIT 1`. Positive control: any S cell of the same login. For a refused S cell the control is an allowed S cell of that login.
- **U cell**: `UPDATE mf_leads SET <col> = DEFAULT WHERE false`. This form needs the UPDATE right on the column but does not read the column, so an UPDATE-only column (crm_id, updated_at for sub; updated_at for others) is testable. (An earlier text used `SET col = col`, which also needs SELECT and would wrongly fail UPDATE-only cells.) Whether `WHERE false` still checks the right is UNVERIFIED; it is also checked with `has_column_privilege(login,'mf_leads',col,'UPDATE')`.
- **I cell**: only mf_door has any INSERT right. For mf_door: `INSERT INTO mf_leads(lead_key, <col>) VALUES ('t1', <valid value>)` (for `lead_key` itself insert only that column). For mf_sub, mf_recover and mf_alert an INSERT that names `lead_key` would be denied because of `lead_key`, not because of the column under test, so their 15 I cells are NOT run as inserts; they are checked with `has_column_privilege(login,'mf_leads',col,'INSERT')` = false, plus a plain `INSERT INTO mf_leads(lead_key) VALUES ('t1')` refused with `42501`.
- A second check compares all 180 cells with `has_column_privilege(...)`.
- Whole-statement checks for every login, all `42501`: `SELECT *`; `DELETE FROM mf_leads`; `TRUNCATE mf_leads`; `INSERT ... ON CONFLICT (lead_key) DO UPDATE SET state='done'` (door has no UPDATE right).

**Other checks.** "Expected" is the SQLSTATE I believe Postgres returns; UNVERIFIED.

| Id | Login | Test | Expected SQLSTATE | Why |
|---|---|---|---|---|
| C1 | each of the 4 | `CREATE TABLE`, `CREATE TEMP TABLE`, `CREATE SCHEMA`, `DROP TABLE mf_leads`, `ALTER TABLE mf_leads ...`, `COMMENT ON`, `CREATE ROLE`, `COPY ... PROGRAM`, `COPY mf_leads TO '/path'`, `SELECT` on any other table | `42501` for each | No structure change and no reach beyond the table (TEMP is closed by the PUBLIC revoke; this row only passes after Part B) |
| C2 | each of the 4 | `SET ROLE` to each other login and to mf_tableowner | `42501` | No login hopping (no memberships exist) |
| C3 | a fresh login with no grants (`mf_nobody`, made for the test) | connect to our database; to `template1`, `postgres` and every other database in `pg_database` | `42501` for our database after Part B (no CONNECT right); for the others: record what happens, do not expect | Shows which other databases anyone can still open (report; changing other databases needs the owner's yes) |
| C4 | the old shared login | after retirement: login is refused; cannot read or write mf_leads; its old n8n password no longer works | `28000` (login not permitted) or `28P01` (password failed); both UNVERIFIED, record the one seen | Retirement proof |
| C5 | catalog | `pg_class.relowner` of mf_leads = mf_tableowner; no PUBLIC entry in the table or column ACL; no flow login is a member of any group | no error; compare lists | Owner and PUBLIC check |
| C6 | each of the 4 | open `CONNECTION LIMIT + 1` connections straight to Postgres (no connection pooler in between: a pooler would hide the count; I know of none, UNVERIFIED) from one client machine | `53300` (too many connections) | The limit is real |
| C7 | mf_door, mf_sub | burst: 50 parallel claim-inserts / sub updates through a pool capped at the credential maximum (section 8) | no error | No lead is refused because of the limit; calls wait instead |
| C8 | n8n credentials | set a short expiry date; after it the login is refused; list open sessions of that login (`pg_stat_activity`): they stay open and must be ended by hand; after the password is changed in Postgres and in n8n the flows work again | `28P01` expected for the expired login (UNVERIFIED) | Rotation drill |
| WS | the wide spots (section 9) | mf_door `INSERT ... state='done'` and `attempts=99`: EXPECTED TO SUCCEED; mf_sub `UPDATE state` on a row whose claim token it did not use: EXPECTED TO SUCCEED | none (success expected) | Makes the remaining wide spots visible instead of hidden |
| FW1 to FW14 | the login that owns statement Sn | run statement Sn, with made-up rows in the right start state, as that login; the result must equal today's (same rows returned, same new state) | none (success expected) | The split must not break a flow. FW1/FW3 test insert and RETURNING; FW10/FW12 test the locking select; FW1 also runs with the real `queryReplacement` shape ($1 to $4 values) |
| X | n8n | after F-011 moves n8n to Postgres, repeat C1 to read n8n's own tables as each flow login | `42501` | Matches test T-ROLES in F-041; cannot run until F-011 exists |

Groups MX, C and WS need only Postgres. The FW group also needs the real flows run end to end (the re-test, section 7).

## 6. Where to build and test it

- Roles belong to the whole Postgres server. A "copy of the take's database" on the same server would still create these logins on the take's server. So build and test only on a separate throwaway server: a fresh Postgres container or a new data folder on another port, with made-up rows. Never run `CREATE ROLE` on the take's server for a test.
- `CREATE DATABASE ... TEMPLATE` copies only data and does not isolate logins, so it is not a safe copy.
- Do not run it while filming: the throwaway server competes with the take for the laptop's processor.
- Use the same Postgres major version as the take (found with `SHOW server_version;`, a read-only query).

## 7. Order of the real change (NOT BEFORE THE VIDEO)

**Never before the video is recorded. After it, only with (1) the owner's written yes, (2) a backup of the take's database, (3) group L run and its output saved. Who runs it: the database administrator's login, by hand, with the owner present (a flow or an agent never does; changing the table owner needs superuser rights).** Steps 3 to 6 change what the flows run on; step 8 removes rights and is a short change window in which anything else on the server that relied on PUBLIC rights or on the old login may stop working; I have not checked what else is on the server.

1. Throwaway server: run section 4 part A, then part B, then groups MX, C, WS and the statement tests FW1 to FW14 until every result matches the expected code; fix grants; keep the raw output.
2. Take's server, after the video, with the three conditions above: run group L, save the output (also the re-grant record).
3. Run section 4 part A only (adds logins and grants; the old login keeps working). Set the marker as written in the SQL header.
4. Create the 4 n8n credentials with the pool maximums of section 8.
5. Edit the 8 flow files' credential names, re-import.
6. Run the full re-test with all four flows end to end (new lead, repeat lead, stuck lead, failed mail, alert) and tests FW1 to FW14 on the new logins. **Rollback up to here**: point the credentials back to the old login; nothing was taken away yet. If anything fails, stop and fix before step 7.
7. Owner decides about retiring the old login (yes or no; check no other flow, script or person uses it).
8. Change window: run section 4 part B (owner change, PUBLIC revokes, old login retired, old sessions ended). **Rollback for step 8** is the re-grant block at the end of part B, built from the group L record; it can be run in minutes, but between the revokes and the re-grant anything depending on the old rights fails: treat it as downtime. Then delete the n8n credential `n8n-publish-pg` and record the date.
9. Re-run FW1 to FW14 and checks C1, C4, C5 on the real server (flows must still work after the revokes).

What takes effect on the take: reading this file has no effect; group L changes nothing; building logins and tests on a throwaway server is safe for the take if it does not run during filming; steps 3 to 8 are not safe before the video.
Estimated work (my estimate, not measured): about 3 hours of agent time (1 for SQL and test script, 1 on the throwaway server, 1 for the 8 edits plus re-test), so one working day including waiting for the owner. The finding is rated Nit (after the video).

## 8. Open Postgres and n8n facts (UNVERIFIED: the manual could not be fetched, proxy answered HTTP 403; all from memory)

| Fact | Manual page to check | What breaks if wrong |
|---|---|---|
| `INSERT ... ON CONFLICT DO NOTHING RETURNING` needs only INSERT on the written columns and SELECT on returned columns (and maybe on the conflict-check column) | postgresql.org/docs/current/sql-insert.html | Both doors accept no leads. Covered by FW1/FW3 |
| `FOR UPDATE SKIP LOCKED` needs UPDATE on at least one column besides SELECT | .../sql-select.html (The Locking Clause) | Recovery cannot take over leads or send alerts. FW10/FW12 |
| `gen_random_uuid()` is built in from Postgres 13; before that it needs the extension pgcrypto | .../functions-uuid.html | Door insert fails on old Postgres. `SHOW server_version` |
| A table-level REVOKE also removes column-level grants (my memory) versus does not (earlier reviewer, also memory) | .../sql-revoke.html, .../ddl-priv.html | A leftover PUBLIC column grant. I revoke at both levels; C5 |
| `UPDATE ... SET col = DEFAULT WHERE false` checks only the UPDATE right on col | .../sql-update.html, .../ddl-priv.html | MX update cells give wrong answers; the `has_column_privilege` cross-check catches it |
| A NOLOGIN or expired login is refused with `28000` / `28P01`; a connection over the limit with `53300` | .../errcodes-appendix.html, .../sql-createrole.html | Wrong codes in section 5; record what is seen |
| `ALTER TABLE ... OWNER TO` needs superuser or membership in both roles plus CREATE on the schema | .../sql-altertable.html | Part B step B1 fails; the administrator runs it |
| `\if`, psql variables and `DO` blocks behave as used in the section 4 guard | .../app-psql.html | Guard does not stop the paste; try it first on the throwaway server |
| Passwords stored as scram-sha-256 (default since Postgres 14) and `pg_hba.conf` does not say `trust` for these logins | .../auth-password.html, .../auth-pg-hba-conf.html | Passwords not enforced. `pg_hba` is unread |
| n8n's Postgres credential has a "maximum number of connections" setting, each credential has its own pool, and queries wait when the pool is full | n8n docs, Postgres credentials page (not fetched) | Leads refused at busy moments |

Connection limits: login limits 6, 6, 3, 3; matching n8n pool maximums one lower (5, 5, 2, 2), so a full pool never exceeds the login limit and extra queries wait in n8n instead of being refused. One spare connection allows a reconnect after n8n restarts. These numbers are my guesses; C7 settles them.

Passwords: each flow login gets `VALID UNTIL` (for example 90 days out) and a rotation note: change in Postgres and in n8n together, drill C8. After the date the flows fail: put the date in the calendar. `VALID UNTIL` does not close sessions already open. If the owner prefers no expiry for the take, he says so in writing; the logins still get long random passwords stored only in n8n.

## 9. What is still too wide (review of my own proposal)

1. **Rows and values are not limited by grants.** mf_door can insert any state (for example `done`) and any `attempts`; mf_sub can set state on any row it can see, limited only by the `WHERE claim_token=...` in the SQL text. Group WS makes this visible. Closing it needs a trigger or a database function (a few lines of our own code on the claim path). Rung table below. The owner decides (section 10).
2. mf_door can read `claim_token` of every row (column grants cannot say "own row").
3. mf_recover reads `email` of every row (S10 needs it to run the sub-workflow again). On the take the data is made up; on a client build it is a read right that needs a masking decision.
4. Every login can still read the database's catalog tables (`pg_catalog`: names of tables, columns and logins); Postgres does not allow closing that. PUBLIC also keeps execute rights on built-in functions, and other databases on the same server may be open to everyone (C3 reports; not changed here).
5. Four passwords are only as safe as n8n's own credential store: one n8n user who can read all four credentials undoes the split (F-011).
6. The SMTP credential (`mf-mail-smtp`) is out of scope; F-010 and F-030 still stand for it.
7. Not covered: a human read-only login, a backup login, network rules (who can reach the database port), `pg_hba.conf` (not read).

| Component (CODE-LAST rung table) | Need | Rung tried | Evidence | What only our code gives | Verdict (not yet tested) |
|---|---|---|---|---|---|
| Four logins with column grants | one identity per function | Postgres's own grants (standard feature) | Statement text read; text check passes; grants never run: UNVERIFIED | nothing | proposed as configuration only; stands or falls with groups MX and FW |
| 4 n8n credentials and 8 file edits | use the logins | n8n credential feature | read from the flow files | nothing | proposed as configuration plus file edits |
| Trigger or function to limit state and attempts values | row and value limits | Postgres CHECK/trigger (standard feature, our few lines) | none yet; no incident evidence | a value limit on the claim path | NOT PROPOSED; owner decides after group WS |

## 10. What I could not fix, and why

| Item | Class | Next step |
|---|---|---|
| Postgres facts in section 8 are unverified | impossible now (manual fetch refused with HTTP 403; no Postgres available) | The lead fetches the pages, or runs groups MX, FW, C on a throwaway server (that also settles every statement of section 4); then update this file |
| Today's rights of the old login are unknown; it may be a superuser or the administrator's login | needs the owner | Owner (after the video) allows group L; masked result comes back |
| Whether another flow, script or person also uses `n8n-publish-pg` | needs the owner | Owner checks n8n's credential list and laptop notes before step 7 of section 7 |
| Wide spots (section 9, item 1) | needs the owner (extra code) | Owner decides after group WS |
| Revoking PUBLIC connect on other databases of the same server | needs the owner | Owner decides after C3 |
| The SQL is in this file, not a separate .sql file | my brief allowed edits to this file only; the paste guard in section 4 and the NOT BEFORE THE VIDEO banners are the protection meanwhile | Lead moves section 4 into its own file if wanted |
| This round-2 version has had no independent review | needs the lead | Lead runs the EGM review of this file |

Not checked: any SQL against a real Postgres; whether the current login is a superuser or owner; the Postgres version; `pg_hba.conf` and network access; whether the database setup exists outside this repository; n8n's pool behaviour; flow folders v3 and v4 and the desk-* workflows; non-Postgres nodes that might call a database; whether film-v5 and real-v5 SQL are identical (not re-compared this round); studio rule numbers (not present in this repository).
