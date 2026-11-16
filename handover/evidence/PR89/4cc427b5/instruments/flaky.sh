#!/bin/bash
. /home/user/build/EV-pr89r23-4cc427b5/instr/env.sh
E=/home/user/build/EV-pr89r23-4cc427b5
T="tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in"
: > $RAW/flaky.txt
for side in head main; do
  if [ $side = head ]; then V=$E/venv; D=$E/wt; else V=$E/fbvenv; D=$E/fbwt; fi
  for i in 1 2 3; do
    cd $D
    export UV_PROJECT_ENVIRONMENT=$V
    echo "$side run $i queued $(date -u +%T)" >> $RAW/flaky.txt
    $CLEAN flock /tmp/heavy-slot-1.lock flock /tmp/heavy-slot-2.lock flock /tmp/heavy-slot-3.lock $V/bin/python -m pytest -p no:cacheprovider -q "$T" > $RAW/flaky-$side-$i.log 2>&1
    echo "$side run $i rc=$? $(tail -n1 $RAW/flaky-$side-$i.log) end $(date -u +%T)" >> $RAW/flaky.txt
  done
done
echo done >> $RAW/flaky.txt
