# Plan review 1: F-money-definer (option B of E13)

Reviewer: fresh, read-only, FAST. Read: the ticket, `migrations-0009-0010-review-1.md`, E13 text in ESCALATIONS.md, and the
cited code. Nothing was run (no PG). Line references below were opened and compared.

## Verdict: FIX FIRST (small fixes, not a redesign). The design is sound; it is the plan text that has gaps. No Blocker in the
definer design itself; four Majors would each cost the builder an hour if found late. Fix the ticket text (about 20 minutes),
then READY TO BUILD for steps 2 and 3 today.

## Citations checked (30 references opened)
Exist and say what the ticket claims: postgres.py add_spend 602-622, `_SCHEMA_TABLES` 370, settle `_CLAIM` 903-910 and
911-957 (claim CTE, day then month, runs.cost_usd update 949-953), expire 959-970, purge 972-983, read-only READ COMMITTED pin
173-175 (actually 170-175), reserve 833+; migrate.py `Grant` 28-49, GRANTS 57-90 (reservations/spend/spend_month `_RW`,
purge `DELETE` + `status, closed_at`), `TRIPWIRE_FUNCTIONS` 97-101, `_apply_grants` 204-222, `effective_problems` 228+,
`_excess_privileges` 590-605, `_pin_search_path` 608-627, `_pin_money_guard` 630-635, `_apply_release_function` 638-658,
membership check 758-766, call order ~786-788; memory.py add_spend 219-225; protocol `check_store_id` 84, `check_spend_day`
101, `check_spend_cap` 115 (docstring 119-139); tick.py purge ~206 and expire ~281; limits.py 152; round2 xfails 253-290;
0010 header and trigger body. Off by one: `_t` is 635-643 (ticket 636-643). NOT opened by me: 0007 CHECK lines, 0003:21,
0008 1-72, memory.py 330-435, protocol 173-331 beyond the ones above. Two statements in the ticket are inexact: `effective_problems`
ALREADY refuses a superuser runtime, BYPASSRLS, a runtime that owns a relation and CREATE on the schema (docstring 228-236), so
those new refusals partly exist.

## Bypass closure (review-1)
- H1 (repeated falls): closed. No UPDATE right on spend/spend_month; the only lowering is settle of one open hold, once (claim).
- H2 (forged settled hold by INSERT, inflate reserved_usd): closed by removing INSERT/UPDATE on spend_reservations.
- H3 (temp table, 0009 seq guard): NOT closed by this ticket. It says "H3 lands first in 0009/0010 in place" (line 4). Fine,
  but H3 and M2 are prerequisites, not part of the 5 steps: put them in step 1 with an owner, else step 4 claims "H3 closed" in N5
  only for the money functions.
- L2 (runtime is owner / member of owner): closed only if the new refusals are real; see Major 3 on what "owner" means.

## Findings

### Major 1: tests that break when the runtime loses INSERT/UPDATE are not listed (ticket line 120, 142; R-sel not done)
The ticket says "the builder lists each" and only names guard tests. By grep and reading, these break at step 4 (or at step 3 for
the SQL-text ones):
1. `tests/test_spend_reservations_pg.py`: 498-500 asserts runtime rights `{SELECT, INSERT, UPDATE}` and purge `{DELETE}` plus
   the two column SELECTs; 604-607 and 655-668 (hand-grant repaired by migrate; purge hand grant "{DELETE}"); 245 and 280
   `REVOKE UPDATE ON spend_month` then expect DENIED/rollback (the runtime no longer holds it: tests lose meaning; 280 and the
   `_break(m, rt, '."spend_month" SET')` monkeypatch of SQL text in the Python store fail at step 3 because that text is deleted);
   882 `REVOKE UPDATE ON spend_reservations` as a way to make expiry fail (must become REVOKE EXECUTE); 564-585 purge login
   direct DELETE statement (line 570 "the statement itself, as the purge login"); 133 and 557-559 denied-matrix.
2. `tests/test_money_guard_pg.py` (lowering_attacks 50-76, 97, 107-124, 158-179: statements as the runtime login) and
   `tests/test_money_guard_mutants.py` (battery depends on them): ticket mentions these (line 120), but test_money_guard_mutants
   kills trigger mutants by running the runtime attacks: after the flip every mutant survives or every attack is refused earlier
   by privilege. Needs re-pointing to the owner login AND a way to call the trigger as a non-owner non-definer (a role granted
   UPDATE by the test), i.e. a design decision not mentioned.
