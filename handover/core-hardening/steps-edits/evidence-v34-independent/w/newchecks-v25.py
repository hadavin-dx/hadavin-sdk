"""newchecks-v25.py: checks C26 to C60, exec'd by check-v25.py with A, B, NOTE, OPEN, fail in scope.
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
need('C27', 'a missed 8.6 can mean spending after the deadline', (('B', B),))                                         # S Major 2 B truthful
need('C27', 'always (the deadline forbids a valid paid key after it)', (('B', B),))
need('C27', 'the card does not stop it', (('B', B),))
need('C28', '(i) the text of the older key appeared on your screen')                                                   # S Major 3 older key exposure trigger
need('C28', 'For the older key (list (b)), N is the count now and K is 1.')
need('C29', 'key list time zone ______'); need('C29', 'Key list time zone: <zone>')                                    # S minor 2
need('C30', '(a long random text: describe only that)')                                                                 # S minor 3
need('C31', "cancel it by the card's list (b), steps 2 to 4", (('B', B),))                                                # S minor 4
need('C32', 'close that window, then FREEZE'); need('C32', 'then run `clear` there')                                    # S minor 6 and 5.7 secret on screen (T)
need('C33', 'Conversation view off in Gmail settings')                                                                  # S minor 7
need('C34', '**Model account**'); need('C34', 'open it only from your own bookmark or an address you type')            # T B2
need('C35', '**Give-up minutes**'); need('C35', '**Latest start**'); need('C35', '**Send**'); need('C35', '**Describe**')   # T glossary
ban('C36', r'\b[Tt]ell(?:ing)?\b|\btold\b')                                                                            # T B4 one word one meaning
need('C37', 'send the numbers message for run <run name>')  # T B1 + other channel
need('C38', 'the receiver Gmail (gets the demo mails)'); need('C38', 'the sender Gmail (sends them)')                                                      # T minor roles
need('C39', 'People: film person <name>, editor <name>, post checker <name>')                                           # T B1 who
need('C39', 'Model settings file: <model settings file>'); need('C39', 'Posting place: <place>')
need('C40', 'If a key was alive the run ends after the card: no word resumes it.')                                      # T FREEZE resume
need('C41', 'after setting, the Windows page shows those values')                                                       # T 5.3 pass test
need('C42', '**tolerated**'); need('C42', 'A difference in a number, name, count, account, time or key state is never tolerated.')  # T UNVERIFIED rule
need('C43', 'Send exactly: ')                                                                                           # card step 5
need('C44', 'never use rotate or any button that shows a new secret')                                                   # S minor 8 rotate
ban('C44', r'rotate or delete', ((('N', NOTE), ('O', OPEN))))
ban('C45', r'Filled example')                                                                                           # sample cut
need('C46', 'then send "none" for the time in 8.1'.replace('then send', 'send') , SH)                                  # card After-the-card none
need('C47', 'a new try needs a new numbers message and yes')                                                            # key save failed path
need('C61', 'Until then the older key stays valid and can spend; the card does not stop it.', (('B', B),))   # S Major 2: B card list (b) says what the card does not stop
need('C62', 'more than 7 days before the run day', (('A', A),))                                                          # S/T older key A: recent use refuses the cancel
need('C63', "otherwise describe each such key's name and time, cancel nothing, wait")                                    # S Major 3: no-key path cancels nothing the owner did not make
# ---- Part 2: the 15 plants check-v24 missed (own25.py), each caught by its own check
PRICES_OK = {'0.27', '0.81', '15.00', '189.00', '3.00'}
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
    pos = [w.find('(%s) ' % c) for c in 'abcdefghi']
    if min(pos) < 0 or pos != sorted(pos): fail('C53', n + ' card trigger letters (a) to (i) missing or out of order')
need('C53', '(f) the test terminal shows a prompt (a line like `name@computer:~$`) before you typed `end`')
need('C54', 'The account must be prepaid, auto-reload off, balance at least the expected total')                          # Q12
ban('C54', r'auto-reload on\b')
SEC = [r'\bsk-[A-Za-z0-9_-]{8,}', r'\bAKIA(?!IOSFODNN7EXAMPLE)[A-Z0-9]{12,}', r'\b[A-Za-z0-9+/_-]{40,}\b', r'\bgh[pousr]_[A-Za-z0-9]{20,}', r'\bxox[abp]-[A-Za-z0-9-]{10,}']
for n, t in (('A', A), ('B', B), ('N', NOTE), ('O', OPEN)):                                                             # Q13: secret-shaped text
    for p in SEC:
        for m in re.finditer(p, t):
            if 'run_real_check_n8n' in m[0] or '/' in m[0] and len(m[0]) < 60: continue
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
