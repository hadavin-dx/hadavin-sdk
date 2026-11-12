#!/bin/bash
# hadavin-sdk, Linux, no docker. Usage (from an EMPTY work folder):  bash run-sdk-linux.sh serial|par|broken|posix  RUN_NUMBER [WORKERS=3]
# Needs: uv, python3.12, git, pypi + github reachable. ~800 s serial on the laptop; budget 20 minutes slack per window.
set -u
MODE=${1:?serial|par|broken|posix}; RUN=${2:?run number}; NW=${3:-3}
HERE=$(cd "$(dirname "$0")" && pwd); W=$PWD; O=$W/out/sdk-$MODE$RUN; mkdir -p "$O"
if [ ! -d "$W/sdk" ]; then
  git clone -q https://github.com/hadavin-dx/hadavin-sdk "$W/sdk" || exit 2   # main at the head the lead names; record it in the ledger
  cd "$W/sdk" && uv sync --locked --no-build --all-extras --group test > "$W/out/uv.txt" 2>&1 || exit 2
  uv pip install --require-hashes --no-deps -r "$HERE/xdist-overlay-hashes.txt" >> "$W/out/uv.txt" 2>&1 || exit 2   # execnet 2.1.2, pytest-xdist 3.8.0; no repo file changes
fi
cd "$W/sdk"; PY=.venv/bin/python
bash "$HERE/quiet-check.sh" "$O/quiet-before.txt" || exit 3
git rev-parse HEAD > "$O/head.txt"; $PY --version > "$O/versions.txt"; nproc >> "$O/versions.txt"
export PYTHONHASHSEED=0 PYTHONPATH=src   # PYTHONPATH=src is what fixed the earlier ModuleNotFoundError: hadavin_sdk
S=$(date +%s)
case $MODE in
 serial) /usr/bin/time -v -o "$O/time.txt" $PY -m pytest -q -m 'not live and not perf' -rA -p no:cacheprovider --junitxml="$O/junit.xml" > "$O/pytest.txt" 2>&1;;
 par)    /usr/bin/time -v -o "$O/time.txt" $PY -m pytest -q -m 'not live and not perf' -rA -p no:cacheprovider -n $NW --dist loadgroup --junitxml="$O/junit.xml" > "$O/pytest.txt" 2>&1;;
 broken) cp tests/test_mutation_runner.py tests/test_zz_broken_copy.py; printf '\n\ndef test_deliberate_failure_control():\n    assert 1 == 2\n' >> tests/test_zz_broken_copy.py
         $PY -m pytest -q -m 'not live and not perf' -rA -p no:cacheprovider -n $NW --dist loadgroup --junitxml="$O/junit.xml" > "$O/pytest.txt" 2>&1; rm -f tests/test_zz_broken_copy.py;;
 posix)  for m in serial par; do N=""; [ $m = par ] && N="-n $NW --dist loadgroup"
           $PY -m pytest -q -p no:cacheprovider -rA $N --junitxml="$O/posix-$m.xml" tests/test_mutation_runner.py > "$O/posix-$m.txt" 2>&1; done;;
esac
echo "exit=$? secs=$(( $(date +%s)-S ))" | tee "$O/result.txt"; tail -1 "$O/pytest.txt" 2>/dev/null >> "$O/result.txt"
