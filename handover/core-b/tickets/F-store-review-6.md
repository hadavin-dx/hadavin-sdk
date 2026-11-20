# F-store review 6 (fresh reviewer, read-only on source): F6 fix of F-store-hostile-review-2 M1, M2

Branch cloud/core-b. Test run: `HADAVIN_TEST_PG_DSN=... pytest tests/test_money_store_round6.py tests/test_limits_reserve.py` = 137 passed.

Verdict: the store/limits/llm side is CLEAN. One Major remains, in a file this branch does not own (agent_loop.py, F-install) and
already requested in the F-store.md follow-up; this review sharpens it (the note's "cannot reach :513 today" is only true for the
built-in providers). Nothing else above Minor.

## Findings

### Major-1 (open, owner F-install): a bad cost from a custom LLM or Detector escapes `handle` and leaves the run WORKING
- runtime/agent_loop.py:353-354 (`_screen`), :513-514 (model reply), and the second `_screen` call at :593.
- `handle` has no outer try/except; `_screen` charges OUTSIDE `injection_check`'s fail-closed `except Exception` (guard/injection.py:89),
  so the ValueError of `Limits.charge`/`add_cost` is not turned into a flag. The :513 charge is outside the `except ProviderError` at
  :497. Nothing is audited and no `_abstain`/`_to` runs: `handle` raises with the run in WORKING (until the tick stuck-run rule).
- Why it is reachable: `Reply` (models.py:294) and `Verdict` (models.py:310) have NO validator on `cost_usd`. Only llm/common.py:304
  and llm/fake.py:65 build a Reply and both are now valid by construction, but `LLM` and `Detector` are public protocols (Hooks).
- Failing scenario A (screen): a custom detector returns `Verdict(flagged=False, score=0, backend="x", cost_usd=Decimal(1)/Decimal(3))`
  (28 digits) or `Decimal("0.0000000000001")` (13 places), `Decimal("-1")`, `Decimal("NaN")`. `if verdict.cost_usd:` is true for all
  (NaN is truthy), so `Limits.charge` raises ValueError at :353; run stays WORKING, caller of `handle` gets ValueError.
  Scenario B (reply): a custom `LLM.chat` returns `Reply(model_id="m", cost_usd=Decimal("-0.5"))`; ValueError at :513 after the
  paid call, run stays WORKING, the call's cost is unbooked.
- Also `AnyOf.check` (guard/injection.py:77) sums child costs with the caller's Decimal context, no clean; fine for valid inputs.
- Fix (either): the F-store.md note (try/except ValueError, note `bad_amount`, abstain NEEDS_PERSON; screen: fail closed as flagged), or
  better at the source: a `field_validator("cost_usd")` on `Reply` and `Verdict` using `check_spend_amount`, which makes every
  custom LLM/Detector a validation error at construction inside `injection_check`/the provider boundary. Do both; the call-site guard
  is the safety net. Note the old behaviour (negative cost lowering `spent`) was worse, so this is not a regression, but the run
  stranding is new in kind for custom code.

### Minor-1: bad provider usage books nothing in the agent_loop path
- llm/common.py:246-262 `_token_count`, :288-289. In agent_loop there is no reserve; a `ProviderError("bad_usage"/"bad_amount")`
  from a billed call abstains `provider_error` with cost 0 booked (the same holds for every ProviderError already). A provider that
  always returns a negative/odd token count gives free calls against the daily/monthly counters (one call per run; the per-run
  loop ends). Through the model gate (reserve then settle) the error is unmarked (`refused_before_response` False, retry.py:148
  re-raises ProviderError unchanged) so the worst case stays booked: consistent. Accept or book the estimate on bad_usage.

### Minor-2: k1b timeout path `budget.charge(worst)` is outside the try
- k1b/loop.py:162-165: `except ValueError` wraps only `worst_case_usd`; `budget.charge(worst)` / `budget.charge(budget.limit)` can raise
  ValueError if worst >= 10**9 (absurd max_tokens x price) or the fallback cap is >= 10**9 or has an odd exponent (`check_spend_cap`
  has no upper bound), escaping `run_case` ("never raises"). Not reachable with sane config. (core-a/k1b: report only.)

