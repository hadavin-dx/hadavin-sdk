#!/usr/bin/env bash
# usage: q4_burst.sh N RETRY(0/1) PASS RUN
N=$1; R=$2; P=$3; K=$4
L=/home/user/work/q4-logs
cd /home/user/work/q4-base
for t in $(seq 1 10); do a=$(cut -d' ' -f1 /proc/loadavg); awk "BEGIN{exit !($a>3.0)}" || break; sleep 30; done
noisy=""; awk "BEGIN{exit !($a>3.0)}" && noisy=NOISY
T=$(mktemp -d /tmp/q4tmp.XXXXXX)
echo "pass=$P run=$K N=$N retry=$R load_before=$(cat /proc/loadavg) $noisy start=$(date -u +%T)" > $L/burst-$N-r$R-p$P-$K.log
TMPDIR=$T PYTHONPATH=src:. LEAD_DESK_LOAD_N=$N LEAD_DESK_LOAD_RETRY=$R timeout 600 /home/user/work/final-venv/bin/python -m pytest tests/test_server_hardening.py -k measure_burst -s -p no:cacheprovider --basetemp=$T/bt >> $L/burst-$N-r$R-p$P-$K.log 2>&1
echo "rc=$? load_after=$(cat /proc/loadavg) end=$(date -u +%T)" >> $L/burst-$N-r$R-p$P-$K.log
rm -rf $T
