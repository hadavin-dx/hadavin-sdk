#!/bin/bash
# f8-r11 test for the intermittent exit 1 "SELFTEST summary line missing in raw/selftest-new.txt" (review f8-r10, evidence f8-r9); f8-r12 adds the publish path (review f8-r12 minor m9, major M1) and a bound on the disturber (m4b).
# Bug class: run_all.sh wrote its raw output into a folder that something else can also touch (the tracked raw/ folder: another run, an editor, git, a reader). Any other process that
# truncates or rewrites a file there while the run is going makes a later read of that file fail or read other text.
# PHASE 1: starts the script with its raw folder pre-filled with the file names the old script wrote, runs a "disturber" that truncates those files every 0.05 s for the whole run, and then requires:
#   1. exit status 0 and no 'summary line missing' text in the output (the run's own results cannot be damaged from outside),
#   2. the sentinel file that the disturber does NOT touch is unchanged and the tracked raw folder holds exactly the files it held before (a run without --refresh writes nothing there).
# PHASE 2 (f8-r12): a full run with --refresh in a mirror of this folder (its own raw/ is the destination): exit 0, every raw file of the run is in raw/ byte for byte, refresh-manifest.txt lists them with their sha256, a file of an older run that this run did not make is left alone, no temporary file stays.
# PHASE 3 (f8-r12): the same run made to FAIL (a wrong pinned count): with --refresh it must publish NOTHING (raw/ keeps exactly what it held), exit 1, and say so.
# The OLD run_all.sh (before f8-r11) fails phase 1; the f8-r11 one fails phases 2 and 3; the new one passes all three. Usage: bash test_run_all_raw.sh [SCRIPT_UNDER_TEST] [SCRATCH_DIR]
# SCRIPT_UNDER_TEST defaults to run_all.sh next to this file; an older copy must sit in a mirror of this folder (it needs ../../demo and ../patches). A full run takes about 4 minutes; phases 2 and 3 run side by side after phase 1 (about 10 minutes in all).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
SUT=${1:-}; [ -n "$SUT" ] || SUT=$HERE/run_all.sh; [ -f "$SUT" ] || { echo "usage: bash test_run_all_raw.sh [run_all.sh to test] [scratch dir (must not exist)]"; exit 2; }
SD=$(cd "$(dirname "$SUT")" && pwd)
if [ -n "${2:-}" ]; then [ -e "$2" ] && { echo "REFUSED: $2 exists"; exit 2; }; T=$2; mkdir -p -- "$T" || exit 2; else T=$(mktemp -d "${TMPDIR:-/tmp}/tra.XXXXXX") || exit 2; fi
DPID=""
# f8-r12 (m4b): whatever ends this test (end, Ctrl-C, kill), the disturber is told to stop and is killed, and its loop is bounded (30 minutes) in any case
stop_disturber() { touch "$T/stop" 2>/dev/null; [ -z "$DPID" ] || { kill "$DPID" 2>/dev/null; wait "$DPID" 2>/dev/null; }; DPID=""; }
TMADE=""; [ -n "${2:-}" ] || TMADE=1
trap 'stop_disturber; [ -z "$TMADE" ] || rm -rf -- "$T"' EXIT
trap 'exit 130' INT; trap 'exit 143' TERM; trap 'exit 129' HUP
NEWOPT=""; grep -q -- '--raw-dir' "$SUT" && NEWOPT=1   # the old script takes its raw folder from RUN_ALL_RAW, the new one from --raw-dir
X="$T/rawfolder"; mkdir -p "$X"
for f in selftest-new.txt take-check.txt apply.log gen-real.log; do echo "stale text from an earlier run" > "$X/$f"; done
echo "sentinel: not touched by the disturber" > "$X/sentinel.txt"
BEFORE=$(cd "$X" && ls -A | sort | tr '\n' ' '); SENT=$(sha256sum < "$X/sentinel.txt")
# phase 2 and 3 mirrors (built now, run after phase 1)
mk_mirror() { # NAME: a mirror folder tree holding a copy of the scripts under test, with links to the flows and patches; prints the folder of the copy
  local m=$T/$1 f; f=$m/handover/flows-audit/flow-check; mkdir -p "$f" || return 1
  local n; for n in take_check.sh test_take_check.sh check_flows.py selftest.py take-warns.pin expected-counts.pin; do [ ! -f "$SD/$n" ] || cp -- "$SD/$n" "$f/$n" || return 1; done
  cp -- "$SUT" "$f/run_all.sh" || return 1
  ln -s "$(cd "$SD/../../demo" && pwd)" "$m/handover/demo" && ln -s "$(cd "$SD/../patches" && pwd)" "$m/handover/flows-audit/patches" || return 1
  echo "$f"
}
(
  while [ ! -e "$T/stop" ] && [ "$SECONDS" -lt 1800 ]; do for f in "$X"/*; do case $f in */sentinel.txt) ;; *) [ -f "$f" ] && : > "$f";; esac; done; sleep 0.05; done
) &
DPID=$!
if [ -n "$NEWOPT" ]; then ( cd "$T" && bash "$SUT" --raw-dir "$X" > "$T/out.txt" 2>&1 ); RC=$?; else ( cd "$T" && env RUN_ALL_RAW="$X" bash "$SUT" > "$T/out.txt" 2>&1 ); RC=$?; fi
stop_disturber
AFTER=$(cd "$X" && ls -A | sort | tr '\n' ' ')
BAD=0; N=0
ok() { N=$((N+1)); if [ "$1" = 0 ]; then echo "ok   $2"; else echo "FAIL $2"; BAD=$((BAD+1)); fi; }
[ "$RC" = 0 ]; ok $? "run exits 0 while another process truncates every file of its raw folder (got exit $RC)"
! grep -q 'summary line missing' "$T/out.txt"; ok $? "no 'summary line missing' text in the run output"
[ "$(sha256sum < "$X/sentinel.txt")" = "$SENT" ]; ok $? "the untouched sentinel file in the raw folder is unchanged"
[ "$AFTER" = "$BEFORE" ]; ok $? "the raw folder holds exactly the same file names as before the run (before: $BEFORE| after: $AFTER)"
[ "$BAD" = 0 ] || { echo "last lines of the run output (phase 1):"; tail -n 5 "$T/out.txt" | cut -c1-200; }
# ---- phases 2 and 3 ----
M2=$(mk_mirror m2) && M3=$(mk_mirror m3) || { echo "FAIL could not build the mirror folders"; exit 1; }
mkdir -p "$M2/raw" "$M3/raw"; echo "file of an older run" > "$M2/raw/older-run-only.txt"; echo "file of an older run" > "$M3/raw/older-run-only.txt"
sed -i 's/^selftest_as_expected=.*/selftest_as_expected=1/' "$M3/expected-counts.pin"   # phase 3: a wrong pinned count makes the run fail at its end, after all the work
( cd "$T" && bash "$M2/run_all.sh" --refresh --keep > "$T/out2.txt" 2>&1; echo $? > "$T/rc2" ) &
P2=$!
( cd "$T" && bash "$M3/run_all.sh" --refresh > "$T/out3.txt" 2>&1; echo $? > "$T/rc3" ) &
P3=$!
wait "$P2" "$P3"
RC2=$(cat "$T/rc2" 2>/dev/null); RC3=$(cat "$T/rc3" 2>/dev/null)
KEPT=$(sed -n 's/^raw output of this run is kept in: \([^ ]*\).*/\1/p' "$T/out2.txt" | head -n 1)
[ "$RC2" = 0 ]; ok $? "phase 2: a passing run with --refresh exits 0 (got exit $RC2)"
[ -n "$KEPT" ] && [ -d "$KEPT" ]; ok $? "phase 2: the run's own raw folder is named in its output (--keep) ($KEPT)"
DIFFN=0; FILEN=0; if [ -d "$KEPT" ]; then for f in "$KEPT"/*; do [ -f "$f" ] || continue; FILEN=$((FILEN+1)); cmp -s "$f" "$M2/raw/$(basename "$f")" || DIFFN=$((DIFFN+1)); done; fi
[ "$FILEN" -gt 20 ] && [ "$DIFFN" = 0 ]; ok $? "phase 2: all $FILEN raw files of the run are in raw/ byte for byte ($DIFFN differ)"
MF="$M2/raw/refresh-manifest.txt"
[ -f "$MF" ] && [ "$(grep -c -v '^#' "$MF")" = "$FILEN" ] && [ -n "$KEPT" ] && grep -q "^$(sha256sum < "$KEPT/selftest-new.txt" | cut -c1-64)  selftest-new.txt$" "$MF" && ! grep -q 'older-run-only' "$MF"; ok $? "phase 2: refresh-manifest.txt lists exactly the files of this run with their sha256 (not the older file)"
[ "$(cat "$M2/raw/older-run-only.txt" 2>/dev/null)" = "file of an older run" ] && [ -z "$(ls -A "$M2/raw" | grep '\.tmp\.')" ]; ok $? "phase 2: the file of an older run is left alone and no temporary file stays"
grep -q "^raw files refreshed in " "$T/out2.txt" && grep -q "^run_all exit status (real-v5 default runs + self-test): 0$" "$T/out2.txt"; ok $? "phase 2: the run says that raw/ was refreshed and prints exit status 0"
[ -z "$KEPT" ] || rm -rf -- "$KEPT"
[ "$RC3" = 1 ]; ok $? "phase 3: a failing run exits 1 (got exit $RC3)"
[ "$(ls -A "$M3/raw" | tr '\n' ' ')" = "older-run-only.txt " ]; ok $? "phase 3: a failing run with --refresh publishes nothing (raw/ holds: $(ls -A "$M3/raw" | tr '\n' ' '))"
grep -q "raw/ was NOT refreshed: this run did not pass" "$T/out3.txt" && grep -q "^run_all exit status (real-v5 default runs + self-test): 1$" "$T/out3.txt"; ok $? "phase 3: the run says raw/ was NOT refreshed and prints exit status 1"
K3=$(sed -n 's/^raw output of this run is kept in: \([^ ]*\).*/\1/p' "$T/out3.txt" | head -n 1); [ -z "$K3" ] || rm -rf -- "$K3"
echo "test_run_all_raw: $((N-BAD)) of $N cases as expected, $BAD not as expected"
[ "$BAD" = 0 ] || { echo "last lines of the run outputs:"; tail -n 4 "$T/out2.txt" | cut -c1-200; tail -n 4 "$T/out3.txt" | cut -c1-200; }
[ "$BAD" = 0 ]
