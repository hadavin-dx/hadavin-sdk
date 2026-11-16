. $HOME/hadavin-smoke/env.sh; RI=; BAD=0; if [ -z "$RI" ]; then echo "GATE1 repeat-flag index not filled (lead reads it from drive.py): STOP"; else for X in A B; do python3 -I -c "
import json, sys
f, x, ri = sys.argv[1], sys.argv[2], int(sys.argv[3])
L = [l for l in open(f) if l.startswith('{')]
R = json.loads(L[-1]).get('replies') if L else None
if not isinstance(R, list) or any(not isinstance(r, list) or len(r) <= ri or not isinstance(r[ri], bool) for r in R):
    print('GATE1-' + x + ' FAIL: output shape not as expected (no replies list or repeat flag not true/false): STOP'); sys.exit(1)
rep = [r[ri] for r in R]
print('GATE1-' + x, 'replies=%d repeat_false=%d repeat_true=%d first_repeat=%s' % (len(rep), rep.count(False), rep.count(True), rep[0] if rep else None))
ok = (len(rep) == 2 and rep == [False, True]) if x == 'A' else (len(rep) == 10 and rep.count(False) <= 1)
print('GATE1-' + x, 'PASS' if ok else 'FAIL: STOP')
sys.exit(0 if ok else 1)
" $T/gate1-$X.out $X $RI || BAD=1; done; if [ $BAD = 0 ]; then echo "GATE1 ROW: PASS"; else echo "GATE1 ROW: FAIL: STOP"; fi; fi
