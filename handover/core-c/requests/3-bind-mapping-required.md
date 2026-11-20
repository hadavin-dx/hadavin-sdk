# Request 3 from core-c (TEXT) to core-b (owner of the install of the model gate: runtime/agent_loop.py, guard/judge.py, evals.py, k1b/)
Date 2026-11-20. Source: lead ORDER 017 items 1, 2 and 5 (design review E6; review finding dz-B1 = cb-M5). Built in guard/model_gate.py by core-c. ModelGate, bind and the module path keep their names.

## 1. The change in `bind`
Before: `bind(agent_id, run_id, *, mapping=None, principal=None, source="gate")`; `mapping=None` silently skipped the enforce step.
Now:    `bind(agent_id, run_id, *, mapping, principal=None, source="gate")`.
- `mapping` is a REQUIRED keyword. Leaving it out is a TypeError at bind time. `mapping=None` (or anything that is not a `collections.abc.Mapping`) is a TypeError too, so a forgotten variable cannot turn the guarantee off.
- "No run map" is said in the call with the named constant `NO_MAP` (`from hadavin_sdk.guard.model_gate import NO_MAP`): `gate.bind(agent_id, run_id, mapping=NO_MAP)`. Only the eval and replay command lines may use it.
- A no-map call is marked in every audit row it writes: the field is `models.AuditEvent.decision` (a free `str | None`), value `"no_map"`; a gate with a map writes `"map_enforced"` (an empty map included).

## 2. What each of your binds passes
- Run loop (`runtime/agent_loop.py`, the live `RunMap` of line 397, `rmap`): `mapping=rmap` (the same object the run keeps writing: the gate reads it by reference and takes one copy per `chat` call), `principal=run.principal_id`.
- Judge (`guard/judge.py:72`, the `llm_judge` detector called from `agent_loop.py` `_screen`) and the shadow-card binds: pass the RUN's map as well (`mapping=rmap`), not NO_MAP. Each needs a test that a value the run knows never leaves raw in what the client receives (a `FakeLLM` that records its input is enough).
- Eval and replay command lines (`evals.py:73`, `k1b/replay.py`): `mapping=NO_MAP`. These have no run and no map.
- A test per site that builds the bound gate the way the site does and fails if `mapping` is NO_MAP outside the two command lines (grep for `NO_MAP` in src: only evals.py and k1b/replay.py may name it).

## 3. The gate's exception type for every failure BEFORE the provider call (ORDER 017 item 5)
`hadavin_sdk.guard.model_gate.GateRefused` (base class; subclasses `UnmaskedInput`, `WorstCaseInvalid`, `ReservationInvalid`, `FramingRefused`). Catch `GateRefused` and you know: NO provider call was made. It carries only a `code` (also `exc.args == (code,)`): no text, no secret, `__cause__` and `__context__` both None.
Raised as `GateRefused` for every failure before the call that is NOT a `SpendRefused`:
| code | when |
|---|---|
| `mask_refused` | the enforce step failed: content that is not `str`, a document that is not `bytes`, a text over `runmap.ENFORCE_MAX_CHARS` (8 x `defaults.MAX_REDACT_CHARS`), the time budget, a bad map, more than 4 sweeps |
| `framing_refused` | a call that carries tool-result framing and a value of the run's map EQUALS a framing word (TOOL, RESULT, END, call_id, tool), a tool name (the `tools` list or an assistant line) or a call id |
| `worst_case_failed` | your `worst_case` function raised (its error is NOT passed on: it may carry text) |
| `worst_case_invalid` | it returned something that is not a finite `Decimal >= 0` |
| `reserve_refused` | `reserve` raised anything that is not a `SpendRefused`: a KeyError, a store that is down, an OSError |
| `reservation_invalid` | `reserve` returned something that is not a non-empty `str` (whatever it booked stays booked until the store's sweep) |
UNCHANGED: a `SpendRefused` (a meter error whose `.reason` is one of the six published reasons: kill_switch, daily_budget, monthly_budget, limits_unavailable, bad_amount, usd_cap) passes as the same object; errors of the client (ProviderError, ProviderExhausted, timeouts, anything) pass as the same object; KeyboardInterrupt / SystemExit pass. When `limits.SpendRefused` lands in `src/hadavin_sdk/limits.py` the gate will import it; until then it is recognised by its published `.reason`.
Map per site (yours to decide, listed in tickets/F-gate-wrapper-body.md "For core-b (install)"): `GateRefused` and `SpendRefused` both mean "no call, nothing was sent"; the run loop must catch both (today line 477 catches ProviderError only and would leave the run in WORKING).

## 4. Cost absent (ORDER 017 item 2)
A reply whose `cost_usd` is absent, None, not a Decimal, NaN, infinite or negative is returned to the caller and NOT settled (audit row `ok` / `cost_unknown`; the worst case stays booked and the store's sweep closes it). `models.Reply.cost_usd` defaults to `Decimal(0)` (models.py line 299): an adapter that sets no cost looks like a free call and is settled at 0. core-b must change the default to `None` (type `Decimal | None`) or make the field required, and every adapter must set it. Until then the gate cannot see the difference.

## 5. Tests and mutants
tests/test_model_gate.py (`test_o17_*`, `test_bind_has_the_published_signature`) and tests/gate_mutants.py (O1 to O7) pin all of the above; run `uv run python tests/gate_mutants.py` after any change to the gate.

## 6. Review round 2 additions (contract sentences)
- The `refused_before_response` mark (settle 0) must be set ONLY if NO attempt of a retried call was answered by the provider. A retry layer that re-raises the LAST attempt's marked error after an earlier attempt was answered would have the gate settle 0 for a billed call. Mark on the error the retry layer finally raises only when every attempt was refused before any response.
- `system`, `tools` and `output_schema` are forwarded untouched (only message `content` and documents are enforced). The install-time check that `system` comes ONLY from the prompt registry (never from run text) belongs to core-b ("For core-b (install)" in the ticket).
- Audit `decision`: `map_enforced` (module default enforce, map with entries), `map_enforced_empty`, `enforce_custom`, `map_failed` (enforce step refused), `no_map`. New row codes: `call_interrupted` (also for `worst_case`), `reserve_interrupted`, `held_value_left`.
- `framing_refused` now only for a value of a secret kind (4+ characters) that EQUALS a tool name or a call id. `models.Reply.cost_usd` default and the `GateRefused` / `SpendRefused` catch sites (agent_loop.py:477, evals.py:73, extract.py:47, guard/injection.py:217-227 catches Exception and would report a kill_switch as guard_unavailable) stay core-b's.
