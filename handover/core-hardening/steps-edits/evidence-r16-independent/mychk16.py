"""Independent checker for EDITS.md (round 16). Written without reusing verify16.py logic.
Usage: python3 -I mychk16.py <EDITS.md>   -> prints FAIL lines and a count. Library: check(text) -> list of 'CODE message'.
No secrets: secret-shaped samples are never stored here; patterns only. Banned list read at run time, counts only."""
import re, sys, os, ast, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(HERE, 'tests', 'test_no_reference_material.py')  # symlink inside this folder

def banned_list():
    src = open(TESTS, encoding='utf-8').read()
    m = re.search(r'BANNED\s*=\s*\((.*?)\n\)', src, re.S)
    return ast.literal_eval('(' + m.group(1) + ')')

def parse(text):
    """rows via own splitter: header line starts '### E-nn: file, line N[ (and M)], status S, type T'"""
    parts = re.split(r'(?m)^(?=### E-\d\d: )', text)
    rows = []
    for p in parts[1:]:
        head = p.split('\n', 1)[0]
        m = re.match(r'### (E-\d\d): (\S+), line (\d+)(?: \(and (\d+)\))?, status (.*), type (.*)$', head)
        if not m:
            rows.append(dict(id=head[4:9], bad=True, body=p)); continue
        # stop body at the next '## ' heading
        body = p.split('\n## Appendix K', 1)[0]
        blocks = re.findall(r'(?ms)^(OLD[^\n]*|NEW[^\n]*):\n~~~~\n(.*?)\n~~~~$', body)
        rows.append(dict(id=m.group(1), file=m.group(2), line=int(m.group(3)), status=m.group(5), type=m.group(6),
                         olds=[b for k, b in blocks if k.startswith('OLD')], news=[b for k, b in blocks if k.startswith('NEW')],
                         body=body, bad=False))
    return rows

def sections(text):
    d = {}
    for m in re.finditer(r'(?m)^## (.*)$', text):
        d[m.group(1)] = m.start()
    return d

def appendix(text):
    i = text.find('\n## Appendix K')
    if i < 0: return ''
    j = text.find('\n## ', i + 5)
    return text[i:j if j > 0 else len(text)]

def hms(h, m, s): return int(h) * 3600 + int(m) * 60 + int(s or 0)

