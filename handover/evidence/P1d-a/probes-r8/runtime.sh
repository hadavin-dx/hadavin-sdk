#!/bin/bash
# usage: runtime.sh TREE  -> one line per input x size x entry, each its own process (timeout 120 s)
T=$1
for name in H1 H6 H10 "[" ">" bt1 bt3 bt2 "ph." "[.]" "&amp;" dom nl; do for n in 65536 262144; do for w in clean blocks; do
 PYTHONPATH=$T/src timeout 120 /home/user/hadavin-sdk/.venv/bin/python p10_t1.py "$name" $n $w || echo "$name $n $w TIMEOUT>120"; done; done; done
