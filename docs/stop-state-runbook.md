# Stop switch: runbook

The stop switch halts the agent's model calls. Stopping is easy and anyone with the runtime configuration can do it.
Clearing a stop (a reset) needs a separate database login, so that the agent's own login can never clear it.

## Set up once (PostgreSQL)
1. Create a login role for resets, for example `hadavin_reset`. Give it a password of its own. `migrate` never creates roles.
2. Run `hadavin-sdk migrate --runtime-role <runtime> --portal-role <portal> --purge-role <purge> --reset-role <reset>`.
   The four roles must be different and not members of each other. Without `--reset-role`, migrate warns that nobody
   but the database owner can reset. Name all the roles in ONE command: a plain `migrate` with no `--runtime-role`
   applies no grants, so an old runtime login keeps UPDATE on `kill_switch` and gets nothing on the new tables (its
   stop then fails with exit 2). Whenever a role is named, migrate reads the grants on THIS schema's stop tables and
   refuses if anyone but the named reset role could clear or defeat a stop: a role those tables grant a right to
   (UPDATE, DELETE or TRUNCATE on `kill_switch`; INSERT on `kill_switch_clears`; TRIGGER on any of the three; a
   column grant counts; a grant to everyone is named `PUBLIC`), a member, directly or through other roles, of such
   a role or of the reset role, or a role that can hand itself the reset role (see "Limits"). The message names
   each one. Running it later without `--reset-role` therefore refuses the reset role itself. Roles of other
   schemas or applications on the same server are not looked at. The check runs when migrate runs: a role or a
   grant added afterwards is not seen until the next run, which is why you run migrate again after any role change.
   See "Limits" for who is not checked.
3. Store the reset login's connection string as a secret on the operator's machine only. Put the NAME of that secret
   in `backends.store.reset_credential_ref`. Do not give this secret to the runtime process.

## Stop
`hadavin-sdk limits stop --by <who>` adds one stop. It works even when the audit log is down (the audit row is written afterwards).

## Reset
`hadavin-sdk limits reset --by <who>` on the operator's machine. The reset is written to the audit log first; then every
stop visible to the clear statement is cleared. A stop committed after that statement began stays ON; a stop committed
between the audit row and that statement is cleared. The command then reads the state back: it prints
`kill switch OFF` and exits 0 only when the state really is OFF; when it is still ON it says so and exits 2 (run the
reset again). A reset that finds no `kill_switch` row fails (exit 2, audit outcome `limits.reset_failed`): run migrate.
The command refuses (exit 2, before any connection) when `backends.store.reset_credential_ref` names the same secret
as `backends.store.dsn_secret_name`.

## Exit codes of `limits stop` and `limits reset`
| code | meaning | what to do |
|---|---|---|
| 0 | done | nothing |
| 2 | refused, or the database answered with an error (for example the login has no right to reset), or the state still reads ON after a reset | read the message; in pilot and prod set `backends.store.reset_credential_ref`; "still ON": reset again |
| 3 | the audit log could not be written, so the reset was NOT done | bring the audit store back, then reset again |
| 4 | the database cannot be reached | nothing was changed; fix the connection |

## What reads as ON
The `kill_switch` row is missing, or its flag is on, or at least one stop has no clear. If the state cannot be read at
all, a run ends with a person (`limits_unavailable`) and makes no model call.

## Limits
- The database owner and a superuser can still change these tables' triggers; they are outside the guarantee. The
  owner can also DROP and recreate the three stop tables (and so any grant on them). Close that: the runtime login
  and every other login must NOT own the schema (nor be a member of its owner); create the schema as the migrate
  login only.
- Managed-database admin roles (`rds_superuser`, `azure_pg_admin`, `cloudsqlsuperuser`) are NOT superusers to
  PostgreSQL, but they can do what a superuser does here. They are outside the guarantee and not listed (below
  PostgreSQL 16 they are listed only because they hold CREATEROLE: see the next point).
- Not checked by migrate, and so also outside the guarantee: a role whose only way to these tables is membership in
  the owner role, in a superuser, or in a PostgreSQL predefined role such as `pg_write_all_data` (it can write every
  table of the server). Do not hand out those memberships on a server that holds a stop switch. The roles NAMED in
  the migrate command are still refused when they are members of the owner. Also not checked: a SECURITY DEFINER
  function or view owned by a privileged role (review every function of the schema; the check reads grants only).
