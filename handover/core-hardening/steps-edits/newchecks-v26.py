"""newchecks-v26.py: checks C26 to C60, exec'd by check-v26.py with A, B, NOTE, OPEN, fail in scope.
Part 1 (C26..C47): one check per finding of the v24 stranger and security reviews. Part 2 (C48..C60): the 15 plants the independent run (Q01..Q24) showed check-v24 missed.
v24-fail-proof.py runs this same file on the v24 texts to show which checks fail on v24."""
import re
SH = (('A', A), ('B', B))
def need(code, s, which=SH):
    for n, t in which:
        if s not in t: fail(code, '%s lacks %r' % (n, s[:70]))
def ban(code, pat, which=SH, flags=0):
    for n, t in which:
        m = re.search(pat, t, flags)
        if m: fail(code, '%s holds %r' % (n, m[0][:70]))
# ---- Part 1: findings of review-v24b-security (S) and review-v24b-stranger (T)
need('C26', 'the start line is exactly `python3 -I scripts/run_real_check_n8n.py --take ` and one file name')            # S Major 1 shape check
need('C26', 'a path starts with `/home/`'); need('C26', 'a backtick')
need('C27', 'a missed 7.11 can mean spending after the deadline', (('B', B),))                                         # S Major 2 B truthful
need('C27', '7.11, always, by ' + F['okb'], (('B', B),))
need('C27', 'Until then the older key stays valid and can spend', (('B', B),))
need('C28', 'W9 the text of the older key appeared on your screen')                                                   # S Major 3 older key exposure trigger
need('C28', 'exactly the rows you wrote minus K'); ban('C28', r'N minus K')
need('C29', 'key list time zone ______'); need('C29', 'Key list time zone: <zone>')                                    # S minor 2
need('C30', '(a long random text: describe only that)')                                                                 # S minor 3
need('C31', "cancel the older key by the card's L2, steps 2 to 4", (('B', B),))                                                # S minor 4
need('C32', 'close that window, FREEZE'); need('C32', 'then run `clear` there')                                    # S minor 6 and 5.7 secret on screen (T)
need('C33', 'Conversation view is off')                                                                  # S minor 7
need('C34', '**Model account**'); need('C34', 'open it only from your own bookmark or an address you type')            # T B2
need('C35', '**Give-up minutes**'); need('C35', '**Latest start**'); need('C35', '**Send**'); need('C35', '**Describe**')   # T glossary
ban('C36', r'\b[Tt]ell(?:ing)?\b|\btold\b')                                                                            # T B4 one word one meaning
need('C37', 'send the numbers message for run <run name>')  # T B1 + other channel
need('C38', 'the receiver Gmail (gets the demo mails)'); need('C38', 'the sender Gmail (sends them)')                                                      # T minor roles
need('C39', 'People: film person <name>, editor <name>, post checker <name>')                                           # T B1 who
need('C39', 'Model settings file: <model settings file>'); need('C39', 'Posting place: <place>')
need('C40', 'A run whose key was alive ends after the card: no word resumes it.')                                      # T FREEZE resume
need('C41', 'the Windows page shows those values')                                                       # T 5.3 pass test
need('C42', '**tolerated**'); need('C42', 'A difference in a number, name, count, account, time or key state is never tolerated.')  # T UNVERIFIED rule
need('C43', 'Send exactly: ')                                                                                           # card step 5
need('C44', 'never use rotate or any button that shows a new secret')                                                   # S minor 8 rotate
ban('C44', r'rotate or delete', ((('N', NOTE), ('O', OPEN))))
ban('C45', r'Filled example')                                                                                           # sample cut
need('C46', 'then send "none" for the time in 8.1'.replace('then send', 'send') , SH)                                  # card After-the-card none
need('C47', 'a new try needs a new numbers message and yes')                                                            # key save failed path
need('C61', 'Until then the older key stays valid and can spend.', (('B', B),))   # S Major 2: B card list (b) says what the card does not stop
need('C62', 'more than 7 days before the run day', (('A', A),))                                                          # S/T older key A: recent use refuses the cancel
need('C63', 'otherwise describe each such key, cancel nothing, wait')                                    # S Major 3: no-key path cancels nothing the owner did not make
# ---- Part 2: the 15 plants check-v24 missed (own25.py), each caught by its own check
PRICES_OK = {'0.27', '0.81', '15.00', '189.00', '3.00', '7.11'}
for n, t in SH:                                                                                                         # Q01 Q02: wrong price or total anywhere
    for m in re.finditer(r'(?<![\d.])\d+\.\d\d\b(?!\.\d)', t):
        if m[0] not in PRICES_OK: fail('C48', '%s holds amount %s (allowed: %s)' % (n, m[0], sorted(PRICES_OK)))
    if t.count('0.27') < 2 or t.count('0.81') < 2: fail('C48', n + ' price or total stated less than twice')
