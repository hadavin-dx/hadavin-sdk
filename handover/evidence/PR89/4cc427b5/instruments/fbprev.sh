#!/bin/bash
. /home/user/build/EV-pr89r23-4cc427b5/instr/env.sh
export UV_PROJECT_ENVIRONMENT=$E/prevvenv
E=/home/user/build/EV-pr89r23-4cc427b5; export UV_PROJECT_ENVIRONMENT=$E/prevvenv
cd $E/prevwt
echo "queued $(date -u +%T)" > $RAW/fbprev.time
$CLEAN /home/user/build/heavy.sh $UV_PROJECT_ENVIRONMENT/bin/python -m pytest -p no:cacheprovider -q -rfE --continue-on-collection-errors --junitxml=$RAW/fbprev.xml tests/test_mutation_runner.py tests/test_mutation_runner_keywords.py tests/test_mutation_runner_meta.py > $RAW/fbprev.log 2>&1
echo "rc=$? end $(date -u +%T)" >> $RAW/fbprev.time
