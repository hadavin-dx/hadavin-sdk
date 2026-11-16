# Builds EDITS.md (round 9) from EDITS.round8.md plus the round-9 changes. Text only; nothing else is read or run.
import re, collections
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
src = open(D + 'EDITS.round8.md', encoding='utf-8').read()
i_rows = src.index('## The row blocks')
i_tail = src.index('## Lines checked and found consistent')
head8 = src[:i_rows]
rows8 = src[i_rows:i_tail]
tail8 = src[i_tail:]

# ------------------------------------------------------------------ rows: parse
parts = re.split(r'(?m)^(?=### E-\d+: )', rows8)
pre_rows = parts[0]            # '## The row blocks\n'
R = collections.OrderedDict()
for p in parts[1:]:
    rid = re.match(r'### (E-\d+):', p).group(1)
    R[rid] = p.rstrip('\n') + '\n'

def rsub(rid, old, new, count=1):
    assert R[rid].count(old) == count, (rid, old[:60], R[rid].count(old))
    R[rid] = R[rid].replace(old, new)

BLK = re.compile(r'(OLD(?: \d)? \(exact\):|NEW[^\n]*:)\n~~~~\n(.*?)\n~~~~', re.S)

def blocks(rid):
    return BLK.findall(R[rid])

def set_block(rid, kind, text, n=0, label=None):
    """replace the n-th block of that kind (OLD or NEW) text (and optionally its label)"""
    k = 0
    def f(m):
        nonlocal k
        if m.group(1).startswith(kind):
            if k == n:
                k += 1
                return (label or m.group(1)) + '\n~~~~\n' + text + '\n~~~~'
            k += 1
        return m.group(0)
    R[rid] = BLK.sub(f, R[rid])
    assert k > n, (rid, kind, n)

def set_header(rid, newhdr):
    R[rid] = re.sub(r'^### .*$', newhdr, R[rid], count=1, flags=re.M)

def set_why(rid, text):
    i = R[rid].index('\nWhy: ')
    R[rid] = R[rid][:i] + '\nWhy: ' + text + '\n'

def why_add(rid, text):
    assert R[rid].endswith('\n')
    R[rid] = R[rid].rstrip('\n') + ' ' + text + '\n'

def hold_label(rid, gate):
    """prefix every NEW label of a held row with [HOLD Gx: DO NOT APPLY]"""
    def f(m):
        if m.group(1).startswith('NEW'):
            lab = m.group(1)
            if lab == 'NEW (exact):':
                lab = 'NEW [HOLD %s: DO NOT APPLY] (exact):' % gate
            else:
                lab = 'NEW [HOLD %s: DO NOT APPLY]' % gate + lab[3:]
            return lab + '\n~~~~\n' + m.group(2) + '\n~~~~'
        return m.group(0)
    R[rid] = BLK.sub(f, R[rid])

exec(open(D + 'build-r9-rows.py', encoding='utf-8').read())
exec(open(D + 'build-r9-head.py', encoding='utf-8').read())
