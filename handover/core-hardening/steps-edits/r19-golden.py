# ================= round 19 golden pins (class fix for the 6 misses of r18: every sentence of EDITS.md is pinned ONCE against r19-pins.txt, not only against its own copies) =================
import collections as _col
def _sent19(t):
    out = []
    for l_ in t.split('\n'):
        l_ = l_.strip()
        if not l_: continue
        out += [s_.strip() for s_ in re.split(r'(?<=[.!?;]) +', l_) if s_.strip()]
    return out
_PINF = os.path.join(HERE_, 'r19-pins.txt')
_PINS = {}
if os.path.exists(_PINF):
    for _ln in open(_PINF, encoding='utf-8').read().split('\n'):
        if '\t' in _ln:
            _n, _s = _ln.split('\t', 1); _PINS[_s] = int(_n)
else:
    F('r19 pin file r19-pins.txt is missing')
def golden19(t):
    c_ = _col.Counter(_sent19(t)); out = []
    for s_, n_ in c_.items():
        if s_ not in _PINS: out.append('sentence not pinned: ' + s_[:90])
        elif _PINS[s_] != n_: out.append('sentence copies %d, pinned %d: %s' % (n_, _PINS[s_], s_[:70]))
    for s_, n_ in _PINS.items():
        if s_ not in c_: out.append('pinned sentence missing: ' + s_[:90])
    return out
_g19 = golden19(txt)
for _f in _g19[:40]: F('r19 golden ' + _f)
if len(_g19) > 40: F('r19 golden: %d more differences' % (len(_g19) - 40))
# the numbers of the changes file: every number written before "words" or "lines" must be a computed number
_CHGF = os.path.join(HERE_, 'r19-CHANGES.md')
def _allowed19():
    wc_ = len(_AP.split()); a_ = {wc_, len(_DAY.split()), len(_APP.split()), 6300, wc_ - 6300, txt.count('\n'), txt.count('\n') + 1}
    for v_ in list(_wc.values()): a_.add(v_); a_.add(wc_ - v_)
    return a_
def chg19(t):
    out = []; al_ = _allowed19()
    for m_ in re.finditer(r'(\d[\d,]*) (?:words|lines)\b', t):
        v_ = int(m_.group(1).replace(',', ''))
        if v_ >= 100 and v_ not in al_: out.append('number not computed: ' + m_.group(0))
    for k_, v_ in (('EDITS.md lines (wc -l): ', txt.count('\n')), ('applied sheet words (wc -w): ', len(_AP.split())), ('day sheet words (wc -w): ', len(_DAY.split())), ('appendix words (wc -w): ', len(_APP.split()))):
        if (k_ + '%d' % v_) not in t.replace(',', ''): out.append('fact line missing or wrong: ' + k_)
    return out
if os.path.exists(_CHGF):
    for _f in chg19(open(_CHGF, encoding='utf-8').read()): F('r19 changes ' + _f)
else: F('r19 changes file r19-CHANGES.md is missing')
print('r19 golden: %d pinned sentences, %d differences' % (len(_PINS), len(_g19)))
