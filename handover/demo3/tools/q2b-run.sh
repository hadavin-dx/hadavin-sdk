#!/bin/bash
# usage: q2b-run.sh SEED...   (sequential, one core; campaigns a b c d per seed)
export TMPDIR=/home/user/work/q2b-tmp PYTHONPATH=src:.:tests
P=/home/user/work/final-venv/bin/python; T=/home/user/hadavin-sdk/handover/demo3/tools/q2b-fuzz.py
PROG=/home/user/hadavin-sdk/handover/demo3/evidence/raw/progress-Q2b.txt; L=/home/user/work/q2b-logs
stamp(){ echo "$(date -u '+%Y-%m-%d %H:%M:%SZ') UTC / $(TZ=Asia/Kolkata date '+%H:%M:%S') IST  $1" >> $PROG; }
cd /home/user/work/q2b-base
for seed in "$@"; do
  stamp "seed $seed START"
  for c in a b c d; do
    case $c in a) n=2400;; b) n=40000;; c) n=5000;; d) n=1200;; esac
    stamp "seed $seed campaign $c START n=$n"
    timeout 1500 $P -I $T --campaign $c --seed $seed --n $n --out $L/s$seed-$c.json > $L/s$seed-$c.log 2>&1; rc=$?
    stamp "seed $seed campaign $c END rc=$rc $(tail -c 250 $L/s$seed-$c.log | tr '\n' ' ')"
  done
  stamp "seed $seed END"
done
stamp "ALL DONE"
