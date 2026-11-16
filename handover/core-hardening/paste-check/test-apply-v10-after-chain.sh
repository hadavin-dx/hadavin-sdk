#!/bin/bash
# Test of apply-v10-after-chain.py on scratch copies only. usage: bash test-apply-v10-after-chain.sh <chained plan, sha 515cf470...> ; makes a new scratch folder with mktemp -d
set -u; D=$(cd "$(dirname "$0")" && pwd); PLAN=$1; W=$(mktemp -d); mkdir "$W/s" "$W/bad"
cp "$D/apply-v10-after-chain.py" "$D/plan-v10-real-v5-edits.md" "$D/plan-v10-corrections-after-chain.md" "$W/s/"
cp "$D/apply-v10-after-chain.py" "$D/plan-v10-real-v5-edits.md" "$D/plan-v10-corrections-after-chain.md" "$W/bad/"
cp "$PLAN" "$W/plan.md"; sha256sum "$PLAN" | cut -c1-16
echo "## T1 good input"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan.md" "$W/out1.md"; echo "rc=$? out_exists=$([ -f "$W/out1.md" ] && echo yes || echo no) sha=$(sha256sum "$W/out1.md" | cut -c1-16)"
EXP=28f92c5d1211207cce0222c87bb7a6e6dc8e39a21a659624a1a7fe9cc32992ce; GOT=$(sha256sum "$W/out1.md" | cut -d' ' -f1); echo "T1 full sha equals expected: $([ "$GOT" = "$EXP" ] && echo YES || echo NO) lines=$(wc -l < "$W/out1.md")"
echo "## T2 wrong input sha (one byte appended)"; cp "$W/plan.md" "$W/plan-x.md"; printf 'x' >> "$W/plan-x.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan-x.md" "$W/out2.md"; echo "rc=$? out_exists=$([ -f "$W/out2.md" ] && echo yes || echo no)"
echo "## T3 wrong input: only the first 100 lines of the chained plan"; head -100 "$W/plan.md" > "$W/plan-h.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan-h.md" "$W/out3.md"; echo "rc=$? out_exists=$([ -f "$W/out3.md" ] && echo yes || echo no)"
echo "## T4 equal paths"; cp "$W/plan.md" "$W/eq.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/eq.md" "$W/eq.md"; echo "rc=$? sha_after=$(sha256sum "$W/eq.md" | cut -c1-16)"
echo "## T5 same file by another name (symlink)"; ln -s "$W/plan.md" "$W/link.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan.md" "$W/link.md"; echo "rc=$? sha_after=$(sha256sum "$W/plan.md" | cut -c1-16)"
echo "## T6 output already exists"; echo keep > "$W/exists.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan.md" "$W/exists.md"; echo "rc=$? content=$(cat "$W/exists.md")"
echo "## T7 failed edit (old text of edit 3 damaged in a scratch copy of the edit list)"; python3 -I - "$W/bad/plan-v10-real-v5-edits.md" <<'PYEOF'
import re,sys
p=sys.argv[1]; t=open(p).read(); i=t.index('## Edit 3:'); j=t.index('~~~~old\n',i)+8
t=t[:j]+'ZZZ-NOT-IN-PLAN '+t[j:]; open(p,'w').write(t); print('damaged edit 3 old text')
PYEOF
python3 -I "$W/bad/apply-v10-after-chain.py" "$W/plan.md" "$W/out7.md"; echo "rc=$? out_exists=$([ -f "$W/out7.md" ] && echo yes || echo no)"
echo "## T8 missing output folder"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan.md" "$W/nodir/out.md"; echo "rc=$?"
echo "## T9 wrong argument count"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan.md"; echo "rc=$?"

# RENUMBER variants: each runs on its own scratch copy of the corrections file; the real file is never touched
RN='RENUMBER edits=8,13,27 from=13 to=16 shift=4'
variant() { # $1 label, $2 replacement text for the RENUMBER line ('' = keep an empty line, 'DELETE' = remove the line)
  local d="$W/rn-$1"; mkdir "$d"; cp "$D/apply-v10-after-chain.py" "$D/plan-v10-real-v5-edits.md" "$d/"
  if [ "$2" = DELETE ]; then grep -vF "$RN" "$D/plan-v10-corrections-after-chain.md" > "$d/plan-v10-corrections-after-chain.md"
  else python3 -I -c "import sys;t=open(sys.argv[1],encoding='utf-8').read();assert sys.argv[2] in t;open(sys.argv[4],'w',encoding='utf-8',newline='').write(t.replace(sys.argv[2],sys.argv[3]))" "$D/plan-v10-corrections-after-chain.md" "$RN" "$2" "$d/plan-v10-corrections-after-chain.md"; fi
  python3 -I "$d/apply-v10-after-chain.py" "$W/plan.md" "$d/out.md"; echo "rc=$? out_exists=$([ -f "$d/out.md" ] && echo yes || echo no) sha=$([ -f "$d/out.md" ] && sha256sum "$d/out.md" | cut -c1-16)"; }
echo "## T10 RENUMBER line deleted (must refuse)"; variant del DELETE
echo "## T11 shift=0 (must refuse: edits 8, 13, 27 would not change)"; variant s0 'RENUMBER edits=8,13,27 from=13 to=16 shift=0'
echo "## T12 'shift = 4' with spaces (malformed, must refuse)"; variant sp 'RENUMBER edits=8,13,27 from=13 to=16 shift = 4'
echo "## T13 shift=4 text with a non-integer shift=x (must refuse)"; variant sx 'RENUMBER edits=8,13,27 from=13 to=16 shift=x'
echo "## T14 to=15 (decision: accepted, item 16 is not referenced by edits 8, 13, 27, so the sha must stay 28f92c5d)"; variant to15 'RENUMBER edits=8,13,27 from=13 to=15 shift=4'
echo "## T15 shift=4 but edit list reduced to 8,13 (must refuse: 27 missing)"; variant ed 'RENUMBER edits=8,13 from=13 to=16 shift=4'
echo "## T16 dangling symlink as output (must refuse, nothing created at the target)"; ln -s "$W/nowhere-target.md" "$W/dangling.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan.md" "$W/dangling.md"; echo "rc=$? target_exists=$([ -e "$W/nowhere-target.md" ] && echo yes || echo no)"
echo "## T17 symlink to an existing file as output (must refuse, file untouched)"; echo keep2 > "$W/real2.md"; ln -s "$W/real2.md" "$W/link2.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan.md" "$W/link2.md"; echo "rc=$? content=$(cat "$W/real2.md")"
echo "scratch folder: $W (left in place; nothing in the repository was changed)"
