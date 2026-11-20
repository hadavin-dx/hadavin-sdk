# Money path hostile re-read 2 (reviewer HR1, branch cloud/core-b head)

Scope read as one system: migrations 0007, 0008, 0010, 0011; store/postgres.py (reserve/settle/expire/purge/add_spend/release/set_cap/cap_matches, `_money_error`); store/memory.py; store/migrate.py (GRANTS, FUNCTION_GRANTS, MONEY_FUNCTIONS, `_apply_money_functions`, `_money_table_writers`, ledger); limits.py; runtime/agent_loop.py (reserve and `_settle_model_call`); runtime/tick.py; cli.py limits commands.
Evidence: scratch DB `hadavin_test_hr1` (PG 16.15, superuser owner, roles hr1_*), plus a second scratch DB rebuilt from the 87f1ffd6f drafts (dropped). No src or tests were edited.

## What I tried and could NOT break (CONFIRMED by run or trace)
- Runtime login with only EXECUTE (as `hr1_runtime`): direct UPDATE of spend / spend_reservations, set_cap, release, purge: all `permission denied`. Wall holds.
- settle of an open hold below its reserved amount lowers the day and month counter by exactly `reserved - actual` of THAT hold, on the hold's own day/month rows, once (second settle: `claimed=f`, nothing moves). Reserve + settle-at-0 with new ids nets to zero. Bounded; no escape.
- add_spend of -1: `22023 invalid argument: p_usd`. expire at age 0: `22023` (min_expiry_age 3600).
- Three bookable days (skew 1) with day cap 10, month cap 12: second reserve refused `month`. Month cap bounds the three days; the 3x day cap residual is as documented.
- Month boundary: a hold keeps its own day/month for settle, expire and release (all use `rec.day` / `p_day`); no double count, no escape. Booking "tomorrow" on the last day of a month uses next month's counter early, it does not exceed any month cap.
- Lock order (reservation row, day, month) is the same in reserve, settle, release; expire locks only reservation rows; add_spend day then month. No cycle found.
- All DEFINER functions pin `pg_catalog, <schema>, pg_temp`, use only pg_catalog builtins, no dynamic SQL; Python calls them schema-qualified. Second schema in the same database: pins are per schema (migrate re-pins with `current_schema()`); no cross-tenant path found (see m4 for the one assumption).
- Expire then late settle: books `max(actual, reserved)`, counters rise only by the positive delta; after a RELEASE the late settle returns `claimed=false` and its real cost is lost, bounded by that hold's reserved amount and by `min_expiry_age`.

## Blocker
none that breaks a cap on a correctly migrated database.

## Major

### M1. A database that ran an earlier draft of 0010/0011 keeps working, or keeps an exploitable function, and migrate only warns (CONFIRMED)
- Where: store/migrate.py:1067-1073 (UNRELEASED_MIGRATIONS), 1140-1192 (`_verify_applied`, warning branch ~1163), 900-917 (`_unmapped_functions`).
- Precondition: DB migrated with a draft 0011 from commit dcf564ba4..87f1ffd6f (7-argument `hadavin_reserve_spend(text,text,date,numeric,numeric,numeric,text)`, caps passed by the caller), runtime login granted EXECUTE on it by the old migrate.
- Steps: upgrade the package, run `migrate` with all five roles. Result (I ran it): the checksum warning, then `ConfigError: hadavin_* functions in neither map: hadavin_reserve_spend(...7 args...)`, whole transaction rolled back, exit non-zero. The old function is untouched and `has_function_privilege('hr1_runtime', old7, 'execute')` stays true. As the runtime: `select hadavin_reserve_spend('x1','ag1', today, 500, 1e12, 1e12, 'r')` with table caps (1,1) SUCCEEDS (I ran it). The new Python calls the 5-argument function, which does not exist there, so the real runtime is down while a compromised runtime can book past any cap.
- Not-refused variant (TRACED from git, not run): a draft DB from after 92e11d00f (5-arg, caps in table) but before ca1dc459e (B3 day window), 1f36063b9 (M1 min age), 2efb50d03 (N1 CHECKs), 168f10f43 (idempotent reserve): migrate SUCCEEDS with only warnings and the old bodies keep running: far-day reserves start fresh counters (month cap bypass, review B3), expire at age 0 works, negative/odd counters not CHECK-guarded. Nothing at runtime start looks at function bodies.
- Breaks: month and day cap (stale B3 body), "runtime cannot choose a cap" (7-arg).
- Fix (one line): when roles are named and an UNRELEASED migration's recorded checksum differs from the file for 0010/0011 (the money wall), raise ConfigError instead of warning (keep warning for 0008/0009 if wanted), and in the refusing path also `REVOKE ALL` on the unmapped hadavin_* overload from the named roles before raising (or name it in the error with the exact DROP FUNCTION).
- Test sketch: build a DB from the old files (git show 87f1ffd6f:...), record their checksums in schema_migrations, GRANT EXECUTE on the 7-arg to the runtime; run migrate with roles; assert it raises AND that the runtime can no longer execute any hadavin_reserve_spend overload other than the 5-arg one. Second case with the 92e11d00f body: assert migrate refuses on checksum mismatch.

