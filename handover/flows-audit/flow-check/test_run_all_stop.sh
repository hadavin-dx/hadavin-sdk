#!/bin/bash
# f8-r12 test (review f8-r12 M2). Bug class: a long script that starts helper processes and removes folders at its end, with no time limit on a step and no clean-up of the helpers when it is stopped.
# Before f8-r12 run_all.sh had a time limit only on the nine checker runs; a stopped or interrupted run left the self-test and the other helpers running and deleted the folders under them.
# Cases (each starts the REAL run_all.sh, waits until its self-test is running, then acts):
#   A. SIGTERM: exit 143, the message INTERRUPTED (TERM), no process of the run is left, the work folder the run made itself is removed, the scratch raw folder is kept and named, and the work folder is made under TMPDIR (not a fixed /tmp)
#   B. SIGINT (Ctrl-C) and C. SIGHUP (terminal closed): the same, with a work folder given on the command line (that one is never removed)
#   D. time limit: in a copy whose self-test is replaced by a program that sleeps for 10 minutes, RUN_ALL_LIMIT_SELFTEST=3 stops it after about 3 seconds while the run goes on; then the run is stopped (as in A) and nothing is left.
# Usage: bash test_run_all_stop.sh [SCRIPT_UNDER_TEST] [SCRATCH_DIR (must not exist)]. About 2 minutes. The f8-r11 script fails these cases (no time limit, no trap, helpers left running).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
SUT=${1:-}; [ -n "$SUT" ] || SUT=$HERE/run_all.sh; [ -f "$SUT" ] || { echo "usage: bash test_run_all_stop.sh [run_all.sh to test] [scratch dir (must not exist)]"; exit 2; }
SD=$(cd "$(dirname "$SUT")" && pwd)
if [ -n "${2:-}" ]; then [ -e "$2" ] && { echo "REFUSED: $2 exists"; exit 2; }; T=$2; mkdir -p -- "$T" || exit 2; else T=$(mktemp -d "${TMPDIR:-/tmp}/trs.XXXXXX") || exit 2; fi
TMADE=""; [ -n "${2:-}" ] || TMADE=1
RUNPID=""
cleanup_all() { [ -z "$RUNPID" ] || kill -KILL "$RUNPID" 2>/dev/null; pkill -KILL -f "$T/(tmp|work|raw|mirror)" 2>/dev/null; [ -z "$TMADE" ] || rm -rf -- "$T"; }
trap cleanup_all EXIT; trap 'exit 130' INT; trap 'exit 143' TERM; trap 'exit 129' HUP
NEWOPT=""; grep -q -- '--raw-dir' "$SUT" && NEWOPT=1
BAD=0; N=0
ok() { N=$((N+1)); if [ "$1" = 0 ]; then echo "ok   $2"; else echo "FAIL $2"; BAD=$((BAD+1)); fi; }
# start NAME SCRIPT WORKDIR(or "") [ENV...]: the run is started with SIGINT at its default (a background job of a script ignores it otherwise, and an ignored signal cannot be trapped)
start() {
  local nm=$1 script=$2 work=$3; shift 3
  mkdir -p "$T/tmp-$nm"
  local args=(); [ -z "$NEWOPT" ] || args=(--raw-dir "$T/raw-$nm"); [ -z "$work" ] || args+=("$work")
  local envv=(TMPDIR="$T/tmp-$nm"); [ -n "$NEWOPT" ] || envv+=(RUN_ALL_RAW="$T/raw-$nm")
  env "${envv[@]}" "$@" python3 -I -c 'import os, signal, sys
signal.signal(signal.SIGINT, signal.SIG_DFL)
os.execvp("bash", ["bash"] + sys.argv[1:])' "$script" ${args[@]+"${args[@]}"} > "$T/out-$nm.txt" 2>&1 &
  RUNPID=$!
}
wait_for() { local i pat=$1 secs=$2; for i in $(seq 1 $((secs*2))); do pgrep -f "$pat" > /dev/null 2>&1 && return 0; sleep 0.5; done; return 1; }
wait_gone() { local i pat=$1 secs=$2; for i in $(seq 1 $((secs*2))); do pgrep -f "$pat" > /dev/null 2>&1 || return 0; sleep 0.5; done; return 1; }
stop_case() { # NAME SIGNAL EXPECTED-EXIT WORKDIR-GIVEN(0/1) [ENV...]
  local nm=$1 sig=$2 want=$3 given=$4 work="" pat; shift 4
  [ "$given" = 0 ] || work="$T/work-$nm"
  start "$nm" "$SUT" "$work" "$@"
  if [ -n "$work" ]; then pat="selftest\\.py .*$T/work-$nm/g/real"; else pat="selftest\\.py .*$T/tmp-$nm/fc8\\.[A-Za-z0-9]*/g/real"; fi
  wait_for "$pat" 150; ok $? "$nm: the self-test of the run is running (waited up to 150 s)"
  kill "-$sig" "$RUNPID" 2>/dev/null
  local i; for i in $(seq 1 80); do kill -0 "$RUNPID" 2>/dev/null || break; sleep 0.5; done
  local alive=0; kill -0 "$RUNPID" 2>/dev/null && alive=1
  [ "$alive" = 0 ]; ok $? "$nm: the run ended within 40 s of SIG$sig"
  wait "$RUNPID" 2>/dev/null; local rc=$?; RUNPID=""
  [ "$rc" = "$want" ]; ok $? "$nm: exit status $want (got $rc)"
  wait_gone "$T/(tmp|work|raw)-$nm" 5; ok $? "$nm: no process of the run is left (checkers, self-test, take script, nested runs)"
  grep -q "^INTERRUPTED ($sig): stopping every process this run started" "$T/out-$nm.txt"; ok $? "$nm: the run says it was interrupted"
  local kept; kept=$(sed -n 's/^raw output of this run is kept in: \([^ ]*\).*/\1/p' "$T/out-$nm.txt" | head -n 1)
  [ -n "$kept" ] && [ -d "$kept" ]; ok $? "$nm: the raw output of the interrupted run is kept and named ($kept)"
  if [ -z "$work" ]; then [ -z "$(ls -A "$T/tmp-$nm" | grep -v '^fc8raw\.')" ]; ok $? "$nm: the work folder the run made itself is removed from TMPDIR (found: $(ls -A "$T/tmp-$nm" | tr '\n' ' '))"
  else [ -d "$work" ]; ok $? "$nm: a work folder given on the command line is NOT removed"; fi
}
stop_case A-sigterm TERM 143 0
stop_case B-sigint INT 130 1
stop_case C-sighup HUP 129 1
# D: the time limit at the real call site
F="$T/mirror/handover/flows-audit/flow-check"; mkdir -p "$F"
for n in run_all.sh take_check.sh test_take_check.sh check_flows.py take-warns.pin expected-counts.pin; do [ ! -f "$SD/$n" ] || cp -- "$SD/$n" "$F/$n"; done
cp -- "$SUT" "$F/run_all.sh"; printf 'import time\ntime.sleep(600)\n' > "$F/selftest.py"
ln -s "$(cd "$SD/../../demo" && pwd)" "$T/mirror/handover/demo"; ln -s "$(cd "$SD/../patches" && pwd)" "$T/mirror/handover/flows-audit/patches"
start D-limit "$F/run_all.sh" "$T/work-D-limit" RUN_ALL_LIMIT_SELFTEST=3
PD="selftest\\.py .*$T/work-D-limit/g/real"
wait_for "$PD" 150; ok $? "D-limit: the stand-in self-test (sleeps 10 minutes) is running"
wait_gone "$PD" 25; ok $? "D-limit: it is stopped by the 3-second limit (within 25 s) while the run goes on"
kill -0 "$RUNPID" 2>/dev/null; ok $? "D-limit: the run itself is still going (the limit stopped the step, not the run)"
kill -TERM "$RUNPID" 2>/dev/null; for i in $(seq 1 80); do kill -0 "$RUNPID" 2>/dev/null || break; sleep 0.5; done
wait "$RUNPID" 2>/dev/null; RUNPID=""
wait_gone "$T/(tmp|work|raw)-D-limit" 5; ok $? "D-limit: no process of the run is left after SIGTERM"
echo "test_run_all_stop: $((N-BAD)) of $N cases as expected, $BAD not as expected"
[ "$BAD" = 0 ] || { echo "last lines of the outputs:"; for f in "$T"/out-*.txt; do echo "[$f]"; tail -n 3 "$f" | cut -c1-200; done; }
[ "$BAD" = 0 ]
