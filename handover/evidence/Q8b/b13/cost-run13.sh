#!/bin/sh
# usage: cost-run13.sh ; writes /home/user/build/b13-notes/cost-b13.txt (3 runs per size, run alone in one heavy slot)
PY=/home/user/build/B-Q8b-b13/.venv/bin/python
out=/home/user/build/b13-notes/cost-b13.txt
: > $out
for tree in head:/home/user/build/B-Q8b-b13/src main:/home/user/build/b13-notes/main/src old:/home/user/build/b13-notes/wt-old/src; do
  name=${tree%%:*}; src=${tree#*:}
  for mode in hostile prose glued glued2; do
    echo "$name $mode $(PYTHONPATH=$src $PY /home/user/build/b13-notes/cost_clean13.py $src $mode 30000,60000,120000,262144 3 2>&1 | tail -1)" >> $out
  done
done
echo done >> $out
