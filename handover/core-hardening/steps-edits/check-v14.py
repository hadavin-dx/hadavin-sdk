"""v14 checks: banned strings, placeholder words, cross references. Read-only."""
import re, sys, ast
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
F = {'S': 'OWNER-STEPS-realrun-v14.md', 'C': 'OWNER-DAY-CARD-v14.md', 'A': 'OWNER-STEPS-v14-APPENDIX.md',
     'CH': 'v14-CHANGES.md', 'OP': 'v14-OPEN-FOR-LEAD.md'}
T = {k: open(D + v, encoding='utf-8').read() for k, v in F.items()}
bad = 0
src = open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read()
m = re.search(r'BANNED = \((.*?)\n\)', src, re.S)
banned = ast.literal_eval('(' + m.group(1) + ')')
print('banned strings in test list:', len(banned))
for k, t in T.items():
    n = sum(t.count(b) for b in banned)
    n2 = len(re.findall(r'\b(PENDING|TBD|TODO)\b', t))
    n3 = len(re.findall(r'\[UNVERIFIED\]', t))
    print(f'{F[k]}: banned={n} PENDING/TBD/TODO={n2} bracketed-UNVERIFIED={n3} bytes={len(t.encode())}')
    bad += n + n2
# cross references
sheet, card, app = T['S'], T['C'], T['A']
steps_s = set(re.findall(r'^\*\*((?:A|B|C|D|0)\.?\d?b?)[ .]', sheet, re.M))
heads = set()
for m_ in re.finditer(r'\*\*(A\.0b|A\.\d|0\.\d|C\.\d|I\.\d|[BD])[ .]', sheet): heads.add(m_.group(1))
for m_ in re.finditer(r'^(\d)\. \*\*I\.(\d)', sheet, re.M): heads.add('I.' + m_.group(2))
for m_ in re.finditer(r'\*\*I\.(\d)', sheet): heads.add('I.' + m_.group(1))
heads |= {'I.0', 'E', 'E.0', 'F', 'F.1', 'F.2', 'F.3', 'F.4', 'F.5', 'H', 'I', 'J', 'G', 'T'}
card_heads = set(re.findall(r'^## (E\.0|E|F)\b', card, re.M)) | {f'F.{i}' for i in range(1, 6)} | {f'E.{i}' for i in range(1, 5)}
print('step headings found in sheet:', sorted(heads))
refs = set()
for k in ('S', 'C', 'A'):
    for r_ in re.findall(r'\b(A\.0b|A\.[0-6]|0\.[1-6]|C\.[1-3]|I\.[0-7]|F\.[1-5]|E\.0)\b', T[k]):
        refs.add((k, r_))
for k, r_ in sorted(refs):
    ok = r_ in heads or r_ in card_heads
    if r_.startswith('F.') or r_ == 'E.0': ok = r_ in card_heads or r_ == 'E.0' and 'E.0' in card_heads
    if r_.startswith('E.') and r_ != 'E.0': ok = ok
    if not ok: print('UNRESOLVED step ref', k, r_); bad += 1
# card headings must contain E.0
if 'E.0 Before E' not in card: print('card lacks E.0 heading'); bad += 1
# F.1-F.5 on card
for i in range(1, 6):
    if not re.search(rf'^{i}\. ', card.split('## F. Film pause')[1], re.M): print('card F item missing', i); bad += 1
# run card rows
for k in ('S', 'C', 'A'):
    for n in re.findall(r'\brows? (\d+)', T[k]):
        if not 1 <= int(n) <= 23: print('bad row', k, n); bad += 1
    for a, b in re.findall(r'rows (\d+) (?:to|and) (\d+)', T[k]):
        for n in (a, b):
            if not 1 <= int(n) <= 23: print('bad row', k, n); bad += 1
