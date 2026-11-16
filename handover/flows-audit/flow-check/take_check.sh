#!/bin/bash
# The take check: runs the checker on the real-v5 flows only and prints what a person must read FIRST (top block), then the full checker output.
# Usage: bash take_check.sh   (from any folder).
# Exit status of this script (decided 2026-11-16, round 6):
#   0 = the checker found no definite fault AND the table file was found AND at least one SQL query was compared AND no column or table is missing. It is NOT "ready to film": see the last line.
#   1 = the checker found at least one FAIL (a definite fault in a file).
#   2 = the checker was started wrongly (bad command line, for example the table file cannot be read).
#   3 = the checker itself broke.
#   4 = the checker found no FAIL, but a check this take depends on did not happen or found a mismatch: the table file demo/n8n-flows-v4/mf_leads.sql is missing, OR 0 query strings were read, OR a query uses a column or table that file does not define, OR a postgres step has no query text (its columns were not compared), OR a flow other than the recovery flow still has run saving off (the take shows the run list, so run saving must be ON: that is the case on the committed real-v5 folder until patch F-008 is applied; the take runs on the patched copy, decision Q17-4/Q18), OR the recorded accept for the recovery flow excused nothing.
# The recovery flow (exact file name mf-recovery.json, nothing else) keeps run saving off on purpose: it fires every 30 s and the one video makes no recovery claim (decision 4). It is printed as an ACCEPTED line, not a WARN. No blanket accept exists in this script.
# film-v5 is NOT FOR THE TAKE and is not checked here.
# The table definition the take needs is demo/n8n-flows-v4/mf_leads.sql (lead decision, order Q16). It is looked up at that exact path only (no search for a file of the same name elsewhere).
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE/../.." || exit 3   # the handover folder: paths printed below are short and relative to it
D="${TAKE_CHECK_FLOWS:-demo/n8n-flows-real-v5}"   # TAKE_CHECK_FLOWS and TAKE_CHECK_DDL (absolute paths) exist only so run_all.sh can test the failure exits; the take uses the defaults. TAKE_CHECK_CK (another checker script) and TAKE_CHECK_FORM_EXPECT exist only for selftest.py and run_all.sh
OUT=$(mktemp /tmp/take-check.XXXXXX) || exit 3
trap 'rm -f -- "$OUT"' EXIT
DDL="${TAKE_CHECK_DDL:-demo/n8n-flows-v4/mf_leads.sql}"
FORMCNT="${TAKE_CHECK_FORM_EXPECT:-12:11}"   # node:connection count of mf-form and mf-hook; run_all.sh sets 15:14 for the patched copy (F-002 adds 3 nodes); the take uses the default only for the unpatched files
DDLOPT=(); [ -f "$DDL" ] && DDLOPT=(--ddl "$DDL")
python3 -I "${TAKE_CHECK_CK:-$HERE/check_flows.py}" "$D" "${DDLOPT[@]}" \
  --accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 \
  --accept-no-save mf-recovery.json \
  --expect mf-form.json="$FORMCNT" --expect mf-hook.json="$FORMCNT" --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 \
  --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token \
  --quiet-info > "$OUT" 2>&1
RC=$?
PROBLEMS=()   # things this script itself found wrong (each one makes the exit status 4 when the checker exited 0)
echo "=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ==="
if [ "$RC" -ge 2 ]; then
  echo "=== THE CHECKER DID NOT GIVE A VERDICT (its exit status is $RC: 2 = started wrongly, 3 = broke). Nothing below says anything about the flows. ==="
  cat "$OUT"
  echo "FINAL: take_check exit status $RC. exit 0 would have meant: no definite fault in the files; NOTHING ran in n8n. The checker gave no verdict; open items: unknown."
  exit "$RC"
