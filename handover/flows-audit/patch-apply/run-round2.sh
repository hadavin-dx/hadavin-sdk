#!/bin/bash
# Round 2 runner. Fresh copies per order. Nothing is run in n8n.
SRC=/home/user/hadavin-sdk/handover/demo
PT=/home/user/hadavin-sdk/handover/flows-audit/patches
CK=/home/user/hadavin-sdk/handover/flows-audit/patch-apply/check_flows.py
W=/tmp/pa13b; rm -rf $W/c $W/g; mkdir -p $W/c $W/g
mkcopy(){ d=$1; mkdir -p $d/handover/demo/n8n-flows $d/handover/demo/n8n-mainframe
  cp $SRC/n8n-flows/*.json $SRC/n8n-flows/mf_leads.sql $SRC/n8n-flows/PAGE-STATEMENTS-V4.md $d/handover/demo/n8n-flows/
  cp $SRC/VIDEO-RUNSHEET.md $d/handover/demo/; cp $SRC/n8n-mainframe/build_mainframe.py $d/handover/demo/n8n-mainframe/; }
gen(){ # copy-dir out-dir
  ( cd $1/handover/demo/n8n-mainframe && MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py $2/real PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER >$2/real.log 2>&1; echo "gen real rc=$?"
    MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py $2/film PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 >$2/film.log 2>&1; echo "gen film rc=$?" ); }
applyorder(){ name=$1; shift; d=$W/c/$name; mkcopy $d; echo "## order $name: $*"
  for p in "$@"; do f=$PT/$p.patch; ( cd $d && git apply --check $f ); a=$?; ( cd $d && git apply $f ); b=$?; echo "$p check=$a apply=$b"; done
  find $d -name '*.orig' -o -name '*.rej' | sed 's/^/LEFTOVER /'; mkdir -p $W/g/$name; gen $d $W/g/$name; }
E="--expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26"
B="--expect mf-form.json=12:11 --expect mf-hook.json=12:11 $E"
P="--expect mf-form.json=15:14 --expect mf-hook.json=15:14 $E"
F1=F-001-one-ddl; F2=F-002-take-key-check-and-claim-error-path; F3=F-003-runsheet-claims; F4=F-004-page-statement-17; F8=F-008-save-runs-for-the-take
echo "## baseline (unpatched copy)"; mkcopy $W/c/base; mkdir -p $W/g/base; gen $W/c/base $W/g/base
applyorder plan $F1 $F2 $F3 $F4 $F8
applyorder reverse $F8 $F4 $F3 $F2 $F1
applyorder p28 $F2 $F8
applyorder p82 $F8 $F2
echo; echo "## byte compare baseline generator vs saved v5 (cmp)"
for v in real film; do for f in mf-form mf-hook mf-recovery mf-sub-crm-mail; do cmp $W/g/base/$v/$f.json $SRC/n8n-flows-$v-v5/$f.json && echo "$v/$f identical"; done; done
echo; echo "## CHECKER"
for v in real film; do
 echo "######## baseline $v"; python3 -I $CK $W/g/base/$v --baseline $W/g/base/$v $B; echo "exit=$?"
 for o in plan reverse p28 p82; do
  echo "######## order $o $v"; python3 -I $CK $W/g/$o/$v --baseline $W/g/base/$v $P --patch-checks F002,F008 --diff-base $W/g/base/$v --allow F002,F008 --diff-out $W/diff-$o-$v.txt; echo "exit=$?"; done
done
echo "######## F-002 alone? (from earlier run, /tmp/pa13/gen) and F-008 alone"
for v in real film; do
 echo "#### F-002 alone $v"; python3 -I $CK /tmp/pa13/gen/F-002-take-key-check-and-claim-error-path/$v --baseline $W/g/base/$v $P --patch-checks F002 --diff-base $W/g/base/$v --allow F002 --quiet-info | tail -25; echo "exit=${PIPESTATUS[0]}"
 echo "#### F-008 alone $v"; python3 -I $CK /tmp/pa13/gen/F-008-save-runs-for-the-take/$v --baseline $W/g/base/$v $B --patch-checks F008 --diff-base $W/g/base/$v --allow F008 --quiet-info | tail -12; echo "exit=${PIPESTATUS[0]}"
done
