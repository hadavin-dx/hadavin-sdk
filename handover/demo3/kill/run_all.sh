#!/bin/bash
# lane3 kill script: the whole sequence, one run at a time (fixed ports, one table). Results append to /home/user/work/kill/results.jsonl
cd "$(dirname "$0")" || exit 1
for spec in \
  control1:j0 K1:j1a K1:j1b K1:j1c K2:j2a K2:j2b K2:j2c K3:j3a K3:j3b K3:j3c K6:j6a K6:j6b K6:j6c \
  Fa:jfa Fb:jfb Fc:jfc control2par:jcp2; do
  python3 harness.py "${spec#*:}" "${spec%%:*}" > /home/user/work/kill/last-run.out 2>&1
  echo "$(date -u +%H:%M:%SZ) ${spec} rc=$?" >> /home/user/work/kill/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) ALL DONE" >> /home/user/work/kill/run_all.progress
