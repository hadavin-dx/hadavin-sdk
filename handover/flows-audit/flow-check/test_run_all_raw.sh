#!/bin/bash
# f8-r11 test for the intermittent exit 1 "SELFTEST summary line missing in raw/selftest-new.txt" (review f8-r10, evidence f8-r9).
# Bug class: run_all.sh wrote its raw output into a folder that something else can also touch (the tracked raw/ folder: another run, an editor, git, a reader). Any other process that
# truncates or rewrites a file there while the run is going makes a later read of that file fail or read other text.
# This test starts the script with its raw folder pre-filled with the file names the old script wrote, runs a "disturber" that truncates those files every 0.05 s for the whole run, and then requires:
#   1. exit status 0 and no 'summary line missing' text in the output (the run's own results cannot be damaged from outside),
#   2. the sentinel file that the disturber does NOT touch is unchanged and the tracked raw folder holds exactly the files it held before (a run without --refresh writes nothing there).
# The OLD run_all.sh (before f8-r11) fails this test (it wrote its raw output into that folder); the new one passes. Usage: bash test_run_all_raw.sh [SCRIPT_UNDER_TEST] [SCRATCH_DIR]
# SCRIPT_UNDER_TEST defaults to run_all.sh next to this file; an older copy must sit in a mirror of this folder (it needs ../../demo and ../patches).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
SUT=${1:-}; [ -n "$SUT" ] || SUT=$HERE/run_all.sh; [ -f "$SUT" ] || { echo "usage: bash test_run_all_raw.sh [run_all.sh to test] [scratch dir (must not exist)]"; exit 2; }
if [ -n "${2:-}" ]; then [ -e "$2" ] && { echo "REFUSED: $2 exists"; exit 2; }; T=$2; mkdir -p -- "$T" || exit 2; else T=$(mktemp -d "${TMPDIR:-/tmp}/tra.XXXXXX") || exit 2; trap 'rm -rf -- "$T"' EXIT; fi
X="$T/rawfolder"; mkdir -p -- "$X"
for f in selftest-new.txt take-check.txt apply.log gen-real.log; do echo "stale text from an earlier run" > "$X/$f"; done
echo "sentinel: not touched by the disturber" > "$X/sentinel.txt"
BEFORE=$(cd "$X" && ls -A | sort | tr '\n' ' '); SENT=$(sha256sum < "$X/sentinel.txt")
( while [ ! -e "$T/stop" ]; do for f in "$X"/*; do case $f in */sentinel.txt) ;; *) [ -f "$f" ] && : > "$f";; esac; done; sleep 0.05; done ) &
DPID=$!
cd "$T" && env RUN_ALL_RAW="$X" bash "$SUT" > "$T/out.txt" 2>&1; RC=$?
touch "$T/stop"; wait "$DPID" 2>/dev/null
AFTER=$(cd "$X" && ls -A | sort | tr '\n' ' ')
BAD=0; N=0
ok() { N=$((N+1)); if [ "$1" = 0 ]; then echo "ok   $2"; else echo "FAIL $2"; BAD=$((BAD+1)); fi; }
[ "$RC" = 0 ]; ok $? "run exits 0 while another process truncates every file of its raw folder (got exit $RC)"
! grep -q 'summary line missing' "$T/out.txt"; ok $? "no 'summary line missing' text in the run output"
[ "$(sha256sum < "$X/sentinel.txt")" = "$SENT" ]; ok $? "the untouched sentinel file in the raw folder is unchanged"
[ "$AFTER" = "$BEFORE" ]; ok $? "the raw folder holds exactly the same file names as before the run (before: $BEFORE| after: $AFTER)"
echo "test_run_all_raw: $((N-BAD)) of $N cases as expected, $BAD not as expected"
[ "$BAD" = 0 ] || { echo "last lines of the run output:"; tail -n 5 "$T/out.txt" | cut -c1-200; }
[ "$BAD" = 0 ]
