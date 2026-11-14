#!/bin/bash
# lane3: restart after the container restart at ~13:15Z (jg3 interrupted). jg3, then run_c, then run_d, in order.
cd "$(dirname "$0")" || exit 1
python3 harness.py jg3 grep > /home/user/work/kill/last-run-e.out 2>&1
echo "$(date -u +%H:%M:%SZ) grep:jg3 (rerun after container restart) rc=$?" >> /home/user/work/kill/run_all.progress
./run_d.sh
./run_c.sh
