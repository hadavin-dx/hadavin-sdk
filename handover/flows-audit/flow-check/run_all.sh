#!/bin/bash
# F8 runner (round 6). Usage: bash run_all.sh [--strict] [WORKDIR]
# THE TAKE USES real-v5 ONLY (lead decision 2026-11-16). This script's exit status and its last line are about real-v5 only.
# film-v5 is NOT FOR THE TAKE: it is run and shown in its own block, it never changes the exit status and its numbers are never added to the real-v5 numbers.
#   --strict : also pass --require-real-credential-ids to the default-mode runs, so a credential id or sub-workflow id that is still a placeholder makes this script exit 1.
#   Last line printed is always 'OPEN LEAD DECISIONS (real-v5, the take): n webhook(s) without auth, m $env node(s)' (or 'unknown' when a checker run is missing): exit 0 does NOT mean authentication was checked.
# Default WORKDIR is a new folder made with mktemp (removed again when the script ends; it is a folder this script made itself). Any other WORKDIR must not exist yet or must be empty; it is never deleted.
# What it does (nothing is run in n8n):
#   1. copies the committed real-v5 flows to a scratch folder, applies patch F-002 then F-008 there, runs the flow generator for "real" and "film"
#   2. runs the checker on the committed folders (pristine) and on the generated patched folders, in two modes each, for real-v5 (gating) and film-v5 (shown only):
#        default mode : exit status of the 2 real-v5 runs decides this script's exit status (must be 0). The two known IF branch gaps are recorded with --accept-if (not a self-baseline).
#        strict mode  : --require-webhook-auth --block-env-access (the owner decides these two; expected to exit 1 today; for real-v5 only exit codes other than 0 or 1 count as failure)
#      plus one informational run of real-v5 pristine without any excuse (raw/pristine-no-baseline.txt, expected exit 1 with 2 FAIL, never gating)
#   3. runs take_check.sh on the PATCHED copy (exit 0 required; on the committed unpatched real-v5 it must exit 4 because run saving is off there) and requires its fixed top-block lines (raw/take-check.txt); the lines about placeholders, credential ids and environment variables are required only while the checker reports them, so this script can exit 0 once the files are fixed and filled; then selftest.py (exit status counts; it also exercises the checker on a film-v5 file, which tests the checker, not the film flows)
# Raw output of every step goes to ./raw/ (files without a suffix = real-v5, files ending -film = film-v5).
# Exit status: 0 only if every real-v5 default-mode run and the self-test exit 0 and no step aborted. Exit 3 = a build step aborted, 2 = usage/bad folder.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); D="$HERE/../../demo"; PT="$HERE/../patches"; CK="$HERE/check_flows.py"; RAW="$HERE/raw"
STRICT_IDS=""; ARGS=()
for a in "$@"; do if [ "$a" = "--strict" ]; then STRICT_IDS="--require-real-credential-ids"; else ARGS+=("$a"); fi; done
if [ -n "${ARGS[0]:-}" ]; then
  W=${ARGS[0]}
  if [ -e "$W" ] && [ -n "$(ls -A -- "$W" 2>/dev/null)" ]; then echo "REFUSED: $W exists and is not empty; this script never deletes a folder it did not make"; exit 2; fi
else
  W=$(mktemp -d /tmp/fc8.XXXXXX) || exit 2
  trap 'rm -rf -- "$W"' EXIT   # only the folder made just above
fi
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
DDLF="$D/n8n-flows-v4/mf_leads.sql"; DDLO=""; [ -f "$DDLF" ] && DDLO="--ddl $DDLF"
E="$DDLO --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token $STRICT_IDS"
ACC="--accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 --accept-no-save mf-recovery.json"
STRICT="--require-webhook-auth --block-env-access"
T0=$(date +%s)
# one background process per (state, mode, flow set); each writes its own file, ending with its own exit code line
run_set() { # name variant state(pristine|patched|bare) extra-args...
  name=$1; v=$2; state=$3; shift 3
  suffix=""; [ "$v" = film ] && suffix="-film"
  out="$RAW/$name$suffix.txt"
  {
    echo "######## $name $v"
    case $state in
      pristine) timeout 300 python3 -I "$CK" "$D/n8n-flows-$v-v5" $ACC --expect mf-form.json=12:11 --expect mf-hook.json=12:11 $E --table "$@";;
      patched)  timeout 300 python3 -I "$CK" "$W/g/$v" $ACC --expect mf-form.json=15:14 --expect mf-hook.json=15:14 $E --patch-checks F002,F008 --diff-base "$D/n8n-flows-$v-v5" --allow F002,F008 --diff-out "$RAW/diff-$v.txt" --table "$@";;
      bare)     timeout 300 python3 -I "$CK" "$D/n8n-flows-$v-v5" --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 --quiet-info "$@";;
    esac
    echo "exit=$?"
  } > "$out" 2>&1
}
for v in real film; do
  run_set pristine $v pristine & 
  run_set patched $v patched &
  run_set pristine-strict $v pristine $STRICT &
  run_set patched-strict $v patched $STRICT &
