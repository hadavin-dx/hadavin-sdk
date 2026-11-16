# External dead-man check on `tick_state.last_ok_at` (note only: no core code)

RUNG: existing code. The tick already writes one `tick_state` row per step with `last_run_at`, `last_ok_at` and `last_error`
(`runtime/tick.py:319`, `store.save_tick_state`; table in `store/migrations/0003_approvals_tick.sql:30-35`). Nothing new is built in core.
The check is a query run by something OUTSIDE the tick process.

STATUS: the query and the identity below were run on 2026-11-16 on a throwaway Postgres 16.15 with only the `tick_state` table (taken from
the migration file) and made-up rows. Raw commands and output: `../fix-patchcopies1.md`. NOT tested: against the real store, with a real
scheduler, or with an alert channel.

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
plain number (no quotes). Without it `psql` stops with a syntax error and exit code 3, which counts as "cannot check" (rule 4 below).
Suggested value: 3 times the tick period (a tick runs every 30-60 s), so `180`; the studio head sets it.

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
(the password comes from the secrets kind, never typed into the command). Alert when the output has any line, OR when `psql` exits non-zero.
The query reads only `step`, `last_ok_at` and `last_run_at`. It does not read `last_error`, so error text can never reach the alert channel.

Example of an unhealthy result (made-up data: `sweep` never succeeded, `stuck` last succeeded 10 minutes ago, `audit_reconcile` has no row):
```
audit_reconcile|||MISSING (no row: never ran)
stuck|2026-11-16 14:28:52+00|2026-11-16 14:38:52+00|STALE (last success older than the limit)
sweep||2026-11-16 14:38:52+00|NEVER SUCCEEDED
```
Healthy: no output, exit code 0. (All of these were seen on the throwaway database; timestamps shortened here.)

## The read-only identity (PROPOSAL: the studio head decides; REVIEW.md D-3 (2) and the identity table row `dead-man reader` under X-6.6)
Name: `deadman_reader` (a proposed name). Who creates it: the studio head's session, as the database owner, at set-up time; the tick, the
agent and this check never create it. Its one grant (one right, the reason is in the last column):

| Statement (run once by the database owner) | Reason |
|---|---|
| `CREATE ROLE deadman_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;` | its own identity, no password in this file (set it through the secrets kind) |
| `GRANT CONNECT ON DATABASE <database> TO deadman_reader;` | to open a connection |
| `GRANT USAGE ON SCHEMA public TO deadman_reader;` | to see the table's schema |
| `GRANT SELECT (step, last_ok_at, last_run_at) ON tick_state TO deadman_reader;` | to read the sign of life; not `last_error` |

Positive test (seen): with this identity the query above returns the unhealthy rows. Refused (seen, each `permission denied`):
`SELECT last_error FROM tick_state`, `SELECT * FROM tick_state`, `INSERT`, `UPDATE`, `DELETE` on `tick_state`, `SELECT` on another table,
`CREATE TABLE` in schema `public`. After `REVOKE SELECT ON tick_state FROM deadman_reader` the check exits 3 with `permission denied`.
UNVERIFIED: Postgres 16.15 only; other versions, a managed database service, and the interaction with the repository's own grant map
(`store/migrate.py:46-68`, not changed here) were not checked. The `PUBLIC` default rights of the client's database may differ.

## Rules for where it runs (to keep it independent)
1. It runs as `deadman_reader` only: no other table, no write right (least privilege). The agent and the tick hold no approver or executor credential and do not hold this one.
2. It runs outside the process and outside the scheduler it watches. If it runs on the same machine as the tick, a machine failure silences both; say which failure it does and does not cover.
3. Its alert goes over a channel that is not the one the tick or the app uses. Which second channel (and who pays) is a studio-head decision (system-map Decision B); this note does not pick one.
4. It alerts on an unreachable store and on any non-zero exit too: a check that cannot read the store has failed, and says so.

## What it does not cover
A tick that runs and succeeds while doing the wrong thing; a slow mail server (the step finishes, the mail is late); an `audit_reconcile` that
drains 0 events because the audit write path itself is broken (the A-01 warning and error log lines cover that).

## Negative test (to run when it is set up, by the lead)
Stop the tick for longer than the limit and confirm the query returns the five names and the alert fires; start it again and confirm the result is
empty. Then revoke the identity's SELECT and confirm the check alerts "cannot read" instead of staying silent (seen on the throwaway database;
the version with a real tick was not run). The grant and revoke need the database owner's identity; the lead's session holds it, not this check.
