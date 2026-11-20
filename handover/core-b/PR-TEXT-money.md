exact money and the no-lowering wall are in force; no-overspend is NOT in force until the model gate installs reserve/settle (F-install)

## What is built (F-money-definer, steps 1 to 6, plus F-store)
1. Prerequisites in 0009/0010 (H3, M1, M2, M3 fixes) verified and kept under regression tests.
2. Migration 0011: `hadavin_limits` and seven SECURITY DEFINER money functions, `FUNCTION_GRANTS`, pinned search paths, one-owner check in `migrate`.
3. The Python store (`postgres.py`) calls the schema-qualified functions and maps their SQLSTATE codes.
4. Grants flip (the wall): the runtime login holds only SELECT on `spend` and `spend_month` and nothing on `spend_reservations`; the purge login holds no table right (EXECUTE on the purge function only). Reserve, settle, expire and add-spend are functions the runtime may EXECUTE. A hand GRANT of a write right is repaired by the next `migrate`; an unnamed writer role is refused.
5. Mutant battery, static test, up/down/rollback test, docs.
6. Caps out of the runtime's hands: table `hadavin_caps`, written only under the reset login; `limits set-cap`, `limits sync-caps`, `limits check-caps`; tick step `check_caps`.
Also: exact decimal money; `Limits.reserve` / `Limits.settle` (tested, not called by the live path); release command for expired holds (0008); stop-state tables (0006, 0009).

## What is NOT built or not in force
- F-install: the model gate that calls `Limits.reserve` before a model call and `Limits.settle` after it. Today the live path (`runtime/agent_loop.py`) still calls `Limits.blocked()` before and books the cost after, so concurrent runs can each pass the check and overshoot a cap by up to (concurrent runs x one call's cost). No text in this PR claims a hard cap.
- Laptop items (need PostgreSQL 15 and 17 and a builder with real databases): `handover/core-b/requests/lead-build-1.md` (watermark and NOT VALID constraint validation; route price guard at client build) and `handover/core-b/requests/lead-build-4.md` (own role for `hadavin_set_cap`; isolation check in `check_role_settings`; audit-table rights; column-privilege and PUBLIC bypass in `_money_table_writers`, MA1; the writers check runs only when a role is named).

## Migrations
0006 `stop_state`, 0007 `spend_reservations`, 0008 `release_expired_spend`, 0009 `stop_state_hardening`, 0010 `money_guard`, 0011 `money_definer` (0007 to 0011 unreleased; see `handover/core-b/MIGRATIONS.md`). Next free number 0012.

## Operator sequence (no rolling upgrade)
Stop the tick scheduler and every runtime-side process; `hadavin-sdk migrate` naming ALL roles (including `--reset-role`); `hadavin-sdk limits sync-caps --by WHO --yes`; start; one smoke `tick`. Every run is refused (`limits_unavailable`) until `sync-caps` has completed.

## Testing
evidence: see handover/core-b/evidence/ (per-step test and mutant logs, for example F-store-tests-evidence.txt and F-install-tests-evidence.txt; batch-*.md for full-suite runs, some of which record failures from a missing local PostgreSQL). No counts are restated here.