BIG_OK = {'1,000,000', '10,000', '10000', '1500', '2026', '40,000', '40000'}
for n, t in SH:                                                                                                         # Q03: sample tokens
    for m in re.findall(r'(?<![\d.,])\d{1,3}(?:,\d{3})+\b|(?<![\d.,])\d{4,}\b', t):
        if m not in BIG_OK: fail('C49', '%s holds number %s (allowed: %s)' % (n, m, sorted(BIG_OK)))
need('C50', '(1) if a key is alive, do the card now; (2) then FREEZE')                                                  # Q08
for n, t in SH:                                                                                                         # Q09: stray backtick (even count per line)
    for i, line in enumerate(t.split('\n'), 1):
        if line.count('`') % 2 and not line.startswith('```'): fail('C51', '%s line %d has an odd number of backticks' % (n, i))
need('C52', '3. For each of your keys: press the cancel button; if a box asks, press the confirmation word.')           # Q10
for n, t in SH:                                                                                                         # Q11: card gates (a) to (i) all present, in order, (f) text exact
    i = t.find('**When (any one'); j = t.find('**What you may cancel'); w = t[i:j]; w = w[w.find('):**') + 4:]
    pos = [w.find('W%d ' % c) for c in range(1, 10)]
    if min(pos) < 0 or pos != sorted(pos): fail('C53', n + ' card triggers W1 to W9 missing or out of order')
need('C53', 'W6 the test terminal shows a prompt before you typed `end`')
need('C54', 'The account must be prepaid, auto-reload off, balance at least the expected total')                          # Q12
ban('C54', r'auto-reload on\b')
SEC = [r'\bsk-[A-Za-z0-9_-]{8,}', r'\bAKIA(?!IOSFODNN7EXAMPLE)[A-Z0-9]{12,}', r'\b[A-Za-z0-9+/_-]{40,}\b', r'\bgh[pousr]_[A-Za-z0-9]{20,}', r'\bxox[abp]-[A-Za-z0-9-]{10,}']
for n, t in (('A', A), ('B', B), ('N', NOTE), ('O', OPEN)):                                                             # Q13: secret-shaped text
    for p in SEC:
        for m in re.finditer(p, t):
            if 'run_real_check_n8n' in m[0]: continue
            fail('C55', '%s holds secret-shaped text (pattern %s)' % (n, p[:22]))
need('C56', 'Silence minutes: 3   Give-up minutes: 40')                                                                  # Q15 Q16
for n, t in SH:                                                                                                         # Q18: delete guard keeps its one domain
    if t.count('@example.com') != 3: fail('C57', '%s has %d @example.com (expected 3)' % (n, t.count('@example.com')))
    if re.search(r'@example\.(?!com)', t): fail('C57', n + ' holds a different example domain')
