#!/bin/bash
# lane3: GREP on the fixed flows WITH the four n8n environment settings from the demo's N8N-START.md (saving off, no save on progress). n = 3. Starts after run_g.sh.
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill
while ! grep -q "QUEUE G DONE" $K/run_all.progress; do sleep 5; done
C=$(cat $K/fixed_commit.txt)
for l in fjg2 fjg3 fjg4; do
  grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  EXECUTIONS_DATA_SAVE_ON_SUCCESS=none EXECUTIONS_DATA_SAVE_ON_ERROR=none EXECUTIONS_DATA_SAVE_ON_PROGRESS=false EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false \
  FLOW_COMMIT="$C + 4 n8n env settings" FLOW_PROBE=$K/probe-fixed-$C python3 harness.py $l grep > $K/last-run-h.out 2>&1
  echo "$(date -u +%H:%M:%SZ) grep:$l (fixed flows $C + 4 env settings) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE H DONE" >> $K/run_all.progress
