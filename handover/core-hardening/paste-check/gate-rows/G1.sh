. $HOME/hadavin-smoke/env.sh; RI=3; RIOK=; BAD=0; if [ -z "$RI" ] || [ "$RIOK" != yes ]; then echo "GATE1 RI=$RI (from plan line 353 of v5, UNVERIFIED) not confirmed: the lead writes the PROGRESS line LEAD-GO RIOK <UTC time> after reading drive.py and the runner then copies RIOK=yes: STOP"; else for X in A B; do python3 -I -c "
import json, sys
f, x = sys.argv[1], sys.argv[2]
try:
    ri = int(sys.argv[3])
except Exception:
    ri = -1
try:
    L = [l for l in open(f) if l.startswith('{')]
    R = json.loads(L[-1]).get('replies') if L else None
except Exception:
    R = None
if ri < 0 or ri == 4 or not isinstance(R, list) or any(not isinstance(r, list) or len(r) <= max(ri, 4) or not isinstance(r[ri], bool) or not isinstance(r[4], bool) for r in R):
    print('GATE1-' + x + ' FAIL: output shape not as expected (RI not a number 0 or more and not 4, no replies list, repeat flag or n8n_error not true/false): STOP'); sys.exit(1)
rep = [r[ri] for r in R]
err = sum(1 for r in R if r[4])
print('GATE1-' + x, 'replies=%d repeat_false=%d repeat_true=%d first_repeat=%s n8n_error_true=%d' % (len(rep), rep.count(False), rep.count(True), rep[0] if rep else None, err))
ok = err == 0 and ((len(rep) == 2 and rep == [False, True]) if x == 'A' else (len(rep) == 10 and rep.count(False) == 1))
print('GATE1-' + x, 'PASS' if ok else 'FAIL: STOP')
sys.exit(0 if ok else 1)
" $T/gate1-$X.out $X $RI || BAD=1; done; if [ $BAD = 0 ]; then echo "GATE1 ROW: PASS"; else echo "GATE1 ROW: FAIL: STOP"; fi; fi
