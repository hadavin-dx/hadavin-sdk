#!/bin/sh
# v7: runs the 16 damages under one shell ($1) in 3 parallel groups, output dir $2 (private, not the earlier run's folder)
SH=$1; O=$2; HERE=$(cd "$(dirname "$0")" && pwd); S=$HERE/../lead-repin-verify.sh
mkdir -p "$O"
python3 -I "$HERE/mutate.py" "$S" "$O" "$SH" v01-no-pre-stage v02-pwcmds-list-unused v03-nonascii-noop v04-ml-start-off v05-length-guard-off > "$O/g1-$SH.txt" 2>&1 &
python3 -I "$HERE/mutate.py" "$S" "$O" "$SH" v06-url-userinfo-off v07-canary-count-off-by-one v08-selftest-count-off-by-one v10-bearer-rule-off v11-jwt-rule-off v15-dotted-camel-rule-reverted v16-ml-continue-off > "$O/g2-$SH.txt" 2>&1 &
python3 -I "$HERE/mutate.py" "$S" "$O" "$SH" v09-signal-kids-not-killed v12-recount-always-ok v13-watchdog-off v14-premain-not-background > "$O/g3-$SH.txt" 2>&1 &
wait
cat "$O/g1-$SH.txt" "$O/g2-$SH.txt" "$O/g3-$SH.txt"
