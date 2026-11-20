# draft-F-store (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

# DRAFT TICKET F-store (owner: SPINE): store-backed pre-call reserve and settle

Read-only draft; nothing was run, edited or checked out. S = `src/hadavin_sdk` on main 51c9fc4fb (snapshot `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main`). Line numbers are main's today; steps A and B land first and will shift `tick.py` STEPS, `migrate.py` GRANTS and the two pins.

## Purpose
Today a model call is checked before (`Limits.blocked`) and booked after (`Limits.charge`), so 50 callers can all pass the check before any of them books. After F-store the worst-case cost is booked on the day and month counters before the call, in one database transaction that refuses at the cap. The real cost replaces it after the call. A process that dies in between leaves the worst case booked.

## NEEDED-CHECK
- Check and booking are two separate calls: `S/limits.py:17-18` (charge) and `20-30` (blocked, "a read, no write").
- Booking happens after the call: `S/runtime/agent_loop.py:485` (reply) and `325` (judge verdict); the pre-check is `251`.
- `add_spend` is an unconditional upsert with no cap: `S/store/postgres.py:416-431`, `S/store/memory.py:196-204`.
- No reservation table exists: migrations stop at `0005_evidence.sql`; `spend` is `0001_core.sql:87-92`, `spend_month` is `0003_approvals_tick.sql:15-20`.
- One store object is one connection behind one lock (`S/store/postgres.py:193-197`), so a threaded test on one store proves nothing.
- No tick step for reservations: `S/runtime/tick.py:249-266`.
- Not needed, already there: UTC day and month buckets, `spend_totals`, the `store` fixture over both kinds (`tests/contracts/conftest.py:30`), the purge-identity wiring (`S/app.py:198-207`).

## Smallest shape
- The counters `spend` and `spend_month` now include open holds; no second counter. So `spend_totals` and `Limits.blocked` need no code change.
- Reserve is one transaction: insert the reservation row, seed the two counter rows with 0, then one conditional UPDATE per counter (day first, then month). Zero rows from either UPDATE raises and rolls everything back.
- Settle is one transaction: claim the row first, then move day and month by `actual - reserved` on the reservation's own day.
- Expire is a status change only; the counters do not move, so the worst case stays booked.
- A release is `settle(id, Decimal(0))`; there is no release method or status.
- Reservation ids are always fresh (`res-` + uuid4 hex) and reserve is never retried, so reserve needs no replay logic: a duplicate id is `StaleState`.

```sql
-- reserve, steps 3 and 4 (cap passed as a parameter; zero rows = refused, whole transaction rolls back)
UPDATE spend SET usd = usd + %(amt)s
 WHERE agent_id = %(agent)s AND day = %(day)s AND usd < %(cap)s AND usd + %(amt)s <= %(cap)s RETURNING usd;
UPDATE spend_month SET usd = usd + %(amt)s
 WHERE agent_id = %(agent)s AND month = %(month)s AND usd < %(cap)s AND usd + %(amt)s <= %(cap)s RETURNING usd;
-- settle, step 1 (the claim); zero rows = return the stored row unchanged, or NotFound
UPDATE spend_reservations SET status = 'settled', settled_usd = %(a)s, closed_at = clock_timestamp()
 WHERE reservation_id = %(id)s AND (status = 'open' OR (status = 'expired' AND %(a)s > reserved_usd))
 RETURNING *;
-- settle, steps 2 and 3: usd = usd + (actual - reserved) on the row's day, then its month; zero rows raises
-- expire
UPDATE spend_reservations SET status = 'expired', settled_usd = reserved_usd, closed_at = clock_timestamp()
 WHERE status = 'open' AND created_at < clock_timestamp() - make_interval(secs => %(age)s);
-- purge (purge role)
DELETE FROM spend_reservations WHERE status <> 'open' AND closed_at < %(before)s;
```
`usd < cap` keeps today's rule that an agent at its cap is blocked even for a zero-cost call (`limits.py:26`).

