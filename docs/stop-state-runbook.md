# Stop switch: runbook

The stop switch halts the agent's model calls. Stopping is easy and anyone with the runtime configuration can do it.
Clearing a stop (a reset) needs a separate database login, so that the agent's own login can never clear it.

## Set up once (PostgreSQL)
1. Create a login role for resets, for example `hadavin_reset`. Give it a password of its own. `migrate` never creates roles.
2. Run `hadavin-sdk migrate --runtime-role <runtime> --portal-role <portal> --purge-role <purge> --reset-role <reset>`.
   The four roles must be different and not members of each other. Without `--reset-role`, migrate warns that nobody
   but the database owner can reset. Name all the roles in ONE command. A `migrate` that names no role at all is
   refused ("no role is named"): it would apply the schema and never check who can clear a stop. `migrate --no-roles`
   is the explicit way to apply the schema only (the first install, before the roles exist); it grants and checks
   nothing, so run the full command right after; do not use it on an existing deployment (old grants stay, nothing is
   checked). A migrate without `--runtime-role` applies no grants, so an old runtime login keeps UPDATE on `kill_switch` and gets nothing on the new tables (its
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
   in `backends.store.reset_credential_ref`. Do not give this secret to the runtime process: the secrets policy
   (IAM or the store's access rules) of the runtime's identity must NOT list the reset secret, because nothing in the
   code can stop a secrets provider from handing it over. The runtime start refuses when ANY secret name it reads (a
   backend, tool, source, action executor, sender or the restored-hash key) is, or folds to, the reset or release ref.

## Stop
`hadavin-sdk limits stop --by <who>` adds one stop. It works even when the audit log is down (the audit row is written afterwards).

## Reset
`hadavin-sdk limits reset --by <who>` on the operator's machine. The reset is compare-and-clear: it first reads the open
stops, writes the audit row (the intent) WITH their ids, their count and a hash of the ids, and then clears exactly those
ids (one `kill_switch_clears` row each, the old flag turned off in the same transaction). A stop that is not in that list
(one set while the audit row was being written, or while the clear ran) is NOT cleared and keeps the switch ON. The command
then reads the state back: it prints `kill switch OFF (by <who>; cleared N stop(s))` and exits 0 only when the state really
is OFF; when it is still ON it says who set the oldest open stop and when, lists each stop it did not clear (id, who, when),
and exits 2. Check the stop reason with that person BEFORE resetting again: the next reset clears every stop it lists. A
reset that finds no `kill_switch` row fails (exit 2, audit outcome `limits.reset_failed`): run migrate.
If the audit log is also down at that moment, the `reset_failed` outcome cannot be kept for later by this command (the login it runs under has no right to park events): the refusal is then shown only on the screen and in the exit code.
The command refuses (exit 2, before any connection) when `backends.store.reset_credential_ref` names the same secret
as `backends.store.dsn_secret_name`, or when the two names hold the same DSN. `release_credential_ref` is checked the same way
against the runtime, reset and purge secrets.

### What a reset records (migration 0009, B8)
In the same transaction as the clears, the reset (the reset login only) inserts one row into `kill_switch_resets`
(`by`, `at`, `cleared_ids` = the ids it really cleared, `audit_seq` = the audit chain seq of its intent when the store
knows it, otherwise NULL: the chain returns an event id, not a seq). This record survives if the audit row is lost. The runtime login holds nothing
on `kill_switch_resets`. Read it as the database owner:
`SELECT at, "by", cardinality(cleared_ids), audit_seq FROM kill_switch_resets ORDER BY at;`.
There is no time watermark, so the gate read hides no stop: a stop with an old `ts` (planted, or hand-inserted after a reset)
that has no clear still reads as ON. The read compares `count(kill_switch_stops)` with `count(kill_switch_clears)`
(every clear names one distinct stop, so a surplus of stops means an open stop; both are index-only counts, about
tens of milliseconds for 200000 rows) and only then looks for the oldest open stop.

## Exit codes of `limits stop` and `limits reset`
| code | meaning | what to do |
|---|---|---|
| 0 | done | nothing |
| 2 | refused, or the database answered with an error (for example the login has no right to reset), or the state still reads ON after a reset | read the message; in pilot and prod set `backends.store.reset_credential_ref`; "still ON": check who set the stop and why before resetting again |
| 3 | the audit log could not be written, so the reset was NOT done | bring the audit store back, then reset again |
| 4 | the database cannot be reached | for a stop, and for a reset that never connected, nothing was changed; for a reset that lost the connection while it ran, it may or may not have been applied: treat the switch as ON until a read shows OFF; fix the connection |

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
  a name is any text of 1 to 63 bytes with no control, format (zero-width, bidirectional) or line-separator
  character and no space at either end (`Admin`, `my-admin`, `user@server` are fine), compared as exact text, never
  `PUBLIC`, `none`, `session_user`, `current_user`, `*` or `%` (in any letter case), and not one of the roles migrate grants; it is left out of the CREATEROLE listing only, and is still listed when it
  holds a grant on the stop tables. Its MEMBERS are still listed (a member can `SET ROLE` to it and use its
  CREATEROLE): vouching covers the role itself, not who may become it. A vouched role that is itself a member of a
  LISTED role (a grantee of a stop-table right, the reset role, or a CREATEROLE role that is not accepted) is still
  listed for that membership. Vouching for the schema owner role seeds nothing and its members are not followed: the
  owner is outside the guarantee (see above). Below PostgreSQL 16 the command prints the
  accepted names (also when it refuses) and logs them at warning level: the record of who vouched is the CI log of
  that run. From PostgreSQL 16 the option has no effect and the command says so in one line. Use it only when you
  can say who holds that login; the other way out is `REVOKE CREATEROLE` from it or PostgreSQL 16 or later.
- The append-only triggers are not enforced while `session_replication_role` is `replica`. From PostgreSQL 15 a
  superuser can let any role set it (`GRANT SET ON PARAMETER session_replication_role`). A role with DELETE or
  TRUNCATE on a stop table plus that right could remove a stop: migrate does not look at parameter rights, so do
  not grant them on a server that holds a stop switch.
- migrate refuses (ConfigError that names the schema and the search_path) when the three stop tables are not all
  found in the schema the store uses (an empty search_path, a schema without the tables, a missing table, or a
  temporary table with a stop table's name): a check that finds nothing never passes. Pin the same schema for the
  migrate and the runtime login with `options=-c search_path=<schema>` in each DSN.
- The search path (E5, 2026-11-20). A login may change its OWN default (`ALTER ROLE <runtime> SET search_path = x`),
  and a decoy schema it owns could then hold a stop table that says OFF. Two defences: (1) the store checks at
  start-up that the effective search_path of its connection is exactly the configured schema (`backends.store.db_schema`,
  else the schema the DSN pins with `options=-c search_path=<schema>`, else `public`) and that `kill_switch` is found
  in `current_schema()`; otherwise it refuses to start and the message names the schema it found. Pin the path in the
  DSN (it overrides any role default; a value with a space needs the libpq escape, `app,\ public`) or make the role
  default equal to the schema. `backends.store.db_schema` is only the EXPECTED schema: it does not choose the schema
  of the login, so set it to the same schema that you pinned. A role default or database default such as `app, public`
  or `app` is refused unless it is exactly the configured schema. (2) migrate, for every role it is given, never
  erases a role default (it reaches every database of the server): a default for this database only is reset, and a
  role-wide default that is not the schema is kept and overridden by `ALTER ROLE r IN DATABASE <this database> SET
  search_path = <schema>`. Each change is printed on stderr (`changed: ...`: role, database, old value, new value) and
  logged; roles not named are never touched. It needs a migrate login with CREATEROLE and the ADMIN OPTION on the role
  (PostgreSQL 16 and later), otherwise it refuses and names the role. A database-wide or server-wide default that is
  not the schema is refused (reset it as a role that may: `ALTER DATABASE x RESET search_path`). Not covered: a role
  default set AFTER start-up changes only new connections, which the start-up check refuses; `PGOPTIONS` in the
  environment overrides a DSN-less path and is refused the same way.
- PostgreSQL 17 MAINTAIN (E5). The MAINTAIN right lets its holder LOCK a table in any mode, so a runtime login that
  held it could block every read of the stop. From 17, migrate revokes MAINTAIN on the three stop tables from every
  role but the owner (and from PUBLIC) and refuses when a named role still holds it (membership in `pg_maintain`:
  remove that membership). The store connection sets `lock_timeout` (`defaults.STORE_LOCK_TIMEOUT_MS`, 10 s) in
  `build()`, so a lock held by someone else makes the read fail inside that time instead of hanging; a failed read
  is not an OFF answer. Below 17 the privilege does not exist and nothing is checked. Test status: the lane's test
  server is PostgreSQL 16; the PostgreSQL 17 logic is tested against a scripted connection, and a real-server test
  runs when HADAVIN_TEST_PG_DSN points at 17 or newer (not yet run).
- The guarantee is about the state stored in the database. A runtime process that is itself taken over can ignore any
  switch: stop the process too.
- Start-up self-check (E6): every runtime store (`limits stop` too) asks the database, with `has_table_privilege`, what
  its own login can do on `kill_switch`, `kill_switch_stops` and `kill_switch_clears` and refuses to start (ConfigError,
  naming the right and the table, for example `INSERT on kill_switch_clears`, never a value) when it holds any right the
  grant map does not give the runtime: UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, INSERT on the clears table, and
  so on, directly, by column grant, through a role it is a member of, or through PUBLIC. A `GRANT ALL ON ALL TABLES` run
  after migrate is caught at the next start. The reset login (marked by the `limits reset` command, not by any config
  setting) and a superuser or a member of the tables' owner (outside the guarantee) are not held to this. Only the
  runtime login is checked; the other roles still drift until the next `migrate`, so schedule `migrate` (it names all
  roles) after any provisioning step.
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

## Before and after migration 0011 (money functions)

- Stop the tick scheduler and every runtime, purge and portal process before running `migrate` for 0011. Old code
  against a migrated database, or new code before 0011, fails; do not leave a cron `tick` running across it.
- After migrate, run ONE smoke `tick` and read its result before restarting the scheduler.
- `migrate` refuses when the `hadavin_*` functions or the money tables (`spend`, `spend_month`,
  `spend_reservations`, `runs`, `hadavin_limits`) have different owners, or when a named role owns them. The message
  names the objects and owners. Run `ALTER FUNCTION <name>(<args>) OWNER TO <the one owner>` (or
  `ALTER TABLE <name> OWNER TO ...`) as that owner or a superuser, then run migrate again.
- `migrate` rewrites the rows of `hadavin_limits` on every run and takes back any hand grant on it or on a money
  function; only the owner reads or writes `hadavin_limits`.

## Release expired spend holds

After a provider outage: the live loop keeps the hold of a failed model call (ProviderError, ProviderExhausted, a crash) at the worst case, and the tick only MARKS it expired; the day and month counters do not move until the operator runs `release_expired_spend`. Enough failed runs make the agent hit `daily_budget` or `monthly_budget`: run the release below.
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
   `migrate` (so a temp table of the release login cannot stand in for a money table).
   Money guard (migration 0010, E11 M4): a BEFORE UPDATE trigger on `spend`, `spend_month` and `spend_reservations`
   that refuses, for every login but the function's owner, an UPDATE that lowers a booked amount. Since the grants flip
   (step 4, migration 0011 and `migrate`) it is a TRIPWIRE behind the wall, not the wall: the runtime login holds only
   SELECT on `spend` and `spend_month` and nothing on `spend_reservations`; it books money only through the SECURITY
   DEFINER functions. `migrate` refuses any role other than the table owner and superusers that can INSERT, UPDATE,
   DELETE or TRUNCATE a money table (PUBLIC and inherited memberships included, when roles are named). Residuals: a
   login that shares the migration owner (or is a member of the owner role) has no guard at all, so keep the runtime
   login separate from the owner; a superuser owner is not stopped; the runtime can still settle an open hold it can
   name. `migrate` pins the trigger function's search path too. The store also checks at start that the runtime login
   (and every role it is a member of, inherit option or not) holds no write right on the money tables and no EXECUTE
   on set_cap, release or purge; a login that owns a table (or is a member of its owner) or a superuser is skipped for
   that table with a WARNING in the log: this is the single-role dev escape hatch, never a production setup. Views and
   materialized views that select from the money tables are not scanned (a residual: review who may write through
   them).
   Drift: when a counter is already below the booked holds, a legal settle that lowers it is refused (fail closed) until
   the counter is repaired; `applied_usd` of a release shows such drift.
   Emergency switch-off (the OWNER only; the guards then do nothing until switched back on): `ALTER TABLE spend
   DISABLE TRIGGER spend_money_guard;` and the same for `spend_month` (`spend_month_money_guard`) and `spend_reservations`
   (`spend_reservations_money_guard`); afterwards `ALTER TABLE spend
   ENABLE TRIGGER spend_money_guard;` and so on. The
   audit guards of 0009 work the same way: `audit_entries_seq_guard` on `audit_entries`, `audit_checkpoints_seq_guard`
   on `audit_checkpoints`. Write the switch-off and switch-on into the incident log.
   Purge (E11 M3): the purge deletes only settled rows (also the rows a release settled at 0); an expired hold
   nobody settled stays, so a late settle still counts its real cost.
   A hand-run `CREATE OR REPLACE` of the function (for example the 0008 file) resets the pin to the placeholder
   `pg_catalog, pg_temp`: the function then cannot find the money tables and fails closed (it is not hijackable). Run
   `migrate` afterwards; it re-pins on every run. `migrate` must run as the function's owner: any other login gets an
   error naming the owner.
   Exit 5 is decided from what the audit chain really did: the chain never raises, it parks a failed outcome
   (the release login cannot write the outbox table, so in memory of the command) and the command then ends, so a
   parked outcome counts as lost and exits 5. Exit 5 means the outcome row MAY be missing: check the audit chain for the
   intent id first (a lost commit reply is also reported this way) before recording anything by hand.
   The release secret name may not be read by the runtime: a tool,
   source, executor or restored-hash secret that folds to the same name stops the start.
   Likewise the secrets policy of the runtime's identity must NOT list the release secret (the start check only
   sees names the runtime config reads; the policy is what keeps the secret out of reach).
Release only the holds of calls you know were not billed: a late settle of a released hold changes nothing, so a call
that really was billed is then missing from the counters.

### The alert: `check_expired_holds`

A provider outage or a revoked key leaves the worst-case hold of every failed call booked (the safe direction) until an
operator releases it; nothing else says so, the agents simply hit `daily_budget`. The tick step `check_expired_holds`
(the last step, every tick, runtime login) makes it loud. It calls the read-only function `hadavin_expired_holds`
(0011; the runtime has no right on `spend_reservations`, so the function answers: agent, day, number of holds and
their summed amount, at most 1000 groups, no hold or run id). When any expired, unreleased hold was closed more than
`EXPIRED_HOLD_ALERT_AFTER_S` ago (default 6 hours: past the one hour in which a late settle can still book the real
cost and the release is refused, with room for an operator to respond) the step fails: an ERROR line
`check_expired_holds <agent> <day>: N holds, X USD` per group and `step=check_expired_holds ...` from the tick, exit 1,
the same text in `tick_state`. It is quiet when there are none, and clears on the first tick after the release.

What it means: those holds still count against the agent's day and month counters although their calls never
settled. Recover with `hadavin-sdk release-expired AGENT --day YYYY-MM-DD --by WHO` (the release login, steps
above) for each agent and day named in the alert. If the call really did cost money (a provider that billed a failed
call), release only after checking: a release lowers the counter and a later settle of that hold is then not found.

## Caps live in a table the runtime cannot write
The day and month spend cap of every agent is read by the database from the table `hadavin_caps` (migration 0011).
The runtime login has no right on that table and cannot run `hadavin_set_cap`; only the reset login can write a cap.
The registry (`budget_usd`) stays the source you edit; an operator copies it into the table with `limits sync-caps`.
Where the two differ, the TABLE wins on PostgreSQL (the memory store has no table and compares the caps a caller passes).

Status: exact money and the no-lowering wall are in force; no-overspend holds for the live loop's main model call only and is NOT in force for the listed ungated sites until the model gate installs reserve/settle (F-install).
The runtime login can neither lower a booked amount nor change a cap (it can still read a cap, settle a hold it can name, add spend).
The live loop's main model call reserves before and settles after (B2): the reservation bounds the booked worst case per call, a reply costing more is booked in full (an overshoot, audited), and the kill switch is read before the reserve, not atomic with it; the ungated sites (see the CHANGELOG money block) are not bounded.
login holds no INSERT, UPDATE or DELETE on `spend`, `spend_month` or `spend_reservations`, SELECT on the two
counters only, and nothing on the reservations; every booking is a SECURITY DEFINER function it may EXECUTE. The
purge login holds no table right either and may only EXECUTE the purge function.

Deploy, in this order (there is no rolling upgrade):
1. Stop the tick scheduler and every runtime-side process.
2. Provision a reset login (every PostgreSQL deployment needs one now, dev and CI too) and run `hadavin-sdk migrate`
   naming ALL roles, including `--reset-role <role>`. Migrate creates the table EMPTY and never guesses or overwrites a cap.
3. Store the reset login's DSN as a secret and set `backends.store.reset_credential_ref` to its NAME (not the runtime,
   purge or release secret; not the same login under another name).
4. `hadavin-sdk limits sync-caps --by WHO --yes`.
5. Start, then run one smoke `tick`.
EVERY RUN IS REFUSED (`limits_unavailable`, for every agent) UNTIL `sync-caps` HAS COMPLETED: every agent needs a cap
row, or `hadavin_reserve_spend` (5 arguments: p_id, p_agent, p_day, p_usd, p_run_id) raises HD005 ("run limits
sync-caps"), fail closed. Afterwards `limits check-caps` (exit 1 on drift or a missing row) and the tick step
`check_caps` report any difference between registry and table. A new agent is refused the same way until its caps are synced.

Commands (all under the reset login; they refuse BEFORE any connection when `reset_credential_ref` is missing or
collides with a runtime secret, in every environment; the memory store is refused: "this store has no cap table"):
- `hadavin-sdk limits set-cap AGENT --day USD --month USD --by WHO [--yes]`: one agent. The audit intent row is
  written first, then the cap, then the outcome row (`set_cap_failed` when the write failed). The agent must be live or
  draft in the registry. If the values differ from the registry it says so: the tick then alerts until they agree.
- `hadavin-sdk limits sync-caps --by WHO [--yes]`: prints the state of every live and draft agent (`same`,
  `differs`, `missing`), then writes the ones that are not `same`: ONE intent and ONE outcome per agent, STOPPING at the
  first failure. A re-run skips what is already equal, so after a failure fix the cause and run the same command again.
  Retired agents are not synced and not deleted (their row stays, harmless) and are not reported.
- `hadavin-sdk limits check-caps`: read-only, writes no audit line. Exit 0 only when every live and draft agent matches;
  exit 1 on any difference or missing row. Run it in CI after a registry change.
Without `--yes` a run that is not interactive is refused (exit 2).
Exit codes: 0 done; 1 (`check-caps` only) a difference or a missing row; 2 refused (config, missing or colliding reset
ref, bad argument, unknown or retired agent, no `--yes`, or the login lacks the right); 3 the audit store is unavailable
(nothing changed); 4 the store is unreachable; 5 the cap IS written but its outcome row could not be audited (the audit
holds the intent row alone: record it by hand, do not repeat the write).

Drift is loud: the tick step `check_caps` (runtime login, read-only `hadavin_cap_matches`) fails the tick (exit 1, an
ERROR line `step=check_caps` naming agent ids and `differs` or `missing`, never a value) while any live or draft agent
differs. A cap LOWERED in the registry and not synced would otherwise stay high in the table; a cap RAISED and not
synced is the safe direction (the agent is refused at the lower table value) but is reported the same way. The fix is
`limits sync-caps`.
Residual: the audit line is written by the CLI, not by the function, so a stolen reset login can call `hadavin_set_cap`
directly with no audit line (the same is true of `release-expired`). Keep the reset login off the runtime machines.

## After the upgrade to 0009: the stop-year constraints
0009 adds `kill_switch_stops_ts_range` and `kill_switch_clears_ts_range` (a `ts` between 2000-01-01 and 2100-01-01)
NOT VALID and never runs `ALTER TABLE ... VALIDATE CONSTRAINT` itself (a conditional validation needs a DO block, which the repo's statement lexer
refuses). Right after the files, every `migrate` run validates each constraint whose table holds no row outside the
range, silently. A clean database therefore ends validated. A database that already holds a planted `ts` (the stop
tables are append-only, such a row cannot be deleted below a superuser) still upgrades, keeps that constraint NOT
VALID, and every `migrate` run prints one warning naming it while the row exists. Look for the rows (`SELECT id, ts FROM
kill_switch_stops WHERE ts NOT BETWEEN '2000-01-01' AND '2100-01-01'`, the same on `kill_switch_clears`), deal with
them, then validate: the next `migrate` does it by itself, or run as the owner `hadavin-sdk migrate
--validate-constraints` (only validates; it cannot be combined with a role flag, `--no-roles`, `--accept-admin-role`,
`--accept-changed-draft` or `--reset-draft`; it needs the stop tables in the schema of HADAVIN_MIGRATE_DSN).
Timeouts and exit codes. The 5-second lock wait and 60-second statement limit (`VALIDATE_LOCK_TIMEOUT`,
`VALIDATE_STATEMENT_TIMEOUT` in `store/migrate.py`) apply to the validation step ONLY, in both places it runs:
`migrate --validate-constraints`, and the settle step at the end of the file loop of every plain `migrate` (set with
`set_config(..., true)`, the same effect as `SET LOCAL`, and put back before the grant and function steps). The rest
of `migrate` has NO lock or statement limit, on purpose: a second `migrate` waits for the first on a
transaction-level advisory lock, and a lock limit would kill that wait. Exit codes, the same in both places:
- 75 (retry later, not a refusal): a lock wait over 5 seconds, a scan over 60 seconds, or a connection lost WHILE the
  validation step runs. A plain `migrate` rolls back as a whole (nothing is applied, run it again).
- 2 (refusal): a row outside the range, a login that is not the table owner (also when it only fails to read the stop
  tables), stop tables not found in the schema, or a flag combination that is not allowed.
- 3 (any other error, as for every command): including a connection that cannot be opened or is lost BEFORE the
  validation step (file loop, grants). Nothing is kept of a failed `migrate`: it is one transaction.
- 0: done.
The 60-second limit assumes small stop tables (they hold one row per stop and per clear; not measured for millions
of rows); on a far larger table raise `VALIDATE_STATEMENT_TIMEOUT` and say so in the change record. Locks: the
migration takes a brief ACCESS EXCLUSIVE lock on the stop tables for the ADD CONSTRAINT and the index build, and
because `migrate` runs every file in ONE transaction it holds that lock until the whole run commits (the settle,
grants and checks). The wait for that lock has no time limit (see above), so it queues behind any long transaction
on the stop tables, and while it queues every stop read and write behind it waits too. Stop the runtimes (or at
least their stop-table readers) before the upgrade, and check for old transactions (`pg_stat_activity`).

0009 has no watermark table (nothing read it). A database that ran an EARLIER, unreleased 0009 still has
`kill_switch_watermark` and `hadavin_watermark_guard()`: `migrate` refuses it with a message saying so. Steps:
(1) as the owner `DROP TABLE kill_switch_watermark CASCADE; DROP FUNCTION hadavin_watermark_guard() CASCADE;`;
(2) run `migrate` with the same role flags plus `--accept-changed-draft 0009_stop_state_hardening` (the 0009 file
changed since that database applied it, so migrate warns of the difference until the new checksum is accepted; the
database then matches the file); the stop-year constraints are validated by that run. Do NOT use `--reset-draft 0009_...`
for this: it deletes the ledger rows of 0009 and every later file and applies them again, which fails on the tables
they already made unless you drop all of those first (the safe choice then is a new database). The leftover check runs
before `--reset-draft`, so the leftovers must be dropped first in any case. There is no 0012: 0009 is unreleased.

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
