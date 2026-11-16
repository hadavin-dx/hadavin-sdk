#!/bin/bash
# Take-level shell test (round 10, review f8-r10). selftest.py does not run take_check.sh, so this script does, on a temporary copy of the PATCHED real-v5 folder.
# Usage: bash test_take_check.sh PATCHED_REAL_DIR [SCRATCH_DIR]    (SCRATCH_DIR must not exist yet; without it a temporary folder is made and removed again)
# Covers: B1 (writing a pin: never the pin in use, never over an existing file, only on a clean run, never a pass), M1 (environment overrides are exit 4 without the test flag and
# are printed), M3 (a listed flow that is a folder or a dangling link is a FAIL), M4 (the pin header date and sha256 are checked), and a flow whose node count changed while everything
# is still wired (no orphan); round 10b adds M-1 (no deletion promise), M-2 (sha256 of the four flow files), M-3 (pin header must be read by a person; no pin is written when the run has other problems). Round 10d adds A1 (pin comment), B1 (enforced flows sha256), B2 (reviewer line grammar), B3 (exit 5, both folder sources, printed source), B4 (run_all.sh lock), a snapshot-order case, a sha256sum failure case and the refusal of the run_all.sh test hooks. Made-up data only. Exit 0 = every case behaved as expected; exit 1 = at least one did not (each is listed).
set -u
HERE=$(cd "$(dirname "$0")" && pwd); TAKE="$HERE/take_check.sh"
P=${1:-}; [ -d "$P" ] || { echo "usage: bash test_take_check.sh PATCHED_REAL_DIR [SCRATCH_DIR]"; exit 2; }
P=$(cd "$P" && pwd)
if [ -n "${2:-}" ]; then
  [ -e "$2" ] && { echo "REFUSED: $2 exists"; exit 2; }
  S=$2; mkdir -p -- "$S" || exit 2
else
  S=$(mktemp -d "${TMPDIR:-/tmp}/ttc.XXXXXX") || exit 2
  trap 'rm -rf -- "$S"' EXIT
fi
BAD=0; N=0
ok() { N=$((N+1)); if [ "$1" = 0 ]; then echo "ok   $2"; else echo "FAIL $2"; BAD=$((BAD+1)); fi; }
# tk NAME ARGS...: run the take check with a clean environment (no override, no test flag) plus the extra variables given before "--"
tk() { local nm=$1; shift; local ev=(); while [ "${1:-}" != "--" ]; do ev+=("$1"); shift; done; shift
  env -u TAKE_CHECK_TEST -u TAKE_CHECK_CK -u TAKE_CHECK_WARN_PIN -u TAKE_CHECK_FLOWS -u TAKE_CHECK_DDL -u TAKE_CHECK_FORM_EXPECT "${ev[@]}" bash "$TAKE" "$@" > "$S/$nm.txt" 2>&1; RC=$?; }
has() { grep -q -F -- "$2" "$S/$1.txt"; }
cmp_pins() { cmp -s <(grep -v '^#' "$1") <(grep -v '^#' "$2"); }
PIN="$HERE/take-warns.pin"
PINSUM=$(sha256sum < "$PIN" | cut -d' ' -f1)
# round 10c (Q1): the committed pin keeps a reviewer line that names a session, so a bare take exits 4 until the lead edits it. Cases that need exit 0 use LEADPIN (same WARN lines, a person's reviewer line); SESSPIN keeps the session wording
{ echo "# reviewed by: Testonly Reviewer, 2026-11-16"; grep -v '^# reviewed by' "$PIN"; } > "$S/lead.pin"; LEADPIN="$S/lead.pin"
{ echo "# reviewed by: flows-audit session, 2026-11-16, content read by that session only, lead to confirm"; grep -v '^# reviewed by' "$PIN"; } > "$S/sess.pin"

