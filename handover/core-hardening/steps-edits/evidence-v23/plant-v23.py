import os, shutil, subprocess, sys, re
SRC = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
W = '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/plant/'
FILES = ['OWNER-SHEET-v22.md', 'OWNER-SHEET-v23.md', 'LEAD-RELEASE-NOTE-v6.md', 'LEAD-RELEASE-NOTE-v7.md', 'v23-OPEN-FOR-LEAD.md', 'v23-CHANGES.md']
def run(name, f, old, new, count=1):
    shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
    for x in FILES: shutil.copy(SRC + x, W + x)
    t = open(W + f, encoding='utf-8').read()
    if old not in t: print('%-34s SETUP FAIL (text not found: %r)' % (name, old[:40])); return False
    open(W + f, 'w', encoding='utf-8').write(t.replace(old, new, count))
    r = subprocess.run([sys.executable, SRC + 'check-v23.py'], env=dict(os.environ, V23_DIR=W), capture_output=True, text=True)
    first = [l for l in r.stdout.splitlines() if l.startswith('PROBLEM')][:1]
    print('%-34s rc=%d %s' % (name, r.returncode, 'CAUGHT' if r.returncode else 'MISSED'), (first[0][:110] if first else r.stderr[-100:]))
    return r.returncode != 0
S, N, O = 'OWNER-SHEET-v23.md', 'LEAD-RELEASE-NOTE-v7.md', 'v23-OPEN-FOR-LEAD.md'
cases = [
 ('price line 0.28', S, 'Price per call at full size: USD 0.27', 'Price per call at full size: USD 0.28'),
 ('expected total 0.82', S, 'Expected total: USD 0.81 (not a limit)', 'Expected total: USD 0.82 (not a limit)'),
 ('renamed placeholder', S, '<run name>', '<runname>'),
 ('Open list form missing row', N, 'Open 2 and 31', 'Open 2 and 91'),
 ('paraphrased cancel rule', S, 'Then do the card at once.', 'Then do the card at once: press the cancel button, steps 2 to 4, with all filters off.'),
 ('pointer 7.8 -> 7.6 (open)', O, 'sheet 7.8', 'sheet 7.6'),
 ('pointer 8.4 -> 8.3 (note)', N, 'G42, sheet 8.4', 'G42, sheet 8.3'),
 ('pointer R7 -> R9 (sheet)', S, 'do only the card and R7', 'do only the card and R9'),
 ('wrong sum check 3', S, '11:30 + 30 =', '11:30 + 40 ='),
 ('wrong IST pair', S, '18:29 UTC = 23:59 IST', '18:29 UTC = 23:29 IST'),
 ('wrong weekday', S, 'Mon 23 Nov 2026', 'Tue 23 Nov 2026'),
 ('gate id in sheet', S, 'the card first, then R1', 'the card first, G12, then R1'),
 ('banned word', S, 'the card first, then R1', 'the card first, Port MCP, then R1'),
 ('verb send', S, 'Tell the two times', 'Send the two times'),
 ('R10 without card first', S, 'FREEZE (R10, key alive: card first). Any other line', 'FREEZE (R10). Any other line', ),
 ('860 s as 14.4', N, '14.33', '14.4'),
 ('tolerated list 5 not 6', O, 'HubSpot private-app', 'HubSpot private'),
 ('yes sentence outside charset', S, 'does not end the calls', 'does not end the calls!'),
 ('unlisted set phrase', S, 'Tell the lead exactly: model key cancelled.', 'Tell the lead exactly: key is cancelled.'),
 ('card step missing', S, '6. The run is over', '6) The run is over'),
 ('in any case cites Q25 only', N, 'Q26 alone', 'Q25'),
 ('older key bracket clause', S, 'older key <its name or none>', 'older key <its name or none> ['),
]
res = [run(*c) for c in cases]
print('planted %d, caught %d, missed/setup-failed %d' % (len(res), sum(res), len(res) - sum(res)))
