#!/bin/bash
# Re-run: bash run.sh   (from any folder; writes only to a mktemp scratch dir, removes it at the end)
H=$(cd "$(dirname "$0")" && pwd); S=$(mktemp -d)
mkdir -p $S/home/hadavin-smoke; : > $S/home/hadavin-smoke/env.sh
case_run() {  # $1 label, $2 flow-values.env text
  export T=$S/t HOME=$S/home; rm -rf $T; mkdir -p $T/flows
  cp $H/input/mf-sub-crm-mail.json $T/flows/; for f in mf-form mf-hook mf-recovery; do echo '[]' > $T/flows/$f.json; done
  printf '%b' "$2" > $T/flow-values.env
  echo "=== case: $1  (flow-values.env CRM_URL line: $(grep -c '^CRM_URL=' $T/flow-values.env) found)"
  bash $H/2.1b.sh 2>&1 | sed "s#$T#\$T#g"
}
case_run "POSITIVE exact http://127.0.0.1:8771" 'CRM_URL=http://127.0.0.1:8771\n'
case_run "NEGATIVE empty value" 'CRM_URL=\n'
case_run "NEGATIVE missing CRM_URL line" 'OTHER=1\n'
case_run "NEGATIVE non-loopback value" 'CRM_URL=https://api.example.com\n'
case_run "NEGATIVE userinfo trick (startswith-style would pass)" 'CRM_URL=http://127.0.0.1:8771@evil.example\n'
case_run "NEGATIVE other loopback port" 'CRM_URL=http://127.0.0.1:9999\n'
case_run "NEGATIVE two CRM_URL lines" 'CRM_URL=http://127.0.0.1:8771\nCRM_URL=http://127.0.0.1:8771\n'
rm -rf $S
