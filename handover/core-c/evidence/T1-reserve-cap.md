# T1: 50-connection cap test and the 0007 grants negative tests (STANDING ORDER 016, backlog item 7)

Written by a test-writer agent of session core-c on 2026-11-20 (06:15 to 06:22 UTC). The builder of the store,
of migration 0007 and of its GRANTS row is session core-b. Nothing was pushed or committed by this agent.

## Inputs (fetched, tips saved)
| ref | tip | what is on it |
|---|---|---|
| refs/inputs/cloud-core-b | 576f2924eaa47bae46f6376174e46fe6fda51782 | F-store code IS pushed, commit 8db9c29 "code F-store: spend reservations (migration 0007), store reserve/settle/expire/purge, Limits.reserve and settle, sweep tick step" |
| refs/inputs/cloud-core-a | 0e7d539eedc966e7359265e64b5e3419a1496d5a | a first tests/contracts/test_t1_reserve_cap.py (WIP snapshots, last cea9a7f) and tests/contracts/test_store_spend_reservations.py |

core-b's pushed code, on refs/inputs/cloud-core-b:
- src/hadavin_sdk/store/postgres.py:603 `reserve_spend`, :664 `settle_spend`, :705 `expire_spend_reservations`, :715 `purge_spend_reservations`
- src/hadavin_sdk/store/migrations/0007_spend_reservations.sql (one table, one partial index)
- src/hadavin_sdk/store/migrate.py:56 `"spend_reservations": Grant("table", _RW, purge="DELETE", purge_cols=("status", "closed_at"))`
- src/hadavin_sdk/limits.py:60 `Limits.reserve`, :92 `Limits.settle`; src/hadavin_sdk/store/protocol.py:50 `SpendCapExceeded`; src/hadavin_sdk/models.py:322 `SpendReservation`

## What core-a had (kept, all 8 tests unchanged in body)
tests/contracts/test_t1_reserve_cap.py, written before the code existed: 50 stores are 50 backend pids; cap 3.00
and worst 1.00 for the day and for the month counter (3 granted, 47 refused, counters at 3.00 read from one more
connection, then settle); the control with the old check-then-add pattern; four role tests (runtime no DELETE,
purge DELETE plus two columns, portal none, reset none). Its reset test skipped while `migrate` had no
`reset_role`; on core-b's code it runs.

## What this agent wrote
1. tests/contracts/test_t1_reserve_cap.py (714 lines, sha256 badfda3b...95b75): core-a's file EXTENDED.
   Changed in core-a's part, three places only: the docstring; `LANDED` is now detected on the `Store` protocol
   (needs no psycopg); a new autouse fixture `_no_silent_skip` FAILS when the DSN is set and psycopg is missing.
   Added below the line "core-c additions" (16 test cases, 12 functions):
   - the 51st connection reads the granted sum BEFORE any settle, is a 51st backend pid, one open row per granted
     id, no row for a refused one, one day and one month counter row;
   - exactly floor(cap / worst) for five pairs: 3.50/1.00 = 3, 0.07/0.01 = 7, 1.00/0.30 = 3, 0.99/1.00 = 0, 50.00/1.00 = 50;
   - two agents on the same 50 connections: 3 each; a month cap reached over two days: 3 in total, day counters add up to the month;
   - settle: 50 connections settle ONE reservation with 50 different amounts: one applied, 49 not, all 50 get the
     same stored row, counters moved once; settle above the reserve (2.50 on 1.00) books 4.50 past the cap and all
     50 are then refused; settles below free room for exactly 2 new ones; settle at 0 gives exactly 3 again;
   - expiry: sweep at 3600 s touches nothing, sweep at 0 expires 3, counters stay, cap stays shut for all 50; 50
     sweeps at once expire each row once (counts add up to 3); settle after expiry: lower changes no counter,
     higher raises them by the difference, a second settle changes nothing; 25 settles racing 25 sweeps on one row
     end in one of the two stated results (0.25 booked when settle came first, 1.00 when the sweep came first).
2. tests/test_grants_negative_0007.py (420 lines, sha256 9d753102...d94d), NEW: 9 pure-Python cases (the GRANTS
   row against a hand-written second copy, 0007 creates one table and no sequence) and 16 PostgreSQL cases
   asserting `psycopg.errors.InsufficientPrivilege` for runtime, portal, purge, reset and a never-granted role:
   one statement per privilege (SELECT, INSERT, UPDATE, DELETE, TRUNCATE), per-column SELECT, UPDATE, INSERT,
   the catalog (has_table_privilege incl. REFERENCES and TRIGGER, has_column_privilege), statements on real
   rows, and the four store methods under the wrong identity. Helpers `_as`, `_schema`, `_statements`,
   `PRIVILEGES` are imported from tests/test_grants_negative_roles.py, not copied.

Both files were copied into /home/user/hadavin-sdk/tests/ (neither existed there). In core-c's tree (no step F,
migrations end at 0005) they skip with their own reason; they start running the day core-b's code is merged.

## Commands and raw output tails
Worktree: `git worktree add --detach /tmp/core-c-t1 refs/inputs/cloud-core-b` (576f292). Python 3.13.18 of the
repo .venv, psycopg 3.3.6, `PYTHONPATH=/tmp/core-c-t1/src` (checked: `hadavin_sdk.__file__` was the worktree's).
PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1), started as the postgres user, data under /tmp/core-c-t1-pg,
listen_addresses=127.0.0.1, a free port, trust; max_connections=200.

