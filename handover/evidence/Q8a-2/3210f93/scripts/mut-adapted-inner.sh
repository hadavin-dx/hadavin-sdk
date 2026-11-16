#!/bin/bash
. /home/user/hadavin-sdk/handover/evidence/Q8a-2/3210f93/scripts/env.sh
cd /home/user/build/EV-Q8a2-r4-mut
echo "slot-got $(date -u +%FT%TZ)" >> $R/mut-meta.txt
$E timeout 1500 python3 $R/scripts/builder-mut-adapted.py > $R/step4b-builder-mut-adapted.txt 2>&1; rc=$?
echo "mut-adapted end $(date -u +%FT%TZ) rc=$rc; src dirty=$(git status --porcelain | wc -l)" >> $R/mut-meta.txt
