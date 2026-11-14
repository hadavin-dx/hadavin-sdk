#!/bin/bash
# lane3: kill points on the v4 flows via harness.py. Usage: run_q.sh LANE spec... ; spec = POINT:label
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill
LANE=$1; shift
for spec in "$@"; do
  p=${spec%%:*}; l=${spec#*:}
  grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  LANE=$LANE FLOW_COMMIT=7709d058-v4 FLOW_PROBE=$K/probe-v4 python3 harness.py $l $p > $K/last-run-q$LANE.out 2>&1
  echo "$(date -u +%H:%M:%SZ) lane$LANE v4 $p:$l (7709d058-v4) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE Q lane$LANE DONE" >> $K/run_all.progress