3. `tests/test_store_lock_timeout_pg.py:79` `_row_count` runs `SELECT count(*) FROM spend_reservations` through the runtime store
   (R-sel is real: this test reads it); line 74 `_holder` runs `UPDATE spend` on a plain connection (whose login? if it is the
   runtime, it breaks). If the runtime keeps SELECT on reservations the first is fine; the ticket's "runtime `''`" decision
   contradicts this reader.
4. `tests/test_p7_store.py:155-157` asserts the runtime can UPDATE `spend_month` (and not DELETE).
5. `tests/test_stop_state_roles.py:466-476` (staged old-release setup deletes `spend_reservations` from GRANTS: should be fine but
   re-check, it monkeypatches the map) and any `w.rights(...)` assertions.
6. `tests/test_store_schema_qualified_pg.py:72-77` seeds with `INSERT INTO ...spend_month / spend_reservations`: fine only if
   as owner; unverified.
7. `tests/test_k5_fixes2.py:272-287` and `tests/fixtures/migrations_released.json`: a new migration file 0011 changes the
   released-manifest and the "five files" fixtures; ticket does not mention the manifest.
8. Contract suite `tests/contracts/kinds/store_postgres.py` runs the whole store suite as a NON-owner runtime login (`pg_schema(runtime=True)`,
   lines 18-47): it is the real regression for step 3/4 and for the "UNCHANGED" claim. It will exercise EXECUTE grants: good. But
   it calls `migrate(scoped, runtime_role=role, purge_role=purge)` with only two roles named: the new "refuse if
   runtime is member of owner / all roles named" rules must still pass for that (owner = the test DSN user = superuser postgres,
   runtime separate: no false positive, OK).
Decision needed in the ticket: runtime SELECT on `spend_reservations` (recommend: keep `SELECT` for tests' sake? No: it lets the
runtime read ids of OTHER agents' open holds, which feeds the settle-to-0 residual; recommend `""` and fix test 3 to read as the
owner/admin). State it.
Estimate impact: add about half a day of test re-pointing at step 4.

### Major 2: function calls are unqualified; the store qualifies every table through `_t` (ticket line 73, 74)
`SELECT * FROM hadavin_reserve_spend(...)` resolves through the session search path. The tests use a scoped schema through a
DSN option and the store has `_schema` (`postgres.py:635-643`; `test_store_schema_qualified_pg.py` exists to prove temp-table
shadowing is refused). An unqualified function call is resolved pg_catalog first, then pg_temp is not searched for functions
unless named, but a user-owned function of the same name EARLIER in the caller's path (runtime login can set its own search_path:
`SET search_path = evil, ...` — yes, any session) would be called INSTEAD of the definer function by the Python store. That is a
caller-side hijack of the store itself (the runtime code is the attacker's own process, so low impact), yet the schema test
suite will fail first. Fix: the store builds `{schema}.hadavin_reserve_spend` with `sql.Identifier`, the same as `_t`.
Also add the five names to the "every function the store calls is qualified" static test.

### Major 3: the 0010 guard compares against the OWNER OF THE RELEASE FUNCTION, not the owner of the definer functions
0010 trigger lets through `current_user = owner(hadavin_release_expired_spend)`. The new functions are owned by whoever runs
`migrate` for 0011. If 0008 was applied by login A and 0011 by login B (or `ALTER FUNCTION OWNER` fixed one of them),
every lowering settle inside the new function is refused with insufficient_privilege (fail closed outage), and conversely
`_pin_search_path` already requires the same owner. Fix in the ticket: add a migrate check that ALL `hadavin_*` functions have
one owner and that owner is not a named role (and refuse otherwise), and say what the operator does when ownership moved.
Also performance (ticket 131): the guard aggregates BEFORE the owner test; do the reorder in the same step (a 3-line change),
not "if above 5 ms".

### Major 4: PL/pgSQL traps that will bite the builder (ticket lines 38, 41; item 4 of the brief)
a) `RETURNS TABLE (reservation_id, agent_id, day, status, ... claimed)` turns every column name into an OUT variable:
   `WHERE reservation_id = p_id`, `SET status = ...`, `ON CONFLICT (agent_id, day)` become "column reference is ambiguous"
   errors (settle and add_spend). Remedy: `#variable_conflict use_column` at the top, or alias every table (`r.reservation_id`),
   or return the row as the table's composite type plus a separate boolean via an OUT-less SETOF. State one.
