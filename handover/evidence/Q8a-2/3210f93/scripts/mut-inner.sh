#!/bin/bash
. /home/user/hadavin-sdk/handover/evidence/Q8a-2/3210f93/scripts/env.sh
cd $W
s=$(date +%s); echo "slot-got $(date -u +%FT%TZ) load: $(cut -d' ' -f1-3 /proc/loadavg)" >> /home/user/build/evidence-raw/Q8a2-r4/mut-meta.txt
$E timeout 2400 uv run --all-extras --group test python tests/stage_mutants.py > /home/user/build/evidence-raw/Q8a2-r4/stage-mutants.log 2>&1
rc=$?; echo "end $(date -u +%FT%TZ) rc=$rc dur=$(( $(date +%s)-s ))s" >> /home/user/build/evidence-raw/Q8a2-r4/mut-meta.txt; exit $rc
