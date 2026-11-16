#!/bin/bash
# The take check: runs the checker on the real-v5 flows only and prints the open decisions FIRST.
# Usage: bash take_check.sh   (from any folder). Exit status = the checker's (0 = no FAIL, 1 = FAIL, 2 = bad command line, 3 = the checker itself broke).
# film-v5 is NOT FOR THE TAKE and is not checked here.
# The table definition the take needs is demo/n8n-flows-v4/mf_leads.sql (it has the four alert columns; the older table in demo/n8n-flows lacks them).
HERE=$(cd "$(dirname "$0")" && pwd); D="$HERE/../../demo/n8n-flows-real-v5"
OUT=$(mktemp /tmp/take-check.XXXXXX) || exit 3
trap 'rm -f -- "$OUT"' EXIT
DDL="$HERE/../../demo/n8n-flows-v4/mf_leads.sql"
if [ ! -f "$DDL" ]; then DDL=$(find "$HERE/../.." -name mf_leads.sql -path '*n8n-flows-v4*' -not -path '*/scratch/*' 2>/dev/null | head -n 1); fi
DDLOPT=(); [ -n "$DDL" ] && [ -f "$DDL" ] && DDLOPT=(--ddl "$DDL")
python3 -I "$HERE/check_flows.py" "$D" "${DDLOPT[@]}" \
  --accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 \
  --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 \
  --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token \
  --quiet-info > "$OUT" 2>&1
RC=$?
echo "=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ==="
echo "=== OPEN LEAD DECISIONS (read before anything else) ==="
grep -h -E '^(OPEN LEAD DECISIONS|No static tool|IF branches accepted|SQL COLUMNS NOT CHECKED|SQL columns compared)' "$OUT"
awk '/^PLACEHOLDERS IN NODE SETTINGS/ {p=1; print; next} p && /^  - / {print; next} {p=0}' "$OUT"
if [ ${#DDLOPT[@]} -eq 0 ]; then
  echo "WARNING: the table definition file (n8n-flows-v4/mf_leads.sql) was not found, so the column names in the SQL steps were NOT checked. On the older table the alert steps would fail on every run and no alert would be sent."
else
  echo "Table definition used for the column check: demo/n8n-flows-v4/mf_leads.sql. The take needs THAT table (with the four alert columns), not the older one in demo/n8n-flows."
fi
echo "GATE BEFORE THE FIRST SEND (decided by the lead, order Q16): the take uses demo/n8n-flows-v4/mf_leads.sql. In psql, run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out. This script cannot see your database."
if ! grep -q '"KeyOk"' "$D/mf-form.json" "$D/mf-hook.json" 2>/dev/null; then
  echo "These files do NOT contain F-002 (the check that a lead key is well formed, the answer for a bad key, and the answer when the table write fails) or F-008 (saving of past runs, so the run list in n8n shows what happened). Apply both patches first if the take should show them."
fi
echo "Environment variables that n8n must hold for these files: $(grep -h -o '\$env\.[A-Za-z0-9_]*' "$D"/*.json | sort -u | sed 's/^\$env\.//' | tr '\n' ' ')"
echo "Two steps of real-v5 read environment variables (the \$env form): if n8n on the filming machine blocks that, they stop working. No file check can see that setting."
echo "To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 below does NOT mean authentication was checked."
echo "=== full checker output ==="
cat "$OUT"
echo "take_check exit status: $RC"
exit $RC
