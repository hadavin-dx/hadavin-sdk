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
# Round 10b (review f8-r10 round 2): the top block and the FINAL line print a sha256 of the four flow files; the pin header needs a "# reviewed by: NAME, DATE" line without the word PLACEHOLDER (exit 4 otherwise); --write-warn-pin writes only when the only problem is the WARN difference; the run-saving INFO line no longer promises a deletion (the take never deletes anything).
# Round 10c (review f8-r10b round 2): (Q1) the output never says a person read the pin: it prints the reviewer line as written, and a reviewer line that names a session or says "lead to confirm" is exit 4 ("pin not yet confirmed by the lead"), so the first exit 0 needs the lead's own line; (Q2) the flow files (the four and every other *.json in the folder) are hashed before the checker and again after the last read, a difference is exit 4, an unreadable file prints MISSING; (Q5) a checker exit status above 3 is shown and returned as 3.
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
# round 10c (Q2): sha256 of the four flow files AND of every other *.json in the folder (this script reads all *.json there for the run-saving check), taken BEFORE the checker runs and again after the last read; a difference is exit 4. A file that is not a regular file or that sha256sum cannot read is printed as MISSING (never as an empty hash).
flow_snapshot() {
  SNAP_FOUR=""; SNAP_OTHER=""; SNAP_MISSING=0
  local f p h
  for f in mf-form.json mf-hook.json mf-recovery.json mf-sub-crm-mail.json; do
    p="$D/$f"
    if [ -f "$p" ] && h=$(sha256sum -- "$p" 2>/dev/null) && [ -n "$h" ]; then SNAP_FOUR="$SNAP_FOUR${h%% *}  $f"$'\n'
    else SNAP_FOUR="${SNAP_FOUR}MISSING  $f"$'\n'; SNAP_MISSING=1; fi
  done
  for p in "$D"/*.json; do
    [ -e "$p" ] || [ -L "$p" ] || continue
    f=${p##*/}
    case "$f" in mf-form.json|mf-hook.json|mf-recovery.json|mf-sub-crm-mail.json) continue;; esac
    if [ -f "$p" ] && h=$(sha256sum -- "$p" 2>/dev/null) && [ -n "$h" ]; then SNAP_OTHER="$SNAP_OTHER${h%% *}  $f"$'\n'
    else SNAP_OTHER="${SNAP_OTHER}MISSING  $f"$'\n'; SNAP_MISSING=1; fi
  done
}
flow_snapshot; SNAP_BEFORE="$SNAP_FOUR$SNAP_OTHER"; FLOWSHA_LINES=$SNAP_FOUR; FLOWSHA_MISSING=$SNAP_MISSING; OTHER_LINES=$SNAP_OTHER
python3 -I "${TAKE_CHECK_CK:-$HERE/check_flows.py}" "$D" "${DDLOPT[@]}" "${PCOPT[@]}" \
  --accept-if mf-recovery.json=StuckRow:1 --accept-if mf-recovery.json=AlertRow:1 \
  --accept-no-save mf-recovery.json \
  --expect mf-form.json="$FORMCNT_FORM" --expect mf-hook.json="$FORMCNT_HOOK" --expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26 \
  --expect-credential postgres=n8n-publish-pg --expect-credential smtp=mf-mail-smtp --expect-credential hubspotAppToken=hubspot-app-token \
  --quiet-info > "$OUT" 2>&1
