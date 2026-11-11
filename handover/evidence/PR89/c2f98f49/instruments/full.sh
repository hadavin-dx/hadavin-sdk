#!/bin/bash
. /home/user/build/ev-pr89r22-scripts/env.sh
cd $WT
echo "queued $(date -u +%FT%TZ)" > $RAW/full.times
$CLEAN /home/user/build/heavy.sh bash -c 'echo "start $(date -u +%FT%TZ)" >> '$RAW'/full.times; uv run --all-extras --group test pytest -q -p no:cacheprovider -m "not live and not perf" --junitxml='$RAW'/full.xml -rfEs > '$RAW'/full.log 2>&1; rc=$?; echo "pytest_rc=$rc" >> '$RAW'/full.times; echo "end $(date -u +%FT%TZ)" >> '$RAW'/full.times; exit $rc'
echo "heavy_rc=$?" >> $RAW/full.times