## INVARIANTS
1. **Atomic reserve.** On PostgreSQL the cap check and the booking are the same UPDATE statement, in the same transaction as the reservation insert. For N concurrent reserves of amount w against cap c from separate connections, exactly floor(c/w) succeed, and the counter never exceeds c through reserves.
2. **All or nothing.** A refused or failed reserve leaves no reservation row and no counter change. A failed settle leaves the row open and both counters unchanged.
3. **Idempotent settle.** For one reservation id the counters move at most once (open to settled), plus at most one upward move (expired to settled when actual > reserved). `settled` is terminal; any later settle returns the stored row and changes nothing.
4. **Crash rule.** An open reservation older than the expiry age becomes `expired` with `settled_usd = reserved_usd`. The counters keep the worst case; after expiry the booked amount never goes down.
5. **Day and month together.** Both counters move in one transaction, always day then month (the same order as `add_spend`), so no deadlock.
6. **Midnight rule.** The day is the UTC date at reserve time (`now().date()`, as `limits.py:18`), stored in the row. Settle and expire act on that stored day and its month, never on today's.
7. **Overshoot.** A settle above the reserved amount is booked in full with no cap check. It is recorded as `settled_usd > reserved_usd` in the row plus one audit outcome. Every later reserve on that day or month is refused until the counter is below the cap.
8. **Fail closed.** Any exception from the store or the kill switch read inside `Limits.reserve` becomes `SpendRefused("limits_unavailable")`. No exception path returns an id.
9. **Amounts.** `worst_usd` and `actual_usd` are finite Decimals >= 0. The table CHECK also refuses NaN and Infinity (upper bound). Nothing is rounded.
10. **Expiry clock.** Expiry age uses the database clock only; `created_at` is never passed by the store method.
11. **Stated limit.** The runtime login can UPDATE its own counters (as today, `migrate.py:53-54`). Reservations protect against races and crashes, not against a hostile runtime login. The memory store guarantees nothing across processes.
12. **Purge.** Purge deletes closed rows only. If the purge role deletes an open row, the worst case stays booked (the safe direction).

## Migration `0007_spend_reservations.sql`
```sql
CREATE TABLE spend_reservations (
    reservation_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    day DATE NOT NULL,
    run_id TEXT,
    reserved_usd NUMERIC NOT NULL CHECK (reserved_usd >= 0 AND reserved_usd < 1000000000),
    settled_usd NUMERIC CHECK (settled_usd >= 0 AND settled_usd < 1000000000),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'settled', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    closed_at TIMESTAMPTZ,
    CHECK ((status = 'open') = (settled_usd IS NULL)),
    CHECK ((status = 'open') = (closed_at IS NULL)),
    CHECK (status <> 'expired' OR settled_usd = reserved_usd)
);
CREATE INDEX spend_reservations_open ON spend_reservations (created_at) WHERE status = 'open';
```
- No foreign key, trigger, sequence or change to `spend` / `spend_month`. Both statements pass the guard's `_SAFE_CREATE` (`migrate.py:80-85`).
- **GRANTS** (one row, same PR, `check_grants` is two-way at `migrate.py:150-166`): `"spend_reservations": Grant("table", _RW, purge="DELETE", purge_cols=("status", "closed_at"))`.

| Role | Rights on `spend_reservations` |
|---|---|
| runtime | SELECT, INSERT, UPDATE |
| purge | DELETE, plus SELECT on `status` and `closed_at` only |
| portal | none |
| reset (step B) | none |

- **Manifest**: `tests/fixtures/migrations_released.json` gains `0007_spend_reservations` with the sha256 of the LF-normalised file, written at merge.
- **Pins**: `tests/test_migration_numbers_guards.py:363` goes from 6 (after B) to 7; `tests/test_p2_postgres.py:290` list gains `"0007_spend_reservations"`; `tests/test_p7_tick.py:82-89` gains the new step name.
- Not needed: a `TABLES` row at `tests/test_p2_postgres.py:31` (the loop at 63 covers listed tables only).
- UNVERIFIED: whether `tests/test_migration_numbers.py:486-491` needs a row; it looks like a synthetic list (it holds `0004_x.sql`).

