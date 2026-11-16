#!/usr/bin/env python3
"""Independent checker for EDITS.md round 12. Usage: check_r12.py EDITS_PATH INPUTS_DIR [-q]
Prints FAIL lines; exit code = 1 if any FAIL. Does not import the builder's verify12.py."""
import sys, re, ast, datetime, collections, os

def parse(txt):
    lines = txt.split('\n')
    rows, cur, infence, label, buf, start = [], None, False, None, [], 0
    hdr = re.compile(r'^### (E-\d+): (\S+), line (\d+)(?: \(and (\d+)\))?, status (.+), type (.+)$')
    prev_nonempty = ''
    for i, ln in enumerate(lines, 1):
        if ln == '~~~~':
            if not infence:
                infence, buf, start, label = True, [], i, prev_nonempty
            else:
                infence = False
                if cur is not None:
                    kind = 'OLD' if label.startswith('OLD') else ('NEW' if label.startswith('NEW') else '?')
                    cur['blocks'].append(dict(kind=kind, label=label, text='\n'.join(buf), line=start))
            continue
        if infence:
            buf.append(ln); continue
        m = hdr.match(ln)
        if m:
            cur = dict(id=m.group(1), file=m.group(2), line=int(m.group(3)), line2=int(m.group(4)) if m.group(4) else None,
                       status=m.group(5), type=m.group(6), blocks=[], hline=i)
            rows.append(cur)
        elif ln.startswith('## ') or (ln.startswith('### ') and not m):
            cur = None if ln.startswith('## ') else cur
        if ln.strip(): prev_nonempty = ln
    return lines, rows, infence

