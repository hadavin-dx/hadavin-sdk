# P2a round 7 probes (run by the resolve session, throwaway PostgreSQL 16.15, psql 16, 2026-11-05)

Server `/tmp/pgprobe`, port 54329, host 127.0.0.1, database `p2a7` (dropped/recreated; not kept). Purpose: check SQL claims of round 7 (order 7). Nothing run against the repository suites. `psycopg` is not installed in this session (`ModuleNotFoundError`), so nothing about psycopg itself was run.

Setup: table `t(id int primary key, v bool)`, view `vw` over it, role `p7rt` (login) with SELECT on `vw` only; table `req(id bigserial primary key, b text)`; SECURITY DEFINER function `stopfn()` that inserts into `req`, EXECUTE granted to `p7rt`. Runtime-like sessions use `PGOPTIONS="-c lock_timeout=1500"` so a wait ends in 1.5 s.

## P1. COR-R7-2 / ADV-R7-3: a role with no table privilege still WAITS for the table lock (CONFIRMED)
Another session holds `LOCK TABLE t IN ACCESS EXCLUSIVE MODE` for 6 s. As `p7rt`:
| statement | result |
|---|---|
| `select count(*) from vw` (view-only role) | `ERROR: canceling statement due to lock timeout` after 1.5 s |
| `update t set v=true` (NO privilege on `t`) | `ERROR: canceling statement due to lock timeout` after 1.5 s (not 42501) |
| `select stopfn()` (touches `req`, not `t`) | returned `1` at once |
| `select has_table_privilege('t','UPDATE')` (run while `t` locked) | `f` at once |
Reading: the privilege check comes AFTER the table lock, so the ticket's dry run (`UPDATE kill_switch` expecting 42501 "before any row lock") can wait and time out; a catalog function (`has_table_privilege`) never waits.

## P2. ADV-R7-4: a stop function waits behind a queued DDL on its own table (CONFIRMED)
Session A: `begin; select count(*) from req; select pg_sleep(5)` (holds ACCESS SHARE). Session B: `alter table req add column z int` (queues for ACCESS EXCLUSIVE). Then as `p7rt`: `select stopfn()` -> `ERROR: canceling statement due to lock timeout` after 1.5 s (the function's INSERT queued behind the waiting DDL). So "takes no lock that another caller can wait on" is false while a migration DDL is queued; the wait is bounded only by the DDL's own `lock_timeout` (or the stopper's).

## P3. COR-R7-6: a bigint argument does not resolve to a function declared `(text, int)` (CONFIRMED)
`create function rf(a text, n int)`; `rf('a', 5::int8)` -> `ERROR: function rf(unknown, bigint) does not exist`; `rf('a', 5::int2)` -> `5`; `rf('a', 5::int8::int)` -> `5`. Whether psycopg3 sends a Python int as int8 for a small value is UNVERIFIED here (psycopg not installed); a cast in the SQL text removes the question.

## Not probed
COR-R7-3 (empty `Grant` rights through `check_grants`), COR-R7-4 (`tick_state` semantics), ADV-R7-1/2 race and livelock arguments (reasoned from the function text, not run), ADV-R7-9 (cluster `max_connections`).
