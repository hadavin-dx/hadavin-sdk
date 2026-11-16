# ROLES-PROPOSAL: separate database logins for the lead-intake flows (queue item F6, finding F-010)

**DANGER, READ FIRST: if one of these database rights is wrong, the flows stop saving new leads, and the recorded video take would fail. Nothing in this file has been run against a database, so no right in it is proven. Do nothing from this file to the video take's database or flows before the video is recorded.**

STATUS: PROPOSAL ONLY. Written, never run. Version 4 (round-3 fixes M1 to M8 and N1 to N10, see `reviews-roles/fix-roles-r3.md`). It has not passed a fourth review. The section 4 SQL changed a lot in this version (three guarded parts, one transaction each), so it is again completely untested. Decisions only the lead or owner can make are listed as questions in section 11.

## What I need from the owner (5 lines)

1. Confirm in writing: nothing in this file touches the video take's database or flows before the video.
2. After the video: say yes or no to running the read-only look (group L in section 5) on the take's database. It only reads the database's own lists and changes nothing. Send me the masked result.
3. Say whether the old shared login may be switched off after the new logins work (section 7, step 7). If another flow, script or person uses it, say so first. Also say now whether the old login is the database administrator's own login or a superuser (a login that is allowed everything): that changes what "switch off" can mean (section 4 part C, section 11 question 3).
4. After the wide-spot checks (group WS) have been run, decide whether to add a small trigger on the lead path (section 9, item 1; extra code of ours, so it is your decision).
5. Decide who runs the change on the take's server: it needs the database administrator's login (section 7). I do not run it.

## 0. Plain words used in this file

- **n8n**: the workflow tool that runs the flows. **Flow**: one n8n workflow file. **Credential** (n8n word): a saved database login inside n8n (name plus password). **Postgres**: the database. **Role**: a database login with its own list of allowed actions; I say "login". **Grant**: one entry on that list. **Column-level grant**: the entry names exact columns of a table, not the whole table. **PUBLIC**: Postgres's built-in group that every login on the same server belongs to (not "the outside world").
- **The video take**: the one recorded run of the demo video. **The laptop**: the machine that runs n8n and the take's database. **Throwaway server**: a separate, empty Postgres used only for tests (section 6).
- **Door**: a flow that receives a lead. Two doors: the form door (file `mf-form.json`) and the webhook door (`mf-hook.json`; a webhook is a web address another system calls). **Sub-workflow** (`mf-sub-crm-mail.json`): the flow the doors call to save the lead in the customer-contact system (the CRM) and send the lead's mail. **Recovery** (`mf-recovery.json`): the flow that runs on a timer, takes over leads that got stuck, and sends alert mails.
- Four things were called "claim" in the old text. Here: **claim insert** = the first save of a new lead (the insert decides who owns the lead). **Claim token** (column `claim_token`) = a random text that proves which run owns the lead right now. **Take over** = recovery giving a stuck lead a new claim token. **Alert claim** = recovery reserving a lead for an alert mail (column `alert_token`). **Alert** = mail telling a person a lead ended in `failed` or `unknown`.
- **Words inside the SQL**: `RETURNING` = the statement hands back columns of the row it just wrote, which counts as reading them. `ON CONFLICT DO NOTHING` = if the lead already exists, do nothing. `FOR UPDATE SKIP LOCKED` = lock the chosen rows and skip rows another run has locked. `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE` = the login cannot become an administrator, create databases or create logins. `NOBYPASSRLS` = the login cannot skip row-level rules (none exist here; this is a safety margin). `NOINHERIT` = a login does not automatically gain the rights of groups it belongs to (none here; a margin). `CONNECTION LIMIT n` = at most n open sessions for this login. `VALID UNTIL` = the password stops working on that date (open sessions are not closed by it). `scram-sha-256` = the modern way Postgres stores and checks passwords. `TEMP` = the right to create temporary tables. `SQLSTATE` = Postgres's 5-character error code; `42501` means "permission denied".
- **Names of tests**: group **L** (the read-only look), group **MX** (the full rights matrix), **FW1 to FW14** (flow-works tests: each statement still does its job), **C1 to C8** (other checks), group **WS** (wide-spot tests). "Earlier review" means review round 1 of this file.
- **Server fingerprint** (section 4): the database name plus the server's own identifier number, written down per server before the first run, used to check the SQL is being run on the server meant. "CODE-LAST" is the studio rule that our own code is the last choice; "EGM" is the studio's review process. Finding ids (F-010, F-011, F-030, F-041) are rows in the flows-audit findings list; they are labels only. `mf_` is the prefix of the existing table `mf_leads`. **Owner** always means the studio owner; the database object's owner is called **table owner**.

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

