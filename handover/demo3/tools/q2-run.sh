#!/bin/bash
# usage: q2-run.sh ROUND SEED_A SEED_B SEED_C   (sequential, one core)
R=$1; export TMPDIR=/home/user/work/q2-tmp PYTHONPATH=src:.:tests
P=/home/user/work/final-venv/bin/python; T=/home/user/hadavin-sdk/handover/demo3/tools/q2-fuzz.py
PROG=/home/user/hadavin-sdk/handover/demo3/evidence/raw/progress-Q2.txt; L=/home/user/work/q2-logs
stamp(){ echo "$(date -u '+%Y-%m-%d %H:%M:%SZ') UTC / $(TZ=Asia/Kolkata date '+%H:%M:%S') IST  $1" >> $PROG; }
cd /home/user/work/q2-base
i=0
for c in a b c; do
  i=$((i+1)); seed=${!i:-0}; eval seed=\${$((i+1))}
  stamp "round $R campaign $c START seed=$seed"
  timeout 2400 $P -I $T --campaign $c --seed $seed --out $L/r$R-$c.json > $L/r$R-$c.log 2>&1; rc=$?
  stamp "round $R campaign $c END rc=$rc $(tail -c 300 $L/r$R-$c.log | tr '\n' ' ')"
done
