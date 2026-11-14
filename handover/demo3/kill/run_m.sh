#!/bin/bash
# lane3: reordered queue (lead order: B90 repeats first). Resumable.
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill
while pgrep -f "v3.py v3a2" >/dev/null; do sleep 5; done
for spec in B90:v3b90b B90:v3b90c A:v3a2 C:v3c2 B20:v3b20b A:v3a3; do
  l=${spec#*:}; grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  FLOW_COMMIT=6ebb7f62-v3 FLOW_PROBE=$K/probe-v3 python3 v3.py $l ${spec%%:*} > $K/last-run-l.out 2>&1
  echo "$(date -u +%H:%M:%SZ) v3 ${spec%%:*}:$l (v3 flows 6ebb7f62) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE M DONE" >> $K/run_all.progress
