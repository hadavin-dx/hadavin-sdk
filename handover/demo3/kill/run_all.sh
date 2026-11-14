#!/bin/bash
# lane3 kill script: the whole sequence, one run at a time (fixed ports, one table). Results append to /home/user/work/kill/results.jsonl
cd "$(dirname "$0")" || exit 1
for spec in control2same:cs control2par:cp controlbad:cb \
  K1:k1a K1:k1b K1:k1c K2:k2a K2:k2b K2:k2c K3:k3a K3:k3b K3:k3c K6:k6a K6:k6b K6:k6c \
  Fa:fa1 Fb:fb1 Fc:fc1 control2par:cp2; do
  python3 harness.py "${spec#*:}" "${spec%%:*}" > /home/user/work/kill/last-run.out 2>&1
  echo "$(date -u +%H:%M:%SZ) ${spec} rc=$?" >> /home/user/work/kill/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) ALL DONE" >> /home/user/work/kill/run_all.progress
