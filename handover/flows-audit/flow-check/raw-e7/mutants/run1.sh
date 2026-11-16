#!/bin/bash
m=$1; d=/tmp/e7m/$m/flows-audit/flow-check
( cd $d && RUN_ALL_RAW=/tmp/e7m/$m/raw timeout 900 bash run_all.sh > /tmp/e7m/$m.out 2>&1; echo "RUN_ALL_RC=$?" >> /tmp/e7m/$m.out )
