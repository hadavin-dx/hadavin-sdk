#!/bin/bash
# usage: loader.sh <copy> <max_seconds>  : repeats the r7u_b test file in that copy until the time is up (bounded)
R=/home/user/build/rr6; O=$R/out/EV7U; T=$O/$1; mkdir -p $O/tmp-load-$1; cd $T
end=$(( $(date +%s) + $2 ))
while [ $(date +%s) -lt $end ]; do
env -i HOME=$O/tmp-load-$1 LANG=C.UTF-8 TMPDIR=$O/tmp-load-$1 PYTHONPATH=$T/src PYTHONDONTWRITEBYTECODE=1 PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 PATH=$R/bin:/usr/local/bin:/usr/bin:/bin \
  timeout -k 10 600 unshare -n python3 $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -q -p no:cacheprovider tests/test_r7u_b_findings.py tests/test_r7u_c_findings.py > $O/load-$1.log 2>&1
done
