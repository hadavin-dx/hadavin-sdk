#!/bin/bash
# usage: run.sh <tree> <pytest args...>
R=/home/user/build/rr6; T=$1; shift; mkdir -p $R/out/R7U-A/tmp
cd $T
env -i HOME=$R/out/R7U-A/tmp LANG=C.UTF-8 TMPDIR=$R/out/R7U-A/tmp PYTHONPATH=$T/src PYTHONDONTWRITEBYTECODE=1 \
  PLAYWRIGHT_BROWSERS_PATH=$R/pw-browsers GITLEAKS_BIN=$R/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 \
  PATH=$R/bin:/usr/local/bin:/usr/bin:/bin \
  timeout -k 20 1500 unshare -n python3 $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs "$@"
