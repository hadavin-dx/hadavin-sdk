# FF build notes (F1/F2/F3 gate-side, branch wip/cloud-core-c/f-findings from origin/cloud/core-c a4c99a006), 2026-11-20

TESTED (this worktree, load under 3):
- F1: `model_gate.LimitsMeter(limits, agent_id)`; 3 tests in tests/test_model_gate.py (recorder with core-b Limits call shapes, no database) pass; 4 new mutants F1a-F1d in tests/gate_mutants.py all KILLED.
- tests/test_model_gate.py, test_runmap_enforce_map.py, test_gate_mutants_picked_up.py, test_gate_install_callers.py: 359 passed, 1 skipped, 7 xfailed (incl. the new F2 strict xfail); rerun after MIN_MUTANTS 147 -> 151 below.
- `python tests/gate_mutants.py` whole: 150 of 151 good; only R8 is a problem (known, E20 update: equivalent under G9).
- ruff check src tests: clean; ruff format on the two edited files: clean.
- The source guard (test_i9) forbids message text in a raise: the wrong-agent reserve raises a fixed-text TypeError, not ValueError.
- F3: the test is true on core-c's tree (passes), NOT edited; the change for the merge is written in handover/core-c/requests/for-core-b-p3-findings.md.
- F2: nothing implemented; strict xfail test_f2_a_reply_with_a_planted_secret_is_returned_unmasked; options in ESCALATIONS.md E25.

NOT RUN:
- Against real Postgres / the real core-b `Limits` (the recorder copies its call shapes from origin/cloud/core-b src/hadavin_sdk/limits.py and runtime/agent_loop.py); p3-scratch's test_gate_store_e2e.py not re-run with LimitsMeter.
- The full test suite, other mutant files, the merge with core-b.
