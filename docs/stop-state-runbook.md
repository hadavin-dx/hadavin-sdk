# Stop state runbook (kill switch)

Plain words. "Stop" turns the kill switch on; "reset" turns it off. A stop adds a row to a request table; a reset
clears exactly the stops the operator saw, named by a pair of numbers: `version` and `open_requests`.

## Daily use

- `hadavin-sdk limits status` prints who stopped (a keyed label, never a typed name), `version` and `open_requests`.
- `hadavin-sdk limits stop --by NAME` stops. It uses the stop login (`store.stop_credential_ref`).
- `hadavin-sdk limits reset --by NAME --expect-version V --expect-open N` resets. Copy V and N from `status`. If a
  stop arrived after you read them, the reset is refused (exit 6) and the switch stays ON: read `status` again.
  If the same refusal repeats, someone keeps stopping: find out why before resetting.
- `hadavin-sdk limits whois NAME` prints the label that NAME turns into, so a label in the audit can be read.
- `hadavin-sdk limits check` reads the guard through the reset login and lists every problem (exit 10), or says the
  guard is fine (exit 0). Exit 7 means the database was busy and nothing is known: run it again.

Exit codes: 0 done, 2 usage, 3 audit unavailable, 4 store unreachable, 5 not permitted, 6 the stops changed or the
row is missing, 7 the store is busy (NOT done, retry), 8 stop done but the audit row was not written, 9 database not
migrated, 10 `check` found problems.

## Database administrator emergency stop (no application, no CLI)

Run as the database owner, with the schema on the search path:

    INSERT INTO kill_switch_stop_requests ("by") VALUES ('dba');

The switch reads ON at once. To clear it, use a registered reset login and `hadavin_kill_switch_reset`.

## Who stopped (one query)

    SELECT "by" FROM kill_switch_stop_requests WHERE cleared_by = <version>;

## Missing `kill_switch` row

A stop still works and reads ON. A reset fails with HD005 until the row is back:

    INSERT INTO kill_switch (id, "on", "by", ts, version)
    VALUES (1, true, 'dba', now(), <largest old_version in kill_switch_resets + 1, or 1 if none>)
    ON CONFLICT DO NOTHING;

then run a normal reset with the open count (it may be 0 when only the flag is on).

## Database not migrated (exit 9)

Run `hadavin-sdk migrate --runtime-role R --reset-role G --stop-role S` as the migration role. Until then use the
emergency stop above.

## Rollback

The migration is forward-only. Old releases cannot stop after the runtime lost its rights on `kill_switch`: stop or
upgrade them before the migration. To go back: in ONE transaction take the migration advisory lock, grant
`SELECT, INSERT, UPDATE ON kill_switch` to the runtime role, and fold the open requests into the flag:

    UPDATE kill_switch SET "on" = true,
      "by" = (SELECT "by" FROM kill_switch_stop_requests WHERE cleared_by IS NULL ORDER BY id LIMIT 1)
    WHERE EXISTS (SELECT 1 FROM kill_switch_stop_requests WHERE cleared_by IS NULL);

Without the fold, a stop made through the new function is invisible to the old release.

## What can delay a stop

A stop takes no row lock. It can still queue behind a migration that holds a table lock: at most
`limits.migrate_lock_timeout_ms` plus the migration statement's own run time. A stop that ends busy (lock or
statement timeout, deadlock, connection limit) reports "NOT done" (exit 7) and is tried once more by `limits stop`.
When the runtime holds all of its own connections the stop login still has its own limit (`stop_connection_limit`).
On PostgreSQL 16 and later, grant `pg_use_reserved_connections` to the stop login and set `reserved_connections`, so
the operator stop connects even when `max_connections` is used up (this does not help against the per-role limit).
Revoking EXECUTE on the stop function from the runtime also disables the meter's automatic stop: stop the runtime
processes first and grant it back at once.

## Notes

- `by` is a keyed label: it gives privacy, not proof of who typed it. The runtime process holds the label key.
- The owner or a superuser can still set `cleared_by` by hand or disable the guard triggers; the probe sees a
  disabled trigger, not a hand-set `cleared_by`. In hand steps type exactly `dba`.
- The demo-only per-process label key is allowed only when `environment` is `demo`.