b) Atomicity and READ COMMITTED: expressible. A VOLATILE plpgsql function runs each statement with a new snapshot in READ COMMITTED,
   so the claim `UPDATE ... FROM (SELECT ... FOR UPDATE)` re-check after a lock wait works as in the Python version, and the
   lock order row, day, month is just statement order in the body. The ticket must say VOLATILE explicitly (STABLE/IMMUTABLE
   would freeze the snapshot and break the contention test) and "no EXCEPTION blocks" (a plpgsql `BEGIN ... EXCEPTION` opens a
   subtransaction: costs, and swallows rollback semantics the store relies on for HD003).
c) `RETURNS TABLE` plus a second settle (claim is empty): the Python code re-SELECTs the row; in the function that second SELECT
   must run in the same function and must apply the "foreign agent -> HD002" rule: the ticket has it (line 38). OK.
d) `delta = settled - reserved` computed under `defaults.money_context()` in Python (`postgres.py:945-946`); numeric in SQL is
   exact. Same result unless the Python context rounds: parity test must include a 12-decimal amount. Mentioned partially.
e) The `HD` class: PL/pgSQL accepts any five-char SQLSTATE; psycopg 3 turns an unknown one into `psycopg.DatabaseError` with
   `.sqlstate`; check the installed psycopg version does that for class `HD` (letters outside 0-9/A-D? the class `HD` is valid:
   uppercase letters or digits). Message text is lost if the store reads `exc.diag.message_primary`; use it for 'day'/'month'.
   23505 mapping to StaleState: a unique violation can also come from the counter seeds if `ON CONFLICT` is omitted: keep it.
f) Cap check parity: `check_spend_cap` has NO upper bound except the exponent window (docstring 119-139), but ticket line 50
   says caps use "the same window" as amounts (< 1e9). A legitimate cap of `1E+9` or 10**12 must keep working: do not reuse
   `p_usd < 1e9` for caps. State the cap rule separately.

### Minor / residual decisions
- (brief item 1) Caps as a caller argument: acceptable for the promise "cannot LOWER", because a huge cap is an overshoot, not an
  erasure, and reserve then settle-to-0 nets zero. It is NOT acceptable to call the result "true by construction" for
  "the budget is enforced": the runtime can disable the cap entirely. Make the lead's Q5 explicit with that sentence; do not hide
  it in the Residual paragraph. A DB-held cap (`money_caps` the runtime cannot write) is the follow-up. I do not call it a Blocker:
  today the gate runs inside the same process.
- Settle-to-0 on an open hold needs no SELECT: ids are caller-chosen and unguessable; recommend runtime `spend_reservations` = `""`.
  A runtime that calls `hadavin_expire_spend_reservations(0)` turns every open hold of EVERY agent into expired, which makes the
  legitimate lowering settle impossible (they stay booked at reserved: safe, but a self-DoS and a cost distortion); the runtime
  can do the same today. Document, or give expire a lower bound (age >= configured minimum) as a function argument check.
- Release stays a separate role: ticket does this (EXECUTE revoked from others and PUBLIC, plus the refuse-if-can-still-run
  check modelled on 650-658). Good. Add: `hadavin_money_guard()` is a trigger function and needs no EXECUTE grant.
- (brief item 3) Purge: the function is `SECURITY DEFINER` owned by owner, EXECUTE to the purge role only; Python call replaces
  postgres.py 972-983; wiring unchanged (`tick.py:206` via `app.purge_store`, `app.py:247-253` builds the purge store from
  `purge_dsn_secret_name`). The purge role keeps `purge_cols` on other tables (runs, tool_calls, redaction_maps); only the
  reservations row of the map changes (`purge=""`, `purge_cols=()`), good. The purge login can pass any `p_before` (deletes all
  settled rows): same as today. One gap: `check_purge_bound` is Python only; the SQL "not infinity" is listed (line 51). Fine.
