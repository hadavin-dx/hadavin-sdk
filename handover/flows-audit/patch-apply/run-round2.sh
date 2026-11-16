#!/bin/bash
# Round 2/3 runner. One command: bash run-round2.sh > raw-round3.txt 2>&1 ; echo $?
# Fresh copy per order and per single-patch case. Aborts (exit 3) on any git apply failure. Exit code = 0 only if every
# apply, generator, checker and negative-test step returned 0. Nothing is run in n8n.
SRC=/home/user/hadavin-sdk/handover/demo
HERE=/home/user/hadavin-sdk/handover/flows-audit/patch-apply
PT=/home/user/hadavin-sdk/handover/flows-audit/patches
CK=$HERE/check_flows.py
W=/tmp/pa13b; rm -rf $W; mkdir -p $W/c $W/g
RC=0
note(){ [ "$1" -ne 0 ] && RC=1; }
mkcopy(){ d=$1; mkdir -p $d/handover/demo/n8n-flows $d/handover/demo/n8n-mainframe
  cp $SRC/n8n-flows/*.json $SRC/n8n-flows/mf_leads.sql $SRC/n8n-flows/PAGE-STATEMENTS-V4.md $d/handover/demo/n8n-flows/
  cp $SRC/VIDEO-RUNSHEET.md $d/handover/demo/; cp $SRC/n8n-mainframe/build_mainframe.py $d/handover/demo/n8n-mainframe/; }
gen(){ # copy-dir out-dir
  ( cd $1/handover/demo/n8n-mainframe && MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py $2/real PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER >$2/real.log 2>&1; r=$?; echo "gen real rc=$r"; [ $r -ne 0 ] && exit 1
    MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py $2/film PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 >$2/film.log 2>&1; r=$?; echo "gen film rc=$r"; [ $r -ne 0 ] && exit 1; exit 0 ); note $?; }
applyorder(){ name=$1; shift; d=$W/c/$name; mkcopy $d; echo "## order $name: $*"
  for p in "$@"; do f=$PT/$p.patch; ( cd $d && git apply --check $f ); a=$?; ( cd $d && git apply $f ); b=$?; echo "$p check=$a apply=$b"
    if [ $a -ne 0 ] || [ $b -ne 0 ]; then echo "ABORT: git apply failed for $p in order $name"; exit 3; fi; done
  find $d -name '*.orig' -o -name '*.rej' | sed 's/^/LEFTOVER /'; mkdir -p $W/g/$name; gen $d $W/g/$name; }
E="--expect mf-recovery.json=10:9 --expect mf-sub-crm-mail.json=20:26"
B="--expect mf-form.json=12:11 --expect mf-hook.json=12:11 $E"
P="--expect mf-form.json=15:14 --expect mf-hook.json=15:14 $E"
F1=F-001-one-ddl; F2=F-002-take-key-check-and-claim-error-path; F3=F-003-runsheet-claims; F4=F-004-page-statement-17; F8=F-008-save-runs-for-the-take
echo "## baseline (unpatched copy)"; mkcopy $W/c/base; mkdir -p $W/g/base; gen $W/c/base $W/g/base
applyorder glob $F1 $F2 $F3 $F4 $F8
applyorder fixplan $F1 $F2 $F8 $F3 $F4
applyorder reverse $F8 $F4 $F3 $F2 $F1
applyorder p28 $F2 $F8
applyorder p82 $F8 $F2
applyorder only002 $F2
applyorder only008 $F8
echo; echo "## byte compare baseline generator vs saved v5 (cmp)"
for v in real film; do for f in mf-form mf-hook mf-recovery mf-sub-crm-mail; do cmp $W/g/base/$v/$f.json $SRC/n8n-flows-$v-v5/$f.json && echo "$v/$f identical"; note $?; done; done
echo; echo "## byte compare of generated JSON against the glob order (cmp), per order"
for o in fixplan reverse p28 p82; do for v in real film; do for f in mf-form mf-hook mf-recovery mf-sub-crm-mail; do cmp -s $W/g/glob/$v/$f.json $W/g/$o/$v/$f.json && echo "$o $v/$f same-as-glob" || echo "$o $v/$f differs-from-glob"; done; done; done
echo; echo "## CHECKER"
for v in real film; do
 echo "######## baseline $v"; python3 -I $CK $W/g/base/$v --baseline $W/g/base/$v $B; r=$?; echo "exit=$r"; note $r
 for o in glob fixplan reverse p28 p82; do
  echo "######## order $o $v"; python3 -I $CK $W/g/$o/$v --baseline $W/g/base/$v $P --patch-checks F002,F008 --diff-base $W/g/base/$v --allow F002,F008 --diff-out $W/diff-$o-$v.txt; r=$?; echo "exit=$r"; note $r; done
 echo "######## F-002 alone $v (fresh)"; python3 -I $CK $W/g/only002/$v --baseline $W/g/base/$v $P --patch-checks F002 --diff-base $W/g/base/$v --allow F002 --quiet-info; r=$?; echo "exit=$r"; note $r
 echo "######## F-008 alone $v (fresh)"; python3 -I $CK $W/g/only008/$v --baseline $W/g/base/$v $B --patch-checks F008 --diff-base $W/g/base/$v --allow F008 --quiet-info; r=$?; echo "exit=$r"; note $r
done
cp $W/diff-glob-real.txt $HERE/diff-base-vs-patched.txt
echo; echo "## NEGATIVE TESTS of the checker"; python3 -I $HERE/checker-negative-tests.py; r=$?; echo "negative exit=$r"; note $r
echo; echo "## AGGREGATE EXIT CODE: $RC"; exit $RC
