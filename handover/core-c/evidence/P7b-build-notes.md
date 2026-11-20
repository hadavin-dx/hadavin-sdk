# P7b build notes (LimitsMeter review 1, items 1-6)
Branch wip/cloud-core-c/p7b from origin/cloud/core-c e9f5b789a. Not merged.

Done
1. TESTED: recorder `_RealShapeLimits` has configurable settle_for return / reserve / settle errors. New tests: overshoot ("ok","overshoot") through LimitsMeter; SpendRefused("daily_budget") through reserve into the row ("refused","daily_budget"); NotFound from settle_for -> ("ok","settle_failed"), one reserve + one settle_for, nothing released; bind naming another agent.
2. TESTED: `LimitsMeter.__init__` raises fixed-text TypeError unless `reserve` and `settle_for` are callable (object(), only one of the two, non-callables, None).
3. TESTED: one gate per agent. `ModelGate.bind` raises TypeError("one gate per agent: the meter is bound to a different agent") at bind time when the meter is a LimitsMeter bound to another agent (new read-only `LimitsMeter.agent_id`). No new audit code needed. The reserve-time TypeError stays as a fail-closed second line (shows as reserve_refused). Documented in the module docstring.
4. Comments fixed (core-b now has its own `limits.Meter` with `settle(*, agent_id)` and `SpendRefused`; gate keeps its local Protocol and getattr shape check); run-on sentence and the unverified "as agent_loop.py does" removed.
5. Mutant F1a label now says "killed by call shape only (settle and settle_for share _settle in core-b)".
6. Note added to handover/core-c/requests/for-core-b-p3-findings.md. NOT RUN: the p3-scratch e2e / real Postgres test itself (core-b's file).
Mutants: 3 added (P7b-a drop return, P7b-b callable check, P7b-c bind agent check); count 159 -> 162; MIN_MUTANTS = 162.

TESTED: ruff check and format clean; pytest tests/test_model_gate.py test_runmap_enforce_map.py test_gate_mutants_picked_up.py test_gate_install_callers.py: 372 passed, 1 skipped, 7 xfailed.
gate_mutants.py whole run: see final line appended below (NOT RUN if absent).
