# F-money-definer H1 review 1 (hostile, read-only)

Scope: ca1dc459e (B3), 1f36063b9 (M1), 2efb50d03 (N1), 06fa176dd, 0011_money_definer.sql, defaults.py, tests/money_caps_seed.py,
tests/test_money_h1_pg.py, H1 mutants in tests/test_money_caps_mutants.py. Ran test_money_h1_pg.py + test_money_caps_mutants.py
(-k h1/b3/m1/n1/limit_seed): all pass (1 strict xfail M2, as designed).

No Blocker. No Major on the money paths. One Major on test quality.

## Major

M-1. tests/test_money_caps_mutants.py:279 `pytest.raises((AssertionError, Exception, pytest.fail.Exception))` in
`test_the_h1_checks_kill_every_mutant`. `Exception` swallows everything, so a mutant "dies" for any reason (a psycopg error, a
HD004, a typo in the replaced text that still migrates but breaks something unrelated). The file's own header says a bare
Exception must NOT count (BEHAVIOUR_FAILURES, line ~45, used by the caps tests). The migrate step is outside the raises, so a
syntactically broken mutant is caught, but not a semantically unrelated break. Fix: use `pytest.raises(BEHAVIOUR_FAILURES)`
(add `psycopg.errors.CheckViolation` only if a check legitimately expects it; the N1 check wraps it in pytest.raises itself).

## Minor

m-1. 0011:64-67 (N1). On a DB with a bad row (negative, NaN, Infinity) VALIDATE fails with raw PG
`check constraint "spend_usd_range" of relation "spend" is violated by some row` (23514). It IS loud and the whole migrate
transaction (one `db.transaction()`, migrate.py ~1136) rolls back, nothing half-applied, ledger row not written. But the
message names no remedy and no row. Fix: say in the migration header (or catch CheckViolation in migrate around the file
execute) "repair the offending rows as owner, then rerun". No test covers a pre-existing bad row; add one (insert bad row via
owner before 0011 using a scratch schema migrated to 0010, then expect failure and an unchanged ledger).
ALTER TABLE / VALIDATE by the owner is fine under the 0010 guard: the guard is a row BEFORE UPDATE trigger, DDL and VALIDATE
fire no row trigger and rewrite nothing (checked by reading 0010; ADD CONSTRAINT takes ACCESS EXCLUSIVE briefly then
VALIDATE only SHARE UPDATE EXCLUSIVE, fine).

m-2. Upgrade path (DB that already ran 0008, then 0011) is correct by reading but untested. CREATE OR REPLACE keeps owner and
ACL; 0011 re-REVOKEs PUBLIC; signature, RETURNS TABLE, SECURITY DEFINER and VOLATILE match 0008 so no "cannot change return
type" error; `migrate` runs `_pin_search_path` and `_apply_release_function` (to_regprocedure exists, re-pin, REVOKE others,
GRANT EXECUTE to the release role) after the files on every run, so final owner/pin/grants are identical on fresh and upgraded
DBs. Only proconfig is reset by REPLACE (to the placeholder), and migrate re-pins in the same transaction. Fix: one test
migrating a scratch schema with files <= 0008 first, then all, asserting proowner, proconfig, ACL of the release function.

m-3. defaults.py:165 `MIN_EXPIRY_AGE_S = RESERVATION_EXPIRE_S` and tick.py:274. The tick cannot refuse today: its age is
`min(MAX_EXPIRY_AGE_S, max(3600, ceil(longest)))` (NaN/inf/too-large clamp to MAX_EXPIRY_AGE_S = 10**7), so it is always
>= 3600 = min_expiry_age and <= max_expiry_age. The rule "longer age while a run could still be working" only raises it. So no
every-minute raise. The coupling is by convention only: raising MIN_EXPIRY_AGE_S without RESERVATION_EXPIRE_S would make every
tick fail the expire step (22023). Fix: a unit test `assert defaults.MIN_EXPIRY_AGE_S <= tick.reservation_expire_s(app)` for an
app with no agents and one with a short stuck-run age (and no test uses the real 3600 against the tick step today).

m-4. 0011:118-121 (B3) residual: with skew 1 the runtime can book yesterday, today and tomorrow, so up to 3x day_cap in one
real day (month cap still bounds, except across a month boundary, where two month counters are reachable). Documented as 3b
only for "never a far day"; add the 3x day_cap sentence to the HONEST RESIDUAL. hadavin_add_spend has no window (listed as
residual 4, raises only, fine).

m-5. Test flake: tests/test_money_h1_pg.py check_b3 uses Python `today_utc()` against the DB's clock; within a few ms of 00:00 UTC
the in-window day can be the edge. Negligible; freeze via the DB (`SELECT (clock_timestamp() AT TIME ZONE 'UTC')::date`).

## Answers to the asked points

- B3: window logic correct (UTC date from clock_timestamp, v_skew::integer from a numeric row, NULL/missing row HD004 fail
  closed, error 22023 names only the parameter, refused before any INSERT so no counter row starts; test asserts counts
  unchanged). Mutants B3a-e kill on real behaviour (the check asserts the exact refusals and the row-driven window).
- M1: expire refuses age < min (22023), release only touches holds whose closed_at (expiry moment) is older than min;
  M-M1a..d kill via the check's asserts (young hold stays 'open'; just-expired hold stays 'expired' with released == 0).
- Test seeding wrapper (tests/money_caps_seed.py): test-only, imported only from tests/conftest.py, test files and
  test_money_definer_pg.py; no src path imports it. It writes as owner, so it cannot mask a production grant problem, but it
  does set min_expiry_age = 0 for all non-`no_cap_seed` PG tests, so they never exercise the real 3600 (tick expire step
  included). Real values ARE tested for B3 and M1 in test_money_h1_pg.py (marked no_cap_seed, assert the seeded row equals the
  defaults constants).
- N1 mutants: M-N1c only mutates spend (spend_month NOT VALID left is caught by the convalidated assertion in the check, but
  there is no mutant for it); add one.
