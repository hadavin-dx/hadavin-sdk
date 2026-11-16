#!/bin/bash
# usage: run.sh <tree> <pytest args...>
T=$1; shift
export TMPDIR=/home/user/build/rr6/tmp-C-r7uc PYTHONPATH=$T/src PYTHONDONTWRITEBYTECODE=1
cd $T
exec unshare -n python3 /home/user/build/rr6/src-v6/drivers/lo_up-q4g.py /home/user/build/rr6/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs "$@"
