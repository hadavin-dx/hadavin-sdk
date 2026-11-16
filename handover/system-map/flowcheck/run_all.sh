#!/bin/bash
# run_all.sh OUTDIR : rebuilds everything for the flowcheck from git (branch origin/cloud/flows-audit), no network, made-up data only.
# Writes: OUTDIR/dry-run.txt, build.txt, repro.txt, selftest.txt, changed-files.txt, go1.txt, md/<variant>-<set>.md. Needs: git, python3, patch. Run from the repository root.
set -u; O=${1:?outdir}; O=$(realpath -m "$O"); case "$O" in /tmp/?*) ;; *) echo "OUTDIR must be a folder under /tmp, with a name"; exit 2;; esac; FAIL=0; R=$(pwd); BR=origin/cloud/flows-audit; HERE=$R/handover/system-map/flowcheck
rm -rf "$O"; mkdir -p "$O/md" "$O/src" "$O/committed"; W=$O/src
D=handover/demo; PA=handover/flows-audit/patches
mkdir -p $W/pristine/$D/n8n-mainframe $W/pristine/$D/n8n-flows
for f in build_mainframe.py mf.py; do git show $BR:$D/n8n-mainframe/$f > $W/pristine/$D/n8n-mainframe/$f; done
for f in n8n-flows/mf_leads.sql n8n-flows/PAGE-STATEMENTS-V4.md VIDEO-RUNSHEET.md; do git show $BR:$D/$f > $W/pristine/$D/$f; done
for k in real film; do mkdir -p $O/committed/$k-v5; for f in mf-form mf-hook mf-recovery mf-sub-crm-mail; do git show $BR:$D/n8n-flows-$k-v5/$f.json > $O/committed/$k-v5/$f.json; done; done
P=(F-001-one-ddl F-002-take-key-check-and-claim-error-path F-003-runsheet-claims F-004-page-statement-17 F-008-save-runs-for-the-take)
: > $O/dry-run.txt
for p in "${P[@]}"; do echo "== $p" >> $O/dry-run.txt; git show $BR:$PA/$p.patch > $O/$p.patch; (cd $W/pristine && patch -p1 --dry-run < $O/$p.patch) >> $O/dry-run.txt 2>&1; echo "rc=$?" >> $O/dry-run.txt; done
for v in f002 f008 both rev; do cp -r $W/pristine $W/$v; done
(cd $W/f002 && patch -p1 < $O/${P[1]}.patch); (cd $W/f008 && patch -p1 < $O/${P[4]}.patch)
(cd $W/both && patch -p1 < $O/${P[1]}.patch && patch -p1 < $O/${P[4]}.patch) >> $O/dry-run.txt 2>&1
(cd $W/rev && patch -p1 < $O/${P[4]}.patch && patch -p1 < $O/${P[1]}.patch) >> $O/dry-run.txt 2>&1
diff $W/both/$D/n8n-mainframe/build_mainframe.py $W/rev/$D/n8n-mainframe/build_mainframe.py > /dev/null && echo "order F-002,F-008 and F-008,F-002 give the same file" >> $O/dry-run.txt || echo "ORDER MATTERS" >> $O/dry-run.txt
: > $O/build.txt
for v in pristine f002 f008 both; do ( cd $W/$v/$D/n8n-mainframe
  MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py $O/built/$v/real-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER >/dev/null 2>&1; echo "$v real-v5 rc=$?" >> $O/build.txt
  MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py $O/built/$v/film-v5 PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 >/dev/null 2>&1; echo "$v film-v5 rc=$?" >> $O/build.txt ); done
: > $O/repro.txt; for k in real-v5 film-v5; do diff -r $O/built/pristine/$k $O/committed/$k >> $O/repro.txt 2>&1 && echo "$k: rebuilt from the pristine generator is byte-identical to the committed folder" >> $O/repro.txt; done
for v in pristine f002 f008 both; do for k in real-v5 film-v5; do python3 -I $HERE/tools/flowcheck.py $O/built/$v/$k/*.json > $O/md/$v-$k.md 2>&1; echo "$v $k flowcheck rc=$?" >> $O/build.txt; done; done
for v in f002 f008 both; do for k in real-v5 film-v5; do echo "== $v vs pristine $k"; diff -rq $O/built/pristine/$k $O/built/$v/$k | sed "s#$O/##g"; done; done > $O/changed-files.txt
sed -i "s#$O#OUT#g" $O/md/*.md $O/dry-run.txt
for f in mf-form mf-hook mf-recovery mf-sub-crm-mail; do for k in real film; do [ -f handover/demo3/kill/flows-go1/$f.json ] && cmp -s handover/demo3/kill/flows-go1/$f.json $O/committed/$k-v5/$f.json && echo "go1/$f == $k-v5" || echo "go1/$f differs from (or is missing next to) $k-v5"; done; done > $O/go1.txt 2>&1
python3 -I $HERE/tools/flowcheck.py --selftest > $O/selftest.txt 2>&1; echo "selftest rc=$?" >> $O/selftest.txt
[ -s $O/repro.txt ] && ! grep -q "byte-identical" $O/repro.txt && FAIL=1
grep -q "rc=[1-9]" <(grep -v flowcheck $O/build.txt) && FAIL=1
grep -q "selftest ok" $O/selftest.txt || FAIL=1
[ $(find $O/committed -name '*.json' -size +0 | wc -l) -eq 8 ] || FAIL=1
grep -q "^ORDER MATTERS" $O/dry-run.txt && FAIL=1
echo "done, fail=$FAIL (flowcheck rc=1 per set is expected: the form step has no password)"; exit $FAIL
