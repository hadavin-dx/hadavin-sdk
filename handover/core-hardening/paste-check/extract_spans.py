import re, sys, os, subprocess, shlex
PLAN, OUT, PCK = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(PLAN, encoding='utf-8').read().split('\n')
fence = False
spans = []  # (line, step, text)
for i, l in enumerate(lines, 1):
    if l.startswith('```'):
        fence = not fence; continue
    if fence: continue
    m = re.match(r'- \*\*([^*]+)\*\*', l)
    if m:
        step = m.group(1); body = l[m.end():]
        cut = body.find(' -> ')
        pre = body if cut < 0 else body[:cut]
        for j, s in enumerate(re.findall(r'`([^`]+)`', pre), 1):
            spans.append((i, step, j, s))
    elif i == 409:
        for j, s in enumerate(re.findall(r'`([^`]+)`', l), 1):
            spans.append((i, 'S13-prefix', j, s))
# prefix from line 409: first span
prefix = [s for (i, st, j, s) in spans if i == 409][0]
PS = re.compile(r'Start-Process|Get-Process|\$PSVersionTable|`& \{|^& \{|Remove-Item|-ErrorAction|\bpwsl?\b')
defs = {}
def defline(ph):
    if ph == '<prefix>': return 409
    for i, l in enumerate(lines, 1):
        if ph in l and re.search(r'(means|stands for|is the|defined|=|same)', l.replace(ph, '')) and not l.startswith('- **'):
            return i
    return ''
rows = []
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).returncode
for (ln, step, j, s) in spans:
    phs = sorted(set(re.findall(r'<[a-z0-9_-]+>', s)))
    if re.search(r'Get-Process|Remove-Item|Start-Process|\$PSVersionTable|^try \{|& \{', s):
        lang = 'powershell'
    elif re.search(r'python3? (-I )?(-c|- <<)', s): lang = 'shell+python'
    else: lang = 'shell'
    be = de = pe = bp = dp = ''
    if lang != 'powershell':
        t = s.replace('<prefix>', prefix)
        fn = f'{OUT}/spans/{ln}-{j}.sh'
        open(fn, 'w').write(t + '\n')
        be = run(['bash', '-n', fn]); de = run(['dash', '-n', fn])
        t2 = re.sub(r'<[a-z0-9_-]+>', 'PH', t); open(fn+'.ph','w').write(t2+'\n'); bp = run(['bash','-n',fn+'.ph']); dp = run(['dash','-n',fn+'.ph'])
        if lang == 'shell+python':
            pe = 0
            for m in re.finditer(r"python3? (?:-I )?-c ('([^']*)'|\"((?:[^\"\\]|\\.)*)\")", t):
                prog = m.group(2) if m.group(2) is not None else m.group(3)
                pf = f'{OUT}/spans/{ln}-{j}.py'
                open(pf, 'w').write(prog)
                r = run(['python3', '-I', '-c', 'import sys;compile(open(sys.argv[1]).read(),"x","exec")', pf])
                pe = pe or r
    rows.append((ln, step, j, lang, be, de, pe, f'{bp}/{dp}', ','.join(f'{p}[def@{defline(p)}]' if defline(p) else f'{p}[undefined]' for p in phs)))
with open(f'{PCK}/spans-index.tsv', 'w') as f:
    f.write('line\tstep\tspan_n\tlang\tbash_n\tdash_n\tpython\tph_substituted_bash/dash\tplaceholders\n')
    for r in rows: f.write('\t'.join(map(str, r)) + '\n')
print(len(rows), 'spans')
