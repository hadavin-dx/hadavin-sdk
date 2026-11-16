"""Independent checker for owner sheet v29. Does NOT import check-v29.py or build-v29.py. Usage: python3 -B -I indep_check.py <folder>
Prints one FAIL line per finding; exit 1 if any. Reads only; writes nothing."""
import re, sys, datetime as dt, os
D = sys.argv[1].rstrip('/') + '/'
OWNER = lambda k: ['OWNER-SHEET-v29-%s.md' % k, 'OWNER-CARD-v29-%s.md' % k, 'OWNER-APPENDIX-v29-%s.md' % k]
FILES = OWNER('A') + OWNER('B') + ['OWNER-FILM-PERSON-v29.md', 'LEAD-RELEASE-NOTE-v13.md', 'v29-OPEN-FOR-LEAD.md']
T = {}
fails = []
def fail(c, m): fails.append('FAIL %s %s' % (c, m))
for n in FILES:
    try: T[n] = open(D + n, encoding='utf-8').read()
    except Exception as e: fail('I00', 'cannot read %s: %s' % (n, type(e).__name__)); T[n] = ''
OWNER_FACING = [n for n in FILES if n.startswith('OWNER-')]
# I01 word counts
for k in 'AB':
    w = len(T['OWNER-SHEET-v29-%s.md' % k].split())
    if w > 6300: fail('I01', 'sheet %s has %d words, limit 6300' % (k, w))
    if w < 4000: fail('I01', 'sheet %s only %d words (suspiciously short)' % (k, w))
    for n in ('OWNER-CARD-v29-%s.md' % k, 'OWNER-APPENDIX-v29-%s.md' % k):
        if len(T[n].split()) < 500: fail('I01', '%s only %d words' % (n, len(T[n].split())))
# I02 every UTC time followed by = IST pair with +5:30 (calendar-aware not needed: wraps mod 1440)
rx_utc = re.compile(r'(?<![\d:])(\d\d):(\d\d)(?::(\d\d))? UTC\b')
rx_pair = re.compile(r' = (\d\d):(\d\d)(?::(\d\d))? IST')
for n, t in T.items():
    for line_no, line in enumerate(t.split('\n'), 1):
        for m in rx_utc.finditer(line):
            p = rx_pair.match(line, m.end())
            if not p:
                fail('I02', '%s:%d UTC time without IST pair: %r' % (n, line_no, line[max(0, m.start() - 10):m.end() + 40])); continue
            u = int(m[1]) * 60 + int(m[2]); i = int(p[1]) * 60 + int(p[2])
            if (u + 330) % 1440 != i or (m[3] and p[3] and m[3] != p[3]): fail('I02', '%s:%d bad IST for %s -> %s' % (n, line_no, m[0], p[0]))
        for m in re.finditer(r'(?<![\d:])(\d\d):(\d\d)(?::\d\d)? IST', line):          # IST with no UTC before it
            if not re.search(r'UTC = ' + re.escape(m[0]), line): fail('I02', '%s:%d IST time with no UTC partner: %s' % (n, line_no, m[0]))
# I03 weekdays
MON = {m: i + 1 for i, m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}
for n, t in T.items():
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b,? (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b(?: (\d{4}))?', t):
        y = int(m[4] or 2026)
        if dt.date(y, MON[m[3]], int(m[2])).strftime('%a') != m[1]: fail('I03', '%s wrong weekday %r' % (n, m[0]))
    for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b,? (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})\b(?: \d\d:\d\d:\d\d (\d{4}))?', t):
        y = int(m[4] or 2026)
        if dt.date(y, MON[m[2]], int(m[3])).strftime('%a') != m[1]: fail('I03', '%s wrong weekday %r' % (n, m[0]))
    for m in re.finditer(r'\b(\d{1,2}) (Nov)\b(?! 2026)', t):          # a bare day-month near a weekday is covered above; flag Nov dates written with another year
        pass
    for m in re.finditer(r'\b(\d{1,2}) Nov (20\d\d)', t):
        if m[2] != '2026': fail('I03', '%s wrong year %r' % (n, m[0]))
# fixed expectations for the four named days
for d, wd in ((16, 'Mon'), (18, 'Wed'), (23, 'Mon'), (25, 'Wed')):
    if dt.date(2026, 11, d).strftime('%a') != wd: fail('I03', 'self-test calendar')
    for n, t in T.items():
        for m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) %d Nov' % d, t):
            if m[1] != wd: fail('I03', '%s: %d Nov named as %s' % (n, d, m[1]))
for n, t in T.items():
    if n.startswith('OWNER-SHEET') and 'Dated Mon 16 Nov 2026' not in t: fail('I03', n + ' lacks "Dated Mon 16 Nov 2026"')
