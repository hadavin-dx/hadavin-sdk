#!/bin/bash
# usage: runfile.sh <pyname:312|313> <worktree> <outdir> <testfile> [timeout]
PYN=$1; WT=$2; OUT=$3; F=$4; T=${5:-420}
SP=/tmp/claude-0/-home-user-hadavin-sdk/3c7954a2-a1b2-5867-97dd-d4d94c9e06fd/scratchpad
if [ $PYN = 312 ]; then PY=$SP/v312/bin/python; else PY=/home/user/build/wt/q8c1-b17fix/.venv/bin/python; fi
mkdir -p $OUT; cd $WT
export PYTHONPATH=$WT/src
b=$(basename $F .py)
{ env -u GH_TOKEN -u GITHUB_TOKEN -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL $PY -c 'import hadavin_sdk;print("sdk:",hadavin_sdk.__file__)'
  env -u GH_TOKEN -u GITHUB_TOKEN -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL timeout $T $PY -m pytest $F -q -p no:cacheprovider --no-header -rfE 2>&1 | tail -40; echo "rc=${PIPESTATUS[0]}"; } > $OUT/$b.txt 2>&1
tail -3 $OUT/$b.txt | tr '\n' ' '; echo " <- $b"
