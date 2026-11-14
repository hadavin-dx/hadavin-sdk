#!/bin/bash
# lane3: my own v3 alert-loss cases (PLAN-V3-ALERT.md) on the demo's v3 flows (commit 6ebb7f62, folder n8n-flows-v3). Resumable. Starts after run_k.
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill
while ! grep -q "QUEUE K DONE" $K/run_all.progress; do sleep 5; done
for spec in A:v3a1 B20:v3b20a C:v3c1 B90:v3b90a A:v3a2 C:v3c2 B20:v3b20b B90:v3b90b A:v3a3; do
  l=${spec#*:}; grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  FLOW_COMMIT=6ebb7f62-v3 FLOW_PROBE=$K/probe-v3 python3 v3.py $l ${spec%%:*} > $K/last-run-l.out 2>&1
  echo "$(date -u +%H:%M:%SZ) v3 ${spec%%:*}:$l (v3 flows 6ebb7f62) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE L DONE" >> $K/run_all.progress
