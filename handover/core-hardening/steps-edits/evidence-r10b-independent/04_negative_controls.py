# Negative controls: each mutation is applied to a scratch copy; the checker must exit non-zero.
import subprocess, sys, os, shutil, re, ast
SD = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
EDITS = sys.argv[2]; INP = sys.argv[3]; BSRC = sys.argv[4]
CHK = HERE + '/check_r10b.py'
base = open(EDITS, encoding='utf-8').read()
os.makedirs(SD + '/neg', exist_ok=True)
bt = open(BSRC, encoding='utf-8').read()
banned = ast.literal_eval('(' + re.search(r'BANNED = \((.*?)\n\)', bt, re.S).group(1) + ')')
def rep(old, new, n=1, count=1):
    def f(t):
        assert t.count(old) >= 1, 'mutation target missing: ' + old[:50]
        return t.replace(old, new, count)
    return f
def fakekey(t): return t.replace('## Gates', 'Key sk-' + 'A1b2C3d4' * 3 + '\n\n## Gates', 1)
def dropfence(t):
    i = t.index('\n~~~~\n'); return t[:i] + t[i + 5:]
def addlone(t): return t.replace('## Gates', 'The take starts at 17:00 UTC.\n\n## Gates', 1)
def addbanned(t): return t.replace('## Gates', banned[0] + '\n\n## Gates', 1)
def addaws(t): return t.replace('## Gates', 'Key AKIA' + 'ZZ' * 8 + '\n\n## Gates', 1)
def addemail(t): return t.replace('## Gates', 'Mail ' + 'jane.doe' + '@' + 'gmail' + '.com\n\n## Gates', 1)
M = [
 ('01-old-word-changed-E01', rep('wt\\nlite-int`).\n~~~~\nNEW', 'wt\\nlite-intX`).\n~~~~\nNEW')),
 ('02-old-repeated-E02', None),
 ('03-old-overlap-E07-inside-E06', None),
 ('04-stated-line-changed-E03', rep('### E-03: OWNER-STEPS-realrun-v3.md, line 5,', '### E-03: OWNER-STEPS-realrun-v3.md, line 6,')),
 ('05-utc-time-changed', rep('18:19 UTC', '18:20 UTC')),
 ('06-ist-time-changed', rep('23:49 IST', '23:48 IST')),
 ('07-gate-letter-in-header-E04', rep('status Hold (gate G1), type CONTRADICTION (code-change gate)', 'status Hold (gate G6), type CONTRADICTION (code-change gate)')),
 ('08-hold-label-removed-E04', rep('NEW [HOLD G1: DO NOT APPLY] (exact):', 'NEW (exact):')),
 ('09-secret-shaped-string', fakekey),
 ('10-weekday-wrong', rep('Wed 18 Nov 2026', 'Thu 18 Nov 2026')),
 ('11-apply-now-count-text', rep('**Apply now 42**', '**Apply now 41**')),
 ('12-duplicate-id', rep('### E-12: ', '### E-11: ')),
 ('13-confirmation-letter-gap', rep('\nj. E-56 puts', '\nk. E-56 puts')),
 ('14-ND-number-changed', rep('\n14. **Does the lease', '\n15. **Does the lease')),
 ('15-fence-line-removed', dropfence),
 ('16-gate-definition-renamed', rep('- **G3, second', '- **G9, second')),
 ('17-row-status-changed-to-Hold-no-gate', rep('### E-01: OWNER-STEPS-realrun-v3.md, line 3, status Apply now,', '### E-01: OWNER-STEPS-realrun-v3.md, line 3, status Hold,')),
 ('18-banned-vendor-string', addbanned),
 ('19-lone-utc-time', addlone),
 ('20-hold-label-gate-mismatch-E49', rep('NEW [HOLD G5: DO NOT APPLY]', 'NEW [HOLD G4: DO NOT APPLY]')),
 ('21-index-line-changed', rep('| E-03 | OWNER-STEPS-realrun-v3.md | 5 |', '| E-03 | OWNER-STEPS-realrun-v3.md | 7 |')),
 ('22-aws-key-shaped', addaws),
 ('23-personal-email', addemail),
 ('24-hold-count-text', rep('**Hold 12**', '**Hold 11**')),
 ('25-iso-date-impossible', rep('2026-11-23 18:29 UTC', '2026-11-31 18:29 UTC')),
]
# special mutations needing the original text
t_e06 = re.search(r'### E-06:.*?OLD \(exact\):\n~~~~\n(.*?)\n~~~~', base, re.S).group(1)
t_e07 = re.search(r'### E-07:.*?OLD \(exact\):\n~~~~\n(.*?)\n~~~~', base, re.S).group(1)
t_e02 = re.search(r'### E-02:.*?OLD \(exact\):\n~~~~\n(.*?)\n~~~~', base, re.S).group(1)
M[1] = (M[1][0], rep('OLD (exact):\n~~~~\n' + t_e02 + '\n~~~~', 'OLD (exact):\n~~~~\nthe\n~~~~'))
M[2] = (M[2][0], rep('OLD (exact):\n~~~~\n' + t_e07 + '\n~~~~', 'OLD (exact):\n~~~~\n' + t_e06[4:40] + '\n~~~~'))
# baseline
r0 = subprocess.run([sys.executable, '-B', '-I', CHK, EDITS, INP, BSRC], capture_output=True, text=True)
print('BASELINE rc=%d (must be 0)' % r0.returncode)
res = []
for name, fn in M:
    try: mut = fn(base)
    except AssertionError as e:
        print('MUTATION-NOT-APPLIED', name, e); res.append((name, 'NOT-APPLIED', None)); continue
    p = SD + '/neg/' + name + '.md'
    open(p, 'w', encoding='utf-8').write(mut)
    r = subprocess.run([sys.executable, '-B', '-I', CHK, p, INP, BSRC], capture_output=True, text=True)
    fl = [l for l in r.stdout.split('\n') if l.startswith('FAIL')]
    open(HERE + '/04-negative-controls-raw/' + name + '.txt', 'w').write('rc=%d\n' % r.returncode + r.stdout + r.stderr)
    res.append((name, 'CAUGHT' if r.returncode != 0 else 'NOT-CAUGHT', fl[0][:110] if fl else '-'))
    print('%-45s rc=%d %s | %s' % (name, r.returncode, res[-1][1], res[-1][2]))
# input-file mutation: scratch copy of inputs with the E-01 old text altered
d = SD + '/neg/inputs'; shutil.rmtree(d, ignore_errors=True); shutil.copytree(INP, d)
f = d + '/OWNER-STEPS-realrun-v3.md'; t = open(f, encoding='utf-8').read(); assert 'lite-int`).' in t
open(f, 'w', encoding='utf-8').write(t.replace('lite-int`).', 'lite-int`)!', 1))
r = subprocess.run([sys.executable, '-B', '-I', CHK, EDITS, d, BSRC], capture_output=True, text=True)
open(HERE + '/04-negative-controls-raw/26-input-file-changed.txt', 'w').write('rc=%d\n' % r.returncode + r.stdout)
res.append(('26-input-file-changed', 'CAUGHT' if r.returncode else 'NOT-CAUGHT', ''))
print('26-input-file-changed rc=%d' % r.returncode)
print('SUMMARY caught %d / %d; not caught: %s' % (sum(1 for x in res if x[1] == 'CAUGHT'), len(res), [x[0] for x in res if x[1] != 'CAUGHT']))
