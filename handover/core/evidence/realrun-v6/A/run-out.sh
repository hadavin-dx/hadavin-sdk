#!/bin/bash
# usage: run.sh TREE RUNNO
RR=/home/user/build/rr6; T=$RR/$1; N=$2
SHA=$(cd $T && git rev-parse --short HEAD)
cd $T; mkdir -p $RR/tmp-$1
S=$(date +%s)
TMPDIR=$RR/tmp-$1 PYTHONPATH=$T/src unshare -n $RR/venv312/bin/python $RR/src-v6/drivers/lo_up-q4g.py $RR/venv312/bin/python -m pytest -q -p no:cacheprovider -rfs > $RR/out/A/run$N.log 2>&1
rc=$?
echo "EXIT=$rc WALL=$(( $(date +%s)-S ))s" >> $RR/out/A/run$N.log
echo DONE >> $RR/out/A/run$N.log