# rows table in appendix has 1..23
rows = sorted(int(x) for x in re.findall(r'^\| (\d+) \|', app.split('## 3.')[0].split('## 2.')[1], re.M))
print('run card rows in appendix 2:', rows[0], '..', rows[-1], 'count', len(rows)); bad += rows != list(range(1, 24))
# appendix sections
secs = sorted(int(x) for x in re.findall(r'^## (\d+)\.', app, re.M)); print('appendix sections', secs[0], '..', secs[-1], len(secs)); bad += secs != list(range(1, 19))
for k in ('S', 'C', 'A', 'CH', 'OP'):
    for n in re.findall(r'appendix (\d+)', T[k]) + (re.findall(r'section (\d+)', T[k]) if k == 'A' else []):
        if int(n) not in secs: print('bad appendix/section ref', k, n); bad += 1
# go item refs
for k in ('S', 'C', 'A'):
    for n in re.findall(r'go items? (\d)', T[k]):
        if not 1 <= int(n) <= 9: print('bad go item', k, n); bad += 1
goitems = re.findall(r'^(\d)\. ', sheet.split('## The go list')[1].split('## The money rule')[0], re.M)
print('go items:', goitems); bad += goitems != [str(i) for i in range(1, 10)]
money = re.findall(r'^(\d)\. ', sheet.split('## The money rule')[1].split('## Rules that hold')[0], re.M)
print('money rule items:', money)
for n in re.findall(r'money rule items? (\d)', sheet + card):
    if n not in money: print('bad money item', n); bad += 1
# ban list
ban = re.findall(r'^|\b(\d+)\. ', app.split('## 8.')[1].split('## 9.')[0])
items = re.findall(r'(?:^|\s)(\d{1,2})\. ', app.split('## 8.')[1].split('## 9.')[0])
print('ban list items in appendix 8:', max(int(i) for i in items))
m2 = re.search(r'full list of (\d+)', sheet); print('sheet says full list of', m2.group(1)); bad += int(m2.group(1)) != max(int(i) for i in items)
# row 12/20/21/22/23 etc referenced on card exist (already range-checked). Ports and dates
for s in ('18:29 UTC = 23:59 IST', '25 Nov 2026 15:00 UTC = 20:30 IST'):
    for k in ('S', 'C'):
        print(k, s, T[k].count(s))
for t_, n in (('S', '23 rows'),):
    print('23 rows mentions', T['S'].count('23 rows'))
# contradictory text removed
for pat in ('exit 3 only', 'or 60 minutes after', 'full list of 12', 'appendix G', 'only when C is unknown'):
    c = sum(T[k].count(pat) for k in ('S', 'C', 'A'))
    print('removed phrase', repr(pat), c); bad += c
# v14: single numbered list of blanks
M='THE STUDIO LEAD FILLS THIS IN'
lst=sheet.split('## The blanks')[1].split('## Words')[0]
nums=[int(x) for x in re.findall(r'\bB(\d+) ', lst)]
print('blank list numbers:', nums)
if nums!=list(range(1,len(nums)+1)): print('blank list not sequential'); bad+=1
body=sheet.split('## The blanks')[0]+sheet.split('## Words')[1]
cited=set(); occ=0
for m_ in re.finditer(M, body):
    occ+=1
    tail=body[m_.end():m_.end()+120]
    mm=re.search(r'blank B(\d+)', tail)
    if not mm: print('marker without blank number near:', body[max(0,m_.start()-60):m_.end()+40].replace('\n',' ')); bad+=1
    elif int(mm.group(1)) not in nums: print('blank number not in list', mm.group(1)); bad+=1
    else: cited.add(int(mm.group(1)))
print('sheet marker uses:', occ, 'distinct blanks cited:', sorted(cited))
for n in nums:
    if n not in cited and not re.search(r'blank B%d\b'%n, body + card): print('list blank never used', n); bad+=1
# the top paragraph also mentions the marker once as definition (before list): allowed
for pat in ('Q21','Q20','Q19','window end is','18:14:40'):
    c=sum(T[k].count(pat) for k in ('S','C')); print('owner-file leftover',repr(pat),c); bad+=c
# 'window end' only as the labelled alias
print('window end mentions in sheet:', sheet.count('window end'))
# card blanks refer
for n in re.findall(r'blank B(\d+)', card):
    if int(n) not in nums: print('card blank not in list', n); bad+=1
print('TOTAL PROBLEMS', bad)
sys.exit(1 if bad else 0)
