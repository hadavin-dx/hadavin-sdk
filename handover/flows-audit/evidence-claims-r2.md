# Evidence: claims tables, round 2 (EVIDENCE RUNNER, raw, no judgement)

Run 2026-11-16 with: python3 -I /tmp/ct2/check.py

## Mismatches first
(a) COLS CLAIMS-TABLE.md:713 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:714 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:715 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:716 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:717 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:718 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:719 has 3, header(line 709) 4
(a) COLS lanes13/claims-B.md:360 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:361 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:362 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:363 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:364 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:365 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:366 has 3, header(line 356) 4
## Raw output
```
table CLAIMS-TABLE.md:98 cols=11 rows=42
table CLAIMS-TABLE.md:145 cols=11 rows=39
table CLAIMS-TABLE.md:224 cols=7 rows=99
table CLAIMS-TABLE.md:394 cols=7 rows=65
table CLAIMS-TABLE.md:461 cols=7 rows=8
table CLAIMS-TABLE.md:471 cols=7 rows=20
table CLAIMS-TABLE.md:493 cols=7 rows=11
table CLAIMS-TABLE.md:506 cols=7 rows=14
table CLAIMS-TABLE.md:522 cols=7 rows=9
table CLAIMS-TABLE.md:533 cols=7 rows=7
table CLAIMS-TABLE.md:542 cols=7 rows=23
table CLAIMS-TABLE.md:567 cols=7 rows=31
table CLAIMS-TABLE.md:600 cols=7 rows=13
table CLAIMS-TABLE.md:615 cols=7 rows=11
table CLAIMS-TABLE.md:628 cols=7 rows=6
table CLAIMS-TABLE.md:636 cols=7 rows=9
table CLAIMS-TABLE.md:647 cols=7 rows=27
table CLAIMS-TABLE.md:700 cols=7 rows=6
table CLAIMS-TABLE.md:709 cols=4 rows=11
table CLAIMS-TABLE.md:727 cols=2 rows=7
table lanes13/claims-A.md:36 cols=7 rows=99
table lanes13/claims-B.md:41 cols=7 rows=65
table lanes13/claims-B.md:108 cols=7 rows=8
table lanes13/claims-B.md:118 cols=7 rows=20
table lanes13/claims-B.md:140 cols=7 rows=11
table lanes13/claims-B.md:153 cols=7 rows=14
table lanes13/claims-B.md:169 cols=7 rows=9
table lanes13/claims-B.md:180 cols=7 rows=7
table lanes13/claims-B.md:189 cols=7 rows=23
table lanes13/claims-B.md:214 cols=7 rows=31
table lanes13/claims-B.md:247 cols=7 rows=13
table lanes13/claims-B.md:262 cols=7 rows=11
table lanes13/claims-B.md:275 cols=7 rows=6
table lanes13/claims-B.md:283 cols=7 rows=9
table lanes13/claims-B.md:294 cols=7 rows=27
table lanes13/claims-B.md:347 cols=7 rows=6
table lanes13/claims-B.md:356 cols=4 rows=11
table lanes13/claims-B.md:374 cols=2 rows=7
A 97 {'UNSUPPORTED': 13, 'SUPPORTED': 34, 'UNTRACED': 7, 'OVERSTATED': 19, 'RELAYED-ONLY': 24}
B 230 {'SUPPORTED': 80, 'UNTRACED': 63, 'OVERSTATED': 30, 'RELAYED-ONLY': 45, 'UNSUPPORTED': 12}
A+B 327 {'UNSUPPORTED': 25, 'SUPPORTED': 114, 'UNTRACED': 70, 'OVERSTATED': 49, 'RELAYED-ONLY': 69}
TABLE 327 {'UNSUPPORTED': 25, 'SUPPORTED': 114, 'UNTRACED': 70, 'OVERSTATED': 49, 'RELAYED-ONLY': 69}
(d) {'## Table 1: Change before the take': 40, '## Table 2: Fix when the files are next touched': 37}
MISMATCHES 14
(a) COLS CLAIMS-TABLE.md:713 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:714 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:715 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:716 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:717 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:718 has 3, header(line 709) 4
(a) COLS CLAIMS-TABLE.md:719 has 3, header(line 709) 4
(a) COLS lanes13/claims-B.md:360 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:361 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:362 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:363 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:364 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:365 has 3, header(line 356) 4
(a) COLS lanes13/claims-B.md:366 has 3, header(line 356) 4
```

