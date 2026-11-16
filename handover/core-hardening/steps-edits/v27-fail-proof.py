"""v27-fail-proof.py: proves each v27 check for a missed v25 plant (N01 N05 N10 N11 N12 N14, M4 x4, C55 slash gap) FAILS on the built v25 files with that plant,
and does not fail on the unplanted built v25 files. It also runs the v25 C55 rule on the slash text to show v25 missed it.
Usage: python3 v27-fail-proof.py   (needs OWNER-SHEET-v25-A/B.md, LEAD-RELEASE-NOTE-v9.md, v25-OPEN-FOR-LEAD.md and newchecks-v27.py in this folder; v25 files are only read). Exit 0 = every plant caught by its own check."""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__)) + '/'
rd = lambda n: open(D + n, encoding='utf-8').read()
A0, B0, NOTE, OPEN = rd('OWNER-SHEET-v25-A.md'), rd('OWNER-SHEET-v25-B.md'), rd('LEAD-RELEASE-NOTE-v9.md'), rd('v25-OPEN-FOR-LEAD.md')
src = rd('newchecks-v27.py'); i = src.index('# ---- Part 3 (v27)'); head = src[:src.index('# ---- Part 1')]
SEC = [r'\bsk-[A-Za-z0-9_-]{8,}', r'\bAKIA(?!IOSFODNN7EXAMPLE)[A-Z0-9]{12,}', r'\b[A-Za-z0-9+/_-]{40,}\b', r'\bgh[pousr]_[A-Za-z0-9]{20,}', r'\bxox[abp]-[A-Za-z0-9-]{10,}']
INTENDED = ('C70', 'C71', 'C72', 'C73', 'C74', 'C75', 'C76', 'C77', 'C78', 'C79')
def run(A, B):
    fails = []
    ns = dict(A=A, B=B, NOTE=NOTE, OPEN=OPEN, fail=lambda c, m: fails.append(c), F={'okb': '16:00 UTC = 21:30 IST'}, SEC=SEC)
    code = head + '\n' + src[i:]
    code = re.sub(r"^(need\('C(?:8[1-9]|9\d|100|101)'.*)$", r"pass", code, flags=re.M)   # only the intended v25-plant checks: the later ones test v27 wording
    exec(code, ns); return set(fails)
clean = run(A0, B0)
print('unplanted v25 built files: intended checks failing:', sorted(c for c in clean if c in INTENDED) or 'none')
PLANTS = [('N01', 'C70', 'IST** = UTC + 5:30', 'IST** = UTC + 4:30'), ('N05', 'C71', 'deleted or archived, or asking', 'deleted or deleted, or asking'),
          ('N10', 'C72', ' (else do not press Enter: do the card)', ''), ('N11', 'C73', 'Posting (by Wed 25 Nov', 'Posting (by Thu 26 Nov'),
          ('N12', 'C74', 'You delete only made-up contacts of this run and demo mails, by hand, one by one.', 'Only made-up contacts of this run and demo mails are deleted, one by one.'),
          ('N14', 'C75', 'Run `date -u` in the read terminal: the run day still holds', 'Run `date` in the read terminal: the run day still holds'),
          ('M4a', 'C76', 'in USD 3.00, out USD 15.00', 'in USD 15.00, out USD 3.00'), ('M4b', 'C77', 'per call: 40000 and 10000', 'per call: 10000 and 40000'),
          ('M4c', 'C78', 'DEADLINE = 2026-11-23T18:29:00Z', 'DEADLINE = 2026-11-23T18:19:00Z'), ('M4d', 'C79', 'Deadline 2026-11-23 18:29 UTC = 23:59 IST."', 'Deadline 2026-11-23 18:19 UTC = 23:49 IST."')]
bad = 0
for pid, code, o, n in PLANTS:
    if A0.count(o) < 1: print(pid, 'anchor not found in v25 A'); bad += 1; continue
    f = run(A0.replace(o, n), B0.replace(o, n))
    ok = code in f and code not in clean
    print('%-4s planted in the built v25 files: %s fails %s (other new codes failing: %s)' % (pid, code, 'YES' if ok else 'NO', sorted(f - clean - {code}) or 'none'))
    bad += 0 if ok else 1
fake = 'q' * 8 + '/' + 'Z' * 16 + '_' + 'k' * 12 + '-' + 'm' * 9                                  # 47 characters with a slash, built from parts
v25_skips = any(('/' in m[0] and len(m[0]) < 60) for m in re.finditer(SEC[2], 'x ' + fake + ' y'))
print('C55 slash gap: the v25 rule (skip a match with "/" and fewer than 60 characters) skips the 47-character text: %s' % ('YES (v25 missed it)' if v25_skips else 'NO'))
bad += 0 if v25_skips else 1
print('v27-fail-proof: %d problem(s)' % bad); sys.exit(1 if bad else 0)
