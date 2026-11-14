#!/bin/bash
# lane3: F-c variant Fc1 (SMTP greeting held 40 s for the FIRST connection only, so the alert connection works). n = 3 on the fixed flows, n = 3 on the 11:05Z flows. After run_j.
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill; C=$(cat $K/fixed_commit.txt)
while ! grep -q "QUEUE J DONE" $K/run_all.progress; do sleep 5; done
for l in fc1a fc1b fc1c; do
  grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  FLOW_COMMIT=$C FLOW_PROBE=$K/probe-fixed-$C python3 harness.py $l Fc1 > $K/last-run-k.out 2>&1
  echo "$(date -u +%H:%M:%SZ) Fc1:$l (fixed flows $C) rc=$?" >> $K/run_all.progress
done
for l in jfc1a jfc1b jfc1c; do
  grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  python3 harness.py $l Fc1 > $K/last-run-k.out 2>&1
  echo "$(date -u +%H:%M:%SZ) Fc1:$l (old flows) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE K DONE" >> $K/run_all.progress
