# INTERFACE (ii): reserve/settle API used by the model gate (version 1)
Owner and builder: core-b. User: core-c's gate wrapper (the one new module that wraps every model client). Contract test: written by a different agent than the builder.

## Plain words
Before a model call the gate asks a "payer" to set aside the most the call could cost (the worst case). If the payer refuses, the model is NOT called. After the call the gate tells the payer the real cost. If the gate leaves without saying anything (an error, a timeout, a killed thread), the payer keeps the full worst case booked. The gate never touches the store, the caps or the stop state itself.

## Source (reuse, not new design)
Branch core/P4b1 (PR 79, head 8cc2021) already has this API: src/hadavin_sdk/meter.py (Meter, Hold, Caps, Settled, SettleFailure, MeterError, OverBudget, MeterUnavailable), money.py (SpendMicro), limits.py:37-85 (Limits.caps, Limits.hold). It is wired into no call site there. Step F takes it and adds only what is marked NEW below. Facts with line numbers: handover/core-b/notes/heads-money.md sections 4.1 to 4.6.

## The API (exact signatures in reserve_settle_api.py)
```python
with payer.hold(agent_id, worst, run_id=run_id) as hold:   # raises MeterError: NO model call
    reply = inner.chat(...)                                # one hold covers the whole chat call incl. the client's own retries
    hold.record(actual_spend(reply))                       # settle at the real cost on exit
# leaving the block without record() or release(): settled at the worst case
```
- `payer.hold(agent_id: str, worst: SpendMicro, *, run_id: str | None = None) -> ContextManager[Hold]`
- `hold.record(actual: SpendMicro | None, *, measured: bool = True) -> None`: plan to settle at `actual` (None = at the worst case). Zero is refused: use release().
- `hold.release() -> None`: plan to give everything back. Use ONLY when the request was certainly never sent to the provider (for example the mask step refused after the hold was taken). The last of record and release wins.
- `worst_case(route, system, messages, *, tools, documents, requests) -> SpendMicro` NEW shared function (module hadavin_sdk.meter): the byte length of everything sent (one token per byte at most) at the input price plus route.max_tokens at the output price, times `requests` (the client's max_attempts), rounded UP once. Formula taken from core/P4a k1b/loop.py:115-132, extended with documents.
- `actual_spend(reply) -> SpendMicro` NEW shared function: Reply.cost_usd rounded UP to whole micro-dollars.

## Two payers, one shape (the gate takes the payer as a constructor argument, plan-v3 A3)
| payer | where | backed by | caps |
|---|---|---|---|
| Limits (limits.py) | Runtime (agent loop, judge, shadow-card judge) | the store, interface (i) | the agent's day and month budget and max_run_usd from the registry |
| Budget (k1b/loop.py) NEW methods | evals command line and replay (no shared store there) | process memory, with a lock | its one total limit; `spent` includes held amounts |
Both satisfy the Protocol `Payer`. The gate must not test which one it got.

## Errors the gate must handle (all subclasses of MeterError; any of them from hold() means: do not call the model)
| error | meaning | gate does |
|---|---|---|
| OverBudget(reasons, which, cap, current, requested, day) | a cap or the stop state refused; reasons are words like daily_budget, monthly_budget, run_budget, kill_switch | refuse the call; pass the error up unchanged (the agent loop turns it into the existing limits stop) |
| MeterUnavailable(code) | the payer could not do its job (store unreachable, busy, conflict, unknown run, damaged counter) | refuse the call; pass up unchanged |
| MeterError("unknown agent") | agent_id is not in the registry | refuse the call |
A failure of the settle at the end of the block is NOT raised to the gate: the reservation stays booked (worst case) and the payer signals `on_settle_failed`. The body's own exception always propagates unchanged.

## INVARIANTS (numbered; each gets a contract test, run against BOTH payers)
1. No model call without a successful hold: if hold() raises, inner.chat is called zero times.
2. One hold per chat call, taken before any provider contact, covering every internal retry of the client.
3. On a normal reply the books change by exactly actual_spend(reply) for that call (not worst, not zero).
4. On any exit without record or release (exception, timeout, KeyboardInterrupt, SystemExit) the books keep the full worst case.
5. release gives the full amount back and is used only when nothing was sent.
6. Under N concurrent holds on one agent the sum of held and settled amounts never passes a cap (store payer: by interface (i) invariant 1; Budget payer: by its lock).
7. A real cost above the worst case is booked in full and signalled (on_overshoot), never dropped.
8. The gate adds no second booking: after step F nothing calls Limits.charge or Store.add_cost for a model call that went through a hold (the five charge sites agent_loop.py:325, 485 and k1b/loop.py:170, 179, 206 are deleted in the same change; a hold with run_id already raises the run's cost).
9. The stop state ON refuses a new hold with reasons containing kill_switch (store payer). The Budget payer does not read the stop state (stated limit: the command-line paths do not read it).
10. Money types never mix: the API takes SpendMicro only; a float, bool, Decimal or BusinessMoney is a TypeError.

## What core-c's wrapper needs from core-b, and gives back
- Gets at construction: `inner: LLM`, `payer: Payer`, `routes` (for worst_case), an audit writer; `bind(agent_id, run_id) -> LLM` returns the bound client (no ContextVar).
- core-b installs the wrapper inside Runtime.__init__, _replay and evals.gate, and deletes the five charge sites (ticket F-store / F-install).
- Open point for the joint review of F: the reservation id is random per hold today (meter.py:252 on the branch). If a retried agent-loop step must not reserve twice, the id must come from (run_id, step number). Recommended: keep random; a crashed step's hold stays booked at the worst case and the run ends with a person, so no second reservation for the same step can be made by a retry.

## Contract test to write (different agent than the builder; one file, both payers by parameter)
tests/contracts/test_payer.py: invariants 1 to 10 with a fake inner client that counts calls; 50 threads on one Budget; hostile amounts (zero, negative, float, bool, NaN Decimal, 10**15 dollars); record then release and release then record; exception types raised inside the block (ValueError, KeyboardInterrupt, SystemExit); settle failure at exit (store raises) leaves the worst case booked and calls on_settle_failed once. Mutants to kill: hold after the call instead of before; exit settles at zero; release on exception; lock removed from Budget; record(None) settles at zero.
