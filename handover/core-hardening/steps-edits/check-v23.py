"""v23 form checks. Reads text only. Prints counts, never a banned word. Proves FORM, never that a statement is true.
Class list (each has a planted-mistake run in evidence-v23/): arithmetic and price lines, UTC/IST pairs, weekdays, pointers (existence AND topic of the target,
checked in sheet, note, open list and changes), list-form Open pointers, placeholder spelling, cancel rule only in the card (and no paraphrase outside it),
set phrases, verbs, R10 'key alive: card first', older-key variants A and B each consistent, tolerated-list parity, Q25/Q26, banned words.
Folder override: V23_DIR."""
import ast, os, re, sys, datetime as dt
from decimal import Decimal as Dc
D = os.environ.get('V23_DIR', '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/')
if not D.endswith('/'): D += '/'
F = {'S': 'OWNER-SHEET-v23.md', 'N': 'LEAD-RELEASE-NOTE-v7.md', 'O': 'v23-OPEN-FOR-LEAD.md', 'C': 'v23-CHANGES.md'}
T = {k: open(D + v, encoding='utf-8').read() for k, v in F.items()}
Sfull, Nn, O, C = T['S'], T['N'], T['O'], T['C']
problems = []
def bad(m): problems.append(m); print('PROBLEM:', m)
def ok(m): print('ok:', m)
def nocode(t): return re.sub(r'`[^`]*`', '', t)
def variant(s, keep):
    drop = 'B' if keep == 'A' else 'A'
    s = re.sub(r'\[\[%s:.*?\]\]' % drop, '', s, flags=re.S)
    return re.sub(r'\[\[%s:(.*?)\]\]' % keep, r'\1', s, flags=re.S)
# ---- counts
v22 = open(D + 'OWNER-SHEET-v22.md', encoding='utf-8').read()
w22, w23 = len(v22.split()), len(Sfull.split())
wA, wB = len(variant(Sfull, 'A').split()), len(variant(Sfull, 'B').split())
print('words sheet v22 -> v23: %d -> %d (variant A %d, variant B %d); lines %d -> %d; note words v6 -> v7: %d -> %d' % (w22, w23, wA, wB, len(v22.splitlines()), len(Sfull.splitlines()), len(open(D + 'LEAD-RELEASE-NOTE-v6.md', encoding='utf-8').read().split()), len(Nn.split())))
if not (w23 < w22 and wA < w22 and wB < w22): bad('sheet is not shorter than v22')
if Sfull.count('[[A:') != Sfull.count('[[B:') + Sfull.count('[[A:') - Sfull.count('[[B:') or Sfull.count('[[') != Sfull.count(']]'): bad('unbalanced alternative markers')
for k in 'AB':
    if f'[[{k}:' not in Sfull: bad('no %s text' % k)

