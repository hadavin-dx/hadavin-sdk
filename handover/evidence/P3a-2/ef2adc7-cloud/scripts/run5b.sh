#!/bin/bash
# fail-before: head's migration tests on the PR base source (py3.13 venv, PYTHONPATH forces base/src)
B=/home/user/build/EV-P73-ef2adc7/base; V=/home/user/build/EV-P73-ef2adc7/venv3.13/bin; E=/home/user/hadavin-sdk/handover/evidence/P3a-2/ef2adc7-cloud
cd $B; echo "BASE HEAD $(git rev-parse HEAD) (merge-base of origin/main and ef2adc7)"; echo "python $($V/python -V)"
export PYTHONPATH=$B/src HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:<port>/postgres HADAVIN_REQUIRE_PINNED_UNIDATA=1
$V/python -c "import hadavin_sdk,sys;print('hadavin_sdk from',hadavin_sdk.__file__)"
M="tests/test_k2_migrations.py tests/test_k5_fixes2.py tests/test_migration_names.py tests/test_migration_numbers.py tests/test_migration_numbers_guards.py tests/test_migration_postgres.py tests/test_migration_rules.py tests/test_migration_wiring.py tests/test_p2_postgres.py"
$V/python -m pytest -q -m "not live and not perf" -rfEs -p no:cacheprovider --continue-on-collection-errors -rfE --junitxml=$E/05b-failbefore-junit.xml $M
