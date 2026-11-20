# P3: gate end to end with core-b's real store (scratch merge)

Branch `wip/cloud-core-c/p3-scratch` = origin/cloud/core-b (8273ff1d0) + `git merge origin/cloud/core-c`. SCRATCH: not for merging.
Environment: Postgres 16.15 on 127.0.0.1:54399 (throwaway cluster; must be initdb -E UTF8, an SQL_ASCII cluster makes psycopg return bytes and `connect()` refuses the session pins), `HADAVIN_TEST_PG_DSN` set.

## Merge conflicts (7 files; none semantic in src)
| file | resolution |
|---|---|
| src/hadavin_sdk/defaults.py | both sides kept (two added blocks of constants, no name clash) |
| src/hadavin_sdk/guard/producers.py | core-c's text for `guard/model_gate.py` (one dict line) |
| tests/conftest.py | both fixtures kept (core-b's PG fixtures, core-c's unidata fixture) |
| tests/contracts/test_t1_reserve_cap.py | add/add: core-b's version kept (core-c's 714-line copy dropped; not diffed against it) |
| SECURITY.md, README.md, CHANGELOG.md | docs only: both sides concatenated (SECURITY.md ~684 lines on core-c's side), NOT reconciled; a real merge needs a human edit |
Python files parse; no conflict markers left.

## TESTED (tests/test_gate_store_e2e.py: 18 passed, 2 strict xfail, real Postgres)
- normal call: reserve 0.40, settle at the real 0.12; row `settled`, day counter 0.12. PASS (via an adapter, see F1).
- refused-before-response ProviderExhausted: settle 0, row settled at 0, day 0. PASS.
- unmarked ProviderExhausted / ProviderError: row stays `open`, day counter holds the worst case 0.40 (not under-counted; the sweep closes it). PASS.
- spend refusals, one test per reason in SPEND_REASONS (kill_switch, daily_budget, monthly_budget, limits_unavailable [store down], bad_amount [13 decimals], usd_cap [in-memory Budget]): audited `refused` with that reason, provider not called, no reservation row, counter unchanged. PASS x6.
- planted secret in a reply: not in audit rows, reservation rows, spend or spend_month; reservation settled. PASS.
- 8 threads, 8 separate store connections, cap 1.00, worst 0.40: exactly 2 ok, 6 `daily_budget`, day total 0.80. PASS.
- KeyboardInterrupt, SystemExit, GeneratorExit in the provider: audited `call_interrupted`, row left `open`, day counter holds the worst case. PASS x3.

## Findings
- **F1 (real bug, integration between lanes; fix is on either side).** `model_gate.py` `BoundGate._settle` calls `self._meter.settle(reservation, usd)` (its `Meter` protocol, 2 args). `limits.py` `Limits.settle(self, reservation_id, actual_usd, *, agent_id)` requires `agent_id` (the docstring of `settle_for` says "The gate should call this one"). With the real `Limits` as meter the call raises TypeError, which `_settle` catches as `settle_failed`: every paid call stays booked at its WORST CASE, never at the real cost (safe direction, but the budget drains at worst-case rate). Tests: `test_real_limits_as_the_meter_keeps_the_worst_case_booked_not_lost` (passes, pins the behaviour) and `test_real_limits_as_the_meter_settles` (strict xfail F1). The other tests use a 6-line adapter `ForGate` (`settle(id, usd) -> limits.settle_for(AGENT, id, usd)`). Also: no production code builds `ModelGate(` (src) and `runtime/agent_loop.py` still calls `limits.reserve` / `settle_for` itself, so the gate is not wired to the store yet.
- **F2 (design gap, boundary of the lanes).** The gate masks what it sends; the model's reply is returned exactly as the client gave it. A planted `password=...` in a reply comes back raw from `chat`. It is not stored by the gate or the store (TESTED), so the only exposure is the caller; the caller's masking step (`runmap.redact_text`) is not part of this test. Strict xfail `test_reply_with_a_planted_secret_is_not_returned_unmasked`. If the contract is "the gate never returns unmasked text", core-c must add reply masking; if not, the doc should say the caller must.
- **F3 (stale assertion after the merge).** `tests/test_model_gate.py::test_no_error_the_adapters_raise_today_carries_the_mark` fails on the merge: core-b's `ProviderError` now has the class attribute `refused_before_response`, the core-c test asserts it does not exist. Test is outdated; update it (the 3 assertions before it, that nothing is marked as refused today, still pass). Of the 359 tests run in test_gate_store_e2e, test_limits_reserve and test_model_gate*, this is the only failure.
- Observation: an unmarked failure leaves the hold open for the sweep; the real sweep has a 3600 s floor (`MIN_EXPIRY_AGE_S`), so a provider outage drains the daily budget at the worst-case rate for an hour per call. Not a bug, noted.

## NOT RUN
- Full test suite on the merge (only the 4 files named above, 359 tests). No ruff, mypy or CI.
- Real provider adapters (retry layer marking `refused_before_response`): a fake provider raised the marked error.
- The sweep (`expire_spend_reservations`, `release_expired_spend`) and `Limits` over a non-owner runtime role: the e2e used the owner login (`pg_schema()`).
- Hostile masked-input side of the gate against the store (inputs with held values): covered by core-c's own gate tests, not repeated here.
