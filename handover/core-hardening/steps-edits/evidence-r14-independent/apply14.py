import sys, os, re
sys.dont_write_bytecode = True
HERE = '/home/user/hadavin-sdk/handover/core-hardening/'
sys.path.insert(0, HERE + 'steps-edits/evidence-r14-independent/')
import chk14
txt = open(HERE + 'steps-edits/EDITS.md', encoding='utf-8').read()
rows = chk14.parse(txt)
cp = {}
for fn in sorted(set(r['file'] for r in rows)): cp[fn] = open(HERE + 'inputs/' + fn, encoding='utf-8').read()
ok = bad = 0; skipped = []
for r in rows:
    if r['status'].split(' (')[0] != 'Apply now': continue
    if not r['new'] or not r['old']: bad += 1; print(r['id'], 'NO OLD OR NEW'); continue
    if len(r['old']) != len(r['new']): print(r['id'], 'old/new count', len(r['old']), len(r['new'])); bad += 1; continue
    good = True
    for o, n in zip(r['old'], r['new']):
        c = cp[r['file']].count(o)
        if c != 1: good = False; print(r['id'], 'OLD matches', c, 'times at apply time (earlier rows may have changed it)'); continue
        cp[r['file']] = cp[r['file']].replace(o, n, 1)
    ok += good; bad += (not good)
    print(r['id'], 'matched' if good else 'NOT MATCHED')
print('Apply now rows', ok + bad, 'matched', ok, 'not matched', bad)
os.makedirs(HERE + 'steps-edits/evidence-r14-independent/scratch-apply/', exist_ok=True)
for fn, t in cp.items():
    open(HERE + 'steps-edits/evidence-r14-independent/scratch-apply/' + fn, 'w', encoding='utf-8').write(t)
    print('scratch', fn, len(t.split('\n')), 'lines')
hold = [r['id'] for r in rows if r['status'].startswith('Hold')]
print('hold rows not applied', hold)
print('HOLD marker text in scratch-apply files:', sum(t.count('[HOLD') for t in cp.values()))