## Store Protocol additions (`S/store/protocol.py`, both stores)
```python
class SpendCapExceeded(RuntimeError):
    def __init__(self, which: str) -> None:  # "day" or "month"; day is checked first
        super().__init__(f"{which} cap reached"); self.which = which

def reserve_spend(self, reservation_id: str, agent_id: str, day: date, usd: Decimal, *,
                  day_cap: Decimal, month_cap: Decimal, run_id: str | None = None) -> None:
    """Book usd on day and month or book nothing: SpendCapExceeded, StaleState (id exists), ValueError (amount)."""
def settle_spend(self, reservation_id: str, actual_usd: Decimal) -> SpendReservation:
    """The stored row after the call. NotFound for an unknown id; ValueError for a bad amount."""
def expire_spend_reservations(self, older_than_s: int) -> int: ...
def purge_spend_reservations(self, before: datetime) -> int: ...
```
- `SpendReservation(Shape)` goes in `S/models.py` (Shape is at `models.py:55`) with the nine table columns.
- **Postgres**: each write is `with self._lock, self._db.transaction()` (pattern at `postgres.py:419`). `UniqueViolation` maps to `StaleState` (pattern at `postgres.py:302`). The isolation level stays the default READ COMMITTED: the conditional UPDATE relies on the re-check after a row-lock wait, and T1 proves it.
- **Memory**: a dict of reservations under `self._lock`. The month is the existing sum over days (`memory.py:199-203`); a settle adjusts `_spend[(agent, row.day)]`.
- `missing_methods` (`protocol.py:151`, `app.py:194`) will refuse a custom store without the four methods; update its docstring.
- No getter, list, release, run cap, meta, retry wrapper or timeouts.

