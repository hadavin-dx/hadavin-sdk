# P3a-2 plan round 2 probes (ticket author, errata rev 2), 2026-11-11 16:24-16:34 UTC (21:54-22:04 IST)

Throwaway PostgreSQL 16.15 cluster (`initdb -E UTF8 --locale=C.UTF-8`, run as the OS user postgres, unix socket only,
port 56231, `max_prepared_transactions = 10`), stopped and deleted after the run. psycopg 3.3.6 (venv
/home/user/build/venv-p3a2b). Made-up roles and objects only. Each `.sql` is run with psql as the superuser
unless it switches role itself; each `.py` prints its own steps. Output files hold the raw output.

| probe | files | question |
|---|---|---|
| a | a-revoke-grantors.sql/.out, a2-orphan-column.sql/.out | REVOKE and grantors (object rights, column rights, memberships, `GRANTED BY`, step 4's `REVOKE ALL`) |
| b | b-row-types.sql/.out | row types per relation kind, sequences, standalone composite types, default `typacl` |
| c | c-public-schema.sql/.out | the `public` schema access list on 16 and who may use or create in it |
| d, g | dfg.py/dfg.out | psycopg `options` merge; role-level `statement_timeout = 1` against a fresh connection |
| e | e-redefer.sql/.out | a deferred trigger that defers itself again: grant lands at COMMIT after the pre-commit read |
| f | f2.py/f2.out (dfg.out has a first run whose proxy cut too late; f2.out is the valid run) | COMMIT refused by the server versus connection cut after COMMIT was sent |
| h | h-pg-monitor.sql/.out | what rev 1 would print for a named role in `pg_monitor` |
| queries | queries.py, run_queries.py/.out | the final query texts of the ticket, run as a plain role, plus a 25-level diamond of roles |
| mutants | mutclass.py/.out | which mutants of `tests/migrate_mutants.py` at 4d328e3d the ticket's lists miss |
| x | x-extension-owner.sql/.out | settles rev 1's open conflict: who owns a trusted extension that a plain role with CREATE on the database installs |
| cost | createdb_cost.py/.out | create plus drop of one database per test case |
| queries r2 | run_queries_r2.py/.out | the same, after widening Q2's third clause for rule O8 (fresh cluster, deleted after) |
