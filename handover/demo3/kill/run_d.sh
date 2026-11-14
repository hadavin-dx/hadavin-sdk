#!/bin/bash
# lane3 kill script, fourth batch: the FIXED flows (newest flows on origin/demo/handover when this batch starts; commit recorded).
# ERROR x3, BURST x1, K3 x3, K6 x3. Starts after run_c.sh. Reads the flow files only (git show), nothing else from the demo branch.
cd "$(dirname "$0")" || exit 1
true
REPO=/home/user/hadavin-sdk
git -C "$REPO" fetch -q origin demo/handover
C=$(git -C "$REPO" log -1 --format=%h origin/demo/handover -- handover/demo/n8n-flows)
SRC=/home/user/work/demo-fixed-$C
mkdir -p "$SRC"
for n in mf-sub-crm-mail mf-form mf-hook mf-recovery; do git -C "$REPO" show origin/demo/handover:handover/demo/n8n-flows/$n.json > "$SRC/$n.json"; done
python3 prepare_probe.py "$SRC" /home/user/work/kill/probe-fixed-$C > /home/user/work/kill/prepare-fixed-$C.out 2>&1
echo "$C" > /home/user/work/kill/fixed_commit.txt
echo "$(date -u +%H:%M:%SZ) BATCH D uses fixed flows commit $C" >> /home/user/work/kill/run_all.progress
for spec in error:ferr1 error:ferr2 error:ferr3 t14:ft14n burst:fb1 K3:fk3a K6:fk6a K3:fk3b K6:fk6b K3:fk3c K6:fk6c; do
  FLOW_COMMIT=$C FLOW_PROBE=/home/user/work/kill/probe-fixed-$C python3 harness.py "${spec#*:}" "${spec%%:*}" > /home/user/work/kill/last-run-d.out 2>&1
  echo "$(date -u +%H:%M:%SZ) ${spec} (fixed flows $C) rc=$?" >> /home/user/work/kill/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) BATCH D DONE" >> /home/user/work/kill/run_all.progress
