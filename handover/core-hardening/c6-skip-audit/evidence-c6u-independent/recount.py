import re,sys
p=sys.argv[1]; L=open(p,encoding='utf-8').read().split('\n')
rows=[l for l in L if re.match(r'^\| \d+ \| NOT APPLIED',l)]
ids=[int(re.match(r'^\| (\d+) ',l).group(1)) for l in rows]
print('rows',len(rows),'unique ids',len(set(ids)),'max',max(ids),'missing',[i for i in range(1,max(ids)+1) if i not in ids])
def st(l): return re.match(r'^\| \d+ \| (NOT APPLIED; [^|]*) \|',l).group(1)
ready=sum(1 for l in rows if st(l)=='NOT APPLIED; ready')
chk=sum(1 for l in rows if 'after check' in st(l))
dflt=sum(1 for l in rows if 'on the default of' in st(l) and 'after check' not in st(l))
own=sum(1 for l in rows if 'waits for the answer of' in st(l))
print('ready',ready,'default-only',dflt,'waits-check',chk,'waits-owner',own,'sum',ready+dflt+chk+own)
print('any default (incl check+default)',sum(1 for l in rows if 'on the default of' in st(l)))
w1=ready+dflt  # wave 1 = ready + on default
print('wave1 (ready+default-only)',w1)
# box
h=[i for i,l in enumerate(L) if l.startswith('## Start here')]
a,b=h[0],h[1]
for name,seg in (('body only',L[a+1:b]),('with heading',L[a:b])):
    print('box words',name,len(' '.join(seg).split()))
m=re.search(r'This box holds (\d+) words',' '.join(L[a:b])); print('stated',m.group(1) if m else None)
for pat in (r'\b96 rows',r'READY \((\d+)',r'ON DEFAULT \((\d+)',r'WAITS FOR A CHECK \((\d+)',r'WAITS FOR THE OWNER \((\d+)',r'the builder applies the (\d+) wave 1 rows'):
    print(pat,re.findall(pat,' '.join(L[a:b])))
