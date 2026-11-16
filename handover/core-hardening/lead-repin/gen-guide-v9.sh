#!/bin/sh
# gen-guide-v9.sh: makes LEAD-REPIN-VERIFY.v9.md from the template and the numbers inside the script.
#   sh gen-guide-v9.sh --write [SCRIPT]   write the guide
#   sh gen-guide-v9.sh --check [SCRIPT]   exit 0 only if the guide on disk equals what --write would make; else exit 1
# Numbers (planned self-test count, planned start-check count, sha256) are READ from the script, never typed here.
D=$(cd "$(dirname "$0")" && pwd)
MODE=$1; SCRIPT=${2:-$D/lead-repin-verify.v9.sh}
TPL=$D/LEAD-REPIN-VERIFY.v9.template.md; GUIDE=${GUIDE:-$D/LEAD-REPIN-VERIFY.v9.md}
case $MODE in --write|--check) ;; *) echo "usage: sh gen-guide-v9.sh --write|--check [SCRIPT]" >&2; exit 2 ;; esac
ST=$(sed -n 's/^SELFTEST_PLANNED=\([0-9][0-9]*\)$/\1/p' "$SCRIPT")
CP=$(sed -n 's/^CANARY_PLANNED=\([0-9][0-9]*\)$/\1/p' "$SCRIPT")
SH=$(sha256sum "$SCRIPT" | cut -d' ' -f1)
[ -n "$ST" ] && [ -n "$CP" ] && [ -n "$SH" ] || { echo "gen-guide: could not read the numbers from the script" >&2; exit 2; }
MIN=${SELFTEST_MINUTES:-4}
TMP=$(mktemp) || exit 2; trap 'rm -f "$TMP"' EXIT
sed -e "s/{{SELFTEST_PLANNED}}/$ST/g" -e "s/{{CANARY_PLANNED}}/$CP/g" -e "s/{{SHA256}}/$SH/g" -e "s/{{SELFTEST_MINUTES}}/$MIN/g" "$TPL" > "$TMP"
if grep -q '{{' "$TMP"; then echo "gen-guide: a token is left in the guide" >&2; exit 2; fi
if [ "$MODE" = --write ]; then cp "$TMP" "$GUIDE"; echo "written: $GUIDE (selftest=$ST canary=$CP sha256=$SH)"; exit 0; fi
if cmp -s "$TMP" "$GUIDE"; then echo "CHECK OK: guide matches script (selftest=$ST canary=$CP sha256=$SH)"; else echo "CHECK FAIL: guide and script disagree (script says selftest=$ST canary=$CP sha256=$SH)"; exit 1; fi
