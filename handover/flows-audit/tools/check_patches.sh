#!/bin/sh
# Check (d). Run from repo root: sh handover/flows-audit/tools/check_patches.sh
# For each handover/flows-audit/patches/*.patch: git apply --check (writes nothing), then apply a COPY of the target files in tools/scratch and parse any patched .json. Exit 0 pass, 1 fail.
P=handover/flows-audit/patches; S=handover/flows-audit/tools/scratch; rc=0; n=0
mkdir -p "$S"
for f in "$P"/*.patch; do
  [ -e "$f" ] || { echo "SKIP no patches"; exit 0; }
  n=$((n+1)); git apply --check "$f" || { echo "FAIL apply-check $f"; rc=1; continue; }
  t="$S/p$n"; rm -rf "$t"; mkdir -p "$t"
  for x in $(git apply --numstat "$f" | cut -f3); do mkdir -p "$t/$(dirname "$x")"; cp "$x" "$t/$x"; done
  (cd "$t" && git apply "../../../../../$f" 2>/dev/null || patch -p1 -s < "../../../../../$f") || { echo "FAIL scratch-apply $f"; rc=1; continue; }
  for j in $(git apply --numstat "$f" | cut -f3 | grep '\.json$'); do python3 -c "import json,sys;json.load(open('$t/$j'))" || { echo "FAIL json-parse $f $j"; rc=1; }; done
done
[ $rc -eq 0 ] && echo "PASS $n patches"; exit $rc
