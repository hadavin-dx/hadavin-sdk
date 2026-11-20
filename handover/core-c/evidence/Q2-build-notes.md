# Q2 build notes: spend fails closed in the gate (branch wip/cloud-core-c/q2-spend, from origin/cloud/core-c d993b4eed)

Code: model_gate.py (REFUSAL_MARK_TYPES, cost_verified, usable_cost, attempt_costs_total, has_input, ModelGate usd_cap, chat reserve and exhausted paths), models.py (Reply.cost_verified).

Re-pins (old behaviour the decision changes):
- test_d2 "a zero worst case is allowed" -> only for an empty input (renamed); new refusal test.
- test_m5 "a zero cost reply is settled at zero" -> only a verified zero (renamed); unverified is cost_unknown.
- test_the_gate_in_front_of_script_llm...: ScriptLLM replies are unverified zeros: settles == [] (was 2), both reservations stay booked.
- i9 source guard: GETATTR_ON_EXC gains attempt_costs, attempt_costs_complete; EXC_MAY_GO_TO gains attempt_costs_total.
- gate_mutants G12, G13, G13b search text follows `isinstance(exc, REFUSAL_MARK_TYPES)`.
- MIN_MUTANTS 159 -> 165 (measured len(M) = 165; six new Q2a-Q2f).

TESTED: test_model_gate.py, test_runmap_enforce_map.py, test_gate_mutants_picked_up.py, test_gate_install_callers.py, test_s3_gate.py all pass (403 passed at the code commit; test_model_gate + picked_up re-run after the last test edit: pass). ruff check and format clean.
TESTED mutants (subsets, one at a time): Q2a-Q2f, G12, G13, G13b, G32, G23d killed with the expected reason.
NOT RUN: `python tests/gate_mutants.py` whole (other mutant runs active, lead's instruction); other mutants whose search text did not change are untouched in text but not re-run. Any real adapter (fake/network kinds) setting cost_verified: not built (core-b). usd_cap not wired by any installer yet.
Limits: attempt_costs is a gate-side contract only; retry.py provides none today, so every exhausted call keeps the full worst case.
