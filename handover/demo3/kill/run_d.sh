#!/bin/bash
# lane3 kill script, fourth batch: ERROR (CRM refuses every call) on the FIXED flows (commit 8e2b6960), two runs. Starts after run_c.sh.
cd "$(dirname "$0")" || exit 1
while pgrep -f run_c.sh > /dev/null; do sleep 5; done
for spec in error:fe1 error:fe2; do
  FLOW_PROBE=/home/user/work/kill/probe-fixed python3 harness.py "${spec#*:}" "${spec%%:*}" > /home/user/work/kill/last-run-d.out 2>&1
  echo "$(date -u +%H:%M:%SZ) ${spec} (fixed flows 8e2b6960) rc=$?" >> /home/user/work/kill/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) BATCH D DONE" >> /home/user/work/kill/run_all.progress
