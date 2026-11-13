#!/bin/bash
# test double: behaves as the venv python, except that the pytest run of the chunk holding tests/test_zz6_marker.py
# ends the way SHIM_MODE says (with exit code 0 unless the mode names a code)
REAL=/tmp/work/rv18-1/v/bin/python
if [[ -n "$SHIM_MODE" && "$*" == *"-m pytest"* && "$*" != *"--collect-only"* && "$*" == *"tests/test_zz6_marker.py"* ]]; then
  case "$SHIM_MODE" in
    rc1)  "$REAL" "$@"; exit 1;;
    rc2)  "$REAL" "$@"; exit 2;;
  esac
  "$REAL" "$@" > /dev/null 2>&1
  case "$SHIM_MODE" in
    noran)    echo "no tests ran in 0.01s";;
    empty)    echo "";;
    error1)   echo "1 error in 0.20s";;
    failed1)  echo "1 failed, 5 passed in 0.20s";;
    progress) printf '....s....  [ 40%%]\n';;
    exitmsg)  echo "!!!! _pytest.outcomes.Exit: stop !!!!";;
  esac
  exit 0
fi
exec "$REAL" "$@"
