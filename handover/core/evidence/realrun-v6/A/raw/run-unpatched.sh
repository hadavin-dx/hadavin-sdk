#!/bin/bash
cd /home/user/build/rr6/tree-U
s=$(date +%s)
TMPDIR=$PWD/.tmp-run PYTHONPATH=$PWD/src timeout 1800 unshare -n python ../src-v6/drivers/lo_up-q4g.py ../venv312/bin/python -m pytest -q -p no:cacheprovider -rfs tests/ > ../out/A/unpatched-main-full-tmpdir-in-tree.log 2>&1
echo "rc=$? wall=$(( $(date +%s)-s ))s" >> ../out/A/unpatched-main-full-tmpdir-in-tree.log
