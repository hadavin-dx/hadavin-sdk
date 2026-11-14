#!/bin/bash
# usage: run.sh <stagedir> <log> files...
B=/home/user/build/rr6; S=$1; L=$2; shift 2; T=$(mktemp -d /home/user/build/rr6/out/R7V/tmpXXXX)
cd $S && env -i HOME=$T LANG=C.UTF-8 TMPDIR=$T PYTHONPATH=$S/src PYTHONDONTWRITEBYTECODE=1 PLAYWRIGHT_BROWSERS_PATH=$B/pw-browsers GITLEAKS_BIN=$B/bin/gitleaks DPLD_REQUIRE_SCAN=1 DPLD_REQUIRE_DEMO=1 PATH=$B/bin:/usr/local/bin:/usr/bin:/bin timeout -k 20 480 unshare -n python3 $B/src-v6/drivers/lo_up-q4g.py $B/venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs "$@" > $L 2>&1
echo rc=$? >> $L
