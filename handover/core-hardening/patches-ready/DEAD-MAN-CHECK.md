# External dead-man check on `tick_state.last_ok_at` (note only: no core code)

RUNG: existing code. The tick already writes one `tick_state` row per step with `last_run_at`, `last_ok_at` and `last_error`
(`runtime/tick.py:323`, table in `store/migrations/0003_approvals_tick.sql:30-35`). Nothing new is built in core. The check
is a query run by something OUTSIDE the tick process.

## What it checks
A tick that has stopped (scheduler dead, container gone, store unreachable) writes nothing, so it cannot report its own
silence. The check asks the store whether each step has succeeded recently.

Steps that run every tick (`every_s` 0 and no `interval`): `sweep`, `reconcile`, `stuck`, `checkpoint`, and `audit_reconcile`
if patch A-01 is applied. Their `last_ok_at` must be newer than a limit. Steps with their own interval (`purge_evidence`,
`reprobe_sources`) need that interval plus a margin as their limit, or are left out.

```sql
-- Returns one row per step that has NOT succeeded within the limit (empty result = healthy).
-- :limit_s = 3 x the tick period (a tick runs every 30-60 s, so 180 s is a reasonable start; the studio head sets it).
SELECT step, last_ok_at, last_run_at, last_error
FROM tick_state
WHERE step IN ('sweep', 'reconcile', 'stuck', 'checkpoint', 'audit_reconcile')
  AND (last_ok_at IS NULL OR last_ok_at < now() - make_interval(secs => :limit_s));
```
A step that is missing from the table also counts as unhealthy (it has never run): compare the returned list against the
five names, or `LEFT JOIN` them from a `VALUES` list.

## Rules for where it runs (to keep it independent)
1. It runs as its own read-only database identity: SELECT on `tick_state` only, no other table (least privilege).
2. It runs outside the process and outside the scheduler it watches. If it runs on the same machine as the tick, a machine
   failure silences both; say which failure it does and does not cover.
3. Its alert goes over a channel that is not the one the tick or the app uses. Which second channel (and who pays) is a
   studio-head decision (system-map Decision B); this note does not pick one.
4. It alerts on an empty or unreachable answer too: a check that cannot read the store has failed, and says so.

## What it does not cover
A tick that runs and succeeds while doing the wrong thing; a slow mail server (the step finishes, the mail is late); an
`audit_reconcile` that drains 0 events because the audit write path itself is broken (the A-01 warning log line covers that).

## Negative test (to run when it is set up, by the lead; not run here)
Stop the tick for longer than the limit and confirm the query returns the five names and the alert fires; start it again and
confirm the result is empty. Then revoke the identity's SELECT and confirm the check alerts "cannot read" instead of staying silent.

Status: UNVERIFIED (static text; no query was run). Cites re-read at b4cce5b: `runtime/tick.py:323`, `0003_approvals_tick.sql:30-35`.
