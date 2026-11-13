#!/usr/bin/env bash
# usage: q4_batch.sh PASS ; one load wait per batch (bounded 10 x 30 s), then NOWAIT runs; load is recorded in each log
P=$1; L=/home/user/work/q4-logs; T=/home/user/hadavin-sdk/handover/demo3/tools
for t in $(seq 1 10); do a=$(cut -d' ' -f1 /proc/loadavg); awk "BEGIN{exit !($a>3.0)}" || break; sleep 30; done
echo "batch pass=$P start $(date -u +%T) load=$(cat /proc/loadavg)" > $L/batch-p$P.log
export NOWAIT=1
for k in 1 2 3; do $T/q4_driver.sh burst:300 $P $k $((19100+P*100+k*10)) 4 100; done
for k in 1 2 3; do $T/q4_driver.sh rate:100:10 $P $k $((19100+P*100+k*10)) 2 50; done
for k in 1 2 3; do $T/q4_driver.sh dupmix:1000:0.3:200 $P $k $((19100+P*100+k*10)) 2 50; done
cd /home/user/work/q4-base; PYTHONPATH=src:. timeout 900 /home/user/work/final-venv/bin/python $T/q4_proto.py $((19100+P*100+80)) $P 3 > $L/proto-p$P.jsonl 2> $L/proto-p$P.err
echo "batch pass=$P end $(date -u +%T) load=$(cat /proc/loadavg)" >> $L/batch-p$P.log