### M2. `migrate` accepts unnamed roles that can write `hadavin_caps`, `hadavin_limits`, or hold COLUMN grants on the money tables (CONFIRMED)
- Where: store/migrate.py:958-981 `_money_table_writers` (tables list at 962 is only spend, spend_month, spend_reservations; test is `has_table_privilege`, which ignores column grants); `_OWNED_RELATIONS` only checks ownership.
- Precondition: some other login (an old runtime login, an ops user, a default-privileges grant) holds `UPDATE ON hadavin_caps`, or `UPDATE (usd) ON spend`, or `UPDATE (reserved_usd) ON spend_reservations`, not named in the migrate command.
- Steps (ran): `GRANT UPDATE ON hadavin_caps TO hr1_other; GRANT UPDATE (usd) ON spend TO hr1_other; GRANT UPDATE (reserved_usd) ON spend_reservations TO hr1_other;` then migrate with the five roles: returned `[]` (success). Then as hr1_other: `update hadavin_caps set day_cap=1e30` -> `UPDATE 1`.
- Result: the cap table, the one thing the whole design says no login but the owner/reset path can change, is writable and migrate calls the deployment clean. Also hadavin_limits (max_amount, skew, min age) is not covered.
- Breaks: day cap, month cap (raised at will by that login).
- Fix: extend `_money_table_writers` to `hadavin_caps` and `hadavin_limits` (also flag any non-owner SELECT-less writer) and add `has_any_column_privilege(r.oid, c.oid, p.priv)` for INSERT/UPDATE.
- Test sketch: grant each of the three above to an unnamed role, assert migrate raises naming role and relation.

### M3. Nothing at runtime start checks that the runtime login lacks money-table rights or that the 5-arg function exists (TRACED)
- Where: store/postgres.py:276-314 `own_stop_rights_problems` and `build()` 317-360 check only `_STOP_TABLES`.
- Precondition: runtime login migrated before step 4 (GRANTS gave it SELECT, INSERT, UPDATE on spend, spend_month, spend_reservations) and the operator did not rerun `migrate --runtime-role` after upgrading; or a login added later.
- Result: the process starts and runs with UPDATE rights; the 0010 trigger is the only brake and is a tripwire (documented bypasses H1, H2). The SECURITY.md promise ("runtime cannot lower a booked amount or change a cap") silently does not hold and no log says so.
- Fix: in `own_stop_rights_problems` also scan spend, spend_month, spend_reservations, hadavin_caps, hadavin_limits (rights beyond `GRANTS[name].runtime`, incl. column grants) and EXECUTE on set_cap / release / purge for the current login; refuse start like the stop-table case.
- Test sketch: login with `GRANT UPDATE ON spend` -> `build()` raises ConfigError naming `UPDATE on spend`; login with EXECUTE on set_cap -> raises.

