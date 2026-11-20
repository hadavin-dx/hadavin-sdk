# Stop switch: runbook

The stop switch halts the agent's model calls. Stopping is easy and anyone with the runtime configuration can do it.
Clearing a stop (a reset) needs a separate database login, so that the agent's own login can never clear it.

## Set up once (PostgreSQL)
1. Create a login role for resets, for example `hadavin_reset`. Give it a password of its own. `migrate` never creates roles.
2. Run `hadavin-sdk migrate --runtime-role <runtime> --portal-role <portal> --purge-role <purge> --reset-role <reset>`.
   The four roles must be different and not members of each other. Without `--reset-role`, migrate warns that nobody
   but the database owner can reset. Name all the roles in ONE command: a plain `migrate` with no `--runtime-role`
   applies no grants, so an old runtime login keeps UPDATE on `kill_switch` and gets nothing on the new tables (its
   stop then fails with exit 2). Whenever a role is named, migrate refuses if any other role, apart from superusers,
   the owner and the named reset role, could clear a stop (a right on `kill_switch` or `kill_switch_clears`, or
   membership in a role that holds one); the message names the role. Running it later without `--reset-role`
   therefore refuses the reset role itself.
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
- The database owner and a superuser can still change these tables' triggers; they are outside the guarantee.
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
