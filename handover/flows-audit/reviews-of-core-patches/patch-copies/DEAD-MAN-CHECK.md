# External dead-man check on `tick_state.last_ok_at` (note only: no core code)

RUNG: existing code. The tick already writes one `tick_state` row per step with `last_run_at`, `last_ok_at` and `last_error`
(`runtime/tick.py:319`, `store.save_tick_state`; table in `store/migrations/0003_approvals_tick.sql:30-35`). Nothing new is built in core.
The check is a query run by something OUTSIDE the tick process.

STATUS: the query and the first four statements of the identity below were run ONCE on 2026-11-16 on a throwaway Postgres 16.15 with only the
`tick_state` table (taken from the migration file) and made-up rows: "seen once on a throwaway Postgres, not the real store". Raw commands and
output: `../fix-patchcopies1.md`. UNVERIFIED (this second pass was static: no database was started): the statements added in this pass (the
`REVOKE ... FROM PUBLIC` lines, `default_transaction_read_only`, `CONNECTION LIMIT`, `statement_timeout`, the password step), the real store, a real
scheduler, an alert channel. **Needs the lead: the real store is not available to this static review; a run on the real store (or a copy of it)
must happen before sign-off. Input: a test database with the real migrations applied. Next step: run the "Negative test" section there.**

## Do this first: apply patch A-01
The step `audit_reconcile` exists only after `A-01.patch` is applied (see `README.md`). Without it the query below reports
`audit_reconcile` as MISSING on every run and always alarms. If A-01 is not applied, delete the `('audit_reconcile')` entry from the
`VALUES` list (four names: `sweep`, `reconcile`, `stuck`, `checkpoint`).

## What it checks
A tick that has stopped (scheduler dead, container gone, store unreachable) writes nothing, so it cannot report its own silence. The check
asks the store whether each step has succeeded recently. Steps that run every tick: `sweep`, `reconcile`, `stuck`, `checkpoint`, and
`audit_reconcile` (after A-01). Steps with their own interval (`purge_evidence`, `reprobe_sources`) are left out; to add one, use its
interval plus a margin as its own limit.

## The query, in a runnable form
Save as `dead-man-check.sql`. Placeholder rule: `:limit_s` is a `psql` variable, set on the command line with `-v limit_s=<seconds>`; it must be a
plain number (no quotes). Without it `psql` stops with a syntax error and exit code 3, which counts as "cannot check" (rule 4 below). An unreachable store gives exit code 2.
Suggested value: 3 times the tick period (a tick runs every 30-60 s), so `180`; the studio head sets it. The query assumes the table is the
unqualified `tick_state` in schema `public` (as the migration creates it); with another schema, qualify it.

```sql
-- One row per tick step that is MISSING from tick_state, never succeeded, or has not succeeded within the limit.
-- An empty result means healthy.
SELECT w.step,
       t.last_ok_at,
       t.last_run_at,
       CASE
           WHEN t.step IS NULL THEN 'MISSING (no row: never ran)'
           WHEN t.last_ok_at IS NULL THEN 'NEVER SUCCEEDED'
           ELSE 'STALE (last success older than the limit)'
       END AS problem
FROM (VALUES ('sweep'), ('reconcile'), ('stuck'), ('checkpoint'), ('audit_reconcile')) AS w(step)
LEFT JOIN tick_state t ON t.step = w.step
WHERE t.step IS NULL
   OR t.last_ok_at IS NULL
   OR t.last_ok_at < now() - make_interval(secs => :limit_s)
ORDER BY w.step;
```
Run: `psql -h <host> -U deadman_reader -d <database> -v ON_ERROR_STOP=1 -v limit_s=180 -At -f dead-man-check.sql`
(the password comes from the secrets kind, never typed into the command). Alert when the output has any line, OR when `psql` exits non-zero. Exit codes of `psql` (its manual): 2 = it could not connect (store
unreachable or login refused); 3 = the script failed (with `ON_ERROR_STOP`), for example a missing `-v limit_s` or `permission denied`; 1 = another
fatal error of `psql` itself.
The query reads only `step`, `last_ok_at` and `last_run_at`. It does not read `last_error`, so error text can never reach the alert channel.

Example of an unhealthy result (made-up data: `sweep` never succeeded, `stuck` last succeeded 10 minutes ago, `audit_reconcile` has no row):
```
audit_reconcile|||MISSING (no row: never ran)
stuck|2026-11-16 14:28:52+00|2026-11-16 14:38:52+00|STALE (last success older than the limit)
sweep||2026-11-16 14:38:52+00|NEVER SUCCEEDED
```
Healthy: no output, exit code 0. (All of these were seen on the throwaway database; timestamps shortened here.)

## The read-only identity (PROPOSAL: the studio head decides; REVIEW.md D-3 (2) and the identity table row `dead-man reader` under X-6.6)
Name: `deadman_reader` (a proposed name). **Who runs these statements: a named human (the database owner of the client's or the studio's database),
signed in with a SEPARATE database login that is not the login the app, the tick or any agent uses. No agent session creates or holds this role's
owner login** (one identity per function, the least-privilege rule). Who that person is: the studio head names them; not stated in the patches.
The tick, the agent and this check never create the role. Each statement and its reason:

