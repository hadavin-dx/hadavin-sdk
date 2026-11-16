# PR72 (P6a-1) result review, head 84bc5d5 (condensed from the egm-codebase-details report; saved by the lead)
Verdict: 0 Blocker, 2 Major, 4 Nit. Not read in detail (UNVERIFIED): mutants 23-72 patch lines, full-312, perf, ruff, bandit, scan-repo, wheel-files, stage-mutants.
- Major 1: private ids / order numbers / mutant numbers in public test text (tests/test_client_profile.py: "gate of P5c" x4, "mutant 47/50/54/55", "order 133", docstring "T0 T1 T2 T5 T7"). Violates order 132 / LEAD-ORDERS:809.
- Major 2: P6a-1's own fail-before evidence (o132: 43 fail/21 pass, collect, recount, pg, client-profile) not in snapshot; Postgres per-test lines for test_k3_pilot_env.py / test_k5_round8_postgres.py not shown at new head. Rerun/supply at 84bc5d5.
- Order 132 asks a build note in the ticket for the pilot/prod refusal of made_up_data_only; ticket S6 still says "no effect": confirm or add.
- Nit: evidence mutant numbers 47-72 clash with ticket BN-5 numbers (goes away with Major 1); ticket names T5(m) as killer of mutant 16 but real killers are t5j and t5q; strict-oldcode.txt header misleading (real proof is strict-oldcode-80f94b8.txt 49/49); `# pragma: no cover` at the _StubDetector.check stub.
- Confirmed: S1, S2, S6, strict-bool sweep built and tested; no suppressions besides the pragma; no weakened tests; credentials built from parts; P6a-2 absent (ticket must stay open).