def run(edits, inputs, quiet=False):
    fails = []
    def F(m): fails.append(m)
    info = []
    txt = open(edits, encoding='utf-8').read()
    lines, rows, openfence = parse(txt)
    if openfence: F('unterminated fence')
    nfence = sum(1 for l in lines if l == '~~~~')
    if nfence % 2: F(f'odd fence line count {nfence}')
    # ---- ids
    ids = [r['id'] for r in rows]
    if len(ids) != 56: F(f'row count {len(ids)} != 56')
    if len(set(ids)) != len(ids): F('duplicate row ids: ' + str([k for k, v in collections.Counter(ids).items() if v > 1]))
    want = ['E-%02d' % n for n in range(1, 59) if n not in (10, 35)]
    if sorted(set(ids)) != want: F('id set differs: ' + str(sorted(set(want) ^ set(ids))))
    # ---- status
    def stat(r): return r['status'].split(' (')[0].strip()
    stc = collections.Counter(stat(r) for r in rows)
    for s in stc:
        if s not in ('Apply now', 'Hold', 'Conditional'): F('unknown status ' + s)
    # ---- row structure
    for r in rows:
        olds = [b for b in r['blocks'] if b['kind'] == 'OLD']
        news = [b for b in r['blocks'] if b['kind'] == 'NEW']
        if not olds: F(r['id'] + ' no OLD block')
        if not news: F(r['id'] + ' no NEW block')
        if r['id'] != 'E-13' and r['line2'] is None and len(olds) != 1: info.append(f"{r['id']} has {len(olds)} OLD blocks")
    # ---- OLD in inputs, once, at stated line
    cache, spans, nold = {}, collections.defaultdict(list), 0
    for r in rows:
        p = os.path.join(inputs, r['file'])
        if not os.path.exists(p): F(f"{r['id']} input missing {r['file']}"); continue
        if p not in cache: cache[p] = open(p, encoding='utf-8').read()
        full = cache[p]
        stated = {r['line']} | ({r['line2']} if r['line2'] else set())
        for b in [b for b in r['blocks'] if b['kind'] == 'OLD']:
            nold += 1
            o = b['text']
            if o == '': F(r['id'] + ' empty OLD'); continue
            c = full.count(o)
            if c != 1: F(f"{r['id']} OLD occurs {c} times in {r['file']}"); continue
            pos = full.index(o)
            ln = full.count('\n', 0, pos) + 1
            if ln not in stated: F(f"{r['id']} OLD at line {ln}, stated {sorted(stated)}")
            spans[p].append((pos, pos + len(o), r['id']))
    for p, sp in spans.items():
        sp.sort()
        for a, b in zip(sp, sp[1:]):
            if b[0] < a[1]: F(f'OLD spans overlap {a[2]} {b[2]}')
    # ---- counts in the file's own text
    cs = txt[txt.index('## Counts'):txt.index('## NOT DECIDED')] if '## Counts' in txt and '## NOT DECIDED' in txt else ''
    m = re.search(r'\*\*Apply now (\d+)\*\*, \*\*Hold (\d+)\*\*, \*\*Conditional (\d+)\*\*', cs)
    if not m: F('counts sentence missing')
    else:
        if (int(m.group(1)), int(m.group(2)), int(m.group(3))) != (stc['Apply now'], stc['Hold'], stc['Conditional']):
            F(f'status counts text {m.groups()} vs headers {dict(stc)}')
    m = re.search(r'(\d+) rows in total', cs)
    if not m or int(m.group(1)) != len(rows): F('rows-in-total text differs')
    fc = collections.Counter(r['file'] for r in rows)
    m = re.search(r'OWNER-STEPS (\d+) rows, AGENT-SCOPE (\d+) rows, DECISION-one-store (\d+) rows', cs)
    if not m or tuple(map(int, m.groups())) != (fc['OWNER-STEPS-realrun-v3.md'], fc['AGENT-SCOPE-DO-AND-DONT.md'], fc['DECISION-one-store.md']): F('per-file counts differ')
    m = re.search(r'Apply now ids \((\d+)\) are: ([^.]*)\.', cs)
    an = [r['id'] for r in rows if stat(r) == 'Apply now']
    if not m or [x.strip() for x in m.group(2).split(',')] != an or int(m.group(1)) != len(an): F('Apply now id list in text differs')
    hl = [r['id'] for r in rows if stat(r) == 'Hold']
    m = re.search(r'the Hold rows are ([^)]*)\)', cs)
    if not m or [x.strip() for x in m.group(1).split(',')] != hl: F('Hold id list in text differs')
    # ---- hold blocks
    hb = 0
    gates_def = set(re.findall(r'\*\*(G\d)\b', txt[txt.index('## Gates'):txt.index('## How the rows are used')])) if '## Gates' in txt else set()
    for r in rows:
        held = stat(r) == 'Hold'
        gm = re.search(r'gate (G\d)', r['status'])
        if held and not gm: F(r['id'] + ' Hold without gate')
        if held and gm and gm.group(1) not in gates_def: F(r['id'] + ' gate not defined')
        for b in r['blocks']:
            if b['kind'] != 'NEW': continue
            lm = re.match(r'NEW \[HOLD (G\w+): DO NOT APPLY\]', b['label'])
            if lm: hb += 1
            if held and not lm: F(f"{r['id']} Hold row has NEW block without hold marker")
            if held and lm and gm and lm.group(1) != gm.group(1): F(f"{r['id']} marker {lm.group(1)} vs header {gm.group(1)}")
            if not held and lm: F(f"{r['id']} non-hold row has hold marker")
            if not held and 'HOLD' in b['label']: F(f"{r['id']} non-hold label has HOLD")
    if hb != 13: F(f'hold-marked NEW blocks {hb} != 13')
    # ---- times
    def outside_old(t):
        return re.sub(r'(?m)^OLD(?: \d)? \(exact\):\n~~~~\n.*?\n~~~~$', '', t, flags=re.S)
    body = outside_old(txt)
    pair = re.compile(r'(\d{1,2}):(\d{2}) UTC(?: = | \()(\d{1,2}):(\d{2}) IST')
    paired_spans = []
    for m in pair.finditer(body):
        u = int(m.group(1)) * 60 + int(m.group(2)); i = int(m.group(3)) * 60 + int(m.group(4))
        if (i - u) % 1440 != 330: F('UTC/IST pair not +5:30: ' + m.group(0))
        paired_spans.append((m.start(), m.end()))
    def inpair(pos): return any(a <= pos < b for a, b in paired_spans)
    for m in re.finditer(r'\b(\d{1,2}):(\d{2})\b(?!Z)', body):
        if not inpair(m.start()):
            ctx = body[max(0, m.start() - 30):m.end() + 12].replace('\n', ' ')
            F('time outside a UTC/IST pair: ' + ctx)
    for m in re.finditer(r'\b\d{1,2}:\d{2} (?:UTC|IST)\b', body):
        if not inpair(m.start()): F('UTC or IST time not in a pair: ' + body[max(0, m.start() - 30):m.end() + 12].replace('\n', ' '))
    # deadlines: whole-file consistency
    pairs_all = collections.Counter(m.group(0).split(' IST')[0] for m in pair.finditer(txt))
    for want_u, want_i in (('18:19', '23:49'), ('18:04', '23:34'), ('18:29', '23:59'), ('18:14', '23:44')):
        for m in re.finditer(re.escape(want_u) + r' UTC', body):
            if not re.match(r' (?:=|\()' + r' ?' + re.escape(want_i) + r' IST', body[m.end():m.end() + 14]): F(f'{want_u} UTC not paired with {want_i}')
        for m in re.finditer(re.escape(want_i) + r' IST', body):
            if not body[max(0, m.start() - 16):m.start()].rstrip(' =(').endswith(want_u + ' UTC'): F(f'{want_i} IST not preceded by {want_u} UTC')
    # context rules (160 chars before the time, same line)
    for m in pair.finditer(body):
        t = f'{int(m.group(1)):02d}:{m.group(2)}'
        ctx = body[max(0, m.start() - 110):m.start()].split('\n')[-1].lower()
        if t == '18:19' and not re.search(r'revoke|once more before|before the last time|2026-11-23 $|latest|last time|ten minutes|so that the take is over|the take is over|ends|cancel', ctx): F('18:19 in unexpected context: ' + ctx[-70:])
        if re.search(r'(last time to revoke|revoke[^.]{0,40}(by|before))\s*(mon 23 nov 2026 |2026-11-23 )?$', ctx) and t != '18:19': F(f'revoke deadline context carries {t}: ' + ctx[-70:])
        if re.search(r'(no start later than|latest start[^.]{0,30}(is|:|at)|asks for no start later than)\s*$', ctx) and t != '18:04': F(f'latest-start context carries {t}: ' + ctx[-70:])
        if re.search(r'(spending window[^.]{0,30}(ends|:)|window ends)\s*(mon 23 nov 2026 |2026-11-23 )?$', ctx) and t != '18:29': F(f'window-end context carries {t}: ' + ctx[-70:])
    if '18:19 UTC = 23:49 IST' not in body: F('revoke deadline pair missing')
    if '18:04 UTC = 23:34 IST' not in body: F('latest start pair missing')
    # ---- weekday / dates (2026)
    dn = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    mon = {'Nov': 11, 'Dec': 12, 'Oct': 10}
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (\d{1,2}) (Oct|Nov|Dec)[a-z]*(?: (\d{4}))?', txt):
        y = int(m.group(4)) if m.group(4) else 2026
        d = datetime.date(y, mon[m.group(3)], int(m.group(2)))
        if dn[d.weekday()] != m.group(1): F(f'weekday wrong: {m.group(0)} (is {dn[d.weekday()]})')
        if y != 2026: F('year not 2026: ' + m.group(0))
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (20\d\d)-(\d\d)-(\d\d)', txt):
        d = datetime.date(int(m.group(2)), int(m.group(3)), int(m.group(4)))
        if dn[d.weekday()] != m.group(1): F('weekday wrong (ISO): ' + m.group(0))
    for m in re.finditer(r'\b(\d{1,2}) (Oct|Nov|Dec)[a-z]* (\d{4})\b', txt):
        if m.group(3) != '2026': F('year not 2026: ' + m.group(0))
    for m in re.finditer(r'\b(20\d\d)-(\d\d)-(\d\d)\b', txt):
        try: datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError: F('bad ISO date ' + m.group(0))
        if m.group(1) != '2026': F('ISO year not 2026: ' + m.group(0))
    # ---- owner-facing NEW text: internal codes
    owner_new = [(r, b) for r in rows if r['file'].startswith('OWNER') for b in r['blocks'] if b['kind'] == 'NEW']
    codes = [(r'\bE-\d{1,2}\b', 'E-nn'), (r'\bG-?\d\b', 'G-nn'), (r'\bR-?\d{1,3}\b', 'R-nn'), (r'\bND ?\d{1,2}\b', 'ND-n'),
             (r'\bEL-\d\b', 'EL-n'), (r'\bWP\d\b', 'WP-n'), (r'\bD\d{1,2}\b', 'D-n'), (r'\bQ\d{2}\b', 'Q-nn'), (r'\bS9-\d+\b', 'S9-n'),
             (r'\bF-\d\d\b', 'F-nn'), (r'\bUNVERIFIED\b', 'UNVERIFIED(info)')]
    for r, b in owner_new:
        for pat, nm in codes:
            for m in re.finditer(pat, b['text']):
                msg = f"{r['id']} owner NEW text has {nm}: " + b['text'][max(0, m.start() - 25):m.end() + 15].replace('\n', ' ')
                if nm.endswith('(info)'): info.append(msg)
                else: F(msg)
    # ---- reply phrases: curated definition anchors + generic scan
    byid = {r['id']: r for r in rows}
    def newtxt(rid, only_applied=False):
        return '\n'.join(b['text'] for b in byid[rid]['blocks'] if b['kind'] == 'NEW') if rid in byid else ''
    anchors = [
        ('E-52', 'the take after which you write `no more takes`'), ('E-52', 'reply `no more takes` or `more takes`; no reply counts as `more takes`'),
        ('E-52', 'there you reply `cut accepted` or list the bad seconds'), ('E-52', '**How you reply**'), ('E-52', 'for `ok` and `no`: no'),
        ('E-52', 'for the secret key questions: `not sure`'),
        ('E-48', 'Reply `yes`, `no, other things use it` or `not sure`'), ('E-48', 'Reply `same key`, `different key` or `not sure`'),
        ('E-48', '`yes` to question 1 and `different key` to question 2'), ('E-48', '(`no, other things use it`, `not sure`, `same key`), do NOT revoke'),
        ('E-16', 'Reply with exactly `Yes, remove the container only` or `No`'),
        ('E-12', '`tested`'), ('E-12', '`untested`'),
        ('E-58', '`key kept`'),
        ('E-37', '`y` and Enter'), ('E-37', '`end`, when the assistant tells you'),
        ('E-49', 'Yes, send the one enquiry on'),
    ]
    for rid, a in anchors:
        if a not in newtxt(rid): F(f'reply-phrase definition missing in {rid}: {a[:60]}')
    # generic: every backticked token in owner NEW text that looks like a typed reply must be in the known vocabulary
    vocab = {'no more takes', 'more takes', 'cut accepted', 'same key', 'different key', 'not sure', 'key kept', 'yes', 'no', 'ok', 'end', 'y',
             'tested', 'untested', 'Yes, remove the container only', 'No', 'no, other things use it', 'proven', 'not proven'}
    # each vocab phrase used in backticks in any owner NEW text must also appear in a defining sentence in an Apply-now OWNER block (not only in held ones) when used in an Apply-now block
    for ph in vocab:
        used_applied = [r['id'] for r, b in owner_new if stat(r) != 'Hold' and f'`{ph}`' in b['text']]
        if used_applied:
            defs = [r['id'] for r, b in owner_new if stat(r) != 'Hold' and re.search(r'`' + re.escape(ph) + r'`[^.\n]{0,160}(means|counts as|ends|stops|is the|you reply|reply|write|type|word)|(reply|write|type|word|answer|send)[^.\n]{0,160}`' + re.escape(ph) + r'`', b['text'])]
            if not defs: F(f'reply phrase `{ph}` used in applied rows {used_applied} but no defining sentence in an applied row')
    # ---- secrets / emails / personal paths
    for pat, nm in ((r'AKIA[0-9A-Z]{16}', 'aws-shaped'), (r'sk-[A-Za-z0-9_-]{20,}', 'sk-shaped'), (r'ghp_[A-Za-z0-9]{20,}', 'gh token'), (r'xox[bap]-[A-Za-z0-9-]{10,}', 'slack token'),
                    (r'pat-[a-z0-9]{2,5}-[0-9a-f-]{20,}', 'hubspot-shaped'), (r'-----BEGIN [A-Z ]*PRIVATE KEY', 'pem'), (r'(?i)password\s*[:=]\s*\S{6,}', 'password assign'),
                    (r'\b[0-9a-f]{40,}\b', 'long hex'), (r'\b[A-Za-z0-9+/]{40,}={0,2}\b', 'long base64-ish'), (r'eyJ[A-Za-z0-9_-]{10,}', 'jwt-shaped')):
        for m in re.finditer(pat, txt):
            F(f'secret-shaped ({nm}): ' + m.group(0)[:12] + '...')
    for m in re.finditer(r'[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})', txt):
        dom = m.group(1).lower()
        if not (dom == 'example.com' or dom.endswith('.example.com')): F('e-mail address with non-example domain: ' + m.group(0)[:3] + '...@' + dom)
    for pat in (r'C:\\Users\\[A-Za-z]', r'/home/[a-z]+/[a-z]', r'/Users/[A-Za-z]'):
        for m in re.finditer(pat, txt): F('personal path: ' + m.group(0))
    # ---- banned vendor list (counts only)
    try:
        bt = open(os.path.join(os.path.dirname(os.path.abspath(edits)), '../../../tests/test_no_reference_material.py'), encoding='utf-8').read()
        ban = ast.literal_eval('(' + re.search(r'BANNED = \((.*?)\n\)', bt, re.S).group(1) + ')')
        hits = sum(1 for b in ban if b.lower() in txt.lower())
        info.append(f'banned scan: {len(ban)} entries, {hits} found in this file')
        if hits: F(f'banned vendor strings found: {hits} entries')
    except Exception as e:
        info.append('banned scan not run: ' + type(e).__name__)
    if not quiet:
        for i in info: print('INFO', i)
        print(f'rows={len(rows)} old_blocks={nold} apply_now={stc["Apply now"]} hold={stc["Hold"]} hold_blocks={hb} fences={nfence}')
    for f in fails: print('FAIL', f)
    print('RESULT', 'FAIL' if fails else 'PASS', len(fails))
    return fails

if __name__ == '__main__':
    q = '-q' in sys.argv
    a = [x for x in sys.argv[1:] if x != '-q']
    sys.exit(1 if run(a[0], a[1], q) else 0)
