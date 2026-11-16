#!/bin/bash
# usage: flake.sh <copy> <tag>   30 sequential runs, one log per run, summary file
R=/home/user/build/rr6; O=$R/out/EV7T; T=$O/$1; TAG=$2
mkdir -p $O/tmp-$1; cd $T; : > $O/flake-$TAG.sum
for i in $(seq 1 30); do
  s=$(date -u +%T); l=$(cut -d' ' -f1 /proc/loadavg)
  env -i HOME=$O/tmp-$1 LANG=C.UTF-8 TMPDIR=$O/tmp-$1 PYTHONPATH=$T/src PYTHONDONTWRITEBYTECODE=1 PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 PATH=$R/bin:/usr/local/bin:/usr/bin:/bin \
    timeout -k 10 300 unshare -n python3 $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -q -p no:cacheprovider tests/test_r7s_findings.py -k "test_s3_a_created_contact and with-cleanup-f3-silent" > $O/flake-$TAG-$i.log 2>&1
  rc=$?
  echo "$i rc=$rc start=$s load1=$l $(tail -1 $O/flake-$TAG-$i.log)" >> $O/flake-$TAG.sum
done
echo done >> $O/flake-$TAG.sum
