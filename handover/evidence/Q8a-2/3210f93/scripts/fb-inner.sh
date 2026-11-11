#!/bin/bash
. /home/user/hadavin-sdk/handover/evidence/Q8a-2/3210f93/scripts/env.sh
M=/home/user/build/EV-Q8a2-r4-main
cd $M; echo "main HEAD=$(git rev-parse HEAD) dirty-before=$(git status --porcelain | wc -l)" > $R/step5-meta.txt
for f in tests/contracts/test_capabilities.py tests/test_lockin_guard.py tests/test_p7_tick.py tests/test_q8a2_callback.py; do mkdir -p $(dirname $f); git -C $W show HEAD:$f > $f; done
git status --porcelain >> $R/step5-meta.txt
PYTHONPATH=$M/src $E $PY -c "import hadavin_sdk;print('imported',hadavin_sdk.__file__)" >> $R/step5-meta.txt
# run A: all 4 files
PYTHONPATH=$M/src $E $PY -m pytest -q -p no:cacheprovider --junitxml=$R/step5-main-A-junit.xml -rfE tests/test_q8a2_callback.py tests/test_lockin_guard.py tests/contracts/test_capabilities.py tests/test_p7_tick.py > $R/step5-main-A-4files-pytest.log 2>&1; echo "run A rc=$? $(tail -n 1 $R/step5-main-A-4files-pytest.log)" >> $R/step5-meta.txt
# run B: 3 files
PYTHONPATH=$M/src $E $PY -m pytest -q -p no:cacheprovider --junitxml=$R/step5-main-junit.xml -rfE tests/test_q8a2_callback.py tests/test_lockin_guard.py tests/contracts/test_capabilities.py > $R/step5-main-B-3files-pytest.log 2>&1; echo "run B rc=$? $(tail -n 1 $R/step5-main-B-3files-pytest.log)" >> $R/step5-meta.txt
git checkout -- . ; git clean -fdq tests; echo "restored dirty-after=$(git status --porcelain | wc -l)" >> $R/step5-meta.txt
