#!/bin/bash
# lane3: parallel lanes (lead order). Usage: run_p.sh LANE "WAITPAT" spec... ; spec = flowver:CASE:label. Each lane has own ports, database, n8n folder (env LANE).
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill
LANE=$1; WAIT=$2; shift 2
[ -n "$WAIT" ] && while pgrep -f "$WAIT" >/dev/null; do sleep 5; done
for spec in "$@"; do
  v=${spec%%:*}; r=${spec#*:}; c=${r%%:*}; l=${r#*:}
  grep -q "\"label\": \"$l\"" $K/results.jsonl && continue
  if [ $v = 4 ]; then FC=7709d058-v4; FP=$K/probe-v4; else FC=6ebb7f62-v3; FP=$K/probe-v3; fi
  LANE=$LANE FLOW_COMMIT=$FC FLOW_PROBE=$FP python3 v3.py $l $c > $K/last-run-p$LANE.out 2>&1
  echo "$(date -u +%H:%M:%SZ) lane$LANE v$v $c:$l ($FC) rc=$?" >> $K/run_all.progress
done
echo "$(date -u +%H:%M:%SZ) QUEUE P lane$LANE DONE" >> $K/run_all.progress
