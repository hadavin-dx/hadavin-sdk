# Checkpoint, EV q8a1-a1869655 (written 23:12 UTC, 11 min in)
Done: setup, ruff check/format (0), bandit (0), scan_repo (0), gitleaks (0), probes (260 probe results incl. old 107 shape), validator/tool-URL probes.
Full pytest at a1869655: 12 FAILED, 10973 passed, 1 skipped (rc 1, 294 s). Failures: 7x tests/contracts/test_secrets.py:19, test_k3_pilot_env.py:125, test_p2_postgres.py:119, test_s3_gate.py:72, warden_port/test_audit_chain.py:258, demo_askdata dblink-connect (my Postgres server env lacked PGHOST; to be re-run alone).
Running: tests/stage_mutants.py (alone). Next: failing tests re-run (PG env fixed), fail-before on 4ccb4f9a and origin/main, RESULTS.md.
