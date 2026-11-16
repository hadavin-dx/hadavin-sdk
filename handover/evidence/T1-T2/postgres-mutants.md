# Postgres-side mutants for the spend counters (A21a fix round 1, head ba89ea7)
The runner (tools/mutation_runner.py) strips HADAVIN_TEST_PG_DSN from its child and runs without conftest, so it cannot
run store-kind tests. Commands: start a cluster (initdb -E UTF8 --locale=C.UTF-8 -A trust, port 55490), then
`HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55490/postgres python handover/evidence/T1-T2/postgres_mutants.py <worktree>`.
It copies src/tests/tools to a temp dir, plants ONE change in src/hadavin_sdk/store/postgres.py, runs
tests/contracts/test_store_time_rules.py -k postgres.
Result: baseline rc=0 (56 passed); P1 day counter replaced instead of added KILLED; P2 month counter replaced KILLED;
P3 add_spend month key = day KILLED (by a database check constraint error, not an assertion); P4 spend_totals month key = day KILLED.
Cluster stopped and its data folder removed afterwards.
