#!/bin/bash
# The take check: runs the checker on the real-v5 flows only and prints the open decisions FIRST.
# Usage: bash take_check.sh   (from any folder). Exit status = the checker's (0 = no FAIL, 1 = FAIL, 2 = bad command line, 3 = the checker itself broke).
# film-v5 is NOT FOR THE TAKE and is not checked here.
HERE=$(cd "$(dirname "$0")" && pwd); D="$HERE/../../demo/n8n-flows-real-v5"
OUT=$(mktemp /tmp/take-check.XXXXXX) || exit 3
trap 'rm -f -- "$OUT"' EXIT
python3 -I "$HERE/check_flows.py" "$D" \
  --accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 \
  --expect mf-form.json=12:11 --expect mf-hook.json=12:11 --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 \
  --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token \
  --quiet-info > "$OUT" 2>&1
RC=$?
echo "=== OPEN LEAD DECISIONS (read before anything else) ==="
grep -h -E '^(OPEN LEAD DECISIONS|No static tool|IF branches accepted)' "$OUT"
echo "Two steps of real-v5 read environment variables (the \$env form): if n8n on the filming machine blocks that, they stop working. No file check can see that setting."
echo "To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 below does NOT mean authentication was checked."
echo "=== full checker output ==="
cat "$OUT"
echo "take_check exit status: $RC"
exit $RC
