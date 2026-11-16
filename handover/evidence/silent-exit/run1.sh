#!/bin/bash
cd /home/user/build/EV-A3
export PGHOST=127.0.0.1 PGPORT=55400 PGUSER=postgres HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55400/se_ev313 PYTHONFAULTHANDLER=1
unset HADAVIN_TEST_VAULT_ADDR
date -u +start=%T
nice -n 10 /home/user/build/venv-A3-313/bin/python -X faulthandler -m pytest -v -rA -m "not live and not perf" -p no:cacheprovider --junitxml=/home/user/hadavin-sdk/handover/evidence/silent-exit/run1.xml -o junit_logging=all tests/contracts/test_store_reserve.py
echo "pytest_rc=$?"; date -u +end=%T
