# PR 72 (P6a) round 1, egm-codebase-details, snapshot d15e53a (condensed by cloud session)
Verdict: no code Blocker. 3 Major, 5 Nit. P6a-2 (S4 scanner, T6) not in this snapshot, not reviewed.
- M1 The 62 P6a-1 mutants are NOT RUN (incl. mutants 15-18, 20, 46 and the live-field rows); evidence has no mutant log at this head.
- M2 Missing evidence: fail-before on old code, recount of rows, collect/wheel check, mutant run.
- M3 Ticket drift in tickets/P6a.md (rows/mutant counts differ from the code; T5q and T7f add ~50 mutants the ticket does not list).
- Nits: detector allow-list should include REPO/"tools"; docs/CHANGELOG wording on self-hosted model; model_copy rows are defence in depth (keep).
Checked correct: app.py:108-121 check position/identity compare; _BUILD_PARAMS; config.py:402-425 single ConfigError; StrictBool; reuse of _cross_checks/DEMO_ONLY; 5 build tests carry allow_test_doubles=True; evidence: 65 passed on 3.12 and 3.13, PG pair 11 passed, ruff/format/bandit clean.
