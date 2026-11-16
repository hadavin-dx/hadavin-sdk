#!/bin/bash
. /home/user/hadavin-sdk/handover/evidence/Q8a-2/3210f93/scripts/env.sh
cd $W
s=$(date +%s); echo "slot-got $(date -u +%FT%TZ) load: $(cut -d' ' -f1-3 /proc/loadavg)" >> $R/full-meta.txt
$E timeout 2400 uv run --all-extras --group test pytest -q -p no:cacheprovider -m "not live and not perf" --junitxml=$R/full-junit.xml -rfEs > $R/full.log 2>&1
rc=$?; echo "end $(date -u +%FT%TZ) rc=$rc dur=$(( $(date +%s)-s ))s" >> $R/full-meta.txt; exit $rc
