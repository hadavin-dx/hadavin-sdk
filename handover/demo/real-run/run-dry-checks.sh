#!/usr/bin/env bash
# run-dry-checks.sh  -  re-runnable DRY-RUN checks of the take scripts of duplicate-proof-lead-desk-n8n.
#
# SAFETY: made-up data only. Every command runs under `env -i` (no proxy, no real key, no inherited variable), in a
# temp dir. Hosts used are 127.0.0.1 / localhost (the desk's own fakes or a dead loopback port) or the unroutable
# documentation address 192.0.2.1, which is only ever given to a setting that is REFUSED before any call.
# The real-service paths are NEVER run: hubspot_probe.py without --dry-run, run_real_check.py answered "y" against a
# real address, run_live_check.py answered "y" against a real address. The only "y" answers go to configs whose every
# address is 127.0.0.1:1 (nothing listens: connection refused) - see the 'y' block in do_pass.
#
# usage: run-dry-checks.sh [REPO_CLONE] [PASSES]      defaults: /tmp/work/q4-base  2
# env:   PY=python with the repo's test deps (default /tmp/work/int2-venv/bin/python)
#        QUICK=1        skip the slow cases (--dry-fakes ~35 s each, the "y" cases ~75 s each)
#        ALLOW_KNOWN=1  do not count the documented known mismatches (KNOWN list below) in the exit code
#        EVDIR=dir      where evidence-q4-*.txt and results.tsv are written (default: this script's folder)
# exit:  0 every case matched; 1 at least one mismatch (known ones included unless ALLOW_KNOWN=1); 2 setup problem.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="${1:-/tmp/work/q4-base}"
PASSES="${2:-2}"
PY="${PY:-/tmp/work/int2-venv/bin/python}"
EVDIR="${EVDIR:-$HERE}"
QUICK="${QUICK:-0}"
ALLOW_KNOWN="${ALLOW_KNOWN:-0}"
SAFE_PATH="$(dirname "$PY"):/usr/bin:/bin"
GEN="$HERE/make_synthetic_config.py"
STUB="$HERE/probe_stub.py"

# Mismatches seen on head 2db3926 (see DRY-RUN-CHECKS.md). A case listed here still counts as FAIL unless ALLOW_KNOWN=1.
KNOWN=" rrc-y-keyfile-missing rrc-y-keyfile-2line rrc-y-keyfile-short rrc-y-memory rrc-cfg-binary rrc-dry-fakes-stray rlc-eof-prompt rlc-n-keyfile-missing "

[ -f "$REPO/scripts/run_real_check.py" ] || { echo "setup: $REPO is not the repo clone"; exit 2; }
[ -x "$PY" ] || { echo "setup: $PY not executable"; exit 2; }
case "$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)" in 2db3926) ;; *) echo "note: HEAD is not 2db3926 (expected results were written for it)";; esac

T="$(mktemp -d /tmp/work/q4-dry.XXXXXX)"
case "$T" in /tmp/work/q4-dry.??????) ;; *) echo "setup: bad temp dir"; exit 2;; esac
mkdir -p "$EVDIR"
BG=""
cleanup() {
  for p in $BG; do kill "$p" 2>/dev/null; done
  if [ -d "$T/repocopy" ]; then
    (cd "$T/repocopy" && env -i PATH="$SAFE_PATH" DESK_PORT="${PORT_D:-18801}" DESK_FAKES_PORT="${PORT_F:-18802}" bash scripts/reset.sh >/dev/null 2>&1)
  fi
  find "$T" -mindepth 1 -delete 2>/dev/null; rmdir "$T" 2>/dev/null
}
trap cleanup EXIT

freeport() { "$PY" -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }
PORT_D="$(freeport)"; PORT_F="$(freeport)"; PORT_X="$(freeport)"

TSV="$EVDIR/results.tsv"; : > "$TSV"
FAILS=0; KNOWN_FAILS=0; CASES=0
PASSNO=1; P=""        # P = per-pass temp root
KEYFILE=""            # file with the made-up keys, grepped for in every output

