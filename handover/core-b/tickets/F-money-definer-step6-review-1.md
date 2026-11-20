# F-money-definer step 6: fresh review 1 (hostile, read-only)

Verdict: NO BLOCKER on the wall itself. The SQL, the grants and the store behave as the design says. There are two Majors (stale text that now makes a false security claim; check_caps behaviour that contradicts the ticket) and several Minors (test masking and weak mutants).

Verified by reading: 0011 (all of it), store/postgres.py `_reserve_call`, `reserve_spend`, `set_cap`, `cap_matches`, `_money_error`; store/migrate.py `GRANTS`, `MONEY_FUNCTIONS`, `FUNCTION_GRANTS`, `_apply_grants`, `effective_problems`, `_apply_money_functions`; cli.py `caps_cmd` and helpers; runtime/tick.py `check_caps`; tests/money_caps_seed.py, the conftest fixture, test_money_caps_reserve_pg.py, test_money_caps_mutants.py.
Ran (shared DB, one command): `tests/test_money_caps_reserve_pg.py tests/test_money_caps_mutants.py`: 11 passed.

## Can the runtime login still choose, raise or lower a cap?
No, by construction:
- `hadavin_caps` has `Grant("table", "")` for every role (`migrate.py:104`); `_apply_grants` does REVOKE ALL on it for each named role (`migrate.py:394`) and `effective_problems` flags any right gained via PUBLIC, membership or default privileges.
- The reserve function has exactly one 5-argument form (no overload; T11/M-t test it). The Python store passes no caps (`postgres.py:927-934`, caps validated and dropped).
- `hadavin_set_cap` is reset-only (`FUNCTION_GRANTS[5]`); `hadavin_cap_matches` is runtime+reset and read-only.
- Residuals (acknowledged, not defects): (a) `hadavin_cap_matches` is a binary-search oracle: a runtime login can read any agent's exact caps in about 100 calls (caps are not secrets per the ticket; make sure the docs say "readable", not only "not writable"). (b) The runtime can still `add_spend`, settle open holds, and reserve for ANY agent id that has a row (pre-existing). (c) With `--no-roles` nothing is revoked (pre-existing behaviour of the grant model).

## Missing, zero, NULL cap rows (0011:128-131, 141-158)
- No row: HD005 before any insert, so no counter is touched; mapped to `ConfigError` and then `limits_unavailable` (`postgres.py:390`, `limits.py:197`). Good, and the HD005 branch precedes the generic `HD*` branch.
- NULL: impossible (NOT NULL + CHECK). NaN/negative/Infinity: refused by the CHECK. Zero cap: `usd < cap` is false, so every reserve is refused, including a zero amount. This is the documented M10 behaviour, and the CLI help says so.
- Race set_cap vs reserve: the cap is read without a lock at statement start (READ COMMITTED). A reserve that is already waiting on the day-counter row lock keeps the OLD cap in `v_day_cap` after a concurrent set_cap lowers it, so exactly one in-flight reserve per waiter can book past the new cap. This is the "seen before or after" case in the ticket (M11) and is bounded by one call's worst case, but the runbook should say "a lowered cap applies to reserves that start after the commit".

## Findings

