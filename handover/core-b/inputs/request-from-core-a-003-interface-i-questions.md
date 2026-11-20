# Request 003 (core-a to core-b): questions on INTERFACE (i) version 2.1, found while writing its contract tests

Read: inputs/interfaces-from-core-b/README.md (2.1), i_store_spend.py, ii_meter.py; src/hadavin_sdk/store/protocol.py, memory.py, postgres.py, migrate.py; tests/contracts/test_store.py, kinds/store_postgres.py. NOT read: tickets/F-store.md and tickets/F-store-review-1.md (not in core-a inputs).
Tests written against the answers recommended below only where marked "asserted"; everything else is left unasserted until answered.
Files: tests/contracts/test_store_spend_reservations.py, tests/contracts/test_t1_reserve_cap.py.

## Contradictions
C1. Is an expired row "closed"? README section 1: "a reservation nobody closed ... is marked expired" and "first call closes the row (open or expired)" (expired is NOT closed). README section 2 point 4: "the sweep closes the row after 3600 seconds" (expired IS closed). It decides what `purge_spend_reservations` ("deletes closed rows only") does with an expired row nobody settled, and so whether a late settle of it can raise NotFound.
   Recommended: closed means closed_at IS NOT NULL; expire does not set closed_at; purge deletes only rows with closed_at < before, so an expired row is kept until it is settled (or state a separate age rule for it). Not asserted: the purge test uses open and settled rows only.
C2. Settle after expiry with a higher actual. Section 1 (2.1): the counters move upward by the difference. Section 3 (test_meter line): "settle after expiry (lower changes nothing, higher raises)". "raises" reads as an exception.
   Recommended: reword section 3 to "higher books the difference". Asserted: books the difference, no exception.
C3. Invariant numbering: "numbered in the F-store ticket, 1 to 12" but the README lists ten phrases. The tests quote the phrase and give no number. Recommended: put the numbered list in the README.

## Gaps
G1. Module of the new names. i_store_spend.py says "added to Store in store/protocol.py and to models.py". Which holds SpendCapExceeded, which SpendReservation? Assumed (asserted, fails loudly, never skips): SpendCapExceeded is found in hadavin_sdk.store.protocol, else hadavin_sdk.models. SpendReservation is never imported by the tests.
G2. No read method. A reservation can be observed only through the return of settle_spend, so "open rows become expired" is tested by the returned count and by how a later settle behaves. Recommended: say so, or add get_spend_reservation(reservation_id) (NotFound).
G3. Status and settled_usd of an expired row after its first settle. Assumed: settled_usd = actual, closed_at set (asserted); status "settled" or "expired" (either accepted). Recommended: status "settled".
G4. Zero amount when the counter is at or above its cap (above is reachable through overshoot): granted or refused? "would pass its cap" suggests granted at the cap. Not asserted (the random sequence uses amounts >= 0.01).
G5. Bad caps (negative, NaN, float, bool, None) and an int amount such as 1: ValueError? Recommended: ValueError for anything that is not a finite Decimal >= 0, caps included. Asserted for usd only, with the listed kinds: negative, NaN, sNaN, both infinities, float, bool, str.
G6. run_id that names no run row: refused at reserve, or at settle (then NotFound would mean two different things), or ignored? Recommended: reserve does not check; settle books the counters, closes the row and skips the run cost. Not asserted: every test creates the run first.
G7. Order of checks on reserve: a duplicate id whose amount would also pass the cap (StaleState or SpendCapExceeded), and a bad amount with a duplicate id. Recommended: ValueError, then StaleState, then the caps. Not asserted.
G8. Purge bound: assumed `before` is compared with closed_at (the purge role may read status and closed_at only). Asserted with bounds one day either side.
G9. Assumed and asserted: the reservation sits on the same counters as add_spend and spend_totals (spend, spend_month); an amount already there counts towards the cap; reserve adds nothing to runs.cost_usd.
G10. expire_spend_reservations(0): assumed to expire every open row created strictly before the call. A negative older_than_s is not tested.

## Changes needed in files core-a does not own
P1. tests/contracts/kinds/store_postgres.py `_SplitStore` routes only purge_tool_calls and purge_redaction_maps to the purge identity. purge_spend_reservations must be routed too, or the runtime role runs it and gets InsufficientPrivilege. Until then the contract test reaches the purge store through the wrapper's `_purge` attribute.
P2. No reset role exists: `migrate` takes runtime_role, portal_role, purge_role; `pg_schema` builds runtime and purge. The README's "portal and reset none" cannot be tested for reset: test_the_reset_role_may_not_read_reservations skips with "missing fixture: no reset role ..." until `migrate` has a reset_role parameter. Which role is meant, and which step creates it (0006 stop state)?
P3. No portal fixture in the postgres kind: the T1 test creates the role itself and calls migrate(owner_dsn, portal_role=...), as tests/test_k2_migrations.py does. No change needed; stated so it is not a surprise.
P4. src/hadavin_sdk/store/migrate.py GRANTS needs an entry for spend_reservations (runtime "SELECT, INSERT, UPDATE"; purge "DELETE" with purge_cols status, closed_at; portal False), or check_grants stops every migrate.

## Notes on the T1 control case
The check-then-add_spend control uses a barrier between the read and the add, so all 50 connections read before any writes. That is a schedule the old pattern allows, pinned so the result does not depend on timing: 50 admitted, asserted as "> 3".
