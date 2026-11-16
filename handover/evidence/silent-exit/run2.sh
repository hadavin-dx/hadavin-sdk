#!/bin/bash
cd /home/user/build/EV-A3
export PGHOST=127.0.0.1 PGPORT=55400 PGUSER=postgres HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:55400/se_ev313
unset HADAVIN_TEST_VAULT_ADDR
date -u +start=%T
nice -n 10 /home/user/build/venv-A3-313/bin/python -m pytest -v -m "not live and not perf" -p no:cacheprovider "tests/contracts/test_store_reserve.py::test_b5_ten_thousand_reserve_settle_pairs_equal_the_exact_decimal_sum"
echo "pytest_rc=$?"; date -u +end=%T
