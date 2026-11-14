#!/bin/bash
# lane3: fault modes F-a, F-b, F-c, n = 3 each, on the FIXED flows (demo commit in fixed_commit.txt). Resumable.
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill; C=$(cat $K/fixed_commit.txt)
for spec in Fa:ffa1 Fb:ffb1 Fc:ffc1 Fa:ffa2 Fb:ffb2 Fc:ffc2 Fa:ffa3 Fb:ffb3 Fc:ffc3; do
  l=${spec#*:}; grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  FLOW_COMMIT=$C FLOW_PROBE=$K/probe-fixed-$C python3 harness.py $l ${spec%%:*} > $K/last-run-j.out 2>&1
  echo "$(date -u +%H:%M:%SZ) ${spec%%:*}:$l (fixed flows $C) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE J DONE" >> $K/run_all.progress
