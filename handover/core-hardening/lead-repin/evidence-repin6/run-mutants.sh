#!/bin/sh
# runs the 16 damages under one shell ($1); three damage groups in parallel (the lead's limit is 4 heavy jobs)
SH=$1; HERE=$(cd "$(dirname "$0")" && pwd); S=$HERE/../lead-repin-verify.sh; O=/tmp/claude-0/mut
mkdir -p "$O"
python3 -I "$HERE/mutate.py" "$S" "$O" "$SH" v01-no-pre-stage v02-pwcmds-list-unused v03-nonascii-noop v04-ml-start-off v05-length-guard-off > "$O/g1-$SH.txt" 2>&1 &
python3 -I "$HERE/mutate.py" "$S" "$O" "$SH" v06-url-userinfo-off v07-canary-count-off-by-one v08-selftest-count-off-by-one v10-bearer-rule-off v11-jwt-rule-off v15-dotted-camel-rule-reverted v16-ml-continue-off > "$O/g2-$SH.txt" 2>&1 &
python3 -I "$HERE/mutate.py" "$S" "$O" "$SH" v09-signal-kids-not-killed v12-recount-always-ok v13-watchdog-off v14-premain-not-background > "$O/g3-$SH.txt" 2>&1 &
wait
cat "$O/g1-$SH.txt" "$O/g2-$SH.txt" "$O/g3-$SH.txt"
