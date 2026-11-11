#!/bin/bash
. /home/user/hadavin-sdk/handover/evidence/Q8a-2/3210f93/scripts/env.sh
RAW=/home/user/build/evidence-raw/Q8a2-r4
cd $W
s=$(date +%s); echo "full2 slot-got $(date -u +%FT%TZ) load: $(cut -d' ' -f1-3 /proc/loadavg)" >> $RAW/full2-meta.txt
$E timeout 2400 uv run --all-extras --group test pytest -q -p no:cacheprovider -m "not live and not perf" --junitxml=$RAW/full2-junit.xml -rfEs > $RAW/full2.log 2>&1
rc=$?; echo "full2 end $(date -u +%FT%TZ) rc=$rc dur=$(( $(date +%s)-s ))s head=$(git rev-parse HEAD) dirty=$(git status --porcelain|wc -l)" >> $RAW/full2-meta.txt; exit $rc