if 'program limit = 12.40 + 0.81 = 13.21' not in NOTE: fail('C58', 'note lacks the program limit sum')                  # Q20
for m in re.finditer(r'(?<![\d.])13\.\d\d\b', NOTE + OPEN):
    if m[0] not in ('13.00', '13.21', '13.50'): fail('C58', 'note or open list holds %s (only 13.21; 13.00 and 13.50 are the pass/fail examples)' % m[0])
need('C59', 'Exit codes accepted: 0 only')                                                                              # Q22
NUM = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7}
for n, t in SH:                                                                                                         # Q24: R8 count equals the listed words
    m = re.search(r'Only (\w+) words in a lead message start or end a step: (.*?)\. No message changes', t, re.S)
    if not m or m[1] not in NUM: fail('C60', n + ' R8 word count sentence not found'); continue
    k = len(re.findall(r'"[^"]+"', m[2]))
    if NUM[m[1]] != k: fail('C60', '%s R8 says %s words but lists %d' % (n, m[1], k))
# ---- Part 3 (v26): one check per v25 finding the independent run showed missed (N01 N05 N10 N11 N12 N14, M4) and per v25 review item.
# Literals below are written out here on purpose (not read from facts-v26.py), so a change in the source AND in facts is still seen.
def secret_hits(t):
    out = []
    for p in SEC:
        for m in re.finditer(p, t):
            if 'run_real_check_n8n' in m[0]: continue
            out.append(m[0])
    return out
need('C70', 'IST** = UTC + 5:30')                                                                                       # N01 offset label
need('C71', 'A line saying contacts will be deleted or archived, or asking you to type a figure, is always a difference.')  # N05 R5
need('C72', 'the time is before the latest start (else do not press Enter: do the card)')                              # N10 warning before cancel path
need('C73', 'Posting (by Wed 25 Nov 2026 15:00 UTC = 20:30 IST')                                                       # N11 post-by date tied to the literal
for n, t in (('N', NOTE), ('O', OPEN)):
    for m in re.finditer(r'[Pp]ost(?:ing)?[- ]by[^.\n]{0,40}?(Mon|Tue|Wed|Thu|Fri) (\d{1,2}) Nov', t):
        if (m[1], m[2]) != ('Wed', '25'): fail('C73', '%s post-by date %s %s' % (n, m[1], m[2]))
