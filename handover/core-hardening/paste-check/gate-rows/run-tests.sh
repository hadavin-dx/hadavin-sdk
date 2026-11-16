#!/bin/sh
# usage: run-tests.sh <shell> <plan.md> <scratchdir>   Stand-in env.sh and pgq; made-up data only.
SH=$1; PLAN=$2; W=$3; rm -rf $W; mkdir -p $W/home/hadavin-smoke $W/T
python3 -I - "$PLAN" "$W" <<'PY'
import sys,re
t=open(sys.argv[1]).read(); w=sys.argv[2]
b=re.findall(r'```sh\n(.*?)\n```',t,re.S)
g=[x for x in b if x.startswith('. $HOME/hadavin-smoke/env.sh; RI=')]; h=[x for x in b if x.startswith('( LC_ALL=C')]
assert len(g)==1 and len(h)==1
open(w+'/G1.blk','w').write(g[0]+'\n'); open(w+'/G2.blk','w').write(h[0]+'\n')
PY
cat > $W/home/hadavin-smoke/env.sh <<EOS
T=$W/T
pgq() { if [ -e \$T/pgq.fail ]; then echo "psql: stand-in error" >&2; return 2; fi; cat \$T/pgq.out; }
EOS
G1() { # name RI RIOK : files gate1-A.out gate1-B.out already in place
  echo "-- [$SH] G1 $1"; sed "s/RI=3; RIOK=;/RI=$2; RIOK=$3;/" $W/G1.blk > $W/g1.run; HOME=$W/home T=$W/T $SH $W/g1.run 2>&1; echo "rc=$?"; }
mk() { # file json
  printf '%s\n' "$2" > $W/T/$1; }
