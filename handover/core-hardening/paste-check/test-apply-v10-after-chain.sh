#!/bin/bash
# Test of apply-v10-after-chain.py on scratch copies only. usage: bash test-apply-v10-after-chain.sh <chained plan, sha 515cf470...> ; makes a new scratch folder with mktemp -d
set -u; D=$(cd "$(dirname "$0")" && pwd); PLAN=$1; W=$(mktemp -d); mkdir "$W/s" "$W/bad"
cp "$D/apply-v10-after-chain.py" "$D/plan-v10-real-v5-edits.md" "$D/plan-v10-corrections-after-chain.md" "$W/s/"
cp "$D/apply-v10-after-chain.py" "$D/plan-v10-real-v5-edits.md" "$D/plan-v10-corrections-after-chain.md" "$W/bad/"
cp "$PLAN" "$W/plan.md"; sha256sum "$PLAN" | cut -c1-16
echo "## T1 good input"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan.md" "$W/out1.md"; echo "rc=$? out_exists=$([ -f "$W/out1.md" ] && echo yes || echo no) sha=$(sha256sum "$W/out1.md" | cut -c1-16)"
echo "## T2 wrong input sha (one byte appended)"; cp "$W/plan.md" "$W/plan-x.md"; printf 'x' >> "$W/plan-x.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan-x.md" "$W/out2.md"; echo "rc=$? out_exists=$([ -f "$W/out2.md" ] && echo yes || echo no)"
echo "## T3 wrong input: the unpatched-shaped file (first 100 lines)"; head -100 "$W/plan.md" > "$W/plan-h.md"; python3 -I "$W/s/apply-v10-after-chain.py" "$W/plan-h.md" "$W/out3.md"; echo "rc=$? out_exists=$([ -f "$W/out3.md" ] && echo yes || echo no)"
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
echo "scratch folder: $W (left in place; nothing in the repository was changed)"
