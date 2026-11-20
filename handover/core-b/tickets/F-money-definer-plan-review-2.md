# Plan review 2: F-money-definer (option B, revision 2)

Reviewer: fresh, read-only, FAST. Nothing was run (no PG). Read: the revised ticket, plan-review-1, and by grep/open: tests/ (all files naming spend, spend_month, spend_reservations, the five store methods), src/ writers, 0010 body, migrate.py, tick.py.

## Verdict: FIX FIRST (small). Two Blockers are ticket-text/decision conflicts, not design flaws; fix them and steps 2-3 can start. Round 1 is mostly answered for real.

## (1) Round-1 answers, checked against the ticket body
| Round 1 | Mapped? | Check |
|---|---|---|
| Major 1 broken tests | PARTLY | list exists (items 1-10) but is INCOMPLETE, see (2): the shared contract helpers that read/update spend_reservations as the runtime are missing, and item 9/"contract UNCHANGED" is false for them. |
| Major 2 qualified calls | YES | "Rules for every function body" + static test; ticket body consistent (Files, postgres.py). |
| Major 3 one owner / guard order | PARTLY | (c) and owner-first are in the body. Gap: owner of the TABLES vs owner of the functions is not checked (see B-3 / Major M1 below). |
| Major 4 a-f | YES | all six present in "Rules" and "Arguments". The limits-from-defaults mechanism (new) is under-specified, see M2. |
| Minors | YES except lower bound | lower bound added, but it collides with the contract suite (Blocker B1). |
| H3/M2 step 1 | YES | step 1 present. Minor: step 1 owner is builder A who also writes the regression tests; ticket line 4 says tests are written by a different agent. |