Lint (worktree, and again on the copies in the repo):
```
$ ruff check tests/test_grants_negative_0007.py tests/contracts/test_t1_reserve_cap.py
All checks passed!
$ ruff format --check tests/test_grants_negative_0007.py tests/contracts/test_t1_reserve_cap.py
2 files already formatted
```
Without a DSN, on core-b's code:
```
$ env -u HADAVIN_TEST_PG_DSN pytest tests/contracts/test_t1_reserve_cap.py tests/test_grants_negative_0007.py -q -rs
SKIPPED [1] tests/test_grants_negative_0007.py:381: HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)
9 passed, 40 skipped in 0.31s
```
With the PostgreSQL 16 DSN, on core-b's code (first try, then once more: same result):
```
$ HADAVIN_TEST_PG_DSN="host=127.0.0.1 port=<free port> user=postgres dbname=postgres" pytest tests/contracts/test_t1_reserve_cap.py tests/test_grants_negative_0007.py -q -rs
.................................................                        [100%]
49 passed in 14.86s
.................................................                        [100%]
49 passed in 14.52s
```
(24 in the T1 file, 25 in the grants file; 0 skipped, 0 failed.)

Can the tests fail? Two hand mutants in the worktree, each reverted with `git checkout --`:
```
mutant 1: both cap conditions removed from the two UPDATEs of reserve_spend (postgres.py:631 and :643)
  15 failed, 9 passed in 11.19s        (first failure: "At index 0 diff: 50 != 3")
mutant 2: GRANTS row widened (runtime + DELETE, portal=True, purge reads reserved_usd)
  16 failed, 14 passed, 19 deselected in 5.22s   (13 in the new grants file, 3 of core-a's role tests)
```
In core-c's own tree (/home/user/hadavin-sdk, no step F), with and without the DSN:
```
49 skipped in 0.29s      reasons: "core-b step F not landed: Store.reserve_spend missing" and
49 skipped in 0.19s               "migration 0007 not in this tree: no spend_reservations row in migrate.GRANTS"
```

## NOT RUN, and why
- PostgreSQL 17 (the lead's batch uses 17.10) and Python 3.12: only 16.15 and 3.13.18 were available here.
- The whole suite, mypy, bandit, the mutant scripts: out of this task; only the two files were run.
- core-a's tests/contracts/test_store_spend_reservations.py: not touched, not run.
- The two files together with core-c's own source tree and step F: no merged tree exists yet.
- Each concurrency test ran twice; no repeat loop (for example 100 runs) was done to look for a rare interleaving.

## Mismatches and notes: published interface (inputs/interfaces-from-core-b, version 2.1) against core-b 576f292
1. A reservation of 0 at a full counter is refused. src/hadavin_sdk/store/postgres.py:631 and :643 add
   `usd < cap` to the condition; protocol.py:203 says so ("A counter that is already at its cap ... refuses").
   The README says only "refuses when a counter would pass its cap". Read in the code, not run.
2. Extra amount limits. protocol.py:67-80 `check_spend_amount` refuses an amount >= 10**9, more than 12 decimal
   places, or an int; the README says "amounts are finite Decimals >= 0, nothing rounded" with no upper bound.
3. An expired row carries `settled_usd = reserved_usd` (postgres.py:709; table CHECK in 0007 line 17) and its
   first settle sets status 'settled' with `settled_usd = max(actual, reserved)` (postgres.py:655-661).
   i_store_spend.py does not state either. The new tests assert the amounts and do not assert that status word.
4. `settle_spend` can raise `RuntimeError("spend counter row missing")` (postgres.py:697), not in the README's
   error column (NotFound, ValueError).
5. core-c's OWN earlier file tests/test_grants_negative_roles.py (commit 327ef82) does not match core-b's code:
   run in the worktree against core-b 576f292 it gives `8 failed, 25 passed` (identities and Grant fields pin
   without `reset`; WRITES without spend_reservations; purge DELETE and purge_cols lists; the stop table rows;
   the two strict xfail step-B tests now XPASS). That file says in its docstring this is intended until it is
   changed on purpose. It must be updated when step B and step F are merged; this agent did not change it.
6. PostgreSQL itself lets a role that holds DELETE take `LOCK TABLE ... IN ACCESS EXCLUSIVE MODE`, so the purge
   role can block the runtime's reservations for as long as it holds the lock. This is the database's rule, not a
   grant in GRANTS; the lock statement is asserted as refused for portal, reset and the never-granted role only.
   Not run for the purge role (stated from the PostgreSQL manual), so it is listed here as a limit, not a finding.
7. No mismatch found in the names: `SpendCapExceeded` (protocol.py:50), `SpendReservation` (models.py:322), the
   four method signatures and the grants are as i_store_spend.py and the README state them.

## Clean-up
PostgreSQL stopped (`pg_ctl -m fast stop`: "server stopped"), /tmp/core-c-t1-pg removed, worktree /tmp/core-c-t1
removed (`git worktree remove --force`). The branch of /home/user/hadavin-sdk was not switched; the only files
added to its working tree are the two test files and this evidence file. A temporary copy of
tests/test_grants_negative_roles.py lived in the worktree only (core-b's ref does not have it) and went with it.
