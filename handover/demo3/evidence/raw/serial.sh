#!/bin/bash
export TMPDIR=/home/user/work/q1-tmp-serial; cd /home/user/work/q1-base
P=/home/user/hadavin-sdk/handover/demo3/evidence/raw/progress-Q1.txt
echo "SERIAL START $(date -u +%FT%TZ) / IST $(TZ=Asia/Kolkata date +%T) load $(cat /proc/loadavg)" >> $P
s=$(date +%s)
timeout 2400 /home/user/work/final-venv/bin/python -m pytest -v -rs -p no:cacheprovider -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt > /home/user/work/q1-logs/serial.log 2>&1
rc=$?
echo "$rc $(( $(date +%s)-s ))" > /home/user/work/q1-logs/serial.rc
echo "SERIAL END rc=$rc $(date -u +%FT%TZ) / IST $(TZ=Asia/Kolkata date +%T) load $(cat /proc/loadavg)" >> $P
