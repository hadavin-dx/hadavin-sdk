#!/bin/bash
R=/home/user/build/rr6; O=$R/out/EV7U; T=$O/before
cd $T
for f in test_r7u_a_findings test_r7u_b_findings test_r7u_c_findings test_r7t_findings; do
env -i HOME=$O/tmp-before LANG=C.UTF-8 TMPDIR=$O/tmp-before PYTHONPATH=$T/src PYTHONDONTWRITEBYTECODE=1 \
  PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 \
  PATH=$R/bin:/usr/local/bin:/usr/bin:/bin \
  timeout -k 20 1800 unshare -n python3 $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfp tests/$f.py > $O/before-$f.log 2>&1
echo rc=$? >> $O/before-$f.log
done