# the control: the plain take on the patched copy. Exit 0 only when the committed pin carries a reviewer line that is not a session (round 10c); until then exit 4 with the plain reason
tk control -- --flows "$P"
CRL=$(sed -n 's/^# reviewed by: //p' "$PIN" | head -n 1)
{ [ "$RC" = 0 ] || { [ "$RC" = 4 ] && has control "pin not yet confirmed by the lead"; }; } && has control "OVERRIDES: none" && has control "Pinned WARN lines:" && has control "known defects" && has control "$CRL"; ok $? "control: the committed pin gives exit 0, or exit 4 with 'pin not yet confirmed by the lead' while its reviewer line names a session; the reviewer line is printed as written; OVERRIDES says none (got exit $RC)"
# Q1: with a person's reviewer line the same take is exit 0, and the output never says a person read the pin
tk q1ok TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$P"
[ "$RC" = 5 ] && has q1ok "reviewed by (as written in the pin): Testonly Reviewer, 2026-11-16" && ! has q1ok "a person read"; ok $? "Q1/B3: a pin with a person's reviewer line gives exit 5 (a would-be pass with the pin override; 5, never 0); the line is printed as written; the output does not say a person read the pin (got exit $RC)"
tk q1a TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/sess.pin" -- --flows "$P"
[ "$RC" = 4 ] && has q1a "pin not yet confirmed by the lead" && has q1a "as written: flows-audit session" && ! has q1a "a person read and accepted"; ok $? "Q1: a reviewer line naming a session and 'lead to confirm' is exit 4 with the plain reason, never 'a person read' (got exit $RC)"
for pair in "only-session:# reviewed by: Audit Session B, 2026-11-16" "only-confirm:# reviewed by: A. Person, 2026-11-16, Lead To Confirm"; do
  nm=q1-${pair%%:*}; { echo "${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 4 ] && has "$nm" "pin not yet confirmed by the lead"; ok $? "Q1: '${pair#*:}' is exit 4 (got exit $RC)"
done

# B1a: the pin in use as the target is refused, the file stays byte for byte the same
cp -- "$PIN" "$S/inuse.pin"; SUM=$(sha256sum < "$S/inuse.pin")
tk b1a TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/inuse.pin" -- --flows "$P" --write-warn-pin "$S/inuse.pin"
[ "$RC" = 2 ] && has b1a "REFUSED" && [ "$(sha256sum < "$S/inuse.pin")" = "$SUM" ]; ok $? "B1a: --write-warn-pin on the pin in use is refused (exit 2) and leaves it unchanged (got exit $RC)"
# B1b: a new file on a clean run: written, exit 4 (never a pass), has date and sha256 header, same lines as the pin in use
tk b1b -- --flows "$P" --write-warn-pin "$S/new.pin"
[ "$RC" = 4 ] && [ -f "$S/new.pin" ] && has b1b "NEW PIN WRITTEN" && has b1b "never a pass" && grep -q '^# date (UTC): ' "$S/new.pin" && grep -q '^# sha256 of the WARN lines below' "$S/new.pin" && cmp_pins "$S/new.pin" "$PIN"; ok $? "B1b: a clean run writes a NEW pin with date and sha256 and exits 4, not 0 (got exit $RC)"
# a pin written by the script is NOT valid until a person replaces the placeholder in its header (round 10b, M-3); reviewed.pin stands for that person's edit
grep -q '^# flows sha256 (the four flow files, combined, as printed in the top block of take_check.sh): [0-9a-f]\{64\}$' "$S/new.pin"; ok $? "B1: the written pin carries the '# flows sha256' line"
grep -q 'PLACEHOLDER' "$S/new.pin" && grep -q 'NOT YET READ BY A PERSON' "$S/new.pin"; ok $? "M-3: the written pin says it is not yet read and holds the placeholder line"
sed 's/^# reviewed by: .*/# reviewed by: Testonly Reviewer, 2026-11-16/' "$S/new.pin" > "$S/reviewed.pin"
tk m3p1 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/new.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m3p1 "STILL HAS THE PLACEHOLDER"; ok $? "M-3: a pin whose header still has the placeholder is exit 4 (got exit $RC)"
grep -v '^# reviewed by' "$S/reviewed.pin" > "$S/norev.pin"
tk m3p2 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/norev.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m3p2 "NO '# reviewed by: NAME, DATE' LINE"; ok $? "M-3: a pin with no 'reviewed by' line is exit 4 (got exit $RC)"
# round trip: the written pin, installed by hand, makes the plain take pass
tk b1b2 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/reviewed.pin" -- --flows "$P"
[ "$RC" = 5 ] && has b1b2 "WARN set equals the pinned set"; ok $? "B1b: the written pin, used as the pin, gives exit 5 (would-be pass with the pin override) (got exit $RC)"
# B1c: an existing file is never overwritten
echo "keep me" > "$S/exists.pin"
tk b1c -- --flows "$P" --write-warn-pin "$S/exists.pin"
[ "$RC" = 2 ] && [ "$(cat "$S/exists.pin")" = "keep me" ]; ok $? "B1c: --write-warn-pin on an existing file is refused (exit 2) and leaves it unchanged (got exit $RC)"
# B1d: a run with a FAIL writes nothing
cp -r -- "$P" "$S/failcopy"
python3 -I - "$S/failcopy/mf-sub-crm-mail.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
for n in j["nodes"]:
    if n["name"] == "SendMail":
        n["disabled"] = True
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk b1d -- --flows "$S/failcopy" --write-warn-pin "$S/fail.pin"
[ "$RC" = 1 ] && [ ! -e "$S/fail.pin" ] && has b1d "NO PIN WRITTEN"; ok $? "B1d: a run with a FAIL writes no pin and keeps exit 1 (got exit $RC)"
# B1e: a changed WARN set: the run shows the difference, writes the new file, and still exits 4
cp -r -- "$P" "$S/warnnew"
python3 -I - "$S/warnnew/mf-sub-crm-mail.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
for n in j["nodes"]:
    if n["name"] == "MarkDone":
        n["maxTries"] = 3   # a plain WARN: maxTries is ignored without retryOnFail
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk b1e -- --flows "$S/warnnew" --write-warn-pin "$S/warnnew.pin"
[ "$RC" = 4 ] && [ -f "$S/warnnew.pin" ] && has b1e "THE WARN SET CHANGED" && has b1e "NEW PIN WRITTEN" && grep -q '^  + ' "$S/b1e.txt"; ok $? "B1e: a changed WARN set prints the difference, writes the new file, exits 4 (got exit $RC)"
[ "$(sha256sum < "$PIN" | cut -d' ' -f1)" = "$PINSUM" ]; ok $? "B1: the pin in use (take-warns.pin) is byte for byte unchanged by all cases above"

# M-3: --write-warn-pin writes nothing when the run has any problem other than the WARN difference
cp -r -- "$P" "$S/nosave"
python3 -I - "$S/nosave/mf-form.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
j["settings"]["saveDataSuccessExecution"] = "none"
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk w1 -- --flows "$S/nosave" --write-warn-pin "$S/w1.pin"
[ "$RC" = 4 ] && [ ! -e "$S/w1.pin" ] && has w1 "NO PIN WRITTEN: this run has other problems"; ok $? "M-3: run saving off (unpatched folder) writes no pin, exit 4 (got exit $RC)"
tk w2 TAKE_CHECK_TEST=1 TAKE_CHECK_DDL="$S/no-such-table.sql" -- --flows "$P" --write-warn-pin "$S/w2.pin"
[ "$RC" = 4 ] && [ ! -e "$S/w2.pin" ] && has w2 "NO PIN WRITTEN: this run has other problems"; ok $? "M-3: table file missing writes no pin, exit 4 (got exit $RC)"
tk w3 TAKE_CHECK_WARN_PIN="$S/reviewed.pin" -- --flows "$P" --write-warn-pin "$S/w3.pin"
[ "$RC" = 4 ] && [ ! -e "$S/w3.pin" ] && has w3 "NO PIN WRITTEN: this run has other problems"; ok $? "M-3: an environment override without the test flag writes no pin, exit 4 (got exit $RC)"
cp -r -- "$P" "$S/nokey"
python3 -I - "$S/nokey/mf-form.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
for n in j["nodes"]:
    if n["name"] == "KeyOk":
        n["name"] = "KeyOkRenamed"   # the key check is gone by name; the wiring in "connections" is left alone on purpose, so the checker may also report a FAIL
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk w4 -- --flows "$S/nokey" --write-warn-pin "$S/w4.pin"
{ [ "$RC" = 4 ] || [ "$RC" = 1 ]; } && [ ! -e "$S/w4.pin" ] && has w4 "NO PIN WRITTEN"; ok $? "M-3: key check absent writes no pin, exit 4 or 1 (got exit $RC)"

# M-1 and M-2: the run-saving INFO line promises no deletion; the top block and the FINAL line carry the sha256 of the four flow files
tk sha TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$P"
EXPECT=$(for f in mf-form.json mf-hook.json mf-recovery.json mf-sub-crm-mail.json; do printf '%s  %s\n' "$(sha256sum < "$P/$f" | cut -d' ' -f1)" "$f"; done | sha256sum | cut -d' ' -f1)
[ "$RC" = 5 ] && has sha "  combined: $EXPECT" && grep -q "^FINAL: .*Flow files sha256 (four files, combined): $EXPECT\." "$S/sha.txt" && has sha "  $(sha256sum < "$P/mf-form.json" | cut -d' ' -f1)  mf-form.json"; ok $? "M-2: the top block and the FINAL line print the combined sha256 of the four flow files (and one per file); exit 5 = would-be pass with the pin override (got exit $RC)"
! has sha "deleted at clean-up" && has sha "This script never deletes them"; ok $? "M-1: the output does not say 'deleted at clean-up'"

# M1: an environment override is printed and is exit 4 without the test flag; with the test flag it is printed and allowed
cp -- "$HERE/check_flows.py" "$S/ck-copy.py"
cp -- "$HERE/../../demo/n8n-flows-v4/mf_leads.sql" "$S/ddl-copy.sql"
tk m1a TAKE_CHECK_WARN_PIN="$S/reviewed.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m1a "ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_WARN_PIN=$S/reviewed.pin" && grep -q '^FINAL: .*ACTIVE ENVIRONMENT OVERRIDES' "$S/m1a.txt"; ok $? "M1: TAKE_CHECK_WARN_PIN without the test flag is exit 4 and is named in the top block and the FINAL line (got exit $RC)"
tk m1-TAKE_CHECK_FLOWS "TAKE_CHECK_FLOWS=$P" --
[ "$RC" = 4 ] && has m1-TAKE_CHECK_FLOWS "ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_FLOWS=$P"; ok $? "M1: TAKE_CHECK_FLOWS without the test flag (and without --flows) is exit 4 and is printed (got exit $RC)"
for pair in "TAKE_CHECK_DDL=$S/ddl-copy.sql" "TAKE_CHECK_CK=$S/ck-copy.py" "TAKE_CHECK_FORM_EXPECT=15:14"; do
  nm=m1-${pair%%=*}
  tk "$nm" "$pair" -- --flows "$P"
  [ "$RC" = 4 ] && has "$nm" "ACTIVE ENVIRONMENT OVERRIDES: $pair"; ok $? "M1: ${pair%%=*} without the test flag is exit 4 and is printed (got exit $RC)"
done
tk m1b TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/reviewed.pin" -- --flows "$P"
[ "$RC" = 5 ] && has m1b "test flag TAKE_CHECK_TEST=1 is set"; ok $? "M1/B3: with the test flag the override is allowed, still printed, and a would-be pass is exit 5 (got exit $RC)"

# M3: a listed flow that is a folder, or a dangling link, is a FAIL (the checker used to skip it silently)
cp -r -- "$P" "$S/dircopy"; rm -f -- "$S/dircopy/mf-hook.json"; mkdir "$S/dircopy/mf-hook.json"
tk m3a -- --flows "$S/dircopy"
[ "$RC" = 1 ] && grep -q '^FAIL .*mf-hook.json this listed flow is not a regular file' "$S/m3a.txt"; ok $? "M3: a folder named mf-hook.json is a FAIL, exit 1 (got exit $RC)"
cp -r -- "$P" "$S/linkcopy"; rm -f -- "$S/linkcopy/mf-recovery.json"; ln -s "$S/does-not-exist.json" "$S/linkcopy/mf-recovery.json"
tk m3b -- --flows "$S/linkcopy"
[ "$RC" = 1 ] && grep -q '^FAIL .*mf-recovery.json this listed flow is not a regular file' "$S/m3b.txt"; ok $? "M3: a dangling link named mf-recovery.json is a FAIL, exit 1 (got exit $RC)"

# M4: the pin header is checked: a hand-edited pin, a pin without the sha256 line and a pin without a date are each exit 4
sed 's/^\(# sha256 of the WARN lines below[^:]*: \)./\1x/' "$S/reviewed.pin" > "$S/badhash.pin"
tk m4a TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/badhash.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m4a "THE PIN HEADER HAS NO SHA-256 LINE"; ok $? "M4: a pin header with a broken sha256 line is exit 4 (got exit $RC)"
sed 's/^\(# sha256 of the WARN lines below[^:]*: [0-9a-f]\{3\}\)./\10/' "$S/reviewed.pin" > "$S/wronghash.pin"
cmp -s "$S/wronghash.pin" "$S/reviewed.pin" && sed 's/^\(# sha256 of the WARN lines below[^:]*: [0-9a-f]\{3\}\)./\11/' "$S/reviewed.pin" > "$S/wronghash.pin"
tk m4b TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/wronghash.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m4b "DOES NOT MATCH ITS OWN SHA-256"; ok $? "M4: a pin whose lines do not match its sha256 is exit 4 (got exit $RC)"
grep -v '^# date' "$S/reviewed.pin" > "$S/nodate.pin"
tk m4c TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/nodate.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m4c "THE PIN HEADER HAS NO DATE"; ok $? "M4: a pin without a date is exit 4 (got exit $RC)"
# a pin edited by hand so that it equals the new WARN set but the header hash is old: caught by the hash, not by the set comparison
{ grep '^#' "$S/reviewed.pin"; grep -v '^#' "$S/reviewed.pin" | head -n 5; } > "$S/short.pin"
tk m4d TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/short.pin" -- --flows "$P"
[ "$RC" = 4 ] && has m4d "DOES NOT MATCH ITS OWN SHA-256" && has m4d "THE WARN SET CHANGED"; ok $? "M4: a pin with lines removed by hand is caught twice (hash and set) (got exit $RC)"

# Q2 (round 10c): a flow file that changes while the check runs is exit 4; every *.json in the folder counts; an unreadable file prints MISSING
cat > "$S/wrap.py" <<PYEOF
import os, subprocess, sys
r = subprocess.run([sys.executable, "-I", "$HERE/check_flows.py"] + sys.argv[1:])
t = os.path.join(sys.argv[1], os.environ["WRAP_TARGET"])
with open(t, "a", encoding="utf-8") as f:
    f.write("\n")   # the checker has finished; the file changes before this script reads the folder again
sys.exit(r.returncode)
PYEOF
for t in mf-hook.json extra.json; do
  cp -r -- "$P" "$S/chg-$t"; [ "$t" = extra.json ] && printf '%s\n' '{"settings": {"saveDataSuccessExecution": "all", "saveDataErrorExecution": "all", "saveManualExecutions": true}}' > "$S/chg-$t/extra.json"
  tk "q2-$t" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_CK="$S/wrap.py" WRAP_TARGET="$t" -- --flows "$S/chg-$t"
  [ "$RC" = 4 ] && has "q2-$t" "A FLOW FILE CHANGED WHILE THIS CHECK RAN"; ok $? "Q2: $t written after the checker ran is exit 4 with the loud line (got exit $RC)"
done
cp -r -- "$P" "$S/extra-ok"; printf '%s\n' '{"settings": {"saveDataSuccessExecution": "all", "saveDataErrorExecution": "all", "saveManualExecutions": true}}' > "$S/extra-ok/extra.json"
tk q2c TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$S/extra-ok"
[ "$RC" = 1 ] && has q2c "other *.json files in the folder (also read by this script, sha256 taken too): 1" && ! has q2c "A FLOW FILE CHANGED"; ok $? "Q2: an extra *.json that does not change is counted (the checker FAILs on the unexpected file, exit 1; no 'changed' line) (got exit $RC)"
mkdir "$S/stub"; REALSHA=$(command -v sha256sum); printf '#!/bin/bash\ncase "$*" in *mf-hook.json*) exit 1;; esac\nexec %s "$@"\n' "$REALSHA" > "$S/stub/sha256sum"; chmod +x "$S/stub/sha256sum"
tk q2d TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" PATH="$S/stub:$PATH" -- --flows "$P"
[ "$RC" = 4 ] && has q2d "MISSING  mf-hook.json" && has q2d "MISSING or unreadable"; ok $? "Q2: a flow file that sha256sum cannot read is printed as MISSING and is exit 4, never an empty hash (got exit $RC)"
# ---- round 10d ----
# A1: the first line of the committed pin no longer says that a person read each line (only the WARN lines are hashed)
! head -n 1 "$PIN" | grep -q -i "a person read"; ok $? "A1: line 1 of take-warns.pin does not claim that a person read each line"
# B1: a flow file changed in a way the checker does not see (a node position), same counts, same WARN lines: exit 4 because of the enforced flows sha256
cp -r -- "$P" "$S/b1flow"
python3 -I - "$S/b1flow/mf-sub-crm-mail.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
j["nodes"][0]["position"] = [12345, 6789]
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
tk b1sha TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$S/b1flow"
[ "$RC" = 4 ] && has b1sha "THE FLOW FILES DO NOT MATCH THE SHA-256 WRITTEN IN THE PIN" && has b1sha "WARN set equals the pinned set"; ok $? "B1: a changed flow file with the same counts and the same WARN lines is exit 4 (got exit $RC)"
grep -v '^# flows sha256' "$LEADPIN" > "$S/noflowsha.pin"
tk b1nosha TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/noflowsha.pin" -- --flows "$P"
[ "$RC" = 4 ] && has b1nosha "THE PIN HEADER HAS NO '# flows sha256 ...' LINE"; ok $? "B1: a pin without the flows sha256 line is exit 4 (got exit $RC)"
# B2: the reviewer line must read NAME, YYYY-MM-DD (optional note); stand-ins are exit 4
for pair in "b2-agent:claude agent, 2026-11-16" "b2-tbd:TBD" "b2-x:x, 2026-11-16" "b2-nodate:Testonly Reviewer" "b2-baddate:Testonly Reviewer, 2026-13-45" "b2-future:Testonly Reviewer, 2999-01-01" "b2-empty-name:, 2026-11-16" "b2-digits:R2D2 4, 2026-11-16" "b2-ai:Some Assistant, 2026-11-16" "b2-placeholder-word:Name Placeholder, 2026-11-16"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 4 ] && grep -q -E "^!!! (THE 'reviewed by' LINE OF THE PIN IS NOT A PERSON|pin not yet confirmed)" "$S/$nm.txt"; ok $? "B2: reviewer line '${pair#*:}' is exit 4 (got exit $RC)"
done
{ echo "# reviewed by: Jane Q. Roe-Smith, 2026-11-16, read all 4 WARN lines"; grep -v '^# reviewed by' "$PIN"; } > "$S/b2good.pin"
tk b2good TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/b2good.pin" -- --flows "$P"
[ "$RC" = 5 ] && ! has b2good "NOT A PERSON"; ok $? "B2: 'Jane Q. Roe-Smith, 2026-11-16, read all 4 WARN lines' is accepted (would-be pass with the override: exit 5) (got exit $RC)"
# f8-r4 (M1): the bypasses of review f8-r3 (words joined by dots or hyphens, two stand-in words, a repeated letter, the script's own stand-in names, a date far in the past or before the pin's own date). Each must be exit 4 with the reviewer-line message, even with the test flag and the pin override (a name that is not "Testonly ..." gets no test allowance)
for pair in "m1-tbd-dot:TBD., 2026-11-16" "m1-claude-code:Claude-Code, 2026-11-16" "m1-agent-dot:Agent., 2026-11-16" "m1-unknown-dash:Unknown-, 2026-11-16" "m1-sonnet-opus:Sonnet Opus, 2026-11-16" "m1-aaa:Aaa, 2026-11-16" "m1-runall:Runall Standin, 2026-11-16" "m1-test-reviewer:Test Reviewer, 2026-11-16" "m1-testonly-no-flag-name:Testonly Reviewer, 2026-11-16" "m1-model-in-name:Jane Gemini, 2026-11-16" "m1-year2000:Jane Q. Roe-Smith, 2000-01-01" "m1-before-pin:Jane Q. Roe-Smith, 2026-11-15" "m1-dotted-llm:Pat O.L.L.M., 2026-11-16" "m1-dotted-claude:P.a.t C.l.a.u.d.e, 2026-11-16"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$nm" = m1-testonly-no-flag-name ] && tk "$nm" TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"   # the test allowance needs BOTH the flag and the override
  [ "$RC" = 4 ] && grep -q -E "^!!! THE 'reviewed by' LINE OF THE PIN IS NOT A PERSON" "$S/$nm.txt"; ok $? "M1: reviewer line '${pair#*:}' is exit 4 with the reviewer-line message (got exit $RC)"
