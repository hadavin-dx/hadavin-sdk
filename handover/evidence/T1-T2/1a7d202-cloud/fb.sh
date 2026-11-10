# fail-before: at origin/main, copy head's new/changed test files in
echo "main HEAD=$(git rev-parse HEAD)"
H=/home/user/build/EV-A21a-1a7d202/wt
for f in tests/contracts/test_store_time_rules.py tests/contracts/test_t1_meter_cap.py tests/meter_memory_killers.py tests/meter_mutants.py tests/meter_support.py tests/pg_dsn.py tests/postgres_mutants.py tests/test_meter_harness.py tests/test_pg_dsn_guard.py tests/contracts/kinds/store_postgres.py tests/demo_askdata/conftest.py; do cp $H/$f $f; echo "copied $f"; done
git status --short
