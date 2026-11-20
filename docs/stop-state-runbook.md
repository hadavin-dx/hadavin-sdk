# Stop switch: runbook

The stop switch halts the agent's model calls. Stopping is easy and anyone with the runtime configuration can do it.
Clearing a stop (a reset) needs a separate database login, so that the agent's own login can never clear it.

## Set up once (PostgreSQL)
1. Create a login role for resets, for example `hadavin_reset`. Give it a password of its own. `migrate` never creates roles.
2. Run `hadavin-sdk migrate --runtime-role <runtime> --portal-role <portal> --purge-role <purge> --reset-role <reset>`.
   The four roles must be different and not members of each other. Without `--reset-role`, migrate warns that nobody
   but the database owner can reset. Name all the roles in ONE command: a plain `migrate` with no `--runtime-role`
   applies no grants, so an old runtime login keeps UPDATE on `kill_switch` and gets nothing on the new tables (its
   stop then fails with exit 2). Whenever a role is named, migrate reads the grants on THIS schema's `kill_switch`
   (UPDATE) and `kill_switch_clears` (INSERT) and refuses if anyone but the named reset role could clear a stop:
   a role those tables grant the right to (a column grant counts; a grant to everyone is named `PUBLIC`), or a
   member, directly or through other roles, of such a role or of the reset role. The message names each one.
   Running it later without `--reset-role` therefore refuses the reset role itself. Roles of other schemas or
   applications on the same server are not looked at. See "Limits" for who is not checked.
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
If the audit log is also down at that moment, the `reset_failed` outcome cannot be kept for later by this command (the login it runs under has no right to park events): the refusal is then shown only on the screen and in the exit code.
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
- The database owner and a superuser can still change these tables' triggers; they are outside the guarantee.
- Not checked by migrate, and so also outside the guarantee: a role whose only way to these tables is membership in
  the owner role, in a superuser, or in a PostgreSQL predefined role such as `pg_write_all_data` (it can write every
  table of the server). Do not hand out those memberships on a server that holds a stop switch. The roles NAMED in
  the migrate command are still refused when they are members of the owner.
- PostgreSQL 16 and later: a membership counts only when its SET or INHERIT option is true. A login with CREATEROLE
  that created the reset role is a member WITH ADMIN OPTION only; it cannot use the reset role's rights, so it is
  not refused. If it grants itself SET or INHERIT on the reset role, the next migrate that names a role refuses it.
  A NOINHERIT member that can `SET ROLE` is always refused.
- The guarantee is about the state stored in the database. A runtime process that is itself taken over can ignore any
  switch: stop the process too.
- "Audited first" is done by the `limits reset` command. The database does not force it: a person with the reset
  login can clear a stop by hand without an audit row.
- The reset login cannot add a stop row. It can set the old flag in `kill_switch` ON, which is also a stop.
- A refused UPDATE, DELETE or TRUNCATE on `kill_switch_stops` or `kill_switch_clears` says "the audit log is
  append-only": the two tables reuse the audit log's trigger function. It means the stop tables are append-only.
- The command-line eval and replay paths do not read the stop state.
- Kill switch and spend reserve are two steps (ORDER 020 m1): a model call reads the stop state and then books its
  worst case, not in one transaction. A stop committed between the two lets one more call through per caller that
  already passed the read; the next reserve of every caller sees it. A call already reserved or running is not
  cancelled. For a hard cut, stop the processes as well.
- Old code must not run against a database that has migration `0006_stop_state`.

## Release expired spend holds
A hold nobody settled (a crash, a lost connection) is marked expired by the tick and stays booked at its worst case, so
an agent can sit at its cap. The one sanctioned way to free it is the release command, under its own login (not the
runtime and not the reset login):
1. As the owner: `hadavin-sdk migrate --runtime-role R ... --reset-role X --release-role Y` (name all roles in ONE command).
   Y holds EXECUTE on one function and the audit append, and nothing on the money tables.
2. Put Y's DSN in a secret and set `backends.store.release_credential_ref` to its NAME (not ending in `_secret_name`; not
   the runtime, purge or reset secret).
3. `hadavin-sdk release-expired AGENT --day YYYY-MM-DD --by WHO`. The audit intent row is written first; then one
   transaction sets the EXPIRED holds of that agent and day to settled at 0 and lowers the day and the month counter by
   the same sum (never below zero); then the outcome row. Open holds and other days are never touched. Exit 0 done
   (also when 0 rows), 2 refused or the login lacks the right, 3 the audit is unavailable (nothing changed), 4 the store
   is unreachable (nothing changed), 5 the release is COMMITTED but its outcome row could not be written: the command
   names the dangling intent id, and the audit then holds an intent row with no outcome. The counters did change; do
   not run the release again to "fix" it. Record the outcome by hand against that intent id, or leave the dangling
   intent as the only record and note it in the incident log.
   The counters stop quietly at zero (`GREATEST`): when a counter was already lower than the expired sum (drift), it
   is not hidden. The outcome row and the command output carry `requested_usd` (the sum of the expired holds) and
   `applied_usd` (what the day counter really fell by); applied lower than requested is drift to look into.
   The function runs as the migration owner with its search path pinned to `pg_catalog, <schema>, pg_temp` by
   `migrate` (so a temp table of the release login cannot stand in for a money table). Consider
   `REVOKE TEMP ON DATABASE <db> FROM PUBLIC`. The release secret name may not be read by the runtime: a tool,
   source, executor or restored-hash secret that folds to the same name stops the start.
Release only the holds of calls you know were not billed: a late settle of a released hold changes nothing, so a call
that really was billed is then missing from the counters.

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
