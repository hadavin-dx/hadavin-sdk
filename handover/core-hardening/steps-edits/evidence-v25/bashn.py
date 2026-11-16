import re, subprocess, sys
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
bad = 0
for n in ('A', 'B'):
    t = open(D + 'OWNER-SHEET-v25-%s.md' % n, encoding='utf-8').read()
    cmds = []
    for m in re.finditer(r'(?m)^```[a-z]*\n(.*?)^```', t, re.S):
        if not m[1].startswith('Run name:'): cmds.append(m[1])
    for m in re.finditer(r'`([^`\n]*)`', t):
        c = m[1]
        if re.match(r'(\(\s?set -C|ls |grep |date -u|clear|echo \$\?|python3 -I|cd )', c): cmds.append(c)
    for i, c in enumerate(cmds):
        c2 = re.sub(r'<[^>]*>', 'x', c)
        r = subprocess.run(['bash', '-n', '-c', c2], capture_output=True, text=True)
        print('== %s-%02d: %s\nbash -n rc=%d %s' % (n, i, c[:110], r.returncode, r.stderr.strip()[:80])); bad += r.returncode != 0
print('bash -n failures:', bad)
