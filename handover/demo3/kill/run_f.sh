#!/bin/bash
# lane3: after batch D, GREP (jg) on the fixed flows, then the fault repeats (run_c).
cd "$(dirname "$0")" || exit 1
while ! grep -q "BATCH D DONE" /home/user/work/kill/run_all.progress; do sleep 5; done
C=$(cat /home/user/work/kill/fixed_commit.txt)
FLOW_COMMIT=$C FLOW_PROBE=/home/user/work/kill/probe-fixed-$C python3 harness.py fjg1 grep > /home/user/work/kill/last-run-f.out 2>&1
echo "$(date -u +%H:%M:%SZ) grep:fjg1 (fixed flows $C) rc=$?" >> /home/user/work/kill/run_all.progress
./run_c.sh
