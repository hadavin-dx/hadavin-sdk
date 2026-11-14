#!/bin/bash
# lane3: resumable queue (the sandbox restarted at 13:15Z and 13:40Z and killed the earlier queues).
# Skips every label already in results.jsonl; starts Postgres if it is down. Order: fixed flows first, then fixed-flow GREP, then fault repeats on the 11:05Z flows.
cd "$(dirname "$0")" || exit 1
K=/home/user/work/kill; B=/usr/lib/postgresql/16/bin
$B/pg_isready -h 127.0.0.1 -p 55432 >/dev/null 2>&1 || { rm -f $K/pg/postmaster.pid; setpriv --reuid=65534 --regid=65534 --clear-groups $B/pg_ctl -D $K/pg -l $K/pg.log -o "-p 55432 -c listen_addresses=127.0.0.1 -c unix_socket_directories=/tmp" start >/dev/null 2>&1; sleep 4; }
C=$(cat $K/fixed_commit.txt)
done_label() { grep -q "\"label\": \"$1\"" $K/results.jsonl; }
run() { # label point mode(fixed|old)
  done_label "$1" && return
  if [ "$3" = fixed ]; then FLOW_COMMIT=$C FLOW_PROBE=$K/probe-fixed-$C python3 harness.py "$1" "$2" > $K/last-run-g.out 2>&1
  else python3 harness.py "$1" "$2" > $K/last-run-g.out 2>&1; fi
  echo "$(date -u +%H:%M:%SZ) $2:$1 ($3 flows) rc=$?" >> $K/run_all.progress
}
for spec in error:ferr2 error:ferr3 t14:ft14n burst:fb1 K3:fk3a K6:fk6a K3:fk3b K6:fk6b K3:fk3c K6:fk6c grep:fjg1; do run "${spec#*:}" "${spec%%:*}" fixed; done
for spec in Fa:jfa2 Fb:jfb2 Fc:jfc2 Fa:jfa3 Fb:jfb3 Fc:jfc3; do run "${spec#*:}" "${spec%%:*}" old; done
echo "$(date -u +%H:%M:%SZ) QUEUE G DONE" >> $K/run_all.progress
