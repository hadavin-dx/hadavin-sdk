# Merged-tree batch 5 (core-c, 09:4xZ): the same 15 files after G7 round 6 (9d8bc580a)

Tree: cloud/core-c at 9d8bc580a plus notes commits (src and tests equal 9d8bc580a). Command (raw): `uv run --all-extras --group test pytest -q -n 3 --no-header -p no:cacheprovider` over tests/test_model_gate.py, test_runmap_enforce_map.py, test_runmap_map_write.py, test_gate_install_callers.py, test_gate_mutants_picked_up.py, test_redact_settle_loop.py, test_redact_context_after_sweep.py, test_redact_idempotent_property.py, test_redact_fold_budget.py, test_k5_producers.py, test_stage_names.py, test_no_hardcoded_values.py, test_p1d_a_paths.py, test_p1d_link_oracle.py, test_undo_composes.py.
Result (raw last line): `2687 passed, 1 skipped, 5 xfailed in 151.76s (0:02:31)`; no failure or error line (the second run after the 09:35Z container restart killed the first one).
The skip count went from 2 to 1 against batch 4: the linkifier agreement test now runs because linkify-it-py is installed in the dev group (349e6ca0c).
NOT RUN: the whole suite, perf tests on this tree, mutant runs, Python 3.12, PostgreSQL 17.
