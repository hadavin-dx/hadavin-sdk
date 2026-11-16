#!/bin/bash
# F8 runner. Usage: bash run_all.sh [WORKDIR]   (default /tmp/fc8). Builds the patched flows (F-002 + F-008 on a copy, generator run),
# then runs two background checker processes in parallel (pristine = committed v5 folders, patched = generated), each bounded by timeout 300.
# Nothing is run in n8n. Raw output: WORKDIR/*.txt and copied to ./raw/.
W=${1:-/tmp/fc8}; HERE=$(cd "$(dirname "$0")" && pwd); D=$HERE/../../demo; PT=$HERE/../patches; CK=$HERE/check_flows.py
rm -rf $W; mkdir -p $W/c/handover/demo/n8n-flows $W/c/handover/demo/n8n-mainframe $W/g $HERE/raw
cp $D/n8n-flows/*.json $D/n8n-flows/mf_leads.sql $D/n8n-flows/PAGE-STATEMENTS-V4.md $W/c/handover/demo/n8n-flows/; cp $D/VIDEO-RUNSHEET.md $W/c/handover/demo/; cp $D/n8n-mainframe/build_mainframe.py $W/c/handover/demo/n8n-mainframe/
for p in F-002-take-key-check-and-claim-error-path F-008-save-runs-for-the-take; do (cd $W/c && git apply --check $PT/$p.patch && git apply $PT/$p.patch) || { echo "ABORT: git apply $p"; exit 3; }; echo "applied $p"; done
cd $W/c/handover/demo/n8n-mainframe && MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py $W/g/real PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER >$W/gen-real.log 2>&1 || { echo "ABORT gen real"; exit 3; }
MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py $W/g/film PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 >$W/gen-film.log 2>&1 || { echo "ABORT gen film"; exit 3; }
cd $HERE
E="--expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26"
( for v in real film; do echo "######## PRISTINE $v (committed n8n-flows-$v-v5)"; timeout 300 python3 -I $CK $D/n8n-flows-$v-v5 --baseline $D/n8n-flows-$v-v5 --expect mf-form.json=12:11 --expect mf-hook.json=12:11 $E --table; echo "exit=$?"; done ) > $W/pristine.txt 2>&1 &
P1=$!
( for v in real film; do echo "######## PATCHED $v (F-002 + F-008, generated)"; timeout 300 python3 -I $CK $W/g/$v --baseline $D/n8n-flows-$v-v5 --expect mf-form.json=15:14 --expect mf-hook.json=15:14 $E --patch-checks F002,F008 --diff-base $D/n8n-flows-$v-v5 --allow F002,F008 --diff-out $W/diff-$v.txt --table; echo "exit=$?"; done ) > $W/patched.txt 2>&1 &
P2=$!
wait $P1; echo "pristine process done"; wait $P2; echo "patched process done"
cp $W/pristine.txt $W/patched.txt $W/diff-*.txt $HERE/raw/
grep -h -E "^exit=|^RESULT" $W/pristine.txt $W/patched.txt
