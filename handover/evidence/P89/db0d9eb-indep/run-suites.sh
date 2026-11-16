#!/bin/bash
O=/home/user/build/EVOUT-P89-indep-db0d9eb; cd /home/user/build/WT-P89i
export HADAVIN_TEST_PG_DSN="postgresql://postgres@127.0.0.1:56189/postgres" PGHOST=127.0.0.1 PGPORT=56189 PGUSER=postgres
for v in 312 313; do
  B=/home/user/build/venv-p89i-$v/bin; rm -rf /home/user/build/p89i-tmp
  /home/user/build/heavy.sh $O/06-pytest-$v.log $B/python -X faulthandler -m pytest -q -m "not live and not perf" -rs -p no:cacheprovider --basetemp=/home/user/build/p89i-tmp --junitxml=$O/06-pytest-$v.xml
  echo "$v done $(date -u +%T)" >> /home/user/build/B-P89-indep-checkpoint.md
done
rm -rf /home/user/build/p89i-tmp
echo SUITES-DONE >> $O/progress.txt