## Script
```python
import re,collections
D='/home/user/hadavin-sdk/handover/flows-audit/'
def cells(l):
    s=l.strip()
    parts=re.split(r'(?<!\\)\|',s)
    return parts[1:-1] if s.endswith('|') else parts[1:]
def tables(path):
    L=open(path,encoding='utf-8').read().split('\n')
    out=[];cur=None
    for i,l in enumerate(L,1):
        if l.lstrip().startswith('|'):
            if cur is None: cur={'start':i,'rows':[]}
            cur['rows'].append((i,l))
        else:
            if cur: out.append(cur);cur=None
    if cur: out.append(cur)
    return L,out
res=[]
# (a)
for f in ['CLAIMS-TABLE.md','lanes13/claims-A.md','lanes13/claims-B.md']:
    L,T=tables(D+f)
    for t in T:
        n=len(cells(t['rows'][0][1]))
        for i,l in t['rows']:
            c=len(cells(l))
            if c!=n: res.append(f'(a) COLS {f}:{i} has {c}, header(line {t["start"]}) {n}')
        print(f'table {f}:{t["start"]} cols={n} rows={len(t["rows"])}')
# claims
V=['SUPPORTED ONLY BY RELAYED NUMBER','SUPPORTED','OVERSTATED','UNSUPPORTED','UNTRACED']
def claims(path):
    L,T=tables(path);d=[]
    for t in T:
        for i,l in t['rows']:
            c=[x.strip() for x in cells(l)]
            if c and re.match(r'^(A|B|X)-\d+$',c[0]) and len(c)>=6: d.append((c[0],c[5],i))
    return d
def vk(v):
    if v.startswith('SUPPORTED ONLY BY RELAYED'): return 'RELAYED-ONLY'
    for w in ['SUPPORTED','OVERSTATED','UNSUPPORTED','UNTRACED']:
        if v.startswith(w): return w
    return 'OTHER:'+v[:30]
A=claims(D+'lanes13/claims-A.md');B=claims(D+'lanes13/claims-B.md');C=claims(D+'CLAIMS-TABLE.md')
cnt=lambda x:collections.Counter(vk(v) for _,v,_ in x)
print('A',len(A),dict(cnt(A)));print('B',len(B),dict(cnt(B)));print('A+B',len(A+B),dict(cnt(A+B)));print('TABLE',len(C),dict(cnt(C)))
exp={'SUPPORTED':114,'RELAYED-ONLY':69,'OVERSTATED':49,'UNSUPPORTED':25,'UNTRACED':70}
ab=cnt(A+B)
for k,v in exp.items():
    if ab.get(k,0)!=v: res.append(f'(b) {k}: recount {ab.get(k,0)} vs printed {v}')
if len(A+B)!=327: res.append(f'(b) total {len(A+B)} vs 327')
# per-id verdict diff
cm={i:vk(v) for i,v,_ in C};ab_m={i:vk(v) for i,v,_ in A+B}
for i in sorted(set(cm)&set(ab_m)):
    if cm[i]!=ab_m[i]: res.append(f'(b) verdict differs {i}: lanes {ab_m[i]} vs TABLE {cm[i]}')
# (c)
sa=set(ab_m);sc=set(cm)
for i in sorted(sa-sc): res.append(f'(c) in lanes, missing from CLAIMS-TABLE: {i}')
for i in sorted(sc-sa): res.append(f'(c) in CLAIMS-TABLE, missing from lanes: {i}')
# (e)
for name,x in [('A',A),('B',B),('TABLE',C)]:
    c=collections.Counter(i for i,_,_ in x)
    for i,n in c.items():
        if n>1: res.append(f'(e) duplicate id {i} x{n} in {name} (lines {[l for j,_,l in x if j==i]})')
c=collections.Counter(i for i,_,_ in A+B)
for i,n in c.items():
    if n>1 and not (i in {j for j,_,_ in A} and i in {j for j,_,_ in B} and False): res.append(f'(e) id {i} x{n} across A+B')
# (d)
L=open(D+'CLAIMS-TABLE.md',encoding='utf-8').read().split('\n')
sec=None;d=collections.Counter()
for l in L:
    if l.startswith('## '): sec=l
    if sec and (sec.startswith('## Table 1') or sec.startswith('## Table 2')) and re.match(r'^\|\s*\d+\s*\|',l): d[sec]+=1
print('(d)',dict(d))
open('/tmp/ct2/mismatch.txt','w').write('\n'.join(res))
print('MISMATCHES',len(res));print('\n'.join(res))
```