RC=$?
PROBLEMS=()   # things this script itself found wrong (each one makes the exit status 4 when the checker exited 0)
if [ ${#OVR[@]} -gt 0 ]; then
  OVRTXT="ACTIVE ENVIRONMENT OVERRIDES: ${OVR[*]}"
  if [ "${TAKE_CHECK_TEST:-}" = 1 ]; then OVRTXT="$OVRTXT (test flag TAKE_CHECK_TEST=1 is set: this is a test run, not a take check)"; else OVRTXT="$OVRTXT (NOT allowed outside tests: this script exits 4)"; PROBLEMS+=("environment override(s) without the test flag"); fi
else
  OVRTXT="OVERRIDES: none"
fi
FLOWSTXT="Flows folder checked: $D"; [ -n "$FLOWSARG" ] && FLOWSTXT="$FLOWSTXT (given with --flows)"
# round 10b (M-2): a sha256 of the four checked flow files, so a person can compare it with the sha written down at re-pin (a different file with the same name gives a different sha); round 10c: taken before the checker ran (see flow_snapshot above)
FLOWSHA=$(printf '%s' "$FLOWSHA_LINES" | sha256sum | cut -d' ' -f1)
[ "$FLOWSHA_MISSING" = 1 ] && FLOWSHA="$FLOWSHA (at least one *.json file in the folder is MISSING or unreadable)"
[ "$FLOWSHA_MISSING" = 1 ] && PROBLEMS+=("a flow file is missing or unreadable")
echo "=== NOTHING RAN IN n8n. Import of these files into n8n was never tried. ==="
echo "$OVRTXT"
echo "$FLOWSTXT"
echo "sha256 of the four flow files checked (compare with the sha written down at re-pin; it is the sha256 of the four lines below, without the two leading spaces):"
echo "  combined: $FLOWSHA"
printf '%s' "$FLOWSHA_LINES" | sed 's/^/  /'
echo "  other *.json files in the folder (also read by this script, sha256 taken too): $(printf '%s' "$OTHER_LINES" | grep -c .)"
printf '%s' "$OTHER_LINES" | grep -F MISSING | sed 's/^/  /'
if [ "$RC" -ge 2 ]; then
  CKRC=$RC; [ "$RC" -ge 4 ] && RC=3   # round 10c (Q5): the checker only has 0 to 3; any other number (127 not found, 137 killed) means it broke, and 4 is reserved for this script
  echo "=== THE CHECKER DID NOT GIVE A VERDICT (its exit status is $CKRC: 2 = started wrongly, 3 = broke; any number above 3 is shown as 3 here). Nothing below says anything about the flows. ==="
  cat "$OUT"
  echo "FINAL: take_check exit status $RC. Flow files sha256 (four files, combined): $FLOWSHA. $OVRTXT. exit 0 would have meant: no definite fault in the files; NOTHING ran in n8n. The checker gave no verdict; open items: unknown."
  exit "$RC"
fi
echo "=== READ THIS BLOCK BEFORE ANYTHING ELSE ==="
echo "--- (1) The lead table and the column check ---"
cnt() { grep -c -E -- "$1" "$OUT"; }   # N3: a closing-block line must appear exactly once (a flow text that imitates it must not win by being first)
if [ ${#DDLOPT[@]} -gt 0 ] && [ "$(cnt '^SQL columns compared with the --ddl file:')" != 1 ]; then PROBLEMS+=("closing line 'SQL columns compared' not exactly once"); fi
[ "$(cnt '^RESULT: ')" -le 1 ] || PROBLEMS+=("line 'RESULT:' seen more than once")
[ "$(cnt '^Known open problems: ')" -le 1 ] || PROBLEMS+=("line 'Known open problems' seen more than once")
QN=$(sed -n 's/^SQL columns compared with the --ddl file: \([0-9][0-9]*\) query string.*/\1/p' "$OUT" | head -n 1)
UNCMP=$(sed -n 's/^SQL NOT COMPARED: query strings read but not compared[^=]*=\([0-9]*\);.*/\1/p' "$OUT" | head -n 1)
COLW=$(sed -n 's/^SQL WARNS: column WARNs=\([0-9]*\) .*/\1/p' "$OUT" | head -n 1)
TBLW=$(sed -n 's/^SQL WARNS: .* table WARNs=\([0-9]*\) .*/\1/p' "$OUT" | head -n 1)
NOQ=$(sed -n 's/^SQL WARNS: .*(not compared)=\([0-9]*\).*/\1/p' "$OUT" | head -n 1)
if [ ${#DDLOPT[@]} -eq 0 ]; then
  echo "!!! THE TABLE FILE IS MISSING: demo/n8n-flows-v4/mf_leads.sql was not found, so the column names in the SQL steps were NOT checked. On the older table the alert steps fail on every run and no alert is sent. This script exits 4."
  PROBLEMS+=("table file missing")
else
  echo "Table definition used for the column check: $DDL (the take needs demo/n8n-flows-v4/mf_leads.sql, with the four alert columns, not the older one in demo/n8n-flows)."
  echo "Query strings read AND compared: ${QN:-unknown}. Query strings read but NOT compared (no table name, only {{ }}): ${UNCMP:-unknown}. Column WARNs: ${COLW:-unknown}. Table WARNs: ${TBLW:-unknown}. Postgres steps with no query text (not compared): ${NOQ:-unknown}."
  if [ -z "$QN" ] || [ "$QN" -eq 0 ]; then
    echo "!!! 0 QUERY STRINGS WERE READ (or the count line is missing): NO column was compared. This script exits 4."
    PROBLEMS+=("0 queries read")
  fi
  if [ "${COLW:-1}" -gt 0 ] || [ "${TBLW:-1}" -gt 0 ] || [ "${NOQ:-1}" -gt 0 ] || [ "${UNCMP:-1}" -gt 0 ]; then
    echo "!!! A COLUMN OR TABLE IS MISSING, or a step was not compared (counts above, WARN lines further down): the alert or lead steps would fail on every run. This script exits 4."
    PROBLEMS+=("column/table WARN")
  fi
fi
echo "GATE BEFORE THE FIRST SEND (a person's step; this script cannot see your database): in psql run: select column_name from information_schema.columns where table_name='mf_leads' and column_name in ('alert_sent','alert_token','alert_until','alert_attempts');  It must list all four alert_ columns. If it lists fewer, do not send: no alert would ever go out."
echo "--- (2) Is saving of past runs off? One line per file (a run list in n8n stays empty when it is off) ---"
grep -h -E '^mf-[a-z-]+\.json nodes=' "$OUT"
grep -h -E '^mf-[a-z-]+\.json nodes=.* saveDataSuccess=all saveDataError=all saveManual=True$' "$OUT" | sed -E 's/^(mf-[a-z-]+\.json) .*/INFO: \1 run saving is ON (successful runs, failed runs and runs started by hand) on purpose: the take shows the run list (patch F-008, lead answer Q18). Saved runs hold made-up lead keys, e-mails and names. This script never deletes them; what happens to them after the take is a person'"'"'s decision./'
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
SBRC=$?   # N2: a helper that crashed must not look like "nothing wrong"
if [ "$SBRC" -ne 0 ]; then echo "!!! THE RUN-SAVING HELPER FAILED (exit status $SBRC): run saving was not checked exactly. This script exits 4."; PROBLEMS+=("run-saving helper failed"); fi
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
# round 10c (Q2): the last read of the flow files is above; hash them again and compare with the hash taken before the checker ran
flow_snapshot; SNAP_AFTER="$SNAP_FOUR$SNAP_OTHER"; CHANGED=0
if [ "$SNAP_BEFORE" != "$SNAP_AFTER" ] || [ "$SNAP_MISSING" = 1 ]; then
  if [ "$SNAP_BEFORE" != "$SNAP_AFTER" ]; then CHANGED=1; echo "!!! A FLOW FILE CHANGED WHILE THIS CHECK RAN (sha256 before the checker differs from sha256 after the last read): the checker and this script may have read different files, so nothing here is a verdict about one file set. Run it again when nothing writes to the folder. This script exits 4."; PROBLEMS+=("flow files changed during the check"); fi
fi
echo "--- (5) Open decisions and environment variables ---"
grep -h -E '^(OPEN LEAD DECISIONS|No static tool|IF branches accepted)' "$OUT"
awk '/^STEPS THAT READ ENVIRONMENT VARIABLES/ {p=1; print; next} p && /^  - / {print; next} {p=0}' "$OUT"
echo "If n8n on the filming machine blocks environment-variable access inside steps, those steps stop working. No file check can see that setting. To see which steps would break, run the checker with --block-env-access (exit 1 expected today). exit 0 does NOT mean authentication was checked."
RESULTLINE=$(grep -h -E '^RESULT: ' "$OUT" | head -n 1)
WARNN=$(sed -n 's/^RESULT: [0-9][0-9]* FAIL, \([0-9][0-9]*\) WARN.*/\1/p' "$OUT" | head -n 1)
UNVN=$(grep -E "^WARN" "$OUT" | grep -c -F "n8n rule UNVERIFIED")
python3 -I - "$OUT" "$D" > "$NORM" <<'PYEOF'
import sys
out, d = sys.argv[1], sys.argv[2]
lines = [l.rstrip("\n").replace(d + "/", "") for l in open(out, encoding="utf-8", errors="replace") if l.startswith("WARN")]
print("\n".join(sorted(lines)))
PYEOF
NRC=$?
if [ "$NRC" -ne 0 ]; then echo "!!! THE WARN-LINE HELPER FAILED (exit status $NRC): the WARN set was not read. This script exits 4."; PROBLEMS+=("warn helper failed"); fi
grep . "$NORM" | LC_ALL=C sort > "$NORM.now"
echo "--- (6) Checker result and the WARN baseline ---"
echo "${RESULTLINE:-RESULT line missing}. WARN lines that rest on an n8n rule nobody verified: $UNVN."
PINNED=0
if [ -z "$WARNN" ]; then
  echo "!!! THE CHECKER'S RESULT LINE IS MISSING: the WARN count is unknown. This script exits 4."
  PROBLEMS+=("result line missing")
elif [ ! -f "$PIN" ]; then
  echo "!!! THE WARN BASELINE FILE IS MISSING ($PIN): a new WARN (for example a disabled node, an unwired error output) could not be seen. This script exits 4."
  PROBLEMS+=("warn pin missing")
else
  grep -v -E '^#' "$PIN" | grep . | LC_ALL=C sort > "$NORM.pin"
  PINNED=$(grep -c . "$NORM.pin")
  PINHASH=$(sha256sum < "$NORM.pin" | cut -d' ' -f1)
  HDRHASH=$(sed -n 's/^# sha256 of the WARN lines below[^:]*: \([0-9a-f]\{64\}\)$/\1/p' "$PIN" | head -n 1)
  HDRDATE=$(sed -n 's/^# date (UTC): \([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\)$/\1/p' "$PIN" | head -n 1)
  HDRREV=$(sed -n 's/^# reviewed by: \(.*\)$/\1/p' "$PIN" | head -n 1)
  if [ -z "$HDRREV" ]; then echo "!!! THE PIN HEADER HAS NO '# reviewed by: NAME, DATE' LINE: nobody has said that a person read these WARN lines. This script exits 4."; PROBLEMS+=("pin has no reviewer line")
  elif printf '%s' "$HDRREV" | grep -q -F "PLACEHOLDER"; then echo "!!! THE PIN HEADER STILL HAS THE PLACEHOLDER IN ITS 'reviewed by' LINE: the file was written by the script and no person has read it. Read every line, then replace that line. This script exits 4."; PROBLEMS+=("pin not reviewed (placeholder)")
  elif printf '%s' "$HDRREV" | grep -q -i -E "session|lead to confirm"; then echo "!!! pin not yet confirmed by the lead: the 'reviewed by' line of the pin (as written: $HDRREV) names a session or says the lead still has to confirm. A session is not a person who read the WARN lines. The lead reads every WARN line and replaces that line with: # reviewed by: NAME, YYYY-MM-DD. This script exits 4."; PROBLEMS+=("pin not yet confirmed by the lead"); fi
  if [ -z "$HDRDATE" ]; then echo "!!! THE PIN HEADER HAS NO DATE ('# date (UTC): YYYY-MM-DD'): nobody can tell when a person read these WARN lines. This script exits 4."; PROBLEMS+=("pin has no date"); fi
  if [ -z "$HDRHASH" ]; then echo "!!! THE PIN HEADER HAS NO SHA-256 LINE: a hand edit of the pin cannot be seen. This script exits 4."; PROBLEMS+=("pin has no hash")
  elif [ "$HDRHASH" != "$PINHASH" ]; then echo "!!! THE PIN FILE DOES NOT MATCH ITS OWN SHA-256 (header $HDRHASH, lines $PINHASH): it was edited after a person read it. This script exits 4."; PROBLEMS+=("pin hash differs"); fi
  echo "Pinned WARN lines: $PINNED (pin dated ${HDRDATE:-unknown}, sha256 ${PINHASH:0:16}...). Reviewer line of the pin, printed exactly as written in the file (this script cannot tell who really read the lines): ${HDRREV:-nobody named}"
  echo "The pinned lines stand for KNOWN DEFECTS and open decisions (for example: a missing answer to the caller when a step fails, steps that turn an error into normal-looking data, IF branches that lead nowhere, ids still to be filled). They are NOT fixed; exit 0 hides none of them. Only the reviewer line above says whether a person read them."
  if cmp -s "$NORM.pin" "$NORM.now"; then
    echo "WARN set equals the pinned set ($(grep -c . "$NORM.now") lines in take-warns.pin): no new and no vanished WARN."
  else
    echo "!!! THE WARN SET CHANGED against take-warns.pin (+ new, - gone). Read each line; if all are intended, write a NEW pin file with: bash take_check.sh --write-warn-pin NEWFILE (the run then exits 4 on purpose; install the file by hand, see README). This script exits 4."
    diff "$NORM.pin" "$NORM.now" | grep -E '^[<>]' | sed -e 's/^> /  + /' -e 's/^< /  - /' | cut -c1-260
    PROBLEMS+=("warn set changed")
  fi
fi
if [ -n "$WRITEPIN" ]; then
  # B1: written only after the comparison above, only when the checker found no FAIL and gave a RESULT line, into a file that did not exist; the run never counts as a pass
  BLOCKING=""   # round 10b (M-3): only the WARN difference (and a missing or unreadable OLD pin, which a new pin replaces) may be present; any other problem means the folder is not the take folder, so its WARN set is not worth pinning
  for pr in "${PROBLEMS[@]}"; do
    case "$pr" in "warn set changed"|"warn pin missing"|"pin has no date"|"pin has no hash"|"pin hash differs"|"pin has no reviewer line"|"pin not reviewed (placeholder)"|"pin not yet confirmed by the lead") ;; *) BLOCKING="$BLOCKING [$pr]";; esac
  done
  if [ "$RC" -ne 0 ] || [ -z "$WARNN" ]; then
    echo "!!! NO PIN WRITTEN: the checker found a FAIL or gave no RESULT line, so this WARN set is not worth pinning. This script exits ${RC/0/4}."
    PROBLEMS+=("pin not written")
  elif [ -n "$BLOCKING" ]; then
    echo "!!! NO PIN WRITTEN: this run has other problems besides a changed WARN set:$BLOCKING. Fix them first (for example apply the patches, put the table file in place, remove environment overrides). This script exits 4."
    PROBLEMS+=("pin not written")
  else
    DATE=$(date -u +%Y-%m-%d)
    NEWHASH=$(sha256sum < "$NORM.now" | cut -d' ' -f1)
    if ( set -C; { echo "# expected WARN lines of the take check (folder path removed, sorted). WRITTEN BY take_check.sh --write-warn-pin AND NOT YET READ BY A PERSON: this file is not valid until a person reads every line and replaces the next line."; echo "# reviewed by: PLACEHOLDER-a person must read every WARN line below, then replace this whole line with: # reviewed by: NAME, YYYY-MM-DD"; echo "# date (UTC): $DATE"; echo "# sha256 of the WARN lines below (LC_ALL=C sort, one per line): $NEWHASH"; cat "$NORM.now"; } > "$WRITEPIN" ) 2>/dev/null; then
      echo "NEW PIN WRITTEN to $WRITEPIN ($(grep -c . "$NORM.now") lines). It is NOT in use. Difference against the pin in use (+ new, - gone):"
      diff "$NORM.pin" "$NORM.now" 2>/dev/null | grep -E '^[<>]' | sed -e 's/^> /  + /' -e 's/^< /  - /' | cut -c1-260
      echo "A person must read every line, replace the PLACEHOLDER line in its header with their name and date (until then the script exits 4 on it), then install it by hand (cp NEWFILE take-warns.pin next to this script) and commit it. This run exits 4: writing a pin is never a pass."
      PROBLEMS+=("new pin written, not installed")
    else
      echo "!!! COULD NOT WRITE $WRITEPIN (it appeared meanwhile or the folder cannot be written). This script exits 4."
      PROBLEMS+=("pin not written")
    fi
  fi
fi
echo "=== end of top block; full checker output follows ==="
cat "$OUT"
KNOWN=$(sed -n 's/^Known open problems: \([0-9][0-9]*\).*/\1/p' "$OUT" | head -n 1)
OPEN=$(( ${KNOWN:-0} + 1 + ${#PROBLEMS[@]} ))   # the checker's own count, the psql gate (always a person's step), what this script found wrong (a missing key check is one of those)
if [ "$RC" -eq 0 ] && [ ${#PROBLEMS[@]} -gt 0 ]; then RC=4; fi
if [ "$CHANGED" = 1 ] && [ "$RC" -le 1 ]; then RC=4; fi   # a FAIL read from files that changed mid-run is not a trustworthy 1 either
echo "Open items counted: checker known open problems ${KNOWN:-0} + psql gate 1 + problems of this script ${#PROBLEMS[@]} (entry flows without the key check: $NOKEY, counted inside the problems)."
echo "FINAL: take_check exit status $RC. Flow files sha256 (four files, combined): $FLOWSHA. ${RESULTLINE:-RESULT line missing}. $PINNED pinned WARN lines stand for known defects that are not fixed. $OVRTXT. exit 0 = no definite fault in the files; NOTHING ran in n8n; open items: $OPEN. (1 = fault in a file, 4 = table check missing or failed, or a check of this script failed.) This is not a pass for filming."
exit $RC