- What migrate lists as able to clear or defeat a stop: any role that holds UPDATE, DELETE or TRUNCATE on
  `kill_switch`, INSERT on `kill_switch_clears` or TRIGGER on any of the three stop tables (a trigger can drop a stop
  or block a clear), directly or by column grant or through PUBLIC; any member of such a role or of the reset role
  (below PostgreSQL 16 every membership; from 16 a membership whose INHERIT, SET or ADMIN option is true: one with
  all three false is not listed); below PostgreSQL 16 every non-superuser role with CREATEROLE (it can grant the
  reset role to itself); from PostgreSQL 16 every holder of the ADMIN option on such a role or on the reset role
  (ADMIN on the owner role is not followed: the owner is outside the guarantee). The login that created the reset
  role holds the ADMIN option (when it is not a superuser), so it is listed: either create the reset role as a
  superuser or the owner, or run `REVOKE ADMIN OPTION FOR <reset role> FROM <creator>`. The listing is
  conservative: it can name a role that holds only DELETE or TRUNCATE on `kill_switch`, or only a column INSERT
  that leaves out `stop_id`, which alone cannot clear a stop, and it judges each membership on its own, not along
  the whole chain. These are harmless refusals: revoke the right.
- A server that holds other administrators (below PostgreSQL 16, or a managed service): the CREATEROLE listing
  looks at the whole server, not this schema. If a listed role is not a person or process that can use CREATEROLE to
  grant the reset role to itself (for example a managed service's own administrator login), you may name it with
  `--accept-admin-role <role>` (repeat the flag for several; in code `accepted_admin_roles`). Rules: you vouch for it;
  a name is any text of 1 to 63 bytes with no control character and no space at either end (`Admin`, `my-admin`,
  `user@server` are fine), compared as exact text, never `PUBLIC`, `session_user`, `current_user`, `*` or `%`, and
  not one of the roles migrate grants; it is left out of the CREATEROLE listing only, and is still listed when it
  holds a grant on the stop tables. Its MEMBERS are still listed (a member can `SET ROLE` to it and use its
  CREATEROLE): vouching covers the role itself, not who may become it. Below PostgreSQL 16 the command prints the
  accepted names (also when it refuses) and logs them at warning level: the record of who vouched is the CI log of
  that run. From PostgreSQL 16 the option has no effect and the command says so in one line. Use it only when you
  can say who holds that login; the other way out is `REVOKE CREATEROLE` from it or PostgreSQL 16 or later.
- The append-only triggers are not enforced while `session_replication_role` is `replica`. From PostgreSQL 15 a
  superuser can let any role set it (`GRANT SET ON PARAMETER session_replication_role`). A role with DELETE or
  TRUNCATE on a stop table plus that right could remove a stop: migrate does not look at parameter rights, so do
  not grant them on a server that holds a stop switch.
- migrate refuses (ConfigError that names the schema and the search_path) when the three stop tables are not all
  found in the schema the store uses (an empty search_path, a schema without the tables, a missing table, or a
  temporary table with a stop table's name): a check that finds nothing never passes. Set the same search_path for
  the migrate and the runtime login.
- The guarantee is about the state stored in the database. A runtime process that is itself taken over can ignore any
  switch: stop the process too.
- "Audited first" is done by the `limits reset` command. The database does not force it: a person with the reset
  login can clear a stop by hand without an audit row.
- The reset login cannot add a stop row. It can set the old flag in `kill_switch` ON, which is also a stop.
- A refused UPDATE, DELETE or TRUNCATE on `kill_switch_stops` or `kill_switch_clears` says "the audit log is
  append-only": the two tables reuse the audit log's trigger function. It means the stop tables are append-only.
- The command-line eval and replay paths do not read the stop state.
- Old code must not run against a database that has migration `0006_stop_state`.

## Going back to the release before the stop state
The change of meaning cannot be undone by code alone: old code does not read `kill_switch_stops`, and its stop needs
UPDATE on `kill_switch`, which the runtime login no longer holds.
1. Stop every runtime process.
2. As the owner, carry an open stop over to the old flag so it is not lost:
   ```sql
   UPDATE kill_switch SET "on" = TRUE
   WHERE EXISTS (
       SELECT 1 FROM kill_switch_stops s
       WHERE NOT EXISTS (SELECT 1 FROM kill_switch_clears c WHERE c.stop_id = s.id)
   );
   ```
3. Either restore the snapshot taken before migrating, or by hand: `DROP TABLE kill_switch_clears;`
   `DROP TABLE kill_switch_stops;` then `DELETE FROM schema_migrations WHERE version = '0006_stop_state';` and
   `GRANT INSERT, UPDATE ON kill_switch TO <runtime>;`.
4. Start the old code.