- (brief item 5) Owner-refusal false positives: test servers (superuser owner, separate non-member runtime logins): no
  false positive. A runtime login that is a MEMBER OF A NAMED role is already refused. Managed PostgreSQL where the owner is a
  cloud admin role: possible false positive only if the runtime was created as a member of the admin role (some consoles
  grant the admin role membership in the new role, which is harmless, the reverse is what matters) and on PG <= 14 where
  `CREATE` on schema public is granted to PUBLIC (refused: correct, but state it in the runbook as the likeliest first failure).
  The superuser-owner NOTE (not refuse) is right: managed services commonly have no real superuser, and on those the check
  `rolsuper` is simply false.
- Sequence: step 4 flips grants inside `migrate()` while a deployed OLD runtime keeps running: ticket says no rolling upgrade;
  but `tests/contracts` run old store code against a freshly migrated database in K2-style compat tests? Not checked.
- Generic-words / lane rules: names `hadavin_*` fine; `HD001` codes fine; no stage names or hard-coded values spotted in the ticket;
  the migration must not hard-code the 1e9 and 200 and 10000000 limits: those are in `protocol.py`/defaults (`MAX_SPEND_*`,
  `check_expiry_age`), so SQL literals will trip `tests/test_no_hardcoded_values.py` (it scans `src/`, which includes .sql?).
  Check the scan covers .sql; either way the parity test is the guard. Add this to the builder notes.
- Rollback story: the down path "DELETE FROM schema_migrations then DROP FUNCTION then OLD migrate" relies on the OLD package refusing
  a ledger it cannot read; fine, but the migrate "applied migrations have no file in this release" check means the step is
  mandatory. Keep the TEST of it (listed).

## Step-by-step shippability (item 6)
- Step 2 (functions + FUNCTION_GRANTS, nothing calls them): shippable. One catch: `check_grants`-style "every hadavin_* function
  is in the map" fails for 0010's trigger functions and for the 0009 guards unless they are in the new map or excluded: define
  that set in step 2.
- Step 3 (store switched, old grants kept): shippable ONLY with step 2's EXECUTE grants applied to the runtime and purge roles in the
  same migrate run, and with the two SQL-text-dependent tests (`_break(... '."spend_month" SET')`, 245/280) re-pointed in the same
  step. Otherwise "contract suite green UNCHANGED" is true but `test_spend_reservations_pg.py` is red. Revert by Python revert
  alone: true only while 0011 stays applied (it does; additive).
- Step 4 (the wall): not shippable without the Major 1 list. Step 5 is pure hardening and independent.

## Estimate (item 7): honest answer: steps 2-3 today, 4-5 next session
By 11:30 UTC (about 1 hour) with three sonnet builders in parallel and a PG16 available:
- Builder A: `0011_money_definer.sql` (five functions) incl. validation, VOLATILE, `#variable_conflict`, error codes. About 50 min.
  Risky: it is the longest and the first PG run.
- Builder B: `migrate.py` (`FUNCTION_GRANTS`, `MONEY_FUNCTIONS`, `_pin_money_functions`, `_apply_money_functions`, owner checks)
  with unit tests against a scratch schema. About 40 min, but cannot finish verification until A's file exists: B writes against
  the signatures in the ticket and integrates at minute 45.
- Builder C (test writer, different agent): `tests/test_money_definer_pg.py` function-level positive and hostile table, written
  from the ticket. About 45 min; first green run at about 11:30 at best.
- Step 3 (store switch + error mapping + qualified calls + the 2 SQL-text tests): a fourth builder starting at 11:10, lands
  11:40. Realistic: end of the hour you have step 2 plausibly green and step 3 in review. Steps 4 (wall, test re-pointing list of
  Major 1, N1-N9, owner checks) and 5 (mutants, performance, up/down test, docs) are the next session: about 1.5 days of the ticket's
  3 to 4 builder days are tests.

## Required ticket edits before build (checklist)
1. List the broken tests (Major 1) and decide runtime SELECT on `spend_reservations` (recommend `""`).
2. Qualify function calls with the schema (Major 2).
3. One owner for all `hadavin_*` functions, check in migrate, guard owner test first (Major 3).
4. `VOLATILE`, `#variable_conflict use_column`, no EXCEPTION blocks, cap rule separate from amount rule (Major 4).
5. Move H3/M2 fixes into an explicit step 1 with an owner.
6. Put the cap residual sentence into question 5 so the lead's answer is explicit.
