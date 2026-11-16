# Mutation lane report, ORDER 016 (C8), run 2026-11-16 UTC

## What failed, survived or could not run
Scratch copies of b4cce5b with one patch each (/tmp/c8/wC, /tmp/c8/wA); the repo was not touched. No scripts/mutation_check.py exists, so a plain loop (/tmp/c8/run.py) was used. Hand-planted mutants, one at a time, original restored and byte-compared after each. Tests run with `env -i`, one process, no xdist. Raw output per mutant: `raw/`.
- C-01: 11 of 15 real mutants killed; SURVIVORS: 4.
- A-01: 12 of 17 real mutants killed; SURVIVORS: 5.
- Mutants 16 (C-01), 1 and 10 (A-01) are no-op controls (identical text); they survive as expected, not counted.
- Not run: the full suite, G5-wording (text only, out of scope), mutants of the test files, and `reprobe_sources`/K1bAudit paths. Mutant lists are hand-made, not exhaustive. `uv sync` needed the network proxy certificate once (outside `env -i`); the tests themselves ran with a clean environment.
- Baseline before mutation: C-01 tests 10 passed; A-01 tests plus test_p7_tick 46 passed.

### Survivors and the assertion that would kill each
- C-01 #11 (`max_tokens` gt=0 -> gt=1): add a case that max_tokens=1 loads.
- C-01 #12, #13, #14 (ceiling constant 200_001 / 199_999 / 2_000_000): the tests use `defaults.MAX_ROUTE_TOKENS` itself, so they follow any value. Add `assert defaults.MAX_ROUTE_TOKENS == 200_000` (or load a literal 200_000 and refuse a literal 200_001, and refuse 2_000_000).
- A-01 #8 (STEPS entry points at `purge_evidence` instead of `audit_reconcile`): assert `[s for s in STEPS if s.name == "audit_reconcile"][0].fn is audit_reconcile`.
- A-01 #9 (interval 0 -> 3600): assert that step's `interval(ctx)` is 0 / that it runs on two consecutive ticks.
- A-01 #17, #18, #19 (`LocalDirSink.write_outcome` warning removed / leaks error text / downgraded to DEBUG): the tests cover only the chain kind. Add the same caplog test for `LocalDirSink` (force `_write` to raise; assert one WARNING with type and event id, and not the error text).

## C-01 (config.py, defaults.py); tests: test_c01_route_limits.py

| # | file | mutation | result | test that killed it |
|---|---|---|---|---|
| 1 | config.py | price check <= 0 -> < 0 (price 0 allowed) | KILLED | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] |
| 2 | config.py | min -> max (only both-zero refused) | KILLED | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] |
| 3 | config.py | output price no longer checked | KILLED | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-output_usd_per_mtok] |
| 4 | config.py | input price no longer checked | KILLED | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] |
| 5 | config.py | live-kind price check removed entirely | KILLED | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] |
| 6 | config.py | price check also applied to fake kind (over-broad) | KILLED | tests/test_c01_route_limits.py::test_the_fake_model_may_cost_nothing |
| 7 | config.py | refusal never raised | KILLED | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] |
| 8 | config.py | max_tokens ceiling dropped | KILLED | tests/test_c01_route_limits.py::test_max_tokens_above_the_ceiling_is_refused |
| 9 | config.py | max_tokens gt=0 -> ge=0 (0 allowed) | KILLED | tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused |
| 10 | config.py | ceiling le -> lt (off-by-one at ceiling) | KILLED | tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused |
| 11 | config.py | max_tokens gt=0 -> gt=1 (1 refused) | SURVIVED |  |
| 12 | defaults.py | ceiling constant +1 | SURVIVED |  |
| 13 | defaults.py | ceiling constant -1 | SURVIVED |  |
| 14 | defaults.py | ceiling constant x10 (the typo it guards) | SURVIVED |  |
| 15 | defaults.py | ceiling constant lowered to 100 (would break 1024 fixtures) | KILLED | tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] |
| 16 | config.py | (no-op control: identical text) | SURVIVED |  |

## A-01 (tick.py, chain.py, local_dir.py); tests: test_a01_audit_reconcile, test_p7_tick, test_s2_audit, test_p3b_neutral_audit

| # | file | mutation | result | test that killed it |
|---|---|---|---|---|
| 1 | runtime/tick.py | (no-op control) | SURVIVED |  |
| 2 | runtime/tick.py | drain count logged as 0 and reconcile never called | KILLED | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count |
| 3 | runtime/tick.py | drain runs but no log line | KILLED | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count |
| 4 | runtime/tick.py | early return: step never drains | KILLED | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count |
| 5 | runtime/tick.py | missing-reconcile guard removed (kind without reconcile crashes) | KILLED | tests/test_a01_audit_reconcile.py::test_a_kind_without_reconcile_is_skipped |
| 6 | runtime/tick.py | logged count off by one | KILLED | tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_count |
| 7 | runtime/tick.py | step removed from STEPS | KILLED | tests/test_a01_audit_reconcile.py::test_the_step_is_in_the_tick_list |
| 8 | runtime/tick.py | STEPS entry points at the wrong function | SURVIVED |  |
| 9 | runtime/tick.py | step interval 0 -> 3600 (not every tick) | SURVIVED |  |
| 10 | audit/chain.py | (no-op control) | SURVIVED |  |
| 11 | audit/chain.py | chain outbox WARNING removed | KILLED | tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body |
| 12 | audit/chain.py | chain WARNING leaks the error text (redaction regression) | KILLED | tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body |
| 13 | audit/chain.py | chain WARNING logs run id instead of event id | KILLED | tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body |
| 14 | audit/chain.py | memory-only ERROR downgraded to DEBUG | KILLED | tests/test_a01_audit_reconcile.py::test_when_the_outbox_table_also_fails_an_error_line_is_logged |
| 15 | audit/chain.py | memory-only ERROR line removed | KILLED | tests/test_a01_audit_reconcile.py::test_when_the_outbox_table_also_fails_an_error_line_is_logged |
| 16 | audit/chain.py | event no longer kept in memory when outbox fails (audit loss) | KILLED | tests/test_a01_audit_reconcile.py::test_when_the_outbox_table_also_fails_an_error_line_is_logged |
| 17 | audit/local_dir.py | local_dir outbox WARNING removed | SURVIVED |  |
| 18 | audit/local_dir.py | local_dir WARNING leaks the error text | SURVIVED |  |
| 19 | audit/local_dir.py | local_dir WARNING downgraded to DEBUG | SURVIVED |  |

