#!/usr/bin/env python3
"""Reads BANNED from the repo test at run time; prints counts only (never the strings)."""
import re, ast, sys, os
bt = open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read()
m = re.search(r'BANNED = \((.*?)\n\)', bt, re.S)
banned = ast.literal_eval('(' + m.group(1) + ')')
print('BANNED list length:', len(banned))
tot = 0
for p in sys.argv[1:]:
    files = [p] if os.path.isfile(p) else [os.path.join(d, f) for d, _, fs in os.walk(p) for f in fs if '__pycache__' not in d]
    for f in sorted(files):
        try: t = open(f, 'rb').read().decode('utf-8')
        except Exception as e: print('UNSCANNABLE', f, type(e).__name__); continue
        n = sum(1 for b in banned if b in t); occ = sum(t.count(b) for b in banned)
        tot += n
        print('%s: distinct banned strings %d, occurrences %d' % (os.path.relpath(f), n, occ))
print('TOTAL distinct-string hits over scanned files:', tot)