done
# f8-r5: names that must still be accepted (would-be pass with the override: exit 5, never the stand-in message). 'Zed' (3 letters, human-looking) is accepted by design: a script cannot tell it from a real name
for pair in "r5-pat-smith:Pat Smith, 2026-11-16" "r5-obrien:O'Brien, 2026-11-16" "r5-aiden-botha:Aiden Botha, 2026-11-16" "r5-zed:Zed Smith, 2026-11-16"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN"; } > "$S/$nm.pin"
  tk "$nm" TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/$nm.pin" -- --flows "$P"
  [ "$RC" = 5 ] && ! has "$nm" "NOT A PERSON"; ok $? "f8-r5: reviewer line '${pair#*:}' is accepted (would-be pass with the override: exit 5) (got exit $RC)"
done
# the test allowance: flag + override + first word Testonly = exit 5 (never 0); the same name without the flag was refused above
{ echo "# reviewed by: Testonly Runall, 2026-11-16"; grep -v '^# reviewed by' "$PIN"; } > "$S/m1-allow.pin"
tk m1-allow TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$S/m1-allow.pin" -- --flows "$P"
[ "$RC" = 5 ] && ! has m1-allow "NOT A PERSON"; ok $? "M1: with the test flag AND a pin override, a 'Testonly ...' name is accepted and the run is exit 5, never 0 (got exit $RC)"
# the real bypass: the script's own stand-in pin copied in as THE pin (no override, no test flag) must not give exit 0. A mirror folder holds copies of the scripts, the real checker and the pin; demo/ is a link to the real demo folder
MIR="$S/mirror"; mkdir -p "$MIR/flows-audit/flow-check" "$MIR/flows-audit/patches" && ln -s "$HERE/../../demo" "$MIR/demo" && cp -- "$HERE/take_check.sh" "$HERE/check_flows.py" "$PIN" "$MIR/flows-audit/flow-check/"
mir() { local nm=$1; shift; env -u TAKE_CHECK_TEST -u TAKE_CHECK_CK -u TAKE_CHECK_WARN_PIN -u TAKE_CHECK_FLOWS -u TAKE_CHECK_DDL -u TAKE_CHECK_FORM_EXPECT bash "$MIR/flows-audit/flow-check/take_check.sh" --flows "$P" > "$S/$nm.txt" 2>&1; RC=$?; }
mir mirbase
MIRSHA=$(sed -n 's/^  combined: \([0-9a-f]\{64\}\)$/\1/p' "$S/mirbase.txt" | head -n 1)
[ -n "$MIRSHA" ]; ok $? "M1: the mirror run printed the combined flows sha256 (needed to build the stand-in pins below)"
for pair in "mir-testrev:Testonly Reviewer, 2026-11-16" "mir-test-reviewer:Test Reviewer, 2026-11-16" "mir-runall:Runall Standin, 2026-11-16" "mir-tbd:TBD., 2026-11-16" "mir-claudecode:Claude-Code, 2026-11-16"; do
  nm=${pair%%:*}; { echo "# reviewed by: ${pair#*:}"; grep -v '^# reviewed by' "$PIN" | sed "s/^\(# flows sha256 .*: \)[0-9a-f]\{64\}\$/\1$MIRSHA/"; } > "$MIR/flows-audit/flow-check/take-warns.pin"
  mir "$nm"
  [ "$RC" = 4 ] && grep -q "NOT A PERSON" "$S/$nm.txt"; ok $? "M1: '${pair#*:}' in the real pin place, no override, no test flag: exit 4, never 0 (got exit $RC)"
