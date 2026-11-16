#!/bin/bash
cd /home/user/build/B-P6a
E=/home/user/build/evid-out/P6a-r3; H=/home/user/build/heavy.sh
CL="env -i PATH=$PATH HOME=$HOME LANG=C.UTF-8"
echo "$ python tools/client_profile_mutants.py" > $E/mutants.txt
$H $E/mutants.txt $CL /home/user/build/B-P6a/.venv/bin/python tools/client_profile_mutants.py &
echo "$ python tests/stage_mutants.py" > $E/stage-mutants.txt
$H $E/stage-mutants.txt $CL /home/user/build/B-P6a/.venv/bin/python tests/stage_mutants.py &
echo "$ pytest -q -m 'not live and not perf' 3.13 (pg 5481)" > $E/full-313.txt
$H $E/full-313.txt $CL HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:5481/postgres HADAVIN_REQUIRE_PINNED_UNIDATA=1 /home/user/build/B-P6a/.venv/bin/python -X faulthandler -m pytest -q -rfE --tb=short -p no:cacheprovider -m "not live and not perf" --junitxml=$E/full-313.xml &
echo "$ pytest -q -m 'not live and not perf' 3.12 (pg 5482)" > $E/full-312.txt
$H $E/full-312.txt $CL HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:5482/postgres /home/user/build/venv-r3-312/bin/python -X faulthandler -m pytest -q -rfE --tb=short -p no:cacheprovider -m "not live and not perf" --junitxml=$E/full-312.xml &
wait
echo ALLDONE > $E/done.txt
