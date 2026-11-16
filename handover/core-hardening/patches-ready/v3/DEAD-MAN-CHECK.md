# Outside check that the tick is still running (v3; a note only, no core code)

Status: UNVERIFIED. This is static text. No query was run and nothing was set up. Cites read at `b4cce5b`:
`runtime/tick.py` (`_run_step`, `STEPS`), `store/migrations/0003_approvals_tick.sql:30-35`, `store/migrate.py` (`GRANTS`).

RUNG (tool ladder), corrected: rung 1 for the data (the tick already writes one `tick_state` row per step), rung 2 first
(if the client already has a monitor or alert tool, it runs the query), otherwise rung 3 (a ready-made scheduled query plus
alert tool). v1 said "existing code" for the whole check; that was wrong, because the reader and the alert do not exist.
Custom code (rung 7) is only the K7 alternative below. Nothing in this file is built.

## What it checks
A tick that has stopped (scheduler dead, container gone, store unreachable) writes nothing, so it cannot report its own
silence. The check asks the store whether each step has succeeded recently.

Steps that run every tick (`every_s` 0 and no `interval`): `sweep`, `reconcile`, `stuck`, `checkpoint`, and `audit_drain`
if patch A-01 v3 is applied. Their `last_ok_at` must be newer than a limit. `purge_evidence` and `reprobe_sources` have
their own intervals: use that interval plus a margin as their limit, or leave them out.

```sql
-- PostgreSQL ONLY (make_interval and now() are not SQLite; the memory store has no outside reader at all).
-- Returns one row per listed step that has NOT succeeded within the limit.
-- :limit_s = 3 x the tick period (a tick runs every 30-60 s, so 180 s is a start; the studio head sets it).
SELECT step, last_ok_at, last_run_at, last_error
FROM tick_state
WHERE step IN ('sweep', 'reconcile', 'stuck', 'checkpoint', 'audit_drain')
  AND (last_ok_at IS NULL OR last_ok_at < now() - make_interval(secs => :limit_s));
```

### Reading the result (v1 mixed this up)
- Rows returned = at least one listed step is late or has never succeeded: ALERT.
- No rows returned does NOT by itself mean healthy. A step missing from the table (never ran) gives no row. Compare against
  the five names, for example `LEFT JOIN` them from a `VALUES` list so a missing step shows as a row with `last_ok_at`
  empty. Healthy = the join returns no late row AND all five names were found.
- An error, a timeout or an unreadable store = ALERT too (the check could not look).

### Clock skew
`last_ok_at` is written with the clock of the machine that runs the tick (`ctx.now`, the app clock), but `now()` above is
the database server's clock. If the two differ by more than a few seconds the check fires late or early. Keep both on NTP;
the limit (180 s) must be far larger than any expected skew. Compare against `max(last_ok_at)` of a step known to be alive
if skew cannot be ruled out.

## Rules for where it runs (to keep it independent)
1. It runs as its own database identity with SELECT on `tick_state` and nothing else. That identity does NOT exist today:
   `tick_state` is not marked `portal` in `GRANTS` (`store/migrate.py`), and `migrate` only knows the runtime, portal and
   purge roles. A migration change is needed to grant it (a new role entry in `GRANTS`/`migrate`), with a negative test:
   the identity is denied SELECT on every other table, and denied INSERT, UPDATE and DELETE on `tick_state`.
   Reusing the portal role would widen the portal's reads; do not.
2. The reader is to be decided by the studio head (who runs it, where, and who pays). This note does not pick one.
3. It runs outside the process and outside the scheduler it watches. If it runs on the same machine as the tick, one
   machine failure silences both; say which failure it does and does not cover.
4. Its alert goes over a channel that is not the one the tick or the app uses (system-map Decision B; studio head).
5. It alerts on an unreadable or empty answer as in "Reading the result".

## Alternative: the external heartbeat (K7)
`runtime/tick.py` (module docstring) records an external heartbeat as PENDING (K7): the CLI would send a ping for every exit
code, and a dead-man service on the receiving side alerts when pings stop. That needs no database identity and no
Postgres, but it is custom code and a second service. Choose between this query and K7 before building either; do not build
both. Differences: the query sees per-step failures; the ping sees only that a tick process started and ended.

## What it does not cover
A tick that runs and succeeds while doing the wrong thing; a slow mail server (the step finishes, the mail is late); a
broken audit write path that fills the outbox: that case now FAILS the `audit_drain` step (A-01 v3), so `last_ok_at` stops
advancing and this check fires. A damaged outbox item (a damaged row, or a file in `outbox/corrupt/` or the spill folder's
`corrupt/`) keeps the step failing until a person deals with it (A-01 README, "What a person does"). Events held only in
another process's memory (no spill folder configured, or the spill folder also failed) are invisible to the tick.

## Negative test (to run when it is set up, by the lead; not run here)
Stop the tick for longer than the limit; confirm rows for all five names and that the alert fires; start it again and
confirm no row and all five names found. Revoke the identity's SELECT and confirm the check alerts "cannot read" instead of
staying silent. Break the audit outbox (A-01 stuck-database case) and confirm `audit_drain` appears as late.
