#!/bin/bash
# lane3 kill script, third batch: two more runs of each fault mode (sample size 3 each) on the 11:05Z flows. Starts after run_b.sh.
cd "$(dirname "$0")" || exit 1
while pgrep -f run_b.sh > /dev/null; do sleep 5; done
for spec in Fa:jfa2 Fb:jfb2 Fc:jfc2 Fa:jfa3 Fb:jfb3 Fc:jfc3; do
  python3 harness.py "${spec#*:}" "${spec%%:*}" > /home/user/work/kill/last-run-c.out 2>&1
  echo "$(date -u +%H:%M:%SZ) ${spec} rc=$?" >> /home/user/work/kill/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) BATCH C DONE" >> /home/user/work/kill/run_all.progress
