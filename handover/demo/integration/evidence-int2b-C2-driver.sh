#!/bin/bash
# resumable chunked full run of the fixed stack (container restarts kill long runs): skips chunks that have an .exit file
cd /tmp/work/int2b-c || exit 1
export PATH=/opt/node22/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers GITLEAKS_BIN=/tmp/work/gl/gitleaks DPLD_REQUIRE_SCAN=1 PYTHONUNBUFFERED=1
N=10
total=$(wc -l < /tmp/work/c2files.txt)
per=$(( (total + N - 1) / N ))
for i in $(seq 0 $((N-1))); do
  out=/tmp/work/c2chunk-$i
  [ -f $out.exit ] && continue
  files=$(sed -n "$((i*per+1)),$(((i+1)*per))p" /tmp/work/c2files.txt | tr '\n' ' ')
  [ -z "$files" ] && continue
  rm -f $out.txt
  date -u +%FT%TZ > $out.start
  timeout 1500 /tmp/work/int2-venv/bin/python -u -m pytest $files -v -o faulthandler_timeout=300 -p no:cacheprovider -rs > $out.txt 2>&1
  echo "exit=$?" > $out.exit; date -u +%FT%TZ >> $out.exit
done
echo done > /tmp/work/c2chunks.done