### M4. Provider failure / bad cost phantom-spend drains the day and month cap with no automatic recovery (TRACED, design consequence)
- Where: runtime/agent_loop.py:559-577: after a successful reserve, `ProviderError` (including `bad_amount`) goes to `_abstain` with no settle; any non-ProviderError exception from `llm.chat` propagates with no settle; `_settle_model_call` 391-413 keeps the hold on ValueError/NotFound/ambiguous failure.
- Sequence: provider returns 5xx/401/refusal for every call (key revoked, outage) -> each run reserves the worst case (say 0.50 USD), call fails, hold stays open, tick expires it after >= 3600 s, it stays booked at the full amount, release is manual per agent per day (`limits release-expired`). A retry loop (inbound events, schedule) books N x worst case with zero real spend until the day cap, and the month cap, are used up: every agent run then ends NEEDS_PERSON `limits.daily_budget` / `monthly_budget` after the provider has recovered. Fail closed, but an outage multiplier and nothing alerts (only a WARNING log of `expired=N`).
- Breaks: availability, not a cap.
- Fix: for a ProviderError the adapter can classify as "request rejected before any billable work" (auth, 4xx validation), settle at 0 (or a documented small amount); keep forfeit only for timeouts/unknown. Also make `expire_reservations` emit an alert-grade line (or fail the step) when expired count > 0 so the operator sees it.
- Test sketch: fake llm raising ProviderError("auth") 20 times against a store with day cap = 10 x worst; assert day counter after = 0 for the auth class and = 10 x worst for the timeout class.

## Minor

### m1. add_spend has no day window; far-day counter rows can be created by the runtime (CONFIRMED)
- 0011:373-414 (no `max_day_skew` test, only 1970..9999). Ran `hadavin_add_spend('ag1', '2099-01-01', 1)` -> `(1,1)`. Only raises counters (no cap escape), but it creates unbounded counter rows for any agent id string (no cap-row check either): table growth and a way to poison a future day/month (self-DoS on 2099 does not matter; on tomorrow it does, and tomorrow is allowed anyway). Fix: apply the same window as reserve to add_spend, and require a cap row. Test: add_spend day = today+5 -> `22023`.

### m2. settle can charge another agent's run (CONFIRMED, already a stated residual m9)
- 0011:243-245. Ran: agent ag1 reserves with run_id 'victim' (a run of agOther), settles 99999: `runs.cost_usd` of the victim = 99999, which drives `max_run_usd` stops (agent_loop.py:318-322) of another agent's run. Fix: `UPDATE runs u ... WHERE u.run_id = rec.run_id AND u.agent_id = rec.agent_id` (memory store too). Test: settle with a foreign run id leaves the foreign run cost unchanged. Also settle may book any actual up to max_amount above the cap (documented: raises only).

### m3. App clock off by more than max_day_skew makes every reserve refuse, with an undiagnosable log (TRACED)
- limits.py:153-158 `except Exception` -> `limits_unavailable`; the DB's `22023 p_day` becomes `ValueError` (postgres.py:405-406) and the log shows only `error_kind=ValueError`. A host with a clock one day or more wrong (restored VM) stops all agents. Midnight itself is fine: the +/-1 day window covers a call across midnight (the hold then lands on yesterday's counter, which may be exhausted, in a window of seconds). Fix: add a fixed hint to the warning for `ValueError` ("spend day refused: check the host clock vs the database UTC date"). Test: monkeypatch `now()` to +3 days, assert the log contains the hint.

### m4. migrate resolves function names through the login's search_path (SUSPECTED)
- migrate.py `_pin_search_path`, `_apply_money_functions`, `_unnamed_money_executors` call `to_regprocedure('hadavin_x(...)')` and `ALTER FUNCTION hadavin_x(...)` unqualified while pinning to `current_schema()`. With a migrate login whose path is `tenantB, tenantA` and 0011 absent in tenantB, it would find and pin/grant tenantA's function. Fix: qualify with `current_schema()` in all those statements. Test: two schemas, path `b, a`, migrate b with only 0001-0007 applied in b; assert nothing in `a` changes.

