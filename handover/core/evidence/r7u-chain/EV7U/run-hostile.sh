#!/bin/bash
R=/home/user/build/rr6; O=$R/out/EV7U
env -i HOME=$O/tmp-host LANG=C.UTF-8 TMPDIR=$O/tmp-host PYTHONDONTWRITEBYTECODE=1 PATH=$R/bin:/usr/local/bin:/usr/bin:/bin timeout 300 unshare -n python3 $R/src-v6/drivers/lo_up-q4g.py $R/venv-br/bin/python -I $O/hostile_a.py > $O/hostile-a.txt 2>&1
echo rc=$? >> $O/hostile-a.txt