def check(text):
    out = []
    def F(code, msg): out.append(f'{code} {msg}')
    rows = parse(text)
    # ---- A. structure
    if any(r['bad'] for r in rows): F('A1', 'unparsable row header')
    ids = [r['id'] for r in rows]
    want = ['E-%02d' % n for n in range(1, 63) if n not in (10, 35)]
    if ids != want: F('A2', 'row ids differ from E-01..E-62 minus E-10,E-35: %s' % sorted(set(ids) ^ set(want)))
    good = [r for r in rows if not r['bad']]
    app = appendix(text)
    na = sum(1 for r in good if r['status'].startswith('Apply now')); nh = sum(1 for r in good if r['status'].startswith('Hold'))
    if (len(good), na, nh) != (60, 48, 12): F('A3', 'counts rows/apply/hold %s' % ((len(good), na, nh),))
    for r in good:
        if r['status'].startswith('Hold') and not re.search(r'gate G[1-5]', r['status']): F('A4', r['id'] + ' hold without gate')
        if len(r['olds']) < 1 and r['id'] not in ('E-13',): F('A5', r['id'] + ' no OLD block')
        if not r['news']: F('A6', r['id'] + ' no NEW block')
        if not re.search(r'(?m)^Why: ', r['body']): F('A7', r['id'] + ' no Why line')
        if r['status'].startswith('Hold'):
            if not any('[HOLD' in l for l in re.findall(r'(?m)^NEW[^\n]*:$', r['body'])): F('A8', r['id'] + ' hold row NEW label lacks [HOLD')
        else:
            if any('[HOLD' in l for l in re.findall(r'(?m)^NEW[^\n]*:$', r['body'])): F('A9', r['id'] + ' apply row labelled HOLD')
    # index table agrees with headers
    idx = {}
    for m in re.finditer(r'(?m)^\| (E-\d\d) \| (\S+) \| ([^|]+?) \| ([^|]+?) \|', text):
        idx[m.group(1)] = (m.group(2), m.group(3), m.group(4))
    for r in good:
        x = idx.get(r['id'])
        if not x: F('A10', 'no index row ' + r['id']); continue
        if x[0] != r['file'] or x[2] != r['status'].split(' (')[0] or not x[1].startswith(str(r['line'])):
            F('A11', 'index differs from header ' + r['id'])
    # ---- B. times: UTC = IST (+5:30), seconds included
    npair = 0
    for m in re.finditer(r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*UTC\s*=\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*IST', text):
        npair += 1
        if (hms(m.group(1), m.group(2), m.group(3)) + 19800) % 86400 != hms(m.group(4), m.group(5), m.group(6)):
            F('B1', 'UTC/IST pair wrong: ' + m.group(0))
    # loose pairs: any hh:mm UTC with a following IST within 30 chars not joined by '='
    for m in re.finditer(r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:UTC|utc)\W{1,6}(\d{1,2}):(\d{2})(?::(\d{2}))?\s*IST', text):
        npair += 1
        if (hms(m.group(1), m.group(2), m.group(3)) + 19800) % 86400 != hms(m.group(4), m.group(5), m.group(6)):
            F('B2', 'loose UTC/IST pair wrong: ' + m.group(0))
    # an UTC time without any IST partner in same clause
    newonly = '\n'.join(t for r in good for t in r['news']) + app
    for m in re.finditer(r'\b\d{1,2}:\d{2}(?::\d{2})? UTC\b(?! = \d)', newonly):
        text_ = newonly; near = text_[m.end(): m.end() + 40]
        if 'IST' not in near:
            F('B3', 'UTC time without IST partner: ' + text_[max(0, m.start() - 20): m.end() + 30].replace('\n', ' '))
    for m in re.finditer(r'\b\d{1,2}:\d{2}(?::\d{2})? IST\b', newonly):
        before = newonly[max(0, m.start() - 40): m.start()]
        if 'UTC' not in before:
            F('B4', 'IST time without UTC partner: ' + newonly[max(0, m.start() - 30): m.end()].replace('\n', ' '))
    # ---- C. weekday/date
    wd = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']; full = {'Monday': 'Mon', 'Tuesday': 'Tue', 'Wednesday': 'Wed', 'Thursday': 'Thu', 'Friday': 'Fri', 'Saturday': 'Sat', 'Sunday': 'Sun'}
    mon = {'Oct': 10, 'Nov': 11, 'Dec': 12}
    nwd = 0
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\.?,? (\d{1,2}) (Oct|Nov|Dec)\w*(?:,? (\d{4}))?', text):
        nwd += 1
        w = full.get(m.group(1), m.group(1))
        y = int(m.group(4) or 2026)
        try: d = datetime.date(y, mon[m.group(3)], int(m.group(2)))
        except ValueError: F('C1', 'impossible date ' + m.group(0)); continue
        if y != 2026 or wd[d.weekday()] != w: F('C2', 'weekday/date wrong: ' + m.group(0))
    for m in re.finditer(r'\b(\d{1,2}) (Nov|Oct|Dec)\w* (?:2026 )?\(?(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b', text):
        nwd += 1
        d = datetime.date(2026, mon[m.group(2)], int(m.group(1)))
        if wd[d.weekday()] != m.group(3): F('C3', 'date/weekday wrong: ' + m.group(0))
    anchors = {16: 'Mon', 18: 'Wed', 22: 'Sun', 23: 'Mon', 25: 'Wed'}
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w* (\d{1,2}) Nov', text):
        if int(m.group(2)) in anchors and anchors[int(m.group(2))] != m.group(1)[:3]: F('C4', 'anchor weekday wrong: ' + m.group(0))
    # a bare day number tied to Nov but wrong year
    for m in re.finditer(r'\b\d{1,2} (?:Oct|Nov|Dec)\w* (20\d\d)\b', text):
        if m.group(1) != '2026': F('C5', 'year not 2026: ' + m.group(0))
    # ---- D. cross references
    kheads = set(re.findall(r'(?m)^K-([A-Z]) \(detail of key step ([A-K])\)', app))
    kletters = {a for a, b in kheads}
    for a, b in kheads:
        if a != b: F('D1', 'appendix heading letter mismatch K-%s vs %s' % (a, b))
    e48 = [r for r in good if r['id'] == 'E-48']
    e48new = e48[0]['news'][0] if e48 and e48[0]['news'] else ''
    steps_def = set(re.findall(r'(?m)^   Key step ([A-K])\.', e48new))
    if steps_def != set('ABCDEFGHIJK'): F('D2', 'key steps defined: %s' % ''.join(sorted(steps_def)))
    subs_def = set(re.findall(r'(?m)^   (D\.\d|G\.\d)\.', e48new))
    for m in re.finditer(r'[Kk]ey steps? ([A-K])(?:\.(\d))?', text):
        if m.group(1) not in steps_def: F('D3', 'ref to undefined key step ' + m.group(0))
        if m.group(2) and (m.group(1) + '.' + m.group(2)) not in subs_def: F('D4', 'ref to undefined sub-step ' + m.group(0))
    for m in re.finditer(r'key steps ([A-K]) to ([A-K])', text):
        if m.group(1) > m.group(2): F('D5', 'range reversed ' + m.group(0))
    for m in re.finditer(r'appendix(?: of this sheet,)? (?:part )?K-([A-K])', text):
        if m.group(1) not in kletters: F('D6', 'ref to missing appendix part K-' + m.group(1))
    for m in re.finditer(r'(?m)Detail[^.\n]{0,60}K-([A-K])', e48new):
        if m.group(1) not in kletters: F('D7', 'Detail ref to missing K-' + m.group(1))
    # Detail letter must equal the key step it sits in
    for m in re.finditer(r'(?m)^   Key step ([A-K])\.(.*)$', e48new):
        for d in re.findall(r'appendix K-([A-K])', m.group(2)):
            if d != m.group(1): F('D8', 'key step %s points to appendix K-%s' % (m.group(1), d))
    erefs = set(re.findall(r'\bE-(\d\d)\b', text))
    for n in erefs:
        if 'E-' + n not in ids: F('D9', 'reference to missing row E-' + n + ('' if n not in ('10', '35') else ' (removed id)')) if n not in ('10', '35') else None
    gdefs = set(re.findall(r'\*\*(G\d)', text[text.find('## Gates'): text.find('## How the rows are used')]))
    for m in re.finditer(r'\bgate (G\d)', text):
        if m.group(1) not in gdefs: F('D10', 'undefined gate ' + m.group(1))
    for m in re.finditer(r'NOT DECIDED (\d+)', text):
        if not 1 <= int(m.group(1)) <= 15: F('D11', 'ND out of range ' + m.group(0))
    # step 8 sub-steps / numbered items inside the card
    card = re.findall(r'(?m)^   (\d)\. (.*)$', e48new)
    if [c[0] for c in card] != ['1', '2', '3', '4', '5', '6', '7']: F('D12', 'card numbering ' + ''.join(c[0] for c in card))
    # ---- E. owner-facing text hygiene
    owner_texts = [(r['id'], t) for r in good if r['file'].startswith('OWNER') for t in r['news']] + [('AppxK', app)]
    pats = [(r'/home/|/Users/|C:\\|/tmp/|/root/', 'absolute path'), (r'\bQ\d{1,2}(?:\.\d+)?\b', 'Q-number'), (r'\bORD:|\bDEC:', 'ORD/DEC code'),
            (r'\bE-\d\d\b', 'E-nn'), (r'\bND ?\d+\b', 'ND code'), (r'\bS9-\d+', 'S9 code'), (r'\bWP\d', 'WP code'), (r'\bR\d{1,3}\b', 'R-number'),
            (r'\bD5\b', 'D5 code'), (r'CODE-GATE', 'gate line')]
    for rid, t in owner_texts:
        for p, nm in pats:
            for m in re.finditer(p, t):
                # UNVERIFIED and gate words are allowed in some rows; only flag the codes above
                F('E1', '%s in owner-facing text of %s: %r' % (nm, rid, m.group(0)))
    # ---- F. secrets (patterns only)
    secs = [r'AKIA[0-9A-Z]{16}', r'\bsk-[A-Za-z0-9_-]{16,}', r'\bghp_[A-Za-z0-9]{20,}', r'\bxox[a-z]-[A-Za-z0-9-]{8,}', r'-----BEGIN [A-Z ]*KEY', r'\beyJ[A-Za-z0-9_-]{15,}\.', r'(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*(?=[^\s`\'"<>]*\d)[^\s`\'"<>]{8,}',
            r'\b[0-9a-f]{40,}\b', r'[A-Za-z0-9+/]{40,}={0,2}', r'[\w.+-]+@(?!example\.com\b)[\w-]+\.(?:com|org|net|io|dev|in)\b', r'\bpat-[a-z0-9]{2,4}-[0-9a-f-]{20,}', r'\bAIza[0-9A-Za-z_-]{20,}']
    for p in secs:
        for m in re.finditer(p, text):
            if m.group(0) == 'AKIAIOSFODNN7EXAMPLE': continue
            F('F1', 'secret-shaped text (%s): len %d' % (p[:18], len(m.group(0))))
    # ---- G. banned (counts only)
    try:
        bl = banned_list(); n = sum(1 for b in bl if b in text)
        if n: F('G1', 'banned strings present: %d of %d' % (n, len(bl)))
    except Exception as e:
        F('G2', 'banned list unreadable: %s' % type(e).__name__)
    # ---- H. semantic invariants (derived by reading the sheet, not from verify16)
    # H1 one order: card items appear in this order
    keys = ['Revoke the secret key for the model and write `key revoked`', 'Shred the copy of the key in the take folder', 'Do your items 2 and 4', 'Do your item 5', 'Shred the two files of your item 6', 'Read the list that the assistant sends', 'The assistant does its item 1']
    pos = [e48new.find(k) for k in keys]
    if -1 in pos or pos != sorted(pos): F('H1', 'card order wrong/missing %s' % pos)
    if 'never starts while a copy of the key exists and the key is not revoked' not in e48new: F('H2', 'item 1 guard sentence missing')
    # H3 deadline sentences: any sentence with revoke and 18:29 must be about the window
    for rid, t in owner_texts:
        for s in re.split(r'(?<=[.;:])\s+', t.replace('\n', ' ')):
            if re.search(r'\brevok', s) and '18:29 UTC' in s and not re.search(r'window|stop spending|later|10 minutes|HubSpot|app password|item 3|clean-up|screenshot|later', s):
                F('H3', 'revoke tied to 18:29 in %s: %s' % (rid, s[:100]))
            if re.search(r'spending window|stop spending|money stop', s) and '18:19 UTC' in s and '18:29' not in s and re.search(r'window ends[^.]{0,25}18:19', s):
                F('H4', 'window end tied to 18:19 in %s: %s' % (rid, s[:100]))
    for p in ('18:19 UTC = 23:49 IST', '18:29 UTC = 23:59 IST', '17:49 UTC = 23:19 IST', '18:09 UTC = 23:39 IST', '18:00 UTC = 23:30 IST'):
        if text.count(p) < 1: F('H5', 'canonical time missing: ' + p)
    if len(re.findall(r'18:19 UTC = 23:49 IST', e48new)) < 8: F('H6', 'E-48 has fewer than 8 mentions of the last time to revoke')
    # H7 margin arithmetic: start 18:00:00 + 1:00 typing + 14:20 take = 18:15:20; margin to 18:19 = 3:40
    t0 = 18 * 3600; t1 = t0 + 60 + 860; marg = 18 * 3600 + 19 * 60 - t1
    if marg != 220 or '3 minutes 40 seconds' not in text: F('H7', 'margin sentence missing or arithmetic differs (computed %d s)' % marg)
    if '18:15:20 UTC = 23:45:20 IST' not in text: F('H8', 'finish time 18:15:20 UTC = 23:45:20 IST not stated')
    # H9 alarms
    for nm in ('`revoke the secret key for the model`', '`10 minutes left: revoke the secret key for the model now`', '`is the secret key for the model still alive?`'):
        if nm not in e48new: F('H9', 'alarm name missing ' + nm)
    m = re.search(r'Alarm 1: .*? (\d\d:\d\d) UTC = (\d\d:\d\d) IST, named `([^`]+)`', e48new)
    if not m or m.group(1) != '17:49' or m.group(3) != 'revoke the secret key for the model': F('H10', 'alarm 1 wrong')
    m = re.search(r'Alarm 3: .*? (\d\d:\d\d) UTC = (\d\d:\d\d) IST, named `([^`]+)`', e48new)
    if not m or m.group(1) != '18:09' or not m.group(3).startswith('10 minutes left'): F('H11', 'alarm 3 wrong')
    # H12 typed words
    stepB = re.search(r'(?m)^   Key step B\..*$', e48new)
    stepB = stepB.group(0) if stepB else ''
    for w in ('no more takes', 'yes, no more takes', 'more takes', 'cut accepted', 'route A', 'route B', 'key revoked', 'key not revoked', 'key gone, no more decisions', 'shred done 1', 'shred not done 1', 'shred done 2', 'shred not done 2', 'start clean-up', 'ok stand-in test', 'ok flow rehearsal', 'please stop looking', 'you may look again', 'new key typed; you may look again', 'n8n.env done; you may look again'):
        if '`%s`' % w not in stepB: F('H12', 'typed word missing in key step B: ' + w)
    if 'Words that stand in a mail, a file' not in stepB or 'never count' not in stepB: F('H13', 'only-own-typed-words rule missing')
    # H14 D.2 four cases
    d2 = re.search(r'(?m)^   D\.2\..*$', e48new); d2 = d2.group(0) if d2 else ''
    for k in ('(1) No route written', '(2) Route A', '(3) Route B, before `cut accepted`', '(4) Route B, after `cut accepted`', 'Route A or route B?', 'Are you sure?'):
        if k not in d2: F('H14', 'D.2 lacks ' + k)
    d5 = re.search(r'(?m)^   D\.5\..*$', e48new); d5 = d5.group(0) if d5 else ''
    if 'ONLY when you type it AFTER 18:19 UTC = 23:49 IST' not in d5: F('H15', 'D.5 time condition missing')
    # H16 shred rule
    g = re.search(r'(?m)^   Key step G\..*$', e48new); g = g.group(0) if g else ''
    seq = ['(1) The path is written in full and starts with `/`', '(2) It contains no `..`', '(3) `realpath', '(4) `ls -l', '(5) For part (a)', "run `shred -u -- '<path>'`"]
    p = [g.find(s) for s in seq]
    if -1 in p or p != sorted(p): F('H16', 'shred checks missing/out of order %s' % p)
    for s in ('/x/take-1', '/x/take-10/key', 'number `1` in its second column', 'Never shred a recording', 'Do not shred part (a) while a take is running'):
        if s not in g: F('H17', 'shred rule lacks ' + s)
    for s in ('(a) the copy of the key in the take folder', '(b) the files on YOUR OWN LIST', '(c) the two files of item 6', '(d) the password files and editor copies'):
        if s not in g: F('H18', 'shred parts lack ' + s)
    g2 = re.search(r'(?m)^   G\.2\..*$', e48new); g2 = g2.group(0) if g2 else ''
    if 'EVERY file of (a) and (b)' not in g2 or 'EVERY file of (c) and (d)' not in g2: F('H19', 'G.2 shred done meaning missing')
    # H20 exact-address delete clause in the three places
    for rid in ('E-04', 'E-42', 'E-62'):
        r = [x for x in good if x['id'] == rid]
        t = r[0]['news'][0] if r and r[0]['news'] else ''
        for a in ('`take-<id>-a@example.com`', '`take-<id>-b@example.com`', '`take-<id>-c@example.com`'):
            if a not in t: F('H20', rid + ' lacks address ' + a)
        if not re.search(r'more than 3', t) or not re.search(r'delete nothing and tell the assistant', t): F('H21', rid + ' lacks the stop rule')
        if re.search(r'made-up names?', t): F('H22', rid + ' still says made-up names')
    # H23 key step questions
    for s in ('Reply `yes`, `no, other things use it` or `not sure`', 'Reply `same key`, `different key` or `not sure`', 'Only `yes` together with `different key`'):
        if s not in e48new: F('H23', 'key step F lacks ' + s)
    for s in ('http://localhost:5678',):
        if s not in e48new: F('H24', 'missing ' + s)
    # H25 revoke only your own key
    if 'revoke the one key that you created for this take and no other key' not in e48new: F('H25', 'revoke-only-own-key sentence missing')
    if 'never tell the assistant the characters of a key' not in e48new: F('H26', 'never tell characters sentence missing')
    # H27 J rules
    if 'more than 7 days ago' not in e48new or 'less than 7 days ago' not in e48new: F('H27', 'key step J 7 day rule')
    # H28 H: 20 minutes
    if e48new.count('20 minutes') < 3: F('H28', 'fewer than 3 mentions of 20 minutes')
    # H29 no timers claim
    if 'a procedure, not a control' not in e48new: F('H29', 'procedure not control sentence missing')
    # H30 week days in E-48
    if 'Wed 18 Nov 2026' not in text: F('H30', 'Wed 18 Nov 2026 missing')
    return out

def words(s): return len(re.findall(r'\S+', s))

if __name__ == '__main__':
    p = sys.argv[1]
    t = open(p, encoding='utf-8').read()
    res = check(t)
    for r in res: print('FAIL', r)
    print('MYCHK FAILURES', len(res))
    sys.exit(1 if res else 0)
