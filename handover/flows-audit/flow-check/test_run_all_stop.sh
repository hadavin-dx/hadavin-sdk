#!/bin/bash
# f8-r12 test (review f8-r12 M2). Bug class: a long script that starts helper processes and removes folders at its end, with no time limit on a step and no clean-up of the helpers when it is stopped.
# Before f8-r12 run_all.sh had a time limit only on the nine checker runs; a stopped or interrupted run left the self-test and the other helpers running and deleted the folders under them.
# Cases (each starts the REAL run_all.sh, waits until its self-test is running, then acts):
#   A. SIGTERM: exit 143, the message INTERRUPTED (TERM), no process of the run is left, the work folder the run made itself is removed, the scratch raw folder is kept and named, and the work folder is made under TMPDIR (not a fixed /tmp)
#   B. SIGINT (Ctrl-C) and C. SIGHUP (terminal closed): the same, with a work folder given on the command line (that one is never removed)
#   D. time limit: in a copy whose self-test is replaced by a program that sleeps for 10 minutes, RUN_ALL_LIMIT_SELFTEST=3 stops it after about 3 seconds while the run goes on; then the run is stopped (as in A) and nothing is left.
#   E. SIGTERM while the nine checker runs are going, F. SIGINT while the take test suite (test_take_check.sh) is going, G. SIGHUP while the four nested test runs are going (f8-r13: A to C only fired during the self-test, so the other steps were never shown to be stopped). In D the run's exit status after the stop must be 143, not 0.
#   Every case also checks, by SESSION id, that no process of the run's own session is left (a helper whose command line has no folder name in it would have been missed by the older command-line check).
# Usage: bash test_run_all_stop.sh [SCRIPT_UNDER_TEST] [SCRATCH_DIR (must not exist)]. About 3 minutes. The f8-r11 script fails these cases (no time limit, no trap, helpers left running).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
SUT=${1:-}; [ -n "$SUT" ] || SUT=$HERE/run_all.sh; [ -f "$SUT" ] || { echo "usage: bash test_run_all_stop.sh [run_all.sh to test] [scratch dir (must not exist)]"; exit 2; }
SD=$(cd "$(dirname "$SUT")" && pwd); SUT=$SD/$(basename "$SUT")   # f8-r13: absolute paths (the patterns below are matched against command lines)
if [ -n "${2:-}" ]; then [ -e "$2" ] && { echo "REFUSED: $2 exists"; exit 2; }; T=$(realpath -m -- "$2"); mkdir -p -- "$T" || exit 2; else T=$(mktemp -d "${TMPDIR:-/tmp}/trs.XXXXXX") || exit 2; fi
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
os.setsid()
os.execvp("bash", ["bash"] + sys.argv[1:])' "$script" ${args[@]+"${args[@]}"} > "$T/out-$nm.txt" 2>&1 &
  RUNPID=$!
}
wait_for() { local i pat=$1 secs=$2; for i in $(seq 1 $((secs*2))); do pgrep -f "$pat" > /dev/null 2>&1 && return 0; sleep 0.5; done; return 1; }
wait_gone() { local i pat=$1 secs=$2; for i in $(seq 1 $((secs*2))); do pgrep -f "$pat" > /dev/null 2>&1 || return 0; sleep 0.5; done; return 1; }
# sid_left PID: 0 when a process of the session that the run started (its session id is the run's pid, see start) is still alive
sid_left() { ps -e -o sid= 2>/dev/null | tr -d ' ' | grep -q -x "$1"; }
wait_sid_gone() { local i; for i in $(seq 1 $(($2*2))); do sid_left "$1" || return 0; sleep 0.5; done; return 1; }
stop_case() { # NAME SIGNAL EXPECTED-EXIT WORKDIR-GIVEN(0/1) [PHASE: selftest|checkers|suite|nested] [ENV...]
  local nm=$1 sig=$2 want=$3 given=$4 phase=${5:-selftest} work="" pat what; shift 4; [ $# -eq 0 ] || shift
  [ "$given" = 0 ] || work="$T/work-$nm"
  start "$nm" "$SUT" "$work" "$@"
  local sid=$RUNPID
  local base="$T/tmp-$nm/fc8\\.[A-Za-z0-9]*"; [ -z "$work" ] || base="$T/work-$nm"
  case $phase in
    selftest) pat="selftest\\.py .*$base/g/real"; what="the self-test";;
    checkers) pat="check_flows\\.py .*$base/g/real"; what="a checker run";;
    suite) pat="test_take_check\\.sh .*$base/g/real"; what="the take test suite";;
    nested) pat="run_all\\.sh .*$base/tc/nested-work"; what="the nested test runs";;
  esac
  wait_for "$pat" 400; ok $? "$nm: $what of the run is running (waited up to 400 s)"
  kill "-$sig" "$RUNPID" 2>/dev/null
  local i; for i in $(seq 1 80); do kill -0 "$RUNPID" 2>/dev/null || break; sleep 0.5; done
  local alive=0; kill -0 "$RUNPID" 2>/dev/null && alive=1
  [ "$alive" = 0 ]; ok $? "$nm: the run ended within 40 s of SIG$sig"
  wait "$RUNPID" 2>/dev/null; local rc=$?; RUNPID=""
  [ "$rc" = "$want" ]; ok $? "$nm: exit status $want (got $rc)"
  wait_gone "$T/(tmp|work|raw)-$nm" 5; ok $? "$nm: no process of the run is left (checkers, self-test, take script, nested runs)"
  wait_sid_gone "$sid" 5; ok $? "$nm: no process of the run's own session is left (found by session id, not by command line)"
  grep -q "^INTERRUPTED ($sig): stopping every process this run started" "$T/out-$nm.txt"; ok $? "$nm: the run says it was interrupted"
  local kept; kept=$(sed -n 's/^raw output of this run is kept in: \([^ ]*\).*/\1/p' "$T/out-$nm.txt" | head -n 1)
  [ -n "$kept" ] && [ -d "$kept" ]; ok $? "$nm: the raw output of the interrupted run is kept and named ($kept)"
  if [ -z "$work" ]; then [ -z "$(ls -A "$T/tmp-$nm" | grep -v '^fc8raw\.')" ]; ok $? "$nm: the work folder the run made itself is removed from TMPDIR (found: $(ls -A "$T/tmp-$nm" | tr '\n' ' '))"
  else [ -d "$work" ]; ok $? "$nm: a work folder given on the command line is NOT removed"; fi
}
stop_case A-sigterm TERM 143 0
stop_case B-sigint INT 130 1
stop_case C-sighup HUP 129 1
# E needs a checker run that lasts: the real checkers end in under a second, so no signal could be aimed at them. In a mirror whose check_flows.py sleeps for 10 minutes the nine checker runs are all alive when the signal comes.
F="$T/mirror-E/handover/flows-audit/flow-check"; mkdir -p "$F"
for n in run_all.sh take_check.sh test_take_check.sh selftest.py take-warns.pin expected-counts.pin README.md; do [ ! -f "$SD/$n" ] || cp -- "$SD/$n" "$F/$n"; done
cp -- "$SUT" "$F/run_all.sh"; printf 'import time\ntime.sleep(600)\n' > "$F/check_flows.py"
ln -s "$(cd "$SD/../../demo" && pwd)" "$T/mirror-E/handover/demo"; ln -s "$(cd "$SD/../patches" && pwd)" "$T/mirror-E/handover/flows-audit/patches"
SUT_REAL=$SUT; SUT=$F/run_all.sh
stop_case E-sigterm-checkers TERM 143 1 checkers
SUT=$SUT_REAL
stop_case F-sigint-suite INT 130 1 suite
stop_case G-sighup-nested HUP 129 1 nested
# H (f8-r13): two SIGTERM in a row at selftest.py itself (run_all.sh and the time-limit command can both send one). The second used to cut the clean-up of the first short and leave fc-selftest-* in TMPDIR. Five tries, each aimed at the moment the work folder appears.
DEMO=$(cd "$SD/../../demo" && pwd); HL=0
for k in 1 2 3 4 5; do
  mkdir -p "$T/h-tmp-$k"
  env TMPDIR="$T/h-tmp-$k" FC_OUT="$T/h-out-$k" python3 -I "$SD/selftest.py" "$DEMO/n8n-flows-real-v5" "$DEMO/n8n-flows-real-v5" "$DEMO/n8n-flows-film-v5" > "$T/h-$k.txt" 2>&1 &
  HP=$!; RUNPID=$HP
  for i in $(seq 1 400); do [ -n "$(ls -A "$T/h-tmp-$k" 2>/dev/null | grep '^fc-selftest-[^o]')" ] && break; sleep 0.05; done
  kill -TERM "$HP" 2>/dev/null; kill -TERM "$HP" 2>/dev/null
  for i in $(seq 1 100); do kill -0 "$HP" 2>/dev/null || break; sleep 0.1; done
  wait "$HP" 2>/dev/null; HRC=$?; RUNPID=""
  [ "$HRC" = 143 ] && [ -z "$(ls -A "$T/h-tmp-$k" 2>/dev/null | grep '^fc-selftest-[^o]')" ] || { HL=$((HL+1)); echo "     try $k: exit $HRC, left in TMPDIR: $(ls -A "$T/h-tmp-$k" | tr '\n' ' ')"; }
done
[ "$HL" = 0 ]; ok $? "H-double-sigterm: selftest.py given two SIGTERM in a row exits 143 and leaves no work folder, 5 tries ($HL went wrong)"
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
SIDD=$RUNPID; wait "$RUNPID" 2>/dev/null; DRC=$?; RUNPID=""
[ "$DRC" = 143 ]; ok $? "D-limit: exit status 143 after the stop (got $DRC), not 0"
wait_gone "$T/(tmp|work|raw)-D-limit" 5; ok $? "D-limit: no process of the run is left after SIGTERM"
wait_sid_gone "$SIDD" 5; ok $? "D-limit: no process of the run's own session is left (by session id)"
echo "test_run_all_stop: $((N-BAD)) of $N cases as expected, $BAD not as expected"
[ "$BAD" = 0 ] || { echo "last lines of the outputs:"; for f in "$T"/out-*.txt; do echo "[$f]"; tail -n 3 "$f" | cut -c1-200; done; }
[ "$BAD" = 0 ]
