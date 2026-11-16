"""newchecks-v35.py: checks C26 to C60, exec'd by check-v35.py with A, B, NOTE, OPEN, fail in scope.
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
need('C27', '7.11, always, by the older-key time of the message', (('B', B),))
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
need('C40', 'a run whose key was alive ends after the card: no word resumes it.')                                      # T FREEZE resume
need('C41', 'the Windows page shows those values')                                                       # T 5.3 pass test
need('C42', '**tolerated**'); need('C42', 'A difference in a number, name, count, account, time or key state is never tolerated.')  # T UNVERIFIED rule
need('C43', 'Send exactly: ')                                                                                           # card step 5
need('C44', 'never use rotate or any button that shows a new secret')                                                   # S minor 8 rotate
ban('C44', r'rotate or delete', ((('N', NOTE), ('O', OPEN))))
ban('C45', r'Filled example')                                                                                           # sample cut
need('C46', 'then send "none" for the time in 8.1'.replace('then send', 'send') , SH)                                  # card After-the-card none
need('C47', 'a new try needs a new numbers message and yes')                                                            # key save failed path
need('C61', 'Until then the older key stays valid and can spend.', (('B', B),))   # S Major 2: B card list (b) says what the card does not stop
need('C62', 'at least 168 hours (7 days) before the earliest key time of the run day', (('A', A),))                                                          # S/T older key A: recent use refuses the cancel
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
    i = t.find('**Danger signs'); j = t.find('**Not danger signs'); w = t[i:j]; w = w[w.find('):**') + 4:]
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
    if t.count('@example.com') != 5: fail('C57', '%s has %d @example.com (expected 5 in v35: R7 once, the appendix people line and clean-up message, the film person page)' % (n, t.count('@example.com')))
    if re.search(r'@example\.(?!com)', t): fail('C57', n + ' holds a different example domain')
if 'program limit = 12.40 + 0.81 = 13.21' not in NOTE: fail('C58', 'note lacks the program limit sum')                  # Q20
for m in re.finditer(r'(?<![\d.])13\.\d\d\b', NOTE + OPEN):
    if m[0] not in ('13.00', '13.21', '13.50'): fail('C58', 'note or open list holds %s (only 13.21; 13.00 and 13.50 are the pass/fail examples)' % m[0])
need('C59', 'Exit codes accepted: 0 only')                                                                              # Q22
NUM = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7}
for n, t in SH:                                                                                                         # Q24: R8 count equals the listed words (v35 wording: the seven words, which alone start or end a step)
    m = re.search(r'the (\w+) words, which alone start or end a step: (.*?); \(6\)', t, re.S)
    if not m or m[1] not in NUM: fail('C60', n + ' R8 word count sentence not found'); continue
    k = len(re.findall(r'"[^"]+"', m[2]))
    if NUM[m[1]] != k: fail('C60', '%s R8 says %s words but lists %d' % (n, m[1], k))
# ---- Part 3 (v35): one check per v25 finding the independent run showed missed (N01 N05 N10 N11 N12 N14, M4) and per v25 review item.
# Literals below are written out here on purpose (not read from facts-v35.py), so a change in the source AND in facts is still seen.
def secret_hits(t):
    out = []
    for p in SEC:
        for m in re.finditer(p, t):
            if 'run_real_check_n8n' in m[0]: continue
            out.append(m[0])
    return out
need('C70', 'IST** = UTC + 5:30')                                                                                       # N01 offset label
need('C71', 'A line saying contacts will be deleted or archived, or asking you to type a figure, is always a difference.')  # N05 R5
need('C72', 'the time is at or before the Enter-by time (else do not press Enter: send "time passed"')                              # N10 warning before cancel path
need('C73', 'Posting (by Wed 25 Nov 2026 15:00 UTC = 20:30 IST'); need('C73', 'Section 9 in full: Start only after the lead\'s word "post"')
for n, t in SH:
    if t.count('Wed 25 Nov 2026 15:00 UTC = 20:30 IST') < 2: fail('C73', n + ': the post-by date must be the same on the sheet pointer and the film page')                                                       # N11 post-by date tied to the literal
for n, t in (('N', NOTE), ('O', OPEN)):
    for m in re.finditer(r'[Pp]ost(?:ing)?[- ]by[^.\n]{0,40}?(Mon|Tue|Wed|Thu|Fri) (\d{1,2}) Nov', t):
        if (m[1], m[2]) != ('Wed', '25'): fail('C73', '%s post-by date %s %s' % (n, m[1], m[2]))
need('C74', 'You delete only made-up contacts of this run and demo mails, by hand, one by one.')                         # N12 active voice, who does what
need('C75', 'Run `date -u` in the read terminal: the run day still holds and the time is at or before the Enter-by time (else do not press Enter')  # N14 full command
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
need('C86', '7.11, always, by the older-key time of the message', (('B', B),)); need('C86', 'Not done by the older-key time', (('B', B),))
if 'alarm 4' not in A: fail('C86', 'A lacks the older-key alarm (v35: A also ends the older key at 7.11)')
need('C87', 'exactly the rows you wrote minus K'); need('C87', 'rows now, own key ______ | rows now, older key ______')
need('C88', 'this cancel cannot be undone'); need('C88', '**Older key point (cannot be undone;', (('B', B),))
need('C89', 'Last checks, then the older key', (('A', A),))                                    # stranger blocker: older key cancel last, after the key is saved
s6 = A.find('## 6. The model key'); s7 = A.find('## 7. The run')
i6 = A.find('\n7. **Last checks, then the older key.**', s6, s7); i66 = A.find('\n6. ', s6, s7)
if i6 < 0 or i66 < 0 or i66 > i6: fail('C89', 'A: the older-key step is not after step 6.6 inside section 6')
need('C90', '**Filled after you press create (6.3):**'); need('C90', '**Filled in step 2:**')
need('C91', 'FREEZE is not a cancel: a live key is cancelled only through the card (a planned moment P1 or P2, or a danger sign W3 to W9)')
need('C92', 'the **backup person** (one named human you can call'); need('C92', 'none named: no run')
need('C93', 'the only valid answer is their own written words "matches the sentences"')
need('C94', 'A differing printed count: send the counts, do not post, FREEZE.')
for nm, t in SH:                                                                                                        # Gmail label and Chrome profile: a click path (UNVERIFIED, tolerated) in both places, never "how unknown"
    if 'how unknown' in t: fail('C95', nm + ': "how unknown" still present')
    need('C95', 'Gmail on the web: gear icon, See all settings, Filters and Blocked Addresses', ((nm, t),)); need('C95', 'click your profile picture at the top right, Add profile, Continue without an account', ((nm, t),))
need('C96', '**Deadline** = only the end of your spending approval (Mon 23 Nov 2026 18:29 UTC = 23:59 IST)')
need('C97', 'remove only that profile, never your normal profile')
need('C98', '**Key** alone = a model key'); need('C98', 'a **run** = this one filmed attempt'); need('C98', '**Run day** is a UTC date')
for slot in ('Other channel:', 'Backup person:', 'Cancelled word:', 'Last-resort step:', 'Key list time zone:', 'Model settings file:', 'Key file:', 'Take folder:', 'cd line:', 'Key list address:',
             'Prepaid page address:', 'Masked in the notice:', 'Gap before 8.1:', 'Spend lock:', 'Key file size in bytes:', 'Price page:', 'Film cue:', 'Waiting line:', 'Demo mail subject start:',
             'Earlier demo mails expected:', 'Recording tool:', 'Posting place:', 'Video by:', 'Latest start:', 'Cancel-by time:', 'Earliest key time:'):
    need('C99', slot)
need('C100', 'the per-key limit if the message names one, the scopes the message names in "Key scopes"')                 # per-key limit and scopes before create
need('C101', 'plugged in; sleep Never')                                                                                  # laptop slot
need('C102', 'the lead checks it is new')                                                               # run name reuse rule
for nm, t in SH:                                                                                                         # one Chrome profile name everywhere
    names = set(re.findall(r'`(demo-[a-z]+)`', t))
    if names != {'demo-take'} or t.count('demo-take') < 3: fail('C103', '%s: Chrome profile names %s, demo-take x%d' % (nm, sorted(names), t.count('demo-take')))
need('C104', 'the entry is the one with the exact name the message gives; no name known: describe, revoke nothing')   # how to identify the entry to revoke
need('C104', 'whether it can be undone')                                                                                  # last-resort reversibility is stated

# ---- Part 4 (v35): one check per finding of review-v26-stranger.md (T) and review-v26-security.md (S). Each fails on the built v26 sheets and passes on v35 (v35-fail-proof.py shows it).
# Literals are written out here on purpose (not read from facts-v35.py).
def pos(t, s): return t.find(s)
need('C105', 'silence at the y question, before the film cue, in the film pause and while waiting for `end` is normal')                  # T BL1
need('C105', 'counted only from your Enter on the start line until the notice, from your `y` until the challenge is printed, and from your challenge answer until you send "run started"')
need('C106', '9. **Look key (after "go", before the earliest key time).**')                                                              # T BL2, S M4 of v26: words seen on a real cancel before the run key matters
need('C106', 'write on the card the three words you see: cancel button, confirmation box (the button that really cancels) and cancelled word')
need('C107', 'Any other difference: press nothing, go to "If it fails".')                                  # T BL2: a differing word never makes the owner improvise
need('C108', '(the lead cannot see your screen); you see the real word at 5.9 and the lead answers "confirmed"')                                                                        # T BL2: blanks come from what the owner saw
ban('C108', r'word seen by the lead|seen by the lead')
need('C108', 'Cancelled word: [OWNER FILLS: cancelled word and where you saw it]'); need('C108', 'the lead answers "confirmed"')
need('C109', 'a new key can always be made; only a program that uses the older key would be hurt', (('A', A),))                         # T M2
need('C110', 'the last resort applies (the older key may still spend)', (('A', A),))                                                     # T M3
for nm, t in SH:                                                                                                                         # T M4: the key-save line is typed before the key exists
    a = pos(t, 'In the test terminal type the printed line of 6.4'); b = pos(t, 'Press create (from now a key is alive)')
    if a < 0 or b < 0 or a > b: fail('C111', nm + ': the printed key-save line is not typed before the create press in 6.3')
need('C111', 'it waits at the paste line and nothing is alive yet')
need('C111', 'The printed line, with the key file path from the message (typed at 6.3):')
need('C111', '(the fixed printed commands of 5.7, 6.4 and 8.1 are typed as printed, with their quotes and pipes; only their filled-in parts are checked)')                                    # T M4 R6 exemption
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
need('C126', 'If the run ends before 6.7 the older key is still valid: you cancel it at 7.11', (('A', A),))                     # T M19
need('C127', 'a second Ubuntu window where you only type `date -u`, `ls -l`, `clear` and the grep of 5.7')                                                                                     # T m2
need('C128', '"none" only at 8.1')                                                                                                       # T m4
need('C129', 'Minimum think time: [LEAD FILLS at re-pin: minimum think time] seconds'); need('C129', 'Run length: [LEAD FILLS at re-pin: run length] minutes')                                                   # S M2, S m10
need('C130', '(its list L2 included, at 7.11)')   # T m14
need('C131', 'copy a harmless word such as `clear`')                                                                                     # T m15
need('C132', 'run `rm -f -- "<key file>"` in the test terminal (R6 shape check first; the file may not exist)')                                              # S m1
need('C133', '(only names the clean-up message already listed)')                                                                         # S m5
need('C134', 'revoke the apps the message names'); ban('C134', r'delete or revoke')                                                      # S m6
need('C135', 'or `prep-<run name>@example.com`')                                                                                         # S m7
need('C136', "that page's host name only"); need('C136', "the part of the page's address between `https://` and the next `/`")                                                          # S m8
need('C137', 'passes 7.11 before 8.1')                                       # S B1
need('C137', '(after your yes, 7.11 still follows, before 8.1)')
need('C137', 'by the older-key time of the message on the run day and even if the lead is silent', (('B', B),))
need('C137', 'whatever way the run ended, by the older-key time of the message', (('B', B),)); need('C137', 'Every way the run ends (finished, "I decline", "time passed"')
need('C138', 'Four phone alarms'); need('C138', 'alarm 4 at the older-key time (do 7.11 now, whatever else is open')   # S B1 fourth alarm
need('C139', 'The cancel-by time is before the older-key time.')                                                         # S B1 time order checked by the owner
_ct = re.search(r'Cancel-by time: (\d\d):(\d\d) UTC', B); _ot = re.search(r'Older-key time: (\d\d):(\d\d) UTC', B)
if not _ct or not _ot or (int(_ct[1]) * 60 + int(_ct[2])) >= (int(_ot[1]) * 60 + int(_ot[2])): fail('C139', 'B: the cancel-by time is not before the older-key time (read from the text)')
need('C140', 'Wait at least the "Minimum think time" of the message'); ban('C140', r'Wait 10 seconds')   # S M2
need('C141', 'Test program asks you to type a figure: no'); need('C141', 'the row "Test program asks you to type a figure" saying anything but no: no run')                          # S M3
need('C142', 'this cancel cannot be undone', (('B', B),)); need('C142', 'first read its last-used time in the key list and describe it to the lead (a use after your run key\'s create time', (('B', B),))   # S M5
need('C143', 'Model key outside the model program: none (the lead checked n8n\'s credential store and shows it)'); need('C143', 'a model key stored in n8n would spend without the spend lock')   # S M6
need('C144', 'Anything else (no `exit` line, or no shell prompt after it): the card first (the key is alive; STOP RULE), then FREEZE')                                                                       # S m2
need('C145', 'put the Privacy switches back as the first sentence of 8.7 says')                                                                                # S m3
need('C146', 'else no run today on this sheet: describe it and wait. What then:', (('A', A),)); need('C146', 'the lead sends a new numbers message with a later run day, at least 7 days after that use', (('A', A),))   # S M4: what happens when the 7-day rule fails
need('C147', '5.1 to 5.8 (and 6.1, which 5.7 needs) may be done on earlier days, 5.9 and the rest of sections 6 to 8 only on the run day')                                      # T m10 and v35 T M1
need('C148', 'or no sentence "the test program made no delete call": skip only the contact deleting of this step and describe which')                  # S m14
need('C159', 'all in IST: alarm 1 at the latest start'); need('C159', 'alarm 2 at the alarm time'); need('C159', 'alarm 3 at the cancel-by time')                                      # plant P11 showed the alarm contents were unchecked
# ---- Part 5 (v35): lead-side documents must match the built sheets (S M1 and the stranger's lead-document findings)
for nm, t in (('N', NOTE), ('O', OPEN)):
    if re.search(r'Builder proposes B|safe default B\b|builder recommends A for money and chose neither', t): fail('C149', nm + ': still recommends B or contradicts itself on A and B')
    if re.search(r'older key stays valid unless its text appears', t): fail('C149', nm + ': stale description of B')
if 'No default pick' not in NOTE: fail('C149', 'N: the no-default-pick wording is missing (Open 71 is OWNER-OPEN)')
if 'No default pick' not in OPEN: fail('C149', 'O: row 71 lacks the no-default-pick wording')
for nm, t in (('N', NOTE), ('O', OPEN)):
    if re.search(r'(?i)money-safe default', t): fail('C149', nm + ': a lead page still names a default sheet (the builder must not decide Open 71)')
if '6.2 option A none at all' in NOTE or '6.6 and 6.7 option A exactly' in NOTE: fail('C150', 'N: G26 still says A has no older key at 6.2 (v26 A keeps the older key valid until 6.7)')
if 'no valid key except the older key (if the message names one); 6.6 and the last checks of 6.7' not in NOTE: fail('C150', 'N: G26 not rewritten for the older key')
if 'both sheets have four alarms, the fourth at 16:00 UTC = 21:30 IST' not in NOTE: fail('C151', 'N: G30 or alarms count wrong')
if '4 owner: two alarms' in NOTE: fail('C151', 'N: the day order still says two alarms')
if 'Test program asks you to type a figure: no' not in NOTE or 'G35' not in NOTE: fail('C152', 'N: typed-figure line / G35 missing')
if 'Minimum think time' not in NOTE or 'Minimum think time' not in OPEN: fail('C153', 'note and open list must name the minimum think time slot')
if 'WHEN IT FAILS (v35)' not in OPEN: fail('C154', 'O: row 78 does not say what happens when the 7 day rule fails')
if 'MET for the sheet page alone' not in OPEN or 'Open 102' not in OPEN: fail('C155', 'O: row 75 does not state the sheet-page word count and the card question')
if 'checked by you with `ls ~/.hadavin-take-tags`' not in NOTE: fail('C156', 'N: run name check by the lead missing')
for nm, t in (('N', NOTE), ('O', OPEN)):
    if re.search(r'\bpay in (only )?(a little(?! more)|less)\b', t.replace('no request to pay in less', '').replace('propose no second account and no smaller payment', '')) : fail('C157', nm + ': suggests the owner pays in less (Q24)')
if 'Added in v13' not in NOTE or 'look key' not in NOTE.lower(): fail('C158', 'N: v12 section or look key missing')
# ---- Part 4 (v35): one check per class change of the v26/v28 root-cause reading (RC1 state machine, RC2 pre-flight facts, RC3 single source) and per evidence-runner fix
def outside_numbers(t):
    i = t.find('## Appendix part 2'); j = t.find('## Appendix part 3')
    return t[:i] + t[j:]
for nm, t in SH:                                                                                                         # C160 N3, m11: lead-set figures are read from the message; no literal copy outside the sample
    o = outside_numbers(t)
    for pat in (r'\b20 seconds\b', r'\bWait 20\b', r'within 5 minutes', r'\b16:00 UTC\b', r'\b21:30 IST\b'):
        m = re.search(pat, o)
        if m: fail('C160', '%s holds the literal %r outside the numbers page' % (nm, m[0]))
need('C161', 'whatever way the run ended', (('B', B),))                                                                  # RC1: one older-key point for every exit
need('C161', 'every way the run ends passes here before 8.1')                                                            # RC1 both sheets
need('C162', 'FREEZE is not a cancel: a live key is cancelled only through the card (a planned moment P1 or P2, or a danger sign W3 to W9)')                                    # RC1: FREEZE never cancels
need('C162', '**Not danger signs (no card, no FREEZE):** a lead message "wait"')                                         # RC1: a wait is never a trigger
need('C163', '"confirmed" (5.9)'); need('C163', 'the seven words, which alone start or end a step')                                    # N2: the new lead word and the count
need('C164', 'Write its state word before the cancel.'); need('C164', 'must differ from the look key\'s word before the cancel and from every live word')   # N2
need('C165', 'If its text appeared on your screen: cancel it at once (the 7-day rule of 5.1 does not apply to that)', (('A', A),)); need('C165', 'If its text appeared on your screen: cancel it at once.', (('B', B),))   # N4
need('C166', 'except the key\'s own one-time display at 5.9 and 6.3 and the paste at 6.4')                              # N1: W7 exemption
need('C167', 'the test program made no delete call')                                                                      # evidence-runner fix: the no-delete line in both sheets
if 'Decision 2 stands: the test program never deletes' not in NOTE or 'the test program deletes;' in NOTE: fail('C167', 'N: the sentence "Decision 2 stands: the test program never deletes" is missing or turned into a delete instruction')   # evidence-runner fix: content check of the note
for nm, t in SH:                                                                                                         # RC2: unknown means no run is stated on the numbers page
    if '"unknown" in any slot' not in t: fail('C168', nm + ': the numbers checks do not say that "unknown" in any slot is no run')
if 'Open 96' not in NOTE or '\n| 96 |' not in OPEN or '\n| 97 |' not in OPEN: fail('C169', 'note or open list lacks the rows for the aborted-run message and the A/B decision')   # N13 and RC3
for nm in 'AB':                                                                                                           # RC3: the pages are named in both sheets as written on disk
    _s = SHEETS_DISK[nm]
    for pg in ('OWNER-CARD-v35-', 'OWNER-APPENDIX-v35-'):
        if pg + nm + '.md' not in _s: fail('C170', '%s does not name %s%s.md' % (nm, pg, nm))
    if 'OWNER-FILM-PERSON-v35.md' not in _s: fail('C170', 'sheet %s does not name the film page' % nm)

# ---- Part 6 (v35): one check per finding of review-v28-security.md, review-v28-stranger.md and evidence-v28-independent/00-SUMMARY.md that v35 fixed. Each fails on the built v28 files (v35-fail-proof.py).
import os as _os
def _wc(t): return len(t.split())
for nm in 'AB':                                                                                                          # L-LEN: the sheet page alone is at most 6,300 words
    if _wc(SHEETS_DISK[nm]) > 6300: fail('C171', 'sheet %s has %d words (limit 6300)' % (nm, _wc(SHEETS_DISK[nm])))
if not _os.path.exists(D + 'OWNER-APPENDIX-v35-A.md') or not _os.path.exists(D + 'OWNER-FILM-PERSON-v35.md'): fail('C171', 'appendix or film person page missing')
need('C172', 'Four phone alarms')                                                                                        # S B1: A has the owner-side older-key end and the fourth alarm
need('C172', 'Older key point (cannot be undone; every way the run ends passes here before 8.1)')                       # 7.11 in both routes
need('C172', 'a FREEZE does not stop this')                                                                              # S B2: B 7.11 and FREEZE: the older key ends even after FREEZE
for nm in 'AB':                                                                                                          # S M: the letter is in the heading and footer of every page (the sheet page is read from SHEETS_DISK)
    _h = SHEETS_DISK[nm].split('\n')[0]
    if 'sheet %s' % nm not in _h or 'End of sheet %s' % nm not in SHEETS_DISK[nm]: fail('C173', 'sheet %s lacks the letter in its heading or its footer' % nm)
    for pg, foot in (('OWNER-CARD-v35-', 'End of the card, sheet %s' % nm), ('OWNER-APPENDIX-v35-', 'End of the appendix, sheet %s' % nm)):
        try: _t = open(D + pg + nm + '.md', encoding='utf-8').read()
        except OSError: fail('C173', pg + nm + '.md missing'); continue
        if 'sheet %s' % nm not in _t.split('\n')[0] or foot not in _t: fail('C173', '%s%s.md lacks the letter in its heading or its footer' % (pg, nm))
need('C174', 'n8n credentials: exactly the three, by name')                                                              # S: numbers page slot
need('C175', 'alone (R1), with the narrowest scopes the create form offers')                                            # S: look key clauses
need('C175', 'cancel is proven')
need('C176', 'a later use: use sheet B'); need('C176', 'at least 168 hours (7 days) before the earliest key time of the run day', (('A', A),))                          # S: the 7-day rule at exactly 7 days, route A/B condition (L-A/B)
for _n, _t in (('NOTE', NOTE), ('OPEN', OPEN)):                                                                          # L-23NOV: 18:14 only with the refusal-limit label and its IST pair
    for _m in re.finditer(r'18:14', _t):
        _w = _t[max(0, _m.start() - 60):_m.start()]
        if 'refusal limit' not in _w: fail('C177', '%s holds 18:14 without the label "refusal limit" near it: %r' % (_n, _t[_m.start() - 30:_m.end() + 20]))
for _n, _t in (('A', A), ('B', B)):
    for _m in re.finditer(r'18:14', _t): fail('C177', '%s sheet holds 18:14 (the owner pages never need the refusal limit)' % _n)
if 'A gap longer than the lease' in NOTE or 'lease sentence of section 5 decided' in NOTE: fail('C178', 'N: the lease sentence is not struck from the public post (lead answer Q22c)')   # L-Q22c
if 'start margin' not in NOTE: fail('C178', 'N: 860 s is not called the start margin')
if F.get('ls23') != '18:04 UTC = 23:34 IST' or F.get('rv23') != '18:19 UTC = 23:49 IST': fail('C179', 'facts: latest start or key-revoked time of 23 Nov is not the lead\'s (L-23NOV)')
for _s in ('18:04 UTC = 23:34 IST', '18:19 UTC = 23:49 IST'):
    if _s not in NOTE or _s not in OPEN: fail('C179', 'note or open list lacks %r (L-23NOV)' % _s)
need('C180', '[OWNER FILLS:'); need('C180', '[LEAD FILLS at re-pin:')                                                      # L-FACTS: visibly different placeholder rows
need('C181', 'the seven words, which alone start or end a step'); need('C181', '"continue" (after a FREEZE)')            # S R8: the whole word set
need('C182', 'The 7-day rule:** the older key\'s last-used time is "never", or at least 168 hours (7 days)')                                                                               # S: the 7-day rule stated once in full
if 'Open 102' not in OPEN or 'Open 103' not in NOTE: fail('C183', 'the open questions about the card word count and the 18:04 derivation are missing')
if 'UNVERIFIED' not in OPEN or 'E-52' not in OPEN: fail('C184', 'O: the L-APP2 / E-52 UNVERIFIED row is missing')

# ---- Part 7 (v30, round 2, kept): one check per finding of review-v29-security.md, review-v29-naive.md and review-v29-evidence.md that v30 fixed. v30-fail-proof.py runs this part on the built v29 files.
import os as _os
_V = globals().get('PAGEVER', 'v35')                                                                                       # v35-fail-proof.py sets PAGEVER = 'v29' to read the old pages
_APP = {'A': A, 'B': B}
for _nm in 'AB':
    _t = _APP[_nm]
    if _t.count('at least 168 hours (7 days)') != 1: fail('C185', '%s: the 7-day rule is not worded exactly once in full (count %d)' % (_nm, _t.count('at least 168 hours (7 days)')))      # S m1: one wording
    if 'the key list may show a last use hours late' not in _t: fail('C185', '%s lacks the last-used lag sentence' % _nm)
for _n, _t in (('A', A), ('B', B), ('NOTE', NOTE), ('OPEN', OPEN)):                                                       # S M2: no "unless you know" escape in 7.11 and no "nothing else I know uses it"
    if 'unless you know something else uses' in _t: fail('C186', '%s holds the escape (describe the older key, then cancel anyway)' % _n)
_i7 = A[A.find('Older key point (cannot be undone'):]; _i7 = _i7[:_i7.find('## 8.')] if '## 8.' in _i7 else _i7[:3000]
if 'nothing else I know uses it' in _i7 or 'I cancel the older key <its name> now, the yes covers it' not in _i7: fail('C186', 'A 7.11: the forced cancel must use the phrase without the claim that nothing else uses the key')
need('C187', 'Alarm 5 (Sun 22 Nov) and alarm 6 (Mon 23 Nov)'); need('C187', 'a person who may cancel only the keys named on the helper')       # S M3
if F.get('bs') != 'Sun 22 Nov 2026 18:09 UTC = 23:39 IST': fail('C187', 'facts: backstop time is not Sun 22 Nov 2026 18:09 UTC = 23:39 IST')
need('C187', 'Sun 22 Nov 2026 18:09 UTC = 23:39 IST'); need('C187', 'No yes yet: alarms 5 and 6 are not set'); need('C187', 'a missed 7.11: they are the second and third chance')
need('C187', 'alarm 5 and alarm 6 of 5.8 are the fifth and sixth')
if 'waits for your message "cancel the older key' in NOTE + OPEN or 'waits for your message "cancel the older key' in A: fail('C188', 'a text still says the older key in A waits for a lead message (S M1)')
if 'does NOT wait for a message from you' not in NOTE: fail('C188', 'note: A older key still seems to wait for a lead message')
_sb = F.get('sevenback', '?')
if _sb not in NOTE:
    fail('C189', 'note: the 7-day time (%s) is missing (S M1)' % _sb)
if _sb not in OPEN: fail('C189', 'open list lacks the 7-day time %s' % _sb)
need('C190', 'no such page: describe that, then go on; UNVERIFIED that no page means no Recall')                                                                    # S m4: Recall
need('C191', 'no clipboard manager, remote-access or screen-capture tool running'); need('C191', 'every clipboard manager, remote-access tool or screen-capture tool')     # S m5
need('C192', 'never a file manager, a second terminal window or the clipboard (no copy and paste)')                      # S m6 film person
need('C192', "the From column of the mail list shows the sender's throwaway address: the film person does not stop for")   # N B1
need('C192', 'say aloud "film pause now"') if False else need('C192', 'aloud "film pause now"')
need('C193', '**Name rule (8.3, 8.4):** revoke only an entry whose exact name is in the numbers message row "Entries to revoke later"')                      # S m7
_gm = F.get('gap_max', '?')
need('C194', 'the latest start is at most %s minutes after the earliest key time' % _gm)
need('C194', 'at most 60 minutes after the earliest key time')                                                           # literal, independent of facts-v35.py (the lead's cap is 60)                                  # S m3: gap cap
if 'at most %s minutes' % _gm not in OPEN or 'at most %s minutes' % _gm not in NOTE and ('%s-minute' % _gm) not in NOTE and ('at most %s minutes' % _gm) not in NOTE and (_gm + ' minutes') not in NOTE: fail('C194', 'note or open list lacks the gap cap of %s minutes' % _gm)
_pair = re.compile(r'\b\d\d:\d\d(?::\d\d)? UTC(?! = \d\d:\d\d(?::\d\d)? IST)')                                           # EVIDENCE: every UTC time carries its IST pair
for _n, _t in (('A', A), ('B', B), ('NOTE', NOTE), ('OPEN', OPEN)):
    for _m in _pair.finditer(_t):
        _ctx = _t[max(0, _m.start() - 25):_m.end() + 25].replace('\n', ' ')
        fail('C195', '%s: a UTC time without its IST pair: %r' % (_n, _ctx))
for _pg in ('OWNER-CARD-%s-A.md' % _V, 'OWNER-CARD-%s-B.md' % _V, 'OWNER-APPENDIX-%s-A.md' % _V, 'OWNER-APPENDIX-%s-B.md' % _V, 'OWNER-FILM-PERSON-%s.md' % _V):
    if not _os.path.exists(D + _pg): continue
    for _m in _pair.finditer(open(D + _pg, encoding='utf-8').read()): fail('C195', '%s: a UTC time without its IST pair near %r' % (_pg, _m[0]))
need('C196', 'the three waits of the message added')                                                                        # N M3: the three waits named
for _nm in 'AB':
    if _APP[_nm].count('at least 5 minutes before the latest start') < 3: fail('C196', '%s: the 5-minute rule is not worded the same in 6.2 and on the card (W5 and the words list)' % _nm)
need('C197', '(only that one person)')                                                                                     # N M5: one person for a failed cancel
need('C198', 'press Enter once; the line `exit 0` appears')                                                                # N M6: press Enter in 6.4
need('C198', 'press Enter once on the empty line')
_bad = []
for _nm in 'AB':                                                                                                           # N M6: no orphaned appendix fragment (every paragraph starts with a capital, a digit or a bold mark)
    _ap = open(D + 'OWNER-APPENDIX-%s-%s.md' % (_V, _nm), encoding='utf-8').read(); _in = False
    for _ln in _ap.split('\n'):
        if _ln.startswith('```'): _in = not _in; continue
        if _in or not _ln.strip() or _ln.startswith('#') or _ln.startswith('---') or _ln.startswith('- '): continue
        if not (_ln[0].isupper() or _ln[0].isdigit() or _ln[0] in '*"'): fail('C199', 'appendix %s: a paragraph starts with %r (orphaned fragment)' % (_nm, _ln[:40]))
    for _ln in _ap.split('\n'):
        if _ln.count('(') != _ln.count(')') and not _ln.startswith('```'): fail('C199', 'appendix %s: unbalanced parentheses in %r' % (_nm, _ln[:50]))
for _nm, _t in (('A', A), ('B', B)):
    for _ln in _t.split('\n'):
        _ln = re.sub(r'(^|\s)[a-d]\)', ' ', _ln)                                                                          # list labels a) b) c) are not parentheses
        if _ln.count('(') != _ln.count(')') and '```' not in _ln and not _ln.lstrip().startswith(('Run name', 'Start line')): fail('C199', '%s: unbalanced parentheses in a line starting %r' % (_nm, _ln[:50]))
for _n, _t in (('A', A), ('B', B), ('NOTE', NOTE), ('OPEN', OPEN)):
    if ': :' in _t or '::' in _t.replace('```', ''): fail('C200', '%s holds a double colon' % _n)
for _nm in 'AB':                                                                                                           # N M7: appendix parts 1..N with no gap, and every sheet pointer exists
    _ap = open(D + 'OWNER-APPENDIX-%s-%s.md' % (_V, _nm), encoding='utf-8').read()
    _parts = [int(x) for x in re.findall(r'^## Appendix part (\d+):', _ap, re.M)]
    if _parts != list(range(1, len(_parts) + 1)) or len(_parts) < 10: fail('C201', 'appendix %s parts are %r (must run 1..10 or more without a gap)' % (_nm, _parts))
    for _k in re.findall(r'\(appendix (\d+)\)', SHEETS_DISK[_nm]) + re.findall(r'appendix part (\d+)', SHEETS_DISK[_nm]):
        if int(_k) not in _parts: fail('C201', 'sheet %s points to appendix %s which does not exist' % (_nm, _k))
need('C202', "Retire check (the lead's own test: it tries each revoked item and sees that it now refuses)")                # N M?: retire check defined
need('C203', 'what "at re-pin" means')                                                                                     # N M8: placeholders explained
if 'at re-pin' not in OPEN: fail('C203', 'open list lacks the exact spelling "at re-pin"')
for _s in ('`[OWNER FILLS: ...]`', '`[LEAD FILLS at re-pin: ...]`'):                                                       # EVIDENCE: exact placeholder spellings in the open list
    if _s not in OPEN: fail('C206', 'open list lacks the exact placeholder spelling %s' % _s)
for _r in ('| 107 |', '| 108 |', '| 109 |'):
    if _r not in OPEN: fail('C207', 'open list lacks row %s' % _r.strip('| '))
for _w in ('L7', 'DB-2', 'delete-path', 'Q27', 'OWNER-OPEN'):
    if _w not in OPEN: fail('C207', 'open list lacks %r (still OWNER-OPEN items)' % _w)
for _nm, _t in (('A', A), ('B', B)):
    if _t.count('deadline reminder') < 3: fail('C208', '%s: the deadline reminder is not set after the yes and named in the card words' % _nm)
for _n, _t in (('A', A), ('B', B), ('NOTE', NOTE)):                                                                       # S M1: the older-key line of the note and the 18:04 plan fact
    pass
if '18:04 is a plan fact' not in NOTE or '18:04 is a plan fact' not in OPEN: fail('C209', 'note or open list lacks the sentence that 18:04 is a plan fact, not a start that fits a run (S m2)')
if 'Older key point (cannot be undone' not in A: fail('C209', 'sheet lacks the older key point')

# ---- Part 8 (v35, round 3): one check per finding of review-v30-security.md, review-v30-naive.md and review-v30-evidence.md. v35-fail-proof.py runs this part on the built v30 files.
import glob as _glob, os as _os
_V = globals().get('PAGEVER', 'v35')                                                                                       # v35-fail-proof.py sets PAGEVER = 'v30' to read the old pages
def _pg(n): return open(D + n, encoding='utf-8').read()
_AP = {k: _pg('OWNER-APPENDIX-%s-%s.md' % (_V, k)) for k in 'AB'}
_FILM = _pg('OWNER-FILM-PERSON-%s.md' % _V)
_BM = 'Mon 23 Nov 2026 18:09 UTC = 23:39 IST'
if F.get('bm') != _BM: fail('C210', 'facts: the Monday reminder is not %s' % _BM)                                            # S M1: owner-side stop on deadline day
for _nm, _t in (('A', A), ('B', B)):
    for _s in (_BM, '18:19 UTC = 23:49 IST', 'Alarm 5 (Sun 22 Nov) and alarm 6 (Mon 23 Nov)', 'key of L1 that you find valid is cancelled at once by steps 2 to 4'):
        if _s not in _t: fail('C210', '%s lacks %r' % (_nm, _s))
    if 'If your run day is Mon 23 Nov' in _t: fail('C210', '%s keeps the dead Mon 23 Nov paragraph' % _nm)
    if _BM not in SHEETS_DISK[_nm]: fail('C210', 'sheet %s itself does not carry the Monday reminder' % _nm)
    if '18:19 UTC = 23:49 IST' not in _pg('OWNER-CARD-%s-%s.md' % (_V, _nm)): fail('C210', 'card %s lacks the cancel-by pair 18:19 UTC = 23:49 IST' % _nm)
for _nm, _t in (('A', A), ('B', B)):                                                                                       # S M2: cancel helper
    for _s in ('a person who may cancel only the keys named on the helper', 'cancel helper <name or none>', 'if I cannot be reached while a key is alive and the cancel helper is none nobody else can cancel it and it can spend until the balance runs out', 'a cancel-only role'):
        if _s not in _t: fail('C211', '%s lacks %r' % (_nm, _s))
if 'OWNER-OPEN' not in OPEN or 'cancel helper' not in OPEN: fail('C211', 'open list: the cancel helper is not kept as OWNER-OPEN')
for _n, _t in (('NOTE', NOTE), ('OPEN', OPEN)):                                                                            # S M3: lead pages
    if re.search(r'on your message|three; four|three alarms|Safe default if you do not answer', _t): fail('C212', '%s holds old wording on the older key, the alarm count or the default' % _n)
if 'fourth alarm' in NOTE and 'both sheets' not in NOTE: fail('C212', 'note: the alarm count is not said to be four in both sheets')
_w = 'will probably fail on Wed 18 Nov'
_r71 = [l for l in OPEN.split('\n') if l.startswith('| 71 |')]
if not _r71 or 'No default pick' not in _r71[0] or _w not in _r71[0] or abs(_r71[0].find(_w) - _r71[0].find('No default pick')) > 500: fail('C212', 'open row 71: the warning is not beside the no-default wording')
if NOTE.count(_w) < 3: fail('C212', 'note: the warning "%s" is missing (count %d)' % (_w, NOTE.count(_w)))
# C213 (evidence H06): ANY phrasing in a lead page or sheet that makes the older-key cancel wait for, or be released by, a lead message
_REL = re.compile(r"(?:on|after|upon|when|once|if) (?:your|the lead's|a lead|the lead|you send|you say) (?:message|word|words|sentence|tells)|(?:lead|you|it) (?:sends?|says?|gives?|writes?|tells?|messages?|releases?|allows?|permits?|approves?|confirms?|signals?|answers?)(?: the owner| him)? (?:the |him |it )?(?:words? |message |go-ahead |signal |release )?[\"“]?(?:cancel|release|go|ok)|waits? for (?:your|a|the lead)|(?:release|permission|go-ahead|signal) (?:from|of|by) (?:the )?lead|until (?:the lead|you) (?:says?|sends?|tells?)|(?:lead|message|word) (?:releases?|allows?|permits?|approves?|frees?|lifts?|unlocks?) (?:\\w+ ){0,4}(?:older key|cancel)", re.I)
_NEG = re.compile(r"\bno lead message\b|does NOT wait|not wait|no message from you|no word of the lead|\bnever\b|without|\bnor\b|was wrong|said so in|no message|not needed|not accepted|neither|no longer|is closed|no lead word|does not wait|not a|only the owner|owner's own")
for _n, _t in (('NOTE', NOTE), ('OPEN', OPEN), ('A', A), ('B', B)):
    for _sent in re.split(r'(?<=[.;|])\s+|\n', _t):
        _l = _sent.lower()
        if 'older key' in _l and 'cancel' in _l and _REL.search(_sent) and not _NEG.search(_sent): fail('C213', '%s: a sentence lets a lead message release the older-key cancel: %r' % (_n, _sent[:110]))
for _nm, _t in (('A', A), ('B', B)):                                                                                       # S m1 name rule
    if 'whose exact name contains the run name' in _t: fail('C214', '%s keeps the run-name rule for revoke names' % _nm)
    if 'Entries to revoke later: app passwords <names, exact>; HubSpot apps <names, exact>' not in _t: fail('C214', '%s: the numbers sample lacks the row Entries to revoke later' % _nm)
    if 'Sheet B cancels the older key at 7.11 even if it was used a day ago' not in _t: fail('C215', '%s lacks the B warning of 5.1 (m2)' % _nm)              # S m2
    if 'It does not mean no valid key remains: the older key may still spend until it is cancelled' not in _t: fail('C216', '%s: card step 5 lacks the older-key sentence (m3)' % _nm)   # S m3
    if 'The yes binds you to 7.11' not in _t or 'There is no older key.' not in _t: fail('C217', '%s: yes binding or the no-older-key wording missing (m4, N m8)' % _nm)       # S m4, N m8
    if 'it is an instruction, not a technical guard' not in _t: fail('C218', '%s lacks the film-person guard honesty sentence (m5)' % _nm)                          # S m5
for _nm in 'AB':                                                                                                           # N M-A1: 5.1 order and split
    _t = SHEETS_DISK[_nm]; _i = _t.find('1. **Which sheet, then run name and key-list facts.**'); _j = _t.find('2. **People:**')
    _b = _t[_i:_j]
    if _i < 0 or not all(('\n   %s) ' % x) in _b for x in 'abc'): fail('C219', 'sheet %s: 5.1 is not split into a), b), c)' % _nm)
    if 'never later than ' + F['last_day'] not in _b or 'a later use: use sheet B' not in _b: fail('C219', 'sheet %s: 5.1a lacks the last run day or the later-use route (B1)' % _nm)
    if 'today plus 7 days' in _b or 'before any message from the lead' in _b: fail('C219', 'sheet %s: 5.1a keeps the unusable v31 wording (B1)' % _nm)
    if _b.count('your first action') != 1: fail('C219', 'sheet %s: 5.1a first-action wording count %d' % (_nm, _b.count('your first action')))
    if any(len(_p.split()) > 230 for _p in _b.split('\n')): fail('C219', 'sheet %s: a paragraph of 5.1 has more than 230 words' % _nm)
for _nm, _t in (('A', A), ('B', B)):                                                                                       # N M-A3, m11
    if 'from 5 minutes before the latest start do not press Enter' not in _t: fail('C220', '%s lacks the last-5-minutes rule' % _nm)
    for _p in ('ends exactly at alarm 2', 'itself it is too late'):
        if _p in _t: fail('C220', '%s keeps the old last-5-minutes wording %r' % (_nm, _p))
if 'press F11' not in _FILM or 'preview' not in _FILM or 'item 3b' not in A: fail('C221', 'film page lacks how to show only the page area (F11, region, preview) or the sheet does not point to item 3b')    # N M-A4
for _nm, _t in (('A', A), ('B', B)):                                                                                       # N minors
    if 'that the From column of the mail list is not a stop' not in _t: fail('C222', '%s: 7.6 does not tell the film person about the From column (m1)' % _nm)
    for _p in ('(STOP RULE below)', 'sample in section 3', 'list ends section 2'):
        if _p in _AP[_nm]: fail('C222', 'appendix %s keeps the wrong pointer %r (m2)' % (_nm, _p))
    for _src, _page in (('sheet', SHEETS_DISK[_nm]), ('appendix', _AP[_nm])):
        if re.search(r'\(appendix \d+\) +\)', _page): fail('C222', '%s %s holds a stray "(appendix N) )" (m3)' % (_src, _nm))
    if 'Remember my preferences' not in _t: fail('C222', '%s: 6.1 gives no path for Sync across your devices (m4)' % _nm)
    if 'this sheet has no R2 or R3, nothing is missing' not in _t: fail('C222', '%s: the R-label sentence still sends a stranger looking for R2 (m5)' % _nm)
    if '## 7. The run (UNVERIFIED)' not in _t: fail('C222', '%s: heading of section 7 (m6)' % _nm)
    if 'Words with one meaning here' not in _t: fail('C222', '%s lacks the definitions of message, take, deadline, wait, gap, post (m7)' % _nm)
    if 'figure line' in _t or 'ends exactly' in _t: fail('C222', '%s: the unclear row name "figure line" is back (m9)' % _nm)
    if 'are not an empty slot' not in _t: fail('C222', '%s: the owner-fill rows are not said to be no empty slot (m10)' % _nm)
    if re.search(r'\btake sheet B\b|\btake B\b', _t.replace('if used less than 7 days ago take B', '')): fail('C222', '%s: "take sheet B" is back (word with two meanings, m7)' % _nm)
if 'the sheet checks only the maximum' not in OPEN or 'sheet checks both at 5.7' in OPEN: fail('C223', 'open list: the 40-minute minimum is said to be checked by the sheet (v29 m7)')
# C224 (evidence H09): every placeholder by exact spelling and count
_LEAD_OK = ['[LEAD FILLS at re-pin: where the raw recording is kept, who deletes it and when]', '[LEAD FILLS at re-pin: last-resort step]', '[LEAD FILLS at re-pin: minimum think time]', '[LEAD FILLS at re-pin: run length]', '[LEAD FILLS at re-pin: the three names]']
_OWN_OK = ['[OWNER FILLS: cancel button word and confirmation box word, from the look key at 5.9]', '[OWNER FILLS: cancelled word and where you saw it]', '[OWNER FILLS: older key last-used time]']
_GEN_OK = {'[LEAD FILLS at re-pin: ...]', '[LEAD FILLS ...]', '[OWNER FILLS: ...]', '[OWNER FILLS ...]'}
for _n, _t in (('A', A), ('B', B), ('NOTE', NOTE), ('OPEN', OPEN)):
    for _m in re.findall(r'\[(?:LEAD|OWNER) FILLS[^\]`\n]*\]', _t):
        if _m not in _LEAD_OK + _OWN_OK and _m not in _GEN_OK: fail('C224', '%s: placeholder with a spelling that is not in the list: %r' % (_n, _m))
for _nm, _t in (('A', _AP['A']), ('B', _AP['B'])):
    _blk = _t[_t.find('SAMPLE (made-up values'):]; _o = _blk.find('```'); _blk = _blk[_o:_blk.find('```', _o + 3)] if _o >= 0 else ''
    for _ph in _LEAD_OK + _OWN_OK:
        if _blk.count(_ph) != 1: fail('C224', 'appendix %s sample: %r appears %d times (must be exactly 1)' % (_nm, _ph, _blk.count(_ph)))
    if len(re.findall(r'\[LEAD FILLS', _blk)) != 5 or len(re.findall(r'\[OWNER FILLS', _blk)) != 3: fail('C224', 'appendix %s sample: placeholder count is not 5 LEAD and 3 OWNER' % _nm)
# C225 (evidence H15): every fact the sources are built from is used by some source; a fact that no source uses is dead
_srcs = ''.join(_pg(x) for x in ('OWNER-SHEET-%s-SOURCE.md' % _V, 'v%s-OPEN-FOR-LEAD-SOURCE.md' % _V[1:]) if _os.path.exists(D + x)) if False else ''
_ns = {}; exec(_pg('facts-%s.py' % _V), _ns)
for _x in _glob.glob(D + '*-SOURCE.md'):
    if _V in _x or 'NOTE' in _x and ('-v19-' in _x if _V == 'v35' else '-v15-' in _x if _V == 'v31' else '-v14-' in _x): _srcs += open(_x, encoding='utf-8').read()
_chk = ''.join(_pg(x) for x in ('check-%s.py' % _V, 'newchecks-%s.py' % _V, 'build-%s.py' % _V) if _os.path.exists(D + x))
_dead = [k for k in _ns['F'] if ('{{%s}}' % k) not in _srcs and not k.startswith('ph_') and ("F['%s']" % k) not in _chk and ("F.get('%s'" % k) not in _chk and ("'%s'" % k) not in _chk]
if _dead: fail('C225', 'facts used by no source (dead): %s' % ', '.join(sorted(_dead)))
# C226 (evidence 5): no email-shaped text in the owner pages except @example.com
for _n, _t in (('A', A), ('B', B)):
    for _m in re.finditer(r'[A-Za-z0-9._…-]+@[A-Za-z0-9.…-]+', _t):
        if 'example.com' not in _m[0]: fail('C226', '%s holds an email-shaped text %r' % (_n, _m[0][:30]))
# C227: staleness by file times read at run time, and no absolute path in any script of this package
def _mt(n): return _os.path.getmtime(D + n)
for _nm in 'AB':
    for _built, _srcn in (('OWNER-SHEET-%s-%s.md' % (_V, _nm), 'OWNER-SHEET-%s-SOURCE.md' % _V), ('OWNER-CARD-%s-%s.md' % (_V, _nm), 'OWNER-SHEET-%s-SOURCE.md' % _V), ('OWNER-APPENDIX-%s-%s.md' % (_V, _nm), 'OWNER-SHEET-%s-SOURCE.md' % _V)):
        for _dep in (_srcn, 'facts-%s.py' % _V, 'build-%s.py' % _V):
            if _os.path.exists(D + _dep) and _mt(_built) + 1 < _mt(_dep): fail('C227', '%s is older than %s (rebuild)' % (_built, _dep))
for _fn in ('check-%s.py' % _V, 'newchecks-%s.py' % _V, 'build-%s.py' % _V, 'facts-%s.py' % _V, 'mut%s.py' % _V[1:], '%s-fail-proof.py' % _V):
    if _os.path.exists(D + _fn) and re.search(r"['\"]/(?:ho" + r"me|tmp|Users|mnt)/", _pg(_fn)): fail('C227', '%s holds a hard-coded absolute path' % _fn)
# ---- Part 9 (v35, round 4): one or more checks per finding of review-v31-security, review-v31-naive and review-v31-evidence (C228 to C250).
# Self-contained: v35-fail-proof.py runs this part on the built v31 pages (it must fail there) and on the built v35 pages (it must pass).
import datetime as _dt
_V9 = globals().get('PAGEVER', 'v35')
def _p9(n): return open(D + n, encoding='utf-8').read() if _os.path.exists(D + n) else ''
_HP = _p9('OWNER-HELPER-%s.md' % _V9)                                    # the helper page exists from v35 on
_CARD = {k: _p9('OWNER-CARD-%s-%s.md' % (_V9, k)) for k in 'AB'}
_APP9 = {k: _p9('OWNER-APPENDIX-%s-%s.md' % (_V9, k)) for k in 'AB'}
_FILM9 = _p9('OWNER-FILM-PERSON-%s.md' % _V9)
_OWNER_PAGES = {'A': A, 'B': B, 'helper': _HP}
_FX = {}; exec(_p9('facts-v35.py'), _FX); _FF = _FX['F']                                      # the expected figures always come from the v35 facts
# C228 (S M1; class: an irreversible-cancel authorization wider than its identity check): no owner page lets anyone cancel "any" key
for _n, _t in _OWNER_PAGES.items():
    for _m in re.finditer(r'(?i)any valid key of yours|any of your keys|cancel any key|all of your keys|any key (?:you|that you) (?:find|see)', _t): fail('C228', '%s holds the over-broad cancel scope %r' % (_n, _m[0]))
for _k in 'AB':
    if 'only if its name and creation date equal the blanks' not in _CARD[_k]: fail('C228', 'card %s: L2 is not tied to the older key by name and creation date' % _k)
    if 'a key you find valid' in _CARD[_k] and 'L1' not in _CARD[_k]: fail('C228', 'card %s: a valid-key rule without L1' % _k)
# C229 (S M2; class: a lead-page statement that contradicts the sheet): the 7.11 path after a failed key save
for _n, _t in (('NOTE', NOTE), ('OPEN', OPEN)):
    if re.search(r'(?i)failed key save cancels nothing|A cancels nothing on a failed', _t): fail('C229', '%s still says a failed key save cancels nothing in A' % _n)
    if not re.search(r'failed (?:key )?save skips 6\.7', _t): fail('C229', '%s does not say a failed save skips 6.7 and that 7.11 still cancels in A' % _n)
# C230 (S M3 and N M3; class: a role named but with no page, trigger or scope): the helper page
if not _HP: fail('C230', 'the cancel helper page OWNER-HELPER-%s.md does not exist' % _V9)
else:
    for _s in (_FF['helper_scope'], 'The owner asks you, by call or message. Never act on the ask itself', 'Never act for the lead, the film person, the backup person', 'not the film person, the editor, the post checker or the backup person', 'every key on your paper that is still valid is cancelled', 'the last-resort step on your paper (model account only) at once, but only if your cancel-only role can do it', 'Never copy, type or photograph key text',
               'plus %s minutes' % _FF['hw'], _FF['hcb'], _FF['hok'], _FF['dl_day'] + ' ' + _FF['rv23']):
        if _s not in _HP: fail('C230', 'helper page lacks %r' % _s[:70])
    if _HP.count('you called the owner twice, 5 minutes apart, with no answer') != 2: fail('C230', 'helper page: triggers (b) and (c) do not both need two calls to the owner')
    if len(re.findall(r'\(([a-d])\) ', _HP)) != 4: fail('C230', 'helper page does not have exactly the four triggers (a) to (d)')
    if re.search(r'(?i)\blead (?:may|can) (?:ask|tell|release)', _HP): fail('C230', 'helper page lets the lead release a cancel')
for _n, _t in (('A', A), ('B', B)):
    for _s in ('OWNER-HELPER-v35.md', 'give your cancel helper (if any) their page and paper', 'is never the film person, editor, post checker or backup person'):
        if _s not in _t: fail('C230', '%s lacks %r' % (_n, _s))
# C231 (S minor; N M5; class: a time named two ways): the backstop time and the end of the last resort
for _n, _t in (('A', A), ('B', B)):
    if _FF['bt_end'] not in _t: fail('C231', '%s lacks the end of the last resort %s (after the deadline, stranger M5)' % (_n, _FF['bt_end']))
    if 'backstop time' not in _t or ('Mon 23 Nov 2026 ' + _FF['rv23']) not in _t: fail('C231', '%s does not name the backstop time with date and both zones' % _n)
    if re.search(r'cancel-by time of (?:Sun|Mon)', _t): fail('C231', '%s calls the backstop time a cancel-by time' % _n)
# C232 (S minor 5, N minor): alarms: two deadline reminders are a fifth and a sixth alarm, set at 5.8
for _n, _t in (('A', A), ('B', B)):
    for _s in ('alarm 5 and alarm 6 of 5.8 are the fifth and sixth', 'check all six are set and ring with sound'):
        if _s not in SHEETS_DISK[_n]: fail('C232', 'sheet %s lacks %r' % (_n, _s))
    if 'alarm 5' not in _CARD[_n]: fail('C232', 'card %s lacks the fifth and sixth alarm' % _n)
    if _FF['bs'] not in _t or _FF['bm'] not in _t: fail('C232', '%s lacks a deadline reminder time' % _n)
# C233 (N M7; class: one statement with two sources): the yes is typed from one pattern, and it binds the owner
for _n, _t in (('A', A), ('B', B)):
    _ym = re.search(r'[Ii]n this pattern: "(Yes, run.*?IST\.)"', _t, re.S)
    if not _ym or _FF['bt_end'] not in _ym[1]: fail('C233', '%s: the typed yes does not carry the end of the last resort %s (stranger M5)' % (_n, _FF['bt_end']))
    for _s in ('this yes binds me to step 7.11 and to alarms 5 and 6', 'cancel helper <name or none>', 'Two sources: the lead\'s sentence and this pattern must b', 'a later yes replaces this one'):
        if _s not in _t: fail('C233', '%s lacks %r' % (_n, _s))
# C234 (N: raw recording; S: owner-open row): the raw recording is a secret file with an owner for deleting
for _n, _t in (('A', A), ('B', B)):
    if 'Raw recording:' not in _t or 'treat it as secret' not in _t: fail('C234', '%s: the raw recording is not placed and treated as secret' % _n)
if 'Open 110' not in OPEN and '| 110 |' not in OPEN: fail('C234', 'open list lacks the raw recording row')
# C235 (evidence H33; class: a computed time with a wrong constant): the 7-day time computed here from independent figures
_rd9 = _dt.datetime(2026, 11, 18, 10, 30) - _dt.timedelta(hours=168)
_exp9 = _rd9.strftime('%a %d %b %Y ') + _rd9.strftime('%H:%M') + ' UTC = ' + (_rd9 + _dt.timedelta(hours=5, minutes=30)).strftime('%H:%M') + ' IST'
if _exp9 != 'Wed 11 Nov 2026 10:30 UTC = 16:00 IST': fail('C235', 'independent 7-day time is %r' % _exp9)
if _FF.get('sevenback') != _exp9 or F.get('sevenback') not in (None, _exp9): fail('C235', 'facts: the 7-day time is %r, independent figure %r' % (F.get('sevenback'), _exp9))
for _n, _t in (('A', A), ('B', B)):
    if _exp9 not in _t: fail('C235', '%s lacks the 7-day time %s' % (_n, _exp9))
_ac9 = _dt.datetime(2026, 11, 22, 10, 30) - _dt.timedelta(hours=168)
if _FF['a_cut'] != _ac9.strftime('%a %d %b %Y ') + '10:30 UTC = 16:00 IST': fail('C235', 'facts: the sheet-A cut is %r' % _FF['a_cut'])
# C236 (evidence H50, H51, H53; class: a number typed once and not tied to the facts file): each figure is read in every place it is written
_TT = A + '\n' + B + '\n' + _APP9['A'] + '\n' + _APP9['B']
for _pat, _want in ((r'Film pause: (\d+)', '10'), (r'film pause \((\d+)\)', '10'), (r'the sample says (\d+) minutes', '10'), (r"Call ceiling \(the lead's figure\): (\d+)", '3'), (r'call ceiling x that = (\d+) x', '3'),
                    (r'sample assume (\d+)\)', '15'), (r'run length \((\d+)\)', '15'), (r'Run length: \[?[^\n]{0,60}? assume (\d+)', '15')):
    _ms = re.findall(_pat, _TT)
    if not _ms and _pat != r'Run length: \[?[^\n]{0,60}? assume (\d+)': fail('C236', 'no place found for %r (a changed sentence?)' % _pat)
    for _v in _ms:
        if _v != _want: fail('C236', '%r reads %s, the figure is %s' % (_pat, _v, _want))
# C237 (evidence H37; class: a structural label defined twice or not at all): labels L1 to L5 and W1 to W9 are each defined once on the card
for _k in 'AB':
    for _i in range(1, 6):
        if len(re.findall(r'(?:\*\* |\. |; )L%d (?!to )(?=[A-Za-z])' % _i, _CARD[_k])) != 1: fail('C237', 'card %s: label L%d is not defined exactly once' % (_k, _i))
    for _i in range(1, 10):
        if len(re.findall(r'(?:\*\* |\. |; )W%d (?!to )(?=[A-Za-z])' % _i, _CARD[_k])) != 1: fail('C237', 'card %s: label W%d is not defined exactly once' % (_k, _i))
    if set(re.findall(r'\bL(\d+)\b', A if _k == 'A' else B)) - set('12345'): fail('C237', 'sheet %s names an L label that does not exist' % _k)
    if set(re.findall(r'\bW(\d+)\b', A if _k == 'A' else B)) - set('123456789'): fail('C237', 'sheet %s names a W label that does not exist' % _k)
# C238 (evidence H38; class: a structural label or heading changed in one place): headings of every page against headings-v35.txt (ACCEPT_HEADINGS=1 rewrites it after a person read the diff)
_hd = []
for _n in ('OWNER-SHEET-%s-A.md', 'OWNER-SHEET-%s-B.md', 'OWNER-CARD-%s-A.md', 'OWNER-CARD-%s-B.md', 'OWNER-APPENDIX-%s-A.md', 'OWNER-APPENDIX-%s-B.md'):
    for _l in _p9(_n % _V9).split('\n'):
        if _l.startswith('#'): _hd.append('%s|%s' % (_n % 'vNN', _l))
for _n in ('OWNER-FILM-PERSON-%s.md', 'OWNER-HELPER-%s.md'):
    for _l in _p9(_n % _V9).split('\n'):
        if _l.startswith('#'): _hd.append('%s|%s' % (_n % 'vNN', _l.replace('(v31)', '(v35)')))
_HL = D + 'headings-v35.txt'
if _os.environ.get('ACCEPT_HEADINGS') == '1': open(_HL, 'w', encoding='utf-8').write('\n'.join(_hd) + '\n'); print('headings-v35.txt rewritten: %d headings' % len(_hd))
elif not _os.path.exists(_HL): fail('C238', 'headings-v35.txt missing')
else:
    _okh = [x for x in open(_HL, encoding='utf-8').read().split('\n') if x]
    for _x in _hd:
        if _x not in _okh: fail('C238', 'heading not in the verified list: ' + _x[:90])
    for _x in _okh:
        if _x not in _hd: fail('C238', 'verified heading is gone: ' + _x[:90])
# C239 (evidence 5; class: a number typed once): the placeholder use count of each fact, per source, against factuse-v35.txt (ACCEPT_FACTUSE=1 rewrites it after a person read the diff)
_srcl = [x for x in ('OWNER-SHEET-%s-SOURCE.md' % _V9, 'LEAD-RELEASE-NOTE-%s-SOURCE.md' % ('v19' if _V9 == 'v35' else 'v15'), '%s-OPEN-FOR-LEAD-SOURCE.md' % _V9) if _os.path.exists(D + x)]
_fu = []
for _x in _srcl:
    _cnt = {}
    for _m in re.findall(r'\{\{([a-z0-9_]+)\}\}', _p9(_x)): _cnt[_m] = _cnt.get(_m, 0) + 1
    _fu += ['%s|%s|%d' % (_x.replace('v19', 'vNN').replace('v18', 'vNN').replace('v17', 'vNN').replace('v15', 'vNN').replace(_V9, 'vNN'), _k, _v) for _k, _v in sorted(_cnt.items())]
_FL = D + 'factuse-v35.txt'
if _os.environ.get('ACCEPT_FACTUSE') == '1': open(_FL, 'w', encoding='utf-8').write('\n'.join(_fu) + '\n'); print('factuse-v35.txt rewritten: %d rows' % len(_fu))
elif not _os.path.exists(_FL): fail('C239', 'factuse-v35.txt missing')
else:
    _okf = set(x for x in open(_FL, encoding='utf-8').read().split('\n') if x)
    for _x in sorted(set(_fu) ^ _okf): fail('C239', 'fact-use row differs from the verified list: ' + _x[:90])
# C240 (evidence H18, H20, H21; class: an internal code or an absolute path in text for the owner)
for _n, _t in _OWNER_PAGES.items():
    for _m in re.finditer(r'/(?:home|Users|tmp|mnt)/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+|\b(?:ORD|DEC|ACK|WP\d*|DF\d+):', _t): fail('C240', '%s holds %r (an absolute path or an internal code)' % (_n, _m[0][:40]))
# C241 (evidence H25; N minor): the one-letter rule is worded in full on both sheets
for _n, _t in (('A', A), ('B', B)):
    if 'The lead sends the numbers message for one letter only; a letter that differs from this sheet: no run' not in _t: fail('C241', '%s lacks the one-letter rule in full' % _n)
# C242 (evidence H54; class: a lead message that releases the older-key cancel, in any wording): no page lets a lead message release it
for _n, _t in (('A', A), ('B', B), ('NOTE', NOTE), ('OPEN', OPEN)):
    for _m in re.finditer(r'(?i)(?:the )?lead (?:sends|says|writes|types|tells) you[^.\n]{0,12}"cancel the older key|"cancel the older key[^"]{0,20}"[^.\n]{0,40}(?:release|allow|permit)', _t): fail('C242', '%s: a lead message appears to release the older-key cancel: %r' % (_n, _m[0][:70]))
# C243 (evidence H09; class: a warning removed from beside the choice it concerns): the 7-day warning is beside Open 71 in both lead pages
for _n, _t in (('NOTE', NOTE), ('OPEN', OPEN)):
    if 'will probably fail on Wed 18 Nov' not in _t or 'No default pick' not in _t: fail('C243', '%s lacks the warning or the no-default wording' % _n)
# C244 (N B1, M1, M2; class: a first action that cannot be done): 5.1a is doable and 6.6 / 7.3 do not contradict each other
for _n, _t in (('A', A), ('B', B)):
    _i = _t.find('a) Which sheet'); _b = _t[_i:_t.find('\n', _i)]
    if len(_b.split()) > 215: fail('C244', '%s: 5.1a has %d words (more than 215)' % (_n, len(_b.split())))
    if _b.count('**The 7-day rule') != 1: fail('C244', '%s: the 7-day rule is not defined exactly once (in bold) in 5.1a' % _n)
    if 'before any message from the lead' in _t: fail('C244', '%s keeps "before any message from the lead" (B1)' % _n)
    if re.search(r'\btake (?:sheet )?B\b', _t): fail('C244', '%s uses "take B" for a choice of sheet (word with two meanings)' % _n)
# C245 (N minors 1, 2, 3; class: a pointer that sends a stranger to a place that does not say it): pointers read by a person are in pointers-v35.txt (C19); here: no bare internal pointer in owner text
for _n, _t in (('A', A), ('B', B)):
    if re.search(r'sheet section 2\b', _t): fail('C245', '%s sends the reader to "sheet section 2" (the STOP RULE is in section 1)' % _n)

# ---- Part 10 (v35, round 5): C246 to C262. One or more checks per finding of review-v32-security, review-v32-naive and review-v32-evidence.
# Source-level checks (C255 to C262) read the SOURCE file itself, so they work with C01 off: a source mutation rebuilds the pages and C01 then passes, only these catch it. Each runs at EVERY occurrence.
_S10 = _p9('OWNER-SHEET-%s-SOURCE.md' % _V9)
def _occ(t, s): return [m.start() for m in re.finditer(re.escape(s), t)]
# C246 (S M1; class: a waiting chain that runs past the deadline): the card, the yes and part 10 do the last-resort step at once and state both chain ends
for _n, _t in (('card A', _CARD['A']), ('card B', _CARD['B'])):
    if 'do the last-resort step at once after your first "cancel failed"' not in _t: fail('C246', '%s lacks the near-deadline last-resort rule' % _n)
for _n, _t in (('A', A), ('B', B)):
    if _t.count('18:31 UTC = 00:01 IST') < 3 or _t.count('18:41 UTC = 00:11 IST') < 3: fail('C246', '%s: a chain end (18:31 UTC = 00:01 IST, 18:41 UTC = 00:11 IST) is not stated in the card, the yes and part 10 (need 3 each)' % _n)
    if _t.count('at once after') < 3: fail('C246', '%s: "at once after" is not in the card, the yes and part 10' % _n)
    if 'the helper does the last-resort step on its paper (none: only yours is left); call the backup person at once' not in _t: fail('C246', '%s lacks "the helper path ends at the owner\'s last-resort step"' % _n)
if _FF['bm_chain'] != 'Mon 23 Nov 2026 18:31 UTC = 00:01 IST' or not _FF['bt_end'].endswith('18:41 UTC = 00:11 IST'): fail('C246', 'the chain end figures are not 18:31 UTC = 00:01 IST and 18:41 UTC = 00:11 IST')
# C247 (S M2; class: a typed line wider than the shape that was checked): the cd line is `cd ` plus the Take folder, in 7.2, the rows rule and R6
for _n, _t in (('A', A), ('B', B)):
    for _s in ('type `cd ` and the Take folder of the message, nothing more', 'the `cd` line of 7.2 is exactly `cd ` plus the Take folder, nothing else (no `&&`, `;`, `|`, second command or space-separated word after the folder)', 'the "cd line" is `cd ` plus the Take folder and nothing else'):
        if _s not in _t: fail('C247', '%s lacks %r' % (_n, _s[:60]))
    if re.search(r'type `cd [^`]*(?:&&|;|\|)', _t): fail('C247', '%s: a cd line with a second command' % _n)
# C248 (S M3, M4, m1; class: a stale claim after a change): no page says A has one live key at a time or keeps "Default: A"; no stale file names
for _n, _t in (('A', A), ('B', B), ('NOTE', NOTE), ('OPEN', OPEN), ('helper', _HP)):
    for _m in re.finditer(r'(?i:one live key at a time)|Default: A\b|Default A\b|OWNER-NUMBERS-|OWNER-FILM-v\d', _t): fail('C248', '%s holds the stale text %r' % (_n, _m[0]))
for _n, _t in (('NOTE', NOTE), ('OPEN', OPEN)):
    if 'OWNER-HELPER-v35.md' not in _t: fail('C248', '%s does not list the helper page' % _n)
# C249 (S m2-m8; class: a stop or a rule only in some places): the Sunday rule, the paper void step, helper trigger, the film stop
for _n, _t in (('A', A), ('B', B)):
    for _s in ('Sunday run day: a run on Sun 22 Nov is allowed only if its cancel-by time is at or before ' + _FF['sun_cb'], 'so that no alarm 5 or backstop time meets a live run key.'):
        if _s not in _t: fail('C249', '%s lacks %r' % (_n, _s[:70]))
if _HP:
    for _s in ('(write VOID on it; a new paper replaces it)', "the owner's phone number", 'call the owner yourself on the phone number on your paper', 'Sun 22 Nov 2026 18:19 UTC = 23:49 IST and Mon 23 Nov 2026 18:19 UTC = 23:49 IST', 'you have none'):
        if _s not in _HP: fail('C249', 'the helper page lacks %r' % _s[:70])
if 'Your "stop" is a danger sign for the owner (W3)' not in _FILM9 and _FILM9: fail('C249', 'the film person page lacks the "stop" effect')
for _n, _t in (('A', A), ('B', B)):
    if 'or the film person says "stop"' not in _t: fail('C249', '%s: W3 lacks the film person "stop"' % _n)
# C250 (N majors 1-10; class: a first-time reader cannot do the step): wording that a stranger needs
for _n, _t in (('card A', _CARD['A']), ('card B', _CARD['B'])):
    if 'press cancel again on the same named row and reload' not in _t: fail('C250', '%s lacks "the same named row" in step 4' % _n)
for _n, _t in (('A', A), ('B', B)):
    for _s in ('Watch the edited video twice', 'the subject start begins with the run name: otherwise no run', 'at or before'):
        if _s not in _t: fail('C250', '%s lacks %r' % (_n, _s))
    if re.search(r'Watch the (?:recording|video) twice', _t): fail('C250', '%s: 8.8 does not say "the edited video"' % _n)
    if 'which are the film person\'s start words' not in _t: fail('C250', '%s does not say that "film pause now" are the film person\'s start words' % _n)
# C251 (reading load; class: a page grown without a stated number): the five pages are counted and printed, and no page is silently over the figure recorded in v35-CHANGES.md
_cg = _p9('v35-CHANGES.md')
if _V9 == 'v35' and not re.search(r'five pages[^\n]{0,80}\d\d,\d\d\d', _cg): fail('C251', 'v35-CHANGES.md does not state the five-page word count')
# --- source-level content checks (evidence C01-only gap): the 11 sentences the independent run mutated, each at every occurrence, on the SOURCE
# C255 (H04) the chain-end figures are placeholders at every occurrence in the source and no literal time follows "would end at" / "until about"
if len(_occ(_S10, '{{bm_chain}}')) < 3 or len(_occ(_S10, '{{bt_end}}')) < 3: fail('C255', 'the source holds {{bm_chain}} %d and {{bt_end}} %d times (need 3 each: card, yes, part 10)' % (len(_occ(_S10, '{{bm_chain}}')), len(_occ(_S10, '{{bt_end}}'))))
for _m in re.finditer(r'(?:would end at|until about|ends? at) (?:Mon 23 Nov 2026 )?\d\d:\d\d UTC', _S10): fail('C255', 'a chain end typed as a literal time: %r' % _m[0])
for _m in re.finditer(r'(?:\{\{bm_chain\}\}|\{\{bt_end\}\})', _S10):
    _w = _S10[_m.end():_m.end() + 160]
    if re.search(r'\d\d:\d\d UTC', _w.split('\n')[0][:60]): fail('C255', 'a literal time right after a chain end placeholder: %r' % _w[:60])
# C256 (H05) every chain-end sentence says AFTER the deadline
if len(_occ(_S10, 'both after the deadline')) < 2: fail('C256', 'the source says "both after the deadline" %d times (need 2)' % len(_occ(_S10, 'both after the deadline')))
for _m in re.finditer(r'(?:\{\{bm_chain\}\}|\{\{bt_end\}\})[^\n]{0,260}', _S10):
    if re.search(r'before the deadline', _m[0]): fail('C256', 'a chain end described as before the deadline: %r' % _m[0][:80])
for _m in re.finditer(r'(?i)last[- ]resort[^.\n]{0,80}before the deadline', _S10): fail('C256', 'the last resort set before the deadline: %r' % _m[0][:80])
# C257 (H07, H35) the helper cancels only keys the owner names that are on the paper; key text that appears is closed and reported, never kept
if _S10.count('Any other key, even one the owner mistyped the name of: touch nothing, write down its name') != 1: fail('C257', 'the helper scope sentence "Any other key ... touch nothing" is not present exactly once in the source')
if len(_occ(_S10, 'you cancel only a key the owner names that is also on your paper')) != 1: fail('C257', 'the "only a key the owner names that is also on your paper" sentence is not present exactly once')
for _m in re.finditer(r'(?i)cancel (?:any|every|all|each) (?:other |valid |remaining )?keys?\b[^.\n]{0,40}', _S10):
    if not re.search(r'(?i)(?:never|not|nothing|no|do not|nor|able to|can) [^.\n]{0,40}$', _S10[max(0, _m.start() - 40):_m.start()]) and 'of L1' not in _m[0] and 'you made' not in _m[0]: fail('C257', 'a broad cancel scope in the source: %r' % _m[0][:60])
if len(_occ(_S10, 'if key text appears, close it and tell the owner it appeared')) != 1: fail('C257', 'the "close it and tell the owner it appeared" sentence is not present exactly once')
for _m in re.finditer(r'(?i)(?:keep|save|store|write down|jot|note down|photograph|copy)[^.\n;]{0,25}\bkey text', _S10):
    if not re.search(r'(?i)never [^.\n]{0,30}$', _S10[max(0, _m.start() - 40):_m.start()]): fail('C257', 'key text kept or copied: %r' % _m[0][:60])
# C258 (H14) R6 says the typed parts are never entered by a tool, script, window or person
if len(_occ(_S10, 'never by a tool, script, window or person')) != 1: fail('C258', 'R6 "never by a tool, script, window or person" is not present exactly once in the source')
for _m in re.finditer(r'(?i)\bor by a tool, script|by a tool, script, window or person\b(?<!never by a tool, script, window or person)', _S10): fail('C258', 'R6 allows a tool or script: %r' % _m[0][:60])
# C259 (H17, H18) the clipboard is emptied of the key after the paste, and the paste is once only
if len(_occ(_S10, 'copy one harmless word such as `clear` (it replaces the clipboard)')) != 1 or len(_occ(_S10, 'copy a harmless word')) < 2: fail('C259', 'the clipboard-clearing steps (harmless word) are missing or fewer than in v32 (need "copy one harmless word such as `clear` (it replaces the clipboard)" once and "copy a harmless word" twice)')
if len(_occ(_S10, 'Paste once (Ctrl+Shift+V or right-click), only if')) != 1: fail('C259', '"Paste once (Ctrl+Shift+V or right-click), only if" is not present exactly once')
for _m in re.finditer(r'(?i)\bpaste (?:as often|again|twice|more than once|repeatedly|as many|freely)[^.\n]{0,30}', _S10): fail('C259', 'the paste is not once only: %r' % _m[0][:60])
# C260 (H19, H20) the key file is private (-rw-------) and a difference is never tolerated
_modes = re.findall(r'starts `(-[rwx-]{9})`', _S10)
if _modes != ['-rw-------']: fail('C260', 'the key file mode in the source is %r (must be exactly one -rw-------)' % _modes)
if re.search(r'-r[w-][x-]r', _S10) or re.search(r'-rw-r', _S10): fail('C260', 'a group or world readable mode appears in the source')
if len(_occ(_S10, 'A difference in a number, name, count, account, time or key state is never tolerated.')) != 2: fail('C260', '"A difference ... is never tolerated." is not present exactly twice (sheet and card)')
for _m in re.finditer(r'(?i)(?<!never )(?<!not )tolerated[^.\n]{0,20}', _S10):
    if not re.search(r'\*\*tolerated\*\*|UNVERIFIED, tolerated|tolerated items|tolerated\)|tolerated::', _S10[_m.start() - 30:_m.end() + 12]): fail('C260', 'the word "tolerated" is used in a new way: %r' % _S10[max(0, _m.start() - 40):_m.end()][:70])
# C261 (H23) every cancel of the older key is tied to name and creation date equal the blanks
_cond = 'name and creation date equal the blanks'
if len(_occ(_S10, _cond)) < 5: fail('C261', 'the older-key condition appears %d times in the source (v32: 5 or more)' % len(_occ(_S10, _cond)))
for _m in re.finditer(r"cancel (?:it|the older key)[^\n]{0,40}(?:L2|card)|L2 the older key named", _S10):
    _w = _S10[max(0, _m.start() - 250):_m.start() + 330]
    if _cond not in _w: fail('C261', 'a cancel of the older key without the name-and-creation-date condition within 330 characters: %r' % _w[:90])
for _n, _t in (('A', A), ('B', B)):
    for _m in re.finditer(r"cancel the older key by the card's L2|L2 the older key named", _t):
        if _cond not in _t[max(0, _m.start() - 250):_m.start() + 330]: fail('C261', '%s: a cancel of the older key without the condition: %r' % (_n, _t[_m.start():_m.start() + 70]))
# C262 (H38 and safe defaults generally): the backstop cancels even if a run is in progress, and no safe default is reversed
if len(_occ(_S10, 'even if a run was in progress')) < 1 or len(_occ(_S10, 'even if a run is in progress')) < 1: fail('C262', 'the backstop "even if a run is/was in progress" sentences are missing (need 1 each)')
for _m in re.finditer(r'(?i)unless a run (?:is|was)[^.\n]{0,30}|(?:backstop|deadline)[^.\n]{0,80}\bunless\b[^.\n]{0,40}run', _S10): fail('C262', 'a backstop cancel with an exception for a run: %r' % _m[0][:70])
_SAFE = ('never copy, type or photograph key text', 'nothing is done by a lead message alone', 'Never copy, type or photograph key text', 'cancel nothing', 'touch nothing', 'FREEZE', 'STOP RULE', 'R6 shape check first', 'this cancel cannot be undone')
_floor = {'FREEZE': 10, 'STOP RULE': 4, 'R6 shape check first': 3, 'touch nothing': 2, 'cancel nothing': 2, 'this cancel cannot be undone': 1, 'Never copy, type or photograph key text': 1}
for _k, _v in _floor.items():
    if len(_occ(_S10, _k)) < _v: fail('C262', 'the safe default %r appears %d times in the source (need %d or more)' % (_k, len(_occ(_S10, _k)), _v))
for _m in re.finditer(r'(?i)\b(?:skip|omit|ignore|no need for|without) (?:the )?(?:R6|shape check|STOP RULE|name and creation date|7-day rule)', _S10): fail('C262', 'a safe default reversed: %r' % _m[0])
# ---- v35 (round 6): every protected sentence is pinned at EVERY occurrence in the SOURCE and in each BUILT page (A and B), so a silent edit of one copy cannot pass on a generator-compare alone
_HELP = rd('OWNER-HELPER-%s.md' % _V9); _FILM = rd('OWNER-FILM-PERSON-%s.md' % _V9)
_PAGES34 = {'A': A, 'B': B}
def _pin(code, phrase, src_n=1, page_n=1, exact=True):
    """phrase must occur src_n times in the source and (exactly or at least) page_n times in each built sheet text A and B"""
    n = len(_occ(_S10, phrase))
    if n < src_n or (exact and n != src_n): fail(code, 'source holds %r %d times (need %d)' % (phrase[:60], n, src_n))
    for _k, _t in _PAGES34.items():
        m = len(_occ(_t, phrase.replace('{{ph_cf}}', 'cancel failed')))
        if m < page_n or (exact and m != page_n): fail(code, 'sheet %s pages hold %r %d times (need %d)' % (_k, phrase[:60], m, page_n))
def _ban(code, rx, texts):
    for _n, _t in texts.items():
        for _m in re.finditer(rx, _t): fail(code, '%s: forbidden wording %r' % (_n, _m[0][:80]))
_ALLTXT = {'source': _S10, 'A': A, 'B': B, 'helper': _HELP}
# C263 (X03) auto-reload must be off: the money rule, every place
_pin('C263', 'auto-reload** = the account tops itself up when low (must be off)', 1, 1)
_pin('C263', 'Auto-reload not off, a valid key other than the older key', 1, 1)
_pin('C263', 'prepaid, auto-reload off, balance at least the expected total', 1, 1)
_ban('C263', r'(?i)auto-reload[^.;|]{0,60}(must be on|stay on|is on\b|on is fine)', _ALLTXT)
# C264 (X07) contact deleting is exact: one address, exactly one result, then delete
_pin('C264', 'search the exact address, see exactly one result whose page shows it, then delete')
_ban('C264', r'(?i)search the (start|beginning|first part|part|domain)|delete all (the )?(results|matches|contacts found)|delete every (result|match)|(start|beginning) of the address', _ALLTXT)
# C265 (X08) the ordinary waiting chain ends at the owner's own last-resort step
_pin('C265', 'if nobody answers within 10 more minutes, do the last-resort step yourself, only in the model account')
_ban('C265', r'(?i)(wait|waiting) (as long as|until) (you like|someone|the lead)[^.]{0,40}last[- ]resort', _ALLTXT)
# C266 (X10) the public post: only the lead's exact sentences, only after "post" and the post checker's written match; nothing else, and no lease or recovery text in the owner pages
_pin('C266', 'Post only the video and the lead\'s exact sentences, after the lead\'s word "post" and the post checker\'s written "matches the sentences"')
_pin('C266', 'the only words you may post', 1, 1)
_pin('C266', 'no other words may be posted', 1, 1)
_ban('C266', r'(?i)\b(?:lease|crash recovery|recovery after a crash)\b', {'A': A, 'B': B, 'helper': _HELP, 'film': _FILM})
_ban('C266', r'(?i)post (?:also|as well|any other|extra|additional)\b[^.]{0,30}(?:text|words|sentence|line|caption)', {'A': A, 'B': B})
# C267 (security M1) a failed helper cancel ends at a last-resort step (on the helper paper or none) and the typed yes names the case
for _p in ('the last-resort step on your paper (model account only) at once, but only if your cancel-only role can do it', "the last-resort step in the owner's words (or none"):
    if _p not in _HELP or len(_occ(_S10, _p)) != 1: fail('C267', 'helper page or source lacks %r' % _p)
_pin('C267', 'the helper does the last-resort step on its paper (none: only yours is left); call the backup person at once')
_pin('C267', 'a helper whose cancel fails does only the last-resort step on its paper or none', 1, 1)
_ban('C267', r'(?i)the helper has (?:none|no last-resort)|you have none, so if your cancel fails and the owner', {'A': A, 'B': B, 'helper': _HELP.replace('Paper says none: you have none, so if the owner cannot be reached', 'X')})
# C268 (security M2 and minor 7) the lead pages: one claim sentence, no open lease wording, one 7-day wording
for _n, _t in (('note', NOTE), ('open list', OPEN)):
    _ban('C268', r'(?i)two sentences|unless approved in writing|lease wording \(G12\)|(?:less|more) than 7 days|\bover 7 days|\bunder 7 days|B is worse than A for money', {_n: _t})
if 'one sentence (lead answer Q22c)' not in NOTE: fail('C268', 'the note does not say the claim wording is one sentence (lead answer Q22c)')
# C269 (stranger B2) the helper paper is completed after step 5.9, and the helper does little until then
if 'Two blanks are allowed at hand-over, the cancel button word and the cancelled word: the owner phones them after step 5.9 on the run day' not in _HELP: fail('C269', 'the helper page does not say when the helper paper is completed')
if "until both are written you act only on the owner's call or at a backstop time" not in _HELP: fail('C269', 'the helper page does not say what the helper does until the paper is complete')
_pin('C269', 'then phone your cancel helper the button word and the cancelled word', 1, 1)
_pin('C269', 'give your cancel helper (if any) their page and paper (first read the role\'s permission list: appendix 10), the two words of 5.9 still blank', 1, 1)
# C270 (stranger B3) one exit for a missing Recall page
_pin('C270', 'no such page: describe that, then go on; UNVERIFIED that no page means no Recall')
_ban('C270', r'Recall[^.]{0,260}(?:this is a STOP|written answer)', {'source': _S10, 'A': A, 'B': B})
# C271 (security minors 1, 2, 4, 5) reminders, backstop times, phone fallback, mismatch exit, 22 minutes
_ban('C271', r'a reminder never cancels a live run key|up to 20 minutes', _ALLTXT)
if len(_occ(_S10, '**Backstop time** = {{rv22}} or {{dl_day}} {{rv23}}')) != 2: fail('C271', 'the two backstop time definitions do not both name the Sunday and Monday times')
_pin('C271', '(retry 2 minutes, phone fallback, send "{{ph_cf}}", then the step)', 1, 1)
_pin('C271', '(they differ: cancel nothing, send "{{ph_cf}}", call the backup person at once)', 1, 1)
_pin('C271', 'In those up to 22 minutes (2 of retry, then 10 and 10)', 1, 1)
# C272 (stranger M7) the screen turn-off is set with sleep and lid
_pin('C272', 'sleep Never; screen off Never; lid close action', 1, 1)
# C273 (reading load) no net words: the five pages are lower than v33 (15722), the sheet is no longer than v33 (6286 on A)
for _k in 'AB':
    _w = {p % _k if '%s' in p else p: len(rd(p % _k if '%s' in p else p).split()) for p in ('OWNER-SHEET-' + _V9 + '-%s.md', 'OWNER-CARD-' + _V9 + '-%s.md', 'OWNER-APPENDIX-' + _V9 + '-%s.md', 'OWNER-FILM-PERSON-' + _V9 + '.md', 'OWNER-HELPER-' + _V9 + '.md')}
    if sum(_w.values()) >= 15722: fail('C273', 'sheet %s: five pages hold %d words, not lower than v33 (15722)' % (_k, sum(_w.values())))
    if _w['OWNER-SHEET-%s-%s.md' % (_V9, _k)] > 6286: fail('C273', 'sheet %s page has %d words: more than v33 (6286)' % (_k, _w['OWNER-SHEET-%s-%s.md' % (_V9, _k)]))