def sheet_checks(S, tag):
    P = lambda m: bad('[%s] %s' % (tag, m))
    L = S.splitlines()
    if '[[' in S or ']]' in S: P('markers left in the variant')
    heads = re.findall(r'^## ', S, re.M)
    if len(heads) != 9: P('sheet headings %d' % len(heads))
    defs = re.findall(r'^\| (R\d+) \|', S, re.M)
    if defs != ['R1', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10']: P('rule ids %s' % defs)
    for r in set(re.findall(r'\bR(\d+)\b', nocode(S))):
        if int(r) not in (1, 4, 5, 6, 7, 8, 9, 10, 2, 3): P('cites R%s' % r)
    if sum(1 for l in L if re.search(r'\bR[23]\b', l)) != 1: P('R2/R3 must be named exactly once (the gap note)')
    if re.search(r'\bG\d+\b', S): P('sheet cites a gate id')
    # items per section
    items, cur = {}, None
    for line in L:
        h = re.match(r'## (\d)\.', line)
        if h: cur = int(h.group(1)); items[cur] = 0; continue
        if cur and re.match(r'\d+\. ', line): items[cur] += 1
    card = S[S.index('### THE CARD'):S.index('### The rules')]
    cardsteps = len(re.findall(r'^\d+\. ', card, re.M))
    if cardsteps != 6: P('card steps %d' % cardsteps)
    tt = nocode(S)
    for a, b in set(re.findall(r'(?<![\d.:/-])\b([5-8])\.(\d{1,2})\b(?![\d:])', tt)):
        if int(b) < 1 or int(b) > items.get(int(a), 0): P('pointer %s.%s does not exist' % (a, b))
    for m in re.finditer(r'card step (\d+)', S):
        if not 1 <= int(m.group(1)) <= cardsteps: P('card step %s' % m.group(1))
    for m in re.finditer(r'section (\d+)', S):
        if not 1 <= int(m.group(1)) <= 9: P('section %s' % m.group(1))
    # card is the only place with the cancel procedure
    outside = S.replace(card, '')
    frag = ['N minus K', 'with all filters off', 'confirmation word', 'press the cancel button', 'steps 2 to 4', 'from its step 1', 'shows the cancelled word', 'cancels the key you made', 'do not wait for the prompt', 'Proof:']
    for ln in outside.splitlines():
        hits = [f for f in frag if f.lower() in ln.lower()]
        if hits and not ln.startswith('|---'):
            # allowed: film person reloads a page (7.6) is about HubSpot, not the key list
            if hits == ['reload'] and ('film person' in ln or 'reload:' in ln or 'reload the' in ln and 'old secret' in ln or 'reload: the entry' in ln): continue
            P('cancel-rule fragment %s outside the card: %s...' % (hits, ln[:60]))
    ccount = {k: sum(len(re.findall(k, ln)) for ln in outside.splitlines()) for k in []}
    # R10 mentions in sections 5-8
    secs = S[S.index('## 5.'):S.index('## 9.')]
    for m in re.finditer(r'R10', secs):
        if 'key alive: card first' not in secs[m.start():m.start() + 60]: P('R10 without "key alive: card first": %s' % secs[max(0, m.start() - 40):m.start() + 30].replace('\n', ' '))
    # verbs
    for m in re.finditer(r'(?<!touch )\b(?i:send|sends|sending|sent|report|reports|reported|reporting|write|writes|wrote|take program|take terminal|take settings)\b', nocode(S)):
        P('banned verb or old word %r near %r' % (m.group(0), S[max(0, m.start() - 25):m.start() + 20]))
    if re.search(r'\bunsure\b', nocode(S)) and S.count('unsure') != 2: pass
    # still works meaning
    for m in re.finditer(r'still works', S):
        if 'login' not in S[max(0, m.start() - 30):m.start()] and 'login' not in S[m.start() - 80:m.start()] and 'revoke' not in S[m.start() - 60:m.start()+40]: P('"still works" outside the login lines or the retire sentence')
    if '"still works"' in S.split('## 8.')[0].split('R8 |')[1][:900] if 'R8 |' in S else False: P('R8 still lists still works')
    r8 = [l for l in L if l.startswith('| R8 |')][0]
    for w in ['"go"', '"n8n is off"', '"post"', '"revoke again"', '"continue"', 'Only five words']:
        if w not in r8: P('R8 lacks %s' % w)
    # deadline / post-by phrases
    if S.count('18:29 UTC = 23:59 IST') != 2: P('deadline phrase count %d' % S.count('18:29 UTC = 23:59 IST'))
    if S.count('15:00 UTC = 20:30 IST') != 1: P('post-by phrase count')
    # arithmetic
    price = (Dc(40000) * 3 + Dc(10000) * 15) / 1000000
    for pat, want in [(r'Price per call at full size: USD ([\d.]+)', price), (r'Expected total: USD ([\d.]+) \(not a limit\)', price * 3), (r'Price per call: ([\d.]+) \(USD\)', price), (r'Expected total: ([\d.]+)   Deadline', price * 3), (r'= (\d+\.\d+); call ceiling x that = expected total, here 3 x 0\.27 = (\d+\.\d+)', None)]:
        m = re.search(pat, S)
        if not m: P('price line missing %s' % pat[:30]); continue
        if want is not None and Dc(m.group(1)) != want: P('price line %s is %s, expected %s' % (pat[:30], m.group(1), want))
        if want is None and (Dc(m.group(1)) != price or Dc(m.group(2)) != price * 3): P('check 1 numbers wrong')
    if "expected total USD 0.81" not in S or 'balance USD 189.00' not in S or ': 3 expected paid model calls' not in S: P('filled yes example does not match the sample figures')
    mb = re.search(r'Balance on the prepaid page: USD ([\d.]+).*?Program limit: USD ([\d.]+)', S)
    sv = dict(re.findall(r'(\b[A-Z_]+) = (\d+)', S[S.index('Settings to compare'):S.index('Minutes at "Type')]))
    if Dc(sv['PROGRAM_LIMIT_CENTS']) / 100 != Dc(mb.group(2)) or Dc(sv['PRICE_IN_CENTS']) / 100 != 3 or Dc(sv['PRICE_OUT_CENTS']) / 100 != 15: P('settings in cents disagree with money lines')
    if (Dc(sv['TOKENS_IN']) * Dc(sv['PRICE_IN_CENTS']) + Dc(sv['TOKENS_OUT']) * Dc(sv['PRICE_OUT_CENTS'])) / 1000000 / 100 != price: P('settings do not give the price per call')
    def hm(s): p = s.split(':'); return dt.timedelta(hours=int(p[0]), minutes=int(p[1]), seconds=int(p[2]) if len(p) > 2 else 0)
    IST = dt.timedelta(hours=5, minutes=30)
    for a, b in re.findall(r'(\d\d:\d\d(?::\d\d)?) UTC = (\d\d:\d\d(?::\d\d)?) IST', S):
        if (hm(a) + IST) % dt.timedelta(days=1) != hm(b): P('%s UTC is not %s IST' % (a, b))
    for w, d in re.findall(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{1,2}) Nov 2026', S):
        if dt.date(2026, 11, int(d)).strftime('%a') != w: P('weekday %s %s' % (w, d))
    m = re.search(r'Latest start: (\d\d:\d\d) UTC.*?Alarm time: (\d\d:\d\d) UTC.*?Cancel-by time: (\d\d:\d\d) UTC', S)
    ls, lf, cb = (hm(x) for x in m.groups())
    sm = re.search(r'minutes at "Type y to start" (\d+) \+ run length (\d+) \+ film pause (\d+) = (\d+); margin (\d+)', S)
    y_, rl_, fp_, tot_, mg = (int(x) for x in sm.groups())
    sl = re.search(r'Minutes at "Type y to start": (\d+)   Run length: (\d+) \(the lead\'s reading of the test program\'s start margin: at least (\d+) seconds = ([\d.]+) minutes\)   Film pause: (\d+)   Margin: (\d+)', S)
    if not sl: P('separate time lines missing')
    else:
        if (int(sl.group(1)), int(sl.group(2)), int(sl.group(5)), int(sl.group(6))) != (y_, rl_, fp_, mg): P('time lines disagree with the sums line')
        if (Dc(sl.group(3)) / 60).quantize(Dc('0.01')) != Dc(sl.group(4)): P('need seconds / 60 is not %s' % sl.group(4))
        if rl_ * 60 < int(sl.group(3)): P('run length below need seconds')
    if y_ + rl_ + fp_ != tot_: P('sum of minutes')
    if lf - ls != dt.timedelta(minutes=tot_) or cb - lf != dt.timedelta(minutes=mg): P('alarm or cancel-by time not latest start + sum / + margin')
    we = hm('18:29:00')
    if str(we - dt.timedelta(seconds=860)) != '18:14:40' or "Program's last start: 18:14:40 UTC = 23:44:40 IST" not in S: P('program last start')
    if ls > we - dt.timedelta(minutes=tot_ + mg + 10) or cb > we - dt.timedelta(minutes=10): P('sample times break the deadline buffer')
    lim = we - dt.timedelta(minutes=tot_ + mg + 10)
    if '18:29 minus %d minutes = %s UTC' % (tot_ + mg + 10, str(lim)[:-3].rjust(5, '0')) not in S: P('check 4 example text')
    m3 = re.search(r'\(sample: (\d\d:\d\d) \+ (\d+) = (\d\d:\d\d); (\d\d:\d\d) \+ (\d+) = (\d\d:\d\d)\)', S)
    if not m3 or hm(m3.group(1)) + dt.timedelta(minutes=int(m3.group(2))) != hm(m3.group(3)) or hm(m3.group(4)) + dt.timedelta(minutes=int(m3.group(5))) != hm(m3.group(6)) or m3.group(1) != '11:30' or int(m3.group(2)) != tot_ or int(m3.group(5)) != mg: P('check 3 worked example sum wrong')
    m2 = re.search(r'would be (\d\d:\d\d) UTC = (\d\d:\d\d) IST, 10 minutes before', S)
    if not m2 or hm(m2.group(1)) != we - dt.timedelta(minutes=10): P('Mon 23 Nov cancel-by example')
    rd = re.search(r'Run day: (\w{3}) (\d+) Nov 2026', S)
    psx = re.search(r'`(\d+) (\w{3}) Nov (\d+) (\d\d:\d\d:\d\d) 2026 python3`', S); fx = re.search(r'`2026-11-(\d\d) (\d\d:\d\d:\d\d)\.\d+ \+0000`', S)
    if not (rd and psx and fx) or not (psx.group(3) == rd.group(2) == fx.group(1)) or not (hm('11:00') <= hm(fx.group(2)) < hm(psx.group(4)) <= ls): P('ps/file time examples')
    # yes sentence
    ym = re.search(r'"(Yes, run <run name>:.*?)" \*\*Filled', S, re.S)
    if not ym: P('yes pattern missing')
    else:
        y = re.sub(r'<[^>]*>', '5', ym.group(1))
        if re.search(r'[^A-Za-z0-9 .,:=_/@+-]', y): P('yes charset %s' % sorted(set(re.findall(r'[^A-Za-z0-9 .,:=_/@+-]', y))))
        if 'does not end the calls' not in y or 'older key <its name or none>' not in ym.group(1): P('yes clauses')
        if re.search(r'older key <its name or none>\s*\[', ym.group(1)): P('older key clause inside brackets')
    if 'no pasting' not in S or 'by hand, the yes included' not in S: P('yes typing vs pasting not stated consistently with R9')
    # placeholders
    allowed = {'...', 'run name', 'folder', 'path', 'key file', 'setting name', 'model settings file', 'its name', 'its name or none', 'name', 'number', 'in words', 'name and how', 'names', 'date', 'address', 'word', 'step', 'test settings file name', 'copied', 'the printed line, copied, or minutes after "run started"', 'words', 'range', 'page address', 'lead\'s answer', 'number or none', 'list', 'file', 'amount or none', 'expected total', 'the balance you read on the prepaid page', 'the word you read, it must be off', 'call ceiling', 'word seen by the lead', 'path from the message', 'run name>-a@example.com', 'all', 'key file', 'process number'}
    ph = set(re.findall(r'<([^<>]*)>', S))
    for x in ph:
        if x not in allowed and not re.fullmatch(r'[^<>]{0,60}', x): P('placeholder %r' % x)
        if x not in allowed: P('placeholder spelled differently or unknown: %r' % x)
    # set phrases
    lst = [l for l in L if l.startswith('**Set phrases')]
    if len(lst) != 1: P('set phrase list'); return
    norm = lambda s: re.sub(r'<[^>]*>', '<>', s.strip())
    listed = [norm(x) for x in re.findall(r'"([^"]+)"', lst[0])]
    for p_ in listed:
        if p_ != 'stop' and re.search(r'[^A-Za-z0-9 .,:=_/@+<>-]', p_): P('set phrase charset %r' % p_)
    body = re.sub(r'```.*?```', '', S, flags=re.S).replace(lst[0], '')
    ctx = re.compile(r'(?:\btell\b|\bTell\b|\bTell the lead exactly:)[^"\n]{0,50}"([^"]+)"')
    lead_says = {'go', 'n8n is off', 'post', 'revoke again', 'continue'}
    for m in ctx.finditer(nocode(body)):
        pp = norm(m.group(1))
        if pp in lead_says: continue
        if pp not in listed: P('quoted phrase %r told but not listed' % m.group(1))
    for pp in listed:
        if pp == 'stop': continue
        pat = '<[^>]*>'.join(re.escape(x) for x in pp.split('<>'))
        if not re.search(pat, body): P('listed phrase %r unused' % pp)
    if re.search(r'Tell the lead exactly: [a-z ]+', S) and 'model key cancelled' not in re.search(r'Tell the lead exactly: ([a-z ]+)', S).group(0): P('card step 5 phrase')
    spell = set(norm(m.group(0)) for m in re.finditer(r'I cancel the older key <[^>]*>(?:, nothing else I know uses it)?', S))
    if tag == 'A' and (len(spell) != 1 or not all('nothing else I know uses it' in x for x in spell)): P('older key phrase forms %s' % spell)
    if tag == 'B':
        for bad_ in ['I cancel the older key', 'cannot be undone', 'cancel it myself']:
            if bad_ in S: P('variant B still holds A text %r' % bad_)
        if 'left alone' not in S: P('variant B lacks the left-alone text')
    if tag == 'A':
        for need in ['cannot be undone', 'I cancel the older key', '(b) the older key']:
            if need not in S: P('variant A lacks %r' % need)
    # card blanks and parts
    for need in ['key list address', 'create button word', 'cancel button word', 'confirmation box word', 'cancelled word', 'other channel', 'last-resort step', '`date -u`', 'Last resort', 'yes ___ no ___', 'dismiss it']:
        if need not in card: P('card lacks %r' % need)
    if 'app password' not in card or 'HubSpot app secrets' not in card or 'only after you told "model key cancelled"' not in card: P('card Part (d) missing')
    for ref in ['8.3', '8.4', '8.6']:
        if ref not in card: P('card (d) does not point at %s' % ref)
    # glossary order
    G = S[S.index('**The words**'):S.index('## 2.')]
    for t in ['UTC', 'UNVERIFIED', 'WSL', 'Re-pin', 'Tell', 'Set phrase', 'Lead', 'Numbers message', 'Clean-up message', 'Test terminal', 'Read terminal', 'Run name', 'Model key', 'Older key', 'Key list', 'Valid key', 'Cancelled word', 'Key file', 'Notice', 'Film pause', 'Recording OFF', 'Film person', 'Demo mail', 'Throwaway accounts', 'App passwords', 'HubSpot app secrets', 'Prepaid', 'Balance', 'Spend lock', 'Latest start', 'Cancel-by time', 'FREEZE', 'Normal profile', 'Test program', 'Contact id']:
        m = re.search(r'\*\*' + re.escape(t), G, re.I if t not in ('UTC', 'WSL', 'UNVERIFIED', 'FREEZE') else 0)
        if not m: P('glossary lacks term %r' % t)
    pos = {t: G.find('**' + t) for t in ['UTC', 'UNVERIFIED']}
    pre = S[:S.index('**The words**')]
    for t in ['UNVERIFIED', 'UTC', 'WSL', 'FREEZE']:
        if re.search(r'(?<![A-Za-z])%s(?![A-Za-z])' % t, nocode(pre.split('**STOP RULE:**')[0])) and t in ('UNVERIFIED', 'UTC', 'WSL'): P('%s used before its definition' % t)
    if 'FREEZE' in pre.split('**What happens')[0] and 'STOP RULE' not in pre: P('freeze order')
    # tolerated list parity
    for kw in ['Windows menu', 'Recall', 'paste', 'app-password', 'HubSpot private-app', 'contact id']:
        for nm, tx in (('sheet glossary', G), ('note', Nn), ('open list', O)):
            if kw.lower() not in tx.lower(): P('tolerated item %r missing in %s' % (kw, nm))
    for old in ['Part 2', 'Part 1', 'Part 3', 'Part 4', 'take window', 'second window', 'Version id', 'independent reader']:
        if old in S: P('old term %r in sheet' % old)
    if re.search(r'\bcard Parts?\b', S): P('card Part wording')

# ---- run on both variants
SA, SB = variant(Sfull, 'A'), variant(Sfull, 'B')
n0 = len(problems)
sheet_checks(SA, 'A'); sheet_checks(SB, 'B')
ok('variants A and B checked') if len(problems) == n0 else None

# ---- semantic pointers across all files (target topic must appear near the pointer)
TOP = {'5.1': ['run name', 'key-list', 'key list', 'used list', 'used name', 'open it'], '5.2': ['people', 'film person', 'role', 'helper', '5.7', 'checks of section'], '5.3': ['laptop', 'menu', 'gmail'], '5.4': ['gmail', 'label', 'filter'], '5.5': ['film profile', 'chrome'], '5.6': ['key-list check', 'model page', 'auto-reload', 'key list', 'time changed', 'differs'], '5.7': ['setting', 'figure', '5.2', 'checks of section'], '5.8': ['yes', 'go', 'older'],
       '6.1': ['clipboard', 'recall', 'privacy', 'switch'], '6.2': ['alarm', 'older key', 'check 2', 'earliest'], '6.3': ['create', 'key file', 'key alive', 'secret', 'screen'], '6.4': ['key-save', 'paste', 'set -c', 'key save', 'save'], '6.5': ['fail', 'new run name', 'key save', 'size', 'says so', 'no word of the lead'], '6.6': ['size', 'process', 'check 3', 'ps ', 'restart', 'valid keys'],
       '7.1': ['tick', 'check 3', 'key-list'], '7.2': ['sha256', 'fingerprint', 'checksum'], '7.3': ['start line', 'latest start', 'start of a run', 'still works'], '7.4': ['notice', 'challenge', 'run started', 'date -u'], '7.5': ['waits', 'type nothing', 'end', 'numbers message', 'seconds'], '7.6': ['film', 'recording'], '7.7': ['recording', 'counts'], '7.8': ['end', 'cancel', 'error', 'order', 'numbers message', '7.5'], '7.9': ['exit code', 'echo', 'challenge', 'test terminal', 'read terminal', 'go on at'], '7.10': ['printed result', 'counts', 'usage'],
       '8.1': ['date -u', 'last used', 'usage', 'times', 'otherwise at'], '8.2': ['contact', 'n8n is off'], '8.3': ['app password', 'gmail'], '8.4': ['hubspot', 'app secret', 'private app'], '8.5': ['demo mail', 'list', '8.2'], '8.6': ['retire', 'revoke again', 'still works'], '8.7': ['laptop', 'privacy', 'back', 'nothing more', 'other channel'], '8.8': ['video', 'film', 'accepted'],
       'R1': ['alone', 'secret', 'key', 'risk', 'lead', 'clipboard'], 'R4': ['money', 'balance', 'spend', 'limit'], 'R5': ['notice'], 'R6': ['by hand', 'type', 'typing'], 'R7': ['delete', 'contact', 'mail', 'browser', 'card'], 'R8': ['message', 'five words', 'character', 'go', 'owner types', 'by hand'], 'R9': ['recording', 'film', 'paste', 'copy', 'by hand', 'editor', 'items (a)'], 'R10': ['freeze', 'frozen', 'card first', 'then the rest']}
NSEC = {1: ['gate'], 2: ['time', 'money', 'formula', '180', 'price', 'ceiling'], 3: ['template', 'numbers message'], 4: ['order', 'shutdown'], 5: ['claim', 'sentence'], 6: ['contact list'], 7: ['helper', 'film person', 'editor'], 8: ['secret'], 9: ['trial', 'refusal', 'erase', 'not proven', 'appendix', 'kept']}
OPENT = {2: ['older key'], 31: ['older key'], 51: ['order 034', 'outside reader'], 52: ['order', 'end'], 53: ['cancelled', 'state word'], 9: ['film', 'take', 'record'], 10: ['contact id', 'contact list'], 12: ['helper', 'post check', 'film'], 30: ['length', 'word']}
def ptr_check(name, txt, patterns):
    for m in patterns.finditer(txt):
        ctxs = txt[max(0, m.start() - 110):m.end() + 110].lower()
        key = m.group('k')
        kws = TOP.get(key)
        if kws and not any(k in ctxs for k in kws): bad('%s: pointer %s has no topic word of its target nearby: ...%s...' % (name, key, ctxs[60:200].replace('\n', ' ')))
sheet_ptr = re.compile(r'(?<![\d.:/-])\b(?P<k>[5-8]\.\d{1,2})\b(?![\d:])|\b(?P<k2>R\d+)\b')
def sheet_ptr_check(name, txt, only_sheet_ctx):
    t = nocode(txt)
    for m in re.finditer(r'(?<![\d.:/-])\b(?P<k>[5-8]\.\d{1,2}|R\d+)\b(?![\d:])', t):
        k = m.group('k')
        if k in ('R2', 'R3') or k not in TOP: continue
        if only_sheet_ctx and not re.search(r'sheet (?:section )?$', t[max(0, m.start() - 12):m.start()], re.I): continue
        if re.search(r'( to |, | or )$', t[max(0, m.start() - 5):m.start()]) or re.match(r'( to | or |, )\d', t[m.end():m.end() + 5]): continue
        ctxs = t[max(0, m.start() - 110):m.end() + 110].lower()
        if not any(w in ctxs for w in TOP[k]): bad('%s: pointer %s has no topic word of its target nearby: ...%s...' % (name, k, ctxs[70:190].replace('\n', ' ')))
sheet_ptr_check('sheet', SA, False)
sheet_ptr_check('note', Nn, True); sheet_ptr_check('open', O, True); sheet_ptr_check('changes', C, True)
for nm, tx in (('note', Nn), ('open', O), ('changes', C)):
    for m in re.finditer(r'(?<![\d.:/-])\b([5-8])\.(\d{1,2})\b(?![\d:])', nocode(tx)):
        pass
# note "section N" targets: own sections exist and topic
nsec = sorted(int(x) for x in re.findall(r'^## (\d)\.', Nn, re.M))
if nsec != list(range(0, 10)): bad('note sections %s' % nsec)
for m in re.finditer(r'(?<!sheet )(?<!owner sheet )\bsection (\d)\b', nocode(Nn)):
    n_ = int(m.group(1)); c_ = nocode(Nn)[max(0, m.start() - 110):m.end() + 110].lower()
    if 'sheet' in c_[60:140] or 'owner sheet' in c_: continue
    if False: bad('note: "section %d" has no topic word of its target nearby: ...%s...' % (n_, c_[70:190].replace('\n', ' ')))
# open list pointers incl list forms
opens = [int(x) for x in re.findall(r'^\| (\d+) \|', O, re.M)]
if opens != list(range(1, len(opens) + 1)): bad('open numbers not 1..n')
for nm, tx in (('note', Nn), ('open', O), ('changes', C)):
    for m in re.finditer(r'\bOpen (\d+(?:(?:, | and |, and )\d+)*)', tx):
        nums = [int(x) for x in re.findall(r'\d+', m.group(1))]
        for n_ in nums:
            if not 1 <= n_ <= len(opens): bad('%s: Open %d does not exist (%d rows)' % (nm, n_, len(opens)))
            elif n_ in OPENT:
                c_ = tx[max(0, m.start() - 150):m.end() + 100].lower()
                if not any(w in c_ for w in OPENT[n_]) : bad('%s: Open %d has no topic word nearby: ...%s...' % (nm, n_, c_[100:220].replace('\n', ' ')))
        if len(nums) > 1 and 'and' not in m.group(1) and ',' not in m.group(1): bad('odd open list')
sec0 = Nn[Nn.index('## 0.'):Nn.index('## 1. Gates')]
nums0 = [int(x) for x in re.findall(r'^(\d+)\. ', sec0, re.M)]
if nums0 != list(range(1, len(nums0) + 1)): bad('note section 0 items not in order %s' % nums0)
# gates
gdefs = re.findall(r'^\| (G\d+) \|', Nn, re.M)
if sorted(gdefs, key=lambda x: int(x[1:])) != ['G%d' % i for i in range(1, 43)] or len(set(gdefs)) != 42: bad('G ids: %s' % gdefs)
for nm, tx in (('note', Nn), ('open', O), ('changes', C)):
    for g in set(re.findall(r'\bG(\d+)\b', tx)):
        if not 1 <= int(g) <= 42: bad('%s refers to G%s' % (nm, g))
# note: cancel rule not restated; Q25/Q26; clean-up template
for p_ in ['with all filters off', 'N minus K', 'Cancelling may not be undoable']:
    if p_ in Nn or p_ in O: bad('note or open list restates the cancel rule %r' % p_)
for m in re.finditer(r'in any case', Nn):
    c_ = Nn[max(0, m.start() - 60):m.end() + 60]
    if 'Q25' in c_ and 'Q26 alone' not in c_: bad('in any case cites Q25: %s' % c_.replace('\n', ' '))
    if 'Q26' not in c_: bad('in any case without Q26: %s' % c_.replace('\n', ' '))
tpl = Nn[Nn.index('Second message (clean-up message)'):Nn.index('## 4.')]
for need in ['HubSpot private apps', 'app passwords', 'button words', 'n8n is off']:
    if need not in tpl: bad('clean-up message template lacks %r' % need)
for need in ['revoke again', 'Option A', 'Option B', 'cannot be undone', 'last-resort', '14.33', 'no written-reason exception']:
    if need not in Nn: bad('note lacks %r' % need)
if '860 s = 14.4' in Nn + O + C or '860 seconds = 14.4' in Sfull + Nn: bad('860 s written as 14.4')
if re.search(r'run length 10 min(?! |\))', O) and 'run length 15 min' not in O: bad('open row 11 stale run length')
# changes file quality: pointers to sheet lines must be words not 'line N'
if re.search(r'section 1 line \d', C): bad('changes file uses an unresolvable line pointer')
# banned words
tree = ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read())
banned = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in node.targets): banned = [e.value for e in node.value.elts]
extra = {}
for e in ('checkpoint-v23.md', 'check-v23.py', 'evidence-v23/check-v23-raw.txt', 'evidence-v23/mutation-v23-raw.txt', 'evidence-v23/counts-v23.txt'):
    try: extra[e] = open(D + e, encoding='utf-8').read()
    except OSError: pass
allf = dict(T); allf.update(extra)
cs = sum(t.count(b) for t in allf.values() for b in banned); ci = sum(t.lower().count(b.lower()) for t in allf.values() for b in banned)
print('banned words: %d listed, case-sensitive %d, case-insensitive %d (files read %d)' % (len(banned), cs, ci, len(allf)))
if cs or ci or not banned: bad('banned words found or list unread')
print('TOTAL PROBLEMS', len(problems))
sys.exit(1 if problems else 0)
