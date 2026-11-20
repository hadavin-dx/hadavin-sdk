# Review 1: migrations 0009 (stop state hardening) and 0010 (money guard)

Reviewer: fresh hostile reviewer, read-only on source. Branch `cloud/core-b`. PostgreSQL 16.15, throwaway schemas and roles
(`m9_*`, dropped afterwards; verified none left). Repros: `/tmp/core-b-scratch-M9/r1.py` (seq guard, checkpoints, money guard),
`r2.py` (settle-then-inflate, upgrade of an existing database), `r3.py` (cost of the guard). Run with `.venv/bin/python`.
All results below were observed, not argued.

## Verdict
0010 does NOT keep its promise: a runtime login lowers a booked counter with three different compositions, one of them
a single legal settle plus plain UPDATEs. 0009's seq guard is bypassed by a temp table of the caller (the search path
pin is `FROM CURRENT` = the bare schema, no `pg_temp` last). 0009 can make an existing database unmigratable.

## Findings

### H1 (High) Money guard: allowed fall is not consumed, so it can be spent repeatedly
`0010_money_guard.sql:36-50`. `allowed_fall` is recomputed per UPDATE from the holds settled in this transaction and is
never decremented by earlier falls. The exact bypass asked about works.
Scenario: counter 100 (90 of it an add_spend charge, 10 a hold). In one transaction the runtime settles the hold at 0
(legal), then `UPDATE spend SET usd = usd - 10` three times; each statement sees `OLD.usd - NEW.usd = 10 <= 10` and
`NEW.usd >= booked (0)`. Observed: all three OK, counter 100 -> 70 (r1.py "lower by 10 #0..2"). The loop can run until
the counter equals the booked holds, so every add_spend charge on that day is erasable. The comment (`:11-12`, runbook
line 162) "by the amount of a real settle ... and no further" is false.
Fix idea: the fall must be bounded by the cumulative delta of the transaction, e.g. require `NEW.usd >= OLD.usd -
allowed_fall` against the value at transaction start (not OLD of the statement), or better: derive the counter's floor from
`sum(booked holds) + non-hold charges` stored in a column the runtime cannot lower, or remove the legal-settle exception
and make settle go through a SECURITY DEFINER function (the release function pattern).

### H2 (High) Money guard: the "legal settle" is forgeable by construction (no hold needed)
`0010_money_guard.sql:37-38,43-44`. `allowed_fall` counts any row with `status='settled' AND closed_at >=
transaction_timestamp() AND reserved_usd > settled_usd`. Two ways to make such a row without a real settle:
1. INSERT (the trigger is BEFORE UPDATE only; the runtime has INSERT): `INSERT INTO spend_reservations (reservation_id,
   agent_id, day, reserved_usd, settled_usd, status, closed_at) VALUES ('fake','ag','2026-11-10',90,0,'settled',now())`,
   then `UPDATE spend SET usd = 10`. Observed: counter 100 -> 10, both OK (r1.py "insert fake settled hold").
2. Settle a hold for real at `reserved = settled`, then raise `reserved_usd` on that row (raising is allowed,
   `:25`) and lower the counter by the inflated difference. Observed: settle OK, inflate to 1000 OK, `usd 100 -> 10`
   OK (r2.py; note a separate-transaction version of this is refused because `closed_at` is old).
Also: the runtime holds UPDATE on spend_reservations, so it can mark any open hold `settled` with a lower `settled_usd`
and lower the counter by the difference: that IS "a legal settle" by construction (it is the settle), so a login can
shrink any open hold of any agent/day. The guard cannot tell the store's settle from the login's hand-written one; the
only protection is bounded by "never below booked holds", which H2.1 also defeats by inserting a hold that is itself settled
at 0.
Net: for H1/H2 the promise "only `limits release-expired` takes back a booked amount" does not hold for a login that
writes SQL. Tests miss all of this: `tests/test_money_guard_pg.py` `lowering_attacks` runs single statements outside a
settle; `test_a_settle_in_the_same_transaction_does_not_open_the_counter_further` (`:174`) tests one extra fall only; no
test composes INSERT of a settled row, repeated falls, or inflate-after-settle. The mutant battery therefore cannot see them.
Fix idea: add `BEFORE INSERT` rules (a row may only be inserted `open`, `closed_at IS NULL`), refuse a raised
`reserved_usd` on a closed row and on any row whose status/settled changes in the same UPDATE, and fix H1.