# check_case ID GROUP EXPECT_EXIT REGEX FORBID_REGEX STDIN -- command...   (cwd = $P/cwd, env cleared)
# REGEX/FORBID_REGEX: "-" = none.  STDIN: null | n | y (y only through ycase)
run_case() {
  local id="$1" grp="$2" want="$3" rx="$4" forbid="$5" stdin="$6"; shift 7
  local out="$P/out/$id.txt" before after got ok note=""
  mkdir -p "$P/cwd" "$P/out" "$P/tmp"
  before="$(cd "$P/cwd" && find . | sort)"
  case "$stdin" in
    null) (cd "$P/cwd" && env -i PATH="$SAFE_PATH" TMPDIR="$P/tmp" "${EXTRA[@]}" "$@" </dev/null >"$out" 2>&1); got=$? ;;
    n)    (cd "$P/cwd" && echo n | env -i PATH="$SAFE_PATH" TMPDIR="$P/tmp" "${EXTRA[@]}" "$@" >"$out" 2>&1); got=$? ;;
    y)    (cd "$P/cwd" && echo y | env -i PATH="$SAFE_PATH" TMPDIR="$P/tmp" "${EXTRA[@]}" "$@" >"$out" 2>&1); got=$? ;;
  esac
  after="$(cd "$P/cwd" && find . | sort)"
  ok=1
  [ "$got" = "$want" ] || { ok=0; note="$note exit $got want $want;"; }
  grep -q "Traceback" "$out" && { ok=0; note="$note traceback;"; }
  [ -n "$KEYFILE" ] && grep -qF -f "$KEYFILE" "$out" && { ok=0; note="$note KEY TEXT IN OUTPUT;"; }
  [ "$rx" != "-" ] && ! grep -qE "$rx" "$out" && { ok=0; note="$note missing /$rx/;"; }
  [ "$forbid" != "-" ] && grep -qE "$forbid" "$out" && { ok=0; note="$note found /$forbid/;"; }
  if [ "$stdin" != y ] && [ "$GROUPSTRAY" != allow ] && [ "$before" != "$after" ]; then ok=0; note="$note stray files in cwd;"; fi
  record "$id" "$grp" "$want" "$got" "$ok" "$note" "$out" "$*"
}

record() {
  local id="$1" grp="$2" want="$3" got="$4" ok="$5" note="$6" out="$7" cmd="$8"
  CASES=$((CASES+1))
  local status=PASS
  if [ "$ok" = 0 ]; then
    case "$KNOWN" in *" $id "*) status="FAIL(known)"; KNOWN_FAILS=$((KNOWN_FAILS+1));; *) status=FAIL; FAILS=$((FAILS+1));; esac
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$id" "$grp" "$want" "$got" "$status" "$note" "${cmd//$P/TMP}" >> "$TSV"
  printf '%-34s %-13s want=%s got=%s %s %s\n' "$id" "$grp" "$want" "$got" "$status" "$note"
  {
    echo "### pass $PASSNO case $id [$grp] status=$status want_exit=$want got_exit=$got $note"
    echo "### command: ${cmd//$P/TMP}"
    echo "### last 30 lines of output:"
    tail -30 "$out" | sed "s#$P#TMP#g"
    echo
  } >> "$EVDIR/evidence-q4-$grp.txt"
  # repeatability material: exit code + normalised output
  { echo "exit=$got"; sed -e "s#$P#TMP#g" -e 's/probe-[0-9a-f]*/probe-X/g' -e 's/[0-9][0-9]*/N/g' "$out"; } > "$P/norm-$id.txt"
}

# 
EXTRA=()
GROUPSTRAY=deny

mkcfg() {  # mkcfg NAME [VAR=VALUE | -VAR]...   -> $P/NAME/real-run.env  (loopback hosts for mail counting)
  local n="$1"; shift
  "$PY" "$GEN" "$REPO" "$P/$n" REAL_IMAP_1_HOST=localhost REAL_IMAP_2_HOST=localhost "$@" >/dev/null || { echo "setup: cfg $n"; exit 2; }
  cat "$P/$n/made-up-keys.txt" >> "$KEYFILE"
}

RRC="$REPO/scripts/run_real_check.py"
RLC="$REPO/scripts/run_live_check.py"
HSP="$REPO/scripts/hubspot_probe.py"

