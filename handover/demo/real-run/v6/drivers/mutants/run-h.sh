#!/bin/bash
LOG=$1; shift
D=$(cat /tmp/work/b12.path)
cd /tmp/work/b12-h
exec unshare -rn python3 /tmp/work/b12-harness/lo_up.py env RV_LOG=$LOG PYTHONPATH=/tmp/work/b12-harness:$D/src:$D "$@"
