# P4a rev 6 plan review, round 6, implementation readiness (egm-implementation-readiness, sonnet)
Verdict: not yet buildable as written. 0 Blockers, 1 Major, 5 Nits. Reviewer ran nothing (Read/Grep/Glob only).

MAJOR
- M1. FB-6 / FB-T6b upgrade recipe (P4a.md ~line 635) cannot give its stated result. `pg_schema()` defaults to `migrated=True` and already applies 0008, so the later `migrate` returns [] not ["0008_spend_reservations_expired_guard"]. Write out `pg_schema(migrated=False)`, `migrate(dsn, reset_role=RESET_GROUP)` twice (reset_role mandatory; RESET_GROUP from tests/stop_state_helpers), how the `expired` row is made (store sweep or direct UPDATE), and which identity runs the UPDATE (ticket says "store's own role", recipe says test's owner login).

NITS
- N1. Hot-file order for limits.py incomplete: "P2a-1b" not mapped to a PR; PR78 dropping `_DEMO_STAGES` (limits.py:33) missing from the order.
- N2. FB-T1e orphan: not in FB-1 test column, no mutant; rounding expression unstated; N must be built from the k1b byte measure.
- N3. Unwritten fixtures: runs row + kill-switch row for FB-T1 stub; counts/attempts/usage numbers for FB-T9 measured sub-rows; how to make real FakeLLM fail (FB-T2).
- N4. Mutant FB-M9g is two mutants under one id; "field reads 0" is wrong (it reads None under the consistency rule).
- N5. Round-5 resolve says "13 causes", ticket says 15 (ticket right); cited release-failure string is a prefix of the logged one.

VERIFIED, NO FINDING: FB-T2 arithmetic (W=27,360, R=164,160), attempts sub-rows, named seams and callers, FB-T9 openai_compat path, FB-T3/T7, SG-T11 and factory, test/mutant counts (17 rows, 35 FB mutants, 19 SG mutants), merge order.
NOT CHECKED: anything not on this branch (P3a-2 late_files, P4d money SQL), 78/79 history, P4a.md body above line 592, sweep_spend_reservations behaviour, replay fence claims, CHANGELOG, lead-order cites.
