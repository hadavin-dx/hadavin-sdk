#!/bin/bash
# $1 = run label (1 or 2), $2 = tmp dir
L=$1; export TMPDIR=/home/user/work/q1-tmp-xdist$L; mkdir -p $TMPDIR; cd /home/user/work/q1-base
P=/home/user/hadavin-sdk/handover/demo3/evidence/raw/progress-Q1.txt
Q4=/home/user/hadavin-sdk/handover/demo3/evidence/raw/progress-Q4.txt
deadline=$(( $(date -d 12:32:00Z +%s) + 2400 ))
if [ "$L" = 1 ]; then
 while true; do
  [ -f /home/user/work/q1-logs/serial.rc ] && { grep -qw END $Q4 2>/dev/null && { echo "XDIST1 wait ended: Q4 END seen $(date -u +%T)Z" >> $P; break; }; [ $(date +%s) -ge $deadline ] && { echo "XDIST1 wait ended: 40-min cap reached without Q4 END; running anyway $(date -u +%T)Z" >> $P; break; }; }
  sleep 20
 done
fi
echo "XDIST$L START $(date -u +%FT%TZ) / IST $(TZ=Asia/Kolkata date +%T) load $(cat /proc/loadavg)" >> $P
s=$(date +%s)
timeout 2400 /home/user/work/q1-xdist-venv/bin/python -m pytest -v -rs -p no:cacheprovider -p xdist -n 3 -o faulthandler_timeout=120 --basetemp=$TMPDIR/bt > /home/user/work/q1-logs/xdist$L.log 2>&1
rc=$?
echo "$rc $(( $(date +%s)-s ))" > /home/user/work/q1-logs/xdist$L.rc
echo "XDIST$L END rc=$rc $(date -u +%FT%TZ) / IST $(TZ=Asia/Kolkata date +%T) load $(cat /proc/loadavg)" >> $P
