#!/bin/bash
O=/home/user/build/rr6/out/EV7T; cd $O
for i in $(seq 1 85); do   # bounded: at most 85 x 10 s
  n=$(pgrep -f "mut3.py|mutB.py|run-full|run-before" | wc -l)
  [ "$n" -eq 0 ] && break
  sleep 10
done
echo "quiet series start $(date -u) other_runners=$(pgrep -f 'mut3.py|mutB.py' | wc -l) load=$(cut -d' ' -f1-3 /proc/loadavg)" > $O/flake-quiet.start
./flake.sh flakeQ quiet