**Coverage check (text only, no database).** Run from `handover`: `python3 -I flows-audit/roles-coverage-check/check_grants_cover_queries.py demo/n8n-flows-real-v5 demo/n8n-flows-film-v5`. On the grants of this version it printed "covered" for all 28 nodes and `TOTAL UNCOVERED OR UNMAPPED: 0` (exit 0). With `claim_token` removed from the recovery SELECT grant (a copy of the script in the scratchpad), it printed UNCOVERED for ClaimStuck and exit status 1, so it does catch that one fault. The grants inside the script are a copy of section 4 part A: if section 4 changes, change the script (round-3 finding: a hand copy can drift; the better fix is for the script to read the GRANT lines of part A itself, which is a change to the script, not made here). The script's own limits found in round 3 (it can report an empty folder as fine, an empty or expression query as covered, ignores which credential a node uses, passes other statement kinds, is case-sensitive, and does not report grants nobody uses) are listed in section 10. It is a rough text parser and can miss unusual SQL; it never ran on a database. The real proof is groups MX and FW.

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
- Cost: 4 credentials created in n8n (each password typed by hand into n8n, never into a file); every Postgres node in the 8 flow files (4 files in each of the two folders; 14 nodes per folder) is pointed at the matching new credential; the 8 files are re-imported. That is a flow change, so it needs the full re-test. It is not a config-only change.
- **n8n finds a credential by its id, not by its name (round-3 finding M6; I checked the files).** In all 8 files every Postgres node carries the SAME placeholder id `PG_CREDENTIAL_ID` and the name `n8n-publish-pg` (grep on `handover/demo/n8n-flows-real-v5` and `n8n-flows-film-v5`), and the sub-workflow call carries the placeholder `SUB_WORKFLOW_ID`. The builder script (`build_mainframe.py`) takes ONE credential id argument, so it cannot build four logins today. Rule I rely on (UNVERIFIED, n8n docs not fetched): n8n resolves a node's credential by `id`; the `name` is only a label. So changing the name alone changes nothing. The needed edit, per node name: door nodes `Claim`, `Stored` (form and hook files) get the id of `n8n-publish-pg-door`; `SetCrmId`, `MailClaim`, `MarkDone`, `MarkUnknownA`, `MarkUnknownB` get `-sub`; `ClaimStuck`, `MarkFailed` get `-recover`; `AlertClaim`, `AlertBackoff`, `AlertMark` get `-alert` (per folder: 2 door nodes in the form file + 2 in the hook file + 5 + 2 + 3 = 14). The builder must be changed to take four ids (or the edit is done by a script that maps node name to credential id and is itself tested). Each real id is only known after the credential exists in n8n; the repository files keep placeholders (`PG_CREDENTIAL_DOOR_ID`, `PG_CREDENTIAL_SUB_ID`, `PG_CREDENTIAL_RECOVER_ID`, `PG_CREDENTIAL_ALERT_ID`).
- **Re-import (UNVERIFIED how n8n behaves):** importing a flow file may create a new workflow with a new id instead of replacing the old one. If the sub-workflow `mf-sub-crm-mail.json` gets a new id, the two doors and the recovery flow must be re-imported with that new id in `SUB_WORKFLOW_ID`, the old copies deactivated, and the webhook address of the webhook door checked (a second active copy would answer on the same address or collide). The re-test in section 7 step 6 must show exactly one active copy of each flow.
- **Option B (two logins, not proposed).** It would put the claim and alert functions under one identity, which breaks the studio rule "one identity per function". Using it needs the owner's explicit yes with the extra rights written out: the merged door-and-sub login would hold INSERT on 7 columns, SELECT on 5, UPDATE on 4, so a door could change the state of any existing lead; the merged recovery-and-alert login would hold SELECT on 10 columns and UPDATE on 8, so the claim step could rewrite alert columns. No yes exists.

## 4. SQL (UNTESTED; throwaway server only until the owner says otherwise)

Three parts, each meant to be saved as its own file by the lead (`mf-roles-part-a.sql`, `mf-roles-part-b.sql`, `mf-roles-part-c.sql`; today they live only in this file, section 10). **Part A only adds** logins and grants; it takes nothing away. **Part B** changes the table owner and removes rights from PUBLIC. **Part C** retires the old shared login. B and C are a change window (section 7). Each part carries its own guard (round-3 finding: one guard at the top of one paste does not protect a part that is run days later) and runs as ONE transaction: if any statement fails, psql stops and nothing of that part is kept (Postgres rule I rely on, UNVERIFIED: CREATE ROLE, ALTER ROLE, GRANT, REVOKE and ALTER TABLE are all transactional DDL; manual, "SQL Commands", and the note on CREATE ROLE; I have not run it).