| Statement (run once, in this order, by the database owner) | Reason |
|---|---|
| `CREATE ROLE deadman_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;` | its own identity; no password text in this file or in any command line |
| Password step: the human generates the secret through the secrets kind (a named lookup, for example `deadman_reader_password`; the value is never typed into a file, a chat or a shell history), then in `psql` runs `\password deadman_reader` and pastes it at the hidden prompt, and stores the same secret for the scheduler through the secrets kind. If the client's database supports short-lived tokens or client certificates, use those instead of a password. | the role cannot log in without a credential; this keeps it out of the repository and the logs |
| `REVOKE CREATE ON SCHEMA public FROM PUBLIC;` and `REVOKE TEMPORARY ON DATABASE <database> FROM PUBLIC;` | rights every role gets through the group `PUBLIC` by default (create tables in `public` on Postgres 14 and older; temporary tables). Revoking them from `PUBLIC` also removes them from every other role that relies on `PUBLIC`: the database owner first lists who does (`\dn+ public`, `\l+`) and gives explicit grants where needed. UNVERIFIED against the real store's roles |
| `GRANT CONNECT ON DATABASE <database> TO deadman_reader;` | to open a connection (do NOT revoke `CONNECT` from `PUBLIC` here: that would lock out other logins) |
| `GRANT USAGE ON SCHEMA public TO deadman_reader;` | to see the table's schema |
| `GRANT SELECT (step, last_ok_at, last_run_at) ON tick_state TO deadman_reader;` | to read the sign of life; not `last_error` |
| `ALTER ROLE deadman_reader SET default_transaction_read_only = on;` | every session of this login starts read-only, a second lock beside the missing write grants |
| `ALTER ROLE deadman_reader CONNECTION LIMIT 2;` | a stuck or abused check cannot use up the database's connections |
| `ALTER ROLE deadman_reader SET statement_timeout = '5s';` | a slow query is cancelled; the check then exits non-zero and alerts |

Seen once on the throwaway Postgres (rows 1, 4, 5 and 6 only: the first pass): with this identity the query above returns the
unhealthy rows. Refused (each `permission denied`): `SELECT last_error FROM tick_state`, `SELECT * FROM tick_state`, `INSERT`, `UPDATE`, `DELETE` on
`tick_state`, `SELECT` on another table, `CREATE TABLE` in schema `public`. After `REVOKE SELECT ON tick_state FROM deadman_reader` the check exits
3 with `permission denied`. To run on the real store (needs the lead): the same list, plus `SHOW default_transaction_read_only;` and
`SHOW statement_timeout;` as that login (expect `on` and `5s`), a third connection attempt while two are open (expect "too many connections for
role"), and `SELECT pg_sleep(10);` (expect "canceling statement due to statement timeout").
UNVERIFIED: Postgres 16.15 only; other versions, a managed database service, and the interaction with the repository's own grant map
(`store/migrate.py:46-68`, not changed here) were not checked. The `PUBLIC` default rights of the client's database may differ.

## Rules for where it runs (to keep it independent)
1. It runs as `deadman_reader` only: no other table, no write right (least privilege). The agent and the tick do not hold this login; that nobody holds more than this was asserted by the rule, not checked here. Which login the tick itself runs under: the patches do not say; `REVIEW.md` X-6 says one runtime login serves agent, tick and approval receiver; whether a deployment splits them: not stated: the lead answers.
2. It runs outside the process and outside the scheduler it watches. If it runs on the same machine as the tick, a machine failure silences both; say which failure it does and does not cover.
3. Its alert goes over a channel that is not the one the tick or the app uses. Which second channel (and who pays) is a studio-head decision (system-map Decision B); this note does not pick one.
4. It alerts on an unreachable store and on any non-zero exit too: a check that cannot read the store has failed, and says so.

## What it does not cover
A tick that runs and succeeds while doing the wrong thing; a slow mail server (the step finishes, the mail is late); an `audit_reconcile` that
drains 0 events because the audit write path itself is broken: the step still records a success, so this check stays green. The A-01 warning and
error log lines are written at the moment a write fails, but NOTHING reads those lines or alerts on them (no alert kind exists in `src`; a person
or a log tool the client sets up would have to), so today they cover nothing automatically. "Green" means the step ran, not that the backlog is empty.
An audit kind with no `reconcile` method: with the A-01 patch in this folder the step FAILS (its `last_ok_at` stays empty, so this check reports
NEVER SUCCEEDED); an earlier version of the patch skipped quietly and recorded a success, which would have shown green. `K1bAudit`
(`k1b/audit_sink.py`) has no `reconcile`, but it is used only by the `k1b` commands, not by the tick (`cli.py:213`, `app.py:161`).

## Negative test (to run when it is set up, by the lead)
Stop the tick for longer than the limit and confirm the query returns the five names and the alert fires; start it again and confirm the result is
empty. Then revoke the identity's SELECT and confirm the check alerts "cannot read" instead of staying silent (seen once on the throwaway
database; the version with a real tick and the real store was not run: needs the lead, see STATUS). The grant and revoke need the database owner's
login, held by the named human of the identity section, not by this check and not by an agent session.
