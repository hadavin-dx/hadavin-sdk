#!/bin/bash
. /home/user/hadavin-sdk/handover/evidence/Q8a-2/3210f93/scripts/env.sh
RAW=/home/user/build/evidence-raw/Q8a2-r4
M=/home/user/build/EV-Q8a2-r4-main
cd $M; echo "main HEAD=$(git rev-parse HEAD) dirty-before=$(git status --porcelain | wc -l)" > $RAW/step5c-meta.txt
for f in tests/contracts/test_capabilities.py tests/test_lockin_guard.py tests/test_p7_tick.py tests/test_q8a2_callback.py; do git -C $W show HEAD:$f > $f; done
for t in tests/test_q8a2_callback.py tests/test_lockin_guard.py tests/contracts/test_capabilities.py tests/test_p7_tick.py; do
  n=$(basename $t .py)
  PYTHONPATH=$M/src $E $PY -m pytest -q -p no:cacheprovider --junitxml=$RAW/step5c-$n-junit.xml -rfE $t > $RAW/step5c-$n.log 2>&1; echo "$t rc=$? $(tail -n 1 $RAW/step5c-$n.log)" >> $RAW/step5c-meta.txt
done
PYTHONPATH=$M/src $E $PY -m pytest -q -p no:cacheprovider --continue-on-collection-errors --junitxml=$RAW/step5c-all4-junit.xml -rfE tests/test_q8a2_callback.py tests/test_lockin_guard.py tests/contracts/test_capabilities.py tests/test_p7_tick.py > $RAW/step5c-all4.log 2>&1; echo "all4 --continue-on-collection-errors rc=$? $(tail -n 1 $RAW/step5c-all4.log)" >> $RAW/step5c-meta.txt
git checkout -- . ; git clean -fdq tests; echo "restored dirty-after=$(git status --porcelain | wc -l)" >> $RAW/step5c-meta.txt
