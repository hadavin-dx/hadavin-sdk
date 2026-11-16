#!/bin/bash
# args: tree label. venv already synced (network only for the sync step); the test run itself is literal `env -i PATH HOME`.
T=$1; N=$2; L=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/f1/raw
cd $T
env -i PATH="$PATH" HOME="$HOME" env > $L/$N-envdump.txt
echo "CMD: env -i PATH=\$PATH HOME=\$HOME $T/.venv/bin/python -m pytest -q -p no:cacheprovider (cwd=$T)" > $L/$N-pytest.log
env -i PATH="$PATH" HOME="$HOME" timeout 2400 $T/.venv/bin/python -m pytest -q -p no:cacheprovider >> $L/$N-pytest.log 2>&1; rc=$?
echo "PYTEST_RC=$rc" >> $L/$N-pytest.log; echo done > $L/$N.done
