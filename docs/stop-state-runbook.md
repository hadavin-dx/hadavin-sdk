# Stop switch: runbook

The stop switch halts the agent's model calls. Stopping is easy and anyone with the runtime configuration can do it.
Clearing a stop (a reset) needs a separate database login, so that the agent's own login can never clear it.

## Set up once (PostgreSQL)
1. Create a login role for resets, for example `hadavin_reset`. Give it a password of its own. `migrate` never creates roles.
2. Run `hadavin-sdk migrate --runtime-role <runtime> --portal-role <portal> --purge-role <purge> --reset-role <reset>`.
   The four roles must be different and not members of each other. Without `--reset-role`, migrate warns that nobody
   but the database owner can reset.
3. Store the reset login's connection string as a secret on the operator's machine only. Put the NAME of that secret
   in `backends.store.reset_credential_ref`. Do not give this secret to the runtime process.

## Stop
`hadavin-sdk limits stop --by <who>` adds one stop. It works even when the audit log is down (the audit row is written afterwards).

## Reset
`hadavin-sdk limits reset --by <who>` on the operator's machine. The reset is written to the audit log first; then every
stop that the reset can see is cleared. A stop made while the reset runs stays in force: check with a second reset.

## Exit codes of `limits stop` and `limits reset`
| code | meaning | what to do |
|---|---|---|
| 0 | done | nothing |
| 2 | refused, or the database answered with an error (for example the login has no right to reset) | read the message; in pilot and prod set `backends.store.reset_credential_ref`; nothing was changed |
| 3 | the audit log could not be written, so the reset was NOT done | bring the audit store back, then reset again |
| 4 | the database cannot be reached | nothing was changed; fix the connection |

## What reads as ON
The `kill_switch` row is missing, or its flag is on, or at least one stop has no clear. If the state cannot be read at
all, a run ends with a person (`limits_unavailable`) and makes no model call.

## Limits
The database owner and a superuser can still change these tables' triggers. The command-line eval and replay paths do
not read the stop state. Old code must not run against a database that has migration `0006_stop_state`.
