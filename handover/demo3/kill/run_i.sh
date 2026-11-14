#!/bin/bash
# lane3: GREP with the four settings PLUS EXECUTIONS_DATA_PRUNE=false (n8n then hard-deletes a not-saved run instead of marking it deleted). n = 3.
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill; C=$(cat $K/fixed_commit.txt)
for l in fjg5 fjg6 fjg7; do
  grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  EXECUTIONS_DATA_PRUNE=false EXECUTIONS_DATA_SAVE_ON_SUCCESS=none EXECUTIONS_DATA_SAVE_ON_ERROR=none EXECUTIONS_DATA_SAVE_ON_PROGRESS=false EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false \
  FLOW_COMMIT="$C + 4 env settings + PRUNE=false" FLOW_PROBE=$K/probe-fixed-$C python3 harness.py $l grep > $K/last-run-i.out 2>&1
  echo "$(date -u +%H:%M:%SZ) grep:$l (fixed flows $C + 4 env settings + PRUNE=false) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE I DONE" >> $K/run_all.progress