### m5. Late settle after expiry over-counts forever and defeats release (TRACED, design)
- 0011:224: expired hold settled -> `settled_usd = greatest(actual, reserved)`, status settled; release (`status='expired'`) no longer finds it. A zombie settle with actual far below reserved leaves the difference booked until direct SQL. Fix (if wanted): keep a separate `settled_at_expiry` marker or let release also take holds settled-at-reserved after expiry whose actual is known. Document in the runbook at least.

### m6. Idempotent reserve answers HD005 before recognising its own retry (TRACED)
- 0011:128-129 cap lookup precedes the duplicate check (134-144); memory returns success. Only when the cap row is deleted between the commit and the retry; the Limits layer never retries (new id per call), so low impact. Fix: none needed beyond a doc line, or move the cap lookup after the idempotency check.

### m7. In-doubt commit leaves a hold nobody knows (TRACED)
- postgres.py:947-964: if the connection dies after COMMIT of reserve but before the reply, `Limits.reserve` raises `limits_unavailable`, the run ends, the hold stays open and is booked until expired and then until released. Bounded by one worst case per incident. Same family: SIGKILL between reserve and settle, any non-ProviderError out of `llm.chat`.

### m8. check_caps / blocked divergence (TRACED)
- limits.py `blocked()` reads the REGISTRY budget, `hadavin_reserve_spend` the TABLE; a cap lowered in the registry but not synced is enforced coarsely by `blocked()` between calls only; concurrent runs can overshoot up to the table cap's worth of holds until `sync-caps`. Loud (tick fails), not silent.

## Memory vs Postgres: rules that diverge
1. Caps: memory uses the `day_cap`/`month_cap` arguments (registry); Postgres validates then IGNORES them and uses `hadavin_caps` (HD005 fail-closed when no row). No cap table, `set_cap`, `cap_matches`, `release_expired_spend` in memory (tick `check_caps` is a no-op there).
2. Day window: Postgres refuses a booking day outside UTC today +/- 1 (`22023`); memory accepts any day from 1970.
3. Month counter: Postgres has a separate `spend_month` row (can drift from the day sum; release clamps day and month independently); memory computes month as the sum of day rows.
4. Expiry age: Postgres refuses `p_age_s < min_expiry_age (3600)`; memory accepts 0..10**7. Tests that expire at 0 pass in memory and cannot run on Postgres.
5. Release: memory cannot release an expired hold at all.
6. add_spend: memory and Postgres both have no window and no cap-row check, but Postgres has CHECK usd < Infinity and unbounded NUMERIC while memory rounds under `money_context`.
7. Idempotent reserve vs a missing cap row (m6); settle with a counter below its holds: Postgres HD003, memory has no equivalent check.
8. Run cost: Postgres adds `p_actual` inside the settle transaction to any run id (m2); memory the same, but through Decimal context rounding.
9. Timing: Postgres ages use the DB clock (`clock_timestamp()`), memory the process clock.

## Places a Python exception leaves a hold open (all end booked at worst case)
agent_loop.py:559-577: (a) `llm.chat` raising anything but ProviderError (adapter bug, ValidationError, cancellation, KeyboardInterrupt); (b) `ProviderError` -> `_abstain` without settle (by design, M4); (c) `_settle_model_call` 399-413: ValueError/NotFound (hold kept, run cost added directly), ambiguous failure (settle may or may not have committed); (d) process kill/crash between reserve and settle; (e) reserve committed but reply lost (m7). All are bounded by one worst case each and cleared only by tick expiry (still booked) plus operator release.

## Verdict
The money wall itself (functions plus grants) holds on a correctly migrated database in every sequence I built. The real gaps are around it: stale draft databases (M1), what migrate and start-up do not verify (M2, M3), and phantom spend on provider failure (M4).
