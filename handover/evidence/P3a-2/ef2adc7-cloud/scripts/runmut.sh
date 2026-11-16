#!/bin/bash
cd /home/user/build/EV-P73-ef2adc7/wt; V=/home/user/build/EV-P73-ef2adc7/venv3.13/bin
echo "HEAD $(git rev-parse HEAD)"; echo "python $($V/python -V)"
export HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:<port>/postgres HADAVIN_REQUIRE_PINNED_UNIDATA=1
$V/python tests/migrate_mutants.py; r1=$?; echo "migrate_mutants_rc=$r1"; git status --short; echo "git_status_after_migrate_mutants_lines=$(git status --short | wc -l)"
$V/python tests/migration_numbers_mutants.py; r2=$?; echo "migration_numbers_mutants_rc=$r2"; git status --short; echo "git_status_after_numbers_mutants_lines=$(git status --short | wc -l)"
exit $((r1|r2))
