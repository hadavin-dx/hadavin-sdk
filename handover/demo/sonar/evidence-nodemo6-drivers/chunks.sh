#!/bin/bash
# usage: chunks.sh <copy> <outdir>   (nodemo-ci-job style: 9 interleaved chunks, one pytest at a time)
cd /tmp/work/sn-v5/$1; mkdir -p $2
export GITLEAKS_BIN=/tmp/work/gl/gitleaks; export DPLD_REQUIRE_SCAN=${REQ-1}; [ -z "$DPLD_REQUIRE_SCAN" ] && unset DPLD_REQUIRE_SCAN
mapfile -t files < <(ls tests/test_*.py)
python=/tmp/work/sn-v5/venv/bin/python
$python -u -m pytest --collect-only -q -p no:cacheprovider "${files[@]}" | tail -1
for i in 0 1 2 3 4 5 6 7 8; do
  chunk=(); for ((j = i; j < ${#files[@]}; j += 9)); do chunk+=("${files[j]}"); done
  echo "== chunk $i: ${#chunk[@]} files"
  $python -u -m pytest -q -p no:cacheprovider --junitxml=$2/chunk-$i.xml -o junit_family=xunit2 "${chunk[@]}" > $2/chunk-$i.txt 2>&1
  echo "rc=$? $(tail -n 1 $2/chunk-$i.txt)"
done
echo CHUNKS-DONE