do_pass() {
  P="$T/p$PASSNO"; mkdir -p "$P/cwd" "$P/out" "$P/tmp"
  KEYFILE="$P/keys.txt"; : > "$KEYFILE"
  printf 'made-up-key-0001\nmade-up-key-0009\nmade-up-key-0002\nmade-up-key-0003\n' >> "$KEYFILE"
  echo "===== PASS $PASSNO ====="

  # ---------------- scripts/run_real_check.py : refusals and prompt (no real call can happen) ----------------
  mkcfg ok
  local C="$P/ok/real-run.env"
  run_case rrc-help rrc 0 'usage: run_real_check.py' - null -- "$PY" "$RRC" --help
  run_case rrc-noargs rrc 2 'refused: give --config' - null -- "$PY" "$RRC"
  run_case rrc-assume-noconf rrc 2 'only for the self-test' - null -- "$PY" "$RRC" --assume-yes
  run_case rrc-assume-with-config rrc 2 'only for the self-test' - null -- "$PY" "$RRC" --assume-yes --config "$C"
  run_case rrc-unknown-flag rrc 2 'unrecognized arguments' - null -- "$PY" "$RRC" --nope
  run_case rrc-cfg-missing-file rrc 2 'refused: FileNotFoundError' - null -- "$PY" "$RRC" --config "$P/none.env"
  mkdir -p "$P/adir"
  run_case rrc-cfg-dir rrc 2 'refused: IsADirectoryError' - null -- "$PY" "$RRC" --config "$P/adir"
  run_case rrc-cfg-empty rrc 2 'config lacks' - null -- "$PY" "$RRC" --config /dev/null
  printf '\377\376\000\200\201 not utf-8' > "$P/binary.env"
  run_case rrc-cfg-binary rrc 2 'refused' 'byte 0x|position' null -- "$PY" "$RRC" --config "$P/binary.env"
  cp "$C" "$P/lower.env"; echo "desk_qualifier=live_claude" >> "$P/lower.env"
  run_case rrc-cfg-lowercase rrc 2 'not NAME=VALUE' 'live_claude' null -- "$PY" "$RRC" --config "$P/lower.env"
  cp "$C" "$P/noeq.env"; echo "made-up-key-0001" >> "$P/noeq.env"
  run_case rrc-cfg-line-is-a-key rrc 2 'not NAME=VALUE' - null -- "$PY" "$RRC" --config "$P/noeq.env"
  local req
  for req in DESK_DB_PATH DESK_HUBSPOT_KEY_FILE DESK_HUBSPOT_MAX_CALLS REAL_HUBSPOT_READBACK_MAX_CALLS DESK_SMTPP_HOST \
             DESK_SMTPP_USER DESK_SMTPP_PASSWORD_FILE DESK_SMTPP_FROM DESK_SMTPP_RECIPIENTS DESK_SMTPP_MAX_SENDS \
             REAL_IMAP_1_USER REAL_IMAP_1_PASSWORD_FILE REAL_IMAP_2_USER REAL_IMAP_2_PASSWORD_FILE; do
    mkcfg "m-$req" "-$req"
    run_case "rrc-missing-$req" rrc 2 "config lacks: $req" - null -- "$PY" "$RRC" --config "$P/m-$req/real-run.env"
  done
  local spec name
  for spec in "persons7|REAL_PERSONS=7|at least 8" "persons1001|REAL_PERSONS=1001|at most 1000" \
              "persons-key|REAL_PERSONS=made-up-key-0001|not a number" \
              "readback4|REAL_HUBSPOT_READBACK_MAX_CALLS=4|at least 5" "readback10001|REAL_HUBSPOT_READBACK_MAX_CALLS=10001|" \
              "maxcalls0|DESK_HUBSPOT_MAX_CALLS=0|between 1 and 10000" "maxcalls10001|DESK_HUBSPOT_MAX_CALLS=10001|between 1 and 10000" \
              "maxsends0|DESK_SMTPP_MAX_SENDS=0|between 1 and 10000" "timeout10|DESK_HUBSPOT_TIMEOUT_SECONDS=10|at most 9" \
              "port99999|DESK_PORT=99999|between 0 and 65535" "security-bad|DESK_SMTPP_SECURITY=plain|starttls or ssl" \
              "rcpt-mismatch|REAL_IMAP_2_USER=other@example.com|same order" "drain0|REAL_DRAIN_SECONDS=0|above 0" \
              "drain-nan|REAL_DRAIN_SECONDS=nan|not a number" "wait-big|REAL_MAIL_WAIT_SECONDS=86401|" \
              "folder-bad|REAL_IMAP_1_FOLDERS=IN\\BOX|plain ASCII" \
              "url-public|DESK_HUBSPOT_BASE_URL=https://192.0.2.1|vendor's own domains" \
              "url-http-public|DESK_HUBSPOT_BASE_URL=http://192.0.2.1:9999|loopback address only" \
              "url-https-loopback|DESK_HUBSPOT_BASE_URL=https://127.0.0.1:9|vendor's own domains" \
              "url-has-key|DESK_HUBSPOT_BASE_URL=https://made-up-key-0001.example.org|vendor's own domains" \
              "db-exists|DESK_DB_PATH=@EXISTING@|already exists"; do
    name="${spec%%|*}"; spec="${spec#*|}"
    local setv="${spec%%|*}" rxs="${spec#*|}"
    [ "$setv" = "DESK_DB_PATH=@EXISTING@" ] && setv="DESK_DB_PATH=$P/ok/secrets/hubspot-key.txt"
    mkcfg "r-$name" "$setv"
    run_case "rrc-refuse-$name" rrc 2 "${rxs:-refused}" - null -- "$PY" "$RRC" --config "$P/r-$name/real-run.env"
  done
  # the prompt: a valid-looking config stops at y/N; nothing is called before the answer
  run_case rrc-valid-eof rrc 1 'there is no terminal' - null -- "$PY" "$RRC" --config "$C"
  run_case rrc-valid-answer-n rrc 1 'stopped, nothing was called' - n -- "$PY" "$RRC" --config "$C"
  run_case rrc-valid-cleanup-n rrc 1 'stopped, nothing was called' - n -- "$PY" "$RRC" --config "$C" --cleanup
  mkcfg qual DESK_QUALIFIER=live_claude
  run_case rrc-qualifier-forced-recorded rrc 1 'recorded replies \(no live call\)' - n -- "$PY" "$RRC" --config "$P/qual/real-run.env"
  run_case rrc-live-settings-missing rrc 2 'DESK_LIVE_MODEL is required' - null -- "$PY" "$RRC" --config "$C" --live-model
  mkdir -p "$P/live"; printf 'made-up-key-0001\n' > "$P/live/k.txt"
  local LIVE="DESK_LIVE_MODEL=made-up-model-1 DESK_LIVE_KEY_FILE=$P/live/k.txt DESK_LIVE_PRICE_IN_PER_MTOK=1 DESK_LIVE_PRICE_OUT_PER_MTOK=5 DESK_LIVE_PRICE_DATE=2026-01-01 DESK_LIVE_CAP_RUN_USD=0.5 DESK_LIVE_CAP_TOTAL_USD=3 DESK_LIVE_LEDGER_PATH=$P/live/ledger.jsonl DESK_LIVE_RUN_ID=made-up-run"
  mkcfg livepub $LIVE DESK_LIVE_BASE_URL=https://192.0.2.1
  run_case rrc-live-public-url rrc 2 "not the provider's own address" - null -- "$PY" "$RRC" --config "$P/livepub/real-run.env" --live-model
  mkcfg liveloop $LIVE DESK_LIVE_BASE_URL=http://127.0.0.1:9
  run_case rrc-live-loopback-answer-n rrc 1 'worst case model cost' - n -- "$PY" "$RRC" --config "$P/liveloop/real-run.env" --live-model

  # ---------------- scripts/run_real_check.py --dry-fakes (the desk's own fakes on 127.0.0.1 only) ----------------
  if [ "$QUICK" != 1 ]; then
    GROUPSTRAY=allow
    local before_tmp after_tmp
    before_tmp="$(find "$P/tmp" | sort)"
    run_case rrc-dry-fakes rrc 0 'ALL CHECKS HOLD' 'FAIL ' null -- "$PY" "$RRC" --dry-fakes --assume-yes
    after_tmp="$(find "$P/tmp" | sort)"
    # stray check: the self-test folder real-dry-* (db, lock, logs, result.json) is left behind in TMPDIR
    if [ "$before_tmp" = "$after_tmp" ]; then record rrc-dry-fakes-stray rrc "no stray" "no stray" 1 "" "$P/out/rrc-dry-fakes.txt" "(TMPDIR listing before/after)"
    else record rrc-dry-fakes-stray rrc "no stray" "stray: $(echo "$after_tmp" | grep -c .) entries" 0 "left in TMPDIR: $(ls "$P/tmp" | tr '\n' ' ')" "$P/out/rrc-dry-fakes.txt" "(TMPDIR listing before/after)"; fi
    run_case rrc-dry-fakes-no-assume rrc 1 'there is no terminal' - null -- "$PY" "$RRC" --dry-fakes
    run_case rrc-dry-fakes-with-config rrc 0 'note: --config is ignored' - null -- "$PY" "$RRC" --dry-fakes --assume-yes --config "$C"
    run_case rrc-dry-fakes-mail-fails rrc 3 'AT LEAST ONE CHECK FAILED' - null -- "$PY" "$RRC" --dry-fakes --assume-yes --dry-smtp-script final_452
    GROUPSTRAY=deny
  fi

  # ---------------- "y" answers: ONLY configs whose every address is 127.0.0.1:1 / localhost:1 (dead loopback port) ----
  if [ "$QUICK" != 1 ]; then
    GROUPSTRAY=allow
    local DEAD="DESK_HUBSPOT_BASE_URL=http://127.0.0.1:1 DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes DESK_SMTPP_PORT=1 REAL_IMAP_1_HOST=localhost REAL_IMAP_2_HOST=localhost REAL_IMAP_1_PORT=1 REAL_IMAP_2_PORT=1 REAL_DRAIN_SECONDS=5 REAL_MAIL_WAIT_SECONDS=5 REAL_MAIL_SETTLE_SECONDS=1"
    mkcfg ymem $DEAD DESK_DB_PATH=:memory: DESK_PORT="$PORT_X"
    run_case rrc-y-memory rrc 2 'refus' - y -- "$PY" "$RRC" --config "$P/ymem/real-run.env"
    rm -f "$P/cwd/desk-1.log" "$P/cwd/desk-2.log"
    mkcfg ykm $DEAD DESK_HUBSPOT_KEY_FILE="$P/none-key.txt" DESK_PORT="$PORT_X"
    run_case rrc-y-keyfile-missing rrc 2 'refus' - y -- "$PY" "$RRC" --config "$P/ykm/real-run.env"
    mkcfg yk2 $DEAD DESK_PORT="$PORT_X"
    printf 'made-up-key-0001\nmade-up-key-0009\n' > "$P/yk2/secrets/hubspot-key.txt"
    run_case rrc-y-keyfile-2line rrc 2 'refus' - y -- "$PY" "$RRC" --config "$P/yk2/real-run.env"
    mkcfg yks $DEAD DESK_PORT="$PORT_X"
    printf 'mk1\n' > "$P/yks/secrets/hubspot-key.txt"
    run_case rrc-y-keyfile-short rrc 2 'refus' - y -- "$PY" "$RRC" --config "$P/yks/real-run.env"
    GROUPSTRAY=deny
  fi

  # ---------------- scripts/run_live_check.py ----------------
  mkdir -p "$P/lv"; printf 'made-up-key-0001\n' > "$P/lv/k.txt"; printf 'made-up-key-0001\nmade-up-key-0009\n' > "$P/lv/k2.txt"
  local LB="--ledger $P/lv/ledger.jsonl --cap-run 0.50 --cap-total 3 --price-date 2026-01-01 --model made-up-model-1=1,5"
  run_case rlc-help rlc 0 'usage: run_live_check.py' - null -- "$PY" "$RLC" --help
  run_case rlc-noargs rlc 2 'arguments are required' - null -- "$PY" "$RLC"
  run_case rlc-public-url rlc 2 "not the provider's own address" - null -- "$PY" "$RLC" --key-file "$P/lv/k.txt" --base-url https://192.0.2.1 $LB
  run_case rlc-http-public rlc 2 'loopback address only' - null -- "$PY" "$RLC" --key-file "$P/lv/k.txt" --base-url http://192.0.2.1 $LB
  run_case rlc-cap-run-over-total rlc 2 'above DESK_LIVE_CAP_TOTAL_USD' - null -- "$PY" "$RLC" --key-file "$P/lv/k.txt" --base-url http://127.0.0.1:9 --ledger "$P/lv/l" --cap-run 5 --cap-total 3 --price-date 2026-01-01 --model m=1,5
  run_case rlc-bad-model rlc 2 'needs ID=IN_PRICE,OUT_PRICE' - null -- "$PY" "$RLC" --key-file "$P/lv/k.txt" --ledger "$P/lv/l" --cap-run 1 --cap-total 3 --price-date 2026-01-01 --model m=abc
  run_case rlc-leads0 rlc 2 'at least 1' - null -- "$PY" "$RLC" --key-file "$P/lv/k.txt" --leads 0 --base-url http://127.0.0.1:9 $LB
  run_case rlc-answer-n rlc 1 'stopped, nothing was called' - n -- "$PY" "$RLC" --key-file "$P/lv/k.txt" --base-url http://127.0.0.1:9 $LB
  run_case rlc-eof-prompt rlc 1 'stopped, nothing was called' - null -- "$PY" "$RLC" --key-file "$P/lv/k.txt" --base-url http://127.0.0.1:9 $LB
  run_case rlc-n-keyfile-missing rlc 2 'refus' - n -- "$PY" "$RLC" --key-file "$P/lv/none.txt" --base-url http://127.0.0.1:9 $LB
  run_case rlc-n-keyfile-2line rlc 1 'stopped, nothing was called' - n -- "$PY" "$RLC" --key-file "$P/lv/k2.txt" --base-url http://127.0.0.1:9 $LB

  # ---------------- scripts/hubspot_probe.py (never the real path: always --plan, a refusal, or a loopback stub) ----
  run_case hsp-help hsp 0 'usage:' - null -- "$PY" -I "$HSP" --help
  run_case hsp-plan hsp 0 'planned calls: 7' - null -- "$PY" -I "$HSP" --plan
  run_case hsp-confirm-missing hsp 2 'pass --yes-spend-calls 7' - null -- "$PY" -I "$HSP"
  run_case hsp-confirm-6 hsp 2 'pass --yes-spend-calls 7' - null -- "$PY" -I "$HSP" --yes-spend-calls 6
  run_case hsp-confirm-abc hsp 2 'bad arguments' - null -- "$PY" -I "$HSP" --yes-spend-calls abc
  EXTRA=()
  run_case hsp-token-unset hsp 2 'missing, empty or not a single token' - null -- "$PY" -I "$HSP" --yes-spend-calls 7 --token-env NOT_SET_VAR_XYZ
  run_case hsp-token-name-is-token hsp 2 'NAME of an environment variable' - null -- "$PY" -I "$HSP" --yes-spend-calls 7 --token-env made-up-key-0001
  EXTRA=(MADEUP_TOKEN="made-up-key-0001 x")
  run_case hsp-token-with-space hsp 2 'not a single token' - null -- "$PY" -I "$HSP" --yes-spend-calls 7 --token-env MADEUP_TOKEN
  EXTRA=(MADEUP_TOKEN=made-up-key-0001)
  run_case hsp-dryrun-nonloopback hsp 2 'loopback http address' - null -- "$PY" -I "$HSP" --yes-spend-calls 7 --token-env MADEUP_TOKEN --dry-run http://192.0.2.1:9
  run_case hsp-dryrun-https hsp 2 'loopback http address' - null -- "$PY" -I "$HSP" --yes-spend-calls 7 --token-env MADEUP_TOKEN --dry-run https://127.0.0.1:9
  run_case hsp-dryrun-userinfo hsp 2 'loopback http address' - null -- "$PY" -I "$HSP" --yes-spend-calls 7 --token-env MADEUP_TOKEN --dry-run 'http://127.0.0.1@192.0.2.1:9'
  run_case hsp-dryrun-dead-port hsp 1 'calls used' - null -- "$PY" -I "$HSP" --yes-spend-calls 7 --token-env MADEUP_TOKEN --dry-run http://127.0.0.1:9
  run_case hsp-token-as-argument hsp 2 'bad arguments' - null -- "$PY" -I "$HSP" --token made-up-key-0001
  run_case hsp-abbreviation hsp 2 'bad arguments' - null -- "$PY" -I "$HSP" --pla
  local mode pf sp want rxm
  for mode in 'happy|0|calls used: 7 of 8' 'owners403|1|owners readable +FAIL' 'echo|1|bad \*\*\*' 'createlost|1|delete +PASS'; do
    name="${mode%%|*}"; want="${mode#*|}"; rxm="${want#*|}"; want="${want%%|*}"
    pf="$P/probe-$name.port"; rm -f "$pf" "$pf.log"
    "$PY" "$STUB" "$name" "$pf" made-up-key-0001 & sp=$!; BG="$BG $sp"
    local i; for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do [ -s "$pf" ] && break; sleep 0.2; done
    run_case "hsp-stub-$name" hsp "$want" "$rxm" - null -- "$PY" -I "$HSP" --yes-spend-calls 7 --token-env MADEUP_TOKEN --dry-run "http://127.0.0.1:$(cat "$pf")"
    if [ "$name" = happy ]; then
      if [ "$(tr '\n' ' ' < "$pf.log")" = "tag owners create patch patch readback gdpr " ]; then record hsp-stub-happy-callorder hsp "7 calls in plan order" "ok" 1 "" "$P/out/hsp-stub-happy.txt" "(stub log)"
      else record hsp-stub-happy-callorder hsp "7 calls in plan order" "$(tr '\n' ' ' < "$pf.log")" 0 "call order differs" "$P/out/hsp-stub-happy.txt" "(stub log)"; fi
    fi
    kill "$sp" 2>/dev/null; wait "$sp" 2>/dev/null
  done
  EXTRA=()

  # ---------------- desk settings refusals (exit 4 per docs/settings.md) ----------------
  mkdir -p "$P/dk"
  EXTRA=(PYTHONPATH="$REPO/src:$REPO" DESK_DB_PATH=":memory:")
  run_case dsk-memory-refused2 dsk 4 "lead book must be a file" - null -- timeout 10 "$PY" -m lead_desk.server
  EXTRA=(PYTHONPATH="$REPO/src:$REPO" DESK_PORT=99999 DESK_DB_PATH="$P/dk/e.db")
  run_case dsk-port-refused dsk 4 'DESK_PORT must be between 0 and 65535' - null -- timeout 10 "$PY" -m lead_desk.server
  EXTRA=(PYTHONPATH="$REPO/src:$REPO" DESK_BIND=0.0.0.0 DESK_CRM=hubspot DESK_DB_PATH="$P/dk/e.db")
  run_case dsk-bind-with-real-service dsk 4 'not a loopback address while a real service' - null -- timeout 10 "$PY" -m lead_desk.server
  EXTRA=(PYTHONPATH="$REPO/src:$REPO" DESK_FAKES_HOST=192.0.2.1 DESK_DB_PATH="$P/dk/e.db")
  run_case dsk-fakes-host-nonloopback dsk 4 'must be this computer' - null -- timeout 10 "$PY" -m lead_desk.server
  EXTRA=()
  [ -e "$P/dk/e.db" ] && record dsk-no-db-on-refusal dsk "no db file" "db created" 0 "a refused start made a file" "$P/out/dsk-port-refused.txt" "(listing)"

  # ---------------- reset_check.py, reset.sh, start_all.sh in a COPY of the repo ----------------
  local RC="$P/repocopy"; mkdir -p "$RC"; cp -r "$REPO/src" "$REPO/scripts" "$REPO/demo_only" "$REPO/load_tools" "$RC/"
  ln -sfn "$RC" "$T/repocopy"
  local ENVD=(DESK_PORT="$PORT_D" DESK_FAKES_PORT="$PORT_F")
  EXTRA=("${ENVD[@]}" PYTHONPATH="src:."); GROUPSTRAY=allow
  # (cwd for these is $P/cwd; use bash -c with cd into the copy)
  rcase() { local id="$1" want="$2" rx="$3"; shift 3; run_case "$id" rst "$want" "$rx" - null -- bash -c "cd '$RC' || exit 9; $*"; }
  rcase rck-clean 0 - "$PY scripts/reset_check.py"
  rcase rck-memory-no-stray 0 - "DESK_DB_PATH=':memory:' $PY scripts/reset_check.py; test ! -e ':memory:.lock' && test ! -e ':memory:'"
  local LST; LST="python3 -c \"import socket,time;s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',$PORT_F));s.listen(1);time.sleep(5)\""
  rcase rck-port-answers 4 'still answers on port' "$LST & sleep 1; $PY scripts/reset_check.py; rc=\$?; kill %1 2>/dev/null; wait 2>/dev/null; exit \$rc"
  EXTRA=("${ENVD[@]}");
  rcase start-bad-mode 1 'mode must be keyed or blind' "bash scripts/start_all.sh bogus"
  rcase start-ok 0 'started: demo servers' "PATH='$SAFE_PATH' bash scripts/start_all.sh keyed"
  sleep 3
  rcase start-desk-answers 0 '"received": 0' "curl -s --noproxy '*' -m 3 http://127.0.0.1:$PORT_D/counts"
  rcase start-again-refused 1 'pid files exist' "bash scripts/start_all.sh keyed"
  EXTRA=("${ENVD[@]}" PYTHONPATH="src:.")
  rcase rck-lock-held 3 'still holds the database' "$PY scripts/reset_check.py"
  EXTRA=("${ENVD[@]}")
  rcase reset-stops-and-deletes 0 'reset done' "bash scripts/reset.sh; test -z \"\$(ls -A data)\""
  rcase reset-twice 0 'reset done' "bash scripts/reset.sh"
  rcase reset-wait-empty-means-10 0 'reset done' "RESET_STOP_WAIT_SECONDS= bash scripts/reset.sh"
  rcase reset-wait-08 2 'whole number of seconds from 0 to 999' "RESET_STOP_WAIT_SECONDS=08 bash scripts/reset.sh"
  rcase reset-wait-1000 2 'whole number of seconds from 0 to 999' "RESET_STOP_WAIT_SECONDS=1000 bash scripts/reset.sh"
  rcase reset-db-outside-data 2 'not inside this repository' "DESK_DB_PATH='$P/elsewhere/d.sqlite3' bash scripts/reset.sh"
  rcase reset-foreign-pid 6 'is not the desk or the demo server' "mkdir -p data; sleep 30 & echo \$! > data/desk.pid; bash scripts/reset.sh; rc=\$?; kill %1 2>/dev/null; wait 2>/dev/null; rm -f data/desk.pid; exit \$rc"
  EXTRA=(); GROUPSTRAY=deny
  # ports freed, nothing of ours left running
  if "$PY" -c "
import socket,sys
for p in ($PORT_D,$PORT_F,$PORT_X):
    try:
        socket.create_connection(('127.0.0.1',p),timeout=0.5).close(); sys.exit(1)
    except OSError: pass"; then record ports-freed rst "all closed" "all closed" 1 "" "$P/out/reset-twice.txt" "(connect to the ports used)"
    else record ports-freed rst "all closed" "a port answers" 0 "" "$P/out/reset-twice.txt" "(connect to the ports used)"; fi
  if command -v pwsh >/dev/null 2>&1; then :; else
    printf 'reset.ps1/start_all.ps1\trst\t-\t-\tSKIPPED\tno pwsh on this machine; only read (tests/test_reset_ps1_links.py covers the text)\t-\n' >> "$TSV"; echo "SKIPPED reset.ps1 / start_all.ps1 (no pwsh)"
  fi
}

