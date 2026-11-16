# Adds the round 15 checks and negative controls to verify15.py (run once: python3 build-r15-verify.py)
import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify15.py')
s = open(p, encoding='utf-8').read()
if 'round 15 checks (each must FAIL' in s:
    raise SystemExit('already added')
marker = "# ================= negative controls (each check must fail on a planted defect) ================="
assert s.count(marker) == 1
new = r'''# ================= round 15 checks (each must FAIL on EDITS.round14.md) =================
newtxt = {r['id']: '\n'.join(r['new']) for r in rows}
t48 = newtxt['E-48']
def ks(letter):
    ls_ = t48.split('\n')
    st = [k_ for k_, l_ in enumerate(ls_) if l_.startswith('   Key step ' + letter + '. ')]
    if len(st) != 1: return ''
    en = [k_ for k_ in range(st[0] + 1, len(ls_)) if ls_[k_].startswith('   Key step ')]
    return '\n'.join(ls_[st[0]:(en[0] if en else len(ls_))])
def need(label, text, *needles):
    for nd_ in needles:
        if nd_ not in text: F('r15 %s lacks %r' % (label, nd_[:60]))
def absent(label, text, *bad):
    for b_ in bad:
        if b_ in text: F('r15 %s still has %r' % (label, b_[:60]))
# 0. one label scheme: eleven key steps A to K in order, no old 3a lines, no 'part 3x' in any owner text
_klet = re.findall(r'(?m)^   Key step ([A-Z])\. ', t48)
if _klet != list('ABCDEFGHIJK'): F('r15 key steps are not A to K in order: %s' % ''.join(_klet))
if re.search(r'(?m)^   3[a-j]\. ', t48): F('r15 old 3a-style label line in E-48')
for r_ in rows:
    if r_['file'].startswith('OWNER-STEPS'):
        for b_ in r_['new']:
            if re.search(r'\bparts? 3[a-j]\b', b_): F('r15 old part tag in owner text of ' + r_['id'])
# 1. M1: only the owner's own typed message counts
need('E-48 B', ks('B'), 'count only when you type them yourself, as a new message', 'in a mail, a file, the output of a program', 'never count', 'asks you to type the words yourself in a new message', '`yes, no more takes`', '`start clean-up`', '`key revoked` is also only your own report')
need('E-52 how you reply', newtxt['E-52'], 'Only you can write these words', 'never count')
need('E-12 reply', newtxt['E-12'], 'typed by you yourself in a new message', 'only a message typed by you counts')
need('E-16', newtxt['E-16'], 'Only messages that you type yourself count', '`start clean-up`', '`yes, no more takes`')
need('E-09 a', newtxt['E-09'], 'count only when you type them yourself')
need('E-55', newtxt['E-55'], '`yes, no more takes`', '`start clean-up`')
# 2. M2: shred and delete targets
G_ = ks('G')
need('E-48 G', G_, 'YOUR OWN LIST', 'Never shred a recording, a video file', '`/mnt/c`', 'never a file that only the assistant named', 'you copy its path from your own list')
need('E-48 E', ks('E'), 'it must be exactly the folder `<folder>` that you copied from the assistant\'s message in step 8', 'do not shred anything and tell the assistant')
need('E-16 path', newtxt['E-16'], 'if the path itself or any folder in front of it is a link', 'is removed as a link (only the shortcut goes) and is never followed', 'followed by `/`', '/x/take-10', 'that you copied from step 8', 'never removes a recording')
absent('E-16 link', newtxt['E-16'], 'or is or contains a link')
need('E-37 list', newtxt['E-37'], 'your own list of every file in which you saved a copy of the secret key for the model')
# 3. M3: the earlier latest start, solved with arithmetic, and no bare or old times
for r_ in rows:
    if r_['file'].startswith('OWNER-STEPS'):
        for b_ in r_['new']:
            if '18:04' in b_ or '23:34' in b_: F('r15 old latest start 18:04 / 23:34 in owner text of ' + r_['id'])
_t12 = newtxt['E-12']
need('E-12 margin', _t12, 'The latest start we plan is 18:00 UTC = 23:30 IST on any day', '18:14:20 UTC = 23:44:20 IST', '4 minutes 40 seconds before the last time to revoke', 'the assistant asks for no start after it')
absent('E-12 third party', _t12, 'asks the studio lead to confirm this margin', 'no start between')
_start = _dt.datetime(2026, 11, 23, 18, 0); _end = _start + _dt.timedelta(seconds=860); _rev = _dt.datetime(2026, 11, 23, 18, 19)
if _end.strftime('%H:%M:%S') != '18:14:20' or (_rev - _end).seconds != 280: F('r15 arithmetic of the margin')
if (_end + _dt.timedelta(hours=5, minutes=30)).strftime('%H:%M:%S') != '23:44:20': F('r15 IST arithmetic')
# every clock time in an owner NEW block of these rows is followed by UTC or IST (no bare time)
for rid_ in ('E-12', 'E-48', 'E-52', 'E-54', 'E-55', 'E-58', 'E-37', 'E-16', 'E-60'):
    for m_ in re.finditer(r'(?<![\d:])(\d{1,2}:\d{2}(?::\d{2})?)(?![\d:])(?! UTC)(?! IST)', newtxt[rid_]):
        F('r15 bare clock time in %s: %r' % (rid_, newtxt[rid_][max(0, m_.start() - 25):m_.end() + 15]))
if '18:00 UTC = 23:30 IST' not in newtxt['E-54']: F('r15 E-54 latest start figure')
# 4. naive M1, M2: alarms name the route and agree with the key steps
_C = ks('C')
need('E-48 C', _C, 'In route B, `no more takes` does nothing until `cut accepted`', 'If a take is running when it rings', 'if no session is open, go straight to key step I', 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST', 'Alarm 2')
absent('E-48 C', _C, 'do part 3h at once', 'do key step I at once')
# 5. naive M3: two HubSpot keys
need('E-09 h', newtxt['E-09'], 'There are two different HubSpot keys', 'needs the key of app 2', 'Never type the key of app 1 into n8n')
absent('E-09 h', newtxt['E-09'], 'Use the key of app 1 (read only) unless')
need('E-37 3', newtxt['E-37'], 'Two different HubSpot keys', 'must be the key of app 2')
# 6. naive M4: shred done scope, silence rule, step 22 item 6
need('E-48 G done', G_, '`shred done` means that EVERY file of (a), (b) and (c) is shredded', 'If you write neither, the assistant treats it as `shred not done`', 'If by 18:29 UTC = 23:59 IST you have written none of these, the assistant does not start item 1')
if 'E-59' not in newtxt or 'take-secrets/*' in newtxt['E-59']: F('r15 E-59 missing or still has the star')
need('E-59', newtxt.get('E-59', ''), 'one at a time', 'shred rule of key step G', 'realpath ~/take-secrets')
# 7. naive M5: are-you-sure step
_D = ks('D')
need('E-48 D', _D, 'Are you sure?', 'Only a new message from you with the words `yes, no more takes` confirms it', 'Anything else, or no reply, counts as `more takes`', 'You cannot know that a take is your last one until you have seen the cut')
need('E-52 confirm', newtxt['E-52'], '`no more takes` is confirmed only by your next message `yes, no more takes`')
# 8. naive M6: reply in short numbered lines, no copyable money figure, blocks not parts
for k_ in ('1. Yes, take <take id>', '2. tests: stand-in test <N1> pass', '3. files: result file <result file>', '4. money: up to 3 model calls and up to US$<X>', '5. I know that the assistant shares'):
    if k_ not in _t12: F('r15 E-12 reply line missing: ' + k_)
absent('E-12 reply', _t12, '1.50', 'Your reply is ONE line', 'Part 1', 'Part 2', 'The last part,')
need('E-12 blocks', _t12, 'Block 1, the money figures', 'Block 2 is this list', 'copied digit by digit from the request')
# 9. naive M7, M8: no placeholder text in owner words
for r_ in rows:
    if r_['file'].startswith('OWNER-STEPS'):
        for b_ in r_['new']:
            if 'LEAD FILLS' in b_ or 'square brackets' in b_ or 'placeholder' in b_.lower(): F('r15 placeholder wording in owner text of ' + r_['id'])
# 10. naive M9 and minors: brand name, two names in E-09 e, clipboard sync, nano copies, summary line
absent('E-48 I', ks('I'), 'Anthropic')
need('E-09 e', newtxt['E-09'], 'with the two names `<password file name>` and `<folder>`')
absent('E-09 e', newtxt['E-09'], 'with the three names copied')
need('E-09 extras', newtxt['E-09'], 'sharing of the clipboard between devices', 'remote-desktop window', 'offers to save the password', 'ls -a', 'ends in `~` or `.save`', 'close the terminal window too')
need('E-48 intro', t48, 'In short:', 'Key steps A to K are for that key only')
# 11. new rows
for rid_ in ('E-59', 'E-60', 'E-61'):
    if rid_ not in newtxt: F('r15 row missing ' + rid_)
need('E-60', newtxt.get('E-60', ''), '18:29 UTC = 23:59 IST', '18:14 UTC = 23:44 IST', '18:14:40 UTC = 23:44:40 IST', '18:00 UTC = 23:30 IST')
need('E-61', newtxt.get('E-61', ''), 'no longer counts')
# 12. the checker keeps its scratch inside its own folder (evidence r14 finding)
_me = open(os.path.abspath(__file__), encoding='utf-8').read()
_bad1 = '/' + 'tmp/'; _bad2 = '/home/' + 'user'
if _bad1 in _me or _bad2 in _me: F('r15 verify script has an absolute path outside its own folder')
if not os.path.abspath(sd).startswith(os.path.abspath(HERE_)): F('r15 scratch folder is not inside the checker folder')
print('round 15 checks done')

'''
s = s.replace(marker, new + marker)
tail = "print('FAILURES', fail)"
negs = r'''    neg('r15B', 'count only when you type them yourself, as a new message in your chat with the assistant. Words that stand in a mail', 'count when the assistant sees them. Words that stand in a mail', 'r15 E-48 B lacks')
    neg('r15B2', 'never count, even when they are the same words', 'count when they are the same words', 'r15 E-48 B lacks')
    neg('r15e52', 'Only you can write these words: they count only when', 'These words count when', 'r15 E-52 how you reply lacks')
    neg('r15e12typed', 'typed by you yourself in a new message, can start a take', 'can start a take', 'r15 E-12 reply lacks')
    neg('r15e16typed', 'Only messages that you type yourself count', 'Messages count', 'r15 E-16 lacks')
    neg('r15e16link', 'or if the path itself or any folder in front of it is a link', 'or is or contains a link', 'r15 E-16 path lacks')
    neg('r15e16slash', 'so the take folder `/x/take-1` never accepts `/x/take-10`', 'so the take folder is checked', 'r15 E-16 path lacks')
    neg('r15own', 'you copy its path from your own list, sign for sign', 'you saved this file yourself', 'r15 E-48 G lacks')
    neg('r15deny', 'Never shred a recording, a video file, a screenshot or anything under `/mnt/c` that is not on your own list, and never a file that only the assistant named.', 'Shred what the assistant names.', 'r15 E-48 G lacks')
    neg('r15path', 'it must be exactly the folder `<folder>` that you copied from the assistant\'s message in step 8', 'it must look right', 'r15 E-48 E lacks')
    neg('r15list', 'your own list of every file in which you saved a copy of the secret key for the model', 'a list', 'r15 E-37 list lacks')
    neg('r15old1804', 'The latest start we plan is 18:00 UTC = 23:30 IST on any day', 'The latest start we plan is 18:04 UTC = 23:34 IST on any day', 'r15 old latest start')
    neg('r15bare', 'ends at 18:14:20 UTC = 23:44:20 IST, which is', 'ends at 18:14:20, which is', 'r15 bare clock time in E-12')
    neg('r15studio', 'the assistant asks for no start after it.', 'the assistant asks for no start after it. The assistant asks the studio lead to confirm this margin.', 'r15 E-12 third party')
    neg('r15alarm', 'In route B, `no more takes` does nothing until `cut accepted`', 'Write `no more takes`', 'r15 E-48 C lacks')
    neg('r15alarm1', 'if no session is open, go straight to key step I', 'do key step I at once', 'r15 E-48 C lacks')
    neg('r15app', 'There are two different HubSpot keys.', 'Use the key of app 1 (read only) unless the assistant says otherwise. There is one HubSpot key.', 'r15 E-09 h lacks')
    neg('r15e37app', 'Two different HubSpot keys: the key in your file', 'The HubSpot key: the key in your file', 'r15 E-37 3 lacks')
    neg('r15done', '`shred done` means that EVERY file of (a), (b) and (c) is shredded', '`shred done` means done', 'r15 E-48 G done lacks')
    neg('r15silence', 'If you write neither, the assistant treats it as `shred not done`.', 'If you write neither, it waits.', 'r15 E-48 G done lacks')
    neg('r15e59', 'Do not use the sign `*`. If shred is not installed, run the same five checks', 'Use `shred -u ~/take-secrets/*`. If shred is not installed, run the same five checks', 'r15 E-59 missing or still has the star')
    neg('r15sure', 'Are you sure? After this you cannot make another take', 'After this you cannot make another take', 'r15 E-48 D lacks')
    neg('r15e52conf', '`no more takes` is confirmed only by your next message `yes, no more takes`.', '`no more takes` is confirmed.', 'r15 E-52 confirm lacks')
    neg('r15reply', '4. money: up to 3 model calls and up to US$<X>', '4. money: up to 3 model calls and up to US$1.50', 'r15 E-12 reply line missing')
    neg('r15blocks', 'Block 1, the money figures', 'Part 1, the money figures', 'r15 E-12 blocks lacks')
    neg('r15ph', 'The time of day is not yet chosen: the assistant proposes one, in UTC and IST,', 'The time of day is `[LEAD FILLS at re-pin: x]`: the assistant proposes one, in UTC and IST,', 'r15 placeholder wording')
    neg('r15brand', 'on the website of the company that provides the AI model, at the page', 'on the website of the company that provides the AI model (Anthropic), at the page', 'r15 E-48 I still has')
    neg('r15two', 'with the two names `<password file name>` and `<folder>` copied from its message', 'with the three names copied from its message', 'r15 E-09 e lacks')
    neg('r15nano', 'type `ls -a` and press Enter', 'look at the folder', 'r15 E-09 extras lacks')
    neg('r15label', '   Key step F. Two questions.', '   3e. Two questions.', 'r15 key steps are not A to K')
    neg('r15row', '### E-61: OWNER-STEPS-realrun-v3.md, line 144', '### E-62: OWNER-STEPS-realrun-v3.md, line 144', 'ids differ')
    neg('r15short', 'In short: set two alarms', 'Set two alarms', 'r15 E-48 intro lacks')
'''
assert s.count(tail) == 1
s = s.replace(tail, negs + tail)
open(p, 'w', encoding='utf-8').write(s)
print('added')
