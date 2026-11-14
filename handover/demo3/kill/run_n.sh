#!/bin/bash
# lane3: queue N (lead order: B90 repeats on v3, then v3 repeats on v4, then remaining v3 repeats). Resumable.
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill
while pgrep -f "v3.py v3b90b" >/dev/null; do sleep 5; done
for spec in 3:B90:v3b90c 4:B90:v4b90a 4:A:v4a1 4:C:v4c1 4:B90:v4b90b 3:C:v3c2 3:B20:v3b20b 3:A:v3a3 4:A:v4a2 4:C:v4c2; do
  v=${spec%%:*}; r=${spec#*:}; c=${r%%:*}; l=${r#*:}
  grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  if [ $v = 4 ]; then FC=7709d058-v4; FP=$K/probe-v4; else FC=6ebb7f62-v3; FP=$K/probe-v3; fi
  FLOW_COMMIT=$FC FLOW_PROBE=$FP python3 v3.py $l $c > $K/last-run-n.out 2>&1
  echo "$(date -u +%H:%M:%SZ) v$v $c:$l ($FC) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE N DONE" >> $K/run_all.progress
