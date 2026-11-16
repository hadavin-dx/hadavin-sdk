#!/bin/bash
# F8 runner (round 3). Usage: bash run_all.sh [--strict] [WORKDIR]
#   --strict : also pass --require-real-credential-ids to the default-mode runs, so a credential id or sub-workflow id that is still a placeholder makes this script exit 1.
#   Last line printed is always 'OPEN LEAD DECISIONS: n webhook(s) without auth, m $env node(s)' (committed flows, real + film): exit 0 does NOT mean authentication was checked.
# Default WORKDIR is /tmp/fc8 (this script deletes and recreates ONLY that exact default folder). Any other WORKDIR must not exist yet or must be empty; it is never deleted.
# What it does (nothing is run in n8n):
#   1. copies the committed real-v5 flows to a scratch folder, applies patch F-002 then F-008 there, runs the flow generator for "real" and "film"
#   2. runs the checker on the committed folders (pristine) and on the generated patched folders, in two modes each:
#        default mode            : exit status of these 4 runs decides this script's exit status (must be 0)
#        strict mode             : --require-webhook-auth --block-env-access (the owner decides these two; expected to exit 1 today; only exit codes other than 0 or 1 count as failure)
#   3. runs selftest.py (exit status counts)
# Raw output of every step goes to ./raw/ (apply and generator logs, patched flow list with sha256, checker output, diffs, self-test output).
# Exit status: 0 only if every default-mode run and the self-test exit 0 and no step aborted. Exit 3 = a build step aborted, 2 = usage/bad folder.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); D="$HERE/../../demo"; PT="$HERE/../patches"; CK="$HERE/check_flows.py"; RAW="$HERE/raw"
DEFAULT_W=/tmp/fc8
STRICT_IDS=""; ARGS=()
for a in "$@"; do if [ "$a" = "--strict" ]; then STRICT_IDS="--require-real-credential-ids"; else ARGS+=("$a"); fi; done
W=${ARGS[0]:-$DEFAULT_W}
if [ "$W" = "$DEFAULT_W" ]; then rm -rf -- "$DEFAULT_W"
elif [ -e "$W" ] && [ -n "$(ls -A -- "$W" 2>/dev/null)" ]; then echo "REFUSED: $W exists and is not empty; this script only deletes its own default folder $DEFAULT_W"; exit 2; fi
mkdir -p -- "$W/c/handover/demo/n8n-flows" "$W/c/handover/demo/n8n-mainframe" "$W/g" "$RAW" || exit 2
cp -- "$D"/n8n-flows/*.json "$D/n8n-flows/mf_leads.sql" "$D/n8n-flows/PAGE-STATEMENTS-V4.md" "$W/c/handover/demo/n8n-flows/" || exit 2
cp -- "$D/VIDEO-RUNSHEET.md" "$W/c/handover/demo/" && cp -- "$D/n8n-mainframe/build_mainframe.py" "$W/c/handover/demo/n8n-mainframe/" || exit 2
: > "$RAW/apply.log"
( cd "$W/c" && git init -q . 2>/dev/null; true )
for p in F-002-take-key-check-and-claim-error-path F-008-save-runs-for-the-take; do
  ( cd "$W/c" && git apply --check "$PT/$p.patch" && git apply "$PT/$p.patch" ) >> "$RAW/apply.log" 2>&1 || { echo "ABORT: git apply $p (see raw/apply.log)"; exit 3; }
  echo "applied $p" | tee -a "$RAW/apply.log"
done
cd "$W/c/handover/demo/n8n-mainframe" || exit 3
MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py "$W/g/real" PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER > "$RAW/gen-real.log" 2>&1 || { echo "ABORT gen real (raw/gen-real.log)"; exit 3; }
MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py "$W/g/film" PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 > "$RAW/gen-film.log" 2>&1 || { echo "ABORT gen film (raw/gen-film.log)"; exit 3; }
( cd "$W/g" && find . -type f | sort | while read -r f; do printf '%s  %s\n' "$(sha256sum "$f" | cut -c1-16)" "$f"; done ) > "$RAW/patched-flows-list.txt"
cd "$HERE" || exit 3
E="--expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token $STRICT_IDS"
STRICT="--require-webhook-auth --block-env-access"
T0=$(date +%s)
# one background process per (state, mode); each writes its own file and its own exit code file
run_set() { # name state-dir extra-args...
  name=$1; shift
  ( for v in real film; do
      echo "######## $name $v"
      if [ "$name" = pristine ] || [ "$name" = pristine-strict ]; then
        timeout 300 python3 -I "$CK" "$D/n8n-flows-$v-v5" --baseline "$D/n8n-flows-$v-v5" --expect mf-form.json=12:11 --expect mf-hook.json=12:11 $E --table "$@"; echo "exit=$?"
      else
        timeout 300 python3 -I "$CK" "$W/g/$v" --baseline "$D/n8n-flows-$v-v5" --expect mf-form.json=15:14 --expect mf-hook.json=15:14 $E --patch-checks F002,F008 --diff-base "$D/n8n-flows-$v-v5" --allow F002,F008 --diff-out "$RAW/diff-$v.txt" --table "$@"; echo "exit=$?"
      fi
    done ) > "$RAW/$name.txt" 2>&1
}
run_set pristine & P1=$!
run_set patched & P2=$!
run_set pristine-strict $STRICT & P3=$!
run_set patched-strict $STRICT & P4=$!
wait $P1; wait $P2; wait $P3; wait $P4
T1=$(date +%s)
python3 -I "$HERE/selftest.py" "$D/n8n-flows-real-v5" "$W/g/real" "$D/n8n-flows-film-v5" > "$RAW/selftest-new.txt" 2>&1; ST=$?
T2=$(date +%s)
echo "checker runs wall time: $((T1-T0)) s; self-test wall time: $((T2-T1)) s" | tee "$RAW/timing.txt"
RC=0
for f in pristine patched; do
  for x in $(grep -h '^exit=' "$RAW/$f.txt" | cut -d= -f2); do [ "$x" = 0 ] || RC=1; done
  [ "$(grep -c '^exit=' "$RAW/$f.txt")" = 2 ] || RC=1
done
for f in pristine-strict patched-strict; do
  for x in $(grep -h '^exit=' "$RAW/$f.txt" | cut -d= -f2); do case $x in 0|1) ;; *) RC=1;; esac; done
  [ "$(grep -c '^exit=' "$RAW/$f.txt")" = 2 ] || RC=1
done
[ "$ST" = 0 ] || RC=1
echo "---- summary (default mode must be exit 0; strict mode shows what the owner's two open decisions would do) ----"
for f in pristine patched pristine-strict patched-strict; do echo "[$f]"; grep -h -E '^(######## |exit=|RESULT|Known open problems)' "$RAW/$f.txt"; done
echo "[selftest exit=$ST] $(tail -n 1 "$RAW/selftest-new.txt")"
echo "run_all exit status: $RC"
echo "placeholder ids: $(grep -h -c 'still placeholders' "$RAW/pristine.txt" | head -1) file(s) warn in the committed flows (pass --strict to make that a failure)"
LW=$(grep -h '^OPEN LEAD DECISIONS:' "$RAW/pristine.txt" | sed -E 's/OPEN LEAD DECISIONS: ([0-9]+) webhook.* ([0-9]+) \$env.*/\1 \2/' | awk '{w+=$1; e+=$2} END {print w+0, e+0}')
echo "OPEN LEAD DECISIONS: ${LW% *} webhook(s) without auth, ${LW#* } \$env node(s)"
exit $RC