### H3 (High) Seq guard bypassed by a temp table (search path pin has no `pg_temp` last)
`0009_stop_state_hardening.sql:57-59,65`. `SET search_path FROM CURRENT` captures what the migrate connection has: the bare
schema (`search_path = m9_s_xxx`, observed in `pg_proc.proconfig`). PostgreSQL searches `pg_temp` first for relations
when it is not listed, and `pg_catalog` first for functions. The comment says a temp table "cannot stand in"; it can. Also
`_pin_search_path` is not applied to this function, so migrate never corrects it (and `FROM CURRENT` pins whatever the
operator's search path was, public included).
Repro (runtime login, r1.py): `CREATE TEMP TABLE audit_entries (seq bigint); INSERT INTO pg_temp.audit_entries VALUES
(3999999999999999999); INSERT INTO <schema>.audit_entries ... seq 4000000000000000000` -> OK; the planted row exists
and wedges the chain (every later append is last + 1). A direct plant of 99 is refused ("got 99, last 0") so the guard works
only against the naive attacker. TEMP is granted to PUBLIC by default.
Fix: `SET search_path = pg_catalog, pg_temp` in the file and `migrate` re-pins to `pg_catalog, <schema>, pg_temp` on every
run (like the money guard), or schema-qualify with `TG_TABLE_SCHEMA` via `format('%I.audit_entries')`; add `audit_entries`
and the guard function to the re-pin list and to a `check`.

### M1 (Medium) 0009 can make an existing database unmigratable
`0009_stop_state_hardening.sql:28-31`. `ADD CONSTRAINT ... CHECK (ts BETWEEN ...)` without `NOT VALID` validates every row.
0006 only enforced `isfinite`, and the stop tables are append-only (UPDATE/DELETE/TRUNCATE trigger refused), so a planted
`0100-01-01 BC` row (the very thing this migration defends against) cannot be removed by anyone below a superuser who
disables the trigger. Repro (r2.py): stage at 0008, insert `ts = '0100-01-01 BC'`, run migrate -> `CheckViolation
"kill_switch_stops_ts_range" ... is violated by some row`; ledger stays at 0008, 0010 never applies, deployment is stuck;
`DELETE` -> "the audit log is append-only". Fix: `ADD CONSTRAINT ... NOT VALID` (still enforced for new rows) and a
separate, documented `VALIDATE CONSTRAINT`, or migrate pre-checks and prints the offending ids with the manual remedy.
Same `ADD CONSTRAINT` takes ACCESS EXCLUSIVE on the stop tables and `CREATE INDEX` (non-concurrent) blocks stop INSERTs
for the build; small tables, say so in the runbook.
The `audit_entries` seq guard itself does not break upgrade (it is insert-time only); an existing gap or planted seq is
not detected or repaired either (the chain continues from planted + 1 and keeps looking valid).

### M2 (Medium) Seq guard does not cover `audit_checkpoints`
`audit_checkpoints` grants runtime INSERT. `signed_through()` is `MAX(seq)` and `checkpoint()` returns early when
`signed_through() >= seq` (`chain.py:622-640`). Observed: runtime inserted a checkpoint `seq = 4e18` -> OK. After that no
checkpoint is ever signed again (unsigned tail grows silently). The same wedge the seq guard was added to stop; one more
trigger (seq <= last audit seq, hash equals that row's hash) or a CHECK is needed.

### M3 (Medium) Money guard cost: no index for the per-settle scans
`0010_money_guard.sql:37-48`. Every counter-lowering UPDATE (practically every settle below the reservation) runs two
aggregates over `spend_reservations` filtered by `(agent_id, day)` / month range; the table has only the PK, a partial
`created_at` index and a partial `closed_at` index. Measured 22 ms for 200k rows (r3.py), linear in table size, under the
counter's row lock (serialises one agent's settles); expired unsettled holds are never purged so the table grows. Add
`CREATE INDEX ... ON spend_reservations (agent_id, day)` in 0010 (it only passes `_SAFE_CREATE`).

### L1 (Low) Guard drift behaviour
`NEW.usd >= booked` (`:50`): when a counter is already below the booked holds (the drift the release function documents
with `applied_usd`), a perfectly legal store settle that lowers it is refused with `insufficient_privilege` and the settle
fails until an operator intervenes. Fail-closed but a new outage mode; mention in the runbook or allow a fall that does not
widen the gap.

### L2 (Low) Owner equals runtime login
`:58` lets `current_user = owner of the release function` through. A deployment where migrate and the runtime share one login
(or the runtime is a member of the owner role) has no guard at all; `migrate` checks membership among named roles only, not
membership in the function owner. Add the check (or refuse when the runtime role is the owner / member of it).

### L3 (Low) Concurrency/lock: seq guard is fine, but only because of the advisory lock
Observed/reasoned: `ORDER BY seq DESC LIMIT 1` uses the PK backwards (cheap). A rolled-back append consumes no seq (seq is
computed, not a sequence), so no gap. Two chain appends serialise on `pg_advisory_xact_lock`. A writer without the lock
(the reset or release login if they bypass ChainAudit, or a future writer) reads the same last, then blocks on the PK and
fails with `UniqueViolation`, not a check violation: no deadlock, but a hard failure instead of a retry. Today the only
`INSERT INTO audit_entries` is `chain.py:294`, so reset/release go through the chain and are compatible with retry,
reconcile and outbox drain; the runbook sentence "any future writer must take the chain lock" is the only enforcement.
Multi-row `INSERT ... VALUES` batches by a non-chain writer would also be refused unless the volatile trigger read sees its
own earlier rows; not used today.

## Checked and fine
- migrate.py: `GRANTS` rows for `kill_switch_resets` (reset: SELECT, INSERT; runtime: nothing) and `kill_switch_watermark`
  (runtime SELECT; reset SELECT, INSERT, UPDATE) are applied to every named role; portal has `portal=False` on both and
  `_excess_privileges` iterates `GRANTS`, so it has nothing; `check_grants` is two-way and caught my staged DB with 0009
  removed ("GRANTS names ... which no migration creates"). `_pin_money_guard` runs on every migrate (after the migration
  loop, before the release pin), pins `pg_catalog, <schema>, pg_temp` (observed in proconfig), and is a no-op before 0010.
- Release function passes the guard (owner is `current_user` in its body); `current_user` cannot be imitated by a login.
- Month boundary: `r.day >= OLD.month AND r.day < (OLD.month + INTERVAL '1 month')::date` is right; holds are attributed to the
  hold's own day.
- A plain lowering by the runtime login, and the old watermark rewind/delete, are refused.
- Planted stop years in a fresh schema are refused by the named CHECKs.

## Rollback and runbook
- No down migration. Reverting Python is safe (the triggers only refuse), but the files and GRANTS rows must stay (migrate
  refuses an applied migration without its file). To switch the money guard off in an emergency the OWNER runs `ALTER TABLE
  ... DISABLE TRIGGER`; nothing says so. Say so, plus the matching `ENABLE` after.
- The 0009 text says the guard cannot be wedged by a planted seq; with H3 and M2 it can. Runbook line 162 ("no further")
  must be corrected whichever way H1/H2 are fixed; B-stop-state 'B7 follow-up' line 224 "temp table cannot stand in" and F-store E11
  M4 "Known limit" are inaccurate for the same reasons.
- The `0010` ledger dependency on 0009 is only in prose in F-store; the manifest fixture does not mention 0009/0010 yet
  (`tests/fixtures/migrations_released.json` has no entries), so check it is written at merge.