fi
echo "=== READ THIS BLOCK BEFORE ANYTHING ELSE ==="
echo "--- (1) The lead table and the column check ---"
QN=$(sed -n 's/^SQL columns compared with the --ddl file: \([0-9][0-9]*\) query string.*/\1/p' "$OUT" | head -n 1)
COLW=$(sed -n 's/^SQL WARNS: column WARNs=\([0-9]*\) .*/\1/p' "$OUT" | head -n 1)
TBLW=$(sed -n 's/^SQL WARNS: .* table WARNs=\([0-9]*\) .*/\1/p' "$OUT" | head -n 1)
NOQ=$(sed -n 's/^SQL WARNS: .*(not compared)=\([0-9]*\).*/\1/p' "$OUT" | head -n 1)
if [ ${#DDLOPT[@]} -eq 0 ]; then
  echo "!!! THE TABLE FILE IS MISSING: demo/n8n-flows-v4/mf_leads.sql was not found, so the column names in the SQL steps were NOT checked. On the older table the alert steps fail on every run and no alert is sent. This script exits 4."
  PROBLEMS+=("table file missing")
else
  echo "Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql (the take needs THAT table, with the four alert columns, not the older one in demo/n8n-flows)."
  echo "Query strings read: ${QN:-unknown}. Column WARNs: ${COLW:-unknown}. Table WARNs: ${TBLW:-unknown}. Postgres steps with no query text (not compared): ${NOQ:-unknown}."
  if [ -z "$QN" ] || [ "$QN" -eq 0 ]; then
    echo "!!! 0 QUERY STRINGS WERE READ (or the count line is missing): NO column was compared. This script exits 4."
    PROBLEMS+=("0 queries read")
  fi
  if [ "${COLW:-1}" -gt 0 ] || [ "${TBLW:-1}" -gt 0 ] || [ "${NOQ:-1}" -gt 0 ]; then
    echo "!!! A COLUMN OR TABLE IS MISSING, or a step was not compared (counts above, WARN lines further down): the alert or lead steps would fail on every run. This script exits 4."
    PROBLEMS+=("column/table WARN")
  fi
fi
echo "GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out."
echo "--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---"
grep -h -E '^mf-[a-z-]+\.json nodes=' "$OUT"
grep -h -E '^mf-[a-z-]+\.json nodes=.* saveDataSuccess=all saveDataError=all saveManual=True$' "$OUT" | sed -E 's/^(mf-[a-z-]+\.json) .*/INFO: \1 run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names and must be deleted at clean-up./'
grep -h -E "^WARN .*run-saving settings" "$OUT" | cut -c1-260
grep -h -E "^WARN accept-no-save" "$OUT" | cut -c1-260
grep -h -E "^ACCEPTED: " "$OUT" | cut -c1-300
if grep -q -E "^WARN .*run-saving settings|^WARN accept-no-save" "$OUT"; then
  echo "!!! A FLOW THAT THE TAKE USES HAS RUN SAVING OFF (or the recorded accept for the recovery flow excused nothing): the run list in n8n stays empty for it. Apply patch F-008 to the flows first. This script exits 4."
  PROBLEMS+=("run saving off")
fi
echo "--- (3) Values that must be filled in before import: mail addresses and credential ids ---"
awk '/^(PLACEHOLDERS IN NODE SETTINGS|CREDENTIAL IDS STILL PLACEHOLDERS)/ {p=1; print; next} p && /^  - / {print; next} {p=0}' "$OUT"
echo "--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---"
NOKEY=0
for f in mf-form.json mf-hook.json; do
  # the node list is read as JSON (a text match would also hit a leftover connection that names KeyOk)
  if python3 -I -c 'import json,sys; sys.exit(0 if any(n.get("name") == "KeyOk" for n in json.load(open(sys.argv[1], encoding="utf-8"))["nodes"]) else 1)' "$D/$f" 2>/dev/null; then echo "$f: key check present (F-002 applied)"; else echo "$f: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially)"; NOKEY=$((NOKEY+1)); fi
done
echo "--- (5) Open decisions and environment variables ---"
grep -h -E '^(OPEN LEAD DECISIONS|No static tool|IF branches accepted)' "$OUT"
awk '/^STEPS THAT READ ENVIRONMENT VARIABLES/ {p=1; print; next} p && /^  - / {print; next} {p=0}' "$OUT"
echo "If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked."
echo "=== end of top block; full checker output follows ==="
cat "$OUT"
KNOWN=$(sed -n 's/^Known open problems: \([0-9][0-9]*\).*/\1/p' "$OUT" | head -n 1)
OPEN=$(( ${KNOWN:-0} + NOKEY + 1 + ${#PROBLEMS[@]} ))   # the checker's own count, files without KeyOk, the psql gate (always a person's step), what this script found wrong
if [ "$RC" -eq 0 ] && [ ${#PROBLEMS[@]} -gt 0 ]; then RC=4; fi
echo "Open items counted: checker known open problems ${KNOWN:-0} + files without the key check $NOKEY + psql gate 1 + problems of this script ${#PROBLEMS[@]}."
echo "FINAL: take_check exit status $RC. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: $OPEN. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming."
exit $RC
