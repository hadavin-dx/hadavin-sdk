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
# Round 9 (review f8-design-r3, 4 Majors): (M1) the top block and the FINAL line print RESULT and the WARN count; the set of WARN lines is pinned in take-warns.pin (folder paths removed) and ANY change is exit 4; (M2) every flow except mf-recovery.json must have run saving exactly all / all / True (a missing settings block, a missing key or an odd word is exit 4, not only "none"/false); (M3) a key check that is ABSENT is exit 4, and when both entry flows have it the checker's F-002 content check (--patch-checks F002) runs on them; (M4) the patched copy is detected by the KeyOk node: the node:connection count 15:14 is then expected without any environment variable (12:11 for an unpatched file).
# Round 10 (review f8-r10): (B1) --write-warn-pin refuses a file that exists (so it can never overwrite the pin in use), writes only when the run has no FAIL and a RESULT line, writes AFTER the comparison, prints the difference and always exits 4: a run that writes a pin is never a pass; a person installs the pin by hand (see README). (M1) the top block and the FINAL line print an OVERRIDES line; an environment override (TAKE_CHECK_CK, TAKE_CHECK_WARN_PIN, TAKE_CHECK_FLOWS, TAKE_CHECK_DDL, TAKE_CHECK_FORM_EXPECT) is exit 4 unless the test flag TAKE_CHECK_TEST=1 is set (only selftest and run_all.sh set it); the documented way to check another folder is the option --flows DIR, which is printed. (M3/M5) the checker FAILs a listed flow that is not a regular file; the F-002 content check also asserts the reply steps and lead_key. F-008 content check (--patch-checks F008) is NOT used here: it would turn the planted run-saving cases (exit 4 by design) into exit 1; the exact run-saving check below judges F-008 instead. (M4) the pin header carries a date and the sha256 of the WARN lines; a pin that does not match its own hash is exit 4; the pinned WARN count is printed and said to stand for known defects. (N1-N4) LC_ALL=C sort, helper exit statuses checked, closing-block lines must appear once, absolute paths before the cd, one temp folder removed on exit.
# Usage: bash take_check.sh [--flows DIR] [--write-warn-pin NEWFILE]   (NEWFILE must not exist yet; the pin in use is take-warns.pin next to this script)
LC_ALL=C; export LC_ALL
HERE=$(cd "$(dirname "$0")" && pwd)
USAGE="usage: take_check.sh [--flows DIR] [--write-warn-pin NEWFILE]"
abspath() { case "$1" in /*) printf '%s' "$1";; *) printf '%s/%s' "$PWD" "$1";; esac; }   # before the cd below, so a relative path means what the person typed
WRITEPIN=""; FLOWSARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --write-warn-pin) [ -n "${2:-}" ] || { echo "$USAGE"; exit 2; }; WRITEPIN=$(abspath "$2"); shift 2;;
    --flows) [ -n "${2:-}" ] || { echo "$USAGE"; exit 2; }; FLOWSARG=$(abspath "$2"); shift 2;;
    *) echo "$USAGE"; exit 2;;
  esac
done
OVR=()   # active environment overrides (each one changes what is checked)
for v in TAKE_CHECK_CK TAKE_CHECK_WARN_PIN TAKE_CHECK_FLOWS TAKE_CHECK_DDL TAKE_CHECK_FORM_EXPECT; do
  if [ -n "${!v:-}" ]; then
    case "$v" in TAKE_CHECK_FORM_EXPECT) OVR+=("$v=${!v}");; *) OVR+=("$v=$(abspath "${!v}")");; esac
  fi
done
[ -n "${TAKE_CHECK_CK:-}" ] && TAKE_CHECK_CK=$(abspath "$TAKE_CHECK_CK")
[ -n "${TAKE_CHECK_WARN_PIN:-}" ] && TAKE_CHECK_WARN_PIN=$(abspath "$TAKE_CHECK_WARN_PIN")
[ -n "${TAKE_CHECK_FLOWS:-}" ] && TAKE_CHECK_FLOWS=$(abspath "$TAKE_CHECK_FLOWS")
[ -n "${TAKE_CHECK_DDL:-}" ] && TAKE_CHECK_DDL=$(abspath "$TAKE_CHECK_DDL")
PIN="${TAKE_CHECK_WARN_PIN:-$HERE/take-warns.pin}"   # the expected set of WARN lines for the take (path prefix removed)
if [ -n "$WRITEPIN" ]; then
  if [ -e "$WRITEPIN" ] || [ -L "$WRITEPIN" ] || [ "$WRITEPIN" = "$PIN" ]; then
    echo "REFUSED: $WRITEPIN already exists (or is the pin in use). --write-warn-pin writes a NEW file only, so the pin in use can never be overwritten by the run that is judged against it."; exit 2
  fi
fi
cd "$HERE/../.." || exit 3   # the handover folder: paths printed below are short and relative to it
D="${TAKE_CHECK_FLOWS:-${FLOWSARG:-demo/n8n-flows-real-v5}}"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/take-check.XXXXXX") || exit 3
trap 'rm -rf -- "$TMP"' EXIT
OUT="$TMP/out"; NORM="$TMP/norm"
DDL="${TAKE_CHECK_DDL:-demo/n8n-flows-v4/mf_leads.sql}"
has_keyok() { python3 -I -c 'import json,sys; sys.exit(0 if any(n.get("name") == "KeyOk" for n in json.load(open(sys.argv[1], encoding="utf-8"))["nodes"]) else 1)' "$1" 2>/dev/null; }   # the node list is read as JSON (a text match would also hit a leftover connection that names KeyOk)
# node:connection count of mf-form and mf-hook, detected per file: 15:14 when the file holds the F-002 key check (it adds 3 nodes), else 12:11. TAKE_CHECK_FORM_EXPECT (test hook) overrides both.
FORMCNT_FORM="${TAKE_CHECK_FORM_EXPECT:-$(has_keyok "$D/mf-form.json" && echo 15:14 || echo 12:11)}"
FORMCNT_HOOK="${TAKE_CHECK_FORM_EXPECT:-$(has_keyok "$D/mf-hook.json" && echo 15:14 || echo 12:11)}"
PCOPT=(); if has_keyok "$D/mf-form.json" && has_keyok "$D/mf-hook.json"; then PCOPT=(--patch-checks F002); fi   # both entry flows carry the key check: also check its content (names, links, condition); only F002 here, because F-008 is judged by the exact settings check below
DDLOPT=(); [ -f "$DDL" ] && DDLOPT=(--ddl "$DDL")
python3 -I "${TAKE_CHECK_CK:-$HERE/check_flows.py}" "$D" "${DDLOPT[@]}" "${PCOPT[@]}" \
  --accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 \
  --accept-no-save mf-recovery.json \
  --expect mf-form.json="$FORMCNT_FORM" --expect mf-hook.json="$FORMCNT_HOOK" --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 \
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
# round 9 (M2): the check above only sees the words "none" and false. Every flow except the accepted recovery flow must say exactly all / all / True (a missing settings block, a missing key or an odd word such as "off" also keeps the run list empty or undefined).
SAVEBAD=$(python3 -I - "$D" <<'PYEOF'
import glob, json, os, sys
files = sorted(glob.glob(os.path.join(sys.argv[1], "*.json")))
if not files:
    print("no flow file found")
for p in files:
    fn = os.path.basename(p)
    if fn == "mf-recovery.json":
        continue
    try:
        st = json.load(open(p, encoding="utf-8")).get("settings")
    except (OSError, ValueError, AttributeError):
        print(f"{fn}: file or settings block unreadable")
        continue
    st = st if isinstance(st, dict) else {}
    got = (st.get("saveDataSuccessExecution"), st.get("saveDataErrorExecution"), st.get("saveManualExecutions"))
    if not (got[0] == "all" and got[1] == "all" and got[2] is True):
        print(f"{fn}: saveDataSuccessExecution={got[0]!r} saveDataErrorExecution={got[1]!r} saveManualExecutions={got[2]!r}")
PYEOF
)
if [ -n "$SAVEBAD" ]; then
  echo "!!! RUN SAVING IS NOT EXACTLY all / all / True (successful runs, failed runs, runs started by hand) ON EVERY FLOW EXCEPT THE RECOVERY FLOW: the run list in n8n would be empty or undefined. Only the recovery flow (mf-recovery.json, ACCEPTED below) may differ. This script exits 4."
  printf '%s\n' "$SAVEBAD" | sed 's/^/    /'
  PROBLEMS+=("run saving not all/all/True")
fi
if [ -f "$D/mf-recovery.json" ] && ! grep -q -F "ACCEPTED: recovery flow not part of the take (decision 4)" "$OUT"; then
  echo "!!! THE RECOVERY FLOW IS NOT PRINTED AS ACCEPTED (line 'ACCEPTED: recovery flow not part of the take (decision 4)' is missing): its run saving is not an excused decision. This script exits 4."
  PROBLEMS+=("recovery flow not accepted")
fi
echo "--- (3) Values that must be filled in before import: mail addresses and credential ids ---"
awk '/^(PLACEHOLDERS IN NODE SETTINGS|CREDENTIAL IDS STILL PLACEHOLDERS)/ {p=1; print; next} p && /^  - / {print; next} {p=0}' "$OUT"
echo "--- (4) Does each of the two entry flows contain the F-002 key check (a node named KeyOk)? ---"
NOKEY=0
for f in mf-form.json mf-hook.json; do
  # the node list is read as JSON (a text match would also hit a leftover connection that names KeyOk)
  if has_keyok "$D/$f"; then echo "$f: key check present (F-002 applied)"; else echo "$f: key check ABSENT (F-002 not applied: a malformed lead key and a failed table write are not answered specially). The take needs F-002: this script exits 4."; NOKEY=$((NOKEY+1)); fi
done
if [ "$NOKEY" -gt 0 ]; then PROBLEMS+=("key check absent in $NOKEY entry flow(s)"); fi
echo "--- (5) Open decisions and environment variables ---"
grep -h -E '^(OPEN LEAD DECISIONS|No static tool|IF branches accepted)' "$OUT"
awk '/^STEPS THAT READ ENVIRONMENT VARIABLES/ {p=1; print; next} p && /^  - / {print; next} {p=0}' "$OUT"
echo "If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked."
RESULTLINE=$(grep -h -E '^RESULT: ' "$OUT" | head -n 1)
WARNN=$(sed -n 's/^RESULT: [0-9][0-9]* FAIL, \([0-9][0-9]*\) WARN.*/\1/p' "$OUT" | head -n 1)
UNVN=$(grep -E "^WARN" "$OUT" | grep -c -F "n8n rule UNVERIFIED")
NORM=$(mktemp /tmp/take-warns.XXXXXX) || exit 3
trap 'rm -f -- "$OUT" "$NORM"' EXIT
python3 -I - "$OUT" "$D" > "$NORM" <<'PYEOF'
import sys
out, d = sys.argv[1], sys.argv[2]
lines = [l.rstrip("\n").replace(d + "/", "") for l in open(out, encoding="utf-8", errors="replace") if l.startswith("WARN")]
print("\n".join(sorted(lines)))
PYEOF
if [ -n "$WRITEPIN" ]; then
  { echo "# expected WARN lines of the take check (folder path removed, sorted); a person read each one; written by take_check.sh --write-warn-pin"; cat "$NORM"; } > "$WRITEPIN" || exit 3
  echo "WARN set written to $WRITEPIN ($(grep -c . "$NORM") lines)."
fi
echo "--- (6) Checker result and the WARN baseline ---"
echo "${RESULTLINE:-RESULT line missing}. WARN lines that rest on an n8n rule nobody verified: $UNVN."
if [ -z "$WARNN" ]; then
  echo "!!! THE CHECKER'S RESULT LINE IS MISSING: the WARN count is unknown. This script exits 4."
  PROBLEMS+=("result line missing")
elif [ ! -f "$PIN" ]; then
  echo "!!! THE WARN BASELINE FILE IS MISSING ($PIN): a new WARN (for example a disabled node, an unwired error output) could not be seen. This script exits 4."
  PROBLEMS+=("warn pin missing")
else
  grep -v -E '^#' "$PIN" | grep . | sort > "$NORM.pin"
  grep . "$NORM" > "$NORM.now"
  if cmp -s "$NORM.pin" "$NORM.now"; then
    echo "WARN set equals the pinned set ($(grep -c . "$NORM.now") lines in take-warns.pin): no new and no vanished WARN."
  else
    echo "!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a new pin with: bash take_check.sh --write-warn-pin FILE. This script exits 4."
    diff "$NORM.pin" "$NORM.now" | grep -E '^[<>]' | sed -e 's/^> /  + /' -e 's/^< /  - /' | cut -c1-260
    PROBLEMS+=("warn set changed")
  fi
  rm -f -- "$NORM.pin" "$NORM.now"
fi
echo "=== end of top block; full checker output follows ==="
cat "$OUT"
KNOWN=$(sed -n 's/^Known open problems: \([0-9][0-9]*\).*/\1/p' "$OUT" | head -n 1)
OPEN=$(( ${KNOWN:-0} + 1 + ${#PROBLEMS[@]} ))   # the checker's own count, the psql gate (always a person's step), what this script found wrong (a missing key check is one of those)
if [ "$RC" -eq 0 ] && [ ${#PROBLEMS[@]} -gt 0 ]; then RC=4; fi
echo "Open items counted: checker known open problems ${KNOWN:-0} + psql gate 1 + problems of this script ${#PROBLEMS[@]} (entry flows without the key check: $NOKEY, counted inside the problems)."
echo "FINAL: take_check exit status $RC. ${RESULTLINE:-RESULT line missing}. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: $OPEN. (1 = fault in a file, 4 = table check missing or failed.) This is not a pass for filming."
exit $RC
