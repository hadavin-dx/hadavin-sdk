"""v26-fail-proof.py: runs the v26 checks (newchecks-v26.py Part 3 + the changed ones) on the BUILT v25 files and prints which new check codes fail there.
Usage: python3 v26-fail-proof.py   Needs the v25 built files in this folder (they are never edited). Exit 0 = every expected check fails on v25."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
A = open(D + 'OWNER-SHEET-v25-A.md', encoding='utf-8').read(); B = open(D + 'OWNER-SHEET-v25-B.md', encoding='utf-8').read()
NOTE = open(D + 'LEAD-RELEASE-NOTE-v9.md', encoding='utf-8').read(); OPEN = open(D + 'v25-OPEN-FOR-LEAD.md', encoding='utf-8').read()
F = {'okb': '16:00 UTC = 21:30 IST'}
FAILS = []
def fail(code, msg): FAILS.append((code, msg))
src = open(D + 'newchecks-v26.py', encoding='utf-8').read()
i = src.index('# ---- Part 3 (v26)'); head = src[:src.index('# ---- Part 1')]
SEC = [r'\bsk-[A-Za-z0-9_-]{8,}', r'\bAKIA(?!IOSFODNN7EXAMPLE)[A-Z0-9]{12,}', r'\b[A-Za-z0-9+/_-]{40,}\b', r'\bgh[pousr]_[A-Za-z0-9]{20,}', r'\bxox[abp]-[A-Za-z0-9-]{10,}']
ns = dict(A=A, B=B, NOTE=NOTE, OPEN=OPEN, fail=fail, F=F, SEC=SEC)
exec(head + '\n' + src[i:], ns)
codes = sorted(set(c for c, _ in FAILS))
want = ['C70', 'C71', 'C72', 'C73', 'C74', 'C75', 'C76', 'C77', 'C78', 'C79', 'C81', 'C82', 'C83', 'C84', 'C85', 'C86', 'C87', 'C89', 'C90', 'C91', 'C93', 'C94', 'C96', 'C97']
print('checks that fail on the built v25 files:', ' '.join(codes))
miss = [c for c in want if c not in codes]
print('expected to fail on v25 but did not:', miss or 'none')
print('C80 (secret scan on a text with a slash) on v25 logic: v25 skipped any 40+ character match containing "/" and shorter than 60: yes (read from check-v25.py line C55)')
sys.exit(1 if miss else 0)
