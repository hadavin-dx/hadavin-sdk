#!/bin/bash
B=/home/user/build/EV-P73-ac94d18; WT=$B/wt; E=$B/evidence; H=/home/user/build/heavy.sh
PORT=55773
UNSET=$(env | cut -d= -f1 | grep -E '^(AWS_|ANTHROPIC_|AZURE_|GOOGLE_|GCP_|VAULT_|OPENAI_|GEMINI_|CLOUDSDK_)' | tr '\n' ' ')
echo "unset names: $UNSET" > $E/unset-env.txt
for n in $UNSET; do unset $n; done
cd $WT
job() { local name=$1 v=$2 dsn=$3; shift 3
  local log=$E/$name.log; : > $log
  echo "HEAD $(git rev-parse HEAD) tree $(git rev-parse HEAD^{tree}) job=$name py=$v dsn=$dsn" >> $log
  if [ $dsn = 1 ]; then export PGHOST=127.0.0.1 PGPORT=$PORT PGUSER=postgres HADAVIN_TEST_PG_DSN="postgresql://postgres@127.0.0.1:$PORT/postgres"; else unset PGHOST PGPORT PGUSER HADAVIN_TEST_PG_DSN; fi
  export PATH=$B/venv$v/bin:/usr/local/bin:/usr/bin:/bin VIRTUAL_ENV=$B/venv$v
  $H $log "$@"; }
J=(tests/test_migration_wiring.py tests/test_migration_rules.py tests/test_migration_postgres.py tests/test_k2_migrations.py tests/test_migration_names.py tests/test_migration_numbers.py tests/test_migration_numbers_guards.py)
F4=(tests/test_migration_wiring.py tests/test_migration_rules.py tests/test_migration_postgres.py tests/test_k2_migrations.py)
job lint 3.13 0 bash -c 'ruff --version; ruff check src tests demos tools; echo rc_check=$?; ruff format --check src tests demos tools; echo rc_format=$?; bandit --version | head -1; bandit -q -r src demos tools -ll; echo rc_bandit=$?'
job full-312-dsn 3.12 1 python -m pytest -m "not live and not perf" -p no:cacheprovider
job full-313-dsn 3.13 1 python -m pytest -m "not live and not perf" -p no:cacheprovider
job full-313-nodsn 3.13 0 python -m pytest -m "not live and not perf" -p no:cacheprovider
mkdir -p $E/mutant-raw
export MIGRATE_MUTANTS_RAW_DIR=$E/mutant-raw
job mutants-313 3.13 1 bash -c 'python tests/migrate_mutants.py; echo rc_mut=$?; python tests/migration_numbers_mutants.py; echo rc_num=$?; git status --short; echo gitstatus_done'
unset MIGRATE_MUTANTS_RAW_DIR
for v in 3.12 3.13; do t=${v/./}
  job mig-$t-run1 $v 1 python -m pytest "${J[@]}" -p no:cacheprovider
  job mig-$t-run2 $v 1 python -m pytest "${J[@]}" -p no:cacheprovider
  job mig-$t-random $v 1 env SHUF_SEED=20261111 PYTHONPATH=$B/shuf python -m pytest -p shufplug "${J[@]}" -p no:cacheprovider
  job mig4-$t $v 1 python -m pytest "${F4[@]}" -p no:cacheprovider
done
job scan 3.13 0 bash -c 'python tools/scan_repo.py; echo rc_scan=$?'
# fail-before on base
cd $B/base
git status --short | head -0
while read st f; do case $st in A|M) mkdir -p "$(dirname $f)"; cp $WT/$f $f;; esac; done < <(git -C $WT diff --name-status 0dabf1f HEAD -- tests)
FB=(tests/test_migration_wiring.py tests/test_migration_rules.py tests/test_migration_postgres.py tests/test_k2_migrations.py tests/test_migration_names.py tests/test_migration_numbers.py tests/test_migration_numbers_guards.py tests/test_k5_fixes2.py tests/test_k5_round10_postgres.py tests/test_p2_postgres.py tests/test_p7_store.py tests/warden_port/test_audit_chain.py tests/contracts)
export PGHOST=127.0.0.1 PGPORT=$PORT PGUSER=postgres HADAVIN_TEST_PG_DSN="postgresql://postgres@127.0.0.1:$PORT/postgres"
export PATH=$B/venv3.13/bin:/usr/local/bin:/usr/bin:/bin VIRTUAL_ENV=$B/venv3.13
log=$E/failbefore.log; echo "BASE $(git rev-parse HEAD) with head's new/changed tests copied in; py=3.13" > $log
PYTHONPATH=$B/base/src python -c "import hadavin_sdk;print('import path',hadavin_sdk.__file__)" >> $log 2>&1
PYTHONPATH=$B/base/src $H $log python -m pytest "${FB[@]}" -p no:cacheprovider --continue-on-collection-errors --junitxml=$E/failbefore.xml -rfE
echo ALLDONE > $E/ALLDONE
