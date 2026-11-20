# For core-b / core-a: spend fails closed in the gate (Q2, P8 item 3; K21, K23, K25)

Gate side is built (branch wip/cloud-core-c/q2-spend). What the gate now needs from you:

## 1. Worst-case function (K25)
`worst_case(route: str, system: str, messages: list[dict], tools: list[dict] | None, documents: list[bytes] | None, output_schema: dict | None) -> Decimal`
- Upper bound in USD: input (system + messages + tool schemas + documents + output_schema) at the input price, plus max_tokens at the output price, times max_attempts.
- MUST NEVER return 0 for a non-empty input. The gate now refuses a 0 for non-empty input (audit code `bad_amount`, raises WorstCaseInvalid, no call). 0 is accepted only when system, tools, documents and every message content are all empty.
- If the cost is unknown (no price for the route), return `None`: the gate reserves its `usd_cap` (new `ModelGate(..., usd_cap=Decimal)`); with no cap set the call is refused (`worst_case_invalid`). Installer must pass `usd_cap`.
- Raising, a float, NaN, negative: refused as before.

## 2. Reply.cost_verified (K21)
Added `cost_verified: bool = False` to `models.Reply` (one line, backwards compatible; core-a/core-b own models.py, please keep it). Contract: the provider adapter sets `cost_verified=True` ONLY when `cost_usd` is the provider's own figure (including a true 0). The gate treats cost 0 with anything but exactly `True` as `cost_unknown`: the worst case stays booked. Non-zero costs need no flag. llm/fake.py and every network kind must set it where their cost is real, or every call stays at its worst case until the sweep.

## 3. Per-attempt costs on ProviderExhausted (K23)
ProviderExhausted has no attempts data today. The gate settles the sum of `exc.attempt_costs` (list/tuple of Decimal, one per attempt) only if `exc.attempt_costs_complete is True` and the sum is > 0 and every entry is a usable amount. Otherwise the worst case (which covers all attempts) stays booked. retry.py should set both attributes if it can know each attempt's cost; sum 0 is never settled this way.

## 4. refused_before_response (K23)
Honoured only on `REFUSAL_MARK_TYPES = (ProviderError, ProviderExhausted)` (hadavin_sdk.llm.protocol); a mark on any other type is ignored; a mark that raises on read is not a mark. A new adapter exception class must subclass ProviderError.

## Pins
Code commit and test names: see handover/core-c/evidence/Q2-build-notes.md (branch wip/cloud-core-c/q2-spend).
- zero worst case: test_q2_a_zero_worst_case_for_a_non_empty_input_is_refused_as_bad_amount, test_d2_a_zero_worst_case_is_allowed_only_for_an_empty_input; mutant Q2a
- unknown -> cap: test_q2_an_unknown_worst_case_reserves_the_usd_cap_and_without_a_cap_is_refused; Q2b
- unverified zero: test_q2_a_hostile_adapter_returning_an_unverified_zero_cost_is_cost_unknown, test_m5_a_verified_zero_cost_reply_is_settled_at_zero; Q2c
- attempts: test_q2_an_exhausted_call_with_three_attempts_and_no_costs_keeps_the_worst_case_booked, ..._settles_the_sum_of_all_three_attempts_..., test_q2_incomplete_or_unusable_attempt_costs_...; Q2d, Q2e
- mark allowlist: test_q2_a_forged_refusal_mark_on_a_plain_exception_is_ignored; Q2f (G12/G13/G13b retargeted)
