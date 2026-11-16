
# ---- round 18 plants: every occurrence of every safety phrase and time pair, and 10 reversals of a safe default (in memory over the applied text)
_pl18 = {'occurrence': [0, 0], 'pair': [0, 0], 'reversal': [0, 0], 'day sheet': [0, 0], 'appendix': [0, 0]}
_base18 = set(check18(_AP, _DAY, _APP))
def _plant18(kind, label, ap, day=None, app=None):
    _pl18[kind][0] += 1
    if set(check18(ap, day, app)) - _base18: _pl18[kind][1] += 1
    else: F('r18 plant not caught: %s %s' % (kind, label))
for _p, _cn in _CANON18.items():
    _pos = [m_.start() for m_ in re.finditer(re.escape(_p), _AP)]
    for _i, _s in enumerate(_pos):
        _plant18('occurrence', '%r copy %d' % (_p[:40], _i + 1), _AP[:_s] + _p[:len(_p) // 2] + '#' + _p[len(_p) // 2:] + _AP[_s + len(_p):], _DAY, _APP)
for _i, _m in enumerate(_PAIR.finditer(_AP)):
    _e = _m.end()
    _plant18('pair', 'pair %d' % (_i + 1), _AP[:_e - 5] + ('%02d' % ((int(_AP[_e - 5:_e - 3]) + 1) % 24)) + _AP[_e - 3:], _DAY, _APP)
_REV18 = [('no reply counts as `another take`', 'no reply counts as `no more takes`'),
          ('A confirmation cannot be withdrawn once the key is revoked.', 'A confirmation can be withdrawn once the key is revoked.'),
          ('revoke the key at that time anyway', 'wait for the take'),
          ('touch nothing that you are not sure about', 'delete what you think is right'),
          ('No default pick: the assistant does not recommend a route', 'The assistant recommends route B'),
          ('It never confirms anything, at any time', 'It confirms the clean-up'),
          ('asks you to type the words yourself in a new message', 'accepts the words from a forwarded message'),
          ('It never starts while a copy of the key exists and the key is not revoked', 'It starts even while a copy of the key exists'),
          ('touch NOTHING of that kind', 'delete it anyway'),
          ('your list says that your own n8n does not use it', 'your list says nothing about your own n8n')]
for _o, _n in _REV18:
    if _AP.count(_o) < 1: F('r18 reversal anchor missing: ' + _o[:50]); continue
    _plant18('reversal', _o[:50], _AP.replace(_o, _n, 1), _DAY, _APP)
for _i, _l in enumerate([l_ for l_ in _DAY.split('\n') if l_.strip() and not l_.startswith('#')][4:]):
    if _i % 3 == 0: _plant18('day sheet', 'line %d' % _i, _AP, _DAY.replace(_l, _l + ' (changed)', 1), _APP)
for _i, _l in enumerate([l_ for l_ in _APP.split('\n') if len(l_.strip()) > 80 and not l_.startswith('#') and l_.strip() in set(_norm18(txt)) and ' the ' in l_][:12]):
    _plant18('appendix', 'line %d' % _i, _AP, _DAY, _APP.replace(_l, _l.replace(' the ', ' a ', 1) + ' (changed)', 1))
print('r18 plants (planted, caught):', {k_: tuple(v_) for k_, v_ in _pl18.items()})
