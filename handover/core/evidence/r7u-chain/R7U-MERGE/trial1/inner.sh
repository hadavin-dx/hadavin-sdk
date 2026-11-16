#!/bin/bash
echo "start $(date -u +%FT%TZ) load=$(cut -d' ' -f1-3 /proc/loadavg) tree=/home/user/build/rr6/tree-R7U-trial" > "/home/user/build/rr6/out/R7U-MERGE/trial1/guard.wrap"
cd "/home/user/build/rr6/out/R7U-MERGE/trial1/stage"
env -i HOME="/home/user/build/rr6/out/R7U-MERGE/trial1/tmp" LANG=C.UTF-8 TMPDIR="/home/user/build/rr6/out/R7U-MERGE/trial1/tmp" PYTHONPATH="/home/user/build/rr6/out/R7U-MERGE/trial1/stage/src" PYTHONDONTWRITEBYTECODE=1 \
  PLAYWRIGHT_BROWSERS_PATH="/home/user/build/rr6/pw-browsers" GITLEAKS_BIN="/home/user/build/rr6/bin/gitleaks" DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 \
  PATH="/home/user/build/rr6/bin:/usr/local/bin:/usr/bin:/bin" \
  timeout -k 20 2400 unshare -n python3 "/home/user/build/rr6/src-v6/drivers/lo_up-q4g.py" "/home/user/build/rr6/venv-br/bin/python" -m pytest -q -p no:cacheprovider -rfs $(cat "/home/user/build/rr6/out/R7U-MERGE/trial1/guard-files.txt" | tr '\n' ' ') > "/home/user/build/rr6/out/R7U-MERGE/trial1/guard.log" 2>&1
rc=$?
echo "end $(date -u +%FT%TZ) rc=$rc" >> "/home/user/build/rr6/out/R7U-MERGE/trial1/guard.wrap"
echo $rc > "/home/user/build/rr6/out/R7U-MERGE/trial1/guard.rc"