J() { python3 -I -c "
import json,sys
print(json.dumps({'replies':[[200,'ok',True,r,e,1] for r,e in zip(eval(sys.argv[1]),eval(sys.argv[2]))]}))" "$1" "$2"; }
F='False'; Tt='True'
A_OK="[False,True]"; E2="[False,False]"; B_OK="[False]+[True]*9"
ok_set() { mk gate1-A.out "$(J "$A_OK" "$E2")"; mk gate1-B.out "$(J "$B_OK" "[False]*10")"; }
echo "######## SHELL: $SH"
ok_set; G1 "pass RI=3 RIOK=yes" 3 yes
G1 "RIOK empty" 3 ""
G1 "RIOK=no" 3 no
G1 "RI empty" "" yes
G1 "RI=abc (not a number, inside the guard)" abc yes
G1 "RI=-1" -1 yes
G1 "RI=4 (n8n_error slot)" 4 yes
G1 "RI=2 (all true)" 2 yes
mk gate1-B.out "$(J "[True]*10" "[False]*10")"; G1 "B zero false (stale or reused id): must FAIL (R2-1)" 3 yes
mk gate1-B.out "$(J "[False,False]+[True]*8" "[False]*10")"; G1 "B two false" 3 yes
mk gate1-B.out "$(J "[False]*10" "[False]*10")"; G1 "B ten false" 3 yes
mk gate1-B.out "$(J "[False]+[True]*8" "[False]*9")"; G1 "B nine replies" 3 yes
mk gate1-B.out "$(J "[False]+[True]*9" "[False]*9+[True]")"; G1 "B one n8n_error" 3 yes
ok_set; mk gate1-A.out "$(J "[True,False]" "$E2")"; G1 "A true then false" 3 yes
mk gate1-A.out "$(J "[False,False]" "$E2")"; G1 "A both false" 3 yes
mk gate1-A.out "$(J "[False]" "[False]")"; G1 "A one reply" 3 yes
mk gate1-A.out "$(J "$A_OK" "[False,True]")"; G1 "A error reply" 3 yes
ok_set; mk gate1-A.out '{"replies":[{"a":1},{"b":2}]}'; G1 "A dict replies" 3 yes
mk gate1-A.out '{"replies":[[200,"ok",true,0,false,1],[200,"ok",true,1,false,1]]}'; G1 "A 0/1 instead of false/true at RI" 3 yes
mk gate1-A.out '{"replies":[[200,"ok",true,false,0,1],[200,"ok",true,true,0,1]]}'; G1 "A 0 instead of false at n8n_error" 3 yes
ok_set; mk gate1-B.out "$(J "$B_OK" "[False]*10")
done: exit 0
not json at all"; G1 "B pass with trailing non-JSON lines (ignored)" 3 yes
mk gate1-B.out "$(J "$B_OK" "[False]*10")
{broken"; G1 "B last line starts with { but is broken" 3 yes
mk gate1-B.out 'plain text only'; G1 "B no JSON" 3 yes
rm -f $T/gate1-B.out $W/T/gate1-B.out; G1 "B file missing" 3 yes
mk gate1-B.out '{"replies":"x"}'; G1 "B replies not a list" 3 yes
ok_set
# ---- G2
G2() { echo "-- [$SH] G2 $1"; HOME=$W/home T=$W/T $SH $W/G2.blk 2>&1; echo "rc=$?"; [ -s $W/T/gate2.err ] && echo "gate2.err holds: $(cat $W/T/gate2.err)"; rm -f $W/T/gate2.err; }
kk() { printf '%b' "$1" > $W/T/keys.txt; }
echo 2 > $W/T/pgq.out; rm -f $W/T/pgq.fail
echo 3 > $W/T/keys-before-s10.txt; kk 'old1\nold2\nB2 oldb\nA ida1\nP idp\nB idb1\n'; G2 "pass: baseline 3, count 2"
echo 2 > $W/T/pgq.out
printf ' 2 \r\n' > $W/T/pgq.out; G2 "count 2 with spaces and CR"
echo 2 > $W/T/pgq.out
kk 'A ida1\r\nB idb1\r\n'; echo 0 > $W/T/keys-before-s10.txt; G2 "CRLF keys, baseline 0"
echo 3 > $W/T/keys-before-s10.txt; kk 'x\ny\nz\nA ida1\n'; G2 "no B line after baseline"
kk 'A stale\nB staleb\nx\n'; G2 "A and B lines only BEFORE baseline (stale rows, R2-2)"
kk 'x\ny\nz\nA ida1\nA ida2\nB idb1\n'; G2 "two different A ids after baseline"
kk 'x\ny\nz\nA ida1\nA ida1\nB idb1\nB idb1\n'; G2 "same A id twice and same B id twice (counts shown)"
kk 'x\ny\nz\nA same\nB same\n'; G2 "A and B same key"
kk "x\ny\nz\nA ida1\nB id'b\n"; G2 "quote in key"
kk 'x\ny\nz\nA ida1\nB idb1\n'
rm -f $W/T/keys-before-s10.txt; G2 "baseline file missing"
echo "" > $W/T/keys-before-s10.txt; G2 "baseline file empty"
echo abc > $W/T/keys-before-s10.txt; G2 "baseline not a number"
echo 3 > $W/T/keys-before-s10.txt
for v in 0 1 3 "" STOP; do printf '%s\n' "$v" > $W/T/pgq.out; G2 "count '$v'"; done
echo 2 > $W/T/pgq.out; touch $W/T/pgq.fail; G2 "pgq fails (stderr to gate2.err)"; rm -f $W/T/pgq.fail
echo 2 > $W/T/pgq.out; kk 'x\ny\nz\nA ida1\nB idb1\n'; HOME=$W/home T=$W/T $SH $W/G2.blk >/dev/null 2>&1; echo "gate2.out saved: $(cat $W/T/gate2.out)"
rm -f $W/T/keys.txt; G2 "keys.txt missing"
echo "-- [$SH] baseline command as pasted in S10 (missing and present keys.txt)"
python3 -I - "$PLAN" > $W/base.cmd <<'PY'
import sys,re
t=open(sys.argv[1]).read()
m=re.search(r'(\{ wc -l < \$T/keys.txt \|\| echo 0; \} 2>/dev/null \| tr -d \' \' > \$T/keys-before-s10.txt;)',t); print(m.group(1))
PY
rm -f $W/T/keys.txt $W/T/keys-before-s10.txt; T=$W/T $SH $W/base.cmd; echo "missing keys.txt -> '$(cat $W/T/keys-before-s10.txt)'"
printf 'a\nb\nc\n' > $W/T/keys.txt; T=$W/T $SH $W/base.cmd; echo "3-line keys.txt -> '$(cat $W/T/keys-before-s10.txt)'"
