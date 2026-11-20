# Review 2 of 7b6c31636 (step 6 review fixes)

Ran: tests/test_tick_check_caps.py + tests/test_money_caps_mutants.py (25 passed). Also tests/test_limits_reserve.py (1 FAILED).

## Blocker

- src/hadavin_sdk/limits.py:198-202 (`detail=%s`, exc). Breaks the existing test
  `tests/test_limits_reserve.py::test_the_refusal_log_line_names_the_error_class_and_not_its_message`
  (fails now: `detail=host=db user=u` in caplog). That test pins a deliberate policy: the log names the error class,
  never the message. The commit did not update or discuss it. Scenario: any store exception (psycopg
  OperationalError with host/user/dbname, DatabaseError with DETAIL/SQL text and values, StaleState carrying a
  reservation id) is now written to the log verbatim. Fix: revert `detail=` and log a bounded, allow-listed hint
  instead (e.g. only for ConfigError, whose messages are fixed strings in `_money_error`:
  `detail=%s` with `str(exc)[:200]` and newlines escaped via `%r`), or keep the policy and keep the existing
  `sync-caps` hint another way; then make the policy test explicit about which classes may carry detail.

## Major

- src/hadavin_sdk/limits.py:198-202. Even if detail is kept: it is unbounded and unescaped. psycopg messages are
  multi-line (log injection: a forged `WARNING ...` line via an exception message or via an agent id echoed in a
  message); no truncation. The claimed "5000-char agent id test" does not exist for Limits (no test greps
  `detail=`); the only 5000-char test is for check_caps. Fix: `%r` on `str(exc)[:200]`, and add a test with a long
  multi-line message asserting a single line and the length bound.

- src/hadavin_sdk/runtime/tick.py:310-311, 321. check_caps logs `agent=%s` and puts `agent.id` into the CapsDrift
  message with no bound or escaping, and `AgentRecord.id` is an unconstrained `str` (registry.py:42). A 5000-char or
  newline-bearing id (the very case the new test uses) gives a 5000-char log line and exception message, and a
  newline in an id forges log lines. Fix: log/format with `%r` of `agent.id[:80]`, or validate the id in
  AgentRecord.

## Minor

- tests/test_tick_check_caps.py:118. The comment says "the database refuses it (22023)". It does not: `check_store_id`
  rejects >200 chars in Python (protocol.py:90) before any SQL, so the 22023 path and `_money_error` are not
  exercised. The test still proves the per-agent except, but the comment is wrong. Fix: correct the comment; add a
  case where `matches` raises a non-ValueError (stub store raising RuntimeError / psycopg.OperationalError) to
  prove the broad `except Exception` and that the remaining agents are still checked.

- tick.py:307 `except Exception` is wide: it also turns a connection loss into `agent:error` for every agent (N
  error lines, one CapsDrift). Acceptable (fail loud, exits 1) but the message says "differs from the registry",
  which is misleading for a DB outage. Fix: word the message "differs or could not be checked".

- tests/money_caps_seed.py: the `_SEEDED` cache is gone, so every reserve in every PG test now does an extra
  upsert round trip (cost only). Also the `WHERE set_by = 'test-seed'` guard is not itself tested by a mutant/test
  (a test that seeds via set_cap and asserts the table wins after a seeding reserve); add one. Seed errors are now not
  swallowed: intended, fine.

- tests/test_money_caps_mutants.py:BEHAVIOUR_FAILURES. Narrowing is right (a broken SQL no longer counts as a kill)
  and every mutant string replacement applies (the new mutants all fail the battery; none equals the control).
  Caveat: a real behaviour change surfacing as NotFound/RuntimeError/StaleState is now a test error, not a kill;
  that errs on the safe side (false failure, not a surviving mutant). No surviving mutant found.

- tests/test_money_caps_reserve_pg.py new `no_cap_seed` test: can fail (asserts SpendRefused, the sync-caps text
  in a log record, and zero spend rows). Note the "sync-caps" log text comes from the ConfigError message that the
  new `detail=` prints, so the test depends on the Blocker above: if `detail=` is reverted, this test fails unless
  the hint is logged another way.

## Behaviour outside step 6

None found beyond the log-policy change in limits.py (Blocker).
