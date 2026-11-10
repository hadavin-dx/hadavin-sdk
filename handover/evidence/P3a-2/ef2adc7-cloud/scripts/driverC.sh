#!/bin/bash
D=/home/user/build/EV-P73-ef2adc7; E=/home/user/hadavin-sdk/handover/evidence/P3a-2/ef2adc7-cloud
H=/home/user/build/heavy.sh; C=$D/clean.sh
run() { name=$1; shift; : > $E/$name.log; echo "$(date -u +%FT%TZ) start $name" >> $E/_driver.log; $H $E/$name.log "$@"; rc=$?; echo "$(date -u +%FT%TZ) end $name rc=$rc" >> $E/_driver.log; }
run 05b-failbefore-base-py313-dsn $C $D/run5b.sh
run 02a-single-askdata-dblink-server-env-py313 env PGHOST=127.0.0.1 PGPORT=<port> $C $D/runpt.sh 3.13 1 "tests/demo_askdata/test_validate_harm.py"
echo "$(date -u +%FT%TZ) DRIVER-DONE-C" >> $E/_driver.log
