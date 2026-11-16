#!/bin/bash
cd /home/user/build/rr6/tree-AF
s=$(date +%s)
TMPDIR=/home/user/build/rr6/tmp-AF PYTHONPATH=$PWD/src PLAYWRIGHT_BROWSERS_PATH=/home/user/build/rr6/pw-browsers GITLEAKS_BIN=/home/user/build/rr6/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 timeout 2400 unshare -n python /home/user/build/rr6/src-v6/drivers/lo_up-q4g.py /home/user/build/rr6/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs tests/ > /home/user/build/rr6/out/AF/after-full.log 2>&1
echo "rc=$? wall=$(( $(date +%s)-s ))s" >> /home/user/build/rr6/out/AF/after-full.log
