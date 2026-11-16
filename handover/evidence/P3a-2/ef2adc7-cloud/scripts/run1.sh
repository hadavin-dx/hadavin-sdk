#!/bin/bash
# step 1: lint, format, bandit (py3.13 venv)
cd /home/user/build/EV-P73-ef2adc7/wt; V=/home/user/build/EV-P73-ef2adc7/venv3.13/bin
echo "HEAD $(git rev-parse HEAD)"; echo "python $($V/python -V)"; $V/ruff --version; $V/bandit --version | head -1
rc=0
echo "== ruff check"; $V/ruff check src tests demos tools; r1=$?; echo "ruff_check_rc=$r1"
echo "== ruff format --check"; $V/ruff format --check src tests demos tools; r2=$?; echo "ruff_format_rc=$r2"
echo "== bandit"; $V/bandit -q -r src demos tools -ll; r3=$?; echo "bandit_rc=$r3"
exit $((r1|r2|r3))
