#!/bin/bash
# usage: runfull.sh <tree> <rawdir>
T=$1; L=$2; G=src/hadavin_sdk/approvals/gate.py
cd "$T" || exit 9
LOG=$L/full-run.log
{ echo "START $(date -u +%FT%TZ)"; echo "gate.py sha256 BEFORE: $(sha256sum $G)"; echo "tests/test_g4 sha256 BEFORE: $(sha256sum tests/test_g4_ids_not_withheld.py)"; } > $LOG
env -i PATH="$PATH" HOME="$HOME" env > $L/full-run-envdump.txt
echo "CMD: env -i PATH=\$PATH HOME=\$HOME uv run --all-extras --group test pytest -q -p no:cacheprovider" >> $LOG
echo "PYTEST_START $(date -u +%FT%TZ)" >> $LOG
env -i PATH="$PATH" HOME="$HOME" timeout 1500 uv run --all-extras --group test pytest -q -p no:cacheprovider >> $LOG 2>&1; rc=$?
echo "PYTEST_RC=$rc" >> $LOG; echo "PYTEST_END $(date -u +%FT%TZ)" >> $LOG
echo "gate.py sha256 AFTER: $(sha256sum $G)" >> $LOG
echo "tests/test_g4 sha256 AFTER: $(sha256sum tests/test_g4_ids_not_withheld.py)" >> $LOG
cd "$T" && git status --porcelain | wc -l | sed 's/^/git status lines after: /' >> $LOG
echo done > $L/full-run.done