## INTERFACE (ii): what the gate wrapper calls
```python
# S/limits.py
class SpendRefused(RuntimeError):
    """Do not call the model. reason is one of:
    kill_switch | daily_budget | monthly_budget | limits_unavailable | bad_amount"""
    def __init__(self, reason: str) -> None:
        super().__init__(reason); self.reason = reason

class Meter(Protocol):  # implemented by Limits (store) and by k1b Budget (memory, install ticket)
    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str: ...
    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal: ...
```
Contract:
1. `reserve` returns a reservation id only after the worst case is booked. Any exception from `reserve` means no model call; `SpendRefused.reason` is the audit error code. An unknown agent is a `KeyError`, as in `blocked` today (`limits.py:25`).
2. `settle` returns the overshoot (`max(0, actual - reserved)`, 0 when none). It may be called any number of times; the first call wins.
3. Real cost known, including a refused request that cost nothing: call `settle(id, reply.cost_usd)` or `settle(id, Decimal(0))`.
4. Real cost unknown (timeout, abandoned thread, crash): do not settle. The worst case stays booked and the sweep closes the row.
5. If `settle` raises (store down after the call), the gate returns the reply anyway. The worst case stays booked; the gate does not retry `reserve`.
6. `Limits.reserve` order: validate the amount, read the kill switch, then `store.reserve_spend(id, agent_id, now().date(), worst_usd, day_cap=budget.daily, month_cap=budget.monthly, run_id=run_id)`. `SpendCapExceeded.which` maps to `daily_budget` / `monthly_budget`, the same codes as `agent_loop.py:251-255`.
7. `Limits.settle` writes one `audit.write_outcome` (domain `limits`, operation `overshoot`, the row's `run_id`) when the overshoot is above zero. It never raises from the audit.
8. A stop set between the kill switch read and the booking lets that one call through (plan B3: "takes effect at the next gate check").
9. `run_id` is stored for investigation only; no run cap is enforced here.
10. Note for the gate ticket, not F-store: `worst_case_usd` (`S/k1b/loop.py:115-122`) counts the system prompt and messages only, not documents or tools, and counts one attempt. The runtime passes documents and tools (`agent_loop.py:470-476`) and `NetworkLLM._retry` can re-send (`llm/common.py:233`). Unless the gate's estimate covers those, overshoot becomes the normal path.

## Sweep tick step
- `expire_reservations(ctx)` calls `ctx.app.store.expire_spend_reservations(defaults.RESERVATION_EXPIRE_S)` and logs the count at WARNING when it is above zero.
- Appended last as `TickStep("expire_reservations", 0, expire_reservations)` (the contract at `tick.py:4-5` is append-only). It runs on the runtime DSN.
- Purge: one line in `purge_evidence` (`tick.py:186+`) on `app.purge_store or app.store`: `store.purge_spend_reservations(ctx.now - timedelta(days=keep.held_tool_calls_max_days))`. This reuses the 400-day ceiling; no new config.

## `Limits.charge` and `Limits.blocked`
- **`charge`**: untouched in F-store. It books on the same counters, so mixed use stays consistent. The install change deletes it together with `agent_loop.py:325` and `485`. The 11 `.charge(` hits under `tests/` then split: those on `Limits` (for example `tests/test_s5_runtime.py:109, 116`) switch to `store.add_spend`; those on k1b `Budget` belong to the install ticket.
- **`Store.add_spend`**: stays.
- **`blocked`**: code unchanged. Its totals now include open holds. It remains the cheap pre-check and kill switch read for `_limits_stop` (`agent_loop.py:251, 716, 790`); `reserve` is the authority.
- **Behaviour changes to state in CHANGELOG**: a call whose worst case does not fit is refused even when some budget is left (today one call may overshoot). A run can see `daily_budget` while another call's hold is still open.

## Tests (written by a different agent than the builder)
**Contract, both stores (`tests/contracts/test_store.py`, `store` fixture)**
- Reserve books day and month; settle lower, equal and higher.
- Exact-cap reserve passes; one micro over is refused with `which="day"`; the month cap binds when lower.
- Budget 0 refuses even amount 0.
- A refused reserve leaves totals and rows unchanged; a duplicate id is `StaleState` and booked once.
- Unknown id on settle is `NotFound`.
- NaN, Infinity and negative amounts are `ValueError` on reserve and settle, with nothing booked.
- Expire with age 0 closes the row with totals unchanged; expire leaves young rows alone; expire twice returns 0 the second time.
- Purge removes closed rows only.

**T1 (Postgres only, `tests/contracts/test_t1_reserve_cap.py`)**
- 50 `PostgresStore` objects from `make(...)`, one per thread (pattern `tests/test_p7_store.py:176-193`), one Barrier. Assert 50 distinct `pg_backend_pid()`.
- Cap 3.00, worst 1.00: exactly 3 granted, 47 `SpendCapExceeded`, total 3.00 read from a 51st connection before any settle.
- No caller settles until all have decided (Schedule from T1-T2-tests `meter_support.py:135`).
- Variants: cap 2.50 gives 2; month cap binding; 50 agents times 1 caller each do not block each other.
- Control: the same schedule with check-then-`add_spend` admits more than 3, which shows the test can fail.
- UNVERIFIED: that the CI Postgres service allows 51+ connections (default 100).

**Crash**
- C1: a spawned child reserves, commits and is killed. The totals hold the worst case; after expire the row is `expired` and the totals are unchanged.
- C2: a child blocked on a day row the parent holds `FOR UPDATE` is killed. No row and no counter change.
- C3: fault injected at the month UPDATE in reserve. No row, day unchanged.
- C4: fault injected at the month UPDATE in settle. Row still open, both counters unchanged.
- C5: late settle after expiry. A lower amount changes nothing; a higher amount raises both counters to the actual.

**Midnight**
- Reserve with day D, settle when today is D+1: only D and D's month move.
- Jan 31 into Feb 1: January's month moves, February stays 0.
- A full day D does not block D+1; a full month blocks D+1.
- `Limits.reserve` at 23:59:59.999999 UTC books D, using FakeClock from T1-T2-tests `meter_support.py:60`.

**Idempotent settle**
- Twice with the same amount; twice with different amounts (the first wins and the returned row is equal).
- 8 connections settle one id with different amounts: one is booked.

**Overshoot**
- Cap 1.00, reserve 0.60, settle 1.50: total 1.50, the row shows 1.50 > 0.60, `Limits.settle` returns 0.90 and writes one audit outcome.
- The next reserve of 0.000001 and of 0 is refused; the next day is free.

**Unreadable store**
- `reserve_spend` raising `OperationalError`, `StoreUnavailable` or `RuntimeError` gives `SpendRefused("limits_unavailable")`.
- `get_kill_switch` raising gives the same.
- A closed connection, and UPDATE on `spend` revoked from the runtime role, both refuse with nothing booked.
- Kill switch on gives `SpendRefused("kill_switch")` with nothing booked.

**Negative per role (real logins via `pg_schema(runtime=True)`; expect `InsufficientPrivilege`, a missing relation is not a pass)**
- Runtime: DELETE and TRUNCATE on `spend_reservations`.
- Purge: SELECT on `reserved_usd`, `agent_id`, `run_id`; INSERT; UPDATE; any right on `spend` or `spend_month`.
- Purge positive: the purge DELETE works.
- Portal and reset: no right at all.
- `migrate` refuses after a hand `GRANT DELETE ON spend_reservations` to the runtime role (`effective_problems`, `migrate.py:342`).

**Tick**
- The step is last in STEPS; a failing store marks the step FAILED and the other steps still run.

**Mutants**
1. Day cap clause removed.
2. Month cap clause removed.
3. `<=` becomes `<`.
4. `usd < cap` removed.
5. Check by SELECT, then an unconditional UPDATE.
6. Reservation insert outside the transaction.
7. Settle claim without the status test.
8. Delta sign flipped.
9. Settle uses today's day.
10. Month key taken from today.
11. Expire sets `settled_usd` to 0 or lowers the counters.
12. Expire ignores the age.
13. An expired row may settle lower.
14. Actual clamped to reserved.
15. `Limits.reserve` returns an id after a store error.
16. `Limits.reserve` skips the kill switch.
17. Runtime grant gains DELETE.
18. Tick step row removed.
19. Purge deletes open rows.

## Branch mining
All three PRs are OPEN. None of the four branches is an ancestor of another. Their merge-bases are 8 to 13 commits behind main.

| Branch | Drags along | As is | With edits | Not reused |
|---|---|---|---|---|
| `origin/core/P4d` (PR 66, da08ce2e2) | 13 files: 8 existing, 5 new; +1824 | Nothing | `test_store_money_baseline.py` as a checklist of bad amounts (it pins that `add_spend` books negatives and NaN) | `store_support.py`, `test_store_registry.py` (604), `test_pg_driver.py`; main already has the `store` fixture over both kinds |
| `origin/core/P4d-a2` (PR 75, a8abba0f9) | 39 files: 22 existing, 17 new; +6681; also `pyproject.toml` and `uv.lock` (which dependency is UNVERIFIED) | Nothing (its migration is numbered 0006, taken by step B) | See list below | See list below |
| `origin/core/P4b1` (PR 79, 8cc2021f7) | 37 files: 18 existing, 19 new; +5676; carries its own copy of the 0006 migration and store changes | The one-line map `{"day": "daily_budget", "month": "monthly_budget"}` (`meter.py:47`) | Nothing | `meter.py` (434) and `money.py` (112), replaced by the two `Limits` methods; `Limits.caps`, `hold`, callbacks. Only the header and outline of `meter.py` were read; `test_meter_processes.py` not read |
| `origin/core/T1-T2-tests` (1a7d20290) | 11 files: 2 existing, 9 new; +1536 | `tests/pg_dsn.py` (16 lines) plus the 8-line `kinds/store_postgres.py` hunk (missing DSN fails when `CI=true`) and `tests/test_pg_dsn_guard.py` (60, not read); it also edits `tests/demo_askdata/conftest.py` (6 lines). `test_store_time_rules.py` (23 tests) as a regression suite while `Limits.charge` exists | See list below | `meter_memory_killers.py` |

P4d-a2 with edits:
- The table DDL: drop `schema_version`, `meta`, `expired_at`, `released`, the foreign key to `runs`, the lock timeout and both trigger functions (about 45 of 69 lines).
- `postgres.py` 647-763: keep the counter-row seeding and the day and month conditional UPDATEs; drop the run step, the kill switch read, meta, the day-bound check and the replay branch.
- `_close` 765-815: keep the claim-first order; change the delta.
- The sweep statement 848-866: drop SKIP LOCKED, the limit and the sort.
- `SpendCapExceeded`, trimmed.
- `tests/contracts/reserve_workers.py` `race` and `reserve_then_hang`: remove `lock_timeout_ms` and `call_budget_ms`, which `PostgresSettings` on main lacks (`S/backends/table.py:116`); use the new signature.
- Test ideas from `test_store_reserve_proofs_pg.py` lines 300, 313, 540, 761, 1070.

P4d-a2 not reused: the `_writes` retry wrapper, `StoreBusy`, `_map_error`, the `check_usd` / `check_cap` / `check_meta` / `check_text` / `check_id` family (about 150 lines of `protocol.py`), `release_spend`, `list_open_reservations`, `get_spend_reservation`, `SpendOutcome`, `MAX_COUNTER_USD`, the config price validator (that is step C), `pg_owner.py`, `test_store_writes_pg.py`, `test_store_hostile.py`. Only the test names of `test_store_reserve.py` were read (30 tests).

T1-T2-tests with edits:
- `tests/meter_support.py`: FakeClock, `build_limits`, Schedule and oracle are reusable; `run_parallel` is threads on one store, so use it for the memory store only.
- `test_t1_meter_cap.py`: the "admits ceil(cap/cost)" cases become floor; the two negative and NaN pin tests flip to refused.
- `postgres_mutants.py` / `meter_mutants.py`: keep the file format; replace the mutant bodies.

## Out
- Run cap inside the store (`agent_loop.py:256-260` and `add_cost` stay).
- Caller-supplied reservation ids or reserve replay.
- A release status.
- Triggers or append-only rules on the table.
- Retry, lock timeout or call budget.
- A database-clock bound on `day`.
- A CHECK on `spend.usd`.
- Per-expiry audit rows.
- Sweep limit or SKIP LOCKED.
- Six-decimal rounding and `SpendMicro`.
- k1b `Budget.reserve` / `settle`, deleting the charge sites, the gate wrapper and the judge binding (install and TEXT tickets).
- A stale-price check.

## Open questions (recommended answer)
1. **May a late settle after expiry lower the booking?** No, raise-only. The cost is that a call slower than the expiry age is charged its worst case.
2. **Expiry age.** Constant `defaults.RESERVATION_EXPIRE_S = 3600`, no config field. It must exceed the longest model call including retries; UNVERIFIED what that maximum is on the runtime path.
3. **Overshoot audit: in `Limits.settle` or in the gate?** In `Limits.settle`, about 4 lines, so both `Meter` implementers keep one signature.
4. **Does the T1 branch's `pg_dsn.py` (CI fails on a missing DSN) come in with F?** Yes, since "NOT RUN = not done" (`resolve-plan-1.md:7`).
5. **Retention of closed rows.** Reuse the 400-day ceiling.
6. **Should `reserve` refuse an unknown agent as `SpendRefused`?** No, keep the `KeyError`; it is still no call.

## Size
- SQL: about 16 lines.
- Source: about 225 lines (protocol 35, postgres 75, memory 45, limits 40, models 12, tick 10, migrate and defaults 4, pins 4).
- Tests: about 600 lines.
- Docs: about 20 lines.

## Files read
- `C:\Users\rakes\Downloads\Hadavin\egm\core-complete-2026-11-20\plan-v4-final.md`, `review-plan-1-design.md` (the six D5 invariants are at line 17 of this file, not in `review-plan-2-design.md`), `review-plan-2-design.md`, `review-plan-3-codebase.md`, `tickets\draft-A-B.md`
- `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main\src\hadavin_sdk\`: `limits.py`, `store\protocol.py`, `store\postgres.py`, `store\memory.py`, `store\migrate.py`, `store\migrations\`, `runtime\tick.py`, `runtime\agent_loop.py`, `k1b\loop.py`, `llm\common.py`
- `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main\tests\`: `contracts\test_store.py`, `contracts\kinds\store_postgres.py`, `test_p7_store.py`, `test_p7_tick.py`, `test_p2_postgres.py`, `test_migration_numbers_guards.py`, `fixtures\migrations_released.json`
- Branches read with `git show` / `git diff` in `C:\Users\rakes\Downloads\Hadavin\projects\hadavin-sdk`
