#!/usr/bin/env bash
T=/home/user/hadavin-sdk/handover/demo3/tools; L=/home/user/work/q4-logs
for t in $(seq 1 10); do a=$(cut -d' ' -f1 /proc/loadavg); awk "BEGIN{exit !($a>3.0)}" || break; sleep 30; done
export NOWAIT=1
for k in 1 2 3; do $T/q4_burst.sh 150 0 2 $k; $T/q4_burst.sh 300 0 2 $k; $T/q4_burst.sh 300 1 2 $k; done
cd /home/user/work/q4-base; PYTHONPATH=src:. timeout 300 /home/user/work/final-venv/bin/python $T/q4_classify.py 19780 2 3 150 256 300 400 > $L/classify-p2.jsonl 2>&1
cd /tmp; $T/q4_batch.sh 2 
echo "PASS2 DONE $(date -u +%T)" > $L/pass2.done
