#!/bin/bash
# usage: run.sh LOG cmd...   (fresh net namespace, loopback only; sitecustomize blocks and logs any non-loopback connect or name lookup)
LOG=$1; shift
D=$(cat /tmp/work/b12.path)
cd "/tmp/work/b12-10209-old"
exec unshare -rn python3 /tmp/work/b12-harness/lo_up.py env RV_LOG=$LOG PYTHONPATH=/tmp/work/b12-harness:/tmp/work/b12-10209-old/src:/tmp/work/b12-10209-old "$@"