# I04 key facts
SH = {k: T['OWNER-SHEET-v29-%s.md' % k] for k in 'AB'}
for k, t in SH.items():
    if 'Mon 23 Nov 2026 18:29 UTC = 23:59 IST' not in T['OWNER-APPENDIX-v29-%s.md' % k] and 'Mon 23 Nov 2026 18:29 UTC = 23:59 IST' not in t: fail('I04', 'sheet %s: money stop 18:29 = 23:59 on Mon 23 Nov missing' % k)
    if 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST' not in t: fail('I04', 'sheet %s: post-by Wed 25 Nov 15:00 UTC = 20:30 IST missing' % k)
NOTE = T['LEAD-RELEASE-NOTE-v13.md'] + '\n' + T['v29-OPEN-FOR-LEAD.md']
for n in ('LEAD-RELEASE-NOTE-v13.md', 'v29-OPEN-FOR-LEAD.md'):
    t = T[n]
    if '18:19 UTC = 23:49 IST' not in t: fail('I04', n + ' lacks key-end 18:19 UTC = 23:49 IST')
if '18:29 UTC = 23:59 IST' not in NOTE: fail('I04', 'lead files lack money stop 18:29 UTC = 23:59 IST')
for n, t in T.items():
    for line_no, line in enumerate(t.split('\n'), 1):
        for m in re.finditer(r'18:14:40|23:44:40', line):
            if not re.search(r'refusal limit', line, re.I): fail('I04', '%s:%d 18:14:40/23:44:40 without the label "refusal limit" on the line' % (n, line_no)); break
if not re.search(r'refusal limit[^\n]{0,80}18:14:40 UTC = 23:44:40 IST', NOTE): fail('I04', 'refusal limit 18:14:40 UTC = 23:44:40 IST not stated with label in lead files')
for n, t in T.items():       # any 23:xx IST / 18:xx UTC key-end claims that differ
    for m in re.finditer(r'key revoked by (\d\d:\d\d) UTC', t):
        if m[1] != '18:19': fail('I04', '%s key revoked by %s (expected 18:19)' % (n, m[1]))
# I05 internal codes in owner-facing text
for n in OWNER_FACING:
    for m in re.finditer(r'(?<![A-Za-z0-9])(Q\d{2}|L-[A-Za-z0-9]+|E-\d+|ORD:)', T[n]): fail('I05', '%s internal code %r' % (n, m[0]))
# I06 placeholders
for n, t in T.items():
    for m in re.finditer(r'\[[^\]\n]{0,40}(?:FILLS|fills|Fills)[^\]\n]*\]', t):
        s = m[0]
        if not (re.fullmatch(r'\[OWNER FILLS: [^\]\n]+\]', s) or re.fullmatch(r'\[LEAD FILLS at re-pin: [^\]\n]+\]', s)):
            if n in OWNER_FACING and ('`[LEAD FILLS at re-pin: ...]`' in t) and s in ('[LEAD FILLS at re-pin: ...]', '[OWNER FILLS: ...]'): continue
            fail('I06', '%s misspelled/odd placeholder %r' % (n, s[:70]))
    for m in re.finditer(r'(?i)\[(owner|lead) fill[^\]\n]*\]', t):
        if not m[0].startswith(('[OWNER FILLS: ', '[LEAD FILLS at re-pin: ')): fail('I06', '%s odd placeholder %r' % (n, m[0][:70]))
for k in 'AB':
    if '[OWNER FILLS: ' not in SH[k] or '[LEAD FILLS at re-pin: ' not in SH[k]: fail('I06', 'sheet %s shows no placeholder of one kind' % k)
# I07 sheet letter
for k, o in (('A', 'B'), ('B', 'A')):
    s, c, a = OWNER(k)
    if not T[s].startswith('# Owner sheet v29, sheet %s: ' % k): fail('I07', s + ' heading letter')
    if not T[s].rstrip().endswith('End of sheet %s (OWNER-SHEET-v29-%s.md).' % (k, k)): fail('I07', s + ' footer letter')
    if not T[a].startswith('# Owner appendix v29, sheet %s' % k): fail('I07', a + ' heading letter')
    if not T[a].rstrip().endswith('End of the appendix, sheet %s (OWNER-APPENDIX-v29-%s.md).' % (k, k)): fail('I07', a + ' footer letter')
    if not T[c].startswith('### THE CARD, sheet %s' % k): fail('I07', c + ' heading letter')
    if not T[c].rstrip().endswith('End of the card, sheet %s.' % k): fail('I07', c + ' footer letter')
    for n in (s, c):
        for m in re.finditer(r'(?<![A-Za-z])sheet %s\b' % o, T[n]):
            ctx = T[n][max(0, m.start() - 70):m.end() + 50].replace('\n', ' ')
            if re.search(r'take sheet|take it|instead|leaves it|cancels the older|differs|letter|no run|sheet %s or|or sheet %s' % (o, o), ctx): continue
            fail('I07', '%s other sheet letter out of context: %r' % (n, ctx))
