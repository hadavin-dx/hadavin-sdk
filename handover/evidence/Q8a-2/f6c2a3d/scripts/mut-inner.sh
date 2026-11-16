#!/bin/bash
. /home/user/build/ev-q8a2f-scripts/env.sh
cd $W
s=$(date +%s); echo "slot-got $(date -u +%FT%TZ) load: $(cut -d' ' -f1-3 /proc/loadavg)" >> $R/mut-meta.txt
$E timeout 2400 uv run --all-extras --group test python tests/stage_mutants.py > $R/stage-mutants.log 2>&1
rc=$?; echo "end $(date -u +%FT%TZ) rc=$rc dur=$(( $(date +%s)-s ))s" >> $R/mut-meta.txt; exit $rc