**How the guard knows which server it is on.** The earlier guard was a setting anyone can type (`SET mf.throwaway = 'yes'`), so it could not tell the take's server from the throwaway one. Now the person running the file passes, on the psql command line, the database name and the server's own identifier (`system_identifier`, a number fixed when the server's data folder was created, shown by `SELECT system_identifier FROM pg_control_system();`, run by the administrator). These two values are written down in the handover notes for each server **before** the first run: the throwaway server's pair for throwaway runs, the take's pair for the real change. In throwaway mode the database name must also start with `mf_throwaway`, so a copy-paste of the throwaway command cannot match the take's server. This stops a paste into the wrong window; it does not stop an administrator who deliberately types the take's values, and nothing can. Whether `pg_control_system()` may be run by the login used, and whether psql stops cleanly when a variable is missing, are UNVERIFIED (try both first on the throwaway server).

```sql
-- ############################################################################
-- PART A.  UNTESTED.  NOT BEFORE THE VIDEO.  Throwaway server first (section 6).
-- Run by the database administrator's own login, by hand. Not by an agent.
-- Roles belong to the whole server, not to one database.
-- Passwords: set by hand AFTER commit with psql's \password, or in n8n's form. Never in this file.
-- Command line (all four -v values are required; a missing one is a psql error and the file stops):
--   psql -v ON_ERROR_STOP=1 -v mode=throwaway -v expect_db=mf_throwaway_x \
--        -v expect_sysid=<server_identifier_written_down> -v valid_until='<date>' -f mf-roles-part-a.sql
--   (mode is 'throwaway' or 'take'; 'take' only after the video, with the owner's yes, a backup and group L done)
-- ############################################################################
\set ON_ERROR_STOP on
SELECT (:'mode' IN ('throwaway','take')
        AND current_database() = :'expect_db'
        AND (SELECT system_identifier::text FROM pg_control_system()) = :'expect_sysid'
        AND (:'mode' <> 'throwaway' OR current_database() LIKE 'mf\_throwaway%')) AS guard_ok \gset
\if :guard_ok
\else
  \echo 'STOP: this is not the server and database named on the command line; read section 7 of ROLES-PROPOSAL.md'
  \quit
\endif

BEGIN;
-- A0. Stop if any of our logins already exists (roles are server-wide; a rerun must not half-apply).
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('mf_tableowner','mf_door','mf_sub','mf_recover','mf_alert')) THEN
    RAISE EXCEPTION 'STOP: one of the mf_ logins already exists; read section 7';
  END IF;
END $$;

-- A1. Logins. No superuser, no create-role, no create-db, no bypass of row rules.
CREATE ROLE mf_tableowner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
CREATE ROLE mf_door    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 6 VALID UNTIL :'valid_until';
CREATE ROLE mf_sub     LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 6 VALID UNTIL :'valid_until';
CREATE ROLE mf_recover LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 3 VALID UNTIL :'valid_until';
CREATE ROLE mf_alert   LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS CONNECTION LIMIT 3 VALID UNTIL :'valid_until';

-- A2. Let the four logins in.
GRANT CONNECT ON DATABASE :"expect_db" TO mf_door, mf_sub, mf_recover, mf_alert;
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
COMMIT;
-- After COMMIT, by hand: \password mf_door  (and mf_sub, mf_recover, mf_alert). Check password_encryption first (section 8).

-- ############################################################################
-- PART B.  UNTESTED.  NOT BEFORE THE VIDEO.  Separate file, run only in the change window
-- (section 7 step 8), after the owner has said yes to retiring the old login (step 7).
-- Removes rights from EVERY login on the server, not just ours.
-- Command line: same four -v values as part A (valid_until not needed) plus
--   -v old_flow_role=<old login> -v old_table_owner=<current owner of mf_leads, from group L>
-- ############################################################################
\set ON_ERROR_STOP on
SELECT (:'mode' IN ('throwaway','take')
        AND current_database() = :'expect_db'
        AND (SELECT system_identifier::text FROM pg_control_system()) = :'expect_sysid'
        AND (:'mode' <> 'throwaway' OR current_database() LIKE 'mf\_throwaway%')) AS guard_ok \gset
\if :guard_ok
\else
  \echo 'STOP: wrong server or database; read section 7'
  \quit
\endif
-- B0. Preconditions: all five mf_ logins exist (part A was run), the table owner is the one group L recorded,
--     and the old login is NOT a superuser and is not a member of any group (else: owner decides, section 10).
SELECT ((SELECT count(*) FROM pg_roles WHERE rolname IN ('mf_tableowner','mf_door','mf_sub','mf_recover','mf_alert')) = 5
        AND (SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = 'public.mf_leads'::regclass) = :'old_table_owner'
        AND NOT (SELECT rolsuper FROM pg_roles WHERE rolname = :'old_flow_role')
        AND NOT EXISTS (SELECT 1 FROM pg_auth_members am JOIN pg_roles m ON m.oid = am.member WHERE m.rolname = :'old_flow_role')) AS pre_ok \gset
\if :pre_ok
\else
  \echo 'STOP: part B preconditions failed (part A missing, table owner differs from group L, old login is a superuser or in a group)'
  \quit
\endif

BEGIN;
-- B1. The table belongs to mf_tableowner, not to a flow login.
--     Postgres rule I rely on (UNVERIFIED, manual page ALTER TABLE): to change the owner the running login must be
--     the table's owner or a superuser, must be able to SET ROLE to the NEW owner, and the NEW owner must hold CREATE
--     on the table's schema. (Round-3 fix: the CREATE right is needed by mf_tableowner, not by the administrator.)
--     So mf_tableowner first gets USAGE and CREATE on the schema, as the schema's own owner or a superuser.
GRANT USAGE, CREATE ON SCHEMA public TO mf_tableowner;
ALTER TABLE mf_leads OWNER TO mf_tableowner;
--     Changing the owner moves only the old owner's entries to the new owner. EVERY OTHER grantee keeps its rights
--     (rule I rely on, UNVERIFIED, manual: ALTER TABLE / Privileges). Group L lists them; revoke each one by hand here:
-- REVOKE ALL ON TABLE mf_leads FROM <grantee listed by group L>;   -- one line per grantee that is not an mf_ login
-- B2. Take away what PUBLIC (every login on the server) gets by default.
REVOKE ALL ON DATABASE :"expect_db" FROM PUBLIC;    -- removes CONNECT and TEMP
REVOKE ALL ON SCHEMA public FROM PUBLIC;            -- includes CREATE on the schema
REVOKE ALL ON TABLE mf_leads FROM PUBLIC;
REVOKE ALL (lead_key, email, name, state, claimed_until, claim_token, attempts, crm_id, mail_sent,
            created_at, updated_at, alert_sent, alert_token, alert_until, alert_attempts)
       ON TABLE mf_leads FROM PUBLIC;               -- belt and braces: the table-level line should already do this (UNVERIFIED); C5 checks the result
-- B3. (round-3 fix) The old line "ALTER DEFAULT PRIVILEGES ... REVOKE ALL ON TABLES FROM PUBLIC" is removed:
--     tables have no default PUBLIC rights, so it did nothing (rule I rely on, UNVERIFIED, manual "Privileges":
--     PUBLIC gets by default only CONNECT and TEMP on databases, EXECUTE on functions, USAGE on languages and types).
--     If group L shows rows in pg_default_acl for the old owner, decide each one with the owner; none is assumed.
-- B4. Check the exact result BEFORE keeping it: the table's ACL and every column's ACL must equal the expected list
--     (section 5, check C5; the expected list is generated from the group MX table, not typed twice). Any difference rolls back.
-- (the C5 query goes here, producing  acl_ok  via \gset)
\if :acl_ok
  COMMIT;
\else
  \echo 'STOP: the rights after part B are not exactly the expected list; rolling back'
  ROLLBACK;
\endif

-- ############################################################################
-- PART C.  UNTESTED.  NOT BEFORE THE VIDEO.  Retires the old shared login. Same guard header and -v values as part B.
-- Path A (old login is an ordinary login): below.
-- Path B (old login is a superuser, which is likely when the database came from a Docker image whose default login
--   is a superuser; round-3 finding N9): REVOKE does nothing to a superuser. Part C then only (1) changes its password
--   by hand and (2) removes it from n8n. The superuser stays the administrator's login. Owner question 3, section 11.
-- ############################################################################
BEGIN;
REVOKE ALL ON TABLE mf_leads FROM :"old_flow_role";
REVOKE ALL (lead_key, email, name, state, claimed_until, claim_token, attempts, crm_id, mail_sent,
            created_at, updated_at, alert_sent, alert_token, alert_until, alert_attempts)
       ON TABLE mf_leads FROM :"old_flow_role";
REVOKE CREATE ON SCHEMA public FROM :"old_flow_role";
ALTER ROLE :"old_flow_role" NOLOGIN PASSWORD NULL;
COMMIT;
-- Column-level rights of the old login are removed by the table-level REVOKE (rule I rely on, UNVERIFIED, manual page REVOKE:
-- "when revoking privileges on a table, the corresponding column privileges (if any) are automatically revoked on each
-- column of the table"); check C5 proves it (it lists column ACLs).
-- Open sessions of the old login stay open until closed: list them with
--   SELECT pid, usename, state FROM pg_stat_activity WHERE usename = :'old_flow_role';
-- and have the administrator end them with pg_terminate_backend(pid).

-- ===== ROLLBACK (the group L record is the truth; this text is only the shape) =====
-- Part C undone: the old login's password was set to NULL, so rollback needs a NEW password (set by hand) and a NEW
--   n8n credential (the old one is deleted in step 8 and its password was never kept anywhere):
--   ALTER ROLE <old_flow_role> LOGIN;  then \password <old_flow_role>;  then create the n8n credential again.
-- Part B undone: ALTER TABLE mf_leads OWNER TO <old_table_owner>;
--   GRANT <exact privileges recorded in relacl and column acl by group L> ON TABLE mf_leads TO <old_flow_role>;
--   GRANT <each other grantee's recorded privileges> ...;  default-privilege rows: restore from the pg_default_acl record;
--   GRANT CONNECT, TEMP ON DATABASE <db> TO PUBLIC;  GRANT USAGE ON SCHEMA public TO PUBLIC;  (only if group L showed them)
--   and take back what part B gave mf_tableowner if wanted: REVOKE CREATE ON SCHEMA public FROM mf_tableowner;
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
| GRANT USAGE, CREATE ON SCHEMA public TO mf_tableowner (part B, before the owner change) | Postgres needs CREATE on the schema for the new owner; USAGE lets it reach the table. mf_tableowner cannot log in; only the administrator uses it with SET ROLE (test C9). Wider than the four flow logins on purpose: it is the migration identity, never used by a flow |

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

**Positive control, one per action (round-3 finding N1)** = an allowed statement of the SAME action (SELECT, INSERT, UPDATE, DELETE, TRUNCATE, CREATE and so on), run by the same login in the same session just before the denied one, on made-up rows that exist. It proves the login can connect, the table and rows exist and the action itself works, so the denial is not caused by something else. For every denied action the test table lists its control; where a login has no allowed statement of that action at all (for example the INSERT of mf_sub, or any DELETE), the control is the same action run by a login that is allowed it (mf_tableowner via `SET ROLE`, on a rolled-back transaction, or the administrator), plus `has_column_privilege` / `has_table_privilege` for the denied login returning false. A denial without its control is not counted.

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
SELECT has_column_privilege('<old_flow_role>', att.attrelid, att.attname, p) AS allowed, att.attname, p FROM pg_attribute att, unnest(ARRAY['SELECT','INSERT','UPDATE']) p WHERE att.attrelid='mf_leads'::regclass AND att.attnum > 0 AND NOT att.attisdropped;   -- round-3 fix N4: information_schema.columns lists only columns the running login can already see; pg_attribute lists all
SELECT pg_get_userbyid(setrole) AS role_name, setdatabase, setconfig FROM pg_db_role_setting;   -- per-login settings (for example a changed search_path or session limits) that a new login would not have
SHOW server_version;  SHOW password_encryption;
SELECT type, database, user_name, address, auth_method FROM pg_hba_file_rules;   -- how logins are checked; any 'trust' line for our logins or our database is a stop (check C10). Needs administrator rights; PG 10 or later (UNVERIFIED)
SELECT rolname, left(rolpassword, 14) AS password_kind FROM pg_authid WHERE rolname = '<old_flow_role>';   -- only the first 14 characters (the kind, not the hash): 'SCRAM-SHA-256$' means scram-sha-256, 'md5' means the old md5 kind
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
| C1 | each of the 4 | `CREATE TABLE`, `CREATE TEMP TABLE`, `CREATE SCHEMA`, `DROP TABLE mf_leads`, `ALTER TABLE mf_leads ...`, `COMMENT ON`, `CREATE ROLE`, `COPY ... PROGRAM`, `COPY mf_leads TO '/path'`, `SELECT` on a second made-up table `mf_other` in schema public (created by the administrator for the test only) | `42501` for each | No structure change and no reach beyond the table (TEMP is closed by the PUBLIC revoke; this row only passes after Part B). Round-3 fix N2: the old text said "any other table", which is false: every login can read the catalog tables such as `pg_class` (section 9 item 4). Reading the catalog is expected to SUCCEED and is listed in WS. |
| C2 | each of the 4 | `SET ROLE` to each other login and to mf_tableowner | `42501` | No login hopping (no memberships exist) |
| C3 | a fresh login with no grants (`mf_nobody`, made for the test) | connect to our database; to `template1`, `postgres` and every other database in `pg_database` | `42501` for our database after Part B (no CONNECT right); for the others: record what happens, do not expect | Shows which other databases anyone can still open (report; changing other databases needs the owner's yes) |
| C4 | the old shared login | after retirement (part C, path A): login is refused; cannot read or write mf_leads; its old n8n password no longer works | `28P01` (password authentication failed) expected FIRST. Round-3 fix N3: Postgres checks the password before it checks the LOGIN attribute (rule I rely on, UNVERIFIED, from the source order described in the manual page for client authentication), and part C sets the password to NULL, so with a password method the code is `28P01`. `28000` ("not permitted to log in") would mean the password check was skipped, for example because `pg_hba.conf` says `trust`: that is a failure of C10. Record the one seen | Retirement proof |
| C5 | catalog | EXACT rights check (round-3 fix M5). (a) `pg_class.relowner` of mf_leads = mf_tableowner. (b) The table-level ACL (`aclexplode(relacl)`) contains only mf_tableowner's own entries: no PUBLIC (grantee 0), no old login, no other grantee. (c) The column-level ACLs (`aclexplode(attacl)` per column of `pg_attribute`) equal EXACTLY the expected list taken from group MX: `SELECT grantee, attname, privilege_type` from the catalog, `EXCEPT` the expected list, and the expected list `EXCEPT` the catalog, both results empty (a difference in either direction fails; this also finds a grant nobody needs). (d) No flow login is a member of any group. The expected list is generated from the MX table by the test script, not typed a second time | both differences empty; no error | Owner and PUBLIC check; the old text only looked for PUBLIC and would not see a leftover grantee (ALTER OWNER leaves other grantees in place) |
| C6 | each of the 4 | open `CONNECTION LIMIT + 1` connections straight to Postgres (no connection pooler in between: a pooler would hide the count; I know of none, UNVERIFIED) from one client machine | `53300` (too many connections) | The limit is real |
| C6b | mf_door, mf_sub, mf_recover, mf_alert | **Hard-kill restart test (round-3 finding M7).** With n8n running its pools, kill the n8n process the hard way (no clean shutdown), start it again at once, and send leads through all four flows. Then repeat with TWO n8n processes running (if the take can run queue workers or a second instance; count them first). Record: does any login hit `53300` after the restart, for how long, and does a lead get refused or lost (lead refused = fail) | none expected; `53300` is the failure to look for | The limit numbers in section 8 assume the old connections vanish when n8n dies. On one machine the operating system closes them at once (UNVERIFIED); over a network Postgres may keep them until it notices the dead client (see `tcp_keepalives_*` and, from Postgres 14, `idle_session_timeout`, UNVERIFIED), and until then they count against the limit. The result decides the final limits (section 11 question 5) |
| C7 | mf_door, mf_sub | burst: 50 parallel claim-inserts / sub updates through a pool capped at the credential maximum (section 8), with the number of n8n processes as in C6b | no error | No lead is refused because of the limit; calls wait instead |
| C8 | n8n credentials | set a short expiry date; after it the login is refused; list open sessions of that login (`pg_stat_activity`): they stay open and must be ended by hand; after the password is changed in Postgres and in n8n the flows work again. **Silent-stop check (round-3 finding M7):** with the expiry passed, keep n8n running (old sessions stay open) and then restart n8n: confirm which flow stops first and whether anyone is told. For `mf_alert` the failure is silent: the alert mails that tell a person a lead failed would simply stop. Also test the early-warning query `SELECT rolname, rolvaliduntil FROM pg_roles WHERE rolname LIKE 'mf\_%' AND rolvaliduntil < now() + interval '14 days'` (expected to return the login whose date is near) | `28P01` expected for the expired login (UNVERIFIED) | Rotation drill; an expiry that nobody watches turns the alerts off without a sign |
| C9 | mf_tableowner (via `SET ROLE` by the administrator) | after part B: `SELECT has_schema_privilege('mf_tableowner','public','USAGE')` and `'CREATE'`; then inside a rolled-back transaction, as mf_tableowner: `ALTER TABLE mf_leads ADD COLUMN probe int` (this is the migration the table owner exists for) | both true; the ALTER succeeds | Round-3 finding M4: part B revokes schema rights from PUBLIC, and a role that is not the schema owner has none of its own, so without the explicit grant in part B step B1 the owner could not migrate. Positive control: the same ALTER by the administrator |
| C10 | any login on the take's and the throwaway server | **Passwords really are checked (round-3 finding M8).** (a) connect as `mf_door` with a wrong password: expect `28P01`; with no password: expect refusal (a prompt or `28P01`), never a session. (b) `SHOW password_encryption` = `scram-sha-256`, and `left(rolpassword,14)` of each mf_ login in `pg_authid` = `SCRAM-SHA-256$` (administrator query; prints no hash). (c) `pg_hba_file_rules`: no line with method `trust` (or `md5`, or `password`) that matches our database and our logins, from the address n8n uses and from any other address the server listens on. On the Docker image's default setup this may FAIL: the official image's local-connection lines may say `trust` (UNVERIFIED), which would make every grant in this file worthless to anyone who can reach the server | `28P01` for (a); the stated values for (b) and (c) | Without this test the grants are proven but the logins could be entered without a password |
| WS | the wide spots (section 9) | mf_door `INSERT ... state='done'` and `attempts=99`: EXPECTED TO SUCCEED; mf_sub `UPDATE state` on a row whose claim token it did not use: EXPECTED TO SUCCEED | none (success expected) | Makes the remaining wide spots visible instead of hidden. Also WS: `SELECT count(*) FROM pg_class` by each login succeeds (catalog is readable, section 9 item 4) |
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

1. Throwaway server (with its own fingerprint written down): run section 4 part A, then part B, then part C, then groups MX, C, WS and the statement tests FW1 to FW14 until every result matches the expected code; fix grants; keep the raw output.
2. Take's server, after the video, with the three conditions above: run group L, save the output (also the re-grant record).
3. Run section 4 part A only (adds logins and grants; the old login keeps working) with `mode=take` and the take's own fingerprint written down in step 2. Then set the four passwords by hand.
4. Create the 4 n8n credentials with the pool maximums of section 8.
5. Point every Postgres node of the 8 flow files at the id of its new credential (node-to-credential table in section 3; a name change alone does nothing, because n8n binds by id), set the sub-workflow id the doors and recovery call, re-import, and check there is exactly one active copy of each flow.
6. Run the full re-test with all four flows end to end (new lead, repeat lead, stuck lead, failed mail, alert) and tests FW1 to FW14 on the new logins. **Rollback up to here**: point the 14 nodes (by id again, not by name) back at the old credential and deactivate the new copies; nothing was taken away yet. If anything fails, stop and fix before step 7.
7. Owner decides about retiring the old login (yes or no; check no other flow, script or person uses it). **If the answer is no, parts B and C are not run at all** (changing the table owner and revoking PUBLIC would also change what the old login can do, and keeping it alive means re-granting it everything, which defeats the split); the three new-login steps stay in place and finding F-010 stays open with the reason written down. If the old login is a superuser, part C path B applies (section 4).
8. Change window: run section 4 part B (owner change, PUBLIC revokes; it rolls itself back if the exact-rights check C5 differs), then part C (old login retired, old sessions ended). **Rollback for step 8** is the rollback block at the end of section 4, built from the group L record; it can be run in minutes, but between the revokes and the re-grant anything depending on the old rights fails: treat it as downtime. After part C the old login has NO password: a rollback needs a new password set by hand and a NEW n8n credential, so **keep the n8n credential `n8n-publish-pg` (disabled, not deleted) until step 9 has passed and one day of normal running** (round-3 finding N6), then delete it and record the date.
9. Re-run FW1 to FW14 and checks C1, C4, C5, C9, C10 on the real server (flows must still work after the revokes).

What takes effect on the take: reading this file has no effect; group L changes nothing; building logins and tests on a throwaway server is safe for the take if it does not run during filming; steps 3 to 8 are not safe before the video.
Estimated work (my estimate, not measured): about 3 hours of agent time (1 for SQL and test script, 1 on the throwaway server, 1 for the 8 edits plus re-test), so one working day including waiting for the owner. The finding is rated Nit (after the video).

## 8. Open Postgres and n8n facts (UNVERIFIED: the manual could not be fetched, proxy answered HTTP 403; all from memory)

| Fact | Manual page to check | What breaks if wrong |
|---|---|---|
| `INSERT ... ON CONFLICT DO NOTHING RETURNING` needs only INSERT on the written columns and SELECT on returned columns (and maybe on the conflict-check column) | postgresql.org/docs/current/sql-insert.html | Both doors accept no leads. Covered by FW1/FW3 |
| `FOR UPDATE SKIP LOCKED` needs UPDATE on at least one column besides SELECT | .../sql-select.html (The Locking Clause) | Recovery cannot take over leads or send alerts. FW10/FW12 |
| `gen_random_uuid()` is built in from Postgres 13; before that it needs the extension pgcrypto | .../functions-uuid.html | Door insert fails on old Postgres. `SHOW server_version` |
| A table-level REVOKE also removes column-level grants. Rule I rely on (round-3 reviewer, my own memory agrees, text not read this round): the REVOKE manual page says that when privileges on a table are revoked, the corresponding column privileges, if any, are automatically revoked on each column too. UNVERIFIED, closable by reading that one page | .../sql-revoke.html, .../ddl-priv.html | A leftover PUBLIC column grant. Part B and C still revoke at both levels (harmless if the rule holds) and C5 compares the exact ACL |
| `UPDATE ... SET col = DEFAULT WHERE false` checks only the UPDATE right on col | .../sql-update.html, .../ddl-priv.html | MX update cells give wrong answers; the `has_column_privilege` cross-check catches it |
| A NOLOGIN or expired login is refused with `28000` / `28P01`; a connection over the limit with `53300` | .../errcodes-appendix.html, .../sql-createrole.html | Wrong codes in section 5; record what is seen |
| `ALTER TABLE ... OWNER TO` needs: you own the table (or are a superuser), you can `SET ROLE` to the NEW owner, and the NEW owner has CREATE on the table's schema. (Round-3 fix M4: the old row said the CREATE right belonged to the person running it.) It moves only the old owner's own ACL entries to the new owner; every other grantee keeps its rights | .../sql-altertable.html, .../ddl-priv.html | Part B step B1 fails (rolled back) or leaves a grantee: B1 grants schema USAGE and CREATE to mf_tableowner first; C5 and C9 test it |
| CREATE ROLE, ALTER ROLE, GRANT, REVOKE and ALTER TABLE can run inside `BEGIN ... COMMIT` and are undone by a failure (transactional DDL) | .../sql-createrole.html, .../sql-begin.html | A failed part leaves half its logins. Try on the throwaway server: make the last statement of part A fail on purpose and check that no mf_ login remains |
| `ALTER DEFAULT PRIVILEGES ... REVOKE ... ON TABLES FROM PUBLIC` changes nothing, because tables have no default PUBLIC rights (only databases: CONNECT, TEMP; functions: EXECUTE; languages and types: USAGE) | .../ddl-priv.html, .../sql-alterdefaultprivileges.html | If wrong, a table made later by the old owner is open to PUBLIC: the pg_default_acl rows in group L show it |
| `system_identifier` from `pg_control_system()` is a fixed number per data folder and the login used may call the function | .../functions-info.html | The fingerprint guard of section 4 cannot run; use another fingerprint the administrator can read (for example `inet_server_port()` plus the database oid and the data folder path) |
| n8n resolves a Postgres node's credential by its `id`, not by its name | n8n docs, credentials and workflow import (not fetched) | The 14 nodes keep using the old login after the "rename"; step 6 would still pass. FW tests must therefore also record which login each statement ran as (`SELECT current_user` in a probe, or `pg_stat_activity.usename` during the run) |
| `idle_session_timeout` exists from Postgres 14; `tcp_keepalives_idle/interval/count` can be set per login | .../runtime-config-client.html, .../runtime-config-connection.html | Option for dead pool connections after a hard kill (C6b); not proposed until C6b shows the problem |
| psql `\if`/`\endif`, `\gset`, `\quit`, the variable forms `:'name'` and `:"name"`, and `-v` command-line values behave as used in the section 4 guards; a missing `-v` value makes the file stop with an error (round-3 fix N7: the old row was about a guard that used none of these; the new guards do, and a `DO` block cannot read psql variables, so none is used for them) | .../app-psql.html | The guard does not stop the run; try each part first on the throwaway server with a wrong fingerprint and with a missing value; both must stop before any change |
| Passwords stored as scram-sha-256 (default since Postgres 14) and `pg_hba.conf` does not say `trust` for these logins | .../auth-password.html, .../auth-pg-hba-conf.html | Passwords not enforced. `pg_hba` is unread; group L and test C10 read it |
| n8n's Postgres credential has a "maximum number of connections" setting, each credential has its own pool, and queries wait when the pool is full | n8n docs, Postgres credentials page (not fetched) | Leads refused at busy moments |

Connection limits: login limits 6, 6, 3, 3; matching n8n pool maximums one lower (5, 5, 2, 2), so a full pool never exceeds the login limit and extra queries wait in n8n instead of being refused. **These numbers hold only for ONE n8n process, and only if old connections disappear when n8n stops** (round-3 finding M7). Rule: (number of n8n processes) x (pool maximum) + 1 spare must not exceed the login limit; count the processes first (queue workers, a second instance, a manual test run). After a hard kill the dead process's connections may stay counted for a while, so the one spare may not be enough for a restart; C6b measures it, and until it has run the limits are guesses, not a design. Do not raise the limits or add `idle_session_timeout` before C6b shows a real problem (a lower idle timeout can also cut healthy pool connections and cause errors on the next query).

Passwords: each flow login gets `VALID UNTIL` (for example 90 days out; part A takes it from `-v valid_until=...`; `'infinity'` means no expiry, UNVERIFIED) and a rotation note: change in Postgres and in n8n together, drill C8. After the date new connections fail: put the date in the calendar AND run the early-warning query in C8 weekly. The danger is that the failure is delayed and quiet: open sessions keep working until n8n restarts, and the expiry of `mf_alert` stops alert mails without any error a person sees. `VALID UNTIL` does not close sessions already open. If the owner prefers no expiry for the take, he says so in writing (question 4, section 11); the logins still get long random passwords stored only in n8n.

## 9. What is still too wide (review of my own proposal)

1. **Rows and values are not limited by grants.** mf_door can insert any state the table allows (the column has a CHECK constraint that already limits `state` to six values: `new`, `processing`, `done`, `review`, `unknown`, `failed`; round-3 finding N8, I checked `mf_leads.sql` line 8; so "any state" in the old text was too wide, but `done` is still allowed) and any `attempts`; mf_sub can set state on any row it can see, limited only by the `WHERE claim_token=...` in the SQL text. Group WS makes this visible. Closing it needs a trigger or a database function (a few lines of our own code on the claim path). Rung table below. The owner decides (section 10).
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
| The SQL is in this file, not in three separate .sql files (part A, B, C) | my brief allowed edits to this file only; each part has its own guard and transaction so it can be cut out unchanged; the NOT BEFORE THE VIDEO banners are the protection meanwhile | Lead moves the three parts into their own files (question 1, section 11) |
| The coverage script (`roles-coverage-check/`) has its own round-3 findings (M9 and the credential check): empty folder, expression queries, credential name against login, other verbs, case, drifting copy of the grants, unused grants | belongs to the other agent, not edited here | The script's owner fixes them; this file only states its limits in section 2. One link from this file: the script should read the grants from the part A SQL, not from a copy (section 2, last paragraph) |
| The doc-side facts that need Postgres or n8n (transactional parts, guard behaviour, ALTER OWNER rule, REVOKE cascade, C1 to C10 codes, credential binding by id) | impossible now (no Postgres here; manual fetch refused with HTTP 403, tried again this round: `www.postgresql.org` refused by the proxy) | All stay UNVERIFIED with the manual rule named in section 4 and section 8; run on the throwaway server |
| This round-3 version has had no independent review | needs the lead | Lead runs the EGM review of this file (security path: repeat until a round finds nothing real) |

Not checked: any SQL against a real Postgres; whether the current login is a superuser or owner; the Postgres version; `pg_hba.conf` and network access; whether the database setup exists outside this repository; n8n's pool behaviour; flow folders v3 and v4 and the desk-* workflows; non-Postgres nodes that might call a database; whether film-v5 and real-v5 SQL are identical (not re-compared this round); studio rule numbers (not present in this repository).

## 11. Questions for the lead or the owner (decisions I cannot make), each with my recommendation

1. **Move part A, B and C into three separate `.sql` files?** My recommendation: yes, in `handover/flows-audit/` (or the demo folder), unchanged, so a person cannot paste part B by accident while reading part A; each part already has its own guard and transaction. My brief let me edit this file only, so I did not.
2. **Which fingerprint pair is written down, and by whom?** Recommendation: the administrator records the database name and `system_identifier` of the throwaway server when it is created and of the take's server when group L is run, in the handover notes, and the owner reads both back before part A runs on the take's server.
3. **Is the old login (the one behind `n8n-publish-pg`) a superuser, the administrator's own login, or the table owner? Is the database from a Docker image?** Recommendation: group L answers it after the video. If it is a superuser, use part C path B (new password, remove from n8n, keep it as the administrator's login only) and say plainly that "retired" then means "no longer used by the flows", not "has no rights". Do not run part B or C until this is answered.
4. **Expiry of the flow logins (`VALID UNTIL`).** Recommendation: for the take (a demo on made-up data) use `infinity` and rotate by calendar; for a client build use 90 days together with the weekly early-warning query from C8 wired to an alert. An expiry nobody watches would stop the alert mails silently.
5. **Connection limits and pool maximums.** Recommendation: keep 6/6/3/3 and 5/5/2/2 for now as test values only, and let C6b (hard kill) and the count of n8n processes decide; I make no change before that result.
6. **If the owner says no to retiring the old login (step 7)?** Recommendation: do not run parts B and C; keep F-010 open and written as "split is in place, the old login can still do everything". Re-granting the old login after part B would defeat the split.
7. **Does the lead accept that mf_tableowner holds CREATE on schema public?** Recommendation: yes. It is the migration identity, cannot log in, and is reached only by the administrator with `SET ROLE`; the alternative is that nobody can migrate the table after part B.
8. **Should the film and real folders be diffed again?** Recommendation: yes, one scripted comparison of the 28 query texts and the credential entries before step 5, saved with the evidence, because the node-to-login table of section 3 assumes both folders have the same node names (I checked the placeholder id in both folders by grep, not the statement texts).