# I08 route A/B and 7-day rule, key-shred, card shape
A_, B_ = SH['A'], SH['B']
if 'take sheet B' not in A_: fail('I08', 'sheet A lacks the route condition "take sheet B"')
if not re.search(r'7 days or more before', A_): fail('I08', 'sheet A lacks "7 days or more before" route condition')
if 'take sheet A' not in B_ and 'sheet A' not in B_: fail('I08', 'sheet B does not point back to sheet A route')
if not re.search(r'less than 7 days|used within|used less than', B_): fail('I08', 'sheet B lacks the "used less than 7 days" condition')
if 'cancel it at 6.7' not in A_: fail('I08', 'sheet A lacks planned older-key cancel at 6.7')
if 'cancel it at 6.7' in B_: fail('I08', 'sheet B must not cancel the older key at 6.7')
if 'older key stays valid and can spend until you cancel it at 7.11' not in B_: fail('I08', 'sheet B lacks "older key stays valid ... until you cancel it at 7.11"')
for k in 'AB':
    s, c, a = OWNER(k)
    if 'rm -- "<key file>"' not in T[s]: fail('I08', s + ' lacks the key-file delete step rm -- "<key file>"')
    if k == 'A' and '7 days (168 hours) or more before' not in T[c]: fail('I08', c + ' lacks the 7-day (168 hours) line')
    if k == 'B' and '7.11' not in T[c]: fail('I08', c + ' lacks 7.11 older-key step')
    for w in ['W%d ' % i for i in range(1, 10)] + ['L%d ' % i for i in range(1, 6)]:
        if w not in T[c]: fail('I08', c + ' lacks ' + w.strip())
    if 'model key cancelled' not in T[c]: fail('I08', c + ' lacks the send word "model key cancelled"')
    if not all(('\n%d. ' % i) in T[c] for i in range(1, 6)): fail('I08', c + ' lacks one of the five steps')
    if '"If it fails"' not in T[c] and '**If it fails.**' not in T[c]: fail('I08', c + ' lacks the If it fails section')
    if T[a].count('## Appendix part') < 5: fail('I08', a + ' lost appendix parts')
# I09 money facts (integers: 40000*300 + 10000*1500 per million = 27 cents; 3 calls = 81; limit 1240+81 = 1321)
p = (40000 * 300 + 10000 * 1500) // 1000000; assert p == 27
for k in 'AB':
    s, c, a = OWNER(k)
    for n in (s, a):
        if '0.27' not in T[n] or '0.81' not in T[n]: fail('I09', n + ' lacks 0.27 or 0.81')
        if '189.00' not in T[n]: fail('I09', n + ' lacks sample balance 189.00')
if not re.search(r'13\.21', NOTE): fail('I09', 'lead files lack limit 13.21')
if not re.search(r'\b860 s', NOTE): fail('I09', 'lead files lack 860 s')
if '14.33' not in NOTE: fail('I09', 'lead files lack 14.33 min')

# I10 (added after plant run 1: gaps found in my own checker)
if A_.count('take sheet B') < 2: fail('I10', 'sheet A: route A condition appears %d times, expected 2' % A_.count('take sheet B'))
if A_.count('7 days (168 hours) or more before') < 2: fail('I10', 'sheet A: 7-day (168 hours) line appears fewer than 2 times')
for k in 'AB':
    if "except the key's own one-time display" not in T['OWNER-CARD-v29-%s.md' % k]: fail('I10', 'card %s lacks the W7 exception' % k)
for m in re.finditer(r'\b(8[0-9]{2}) s\b', NOTE):
    if m[1] != '860': fail('I10', 'lead files: run length %s s (expected 860)' % m[1])
for k in 'AB':
    ap = T['OWNER-APPENDIX-v29-%s.md' % k]
    for name, val in (('TOKENS_IN', '40000'), ('TOKENS_OUT', '10000'), ('PRICE_IN_CENTS', '300'), ('PRICE_OUT_CENTS', '1500'), ('CALL_CEILING', '3')):
        mm = re.search(name + r' = (\d+)', ap)
        if not mm or mm[1] != val: fail('I10', 'appendix %s setting %s = %s (expected %s)' % (k, name, mm[1] if mm else None, val))
print('\n'.join(sorted(set(fails))))
print('indep_check: %d failure line(s)' % len(set(fails)))
sys.exit(1 if fails else 0)
