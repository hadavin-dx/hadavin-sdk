#!/bin/bash
R=/home/user/build/rr6; O=$R/out/EV7U; T=$O/hcopy
mkdir -p $O/tmp-probe; : > $O/probe-table.txt
cd $T
env -i HOME=$O/tmp-probe LANG=C.UTF-8 TMPDIR=$O/tmp-probe EV7U_OUT=$O/probe-table.txt PYTHONPATH=$T/src PYTHONDONTWRITEBYTECODE=1 \
  PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 \
  PATH=$R/bin:/usr/local/bin:/usr/bin:/bin \
  timeout -k 20 1800 unshare -n python3 $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -q -p no:cacheprovider tests/test_ev7u_probe.py > $O/probe-pytest.log 2>&1
echo rc=$? >> $O/probe-pytest.log