## (2) Tests the list is MISSING (greps done by me)
Runtime-login statements against the three tables or runtime SELECT/UPDATE (the store's own `_exec` is the runtime connection in `pg_schema(runtime=True)`):
1. `tests/contracts/test_store_spend.py:58` `_rows` = `store._exec("SELECT * FROM spend_reservations")`, `:72` `_older` = `UPDATE spend_reservations SET created_at`, `:89` `_closed_earlier` = `UPDATE ... closed_at`. NOT in the list. These break at step 4 for every contract test that calls them (aging for expire/purge: ~20 tests; `_rows` is imported by caps/ids_caps tests too). The ticket promises the contract "UNCHANGED" and "I need from core-a: nothing" (lines 101, 136): false.
2. `tests/contracts/test_store_spend_model.py:247` `_rows` same SELECT as the runtime (the sibling `_shift` 259-290 already goes through the owner DSN with `session_replication_role = replica`: the model to copy; `_rows` does not).
3. `tests/contracts/test_store_spend_ids_caps.py:337` is an admin DELETE (fine); `:262-271,:362` call `expire_spend_reservations(0)` (see B1).
4. `tests/test_spend_reservations_pg.py`: `w.run` login not stated in the ticket (item 10 says "verify"); lines 92-109 `w.run` reads of spend/spend_reservations. Verify, not in the list by name beyond 133/245/280/498...
5. `tests/test_migration_numbers.py` and `tests/test_migration_numbers_guards.py` (lock key, folder, "late file" recipe, ledger-newer message using hard-coded 0010/0011 style names) and `tests/test_lockin_guard.py:734-741` (`sql_problems` scans migration `.sql` for vendor literals: 0011 text is scanned, so the "assume .sql is NOT scanned" claim at ticket line 63 is partly wrong; the lockin guard DOES scan `.sql`, check whether the hard-coded-values test does too). Not in the list.
6. `tests/test_k2_migrations.py:221,255,358-371` loop over `mig.GRANTS` and compare held rights to the map: self-consistent after the map change, but `:371` compares the catalog to GRANTS (relations only); the NEW "every hadavin_* function in the map" check needs its own test here. Not named.
7. `tests/test_p7_store.py:155` yes (listed). `tests/test_store_lock_timeout_pg.py:74,79` yes (listed). `tests/test_purge_keeps_expired.py:89` listed.
No other test file writes the tables as the runtime. Checked with no spend access: tests/test_p3b_*, test_p7_tick, warden_port, tests/test_money_context_*, test_money_store_round6 (store methods only), test_limits_reserve and test_store_memory_atomic (memory), test_peel_run_id, k5_support, test_k5_tools. src/: writers are only postgres.py (5 methods), `limits.py:152,183,215,217`, `tick.py:206,281`; cli.py has only `release-expired` (release role, unchanged) and `migrate`; `evals.py`, `k1b/`, demos (`askdata/meter.py` is a file meter, not these tables) touch none. Good: no hidden src writer.
Also: all line numbers the ticket cites in postgres.py are stale by about 37 lines (purge is now at 1009-1020, settle claim at ~940-963, reserve INSERT at 894). Builders must re-open (Minor).

## (3) New findings
### Blocker B1: the expire lower bound contradicts the contract suite and the memory store (ticket line 60, 186)
Contract tests call `store.expire_spend_reservations(0)` on the Postgres store as the runtime: `test_store_spend.py:128`, `test_store_spend_caps.py:131-132`, `test_store_spend_ids_caps.py:271` (`edge` 0 must expire 1 row, parametrised "zero"), `:362`. `check_expiry_age` (protocol.py:143-148) accepts 0..MAX and both stores share it. A function minimum age (default 3600, `defaults.RESERVATION_EXPIRE_S`) returns 0 rows for age 0: about 8 contract tests go red, and the memory store (no bound) would diverge, breaking "same inputs, same results" (invariant 5). Scenario: step 4 flips; `test_the_edges_of_the_expiry_age_are_accepted[zero]` fails. Real expire caller `tick.py:281` already passes age >= `RESERVATION_EXPIRE_S`, so a bound is safe in prod. Fix: either drop the bound and document the residual (lead Q5 already allows it), or put the same minimum into `check_expiry_age` for BOTH stores and change the contract tests (core-a files, lead decision) and add a test seam. Recommend: drop the bound for this ticket, document it (self-DoS only, safe: holds stay booked).

### Blocker B2: "contract UNCHANGED, nothing needed from core-a" is false (lines 101, 136, 149 item 9)
See (2) items 1-2. Removing runtime SELECT/UPDATE breaks the shared helpers `_rows/_older/_closed_earlier` in two core-a files. Scenario: step 4 PG contract run: `psycopg.errors.InsufficientPrivilege` on `SELECT * FROM spend_reservations` for every test using `_rows`. Fix: ticket must list these four helpers, say core-a is told (the lane file edit is mechanical: route them through the owner DSN as `_shift` does), and soften "UNCHANGED" to "assertions unchanged, three test helpers re-pointed". Needs the lead's OK because it edits contracts.

### Major M1: owner consistency checks function owners only; the definer needs rights on the TABLES (lines 70, 77)
(c) checks all `hadavin_*` function owners are equal and not a named role. Nothing requires that owner to own (or hold UPDATE/INSERT/DELETE on) the money tables and `runs`. Scenario: tables created by login A (0001-0007), 0011 applied by login B with CREATE on schema: all functions consistent (B), guard passes, every reserve raises insufficient_privilege (fail-closed outage, same class as Major 3 of round 1). Fix: extend (c): owner of `spend`, `spend_month`, `spend_reservations`, `runs` equals the function owner (or the function owner is a superuser). Same message and runbook step.

### Major M2: "limits from defaults, not literals" has no mechanism in migrate.py (line 63)
migrate.py has no text-substitution of migration files (only the `ALTER FUNCTION ... SET search_path` re-pin; no checksum either). Substituting limits into the body needs `CREATE OR REPLACE` on EVERY migrate run (otherwise a changed default never reaches the function: the "run with a changed default" parity test fails), and it fights `tests/fixtures/migrations_released.json`/the file-hash and `test_migration_numbers*` lexer rules (placeholders in a file). Fix: pick the settings-relation (`hadavin_limits`, owner-written by migrate on every run, read by definers) now; it needs one more GRANTS row (runtime none) and an entry in `check_grants` tests. Builder A cannot choose later without changing builder B's file set.

### Major M3: deploy window with the `tick` cron (line 156)
`tick` is a separate command (cli.py:123, "run every 30-60 s"), purge wired through `app.purge_store`. Sequence stop-runtime, migrate, start-new leaves a cron `tick` that may still start OLD code between migrate (grants flip, step 4) and the new rollout: old `expire_spend_reservations`/`purge_spend_reservations` get insufficient_privilege and `tick` logs FAILED steps (fail-closed, loud, but pages). Also the reverse at step 3: new code before 0011 -> "function does not exist" in tick. Fix (one line each): runbook says stop the tick scheduler and every purge/portal/other process too, and the post-migrate smoke test runs one `tick`; `migrate` should print the order. No code change.

### Major M4 (purge): `purge` as a function (line 49) is OK, but two things are unstated
(a) `tests/test_p2_postgres.py` has NO purge/spend tests (grep: none), so no test of that name breaks; the purge tests are in `test_spend_reservations_pg.py:564-585,604-668`, `test_purge_keeps_expired.py`, `contracts/test_store_spend*.py`, all listed or re-pointable. (b) The purge role's only `spend_reservations` privilege disappears from GRANTS: `effective_problems`/`_excess_privileges` run for the purge role at migrate.py:786-792: confirm the "no excess" check still sees EXECUTE (function) as allowed, otherwise migrate refuses its own state. Add one test in step 2 (migrate with purge role named and the wall on).

### Minor
- Owner-first guard reorder (line 91, 161): design is sound (owner passes, definers run as owner, non-owner still hits the aggregate). It adds one `pg_proc` lookup per row UPDATE; negligible. Note the honest consequence in the header: with owner-first, the trigger gives NO protection against a bug inside the definer functions (they are owner); the ticket's trade-off (3) says this, keep it in the 0010 header too.
- Removal of runtime SELECT on `spend_reservations`: src reads none outside the settle second-read (postgres.py ~963, moves into the function). `Limits/Budget/tick/cli` read only `spend_totals` (spend, spend_month): safe. Only tests read it (B2).
- `check_spend_day` plain `date` only; infinity refusal in SQL means a Python/SQL difference unless Python also refuses infinity (psycopg cannot send `date` infinity from Python `date`; fine, parity row must expect "SQL-only reject").
- Step 1 regression tests by the builder A contradicts "tests by a different agent" (line 4): assign them to C.

## (4) Build order and builder file sets
Steps 1-3 are shippable per step with the revised order: 1 (verify + 0010 reorder, in place, 0008-0010 are not in the released manifest, so in-place edit is legal), 2 (additive 0011 + migrate EXECUTE; nothing calls it; but note step 2 ships the NEW owner-consistency ConfigError, i.e. a behaviour change for existing multi-login deployments: say so in the CHANGELOG), 3 (store switch with old grants; needs a database that has run step 2's migrate). Step 3 must not ship before step 2 is migrated: state in the runbook.
File-set overlaps:
- A (0011.sql, 0010 reorder) and step 1 regression tests: tests written by A (rule breach); put in C.
- B (`migrate.py`) and A: shared contract of the function-name list (`MONEY_FUNCTIONS`, signatures) and the limits mechanism (M2): single list in one place or they drift.
- C `tests/test_money_definer_static.py` asserts calls qualified in `postgres.py` (D's file) and C's pg test needs A's file: C cannot go green before A and D. Order C last.
- D (`postgres.py`) and the re-pointing of `tests/test_spend_reservations_pg.py`, `tests/reserve_mutants.py` (step 3) vs the same file's step-4 edits (sequential: OK but name one owner for the file).
- Step 4 edits core-a contract helpers (B2): new owner, needs lead approval.
Otherwise disjoint (A: sql; B: migrate.py; C: new test files; D: postgres.py).

## (5) Verdict and minimal diff
FIX FIRST. Minimal ticket diff:
1. Line 60/186: drop the expire lower bound (document as residual) OR add it to `check_expiry_age` for both stores and list the ~8 contract tests; recommend drop (B1).
2. "Tests that break": add (2) items 1, 2, 5, 6 and 4; change "contract UNCHANGED/I need from core-a: nothing" to "three helper functions in two contract files re-pointed to the owner DSN, core-a told, lead confirms" (B2).
3. Owner consistency (c): add table-owner = function-owner (M1).
4. "Limits come from defaults": choose the `hadavin_limits` relation, list its GRANTS row, drop the "builder picks" (M2).
5. Runbook line: stop `tick` scheduler and all other runtime-side processes; post-migrate smoke `tick` (M3).
6. Step 2: add the purge-role-named migrate test (M4b); fix line 4 tests-by-other-agent for step 1; add a note that postgres.py line numbers are stale.
After that: READY TO BUILD for steps 1-3.
