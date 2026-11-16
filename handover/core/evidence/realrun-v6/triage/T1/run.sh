#!/bin/bash
# usage: run.sh LOG pytest-args...
R=/home/user/build/rr6; T=$R/tree-T1; LOG=$1; shift
cd $T && TMPDIR=$T/.tmp-run PYTHONPATH=$T/src timeout 460 unshare -n $R/venv312/bin/python $R/src-v6/drivers/lo_up-q4g.py $R/venv312/bin/python -m pytest -q -p no:cacheprovider -rfs "$@" > $LOG 2>&1
echo "rc=$? DONE" >> $LOG