need('C74', 'You delete only made-up contacts of this run and demo mails, by hand, one by one.')                         # N12 active voice, who does what
need('C75', 'Run `date -u` in the read terminal: the run day still holds and the time is before the latest start (else do not press Enter')  # N14 full command
need('C76', 'Prices per million: in USD 3.00, out USD 15.00')                                                          # M4 price line
need('C77', 'Tokens in and out per call: 40000 and 10000'); need('C77', 'TOKENS_IN = 40000 | TOKENS_OUT = 10000')      # M4 tokens
need('C78', 'DEADLINE = 2026-11-23T18:29:00Z')                                                                          # M4 DEADLINE line
need('C79', 'Deadline 2026-11-23 18:29 UTC = 23:59 IST."')                                                              # M4 yes-line deadline pair
fake = 'q' * 8 + '/' + 'Z' * 16 + '_' + 'k' * 12 + '-' + 'm' * 9                                                        # C55 gap: a 47-character secret-shaped text with a slash, built from parts
if not secret_hits('x ' + fake + ' y'): fail('C80', 'the secret scan misses a 47-character text with a slash')
need('C81', 'for exactly these seven settings, `MODEL_NAME`, `TOKENS_IN`, `TOKENS_OUT`, `PRICE_IN_CENTS`, `PRICE_OUT_CENTS`, `CALL_CEILING`, `DEADLINE`')
need('C81', 'first do 6.1 (Recording and the Privacy switches OFF')
need('C82', 'has no `..` and no part starting with `.`'); need('C82', 'the key file name contains the run name and lies inside the Take folder of the message')
need('C83', 'addresses starting `take-<run name>-` or `prep-` and ending `@example.com`')
need('C84', 'type `rm -- "<key file>"`'); need('C84', 'then `ls -l "<key file>"` in the read terminal must say no such file')
need('C85', '"restarted" (6.6)'); need('C85', '"restarted" came after 6.6')
need('C86', '7.11, always, by 16:00 UTC = 21:30 IST', (('B', B),)); need('C86', 'Not done by 16:00 UTC = 21:30 IST', (('B', B),))
if '16:00 UTC' in A: fail('C86', 'A holds the B-only time')
need('C87', 'exactly the rows you wrote minus K'); need('C87', 'rows now, own key ______ | rows now, older key ______')
need('C88', 'This cancel cannot be undone.'); need('C88', '**Older key (cannot be undone).**', (('B', B),))
need('C89', 'only at 6.7, after 6.6 passed (new key saved, size checked)', (('A', A),))                                    # stranger blocker: older key cancel last, after the key is saved
s6 = A.find('## 6. The model key'); s7 = A.find('## 7. The run')
i6 = A.find('\n7. **Last checks, then the older key.**', s6, s7); i66 = A.find('\n6. ', s6, s7)
if i6 < 0 or i66 < 0 or i66 > i6: fail('C89', 'A: the older-key step is not after step 6.6 inside section 6')
need('C90', '**Filled after you press create (6.3), not before:**'); need('C90', '**Filled during the card, just before each cancel (step 2):**')
need('C91', '**FREEZE** (a key alive: the card first)')
need('C92', 'the **backup person** (a human you can call'); need('C92', 'none named: no run')
need('C93', 'the only valid answer is their own written words "matches the sentences"')
need('C94', 'A differing printed count: send the counts, do not post, FREEZE.')
for nm, t in SH:                                                                                                        # Gmail label and Chrome profile: how, or an explicit "ask the lead" (both places)
    if t.count('how unknown: ask the lead') != 2: fail('C95', '%s: "how unknown: ask the lead" appears %d times (expected 2: Gmail label, Chrome profile)' % (nm, t.count('how unknown: ask the lead')))
need('C96', '**Deadline** = the end of the period your spending approval covers')
need('C97', 'remove only that profile, never your normal profile')
need('C98', '**Key** alone = a model key'); need('C98', 'a **run** = this one filmed attempt'); need('C98', '**Run day** = the one day of the run')
for slot in ('Other channel:', 'Backup person:', 'Cancelled word:', 'Last-resort step:', 'Key list time zone:', 'Model settings file:', 'Key file:', 'Take folder:', 'cd line:', 'Key list address:',
             'Prepaid page address:', 'Masked in the notice:', 'Gap before 8.1:', 'Spend lock:', 'Key file size in bytes:', 'Price page:', 'Film cue:', 'Waiting line:', 'Demo mail subject start:',
             'Earlier demo mails expected:', 'Recording tool:', 'Posting place:', 'Video by:', 'Latest start:', 'Cancel-by time:', 'Earliest key time:'):
    need('C99', slot)
need('C100', 'the per-key limit if the message names one, the narrowest scopes that allow model calls')                 # per-key limit and scopes before create
need('C101', 'plugged in; sleep Never')                                                                                  # laptop slot
need('C102', '(no earlier run used it or begins like it)')                                                               # run name reuse rule
for nm, t in SH:                                                                                                         # one Chrome profile name everywhere
    names = set(re.findall(r'`(demo-[a-z]+)`', t))
    if names != {'demo-take'} or t.count('demo-take') < 3: fail('C103', '%s: Chrome profile names %s, demo-take x%d' % (nm, sorted(names), t.count('demo-take')))
need('C104', 'the entry is the one with the exact name the numbers or clean-up message gives; no name known: describe, revoke nothing')   # how to identify the entry to revoke
need('C104', 'whether it can be undone')                                                                                  # last-resort reversibility is stated
