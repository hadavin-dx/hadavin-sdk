"""newchecks-v28.py: checks C26 to C60, exec'd by check-v28.py with A, B, NOTE, OPEN, fail in scope.
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
need('C53', 'W6 the test terminal shows a shell prompt before you typed `end`')
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
    if t.count('@example.com') != 4: fail('C57', '%s has %d @example.com (expected 4: people line, R7 twice, prep contact)' % (n, t.count('@example.com')))
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
# ---- Part 3 (v28): one check per v25 finding the independent run showed missed (N01 N05 N10 N11 N12 N14, M4) and per v25 review item.
# Literals below are written out here on purpose (not read from facts-v28.py), so a change in the source AND in facts is still seen.
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
need('C83', 'addresses `take-<run name>-a@example.com`, `-b@` and `-c@` or `prep-<run name>@example.com`')
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
need('C90', '**Filled after you press create of the run key (6.3), not before:**'); need('C90', '**Filled during the card, just before each cancel (step 2):**')
need('C91', '**FREEZE** (a key alive: the card first)')
need('C92', 'the **backup person** (a human you can call'); need('C92', 'none named: no run')
need('C93', 'the only valid answer is their own written words "matches the sentences"')
need('C94', 'A differing printed count: send the counts, do not post, FREEZE.')
for nm, t in SH:                                                                                                        # Gmail label and Chrome profile: a click path (UNVERIFIED, tolerated) in both places, never "how unknown"
    if 'how unknown' in t: fail('C95', nm + ': "how unknown" still present')
    need('C95', 'Gmail on the web: gear icon, See all settings, Filters and Blocked Addresses', ((nm, t),)); need('C95', 'click your profile picture at the top right, Add profile, Continue without an account', ((nm, t),))
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

# ---- Part 4 (v28): one check per finding of review-v26-stranger.md (T) and review-v26-security.md (S). Each fails on the built v26 sheets and passes on v28 (v28-fail-proof.py shows it).
# Literals are written out here on purpose (not read from facts-v28.py).
def pos(t, s): return t.find(s)
need('C105', 'silence at the y question, before the film cue, in the film pause and while waiting for `end` is normal')                  # T BL1
need('C105', 'counted only from your Enter on the start line until the notice, and from your challenge answer until you send "run started"')
need('C106', '9. **Look key (after "go", before the earliest key time).**')                                                              # T BL2, S M4 of v26: words seen on a real cancel before the run key matters
need('C106', 'write on the card the three words you see: cancel button, confirmation box (the button that really cancels) and cancelled word')
need('C107', 'A button or box word that differs from the blank: press nothing, go to "If it fails".')                                  # T BL2: a differing word never makes the owner improvise
need('C108', 'you see the real word at 5.9 and that word counts')                                                                        # T BL2: blanks come from what the owner saw
ban('C108', r'word seen by the lead|seen by the lead')
need('C108', 'Cancelled word: <sample word or unknown> (UNVERIFIED sample; you see the real word at 5.9)')
need('C109', 'a new key can always be made; only a program that uses the older key would be hurt', (('A', A),))                         # T M2
need('C110', 'the last resort applies (the older key may still spend)', (('A', A),))                                                     # T M3
for nm, t in SH:                                                                                                                         # T M4: the key-save line is typed before the key exists
    a = pos(t, 'Then in the test terminal type the printed line of 6.4'); b = pos(t, 'Only then press create')
    if a < 0 or b < 0 or a > b: fail('C111', nm + ': the printed key-save line is not typed before the create press in 6.3')
need('C111', 'it waits at the paste line and nothing is alive yet')
need('C111', 'The printed line, with the key file path from the message (typed at 6.3):')
need('C111', '(the fixed printed line of 6.4 is typed as printed; only its key file path is checked)')                                    # T M4 R6 exemption
need('C112', 'a state word you cannot judge counts as valid')                                                                            # T M5
need('C113', 'the lead names the model company when it confirms the run name'); need('C113', 'model company and account <name>')         # T M6
need('C114', 'Windows Settings, System, Power & battery'); need('C114', 'Control Panel, Power Options')                                   # T M7
need('C115', 'the sender Gmail only at 8.3, in this profile, never in your normal profile'); need('C115', 'sign that account in at `demo-take` for this step only')   # T M8
need('C116', "open the key list address in your phone's browser, signed in, and describe whether it loads")                              # T M9
need('C117', 'The last-resort step only stops spending (it never closes the account or removes other keys) and says whether it can be undone')   # T M10
need('C118', '**Spend lock** = a lock that stops the model program making paid calls'); need('C118', '"NOT SHOWN" = nobody has shown it exists')   # T M11
need('C119', '**"restarted"** = the lead\'s word that it started again and now reads the key file')                                     # T M12
need('C120', '**submitted N times**'); need('C120', '**person id** = the made-up code'); need('C120', 'a printed line "unknown" for C is allowed')   # T M13
need('C120', '**HubSpot app secrets** = secret values of the small HubSpot programs')
need('C121', "your phone's clock (IST minus 5:30) is within 2 minutes of it"); need('C121', 'a difference of more than 2 minutes after converting the zones')   # T M14
need('C122', 'say "filmed" and read both counts aloud'); need('C122', 'the counts the film person read aloud equal the expected counts')   # T M15
for nm, t in SH:                                                                                                                         # T M16: prompt has one meaning each
    need('C123', '**Shell prompt** = the line ending in `$`', ((nm, t),)); need('C123', '**The y question** = the line `Type y to start`', ((nm, t),)); need('C123', '**Paste line** = `paste key, Enter:`', ((nm, t),))
    for m in re.finditer(r'(?<![Ss]hell )(?<!\*\*)prompt', t): fail('C123', '%s holds "prompt" without "shell" at %d' % (nm, m.start()))
need('C124', 'none within the silence minutes: describe, FREEZE; no key is alive then')                                                  # T M17
need('C125', 'Start only after the lead\'s word "post" (it means the lead has the printed result and the video is accepted)')           # T M18
need('C126', 'A run that ended before 6.7: no cancel of it until the lead sends a new numbers message', (('A', A),))                     # T M19
need('C127', 'a second Ubuntu window where you only type `date -u`, `ls -l`, `clear` and the grep of 5.7')                                                                                     # T m2
need('C128', '"none" only at 8.1')                                                                                                       # T m4
need('C129', 'Minimum think time: 20 seconds'); need('C129', 'Run length: 15 minutes')                                                   # S M2, S m10
need('C130', '[[A:(its list L2 included, at 6.7)]]'.replace('[[A:', '').replace(']]', ''), (('A', A),)); need('C130', '(its list L2 included, and 7.11)', (('B', B),))   # T m14
need('C131', 'copy a harmless word such as `clear`')                                                                                     # T m15
need('C132', 'run `rm -f -- "<key file>"` (R6 shape check first; the file may not exist)')                                              # S m1
need('C133', '(only names the clean-up message already listed)')                                                                         # S m5
need('C134', 'revoke the apps the message names'); ban('C134', r'delete or revoke')                                                      # S m6
need('C135', 'or `prep-<run name>@example.com`')                                                                                         # S m7
need('C136', "host name only (the part before the first `/`; type it by hand)")                                                          # S m8
need('C137', 'On every route, after your yes, do 7.11 before 8.1 if it is not done.', (('B', B),))                                       # S B1
need('C137', '(on every route after your yes; 7.11 is named in "After the card", "If it fails", FREEZE and R1)', (('B', B),))
need('C137', '(after your yes, 7.11 is still due by 16:00 UTC = 21:30 IST)', (('B', B),))
need('C137', 'whatever way the run ended (finished, declined, time passed, key save failed, cancel failed, FREEZE, no `end`)', (('B', B),))
need('C138', 'Four phone alarms', (('B', B),)); need('C138', 'alarm 4 at 16:00 UTC = 21:30 IST (do 7.11 now, whatever else is open)', (('B', B),))   # S B1 fourth alarm
if 'alarm 4' in A: fail('C138', 'A holds the B-only fourth alarm')
need('C139', 'The cancel-by time is before 16:00 UTC = 21:30 IST.', (('B', B),))                                                         # S B1 time order checked by the owner
_ct = re.search(r'Cancel-by time: (\d\d):(\d\d) UTC', B); _ot = re.search(r'alarm 4 at (\d\d):(\d\d) UTC', B)
if not _ct or not _ot or (int(_ct[1]) * 60 + int(_ct[2])) >= (int(_ot[1]) * 60 + int(_ot[2])): fail('C139', 'B: the cancel-by time is not before the older-key time (read from the text)')
need('C140', 'Wait at least 20 seconds (the minimum think time of the message; the program refuses faster answers)'); ban('C140', r'Wait 10 seconds')   # S M2
need('C141', 'Test program asks you to type a figure: no'); need('C141', 'a figure line that is not "no": no run')                          # S M3
need('C142', 'this cancel cannot be undone.', (('B', B),)); need('C142', 'send its last-used time (a use after your run key\'s create time: describe it, still cancel)', (('B', B),))   # S M5
need('C143', 'Model key outside the model program: none (the lead checked n8n\'s credential store and shows it)'); need('C143', 'a model key stored in n8n would spend without the spend lock')   # S M6
need('C144', 'anything but `exit 0` and the shell prompt: FREEZE')                                                                       # S m2
need('C145', 'put the Privacy switches back as 8.7 says')                                                                                # S m3
need('C146', 'if the last-used time is under 7 days'.replace('if the last-used time is under 7 days', 'else no run today (describe it and wait: the lead sends a new numbers message with a later run day at least 8 days after that use'), (('A', A),))   # S M4: what happens when the 7-day rule fails
need('C147', '5.1 to 5.8 may be done on earlier days, 5.9 and sections 6 to 8 only on the run day')                                      # T m10
need('C148', 'or no sentence "the test program made no delete call": skip that step (all deleting) and describe which')                  # S m14
need('C159', 'alarm 1 at the latest start, alarm 2 at the alarm time, alarm 3 at the cancel-by time')                                      # plant P11 showed the alarm contents were unchecked
# ---- Part 5 (v28): lead-side documents must match the built sheets (S M1 and the stranger's lead-document findings)
for nm, t in (('N', NOTE), ('O', OPEN)):
    if re.search(r'Builder proposes B|safe default B\b|builder recommends A for money and chose neither', t): fail('C149', nm + ': still recommends B or contradicts itself on A and B')
    if re.search(r'older key stays valid unless its text appears', t): fail('C149', nm + ': stale description of B')
if 'Money-safe default if you do not choose: A.' not in NOTE: fail('C149', 'N: A is not named as the money-safe default')
if 'Safe default if you do not answer: A' not in OPEN: fail('C149', 'O: row 71 does not name A as the safe default')
if '6.2 option A none at all' in NOTE or '6.6 and 6.7 option A exactly' in NOTE: fail('C150', 'N: G26 still says A has no older key at 6.2 (v26 A keeps the older key valid until 6.7)')
if 'no valid key except the older key (if the message names one); 6.6 and the last checks of 6.7' not in NOTE: fail('C150', 'N: G26 not rewritten for the older key')
if 'sheet B has a fourth alarm at 16:00 UTC = 21:30 IST' not in NOTE: fail('C151', 'N: G30 or alarms count wrong for B')
if '4 owner: two alarms' in NOTE: fail('C151', 'N: the day order still says two alarms')
if 'Test program asks you to type a figure: no' not in NOTE or 'G35' not in NOTE: fail('C152', 'N: typed-figure line / G35 missing')
if 'Minimum think time' not in NOTE or 'Minimum think time' not in OPEN: fail('C153', 'note and open list must name the minimum think time slot')
if 'WHEN IT FAILS (v28)' not in OPEN: fail('C154', 'O: row 78 does not say what happens when the 7 day rule fails')
if 'NOT MET at v28' not in OPEN: fail('C155', 'O: row 75 does not say the word target is not met')
if 'checked by you with `ls ~/.hadavin-take-tags`' not in NOTE: fail('C156', 'N: run name check by the lead missing')
for nm, t in (('N', NOTE), ('O', OPEN)):
    if re.search(r'\bpay in (only )?(a little(?! more)|less)\b', t.replace('no request to pay in less', '').replace('propose no second account and no smaller payment', '')) : fail('C157', nm + ': suggests the owner pays in less (Q24)')
if 'Added in v11' not in NOTE or 'look key' not in NOTE.lower(): fail('C158', 'N: v11 section or look key missing')
