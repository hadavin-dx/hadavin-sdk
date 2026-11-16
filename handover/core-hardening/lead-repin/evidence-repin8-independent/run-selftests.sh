#!/bin/sh
E=/home/user/hadavin-sdk/handover/core-hardening/lead-repin/evidence-repin8-independent
S=/home/user/hadavin-sdk/handover/core-hardening/heavy-slot.sh
n=0; while pgrep -f run-plants-serial >/dev/null && [ $n -lt 150 ]; do sleep 10; n=$((n+1)); done
for sh in dash bash; do
 echo "start $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg)" > $E/02-selftest-$sh-root.txt
 sh $S env TMPDIR=/tmp/hd8i/sig $sh /tmp/hd8i/v8.sh --self-test >> $E/02-selftest-$sh-root.txt 2>&1; echo "exit=$? end $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg)" >> $E/02-selftest-$sh-root.txt
 echo "start $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg)" > $E/03-selftest-$sh-uid65534.txt
 sh $S setpriv --reuid=65534 --regid=65534 --clear-groups env HOME=/tmp/hd8i/nr TMPDIR=/tmp/hd8i/nr $sh /tmp/hd8i/v8.sh --self-test >> $E/03-selftest-$sh-uid65534.txt 2>&1; echo "exit=$? end $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg)" >> $E/03-selftest-$sh-uid65534.txt
done