### Major 1: stale text now states a false security claim (docs and the migration header)
- `src/hadavin_sdk/store/migrations/0011_money_definer.sql:12-15`: "(1) The caps are arguments of hadavin_reserve_spend, so the runtime CAN DISABLE CAP ENFORCEMENT ... a caps table the runtime cannot write is the named follow-up, step 6". Both are false after this step. A reader will think the wall is weaker than it is, or that the SQL differs from the file below it.
- `0011_money_definer.sql:319-320`: "The reserve function above still takes its caps as arguments in this step; a later step makes it read this table." False.
- `docs/stop-state-runbook.md:242-244`: the literal "TODO-E2 ... 7-argument form" and "UNTIL THEN, verbatim: a compromised runtime login can bypass the cap" lines ship in the runbook. The runbook now says two opposite things. `CHANGELOG.md:16-18` has the same `TODO-E2` and "stands" text.
- `0010_money_guard.sql:22-26` (not in your list) says "Until step 6 ships: a compromised runtime login can bypass the cap".
- `SECURITY.md` has no sentence about caps at all (the ticket's step 5 asked for it in SECURITY.md); grep for "cap" finds only an unrelated audit line.
- Fix: replace all of them with "the runtime login can neither lower a booked amount nor change a cap (it can still read a cap through hadavin_cap_matches, settle an open hold it can name, and add spend)", and add that sentence to SECURITY.md. Caution on 0011: it is unreleased, so editing the header is fine (the ledger hash is of the file; re-record it if `migrations_released.json` pins it).

### Major 2: `check_caps` alerts on a RAISED registry cap, contradicting ticket T13/M5
- `runtime/tick.py:301-312`: any state other than "same" is added to `bad`, so after an operator raises `budget_usd` and before `sync-caps`, every tick step fails and the tick exits 1 (the docstring says "for any difference"). Ticket T13 says "a raised registry cap raises no alert (M5)". Scenario: a cap raise is a routine, safe operation; it now pages on every tick until sync, which trains operators to ignore the alert that matters (lowered cap still high in the table).
- Also `cap_matches` only returns same/differs/missing, so the runtime cannot tell raised from lowered. The step cannot distinguish them with the current function; either T13 is relaxed in the ticket (and documented) or the function must return 'higher'/'lower'. No test covers the raised case (`tests/test_tick_check_caps.py` has none), so nothing pins either behaviour.
- Fix: decide, then pin with a test. Cheapest: update the ticket/runbook to say "any difference alerts; sync after every registry edit", and add a test "a raised registry cap fails the step". Alternative: return 'lower'/'higher' from `hadavin_cap_matches` and alert only on 'lower' and 'missing'.

### Minor 1: the autouse seed fixture can hide a real regression
- `tests/conftest.py:120-143` + `tests/money_caps_seed.py:44-66`: every PG test that reserves with caps as arguments gets its table row overwritten from the argument on the same call. No production path depends on it (grep: `seeding_reserve` appears only in conftest, nothing in `src`). But:
  1. It makes HD005 unreachable in every test without `no_cap_seed`, including the Limits-level and contract tests. The only HD005 tests are in `test_money_caps_reserve_pg.py` at store level; there is no PG test that `Limits.reserve` with a missing row gives `SpendRefused("limits_unavailable")` end to end.
  2. It overwrites the table with the argument whenever the pair differs from its cache, so any test that calls `set_cap`/`hadavin_set_cap` and then reserves through the store without the marker silently gets the argument, not the table cap. The effect depends on the module-level `_SEEDED` cache (cache hit means the table value wins by accident, miss means the argument wins). Today no such test exists (checked: only `test_money_caps_*.py`, `test_caps_cli.py`, `test_tick_check_caps.py` touch set_cap, and the first and last do not reserve), but it is a trap for the next one.
  3. `except Exception: pass` around the seed (`money_caps_seed.py:54-56`) swallows a seed failure (for example a connection error or a dropped schema), so the test then fails with HD005 and a misleading "no cap" message instead of the real cause.
  4. `_SEEDED` is a process-global cache; it is safe only because `World` uses random schema names (`test_stop_state_roles.py:66`). A fixed schema name would cause false HD005 failures.
- Fix: add a PG test through `Limits.reserve` (marker `no_cap_seed`) asserting `limits_unavailable` and no counter row; make the fixture refuse (assert) when the table already holds a different pair for that agent that was written by something other than the seed (`set_by <> 'test-seed'`), and drop the cache.

### Minor 2: weak mutant battery (`tests/test_money_caps_mutants.py`, `caps_battery` in `test_money_caps_reserve_pg.py:79-96`)
Mutants of the reserve text that would SURVIVE the battery (which only runs `caps_battery`; the zero-amount and lowered-below-booked tests are separate tests and are not run against the mutants):
- Drop the `s.usd < v_day_cap` leg (0011:~151) or the `m.usd < v_month_cap` leg: the cap-exact case only checks the day, a zero-amount reserve at cap is not in the battery.
- Change `m.usd + p_usd <= v_month_cap` to `<` (month): no exact-month-cap case is in the battery (the `exact` agent is 5/50 and only reaches the day cap).
- Zero cap row not tested: a mutant treating 0 as "unlimited" (`NULLIF(cap,0)`-style) survives.
- Remove the `HD005` mapping in Python (return the generic `ConfigError`): the `match="no cap for this agent"` assertion kills it, fine.
- `with pytest.raises((AssertionError, Exception, pytest.fail.Exception))` (mutants file, last lines) is `Exception`, so a mutant that merely breaks the SQL (syntax error that migrate happened to accept, a wrong column) counts as "killed" even if it does not exercise the intended property. Control passes, so the harness is sound for the listed mutants, but it proves less than it looks.
- No mutants at all for `hadavin_set_cap` and `hadavin_cap_matches` (validation removed, `<` for `<=` on the cap rule, 'same' returned when only the day cap matches, upsert that does not overwrite month_cap). `test_money_caps_pg.py` has behaviour tests for them, but I did not see a mutant run; a mutant `rec.day_cap = p_day_cap OR rec.month_cap = p_month_cap` should be tried.
- Fix: put zero-amount-at-cap, exact month cap, zero cap and a day-above-month pair into `caps_battery`; narrow the mutant assertion to `AssertionError`/`pytest.fail.Exception` (the migrate-refusal path is already handled above it); add 3 mutants for `cap_matches`.

### Minor 3: operability and edge behaviour
- `limits.py:197-199` logs only `error_kind=ConfigError` for the missing-cap refusal, so an operator who sees `limits_unavailable` after a deploy that skipped `sync-caps` is not told why (the helpful "run limits sync-caps" text in `postgres.py:391` is discarded). Fix: log the ConfigError message (it carries no value) or a distinct reason code in the audit.
- `tick.py:301-308`: `check_caps` loops over agents and lets the first `cap_matches` exception (for example a 22023 for one agent id that SQL refuses) abort the step with a database error instead of naming the agent; later agents are not checked. Fix: catch per agent and report `agent:error`.
- `cli.py` (`caps_cmd`): `states` is read for all agents, then written one by one with no re-check; between the two a concurrent `set-cap` by another operator is overwritten silently. Low risk (single operator, audited); mention in the runbook or re-check inside `_set_one_cap`.
- `by` is an unauthenticated operator-supplied name (`--by`); the audit line is the only record. Same as the other limits commands; no change needed, but the runbook should not call it an identity.

## Not found
- No path where the runtime can write `hadavin_caps`, call `hadavin_set_cap`, or pass a cap into reserve.
- No production code path calls the seeding wrapper; `no_cap_seed` marker is registered in pyproject.toml:87.
- `hadavin_set_cap`/`cap_matches` are VOLATILE, definer, pinned, REVOKE ALL FROM PUBLIC, validated inside (checked against 0011:322-415).
