#!/bin/bash
# usage: runpt.sh PYVER DSN(0|1) [extra pytest args...]   (cwd wt)
v=$1; dsn=$2; shift 2
cd /home/user/build/EV-P73-ef2adc7/wt; V=/home/user/build/EV-P73-ef2adc7/venv$v/bin
echo "HEAD $(git rev-parse HEAD)"; echo "python $($V/python -V)"; psql -h 127.0.0.1 -p <port> -U postgres -tAc "select version()"
[ "$dsn" = 1 ] && export HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:<port>/postgres || unset HADAVIN_TEST_PG_DSN
[ "$v" = 3.13 ] && export HADAVIN_REQUIRE_PINNED_UNIDATA=1
echo "DSN set: $([ -n "$HADAVIN_TEST_PG_DSN" ] && echo yes || echo no); UNIDATA pin required: ${HADAVIN_REQUIRE_PINNED_UNIDATA:-unset}"
exec $V/python -m pytest -v -m "not live and not perf" -rfEs "$@"
