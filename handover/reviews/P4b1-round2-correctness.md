# P4b1 round 2, correctness review (ticket rev 2, 375 lines on disk) - agent ae021b9cbbe7779a4
Status: REPORTED (saved by the lead session from the reviewer's hand-back, model output, not user authority)
Reviewer: ae021b9cbbe7779a4 (read-only)
Verdict: no Blocker; 3 Majors (R2-COR-1..3), 7 Minors, 2 Nits

R2 correctness review of handover/tickets/P4b1.md (rev 2; the ticket says 374 lines, the file has 375). Code was checked on current main, not on ce70eb5; whether main differs from ce70eb5 was not checked.

## Majors

| id | sev | line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Major | 238, 231, 66 (T4.4/M52) | The ticket says the wrapper "works with every llm kind, fake included". P4a's frozen ticket (P4a.md:196) says `fake` KEEPS zero route prices. Zero prices give W = 0, and `Meter.reserve` demands `worst > 0` (line 72) and `SpendMicro(0)` is a `ValueError` for `record`. So a `MeteredLLM` over `FakeLLM` with a zero-price route fails with `ValueError` before the model is called. B10, R4a and B17 only use a nonzero-price route, so no test reveals this. | Decide it in the ticket. Either floor W at 1 micro-dollar, or allow a zero worst case for a zero-price route (skip the hold), or require nonzero prices in fake routes. Add a row for a zero-price route. |
| R2-COR-2 | Major | 231 vs code `config.py:55-59`, P4a.md:197 | W is described as using "integers, micro-dollars per million tokens, as P4d's Route price check requires". On main, `Route.input_usd_per_mtok` and `output_usd_per_mtok` are `Money` (Decimal USD per Mtok, e.g. `"3.00"`; tests use `Decimal("3.00")`). P4a.md:197 says "no new field", so prices stay Decimal USD. The conversion Decimal USD per Mtok -> integer micro-dollars per Mtok is not specified, nor is what happens to a price with more than 6 decimals. This is a money step with no rule: the price is the heart of W. | Add the exact conversion (`Decimal * MICRO_PER_USD` must be an integer, else `ValueError`; or round UP). Add the matching test and mutant. |
| R2-COR-3 | Major | 72 vs 105 (T1.13), 100 | Line 72 says "on ANY exception the meter makes one best-effort release", then excludes `OverBudget` and `store_busy` only in a later sentence. The exceptions in between are not decided: `NotFound` (`unknown_run`), `ReservationConflict`/`StaleState` (`conflict`), `CounterDamaged`, store `ValueError`. Does `release` follow them? T1.12 and T1.13 test only the two ends. A builder must guess, and two builds can differ. `CounterDamaged` followed by a release also sits oddly with the caller rule. | Write a table with one release yes/no per error row of the error table, plus a spy test row for each. |

## Minors and Nits

- R2-COR-4 Minor, 66/24: literal 3600 (`max_hold_s` 1..3600), `max_decimals=6` and exponent -6 have no constant names, so the ticket's own T4.4/M52 scan fails on its spec. Fix: add `METER_MAX_HOLD_LIMIT_S` and `MICRO_DECIMALS` (or derive from `MICRO_PER_USD`).
- R2-COR-5 Minor, 78 (cites P4c.md:51): ticket says P4c-2 maps overshoot to `NEEDS_PERSON run_budget` and audit row `guard/estimate_exceeded`; the P4c line on disk says overshoot is NOT a P4c outcome (PENDING LEAD item 14) and never mentions `estimate_exceeded`. Fix: reword to "P4c must" and drop the line cite, or cite the revision that says it.
- R2-COR-6 Minor, 235/362 (PL17): "up to 2W" holds only for count 1 and 3 attempts; the excess is count x (attempts-1) x W (4W for count 2, 3 attempts), contradicting R4d-1's own example (6W booked). Fix: replace "2W" with the formula, also in the CHANGELOG line.
- R2-COR-7 Minor, 262 (B14) vs 234: B14 attacks hostile `Reply` cost values, but line 234 computes cost from usage and route price, not `Reply.cost_usd` (today `Reply` has `input_tokens`, `output_tokens`, `cost_usd`, `models.py:289-297`). Fix: state `Reply.cost_usd` is ignored (or compared); B14 names the field it attacks.
- R2-COR-8 Minor, 235: failure booking `count x attempts x W` can exceed `MAX_USD`, so `record` raises `ValueError` inside `except`/`finally`; B15 covers only the reservation. Fix: pin the behaviour (cap at `MAX_USD`, or keep the reservation) and add a row.
- R2-COR-9 Minor, 89: `check_usd`, `StoreBusy`, `CounterDamaged`, `MAX_USD` and `METER_*` are listed under "Existing core code reused (checked)" but exist only in P4d; on main only `missing_methods`, `StaleState`, `NotFound` exist (`protocol.py:25,45,151`). Fix: move to a "from P4d, UNVERIFIED" list.
- R2-COR-10 Minor, 70/79/129: clocks not unified; `limits.py:8` binds `now` at import so patching `models.now` does not move `Limits.blocked`/`charge`, while `Meter` resolves `models.now` at call time; M16 cannot be killed deterministically. Fix: `Limits.hold` passes `clock=lambda: now()` using `limits.py`'s own name; T2.6 patches only that name.
- R2-COR-11 Nit, 134: T2.11 calls the `SpendMicro` charge a "regression pin" but it is new; only the `Decimal` charge is a pin. Fix: split the row.
- R2-COR-12 Nit, 175 (M24), 3, 11: M24 mutates the test, not `meter.py`/`money.py`/`limits.py`, so the runner rule (line 148) cannot apply; header says 374 lines, file has 375. Fix: drop M24 (keep exact-count rule in T5.1; 73 becomes 72) or reword; fix the line count.

## Verified
- Mutant count: -a has M1-M53 minus 3 CUT (M14, M17, M25) = 50 rows; -b has W1-W24 minus W2 = 23; total 73, lines 212 and 296 agree.
- Row count: T1 30, T2 13, T3 14 (P1-P14), T4 4, T5 5, T6 8 = 74 for -a; -b has 6 R4 rows plus B1-B17 = 23; total 97.
- Error codes: seven listed, seven in the table.
- Parity arithmetic: P8 gives 1 and 38; P14 gives 6,620 and 26,480; P2 gives 400,010 x 2 refused third, then fits after settling at 10; `ceil_cost(1, 3)` example right; `orphan_age_s` threshold (above 297 -> 2x+5, else 600) right.
- Code cites holding on main: `limits.py` 17-30 (`now().date()` at 18 and 24, `>=` cap check at 26 and 28); `agent_loop.py` 240, 314-315, 440-441; `llm/common.py:59` and `:92`; `FakeLLM` has no `max_attempts`; `models.new_id` gives `prefix-<32 hex>`; `DEV_ONLY` at `table.py:593`; `store/protocol.py` treats `OSError` as unreachable (line 33); `Route.max_tokens` exists; `P4a.md:164` fail-before wording.
- All 17 template fields present in -a and -b; Step 0 stop rule, live-call gate and caller rule are consistent between sections.

## Not checked (UNVERIFIED)
- Everything taken from frozen P4d rev 10 and P4a rev 12 (six reservation methods, `check_usd`, `MAX_USD`, `StoreBusy`, `CounterDamaged`, `request_bound`, `UsageMissing`, `round_cost_up`, PL10/12/14/22/23/51/60); P4d was not re-read.
- Intake line cites, PR #48 figures, the 89-passed claim; whether `unknown_attempts` matches P4b2; `tests/test_s5_runtime.py:109-128`; the 100,000-token tier figure; Postgres, Python 3.12, lock-in guard allow-list; whether the T2 shim imports only modules that exist on ce70eb5.