### Nit-1
- store/postgres.py:747 (`reserve_spend`) and :813 (`settle_spend`) call `check_spend_amount`, not `clean_spend_amount`, unlike the
  memory store (memory.py:321, :354). PostgreSQL `numeric` has no negative zero, so no divergence in stored values; consistency only.
- evals.py:86 sums `reply.cost_usd` into a report figure with no validation (writes no counter; a custom LLM could print a NaN/negative cost).

## Answers to the five questions

1. Writers. Every writer of a counter/run cost goes through the check: `Limits.charge` (limits.py:142) -> `store.add_spend`
   (memory.py:213 / postgres.py:545 clean); `store.add_cost` (memory.py:90 / postgres.py:404 clean); reserve/settle in both stores
   check (memory 321/354 clean; postgres 747/813, and the settle SQL at postgres.py:852 uses the checked `actual_usd`; the counter
   delta at :829 is computed in `money_context`); `Budget.charge` (limits.py:78 clean) and `Budget.reserve/settle_for` (89, 111).
   Callers of `charge(`: k1b/loop.py:165/174/201 (Budget, validated), agent_loop.py:353/513 (validated, but see Major-1). No
   `UPDATE spend`/`cost_usd =` writer in evals.py, approvals/, guard/ or elsewhere in runtime/ (guard/judge only copies
   `reply.cost_usd` into a Verdict). No bypass of the store rule found. The only gap is the missing guard at the call sites.
2. `round_up_cost`. Config prices are limited to 6 decimals (config.py:92-111), token counts are ints, and the divisor is 10**6, so a
   raw cost has at most 12 decimals: the round-up (ROUND_CEILING to 12 dp) is a no-op for every config-valid route and cannot make a
   refused amount where the price is fine. It only acts on a price that config would not load. Reserve/settle consistency holds:
   `worst_case_usd` (llm/common.py:99-104) also quantizes UP to 12 dp, and ceil is monotone, so raw actual <= raw worst implies settled
   <= reserved; where actual exceeds worst the overshoot is `settle`'s documented "never refuses" path. Rounding up can exceed a cap by
   at most 1e-12 per call, but cap checks run on the rounded reserved amount, so no hidden excess. k1b `worst_case_usd`
   (k1b/loop.py:102) is unrounded but also <= 12 dp for the same reason. A cost >= 10**9 (absurd token count) is `bad_amount`
   ProviderError (fail closed).
3. Token counts. `type(n) is not int` rejects bool, numpy ints and int subclasses on purpose (`True` would be 1 token, a numpy int
   or float 10.0 from odd JSON would be an unreviewed type); the real adapters hand plain ints. None and 0 mean "not reported" and are
   estimated: `estimate_tokens` is len//3, min 1 (llm/common.py:62), pessimistic for visible text (input: the sent text; output:
   text plus tool-call JSON). It is not an upper bound on what a provider billed: a provider reporting 0 for a huge or hidden (reasoning)
   reply is billed only for the visible text. This is the old behaviour, unchanged; it needs a hostile provider, so not a finding
   (trust boundary: the provider's usage is the bill of record). Rejecting negatives is what closes the real hole.
4. agent_loop :353 and :513. Not safe against custom code; see Major-1. For the built-in providers and FakeLLM, :513 is safe
   (valid cost, or a ProviderError that is caught at :497) and the built-in judge's `verdict.cost_usd` is the same valid reply cost, so
   with only built-ins nothing escapes. The note's claim at :513 is therefore correct only for built-ins.
5. New. Major-1 root cause (no validator on `Reply.cost_usd`/`Verdict.cost_usd`) and Minor-1/2, Nit-1 above. No issue found with
   `clean_spend_amount` (-0 becomes 0 without arithmetic), the postgres settle delta under money_context, or the 'bad_usage'/'bad_amount'
   ProviderError mapping (unmarked, so a billed call keeps its worst case at the gate).