done
{ echo "# reviewed by: Jane Q. Roe-Smith, 2026-11-16, read all WARN lines"; grep -v '^# reviewed by' "$PIN" | sed "s/^\(# flows sha256 .*: \)[0-9a-f]\{64\}\$/\1$MIRSHA/"; } > "$MIR/flows-audit/flow-check/take-warns.pin"
mir mir-human
[ "$RC" = 0 ]; ok $? "M1 (honesty check): a made-up human-looking name in the real pin place IS accepted, exit 0: the script cannot know who read the pin; it only turns away stand-ins (got exit $RC)"
# B3: a would-be pass with a leaked override and the test flag is exit 5, never 0; a copy of the real checker given by TAKE_CHECK_CK is shown
tk b3ck TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_CK="$S/ck-copy.py" -- --flows "$P"
[ "$RC" = 5 ] && has b3ck "ACTIVE ENVIRONMENT OVERRIDES: TAKE_CHECK_CK=$S/ck-copy.py" && has b3ck "a run that would pass exits 5, never 0" && grep -q '^FINAL: take_check exit status 5\.' "$S/b3ck.txt"; ok $? "B3: test flag plus a leaked TAKE_CHECK_CK (and the pin override) is exit 5 with the FINAL line saying 5, not exit 0 (got exit $RC)"
# B3: TAKE_CHECK_FLOWS together with --flows is refused (exit 2) in every mode
tk b3both TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_FLOWS="$S/b1flow" -- --flows "$P"
[ "$RC" = 2 ] && has b3both "REFUSED: the environment variable TAKE_CHECK_FLOWS and the option --flows are both set"; ok $? "B3: TAKE_CHECK_FLOWS and --flows both set is exit 2 (got exit $RC)"
# B3: the real source of the folder name is printed
tk b3src1 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" TAKE_CHECK_FLOWS="$P" --
has b3src1 "Flows folder checked: $P (taken from the environment variable TAKE_CHECK_FLOWS, a test override)" && [ "$RC" = 5 ]; ok $? "B3: a folder taken from TAKE_CHECK_FLOWS is printed as coming from the variable (got exit $RC)"
tk b3src2 TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" -- --flows "$P"
has b3src2 "Flows folder checked: $P (given with --flows)"; ok $? "B3: a folder given with --flows is printed as given with --flows"
# snapshot order (minor): the first read of a flow file (has_keyok, python3) must come AFTER the sha256 snapshot, so a write made by that very first read is seen
cp -r -- "$P" "$S/snapord"; mkdir "$S/stubpy"; REALPY=$(command -v python3)
printf '#!/bin/bash\nif [ ! -e "%s/stubpy/done" ]; then : > "%s/stubpy/done"; printf "\\n" >> "%s/snapord/mf-form.json"; fi\nexec %s "$@"\n' "$S" "$S" "$S" "$REALPY" > "$S/stubpy/python3"; chmod +x "$S/stubpy/python3"
tk snapord TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" PATH="$S/stubpy:$PATH" -- --flows "$S/snapord"
[ "$RC" = 4 ] && has snapord "A FLOW FILE CHANGED WHILE THIS CHECK RAN"; ok $? "snapshot order: a flow file written by the first python3 read is caught (got exit $RC)"
# sha256sum failure (minor): a sha256sum that fails when it reads standard input is a loud problem, exit 4, never an empty hash
mkdir "$S/stub3"; printf '#!/bin/bash\n[ $# -eq 0 ] && exit 1\nexec %s "$@"\n' "$(command -v sha256sum)" > "$S/stub3/sha256sum"; chmod +x "$S/stub3/sha256sum"
tk shafail TAKE_CHECK_TEST=1 TAKE_CHECK_WARN_PIN="$LEADPIN" PATH="$S/stub3:$PATH" -- --flows "$P"
[ "$RC" = 4 ] && has shafail "UNAVAILABLE (sha256sum failed)" && grep -q '^!!! sha256sum FAILED' "$S/shafail.txt"; ok $? "sha256sum failure: exit 4 with a loud line, no empty hash (got exit $RC)"
# B4 + f8-r4 (M2): run_all.sh locks the raw FOLDER itself (physical path, pwd -P), so the lock does not depend on TMPDIR, on how the path is written (relative, symbolic link) or on the current folder. The test holds a lock on the folder and starts --lock-only runs in other ways
RA="$HERE/run_all.sh"; mkdir -p "$S/rl-cwd" "$S/rl-raw" "$S/tmpA" "$S/tmpB"; ln -s "$S/rl-raw" "$S/rl-link"
ra() { local nm=$1 cwd=$2 tmpd=$3 raw=$4; ( cd "$cwd" && TMPDIR="$tmpd" RUN_ALL_NESTED=1 RUN_ALL_RAW="$raw" timeout 20 bash "$RA" --lock-only > "$S/$nm.txt" 2>&1; echo $? > "$S/$nm.rc" ); RC=$(cat "$S/$nm.rc" 2>/dev/null); }
# nobody holds the lock: acquired, exit 0, and no lock file is left in either TMPDIR
ra b4free "$S/rl-cwd" "$S/tmpA" "$S/rl-raw"
[ "$RC" = 0 ] && grep -q "lock acquired" "$S/b4free.txt" && [ -z "$(ls -A "$S/tmpA")" ]; ok $? "B4: with nobody holding the lock, run_all.sh --lock-only takes it, exits 0 and leaves no lock file in TMPDIR (got exit $RC)"
# someone holds the lock on the folder (the test itself, on the physical folder)
(
  exec 9< "$S/rl-raw" && flock -n 9 || exit 9
  ra b4held "$S/rl-cwd" "$S/tmpA" "$S/rl-raw";            [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4held.txt"; echo $? > "$S/m2a.r"
  ra b4tmp "$S/rl-cwd" "$S/tmpB" "$S/rl-raw";             [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4tmp.txt";  echo $? > "$S/m2b.r"
  ra b4link "$S/rl-cwd" "$S/tmpB" "$S/rl-link";           [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4link.txt"; echo $? > "$S/m2c.r"
  ra b4rel "$S/rl-cwd" "$S/tmpA" "../rl-raw";             [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4rel.txt";  echo $? > "$S/m2d.r"
  ra b4dots "$S/rl-cwd" "$S/tmpB" "$S//rl-link/../rl-raw/"; [ "$RC" = 2 ] && grep -q "REFUSED: another run_all.sh holds the lock" "$S/b4dots.txt"; echo $? > "$S/m2e.r"
  ra b4other "$S/rl-cwd" "$S/tmpA" "$S/rl-raw-other";     [ "$RC" = 0 ] && grep -q "lock acquired" "$S/b4other.txt"; echo $? > "$S/m2f.r"
)
for pair in "m2a:a second run_all.sh on a locked raw folder is refused, exit 2" "m2b:the same raw folder with a DIFFERENT TMPDIR is refused, exit 2" "m2c:the same raw folder given through a symbolic link (and another TMPDIR) is refused, exit 2" "m2d:the same raw folder given as a relative path from another folder is refused, exit 2" "m2e:the same raw folder given with a double slash, a link and .. is refused, exit 2" "m2f:a DIFFERENT raw folder is not blocked by that lock (exit 0)"; do
  [ "$(cat "$S/${pair%%:*}.r" 2>/dev/null)" = 0 ]; ok $? "M2: ${pair#*:}"
done
[ -z "$(ls -A "$S/tmpA")" ] && [ -z "$(ls -A "$S/tmpB")" ]; ok $? "M2: no lock file was left in either TMPDIR"
# minor: the run_all.sh test hooks are refused without RUN_ALL_NESTED
( cd "$S/rl-cwd" && env -u RUN_ALL_NESTED RUN_ALL_TAKE_FLOWS="$S/b1flow" RUN_ALL_RAW="$S/rl-raw2" timeout 20 bash "$RA" --lock-only > "$S/hook.txt" 2>&1; echo $? > "$S/hook.rc" )
[ "$(cat "$S/hook.rc" 2>/dev/null)" = 2 ] && grep -q "REFUSED: RUN_ALL_TAKE_FLOWS is a test hook" "$S/hook.txt"; ok $? "RUN_ALL_TAKE_FLOWS without RUN_ALL_NESTED is refused, exit 2 (got exit $(cat "$S/hook.rc" 2>/dev/null))"

# Q5 (round 10c): a checker exit status above 3 is shown and returned as 3 (also with --write-warn-pin); the real codes of --write-warn-pin are 4 (written), 1 (FAIL), 2 (refused), 3 (checker broke)
for n in 3 4 127 137; do
  printf 'import sys\nsys.exit(%s)\n' "$n" > "$S/exit$n.py"
  tk "q5-$n" TAKE_CHECK_TEST=1 TAKE_CHECK_CK="$S/exit$n.py" -- --flows "$P"
  [ "$RC" = 3 ] && has "q5-$n" "its exit status is $n" && has "q5-$n" "FINAL: take_check exit status 3."; ok $? "Q5: a checker that exits $n is shown as $n and the take exits 3 (got exit $RC)"
done
tk q5w TAKE_CHECK_TEST=1 TAKE_CHECK_CK="$S/exit127.py" -- --flows "$P" --write-warn-pin "$S/q5w.pin"
[ "$RC" = 3 ] && [ ! -e "$S/q5w.pin" ]; ok $? "Q5: --write-warn-pin with a checker that exits 127 writes nothing and exits 3 (got exit $RC)"

# count change without an orphan (coordinator item): one extra step is wired in (Receive -> ExtraNode -> ReplyRan), so nothing is unreachable, but 16 steps are not the expected 15
for f in mf-form.json mf-hook.json; do
  cp -r -- "$P" "$S/count-$f"
  python3 -I - "$S/count-$f/$f" <<'PYEOF'
import json, sys
p = sys.argv[1]
j = json.load(open(p, encoding="utf-8"))
j["nodes"].append({"id": "extra-node-0001", "name": "ExtraNode", "type": "n8n-nodes-base.noOp", "typeVersion": 1, "position": [0, 0], "parameters": {}})
c = j["connections"]
c["Receive"]["main"][0].append({"node": "ExtraNode", "type": "main", "index": 0})
c["ExtraNode"] = {"main": [[{"node": "ReplyRan", "type": "main", "index": 0}]]}
json.dump(j, open(p, "w", encoding="utf-8"))
PYEOF
  tk "count-$f" -- --flows "$S/count-$f"
  [ "$RC" = 1 ] && grep -q "^FAIL .*$f node count 16 != expected 15" "$S/count-$f.txt" && ! grep -q -E "^FAIL .*(unreachable|orphan)" "$S/count-$f.txt"; ok $? "count: $f with one extra wired step is exit 1 with a node-count FAIL and no orphan FAIL (got exit $RC)"
done
echo "test_take_check: $((N-BAD)) of $N cases as expected, $BAD not as expected"
[ "$BAD" = 0 ]
