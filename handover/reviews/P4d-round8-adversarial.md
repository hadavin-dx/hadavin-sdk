# P4d round 8, adversarial review (ticket revision 9)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-design`, read-only, nothing run, did not open `reviews/`. Round 1 of at most 3 under order 16. All traces UNVERIFIED.

Verdict: NOT CLEAN. 0 Blocker, 2 Major, 2 Nit.

## MAJOR

**M1. Test row a7 cannot be built as written, so mutants i10h and i10g lose their killer (lines 81, 82, 92, 93).** Row a7 is "1 token at price 1E-30" through both producers; `reply()` takes its price from a `Route`. The same sub-ticket adds a `Route` validator (line 76) refusing any price with more than 6 decimals, so 1E-30 is refused at construction. The builder either fails at `Route(...)` or bypasses validation with `model_copy(update=...)` (the bypass path line 76 names). a7 is the only killer of i10h and is named in i10a-e and i10g. Fix: use a price that passes the validator: price 0.000001 with 1 token gives exact cost 1E-12, expected 0.00000001; same edit in the table and line 81. Hand check: 1 x 1E-6 / 10^6 = 1E-12 rounds up to 1E-8 at 8 decimals.

**M2. Money safety: the excess-bound refusal (PL19; lines 156, 176, 189, 294) leaves only under-booking exits.** If the reply cost exceeds `max(reserved, 1 USD)` above the reservation, `settle_spend` raises `ValueError` and rolls back; the reservation stays open at the smaller reserved amount. The ticket's only exits are release or retry with a smaller amount: release books 0 for a call that spent money; a smaller retry books less than was spent. Both break order 14(3) (book the upper bound, never less). Fix: state in P4d-b and the P4b1 relay that on this refusal the caller must settle at the largest accepted amount, `reserved + max(reserved, floor)`, and book the rest with `add_spend` (uncapped, no new store method); add one B3 row (refused, settle at the bound, `add_spend` of the remainder, counters equal full true spend). Alternative: drop the per-call bound and rely on the ceiling (loses PL19's protection).

## NIT

- N1: line 12 cites P2a "revision 5"; elsewhere P2a revision 9 (lines 17, 269).
- N2: item 18 (line 293) says "ANSWERED YES by order 8(2)" and ends "Answer needed before P4d-a2-i starts"; delete the trailing sentence; confirm item 17 is genuinely open.

## Held

Cites (`memory.py:31`, `postgres.py:197` plain locks; `defaults.py` imports only `__future__`; `models.py:16` `field_validator`; `ci.yml:40` one postgres image; `estimate_tokens` at least 1). Counts: 18 write methods (8 `_insert`, 2 `_update_run`, 8 direct); 32 to 38 Protocol methods; 12 `SpendReservation` fields; trigger matrix 16 pairs, 5 allowed, 11 refused; 5 x 8 = 40 frozen-column checks; 4 field rules. Rounding kill sets a1-a8 and i10a-j re-derived by hand. 24-digit counter statement. Lock order, NOWAIT probes, T4 timing arithmetic, retry rule, upper-bound behaviour of the sweep.

## Not checked

Everything needing a run (Postgres behaviour, evidence runs, T4/B4b timings, `wait_event`); other tickets' text (relays unverified); the order 14(3) booking table (belongs to P4a/P4b2); the "52 cases / 26 test functions" and "16 test files that build a Reply" claims; `models.py` and `config.py` cites beyond those listed.