declare -A NORM
for PASSNO in $(seq 1 "$PASSES"); do
  if [ "$PASSNO" = 1 ]; then rm -f "$EVDIR"/evidence-q4-*.txt; fi
  do_pass
  mkdir -p "$T/norm$PASSNO"; cp "$P"/norm-*.txt "$T/norm$PASSNO/" 2>/dev/null
done

# repeatability: pass 2 output (normalised) must equal pass 1 output for every case except those with timing/ids
if [ "$PASSES" -ge 2 ]; then
  echo "===== repeatability (pass 1 vs pass 2, normalised) ====="
  for f in "$T"/norm1/norm-*.txt; do
    b="$(basename "$f")"
    if [ -f "$T/norm2/$b" ] && ! diff -q "$f" "$T/norm2/$b" >/dev/null; then
      case "$b" in
        norm-rrc-dry-fakes*.txt) # the self-test table text carries run-specific counts: compare PASS/FAIL columns only
          if diff -q <(grep -E '^(F?[0-9]+) +(PASS|FAIL)|CHECKS' "$f" | sed 's/[0-9]*//g' | awk '{print $1,$2}') <(grep -E '^(F?[0-9]+) +(PASS|FAIL)|CHECKS' "$T/norm2/$b" | sed 's/[0-9]*//g' | awk '{print $1,$2}') >/dev/null; then continue; fi;;
      esac
      echo "NOT REPEATABLE: $b"; diff "$f" "$T/norm2/$b" | head -6
      printf '%s\trepeat\t-\t-\tFAIL\tnot repeatable\t-\n' "${b%.txt}" >> "$TSV"; FAILS=$((FAILS+1))
    fi
  done
fi

echo "====="
echo "cases run (all passes): $CASES   FAIL: $FAILS   FAIL(known): $KNOWN_FAILS"
echo "evidence: $EVDIR/evidence-q4-*.txt   table: $TSV"
if [ "$FAILS" -gt 0 ]; then exit 1; fi
if [ "$KNOWN_FAILS" -gt 0 ] && [ "$ALLOW_KNOWN" != 1 ]; then exit 1; fi
exit 0
