#!/bin/bash
# lane3 kill script, second batch: BURST, ERROR, GREP on the 11:05Z flows; then T14 (idle 120 s) on the FIXED flows (commit 8e2b6960).
# Starts only after run_all.sh has finished (one table, fixed ports).
cd "$(dirname "$0")" || exit 1
while pgrep -f run_all.sh > /dev/null; do sleep 5; done
for spec in burst:jb1 burst:jb2 burst:jb3 error:je1 error:je2 grep:jg1 grep:jg2 grep:jg3; do
  python3 harness.py "${spec#*:}" "${spec%%:*}" > /home/user/work/kill/last-run-b.out 2>&1
  echo "$(date -u +%H:%M:%SZ) ${spec} rc=$?" >> /home/user/work/kill/run_all.progress
done
for spec in t14:ft14a t14:ft14b t14:ft14c; do
  FLOW_PROBE=/home/user/work/kill/probe-fixed python3 harness.py "${spec#*:}" "${spec%%:*}" > /home/user/work/kill/last-run-b.out 2>&1
  echo "$(date -u +%H:%M:%SZ) ${spec} (fixed flows 8e2b6960) rc=$?" >> /home/user/work/kill/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) BATCH B DONE" >> /home/user/work/kill/run_all.progress
