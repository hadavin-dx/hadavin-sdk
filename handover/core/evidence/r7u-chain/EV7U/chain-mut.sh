#!/bin/bash
O=/home/user/build/rr6/out/EV7U; cd $O
for i in $(seq 1 120); do pgrep -f "mut_a.py" >/dev/null || break; sleep 10; done
: > mut-results-B.tsv; python3 mut_b.py mut-results-B.tsv > mutB.out 2>&1
: > mut-results-C.txt; python3 mut_c.py > mutC.out 2>&1
echo chain-done $(date -u) > chain-mut.done
