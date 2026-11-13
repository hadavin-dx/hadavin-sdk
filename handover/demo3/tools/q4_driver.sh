#!/usr/bin/env bash
# usage: q4_driver.sh SCENARIO PASS RUN PORTBASE [WORKERS THREADS]   e.g. burst:300 1 1 19500 4 100
SC=$1; P=$2; K=$3; PB=$4; W=${5:-2}; TH=${6:-50}
L=/home/user/work/q4-logs; Q=/home/user/work/q4-base
tag=$(echo $SC | tr ':' '_')-p$P-$K
[ -z "$NOWAIT" ] && for t in $(seq 1 10); do a=$(cut -d' ' -f1 /proc/loadavg); awk "BEGIN{exit !($a>3.0)}" || break; sleep 30; done
a=$(cut -d" " -f1 /proc/loadavg); noisy=""; awk "BEGIN{exit !($a>3.0)}" && noisy=NOISY
T=$(mktemp -d /tmp/q4drv.XXXXXX); cd $Q
export PYTHONPATH=src:. TMPDIR=$T DESK_DB_PATH=$T/desk.db DESK_PORT=$PB DESK_FAKES_PORT=$((PB+1)) PY=/home/user/work/final-venv/bin/python
echo "scenario=$SC pass=$P run=$K workers=$W threads=$TH load_before=$(cat /proc/loadavg) $noisy" > $L/drv-$tag.log
$PY -m demo_only.fakes_server --outbox keyed --port $((PB+1)) > $T/fakes.log 2>&1 & FP=$!
$PY -m lead_desk.server > $T/desk.log 2>&1 & DP=$!
for i in 1 2 3 4 5 6 7 8 9 10; do curl -sf http://127.0.0.1:$PB/counts >/dev/null && break; sleep 1; done
t0=$(date +%s.%N)
timeout 300 $PY -m load_tools.load_driver --base-url http://127.0.0.1:$PB --scenario $SC --log $T/req.jsonl --workers $W --threads $TH --id-prefix r$P$K >> $L/drv-$tag.log 2>&1; echo "driver rc=$?" >> $L/drv-$tag.log
t1=$(date +%s.%N)
# poll drain: bounded 150 x 1s
for i in $(seq 1 150); do c=$(curl -s http://127.0.0.1:$PB/counts); echo "$c" | $PY -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d["pending_followups"]==0 and d["sending_followups"]==0 else 1)' && break; sleep 1; done
t2=$(date +%s.%N)
echo "driver_seconds=$(echo "$t1 - $t0" | bc) drain_after_driver_end_seconds=$(echo "$t2 - $t1" | bc) loops=$i" >> $L/drv-$tag.log
echo "COUNTS $(curl -s http://127.0.0.1:$PB/counts)" >> $L/drv-$tag.log
curl -s http://127.0.0.1:$((PB+1))/fake/outbox | $PY -c 'import sys,json; print("OUTBOX_COUNT",json.load(sys.stdin)["count"])' >> $L/drv-$tag.log
$PY - $T/req.jsonl >> $L/drv-$tag.log <<'PYEOF'
import sys,json,collections
rows=[json.loads(l) for l in open(sys.argv[1])]
c=collections.Counter(); tries=0; sawb=0; endb=0; acc=0; lag=[]
for r in rows:
    codes=r.get("codes",[]); tries+=len(codes); c.update(map(str,codes))
    if 503 in codes: sawb+=1
    if r.get("final_status")==503: endb+=1
    acc+= bool(r.get("accepted",True)); lag.append(r.get("lag_s",0))
print("REQS",len(rows),"TRIES",tries,"CODES",dict(c),"saw503",sawb,"end503",endb,"accepted",acc,"maxlag",round(max(lag),2))
PYEOF
kill $DP $FP 2>/dev/null; wait $DP $FP 2>/dev/null
echo "end load_after=$(cat /proc/loadavg)" >> $L/drv-$tag.log
cp $T/desk.log $L/drv-$tag.desk.log 2>/dev/null; rm -rf $T