done
run_set pristine-no-baseline real bare &
wait
T1=$(date +%s)
python3 -I "$HERE/selftest.py" "$D/n8n-flows-real-v5" "$W/g/real" "$D/n8n-flows-film-v5" > "$RAW/selftest-new.txt" 2>&1; ST=$?
T2=$(date +%s)
# the take script itself: exit 0 and the lines the owner must see (a missing line sets this script's exit status to 1)
# the take runs on the PATCHED copy (F-002 and F-008 applied, lead answers Q17-4 and Q18): exit 0 required, and the run-saving block must hold ACCEPTED lines only (no WARN)
TAKE_CHECK_FLOWS="$W/g/real" TAKE_CHECK_FORM_EXPECT=15:14 bash "$HERE/take_check.sh" > "$RAW/take-check.txt" 2>&1; TC=$?
grep -q -E "^WARN .*run-saving settings|^WARN accept-no-save" "$RAW/take-check.txt" && TCMISS="$TCMISS [a run-saving WARN on the patched copy]"
grep -q -F "ACCEPTED: recovery flow not part of the take (decision 4)" "$RAW/take-check.txt" || TCMISS="$TCMISS [ACCEPTED line for the recovery flow]"
TCMISS=""
for w in "NOTHING RAN IN n8n" "READ THIS BLOCK BEFORE ANYTHING ELSE" "Query strings read:" "GATE BEFORE THE FIRST SEND" "Is saving of past runs off" "key check" "FINAL: take_check exit status"; do
  grep -q -F -- "$w" "$RAW/take-check.txt" || TCMISS="$TCMISS [$w]"
done
# lines that exist only while the checker itself reports the matching problem: required when it reports it, not otherwise (so this script can exit 0 on files that are fixed and filled)
grep -q -F "PLACEHOLDERS IN NODE SETTINGS" "$RAW/pristine.txt" && { grep -q -F "PLACEHOLDERS IN NODE SETTINGS" "$RAW/take-check.txt" || TCMISS="$TCMISS [PLACEHOLDERS IN NODE SETTINGS]"; }
grep -q -F "CREDENTIAL IDS STILL PLACEHOLDERS" "$RAW/pristine.txt" && { grep -q -F "CREDENTIAL IDS STILL PLACEHOLDERS" "$RAW/take-check.txt" || TCMISS="$TCMISS [CREDENTIAL IDS STILL PLACEHOLDERS]"; }
grep -q -F "STEPS THAT READ ENVIRONMENT VARIABLES" "$RAW/pristine.txt" && { grep -q -F "STEPS THAT READ ENVIRONMENT VARIABLES" "$RAW/take-check.txt" || TCMISS="$TCMISS [STEPS THAT READ ENVIRONMENT VARIABLES]"; }
for f in mf-form.json mf-hook.json; do grep -q -F "$f: key check" "$RAW/take-check.txt" || TCMISS="$TCMISS [key check line for $f]"; done
grep -q -F "SQL COLUMNS NOT CHECKED" "$RAW/take-check.txt" && TCMISS="$TCMISS [columns not checked]"
grep -q -F "!!!" "$RAW/take-check.txt" && TCMISS="$TCMISS [a !!! line: the take script found a table or column problem]"
# take_check.sh failure exits (each must be 4 with its own loud line): table file missing, old table without the alert columns, no query text to read
mkdir -p "$W/tc" && cp -r -- "$D/n8n-flows-real-v5" "$W/tc/noquery" || TCMISS="$TCMISS [could not make the no-query test folder]"
python3 -I - "$W/tc/noquery" <<'PYEOF' || TCMISS="$TCMISS [no-query test folder not built]"
import glob, json, sys
for p in glob.glob(sys.argv[1] + "/*.json"):
    j = json.load(open(p, encoding="utf-8"))
    for n in j["nodes"]:
        n.get("parameters", {}).pop("query", None)
    json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tcfail() { # name expected-line env-assignments...
  nm=$1; want=$2; shift 2
  env "$@" bash "$HERE/take_check.sh" > "$RAW/take-check-$nm.txt" 2>&1; x=$?
  [ "$x" = 4 ] && grep -q -F -- "$want" "$RAW/take-check-$nm.txt" || TCMISS="$TCMISS [take_check $nm: want exit 4 and '$want', got exit $x]"
}
tcfail unpatched-run-saving "A FLOW THAT THE TAKE USES HAS RUN SAVING OFF"
tcfail no-table-file "THE TABLE FILE IS MISSING" TAKE_CHECK_DDL="$W/tc/does-not-exist.sql"
tcfail old-table "A COLUMN OR TABLE IS MISSING" TAKE_CHECK_DDL="$D/n8n-flows/mf_leads.sql"
tcfail zero-queries "0 QUERY STRINGS WERE READ" TAKE_CHECK_FLOWS="$W/tc/noquery"
echo "checker runs wall time: $((T1-T0)) s; self-test wall time: $((T2-T1)) s" | tee "$RAW/timing.txt"
RC=0
for f in pristine patched; do   # gating: real-v5 default mode, exactly one exit line each
  [ "$(grep -c '^exit=' "$RAW/$f.txt")" = 1 ] || RC=1
  for x in $(grep -h '^exit=' "$RAW/$f.txt" | cut -d= -f2); do [ "$x" = 0 ] || RC=1; done
