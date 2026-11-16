import re, ast, os, sys
bt = open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read()
banned = ast.literal_eval('(' + re.search(r'BANNED = \((.*?)\n\)', bt, re.S).group(1) + ')')
root = sys.argv[1]; files = 0; hitfiles = []; per = [0] * len(banned)
for d, _, fs in os.walk(root):
    for f in fs:
        p = os.path.join(d, f)
        try: t = open(p, encoding='utf-8', errors='replace').read()
        except Exception: continue
        files += 1
        h = [i for i, b in enumerate(banned) if b in t]
        for i in h: per[i] += t.count(banned[i])
        if h: hitfiles.append((os.path.relpath(p, root), len(h)))
print('banned list size', len(banned)); print('files scanned', files)
print('files with a hit', len(hitfiles)); print('hit files (name, distinct strings):', hitfiles[:20])
print('total occurrences per banned index:', per)
