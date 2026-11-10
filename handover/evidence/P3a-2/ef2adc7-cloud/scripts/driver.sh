#!/bin/bash
D=/home/user/build/EV-P73-ef2adc7; E=/home/user/hadavin-sdk/handover/evidence/P3a-2/ef2adc7-cloud
H=/home/user/build/heavy.sh; C=$D/clean.sh
M="tests/test_k2_migrations.py tests/test_k5_fixes2.py tests/test_migration_names.py tests/test_migration_numbers.py tests/test_migration_numbers_guards.py tests/test_migration_postgres.py tests/test_migration_rules.py tests/test_migration_wiring.py tests/test_p2_postgres.py"
SEED=${SEED:-7311}
run() { name=$1; shift; : > $E/$name.log; echo "$(date -u +%FT%TZ) start $name" >> $E/_driver.log; $H $E/$name.log "$@"; rc=$?; echo "$(date -u +%FT%TZ) end $name rc=$rc" >> $E/_driver.log; }

run 02a-full-py313-dsn $C $D/runpt.sh 3.13 1
run 02b-full-py312-dsn $C $D/runpt.sh 3.12 1
run 02c-full-py313-nodsn $C $D/runpt.sh 3.13 0
run 03-mutants-py313 $C $D/runmut.sh
for v in 3.12 3.13; do
  run 04-migtests-py$v-dsn-run1 $C $D/runpt.sh $v 1 $M
  run 04-migtests-py$v-dsn-run2 $C $D/runpt.sh $v 1 $M
  run 04-migtests-py$v-dsn-random-seed$SEED env SHUF_SEED=$SEED PYTHONPATH=$D/shuf $C $D/runpt.sh $v 1 -p shufplugin $M
done
echo "$(date -u +%FT%TZ) DRIVER-DONE-A" >> $E/_driver.log