done
for f in pristine-strict patched-strict; do   # real-v5 strict: 0 or 1 are both fine, anything else (a crash) is not
  [ "$(grep -c '^exit=' "$RAW/$f.txt")" = 1 ] || RC=1
  for x in $(grep -h '^exit=' "$RAW/$f.txt" | cut -d= -f2); do case $x in 0|1) ;; *) RC=1;; esac; done
done
[ "$ST" = 0 ] || RC=1
[ "$TC" = 0 ] && [ -z "$TCMISS" ] || RC=1
show() { for f in "$@"; do echo "[$f]"; grep -h -E '^(######## |exit=|RESULT|Known open problems)' "$RAW/$f.txt"; done; }
echo "==== real-v5 (THE TAKE) ===="
echo "---- default mode must be exit 0; strict mode shows what the owner's two open decisions would do ----"
show pristine patched pristine-strict patched-strict
echo "[pristine-no-baseline] (information only: no excuse for the 2 IF gaps; exit 1 with 2 FAIL is expected)"; grep -h -E '^(exit=|RESULT)' "$RAW/pristine-no-baseline.txt"
echo "==== film-v5 (NOT FOR THE TAKE; shown only, not gating, not added to the real-v5 numbers) ===="
show pristine-film patched-film pristine-strict-film patched-strict-film
echo "[selftest exit=$ST] $(tail -n 1 "$RAW/selftest-new.txt")"
echo "[take_check.sh exit=$TC] missing lines:${TCMISS:- none}"
echo "run_all exit status (real-v5 default runs + self-test): $RC"
echo "real-v5 placeholder ids: $(grep -c 'still placeholders' "$RAW/pristine.txt") file(s) warn in the committed flows (pass --strict to make that a failure)"
LW=$(grep -h '^OPEN LEAD DECISIONS:' "$RAW/pristine.txt" | sed -E 's/OPEN LEAD DECISIONS: ([0-9]+) webhook.* ([0-9]+) \$env.*/\1 \2/')
case $LW in
  [0-9]*\ [0-9]*) echo "OPEN LEAD DECISIONS (real-v5, the take): ${LW% *} webhook(s) without auth, ${LW#* } \$env node(s); n8n's env-access setting is NOT visible to any static check";;
  *) echo "OPEN LEAD DECISIONS (real-v5, the take): unknown (the real-v5 checker run did not finish; see raw/pristine.txt)"; RC=1;;
esac
exit $RC
