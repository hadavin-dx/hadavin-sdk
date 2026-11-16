#!/bin/bash
R=/home/user/build/rr6; O=$R/out/EV7T; T=$O/htree
mkdir -p $O/tmp-full
echo "start $(date -u +%FT%TZ) load=$(cut -d' ' -f1-3 /proc/loadavg)" > $O/wrapper.log
cd $T
env -i HOME=$O/tmp-full LANG=C.UTF-8 TMPDIR=$O/tmp-full PYTHONPATH=$T/src PYTHONDONTWRITEBYTECODE=1 \
  PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 \
  PATH=$R/bin:/usr/local/bin:/usr/bin:/bin \
  timeout -k 20 3600 unshare -n python3 $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs tests/test_load_tools.py tests/test_r7k_findings.py tests > $O/pytest-full.log 2>&1
rc=$?
echo "end $(date -u +%FT%TZ) rc=$rc load=$(cut -d' ' -f1-3 /proc/loadavg)" >> $O/wrapper.log
