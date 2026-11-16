"""Plants hostile mutations on copies of EDITS.orig.md; runs verify16.py (builder) and mychk16.py (own). Banned and key-shaped samples are built from parts at run time.
Caught = FAIL lines differ from the unmutated baseline."""
import os, re, subprocess, sys, ast, json
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, H)
import mychk16
SRC = open(os.path.join(H, 'EDITS.orig.md'), encoding='utf-8').read()
V = os.path.join(H, 'a', 'b', 'steps-edits', 'verify16.py')
bl = mychk16.banned_list()
def row(rid, t):
    i = t.index('\n### %s: ' % rid) + 1
    m = re.compile(r'\n### E-\d\d: |\n## Appendix K').search(t, i + 5)
    return i, (m.start() + 1 if m else len(t))
M = []
def m(name, old, new, rid=None, nth=1, allocc=False):
    M.append((name, old, new, rid, nth, allocc))
E48 = 'E-48'
E48='E-48'
m('B01 alarm 3 name drops now', 'named `10 minutes left: revoke the secret key for the model now`', 'named `10 minutes left: revoke the secret key for the model`', E48)
m('B02 route B recommended -> A', 'the assistant recommends route B', 'the assistant recommends route A', E48)
m('B03 shred check (2) drop no space rule', 'It contains no `..`, no space, no quote sign', 'It contains no `..`, no quote sign', E48)
m('B04 K-A window 10 min -> 20 min words', 'The spending window ends at 18:29 UTC = 23:59 IST; the 10 minutes between', 'The spending window ends at 18:29 UTC = 23:59 IST; the 20 minutes between')
m('B05 step 21 heading time 18:19->18:21 consistent pair', 'Watch the cut by Mon 23 Nov 2026 18:19 UTC = 23:49 IST', 'Watch the cut by Mon 23 Nov 2026 18:21 UTC = 23:51 IST')
m('B06 step 22 heading deadline weekday Mon->Sun', 'Retirement, by Mon 23 Nov 18:29 UTC (23:59 IST)', 'Retirement, by Sun 23 Nov 18:29 UTC (23:59 IST)')
m('B07 E-48 shred part (b) own list dropped', '(b) the files on YOUR OWN LIST of copies of the old key, a list that you wrote by hand on paper or on your phone BEFORE the take', '(b) the files on your list', E48)
m('B08 key step E: the assistant never opens key file removed', 'The assistant never opens the key file (this is a procedure, not enforced by a program).', '', E48)
m('B09 D.3 no reply counts as more takes -> counts as no more takes', 'no reply counts as `more takes`; in route B', 'no reply counts as `no more takes`; in route B', E48)
m('B10 K step: revoke anyway wording', 'tell the assistant at once and revoke the key at that time anyway (key step I)', 'tell the assistant at once and wait for the take (key step I)', E48)
m('B11 E-62 any other contact -> delete them', 'or any other contact, you delete nothing and tell the assistant', 'or any other contact, you delete them and tell the assistant', 'E-62')
m('B12 Hold row label HOLD removed (E-04)', 'NEW [HOLD G1: DO NOT APPLY] (exact):', 'NEW (exact):', 'E-04')
m('B13 key list screenshot crop dropped', ', cropped so that it shows the key names and dates but no account name, no web address and no key characters', '', E48)
m('B14 take folder prefix rule weakened', 'the path starts with the full path of the take folder followed by `/`', 'the path starts with the full path of the take folder', E48)
def apply(t, mu):
    name, old, new, rid, nth, allocc = mu
    if callable(old):
        return old(t)
    if rid:
        i, j = row(rid, t); seg = t[i:j]
        if old not in seg: return None
        seg = seg.replace(old, new, 1); return t[:i] + seg + t[j:]
    if old not in t: return None
    return t.replace(old, new) if allocc else t.replace(old, new, 1)

def run_v(path):
    env = dict(os.environ, EDITS_PATH=path, NO_NEG='1')
    p = subprocess.run([sys.executable, '-I', V], env=env, capture_output=True, text=True, cwd=os.path.dirname(V))
    return sorted(l[:160] for l in p.stdout.split('\n') if l.startswith('FAIL'))
base_v = run_v(os.path.join(H, 'EDITS.orig.md'))
base_m = sorted(mychk16.check(SRC))
res = []
tmp = os.path.join(H, 'mut-tmp.md')
for mu in M:
    t = apply(SRC, mu)
    if t is None: res.append((mu[0], 'ANCHOR MISSING', '', '')); continue
    if t == SRC: res.append((mu[0], 'NO CHANGE', '', '')); continue
    open(tmp, 'w', encoding='utf-8').write(t)
    v = run_v(tmp); new_v = [x for x in v if x not in base_v]
    mm = sorted(mychk16.check(t)); new_m = [x for x in mm if x not in base_m]
    res.append((mu[0], bool(new_v), bool(new_m), (new_v[0][:90] if new_v else ''), (new_m[0][:90] if new_m else '')))
os.remove(tmp)
json.dump(res, open(os.path.join(H, 'mut-results-B.json'), 'w'), indent=1)
bv = sum(1 for r in res if r[1] is True); bm = sum(1 for r in res if r[2] is True)
print('planted', len(res), 'verify16 caught', bv, 'mychk16 caught', bm)
for r in res: print(r)
