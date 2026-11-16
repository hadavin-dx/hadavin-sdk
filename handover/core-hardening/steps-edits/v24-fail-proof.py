"""Runs newchecks-v25.py on the v24 built sheets, note and open list: every FAIL id printed here is a new check that fails on v24."""
import os, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
A = rd('OWNER-SHEET-v24-A.md'); B = rd('OWNER-SHEET-v24-B.md'); NOTE = rd('LEAD-RELEASE-NOTE-v8.md'); OPEN = rd('v24-OPEN-FOR-LEAD.md')
F = []
def fail(c, m): F.append((c, m))
exec(open(D + 'newchecks-v25.py', encoding='utf-8').read())
ids = sorted(set(c for c, _ in F))
for c, m in F: print('FAIL', c, m[:110])
print('ids that fail on v24:', ' '.join(ids))
