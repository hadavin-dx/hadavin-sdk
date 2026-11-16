#!/bin/sh
cd /home/user/build/rr6/tree-D1
export TMPDIR=/home/user/build/rr6/tmp-D1 PYTHONPATH=/home/user/build/rr6/tree-D1/src PYTHONDONTWRITEBYTECODE=1
S=$(date +%s)
timeout 2400 unshare -n python3 /home/user/build/rr6/src-v6/drivers/lo_up-q4g.py /home/user/build/rr6/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs tests/ > /home/user/build/rr6/out/D1/full.log 2>&1
echo "rc=$? wall=$(( $(date +%s)-S ))" >> /home/user/build/rr6/out/D1/full.log
